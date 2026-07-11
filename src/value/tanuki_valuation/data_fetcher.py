"""
TANUKI VALUATION - Data Fetcher v2.4
SEC EDGAR + yfinance ハイブリッド取得（マイクロキャップ対応 + β取得）

v2.4 変更点:
- beta_config.json によるKoichi意図βを最優先採用
  優先順位: beta_config.json override > yfinance β > セクターデフォルト
- β採用理由をログ出力・latest.jsonに記録
"""

import logging
import os
import sys
import json
from statistics import mean
from typing import Dict, Any, Optional, Tuple

# yfinance
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# SEC EDGAR - common/sec_data/reader.py
HAS_SEC = False
SECReader = None
repo_root: str | None = None

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    
    from common.sec_data.reader import SECReader
    HAS_SEC = True
except Exception:
    pass

if not HAS_SEC:
    try:
        github_workspace = os.environ.get("GITHUB_WORKSPACE", "")
        if github_workspace:
            repo_root = github_workspace
        if github_workspace and github_workspace not in sys.path:
            sys.path.insert(0, github_workspace)
        from common.sec_data.reader import SECReader
        HAS_SEC = True
    except Exception:
        pass


# セクター別デフォルトβ
SECTOR_DEFAULT_BETA = {
    "Technology": 1.20,
    "Consumer Cyclical": 1.10,
    "Consumer Defensive": 0.80,
    "Communication Services": 1.00,
    "Healthcare": 0.90,
    "Financial Services": 1.30,
    "Industrials": 1.10,
    "Energy": 1.15,
    "Basic Materials": 1.10,
    "Real Estate": 0.90,
    "Utilities": 0.50,
    "default": 1.00
}


def _quarters_complete(flow: dict, *field_names: str, min_quarters: int = 4) -> bool:
    """
    指定フィールドすべてがquarters_used>=min_quartersを満たすか判定する。

    TTM-QUARTERS-CHECK-1対応: 四半期粒度のSECデータ取得が始まる前の境界期間
    （2022年Q1前後が大半）では、本来4四半期必要な集計が1〜3四半期分しか
    揃っていない不完全なTTM値がflow内に存在する。field_nameが未取得（キー自体が
    存在しない）場合もquarters_used=0扱いとして不完全と判定する。
    """
    return all(
        flow.get(name, {}).get("quarters_used", 0) >= min_quarters
        for name in field_names
    )


class TTMReader:
    """TTM系列ファイル（{ticker}_ttm_series.json）の読み込み"""

    def __init__(self, ticker: str, repo_root_path: str | None):
        self.ticker = ticker.upper()
        self._series: list[dict] | None = None
        if repo_root_path:
            self._path: str | None = os.path.join(
                repo_root_path, "common", "sec_data", "ttm",
                f"{self.ticker}_ttm_series.json",
            )
        else:
            self._path = None
        self._load()

    def _load(self) -> None:
        if not self._path:
            logging.warning("[%s] TTMReader: repo_root未解決のためスキップ", self.ticker)
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
                self._series = data.get("series", [])
        except FileNotFoundError:
            self._series = None
            logging.warning("[%s] TTM series file not found: %s", self.ticker, self._path)

    def get_fcf_series(self) -> list[float] | None:
        """
        FCF系列をfloatリストで返す（降順・最新が先頭）。2点未満はNone

        OCF・CapExいずれかがquarters_used<4（四半期集計が不完全）の期間は
        除外する（TTM-QUARTERS-CHECK-1）。FCF=OCF-CapExのため、片方でも
        不完全ならFCF自体の値も欠陥値になる。
        """
        if not self._series:
            return None
        vals = [
            s["flow"]["FCF"]["val"]
            for s in self._series
            if s.get("flow", {}).get("FCF", {}).get("val") is not None
            and _quarters_complete(s.get("flow", {}), "OCF", "CapEx")
        ]
        return vals if len(vals) >= 2 else None

    def get_ttm_end(self) -> str | None:
        if self._series:
            return self._series[0].get("ttm_end")
        return None

    def get_periods(self) -> int:
        """get_fcf_series()が実際に採用する点数と一致させる（表示用の点数が
        実データと乖離しないよう、同一の完全性フィルタを適用する）"""
        if not self._series:
            return 0
        return sum(
            1 for s in self._series
            if s.get("flow", {}).get("FCF", {}).get("val") is not None
            and _quarters_complete(s.get("flow", {}), "OCF", "CapEx")
        )

    def get_series(self) -> list[dict] | None:
        return self._series


