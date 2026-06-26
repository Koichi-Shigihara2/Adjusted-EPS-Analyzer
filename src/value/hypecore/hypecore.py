"""
HypeCore PoC v2 - src/value/hypecore/poc.py

ステージ定義（Koichi定義準拠）:
  S0 失望/蓄積期: 機関未参入・規模小・赤字頻発・スマートマネー仕込み段階
  S1 期待覚醒期:  EPS上方修正・出来高急増・MA50突破・新カタリスト出現
  S2 期待拡大期:  マルチプル拡大・機関積み増し・カタリスト連発・黒字定着
  S3 陶酔期:      RSI過熱・PER異常・insider売り・良ニュースで株価反応鈍化
  S4 期待剥落期:  ガイダンス下方修正・良決算でも下落・機関Distribution開始
"""

import json
import warnings
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# ── パス設定 ──────────────────────────────────────────────
_HERE      = Path(__file__).resolve().parent
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TANUKI_DIR = _REPO_ROOT / "docs" / "value-monitor" / "tanuki_valuation" / "data"
_NORM_DIR   = _REPO_ROOT / "common" / "sec_data" / "normalized"
_OUT_DIR    = _HERE / "data"
_OUT_DIR.mkdir(exist_ok=True, parents=True)

# ── ステージ定義 ──────────────────────────────────────────
STAGE_LABELS = {
    0: "失望/蓄積期",
    1: "期待覚醒期",
    2: "期待拡大期",
    3: "陶酔期",
    4: "期待剥落期",
}

# 正解ラベル（PLTR・月次・Koichi感覚値）
PLTR_GROUND_TRUTH = {
    "2024-01": 2, "2024-02": 3, "2024-03": 3,
    "2024-04": 2, "2024-05": 2, "2024-06": 3,
    "2024-07": 3, "2024-08": 3, "2024-09": 3,
    "2024-10": 3, "2024-11": 3, "2024-12": 3,
    "2025-01": 3, "2025-02": 3, "2025-03": 3,
    "2025-04": 3, "2025-05": 3, "2025-06": 3,
    "2025-07": 3, "2025-08": 3, "2025-09": 3,
    "2025-10": 3, "2025-11": 4, "2025-12": 4,
    "2026-01": 4, "2026-02": 4, "2026-03": 4,
    "2026-04": 4, "2026-05": 4,
}


def z_score_series(s: pd.Series, window: int = 24) -> pd.Series:
    """ローリングZ-score（自分自身の過去window期間を基準）"""
    s = s.replace([np.inf, -np.inf], np.nan)
    roll_mean = s.rolling(window, min_periods=6).mean()
    roll_std  = s.rolling(window, min_periods=6).std()
    return (s - roll_mean) / (roll_std + 1e-9)


# ── データ取得 ────────────────────────────────────────────

