"""
SEC データリーダー
各ツール（Adjusted EPS Analyzer, TANUKI VALUATION等）からのアクセス用インターフェース
"""

import json
import os
from typing import Optional, Dict, Any, List

from .config import TICKERS, get_ticker_info


class SECReader:
    """SECデータ読み取りインターフェース"""
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    # =========================================
    # 年次データ取得
    # =========================================
    
    def get_annual(self, ticker: str, year: int) -> Optional[Dict[str, Any]]:
        """
        年次データ取得
        
        Args:
            ticker: ティッカーシンボル
            year: 年度（例: 2024）
        
        Returns:
            dict: {
                "ticker": "TSLA",
                "period": 2024,
                "form": "10-K",
                "bs": {"total_assets": ..., "stockholders_equity": ..., ...},
                "pl": {"revenue": ..., "net_income": ..., "eps_diluted": ...},
                "cf": {"operating_cash_flow": ..., "capital_expenditure": ..., "free_cash_flow": ...},
                "shares": {"shares_diluted": ..., "shares_basic": ...}
            }
        """
        ticker = ticker.upper()
        path = os.path.join(self.data_dir, ticker, f"annual_{year}.json")
        return self._load_json(path)
    
    def get_annual_range(self, ticker: str, years: int = 5) -> List[Dict[str, Any]]:
        """
        直近N年分の年次データ取得
        
        Args:
            ticker: ティッカーシンボル
            years: 取得年数（デフォルト5年）
        
        Returns:
            list: 年次データのリスト（新しい順）
        """
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.data_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            return []
        
        # 利用可能な年次ファイルを検索
        results = []
        files = sorted(os.listdir(ticker_dir), reverse=True)
        
        for f in files:
            if f.startswith("annual_") and f.endswith(".json"):
                data = self._load_json(os.path.join(ticker_dir, f))
                if data:
                    results.append(data)
                    if len(results) >= years:
                        break
        
        return results
    
    # =========================================
    # 四半期データ取得
    # =========================================
    
    def get_quarterly(self, ticker: str, quarter: str) -> Optional[Dict[str, Any]]:
        """
        四半期データ取得
        
        Args:
            ticker: ティッカーシンボル
            quarter: 四半期（例: "2024Q1"）
        
        Returns:
            dict: 四半期財務データ
        """
        ticker = ticker.upper()
        path = os.path.join(self.data_dir, ticker, f"quarterly_{quarter}.json")
        return self._load_json(path)
    
    def get_quarterly_range(self, ticker: str, quarters: int = 8) -> List[Dict[str, Any]]:
        """
        直近N四半期分のデータ取得
        
        Args:
            ticker: ティッカーシンボル
            quarters: 取得四半期数（デフォルト8）
        
        Returns:
            list: 四半期データのリスト（新しい順）
        """
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.data_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            return []
        
        results = []
        files = sorted(os.listdir(ticker_dir), reverse=True)
        
        for f in files:
            if f.startswith("quarterly_") and f.endswith(".json"):
                data = self._load_json(os.path.join(ticker_dir, f))
                if data:
                    results.append(data)
                    if len(results) >= quarters:
                        break
        
        return results
    
    # =========================================
    # TANUKI VALUATION用ヘルパー
    # =========================================
    
    def get_fcf_5yr_avg(self, ticker: str) -> float:
        """FCF 5年平均を取得"""
        annual_data = self.get_annual_range(ticker, 5)
        
        fcf_list = []
        for data in annual_data:
            fcf = data.get("cf", {}).get("free_cash_flow")
            if fcf is not None:
                fcf_list.append(fcf)
        
        return sum(fcf_list) / len(fcf_list) if fcf_list else 0.0
    
    def get_roe_avg(self, ticker: str, years: int = 10) -> float:
        """
        ROE平均を取得（純利益÷株主資本）
        赤字年度を含まない直近の連続黒字期間のみ使用
        """
        annual_data = self.get_annual_range(ticker, years)
        
        roe_list = []
        for data in annual_data:
            net_income = data.get("pl", {}).get("net_income")
            equity = data.get("bs", {}).get("stockholders_equity")
            
            if net_income is not None and equity and equity > 0:
                if net_income > 0:
                    # 黒字年度のみ追加
                    roe = net_income / equity
                    roe_list.append(roe)
                else:
                    # 赤字に到達したら打ち切り（直近連続黒字のみ使用）
                    break
        
        return sum(roe_list) / len(roe_list) if roe_list else 0.0
    
    def get_diluted_shares(self, ticker: str) -> int:
        """
        直近の希薄化後株式数を取得
        100万株未満の場合は異常値とみなし、shares_basicを試行
        """
        annual_data = self.get_annual_range(ticker, 1)
        
        if annual_data:
            shares_data = annual_data[0].get("shares", {})
            shares_diluted = shares_data.get("shares_diluted", 0)
            shares_basic = shares_data.get("shares_basic", 0)
            
            # 希薄化後株式数が100万以上なら使用
            if shares_diluted and shares_diluted >= 1_000_000:
                return int(shares_diluted)
            
            # 100万未満の場合、basicsを試行
            if shares_basic and shares_basic >= 1_000_000:
                return int(shares_basic)
            
            # それでも小さい場合、大きい方を返す（異常値の可能性あり）
            return int(max(shares_diluted or 0, shares_basic or 0))
        
        return 0
    
    def get_latest_revenue(self, ticker: str) -> float:
        """直近の売上高を取得"""
        annual_data = self.get_annual_range(ticker, 1)
        
        if annual_data:
            revenue = annual_data[0].get("pl", {}).get("revenue")
            if revenue:
                return float(revenue)
        
        return 0.0
    
    def get_fcf_list(self, ticker: str, years: int = 5) -> List[float]:
        """FCFリストを取得（新しい順、fcf_list[0]が直近）"""
        annual_data = self.get_annual_range(ticker, years)
        # annual_data は新しい順（get_annual_range の仕様）なのでそのまま使用
        fcf_list = []
        for data in annual_data:
            fcf = data.get("cf", {}).get("free_cash_flow")
            if fcf is not None:
                fcf_list.append(fcf)
        
        return fcf_list
    
    def get_rpo(self, ticker: str) -> float:
        """直近のRPO（残存履行義務）を取得 - SaaS企業向け"""
        annual_data = self.get_annual_range(ticker, 1)

        if annual_data:
            rpo = annual_data[0].get("other", {}).get("rpo")
            if rpo:
                return float(rpo)

        return 0.0

    def get_rpo_series(self, ticker: str, quarters: int = 8) -> list[dict]:
        """
        normalizedデータからRPO時系列を返す（直近quarters件、昇順）
        戻り値: [{"period": "2025-03", "rpo": 242800000000}, ...]  古→新順
        normalizedがない場合は[]を返す
        rpo_series[-1] が最新、rpo_series[-5] が約4四半期前
        """
        ticker = ticker.upper()
        normalized_dir = os.path.join(os.path.dirname(__file__), "normalized")
        path = os.path.join(normalized_dir, f"{ticker}_quarterly_normalized.json")

        normalized = self._load_json(path)
        if not normalized:
            return []

        rpo_entries = normalized.get("fields", {}).get("RPO", [])
        q_entries = [e for e in rpo_entries if not e.get("is_annual")]
        # 昇順ソート後、直近quarters件を取得（[-1]が最新になる）
        q_entries = sorted(q_entries, key=lambda x: x["end"])[-quarters:]

        return [
            {"period": e["end"][:7], "rpo": e["val"]}
            for e in q_entries
        ]

    def get_rpo_context(self, ticker: str) -> dict:
        """
        RPO補正に必要なコンテキストをnormalizedから計算して返す

        戻り値:
            rev_yoy    : Revenue前年比成長率（TTMベース, 8四半期以上で計算）
            rev_ttm    : TTM Revenue
            op_margin  : TTM営業利益率（OperatingIncome/Revenue）
            rpo_series : RPO時系列（昇順、get_rpo_series()と同一）
        """
        ticker = ticker.upper()
        normalized_dir = os.path.join(os.path.dirname(__file__), "normalized")
        path = os.path.join(normalized_dir, f"{ticker}_quarterly_normalized.json")

        normalized = self._load_json(path)
        if not normalized:
            return {"rev_yoy": None, "rev_ttm": None, "op_margin": None, "rpo_series": []}

        fields = normalized.get("fields", {})

        def _q_sorted(field_name: str) -> list:
            return sorted(
                [e for e in fields.get(field_name, []) if not e.get("is_annual")],
                key=lambda x: x["end"],
            )

        # TTM Revenue（直近4四半期合計）
        rev_all = _q_sorted("Revenue")
        rev_ttm: Optional[float] = None
        rev_yoy: Optional[float] = None
        if len(rev_all) >= 4:
            rev_ttm = sum(e["val"] for e in rev_all[-4:])
            if len(rev_all) >= 8:
                rev_yago_ttm = sum(e["val"] for e in rev_all[-8:-4])
                if rev_yago_ttm > 0:
                    rev_yoy = (rev_ttm - rev_yago_ttm) / rev_yago_ttm

        # TTM OperatingIncome → op_margin
        oi_all = _q_sorted("OperatingIncome")
        op_margin: Optional[float] = None
        if len(oi_all) >= 4 and rev_ttm and rev_ttm > 0:
            oi_ttm = sum(e["val"] for e in oi_all[-4:])
            op_margin = oi_ttm / rev_ttm

        return {
            "rev_yoy":    rev_yoy,
            "rev_ttm":    rev_ttm,
            "op_margin":  op_margin,
            "rpo_series": self.get_rpo_series(ticker),
        }

    def get_net_cash(self, ticker: str, sector: Optional[str] = None, industry: str = "") -> dict:
        """
        ネットキャッシュ関連BSデータを取得 v8.1

        ネットキャッシュ = (現金 + 短期投資) - (長期有利子負債 + 短期有利子負債)
        プラス → 純キャッシュ（負債より現金が多い）
        マイナス → 純負債（負債が現金を上回る）

        v8.1追加: セクターガード
          - 保険 (Insurance): 有利子負債フィールドに保険準備金が混入するリスクあり
            → net_cash計算では負債側を0とし、現金のみで近似（保守的）
          - Fintech (Financial Services): DebtCurrent等に顧客預金が混入するリスク
            → long_term_debt のみを使用（short_term_debtを除外）

        Returns:
            {
                "cash":                   float
                "short_term_investments": float
                "long_term_debt":         float
                "short_term_debt":        float
                "net_cash":               float  ネットキャッシュ（符号付き）
                "fiscal_year":            int    取得会計年度
                "available":              bool   データ取得成功フラグ
                "sector_guard":           str    適用したセクターガード名（v8.1）
            }
        """
        annual_data = self.get_annual_range(ticker, years=1)
        if not annual_data:
            return {
                "cash": 0.0, "short_term_investments": 0.0,
                "long_term_debt": 0.0, "short_term_debt": 0.0,
                "net_cash": 0.0, "fiscal_year": 0, "available": False,
                "sector_guard": "none",
            }

        latest = annual_data[0]
        bs = latest.get("bs", {})

        try:
            fy = int(latest.get("period", 0))
        except (ValueError, TypeError):
            fy = 0

        cash    = bs.get("cash_and_equivalents", 0) or 0
        st_inv  = bs.get("short_term_investments", 0) or 0
        lt_debt = bs.get("long_term_debt", 0) or 0
        st_debt = bs.get("short_term_debt", 0) or 0

        # ── セクターガード（v8.1: industry優先判定）──
        # _is_insurance()と同じロジックをここで直接適用
        # （adjustments.pyのimportを避けるため複製）
        def _is_insurance_local(t: str, s: Optional[str], ind: str) -> bool:
            if ind:
                ind_lower = ind.lower()
                if "insurance" in ind_lower or "managed health" in ind_lower:
                    return True
            INSURANCE_TICKERS = {
                "UNH", "CVS", "CI", "HUM", "ELV", "CNC", "MOH",
                "MET", "PRU", "AFL", "ALL", "TRV", "CB", "HIG",
                "PGR", "AIZ", "CINF", "AIG", "L", "GL",
            }
            if t.upper() in INSURANCE_TICKERS:
                return True
            return s == "Insurance"

        sector_guard = "none"
        if _is_insurance_local(ticker, sector, industry):
            lt_debt = 0.0
            st_debt = 0.0
            sector_guard = "insurance_liabilities_excluded"
        elif sector == "Financial Services":
            st_debt = 0.0
            sector_guard = "fintech_st_debt_excluded"

        net_cash = (cash + st_inv) - (lt_debt + st_debt)
        available = any([cash, st_inv, lt_debt, st_debt])

        return {
            "cash":                   float(cash),
            "short_term_investments": float(st_inv),
            "long_term_debt":         float(lt_debt),
            "short_term_debt":        float(st_debt),
            "net_cash":               float(net_cash),
            "fiscal_year":            fy,
            "available":              available,
            "sector_guard":           sector_guard,
        }

    # =========================================
    # Adjusted EPS Analyzer用ヘルパー
    # =========================================
    
    def get_eps_diluted(self, ticker: str, quarter: str) -> Optional[float]:
        """四半期EPSを取得"""
        data = self.get_quarterly(ticker, quarter)
        if data:
            return data.get("pl", {}).get("eps_diluted")
        return None
    
    # =========================================
    # ユーティリティ
    # =========================================
    
    def _load_json(self, path: str) -> Optional[Dict[str, Any]]:
        """JSONファイル読み込み"""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    
    def get_available_tickers(self) -> List[str]:
        """データが存在するティッカー一覧"""
        if not os.path.exists(self.data_dir):
            return []
        
        tickers = []
        for name in os.listdir(self.data_dir):
            path = os.path.join(self.data_dir, name)
            if os.path.isdir(path) and not name.startswith("_"):
                tickers.append(name)
        
        return sorted(tickers)
    
    def get_data_summary(self, ticker: str) -> Dict[str, Any]:
        """ティッカーのデータサマリー"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.data_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            return {"error": "データなし"}
        
        files = os.listdir(ticker_dir)
        annual_files = [f for f in files if f.startswith("annual_")]
        quarterly_files = [f for f in files if f.startswith("quarterly_")]
        
        info = get_ticker_info(ticker)
        
        return {
            "ticker": ticker,
            "name": info["name"],
            "status": info["status"],
            "annual_count": len(annual_files),
            "quarterly_count": len(quarterly_files),
            "has_company_facts": "company_facts.json" in files,
        }


# シングルトンインスタンス
_reader = None

def get_reader() -> SECReader:
    """グローバルリーダーインスタンス取得"""
    global _reader
    if _reader is None:
        _reader = SECReader()
    return _reader


if __name__ == "__main__":
    reader = SECReader()
    
    # テスト
    print("=== 利用可能ティッカー ===")
    print(reader.get_available_tickers())
    
    print("\n=== TSLA サマリー ===")
    print(reader.get_data_summary("TSLA"))
    
    print("\n=== TSLA FCF 5年平均 ===")
    print(f"${reader.get_fcf_5yr_avg('TSLA'):,.0f}")
    
    print("\n=== TSLA ROE平均 ===")
    print(f"{reader.get_roe_avg('TSLA'):.1%}")