def build_rice_annual_shape(ttm_series: list[dict]) -> list[dict]:
    """
    TTM系列を rice.py が期待する annual_data 形式に変換するアダプター。
    rice.py は変更しない — このアダプターでインターフェースを吸収する。

    rice.py が使うフィールド:
      period                      ← "TTM@{ttm_end}" 形式（警告ログ用）
      cf.operating_cash_flow      ← OCF
      cf.capital_expenditure      ← CapEx
      pl.revenue                  ← Revenue
      pl.net_income               ← NetIncome
      pl.research_and_development ← RD（Noneの場合はNoneのまま渡す）
      pl.selling_and_marketing    ← SM（Noneの場合はNoneのまま渡す、rice側で or 0.0）
      data_quality                ← sga_gap_warning用（TTMパスでは空dict）

    OCF/CapEx/Revenue/NetIncomeのいずれかがquarters_used<4（四半期集計が
    不完全）の期間はresultから除外する（TTM-QUARTERS-CHECK-1）。RD/SMは
    rice.py側で既にNone許容（0扱い・警告ログのみ）のためチェック対象外。
    """
    result = []
    for s in ttm_series:
        flow = s.get("flow", {})
        if not _quarters_complete(flow, "OCF", "CapEx", "Revenue", "NetIncome"):
            continue
        result.append({
            "period": f"TTM@{s.get('ttm_end', '?')}",
            "cf": {
                "operating_cash_flow":    flow.get("OCF", {}).get("val"),
                "capital_expenditure":    flow.get("CapEx", {}).get("val"),
                "stock_based_compensation": flow.get("SBC", {}).get("val"),
            },
            "pl": {
                "revenue":                  flow.get("Revenue", {}).get("val"),
                "net_income":               flow.get("NetIncome", {}).get("val"),
                "research_and_development": flow.get("RD", {}).get("val"),
                "selling_and_marketing":    flow.get("SM", {}).get("val"),
            },
            "data_quality": {},
        })
    return result


def _load_beta_config() -> Dict[str, Any]:
    """
    config/beta_config.json を読み込む

    GitHub Actions 実行時は GITHUB_WORKSPACE から、
    ローカル実行時はファイルの相対パスで解決する。
    """
    search_paths = []

    # GitHub Actions 環境
    workspace = os.environ.get("GITHUB_WORKSPACE", "")
    if workspace:
        search_paths.append(os.path.join(workspace, "config", "beta_config.json"))

    # ローカル: このファイルから4階層上がるとリポジトリルート
    try:
        current = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current)))
        search_paths.append(os.path.join(repo_root, "config", "beta_config.json"))
    except Exception:
        pass

    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"   [WARN] beta_config.json 読み込みエラー: {e}")
                return {}

    return {}