def fetch_price_data(ticker: str, start: str = "2021-01-01") -> pd.DataFrame:
    """yfinanceから日次株価・出来高を取得し月次に集約"""
    t = yf.Ticker(ticker)
    hist = t.history(start=start, auto_adjust=True)
    if hist.empty:
        raise ValueError(f"{ticker}: 株価データ取得失敗")

    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    hist = hist[["Close", "Volume"]].rename(columns={"Close": "price", "Volume": "volume"})

    monthly = hist.resample("ME").agg({"price": "last", "volume": "mean"})
    monthly.index = monthly.index.to_period("M").to_timestamp()

    # テクニカル指標（日次計算→月末値）
    hist["ma50"]  = hist["price"].rolling(50).mean()
    hist["ma200"] = hist["price"].rolling(200).mean()

    delta = hist["price"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    hist["rsi"] = 100 - 100 / (1 + gain / (loss + 1e-9))

    hist["ma50_dev"]  = (hist["price"] - hist["ma50"])  / (hist["ma50"]  + 1e-9) * 100
    hist["ma200_dev"] = (hist["price"] - hist["ma200"]) / (hist["ma200"] + 1e-9) * 100

    # 出来高比（日次平均出来高との比較）
    hist["vol_20d_avg"] = hist["volume"].rolling(20).mean()
    hist["volume_ratio"] = hist["volume"] / (hist["vol_20d_avg"] + 1e-9)

    tech = hist[["ma50_dev", "ma200_dev", "rsi", "volume_ratio"]].resample("ME").last()
    tech.index = tech.index.to_period("M").to_timestamp()

    # 月次出来高（月平均）
    vol_monthly = hist[["volume"]].resample("ME").mean()
    vol_monthly.index = vol_monthly.index.to_period("M").to_timestamp()
    vol_monthly.columns = ["volume_monthly"]

    return monthly.join(tech).join(vol_monthly)


def fetch_info_snapshot(ticker: str) -> dict:
    """yfinance .infoから現時点のバリュエーション・アナリスト情報を取得"""
    info = yf.Ticker(ticker).info
    avg_vol = info.get("averageVolume") or info.get("averageVolume10days") or 1
    cur_vol = info.get("volume") or avg_vol
    return {
        "forward_pe":         info.get("forwardPE"),
        "trailing_pe":        info.get("trailingPE"),
        "psr":                info.get("priceToSalesTrailing12Months"),
        "peg_ratio":          info.get("pegRatio"),
        "revenue_growth":     info.get("revenueGrowth"),        # YoY (小数)
        "earnings_growth":    info.get("earningsGrowth"),       # YoY (小数)
        "gross_margins":      info.get("grossMargins"),
        "recommendation_mean": info.get("recommendationMean"),  # 1=Strong Buy, 5=Sell
        "num_analysts":       info.get("numberOfAnalystOpinions"),
        "short_pct_float":    info.get("shortPercentOfFloat"),
        "short_ratio":        info.get("shortRatio"),
        "volume_vs_avg":      cur_vol / avg_vol if avg_vol else None,
        "market_cap":         info.get("marketCap"),
        "shares":             info.get("sharesOutstanding"),
        "ev_ebitda":          info.get("enterpriseToEbitda"),  # 負値も格納（UIで変換）
    }


def fetch_quarterly_fundamentals(ticker: str) -> pd.DataFrame:
    """normalizedJSONから四半期財務データを取得し月次補間"""
    norm_path = _NORM_DIR / f"{ticker}_quarterly_normalized.json"
    if not norm_path.exists():
        print(f"  警告: normalizedファイルなし: {norm_path}")
        return pd.DataFrame()

    with open(norm_path, encoding="utf-8") as f:
        norm = json.load(f)

    fields = norm.get("fields", {})

    def extract(fname: str) -> pd.Series:
        entries = [
            e for e in fields.get(fname, [])
            if not e.get("is_annual") and not e.get("is_ytd") and e.get("val") is not None
        ]
        if not entries:
            return pd.Series(dtype=float)
        df = pd.DataFrame(entries)[["end", "val"]].copy()
        df["end"] = pd.to_datetime(df["end"])
        return df.set_index("end").sort_index()["val"]

    rev = extract("Revenue")
    ni  = extract("NetIncome")
    ocf = extract("OCF")

    if rev.empty:
        return pd.DataFrame()

    rev_ttm       = rev.rolling(4).sum()
    rev_ttm_prior = rev_ttm.shift(4).replace(0, np.nan)
    rev_yoy       = (rev_ttm / rev_ttm_prior - 1) * 100
    ni_yoy     = ni.pct_change(4) * 100 if not ni.empty else pd.Series(dtype=float)
    op_margin  = (ni / rev.replace(0, np.nan) * 100) if (not ni.empty) else pd.Series(dtype=float)
    rule40     = rev_yoy + op_margin if not op_margin.empty else pd.Series(dtype=float)

    result = pd.DataFrame({
        "rev_yoy":   rev_yoy,
        "ni_yoy":    ni_yoy,
        "rule40":    rule40,
        "ocf":       ocf,
        "revenue":   rev,
    }).dropna(how="all")

    result.index = pd.to_datetime(result.index)
    monthly_idx = pd.date_range(
        start=result.index.min(),
        end=date.today().isoformat(),
        freq="MS"
    )
    return result.reindex(monthly_idx, method="ffill")


def fetch_tanuki_iv(ticker: str) -> pd.Series:
    """TANUKI history + latestからIV時系列を取得"""
    ticker_dir = _TANUKI_DIR / ticker
    iv_series = {}

    history_dir = ticker_dir / "history"
    if history_dir.exists():
        for f in sorted(history_dir.glob("*.json")):
            try:
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                iv = d.get("intrinsic_value_per_share") or d.get("iv_per_share")
                calc_date = d.get("calculation_date") or f.stem
                if iv and calc_date:
                    ts = pd.Timestamp(calc_date[:10]).to_period("M").to_timestamp()
                    iv_series[ts] = float(iv)
            except Exception:
                continue

    latest_path = ticker_dir / "latest.json"
    if latest_path.exists():
        with open(latest_path, encoding="utf-8") as f:
            d = json.load(f)
        iv = d.get("intrinsic_value_per_share") or d.get("iv_per_share")
        if iv:
            today = pd.Timestamp(date.today()).to_period("M").to_timestamp()
            iv_series[today] = float(iv)

    if iv_series:
        s = pd.Series(iv_series).sort_index()
        print(f"  TANUKI IV: {len(s)}件 最新=${s.iloc[-1]:.2f}")
        return s

    print(f"  警告: {ticker} のTANUKI IVが見つかりません")
    return pd.Series(dtype=float)


def fetch_analyst_history(ticker: str) -> pd.DataFrame:
    """
    yfinanceからアナリスト履歴を月次DataFrameに変換。

    取得データ:
      upgrades_downgrades → 月次アナリスト修正率（上方/下方）
      earnings_history    → 四半期EPSサプライズ率
      recommendations     → 直近Buy/Hold/Sell比率（現時点値）

    返却列:
      analyst_upgrade_rate : 上方修正/(上方+下方) 3ヶ月移動平均
      analyst_downgrade_rate: 下方修正率
      eps_surprise         : EPSサプライズ率% (四半期→月次前方補完)
      buy_hold_ratio       : (StrongBuy+Buy)/全アナリスト (現時点値のみ)
      sell_on_good_news    : EPSサプライズ>0 かつ 当月株価変化<-3% (bool→float)
    """
    t = yf.Ticker(ticker)
    result = pd.DataFrame()

    # ── 1. upgrades_downgrades → 月次修正率 ──────────────────
    try:
        ud = t.upgrades_downgrades
        if ud is not None and not ud.empty:
            ud = ud.copy()
            ud.index = pd.to_datetime(ud.index).tz_localize(None)

            # ToGradeでBuy系/Sell系を分類
            BUY_GRADES  = {"Buy","Strong Buy","Outperform","Overweight","Market Outperform","Positive"}
            SELL_GRADES = {"Sell","Strong Sell","Underperform","Underweight","Market Underperform","Negative"}

            ud["is_upgrade"]   = ud["ToGrade"].isin(BUY_GRADES).astype(int)
            ud["is_downgrade"] = ud["ToGrade"].isin(SELL_GRADES).astype(int)

            monthly_ud = ud.resample("ME").agg(
                upgrades=("is_upgrade", "sum"),
                downgrades=("is_downgrade", "sum"),
            )
            monthly_ud.index = monthly_ud.index.to_period("M").to_timestamp()
            monthly_ud["total_changes"] = monthly_ud["upgrades"] + monthly_ud["downgrades"]
            monthly_ud["analyst_upgrade_rate"] = (
                monthly_ud["upgrades"] / (monthly_ud["total_changes"] + 1e-9)
            )
            monthly_ud["analyst_downgrade_rate"] = (
                monthly_ud["downgrades"] / (monthly_ud["total_changes"] + 1e-9)
            )
            # 3ヶ月移動平均でノイズ除去
            monthly_ud["analyst_upgrade_rate"] = (
                monthly_ud["analyst_upgrade_rate"].rolling(3, min_periods=1).mean()
            )
            result = monthly_ud[["analyst_upgrade_rate", "analyst_downgrade_rate"]]
            print(f"  アナリスト修正: {len(ud)}件（{ud.index.min().date()}〜）")
    except Exception as e:
        print(f"  警告: upgrades_downgrades取得失敗: {e}")

    # ── 2. earnings_history → 四半期EPSサプライズ率 ──────────
    eps_fetched = False
    try:
        eh = t.earnings_history
        if eh is not None and not eh.empty:
            eh = eh.copy()
            eh.index = pd.to_datetime(eh.index).tz_localize(None)
            eh_monthly = eh[["surprisePercent"]].copy()
            eh_monthly.columns = ["eps_surprise"]
            eh_monthly["eps_surprise"] *= 100  # 小数→%
            if not result.empty:
                monthly_idx = result.index
            else:
                monthly_idx = pd.date_range(
                    start=eh_monthly.index.min(),
                    end=date.today().isoformat(),
                    freq="MS"
                )
            eps_monthly = eh_monthly.reindex(monthly_idx, method="ffill", limit=4)
            # 最新月がNullの場合、最後の有効値で補完
            if "eps_surprise" in eps_monthly.columns:
                eps_monthly["eps_surprise"] = eps_monthly["eps_surprise"].ffill()
            if result.empty:
                result = eps_monthly
            else:
                result = result.join(eps_monthly, how="outer")
            print(f"  EPSサプライズ: {len(eh)}件")
            eps_fetched = True
    except Exception as e:
        print(f"  警告: earnings_history取得失敗: {e}")

    # フォールバック①: quarterly_earnings から surprisePercent を取得
    if not eps_fetched:
        try:
            qe = t.quarterly_earnings
            if qe is not None and not qe.empty and "Surprise(%)" in qe.columns:
                qe = qe.copy()
                qe.index = pd.to_datetime(qe.index).tz_localize(None)
                qe_monthly = qe[["Surprise(%)"]].rename(columns={"Surprise(%)": "eps_surprise"})
                if not result.empty:
                    monthly_idx = result.index
                    eps_monthly = qe_monthly.reindex(monthly_idx, method="ffill")
                    result = result.join(eps_monthly, how="left")
                print(f"  EPSサプライズ(fallback1): {len(qe)}件")
                eps_fetched = True
        except Exception as e:
            print(f"  警告: quarterly_earnings取得失敗: {e}")

    # フォールバック②: info['earningsGrowth'] を欠損月のみに適用
    if not eps_fetched:
        try:
            info_snap = t.info
            eg = info_snap.get("earningsGrowth")
            if eg is not None:
                eg_val = round(float(eg) * 100, 2)
                if not result.empty:
                    if "eps_surprise" not in result.columns:
                        result["eps_surprise"] = eg_val
                    else:
                        result["eps_surprise"] = result["eps_surprise"].fillna(eg_val)
                print(f"  EPSサプライズ(fallback2/earningsGrowth): {eg:.1%}")
                eps_fetched = True
        except Exception as e:
            print(f"  警告: earningsGrowth取得失敗: {e}")

    # 最終補完: eps_surpriseのNullを前方補完（最大3ヶ月）
    if not result.empty and "eps_surprise" in result.columns:
        result["eps_surprise"] = result["eps_surprise"].ffill(limit=3)

    if not eps_fetched:
        print(f"  警告: EPSサプライズ全手段で取得失敗")

    # ── 3. recommendations → Buy/Hold/Sell比率（現時点） ──────
    try:
        rec = t.recommendations
        if rec is not None and not rec.empty:
            # 直近月（0m）のデータ
            cur = rec[rec["period"] == "0m"].iloc[0] if len(rec[rec["period"] == "0m"]) > 0 else rec.iloc[0]
            total = (cur.get("strongBuy", 0) + cur.get("buy", 0) +
                     cur.get("hold", 0) + cur.get("sell", 0) + cur.get("strongSell", 0))
            buy_ratio = (cur.get("strongBuy", 0) + cur.get("buy", 0)) / (total + 1e-9)
            # 現時点値を全期間に設定（将来は月次記録で上書き）
            if "buy_hold_ratio" not in result.columns:
                result["buy_hold_ratio"] = np.nan
            today_ts = pd.Timestamp(date.today()).to_period("M").to_timestamp()
            if today_ts in result.index:
                result.loc[today_ts, "buy_hold_ratio"] = buy_ratio
            print(f"  Buy比率: {buy_ratio:.1%}（現時点）")
    except Exception as e:
        print(f"  警告: recommendations取得失敗: {e}")

    return result


# ── スコア計算 ────────────────────────────────────────────

def compute_scores(ticker: str) -> pd.DataFrame:
    """全指標を月次DataFrameに統合"""
    print(f"\n[{ticker}] データ取得中...")

    price_df = fetch_price_data(ticker, start="2021-01-01")
    print(f"  株価: {len(price_df)}ヶ月分")

    fund_df = fetch_quarterly_fundamentals(ticker)
    print(f"  財務: {len(fund_df)}行")

    iv_series = fetch_tanuki_iv(ticker)

    # アナリスト履歴（月次）
    analyst_df = fetch_analyst_history(ticker)

    # .info（現時点値）
    info = fetch_info_snapshot(ticker)
    _fpe = info.get('forward_pe')
    print(f"  .info: ForwardPE={_fpe:.1f} PEG={info.get('peg_ratio')} "
          f"RevGrowth={info.get('revenue_growth')}"
          if _fpe is not None else
          f"  .info: ForwardPE=N/A PEG={info.get('peg_ratio')} "
          f"RevGrowth={info.get('revenue_growth')}")

    # 結合
    df = price_df.copy()
    if not fund_df.empty:
        df = df.join(fund_df, how="left")

    # IV乖離率（時系列）
    if not iv_series.empty:
        iv_monthly = iv_series.reindex(df.index, method="ffill")
        df["iv"] = iv_monthly
        df["price_iv_ratio"] = df["price"] / df["iv"]
    else:
        df["price_iv_ratio"] = np.nan

    # FCF Yield
    shares = info.get("shares")
    if shares and "ocf" in df.columns:
        df["fcf_yield"] = df["ocf"] / (df["price"] * shares) * 100
    else:
        df["fcf_yield"] = np.nan

    # .info現時点値を最新月にのみセット（将来は月次記録に拡張）
    today_ts = pd.Timestamp(date.today()).to_period("M").to_timestamp()
    for key in ["forward_pe", "peg_ratio", "revenue_growth", "earnings_growth",
                "recommendation_mean", "short_pct_float", "volume_vs_avg",
                "gross_margins", "psr", "ev_ebitda"]:
        df[key] = np.nan
        if today_ts in df.index:
            df.loc[today_ts, key] = info.get(key)

    # アナリスト履歴を結合
    if not analyst_df.empty:
        df = df.join(analyst_df, how="left")

    # eps_surpriseのffill（join後に欠損が生じる場合の補完）
    if "eps_surprise" in df.columns:
        df["eps_surprise"] = df["eps_surprise"].ffill(limit=4)
    
    # EPSが完全に取れない場合、earningsGrowthで補完
    if "eps_surprise" not in df.columns or df["eps_surprise"].isna().all():
        eg = info.get("earnings_growth")
        if eg is not None:
            df["eps_surprise"] = round(float(eg) * 100, 2)

    # ── 生値指標 ──────────────────────────────────────────

    df["peak_24m"]    = df["price"].rolling(24, min_periods=6).max()
    df["from_peak"]   = (df["price"] - df["peak_24m"]) / df["peak_24m"] * 100
    df["price_mom3m"] = df["price"].pct_change(3) * 100
    df["ma200_mom"]   = df["ma200_dev"].diff(3)
    df["ma50_cross"]  = (df["ma50_dev"] > 0).astype(int)  # MA50上抜け

    # 出来高急増フラグ（月次平均の1.5倍以上）
    vol_avg = df["volume_monthly"].rolling(6, min_periods=3).mean()
    df["vol_surge"] = df["volume_monthly"] / (vol_avg + 1e-9)

    # sell_on_good_news: EPSサプライズ>0 かつ 当月株価変化<-3%（S4の核心シグナル）
    df["price_mom1m"] = df["price"].pct_change(1) * 100
    if "eps_surprise" in df.columns:
        df["sell_on_good_news"] = (
            (df["eps_surprise"] > 5) & (df["price_mom1m"] < -3)
        ).astype(float)
    else:
        df["sell_on_good_news"] = np.nan

    # アナリストスコア（期待スコアへの寄与）
    # upgrade_rate高い=期待上昇中、低い=期待剥落中
    if "analyst_upgrade_rate" in df.columns:
        df["analyst_score"] = z_score_series(df["analyst_upgrade_rate"])
    else:
        df["analyst_score"] = np.nan

    # ── Z-scoreスコア ──────────────────────────────────────

    # 期待スコア（高いほど期待過熱）
    expect_cols = []
    for col in ["ma200_dev", "ma50_dev"]:
        if col in df.columns:
            expect_cols.append(z_score_series(df[col]))
    if not df["price_iv_ratio"].isna().all():
        expect_cols.append(z_score_series(df["price_iv_ratio"]))
    # アナリスト修正率（上方修正が多いほど期待過熱）
    if "analyst_score" in df.columns and not df["analyst_score"].isna().all():
        expect_cols.append(df["analyst_score"])
    df["expectation_score"] = pd.concat(expect_cols, axis=1).mean(axis=1) if expect_cols else np.nan

    # 実体スコア（高いほど実体良好）
    fund_cols = []
    for col in ["rev_yoy", "ni_yoy", "rule40", "fcf_yield"]:
        if col in df.columns and not df[col].isna().all():
            fund_cols.append(z_score_series(df[col]))
    df["fundamental_score"] = pd.concat(fund_cols, axis=1).mean(axis=1) if fund_cols else np.nan

    # モメンタムスコア（高いほど上昇トレンド）
    mom_cols = []
    for col in ["ma50_dev", "ma200_dev", "rsi"]:
        if col in df.columns:
            mom_cols.append(z_score_series(df[col]))
    df["momentum_score"] = pd.concat(mom_cols, axis=1).mean(axis=1) if mom_cols else np.nan

    return df


# ── ステージ判定 ────────────────────────────────────────────

def determine_stage(row: pd.Series, prev_stage: int = 2, s3_streak: int = 0, s4_streak: int = 0) -> int:
    """
    Koichi定義に基づくステージ判定。
    「期待と実体の関係性」で判断する。

    s3_streak: 直前からS3が何ヶ月連続しているか（S4転落の文脈判定に使用）
    s4_streak: 直前からS4が何ヶ月連続しているか（S4脱出条件に使用）

    判定優先順位:
      1. S4優先チェック（S3が一定期間続いた後の急落）
      2. S3（陶酔期）: 期待が実体を大幅超過
      3. S4（期待剥落期）: 期待の崩壊
      4. S0（失望/蓄積期）: 深い低迷・無関心
      5. S1（期待覚醒期）: 期待の萌芽
      6. S2（期待拡大期）: 期待と実体が噛み合っている
    """
    # テクニカル生値
    ma200_dev   = row.get("ma200_dev",   0) or 0
    ma200_mom   = row.get("ma200_mom",   0) or 0
    from_peak   = row.get("from_peak",   0) or 0
    price_mom3m = row.get("price_mom3m", 0) or 0
    rsi         = row.get("rsi",        50) or 50
    vol_surge   = row.get("vol_surge",   1) or 1

    # アナリスト・EPS指標
    sell_on_good = row.get("sell_on_good_news", 0) or 0  # 良決算でも下落
    eps_surprise = row.get("eps_surprise")               # EPSサプライズ率%
    upgrade_rate = row.get("analyst_upgrade_rate")       # アナリスト上方修正率
    buy_ratio    = row.get("buy_hold_ratio")             # Buy比率

    # バリュエーション（現時点値・NaNの場合は判定に使わない）
    forward_pe  = row.get("forward_pe")
    peg         = row.get("peg_ratio")
    rev_growth  = row.get("revenue_growth")   # 小数（YoY）
    earn_growth = row.get("earnings_growth")  # 小数（YoY）
    short_pct   = row.get("short_pct_float")
    rec_mean    = row.get("recommendation_mean")

    # Z-scoreスコア
    e = row.get("expectation_score",  0) or 0
    f = row.get("fundamental_score",  0) or 0
    m = row.get("momentum_score",     0) or 0

    # ── S4優先チェック（S3が続いた後の急落 = 期待剥落確定）──────
    # S3が2ヶ月以上続いた後にピーク比-28%超かつRSI<47 → 期待崩壊
    if prev_stage in (3, 4) and s3_streak >= 2 and from_peak < -28 and rsi < 47:
        return 4
    # S4脱出（長期S4かつ実体が強い → バリュエーション訂正完了とみなしてS2へ）
    if prev_stage == 4 and s4_streak >= 6:
        rev_yoy_val = row.get("rev_yoy")
        ni_yoy_val  = row.get("ni_yoy")
        if rev_yoy_val is not None and float(rev_yoy_val) > 20:
            if ni_yoy_val is not None and float(ni_yoy_val) > 0:
                return 2
    # S4慣性（直前S4で下落継続中 → 期待はまだ戻っていない）
    if prev_stage == 4 and from_peak < -8 and ma200_dev < 30:
        return 4

    # ── S3: 陶酔期 ──────────────────────────────────────────
    # 【核心】期待が実体を大幅に超過している過熱状態
    # 条件A: MA200乖離が大きく上昇継続中
    if ma200_dev > 40:
        return 3
    if ma200_dev > 25 and rsi > 50:
        return 3
    # 条件B: MA200 > 12% かつ RSI高騰 かつ上昇モメンタム
    if ma200_dev > 12 and rsi > 58 and price_mom3m > 5:
        return 3
    if ma200_dev > 15 and rsi > 55:
        return 3
    # 条件C: バリュエーション過熱
    if forward_pe is not None and forward_pe > 60 and ma200_dev > 15:
        return 3
    if peg is not None and peg > 2.5 and ma200_dev > 10 and rsi > 55:
        return 3
    # 条件D: Buy比率が異常に高い + テクニカル過熱
    if buy_ratio is not None and buy_ratio > 0.8 and ma200_dev > 15:
        return 3
    # 条件E: S3慣性（MA200高水準で-25%未満かつMA200momが悪化していない）
    if prev_stage == 3 and ma200_dev > 20 and from_peak > -25 and ma200_mom > -10:
        return 3
    # 条件F: Z-scoreベース
    if e > 0.7 and m > 0.5:
        return 3

    # ── S4: 期待剥落期 ──────────────────────────────────────
    # 【核心】S3から転落開始、または下落継続中
    # 条件A: 良決算でも株価下落（S4の最強シグナル）
    if sell_on_good == 1 and from_peak < -5:
        return 4
    # 条件B: S3/S4からの転落（ピーク比-25%超かつMA200mom悪化）
    if prev_stage in (3, 4) and from_peak < -25 and ma200_mom < -10:
        return 4
    # 条件C: MA200乖離が急速に悪化
    if from_peak < -8 and rsi < 50 and ma200_mom < -10:
        return 4
    # 条件D: MA200割れ + 下落継続
    if ma200_dev < 0 and from_peak < -15 and price_mom3m < -3:
        return 4
    # 条件E: 大幅下落でMA200がまだプラスでも
    if from_peak < -40 and ma200_dev < 25:
        return 4

    # ── S0: 失望/蓄積期 ──────────────────────────────────────
    # 【核心】機関未参入・深い低迷・スマートマネー仕込み段階
    _is_s0 = (
        ma200_dev < -20
        or (short_pct is not None and short_pct > 0.08 and ma200_dev < -10)
        or (from_peak < -50 and ma200_dev < -15)
    )
    if _is_s0:
        # S0→S1昇格: 反発モメンタムが強ければS1に昇格
        # 浅い低迷（MA200 > -20%）: 3M+10%超で昇格
        # 深い低迷（MA200 <= -20%）: 3M+20%超の強烈反発のみ昇格
        if (ma200_dev > -20 and price_mom3m > 10) or (ma200_dev <= -20 and price_mom3m > 20):
            return 1
        return 0

    # ── S1: 期待覚醒期 ──────────────────────────────────────
    # 【核心】底打ち確認 + 新しいトリガー + 出来高急増
    # 条件A: MA200 < -10% から強い反発
    if ma200_dev < -10 and price_mom3m > 10:
        return 1
    # 条件B: MA200 < -5% から急反発
    if ma200_dev < -5 and price_mom3m > 20:
        return 1
    # 条件C: 出来高急増 + 低迷圏からの回復（強い上昇のみ）
    if vol_surge > 1.5 and ma200_dev < 0 and price_mom3m > 10:
        return 1
    # 条件D: EPSサプライズ + アナリスト上方修正開始（底値圏）
    if (eps_surprise is not None and eps_surprise > 10 and
            upgrade_rate is not None and upgrade_rate > 0.6 and
            ma200_dev < 5):
        return 1
    # 条件E: アナリストが強気転換し始め + 底値圏
    if rec_mean is not None and rec_mean < 2.0 and ma200_dev < -5 and price_mom3m > 0:
        return 1
    # 条件F: Z-scoreベース
    if e < -0.3 and m > 0.5:
        return 1

    # ── S2: 期待拡大期 ──────────────────────────────────────
    # 【核心】実体成長 + マルチプル拡大中。過熱でも低迷でもない上昇局面
    return 2



def detect_substage(row: pd.Series, stage: int, stage_months: int) -> dict:
    """
    各ステージの内部フェーズ（入口・中盤・出口）を判定。
    「今のステージはどこにいるか」「次に何が起きるか」を示す。
    """
    ma200  = row.get("ma200_dev",   0) or 0
    fp     = row.get("from_peak",   0) or 0
    rsi    = row.get("rsi",        50) or 50
    mom3m  = row.get("price_mom3m", 0) or 0
    ma200m = row.get("ma200_mom",   0) or 0

    def _v(val):
        """pandas NaN を None に変換（NaN は is None で検出できないため）"""
        return None if pd.isna(val) else val

    rev_yoy   = _v(row.get("rev_yoy"))
    eps_surp  = _v(row.get("eps_surprise"))

    # 実体の強さ判定
    # 条件A: 標準（売上>15% かつ EPSが大きくミスしていない、またはEPS黒字サプライズ）
    _real_standard = (
        (rev_yoy is not None and rev_yoy > 15 and (eps_surp is None or eps_surp > -5)) or
        (eps_surp is not None and eps_surp > 0 and rev_yoy is not None and rev_yoy > 0)
    )
    # 条件B: 高成長グロース（売上>30%かつEPS大幅ミスでない）
    # 赤字成長企業でも売上が急拡大していれば「実体崩壊」とは言えない
    _real_growth = (
        rev_yoy is not None and rev_yoy > 30 and
        (eps_surp is None or eps_surp > -30)
    )
    real_strong = _real_standard or _real_growth

    if stage == 3:  # 陶酔期
        if ma200m < -5 and fp < -5:
            return dict(phase="出口", label="ピークアウト兆候",
                watch="高値から離れ始め、MA200乖離も縮小中。売りの準備タイミング。高値更新が止まっているか確認。",
                next="S4（期待剥落期）への移行に備える。ポジション縮小を開始。")
        if rsi < 40 and ma200 > 30:
            return dict(phase="出口", label="過熱感に陰り",
                watch="RSIが低下。モメンタムが弱まっている。出来高・高値更新の有無を確認。",
                next="出来高を伴う下落が出れば売りシグナル。")
        if ma200 > 50 and fp > -5:
            return dict(phase="中盤", label="過熱継続",
                watch="MA200乖離が高水準で推移。良ニュースへの株価反応が鈍くなっていないか。",
                next="良決算でも株価が反応しなくなったらS4転換のサイン。")
        if stage_months <= 3:
            return dict(phase="入口", label="陶酔期入り",
                watch="過熱が始まったばかり。まだ上昇余地がある可能性。",
                next="急いで売らない。MA200乖離がさらに拡大するか監視。")
        return dict(phase="中盤", label="陶酔継続",
            watch="期待過熱が続いている。ピークアウトのシグナルを待つ。",
            next="MA200乖離の縮小・RSI低下・高値更新停止が売りの合図。")

    elif stage == 4:  # 期待剥落期
        ma200_shrinking = ma200m > -5
        price_iv  = row.get("price_iv_ratio")
        forward_pe = row.get("forward_pe")

        # バリュエーション過熱チェック
        # 株価÷IV > 2.0 または FwdPE > 100 の場合は「底打ち兆候」に昇格しない
        # （実体が強くても期待がまだ過熱しており、さらなる訂正余地が大きい）
        valuation_overheat = (
            (price_iv is not None and price_iv > 2.0) or
            (forward_pe is not None and forward_pe > 100)
        )

        # 底打ち兆候：実体強い + MA200収縮鈍化 + RSI>40 + 過大下落していない
        bottoming = real_strong and ma200_shrinking and rsi > 40 and fp > -45

        if bottoming:
            if valuation_overheat:
                piv_str = f"株価÷IV={price_iv:.2f}x" if price_iv is not None else ""
                fpe_str = f"FwdPE={forward_pe:.0f}x" if forward_pe is not None else ""
                overheat_str = "、".join(filter(None, [piv_str, fpe_str]))
                return dict(phase="中盤B", label="実体維持・バリュエーション過熱",
                    watch=f"実体（売上・EPS）は強いが、{overheat_str}と割高感が残る。"
                           "期待の訂正がまだ終わっていない可能性。",
                    next="バリュエーションが正常化（FwdPE<60 または 株価÷IV<2.0）するまで様子見。"
                         "実体の強さだけで底打ちと判断するのは早計。")
            return dict(phase="出口", label="底打ち兆候",
                watch="実体（売上・EPS）は強く、MA200乖離の縮小が鈍化。期待と実体が近づいている。",
                next="打診買いの準備を始める。出来高増加を伴う株価反発で本格エントリー。")
        # 長期調整（S4が6ヶ月超かつ実体強い）：バリュエーション訂正が長引いている状態
        if stage_months >= 6 and real_strong:
            ni_yoy_val = _v(row.get("ni_yoy"))
            ni_str = f"・純利益{ni_yoy_val:+.1f}%" if ni_yoy_val is not None else ""
            rev_str = f"売上{rev_yoy:+.1f}%" if rev_yoy is not None else "売上データなし"
            return dict(phase="中盤B", label="長期調整・実体強",
                watch=f"S4が{stage_months}ヶ月継続。{rev_str}{ni_str}と実体は強い。"
                       "バリュエーション訂正が長引く典型的な長期調整局面。",
                next="実体の強さが続けばS2への回帰が近い。出来高を伴う反発・MA200復帰に注目。")
        if real_strong:
            return dict(phase="中盤B", label="実体維持・期待崩壊中",
                watch="売上・EPSは強い。期待の過熱訂正が続いているが、実体が下支え。",
                next="実体の強さが続けば底は近い。MA200乖離の縮小ペースを監視。")
        if stage_months <= 2:
            return dict(phase="入口", label="期待剥落開始",
                watch="S3から転落直後。Distribution（大口売り抜け）が始まっている可能性。",
                next="ポジション縮小推奨。実体（次の決算）が強ければ早期底打ちの可能性。")
        # EPSデータなし＋売上が強い場合は中盤Bに寄せる（誤判定防止）
        eps_missing = eps_surp is None
        if eps_missing and rev_yoy is not None and rev_yoy > 15:
            return dict(phase="中盤B*", label="実体維持の可能性（EPS要確認）",
                watch=f"売上成長{rev_yoy:+.1f}%は維持されているが、EPSデータが未取得。決算結果を別途確認推奨。",
                next="次の決算でEPS黒字なら底打ちの可能性。マイナスなら中盤A（実体崩壊）に移行。")
        # 中盤A: rev_yoyの水準でラベルを変える
        # rev_yoyがプラスなら「実体崩壊」とは言えず「軟化」が適切
        if rev_yoy is not None and rev_yoy > 5:
            # eps_surprise の実際の値に応じてテキストを分岐（固定「大幅ミス」を回避）
            if eps_surp is not None and eps_surp < -5:
                eps_text = f"EPSが予想比{eps_surp:+.1f}%の大幅ミスで期待の修正が続いている。"
            elif eps_surp is not None and eps_surp < 0:
                eps_text = f"EPSが予想比{eps_surp:+.1f}%とわずかにミスしている。"
            else:
                eps_text = "EPSは予想並みまたは超過。株価調整はバリュエーション面の見直し。"
            return dict(phase="中盤A", label="実体軟化・期待崩壊中",
                watch=f"売上成長{rev_yoy:+.1f}%はあるが、{eps_text}",
                next="次の決算でEPS改善が確認されれば「実体維持」に格上げ。悪化なら本格的な崩壊へ。")
        return dict(phase="中盤A", label="実体も崩壊中",
            watch="売上・EPSの悪化も確認される本格的な下落局面。",
            next="実体の回復（売上加速・EPSサプライズ）が出るまで売り継続。")

    elif stage == 2:  # 期待拡大期
        if ma200 > 20 and rsi > 65 and mom3m > 15:
            return dict(phase="出口", label="過熱の手前",
                watch="MA200乖離が拡大し過熱圏に近づいている。バリュエーションの拡大速度を確認。",
                next="S3（陶酔期）移行に備える。利益確定の準備を始める。")
        if stage_months <= 3:
            return dict(phase="入口", label="期待拡大開始",
                watch="期待と実体が噛み合い始めた段階。",
                next="売上成長の加速・アナリスト上方修正増加が続けばS3へ向かう。")
        return dict(phase="中盤", label="拡大継続",
            watch="健全な上昇局面。過熱サインを監視。",
            next="MA200乖離が20%超かつRSI65超で過熱の兆候。")

    elif stage == 1:  # 期待覚醒期
        if ma200 > -5 and rsi > 55 and mom3m > 5:
            return dict(phase="出口", label="S2移行の兆候",
                watch="底打ちが確認され、モメンタムが回復。",
                next="S2（期待拡大）への移行が近い。ポジション構築を検討。")
        return dict(phase="入口", label="覚醒初期",
            watch="本物の覚醒か、だましの反発かを見極める。出来高が鍵。",
            next="出来高を伴う連続上昇でS2への移行を確認。")

    else:  # S0 失望/蓄積期
        if mom3m > 10 and rsi > 40:
            return dict(phase="出口", label="物語の萌芽",
                watch="モメンタムが回復し始めた。スマートマネーが動いている可能性。",
                next="S1（期待覚醒）への移行を確認。出来高急増が確認されればエントリー検討。")
        return dict(phase="中盤", label="低迷継続",
            watch="底値形成中。まだ急いで動かない。",
            next="出来高を伴う株価反発・新しい物語（製品・契約・提携）の出現を待つ。")

def run_poc(ticker: str = "PLTR") -> dict:
    """PoC実行"""
    print(f"\n{'='*55}")
    print(f"HypeCore PoC v2 - {ticker}")
    print(f"{'='*55}")

    df = compute_scores(ticker)

    # ステージ判定（慣性ルールのため順番に処理）
    stages = []
    prev = 2
    s3_streak = 0  # S3連続月数
    s4_streak = 0  # S4連続月数
    for _, row in df.iterrows():
        s = determine_stage(row, prev_stage=prev, s3_streak=s3_streak, s4_streak=s4_streak)
        stages.append(s)
        s3_streak = s3_streak + 1 if s == 3 else 0
        s4_streak = s4_streak + 1 if s == 4 else 0
        prev = s
    df["stage"] = stages
    df["stage_label"] = df["stage"].map(STAGE_LABELS)

    # 内部フェーズ判定
    substages = []
    stage_months = 0
    prev_s = None
    for _, row in df.iterrows():
        s = int(row["stage"])
        if s != prev_s:
            stage_months = 1
        else:
            stage_months += 1
        substages.append(detect_substage(row, s, stage_months))
        prev_s = s
    df["substage"] = substages

    # 低ベース効果検出: 前年(12ヶ月前)のrev_yoyがマイナスかつ今年が50%超
    df["prev_rev_yoy"] = df["rev_yoy"].shift(12)
    df["low_base_effect"] = (
        df["prev_rev_yoy"].notna()
        & (df["prev_rev_yoy"] < -10)
        & (df["rev_yoy"].fillna(0) > 50)
    )

    df_out = df[df.index >= "2024-01-01"].copy()

    # PLTRのみ正解ラベルと比較
    if ticker == "PLTR":
        gt = PLTR_GROUND_TRUTH
        df_out["ground_truth"] = df_out.index.strftime("%Y-%m").map(gt)
        df_out["correct"] = df_out["stage"] == df_out["ground_truth"]
        accuracy = df_out["correct"].mean()
        print(f"\n【検証結果】正解率: {accuracy:.1%}")
        print(f"\n{'月':10s} {'予測':5s} {'正解':5s} {'一致':5s} {'MA200':8s} {'ピーク比':8s} {'RSI':5s} {'株価':8s}")
        print("-" * 65)
        for idx, row in df_out.iterrows():
            ym  = idx.strftime("%Y-%m")
            pred = int(row["stage"])
            g    = gt.get(ym, "-")
            ok   = "✅" if row.get("correct") else "❌"
            ma   = f"{row['ma200_dev']:+.1f}%" if not pd.isna(row.get("ma200_dev", float("nan"))) else "—"
            fp   = f"{row['from_peak']:+.1f}%"  if not pd.isna(row.get("from_peak", float("nan"))) else "—"
            rs   = f"{row['rsi']:.0f}"          if not pd.isna(row.get("rsi",       float("nan"))) else "—"
            p    = f"${row['price']:.1f}"
            print(f"{ym:10s} {pred!s:5s} {g!s:5s} {ok:5s} {ma:8s} {fp:8s} {rs:5s} {p:8s}")

    # JSON保存
    def safe(v):
        try:
            return None if (v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v)))) else round(float(v), 3)
        except Exception:
            return None

    out = []
    for idx, row in df_out.iterrows():
        out.append({
            "month":              idx.strftime("%Y-%m"),
            "price":              safe(row.get("price")),
            "stage":              int(row["stage"]),
            "stage_label":        STAGE_LABELS[int(row["stage"])],
            # テクニカル
            "ma200_dev":          safe(row.get("ma200_dev")),
            "ma50_dev":           safe(row.get("ma50_dev")),
            "from_peak":          safe(row.get("from_peak")),
            "rsi":                safe(row.get("rsi")),
            "volume_ratio":       safe(row.get("volume_ratio")),
            "vol_surge":          safe(row.get("vol_surge")),
            # 財務
            "rev_yoy":            safe(row.get("rev_yoy")),
            "ni_yoy":             safe(row.get("ni_yoy")),
            "rule40":             safe(row.get("rule40")),
            "fcf_yield":          safe(row.get("fcf_yield")),
            # バリュエーション（現時点値）
            "forward_pe":         safe(row.get("forward_pe")),
            "peg_ratio":          safe(row.get("peg_ratio")),
            "psr":                safe(row.get("psr")),
            "revenue_growth":     safe(row.get("revenue_growth")),
            "earnings_growth":    safe(row.get("earnings_growth")),
            "recommendation_mean": safe(row.get("recommendation_mean")),
            "short_pct_float":    safe(row.get("short_pct_float")),
            # アナリスト・EPS
            "eps_surprise":       safe(row.get("eps_surprise")),
            "analyst_upgrade_rate": safe(row.get("analyst_upgrade_rate")),
            "analyst_downgrade_rate": safe(row.get("analyst_downgrade_rate")),
            "sell_on_good_news":  safe(row.get("sell_on_good_news")),
            "buy_hold_ratio":     safe(row.get("buy_hold_ratio")),
            # 内部フェーズ
            "substage_phase":     row["substage"]["phase"] if isinstance(row.get("substage"), dict) else None,
            "substage_label":     row["substage"]["label"] if isinstance(row.get("substage"), dict) else None,
            "substage_watch":     row["substage"]["watch"] if isinstance(row.get("substage"), dict) else None,
            "substage_next":      row["substage"]["next"]  if isinstance(row.get("substage"), dict) else None,
            # スコア
            "expectation_score":  safe(row.get("expectation_score")),
            "fundamental_score":  safe(row.get("fundamental_score")),
            "momentum_score":     safe(row.get("momentum_score")),
            # IV
            "price_iv_ratio":     safe(row.get("price_iv_ratio")),
            "ev_ebitda":          safe(row.get("ev_ebitda")),   # 負値も格納（UIで変換）
            # 低ベース効果: 前年rev_yoy<-10% かつ 今年rev_yoy>50%
            "low_base_effect":    bool(row.get("low_base_effect", False)),
        })

    JST = timezone(timedelta(hours=9))
    result = {
        "ticker":       ticker,
        "generated":    date.today().isoformat(),
        "generated_at": datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "monthly":      out,
    }
    out_path = _OUT_DIR / f"{ticker}_poc.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n保存完了: {out_path}")
    return result


if __name__ == "__main__":
    import sys
    import shutil

    _DOCS_DIR = _REPO_ROOT / "docs" / "value-monitor" / "hypecore" / "data"
    _DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # cik_lookup.csv の hypecore=true 銘柄を動的に取得
    try:
        import sys as _sys
        _sys.path.insert(0, str(_REPO_ROOT / "common" / "sec_data"))
        from tickers import get_hypecore_tickers
        ALL_TICKERS = get_hypecore_tickers()
        print(f"[INFO] hypecore対象: {len(ALL_TICKERS)}銘柄 (cik_lookup.csv)")
    except Exception as _e:
        print(f"[WARN] tickers.py読み込み失敗、フォールバックリストを使用: {_e}")
        ALL_TICKERS = [
            "AAPL","ALAB","AMAT","AMD","AMZN","APP","ASTS","AVAV","BBAI",
            "BSY","CAKE","CART","CEG","CELH","COHR","CRM","CRWV","CWAN",
            "ELF","GOOGL","GTLB","IONQ","IOT","JOBY","KO","LITE","LLY","LMT",
            "META","MRVL","MSFT","NOW","NVDA","ONDS","PLTR","QBTS","RBRK","RCAT",
            "RDW","RKLB","RXRX","S","SITM","SOFI","SOUN","SPIR","TSLA",
            "VRT","ZETA",
        ]

    args = sys.argv[1:]
    if not args:
        tickers = ["PLTR"]
    elif args[0] == "--all":
        tickers = ALL_TICKERS
    elif args[0] == "--batch":
        tickers = args[1:] if len(args) > 1 else ["PLTR"]
    else:
        tickers = [args[0]]

    success, failed = [], []
    for t in tickers:
        try:
            run_poc(t)
            src = _OUT_DIR / f"{t}_poc.json"
            dst = _DOCS_DIR / f"{t}_poc.json"
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  → docs にコピー完了: {dst.name}")
            success.append(t)
        except Exception as e:
            print(f"[ERROR] {t}: {e}")
            failed.append(t)

    print(f"\n{'='*50}")
    print(f"完了: {len(success)}銘柄 / 失敗: {len(failed)}銘柄")
    if failed:
        print(f"失敗銘柄: {', '.join(failed)}")
    if success:
        print(f"成功銘柄: {', '.join(success)}")