class TanukiDataFetcher:
    """
    TANUKI VALUATION 用データフェッチャー v2.3
    
    データソース優先順位:
    1. 株式数: yfinance implied > max(SEC diluted, yfinance outstanding)
    2. FCF/Revenue/ROE/RPO: SEC XBRL (SECReaderのヘルパーメソッド使用)
    3. 株価/β: yfinance
    """
    
    def __init__(self):
        self.sec_reader = SECReader() if HAS_SEC else None
        # beta_config.json をロード（起動時1回のみ）
        _cfg = _load_beta_config()
        self._beta_overrides: Dict[str, Any] = _cfg.get("overrides", {})
        if self._beta_overrides:
            print(f"   [INFO] beta_config.json: {len(self._beta_overrides)}銘柄のβオーバーライドを読み込みました")
    
    def get_financials(self, ticker: str) -> Dict[str, Any]:
        """財務データ取得メイン関数"""
        print(f"\n   [{ticker}] データ取得開始")
        
        fcf_list = []
        fcf_avg = 0.0
        sec_diluted = 0
        roe_avg = None
        roe_years_used = 0
        roe_outlier_adj = False
        revenue = 0.0
        rpo = 0.0
        net_cash_data = {"net_cash": 0.0, "available": False}  # BS評価補正用

        # TTM FCF/RICE 状態（TTMReader ブロックで更新）
        fcf_source = "annual_fallback"
        fcf_ttm_end: str | None = None
        fcf_ttm_periods = 0
        rice_annual_data = None
        rice_data_source = "annual_fallback"
        
        # ========================================
        # 1. SEC EDGAR
        # ========================================
        if self.sec_reader:
            try:
                fcf_avg = self.sec_reader.get_fcf_5yr_avg(ticker)
                print(f"   [{ticker}] SEC FCF 5yr avg: ${fcf_avg:,.0f}")
                
                fcf_list = self.sec_reader.get_fcf_list(ticker, years=5)
                print(f"   [{ticker}] SEC FCF list: {len(fcf_list)}年分")
                
                # ファイナンスリース除外が適用されたか確認
                _annual = self.sec_reader.get_annual_range(ticker, 1)
                if _annual:
                    _fl_applied = _annual[0].get("cf", {}).get("finance_lease_payments_applied", False)
                    _fl_amt = _annual[0].get("cf", {}).get("finance_lease_payments", 0)
                    if _fl_applied:
                        print(f"   [{ticker}] ファイナンスリース除外: ${abs(_fl_amt):,.0f}をCapExから控除")
                
                sec_diluted = self.sec_reader.get_diluted_shares(ticker)
                if sec_diluted > 0:
                    print(f"   [{ticker}] SEC shares: {sec_diluted:,.0f}")
                
                roe_avg, roe_years_used, roe_outlier_adj = self.sec_reader.get_roe_avg_detail(ticker, years=10)
                _roe_str = f"{roe_avg:.1%}" if roe_avg is not None else "N/A (負債超過)"
                print(f"   [{ticker}] SEC ROE avg: {_roe_str} ({roe_years_used}yr)")
                
                revenue = self.sec_reader.get_latest_revenue(ticker)
                print(f"   [{ticker}] SEC revenue: ${revenue:,.0f}")
                
                rpo = self.sec_reader.get_rpo(ticker)
                if rpo > 0:
                    print(f"   [{ticker}] SEC RPO: ${rpo:,.0f}")

                # BS評価補正用（v8.1: sector確定後に呼ぶため、ここでは取得しない）

            except Exception as e:
                print(f"   [{ticker}] SEC取得エラー: {e}")

        # ========================================
        # TTM系列: FCFソース切り替え（年次→TTM）
        # ========================================
        ttm_reader = TTMReader(ticker, repo_root)
        fcf_series = ttm_reader.get_fcf_series()

        if fcf_series:
            fcf_list = fcf_series
            fcf_avg = float(mean(fcf_series))
            fcf_source = "ttm_series"
            fcf_ttm_end = ttm_reader.get_ttm_end()
            fcf_ttm_periods = ttm_reader.get_periods()
            print(f"   [{ticker}] TTM FCF series: {len(fcf_series)}点 end={fcf_ttm_end}")
        else:
            logging.warning("[%s] TTM series unavailable, fallback to annual FCF", ticker)

        ttm_series_data = ttm_reader.get_series()
        if ttm_series_data:
            rice_annual_data = build_rice_annual_shape(ttm_series_data)
            rice_data_source = "ttm_series"
        else:
            rice_annual_data = self.sec_reader.get_annual_range(ticker, years=4) if self.sec_reader else None
            rice_data_source = "annual_fallback"

        # ========================================
        # 2. yfinance（株式数、株価、β、セクター）
        # ========================================
        yf_implied = 0
        yf_outstanding = 0
        current_price = 0.0
        beta = None
        sector = "default"
        industry = ""       # v8.1: 保険判定精度向上のためindustryも取得
        per = None
        peg = None
        ps = None
        ev_ebitda = None
        ma200 = None
        forward_eps = None
        analyst_target_median = None
        analyst_target_mean = None
        analyst_target_low = None
        analyst_target_high = None
        analyst_count = None
        analyst_rec_key = ""
        dividend_yield = 0.0
        payout_ratio   = 0.0

        if HAS_YFINANCE:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # 株式数
                yf_implied = info.get("impliedSharesOutstanding", 0) or 0
                if yf_implied > 0:
                    print(f"   [{ticker}] yfinance implied shares: {yf_implied:,.0f}")
                
                yf_outstanding = info.get("sharesOutstanding", 0) or 0
                if yf_outstanding > 0:
                    print(f"   [{ticker}] yfinance outstanding shares: {yf_outstanding:,.0f}")
                
                # 株価
                current_price = (
                    info.get("currentPrice") or 
                    info.get("regularMarketPrice") or 
                    info.get("previousClose") or 0
                )
                if current_price > 0:
                    print(f"   [{ticker}] yfinance price: ${current_price:.2f}")
                
                # β（ベータ）
                beta = info.get("beta")
                if beta is not None and beta > 0:
                    print(f"   [{ticker}] yfinance beta: {beta:.2f}")
                
                # セクター・業種（v8.1: industryを追加取得）
                sector = info.get("sector", "default")
                if sector and sector != "default":
                    print(f"   [{ticker}] yfinance sector: {sector}")
                industry = info.get("industry", "")
                if industry:
                    print(f"   [{ticker}] yfinance industry: {industry}")


                # PER（株価収益率）
                _trailing_pe = info.get("trailingPE")
                _forward_pe  = info.get("forwardPE")
                per = _trailing_pe or _forward_pe or None
                per_is_forward = (
                    (_trailing_pe is None or _trailing_pe <= 0)
                    and _forward_pe is not None and _forward_pe > 0
                )
                if per is not None and per > 0:
                    _pe_src = "Fwd" if per_is_forward else "Trailing"
                    print(f"   [{ticker}] yfinance PER({_pe_src}): {per:.1f}")

                # PEG（成長調整PER）
                peg_raw = info.get("pegRatio") or None
                if peg_raw is not None and peg_raw > 0:
                    peg = float(peg_raw)
                    print(f"   [{ticker}] yfinance PEG: {peg:.2f}")

                # PS（株価売上高倍率）
                ps_raw = info.get("priceToSalesTrailing12Months") or None
                if ps_raw is not None and ps_raw > 0:
                    ps = float(ps_raw)
                    print(f"   [{ticker}] yfinance PS: {ps:.2f}")

                # EV/EBITDA
                ev_ebitda_raw = info.get("enterpriseToEbitda") or None
                if ev_ebitda_raw is not None and ev_ebitda_raw > 0:
                    ev_ebitda = float(ev_ebitda_raw)
                    print(f"   [{ticker}] yfinance EV/EBITDA: {ev_ebitda:.2f}")

                # 200日移動平均
                ma200 = info.get("twoHundredDayAverage") or None
                if ma200 is not None and ma200 > 0:
                    print(f"   [{ticker}] yfinance 200MA: ${ma200:.2f}")

                # Forward EPS（アナリスト予想EPS）
                forward_eps_raw = info.get("forwardEps")
                if forward_eps_raw is not None and isinstance(forward_eps_raw, (int, float)):
                    forward_eps = float(forward_eps_raw)
                    print(f"   [{ticker}] yfinance forwardEps: ${forward_eps:.4f}")

                # 配当（ディビデンドトラップ判定用）
                dividend_yield = info.get("trailingAnnualDividendYield") or 0.0
                payout_ratio   = info.get("payoutRatio") or 0.0
                if dividend_yield > 0:
                    print(f"   [{ticker}] yfinance dividend yield: {dividend_yield:.1%}, payout ratio: {payout_ratio:.1%}")

                # アナリスト目標株価
                _at_median = info.get("targetMedianPrice")
                _at_mean   = info.get("targetMeanPrice")
                _at_low    = info.get("targetLowPrice")
                _at_high   = info.get("targetHighPrice")
                _at_count  = info.get("numberOfAnalystOpinions")
                _at_rec    = info.get("recommendationKey") or ""
                if _at_median is not None and isinstance(_at_median, (int, float)) and _at_median > 0:
                    analyst_target_median = float(_at_median)
                    analyst_target_mean   = float(_at_mean)   if isinstance(_at_mean,  (int, float)) and _at_mean  > 0 else None
                    analyst_target_low    = float(_at_low)    if isinstance(_at_low,   (int, float)) and _at_low   > 0 else None
                    analyst_target_high   = float(_at_high)   if isinstance(_at_high,  (int, float)) and _at_high  > 0 else None
                    analyst_count         = int(_at_count)    if isinstance(_at_count, (int, float)) and _at_count > 0 else None
                    analyst_rec_key       = _at_rec.lower()
                    print(f"   [{ticker}] analyst target median: ${analyst_target_median:.2f} ({analyst_count} analysts)")

            except Exception as e:
                print(f"   [{ticker}] yfinance取得エラー: {e}")
                per = None
                peg = None
                ps = None
                ev_ebitda = None
                ma200 = None
                forward_eps = None
                analyst_target_median = None
                analyst_target_mean = None
                analyst_target_low = None
                analyst_target_high = None
                analyst_count = None
                analyst_rec_key = ""
                dividend_yield = 0.0
                payout_ratio   = 0.0

        # ========================================
        # 3. β決定（beta_config.json > yfinance > セクターデフォルト）
        # ========================================
        final_beta, beta_source = self._determine_beta(ticker, beta, sector)
        
        # ========================================
        # 4. 株式数決定
        # ========================================
        final_shares, shares_source = self._determine_diluted_shares(
            ticker, yf_implied, yf_outstanding, sec_diluted
        )
        
        # ========================================
        # FCF 直近2年平均の計算（CV方式のベース判定用）
        # ========================================
        fcf_2yr_avg = self._calc_fcf_2yr_avg(fcf_list)
        if fcf_2yr_avg > 0:
            print(f"   [{ticker}] SEC FCF 2yr avg: ${fcf_2yr_avg:,.0f}")

        # ========================================
        # 5. BS評価補正データ取得（v8.1: sector確定後に呼ぶ）
        # ========================================
        if self.sec_reader and hasattr(self.sec_reader, 'get_net_cash'):
            try:
                net_cash_data = self.sec_reader.get_net_cash(ticker, sector=sector, industry=industry)
                guard = net_cash_data.get("sector_guard", "none")
                if guard != "none":
                    print(f"   [{ticker}] BS補正 セクターガード: {guard}")
            except Exception as e:
                print(f"   [{ticker}] get_net_cash エラー: {e}")
                net_cash_data = {"net_cash": 0.0, "available": False, "sector_guard": "none"}

        # ========================================
        # 最終サマリー
        # ========================================
        print(f"   [{ticker}] 最終結果:")
        print(f"       FCF 5yr Avg: ${fcf_avg:,.0f}")
        print(f"       FCF 2yr Avg: ${fcf_2yr_avg:,.0f}")
        print(f"       Diluted Shares: {final_shares:,.0f} ({shares_source})")
        print(f"       ROE avg: {f'{roe_avg:.1%}' if roe_avg is not None else 'N/A (負債超過)'}")
        print(f"       Current Price: ${current_price:.2f}")
        print(f"       Revenue: ${revenue:,.0f}")
        print(f"       Beta: {final_beta:.2f} ({beta_source})")
        if rpo > 0:
            print(f"       RPO: ${rpo:,.0f}")

        # ========================================
        # インサイダー取引データ取得（SEC EDGAR Form 4）
        # ========================================
        insider_buy_count: Optional[int] = None
        insider_sell_count: Optional[int] = None
        insider_net_direction: Optional[str] = None
        insider_latest_date: Optional[str] = None
        try:
            import csv as _csv
            _cik_csv = os.path.join(repo_root, "config", "cik_lookup.csv") if repo_root else ""
            if _cik_csv and os.path.exists(_cik_csv):
                _cik = None
                with open(_cik_csv, encoding="utf-8", newline="") as _f:
                    for _row in _csv.DictReader(_f):
                        if _row.get("ticker", "").upper() == ticker.upper():
                            _cik = _row.get("cik", "")
                            break
                if _cik:
                    _insider = self.fetch_insider_trades(ticker, _cik)
                    if _insider is not None:
                        insider_buy_count  = _insider.get("buy_count")
                        insider_sell_count = _insider.get("sell_count")
                        insider_net_direction = _insider.get("net_direction")
                        insider_latest_date   = _insider.get("latest_date")
        except Exception as _ie:
            print(f"   [{ticker}] insider fetch error: {_ie}")

        return {
            "fcf_5yr_avg": fcf_avg,
            "fcf_2yr_avg": fcf_2yr_avg,
            "fcf_list_raw": fcf_list,
            "net_cash_data": net_cash_data,
            "diluted_shares": final_shares,
            "roe_10yr_avg": roe_avg,
            "roe_years_used": roe_years_used,
            "roe_outlier_adj": roe_outlier_adj,
            "current_price": current_price,
            "latest_revenue": revenue,
            "rpo": rpo,
            "beta": final_beta,
            "beta_yf_raw": float(beta) if (beta is not None and beta > 0) else None,
            "sector": sector,
            "industry": industry,
            "per": per,
            "per_is_forward": per_is_forward,
            "peg": peg,
            "ps": ps,
            "ev_ebitda": ev_ebitda,
            "ma200": ma200,
            "forward_eps": forward_eps,
            "analyst_target_median": analyst_target_median,
            "analyst_target_mean": analyst_target_mean,
            "analyst_target_low": analyst_target_low,
            "analyst_target_high": analyst_target_high,
            "analyst_count": analyst_count,
            "analyst_rec_key": analyst_rec_key,
            "dividend_yield": dividend_yield,
            "payout_ratio": payout_ratio,
            "insider_buy_count": insider_buy_count,
            "insider_sell_count": insider_sell_count,
            "insider_net_direction": insider_net_direction,
            "insider_latest_date": insider_latest_date,
            "eps_data": {"ticker": ticker},
            "_shares_source": shares_source,
            "_beta_source": beta_source,
            "fcf_source": fcf_source,
            "fcf_ttm_end": fcf_ttm_end,
            "fcf_ttm_periods": fcf_ttm_periods,
            "rice_annual_data": rice_annual_data,
            "rice_data_source": rice_data_source,
            "rice_sector": self._get_rice_sector(ticker, sector),
        }

    def fetch_insider_trades(self, ticker: str, cik: str, days: int = 90) -> Optional[Dict[str, Any]]:
        """SEC EDGAR Form 4 から直近N日のインサイダー取引(P=買い/S=売り)を集計"""
        import os as _os
        import time
        import xml.etree.ElementTree as ET
        from datetime import datetime, timedelta
        try:
            import requests as _req
        except ImportError:
            return None

        headers = {'User-Agent': 'tanuki-valuation research@example.com'}
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cik_num = cik.lstrip('0') or '0'
        cik_padded = cik_num.zfill(10)

        try:
            r = _req.get(
                f'https://data.sec.gov/submissions/CIK{cik_padded}.json',
                headers=headers, timeout=10
            )
            if r.status_code != 200:
                return None
            sub_data = r.json()
        except Exception:
            return None

        filings = sub_data.get('filings', {}).get('recent', {})
        forms = filings.get('form', [])
        dates = filings.get('filingDate', [])
        accns  = filings.get('accessionNumber', [])
        docs   = filings.get('primaryDocument', [])

        form4_recent = [
            (d, a, doc) for f, d, a, doc in zip(forms, dates, accns, docs)
            if f == '4' and d >= cutoff
        ]

        buy_count = 0
        sell_count = 0
        latest_date: Optional[str] = None

        for filing_date, accn, primary_doc in form4_recent:
            accn_nd = accn.replace('-', '')
            # BUG-INSIDER-1: ファイル名は filer ごとに異なる（form4.xml固定は誤り）。
            # primaryDocument はXSLビューア用パス（xslF345X06/...）を指すことがあり、
            # そのままGETするとHTML整形版が返るため、basenameのみアクセッション直下で取得する
            # （実機検証済み: PLTR/NVDA/TSLA等で生XMLが正しく取得できることを確認）
            fname = _os.path.basename(primary_doc)
            xml_url = (
                f'https://www.sec.gov/Archives/edgar/data/{cik_num}/{accn_nd}/{fname}'
            )
            try:
                time.sleep(0.1)
                r = _req.get(xml_url, headers=headers, timeout=10)
                if r.status_code != 200:
                    continue
                root = ET.fromstring(r.content)
                for txn in root.findall('.//nonDerivativeTransaction'):
                    code_el = txn.find('.//transactionCode')
                    code = code_el.text.strip() if code_el is not None and code_el.text else ''
                    if code == 'P':
                        buy_count += 1
                    elif code == 'S':
                        sell_count += 1
                if latest_date is None or filing_date > latest_date:
                    latest_date = filing_date
            except Exception:
                continue

        total = buy_count + sell_count
        if total == 0:
            net_direction = "中立"
        elif buy_count > sell_count:
            net_direction = "Buy優勢"
        elif sell_count > buy_count:
            net_direction = "Sell優勢"
        else:
            net_direction = "中立"

        print(f"   [{ticker}] insider trades (90d): buy={buy_count}, sell={sell_count} → {net_direction}")
        return {
            "buy_count": buy_count,
            "sell_count": sell_count,
            "net_direction": net_direction,
            "latest_date": latest_date,
        }

    def _get_rice_sector(self, ticker: str, yf_sector: str) -> str:
        """RICE除外判定用セクター取得。beta_config.jsonのrice_sectorを優先する。"""
        override = self._beta_overrides.get(ticker, {}).get("rice_sector", "")
        if override:
            print(f"   [{ticker}] RICE sector override: {yf_sector} → {override}")
            return override
        return yf_sector
    
    def _calc_fcf_2yr_avg(self, fcf_list: list) -> float:
        """
        FCFリストから直近2年平均を計算

        fcf_listはget_fcf_list()の返却値（新しい順、インデックス0が最新）。
        最新2件はリストの先頭[:2]で取得する。
        2件未満の場合は0.0を返す。
        """
        if not fcf_list or len(fcf_list) < 2:
            return 0.0
        # fcf_listは新しい順（fcf_list[0]が直近）→ 先頭2件が直近2年
        recent_2 = fcf_list[:2]
        if all(v is not None for v in recent_2):
            return sum(recent_2) / 2
        return 0.0

    def _determine_beta(
        self,
        ticker: str,
        yf_beta: float,
        sector: str
    ) -> Tuple[float, str]:
        """
        β（ベータ）を決定

        優先順位:
        1. beta_config.json の overrides（Koichi意図β）
        2. yfinanceのβ（0.1〜3.0の範囲内）
        3. セクター別デフォルトβ
        4. 全体デフォルト（1.0）
        """
        # ── 1. beta_config.json オーバーライド（最優先） ──
        override = self._beta_overrides.get(ticker)
        if override and isinstance(override.get("beta"), (int, float)):
            beta_val = float(override["beta"])
            reason   = override.get("reason", "")
            sector_label = override.get("sector", "")
            print(f"   [{ticker}] → beta_config.json採用: β={beta_val:.2f} ({sector_label})")
            if reason:
                print(f"   [{ticker}]   理由: {reason}")
            return beta_val, f"beta_config({sector_label})"

        # ── 2. yfinanceのβ（有効範囲: 0.1〜3.0） ──
        if yf_beta is not None and 0.1 <= yf_beta <= 3.0:
            return float(yf_beta), "yfinance"

        # ── 3. セクター別デフォルト ──
        sector_beta = SECTOR_DEFAULT_BETA.get(sector)
        if sector_beta:
            print(f"   [{ticker}] → セクターデフォルトβ採用: {sector} = {sector_beta}")
            return float(sector_beta), f"sector_{sector}"

        # ── 4. 全体デフォルト ──
        default_beta = SECTOR_DEFAULT_BETA["default"]
        print(f"   [{ticker}] → デフォルトβ採用: {default_beta}")
        return float(default_beta), "default"
    
    def _determine_diluted_shares(
        self, 
        ticker: str,
        yf_implied: int, 
        yf_outstanding: int, 
        sec_diluted: int
    ) -> Tuple[int, str]:
        """完全希薄化後株式数を決定"""
        MIN_SHARES = 100_000
        
        if yf_implied > MIN_SHARES:
            print(f"   [{ticker}] → yfinance implied採用（完全希薄化後）")
            return int(yf_implied), "yf_implied"
        
        has_sec = sec_diluted > MIN_SHARES
        has_yf = yf_outstanding > MIN_SHARES
        
        if has_sec and has_yf:
            ratio = yf_outstanding / sec_diluted
            
            if ratio > 5:
                print(f"   [{ticker}] ⚠️ 大規模増資検出: yf={yf_outstanding:,.0f} vs SEC={sec_diluted:,.0f} (×{ratio:.1f})")
                print(f"   [{ticker}] → yfinance outstanding採用（増資後の現在値）")
                return int(yf_outstanding), "yf_outstanding_post_dilution"
            elif ratio < 0.2:
                print(f"   [{ticker}] → SEC diluted採用")
                return int(sec_diluted), "sec_diluted"
            else:
                max_shares = max(sec_diluted, yf_outstanding)
                source = "max_sec" if sec_diluted >= yf_outstanding else "max_yf"
                print(f"   [{ticker}] → max採用: {max_shares:,.0f} ({source})")
                return int(max_shares), source
        
        if has_yf:
            print(f"   [{ticker}] → yfinance outstanding採用")
            return int(yf_outstanding), "yf_outstanding"
        
        if has_sec:
            print(f"   [{ticker}] → SEC diluted採用")
            return int(sec_diluted), "sec_diluted"
        
        print(f"   [{ticker}] ⚠️ 株式数取得不可")
        return 0, "none"
