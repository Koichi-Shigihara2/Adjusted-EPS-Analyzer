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
from datetime import date, timedelta
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
    "2024-01": 2, "2024-02": 2, "2024-03": 2,
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

    rev_yoy    = rev.pct_change(4) * 100
    ni_yoy     = ni.pct_change(4) * 100 if not ni.empty else pd.Series(dtype=float)
    op_margin  = (ni / rev * 100) if (not ni.empty) else pd.Series(dtype=float)
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


# ── スコア計算 ────────────────────────────────────────────

def compute_scores(ticker: str) -> pd.DataFrame:
    """全指標を月次DataFrameに統合"""
    print(f"\n[{ticker}] データ取得中...")

    price_df = fetch_price_data(ticker, start="2021-01-01")
    print(f"  株価: {len(price_df)}ヶ月分")

    fund_df = fetch_quarterly_fundamentals(ticker)
    print(f"  財務: {len(fund_df)}行")

    iv_series = fetch_tanuki_iv(ticker)

    # .info（現時点値）
    info = fetch_info_snapshot(ticker)
    print(f"  .info: ForwardPE={info.get('forward_pe'):.1f} PEG={info.get('peg_ratio')} "
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
                "gross_margins", "psr"]:
        df[key] = np.nan
        if today_ts in df.index:
            df.loc[today_ts, key] = info.get(key)

    # ── 生値指標 ──────────────────────────────────────────

    df["peak_24m"]    = df["price"].rolling(24, min_periods=6).max()
    df["from_peak"]   = (df["price"] - df["peak_24m"]) / df["peak_24m"] * 100
    df["price_mom3m"] = df["price"].pct_change(3) * 100
    df["ma200_mom"]   = df["ma200_dev"].diff(3)
    df["ma50_cross"]  = (df["ma50_dev"] > 0).astype(int)  # MA50上抜け

    # 出来高急増フラグ（月次平均の1.5倍以上）
    vol_avg = df["volume_monthly"].rolling(6, min_periods=3).mean()
    df["vol_surge"] = df["volume_monthly"] / (vol_avg + 1e-9)

    # ── Z-scoreスコア ──────────────────────────────────────

    # 期待スコア（高いほど期待過熱）
    expect_cols = []
    for col in ["ma200_dev", "ma50_dev"]:
        if col in df.columns:
            expect_cols.append(z_score_series(df[col]))
    if not df["price_iv_ratio"].isna().all():
        expect_cols.append(z_score_series(df["price_iv_ratio"]))
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

def determine_stage(row: pd.Series, prev_stage: int = 2) -> int:
    """
    Koichi定義に基づくステージ判定。

    判定優先順位:
      1. S3（陶酔期）: 過熱を最初に検出
      2. S4（期待剥落期）: S3からの転落・下落継続
      3. S0（失望/蓄積期）: 深い低迷
      4. S1（期待覚醒期）: 底打ちからの回復
      5. S2（期待拡大期）: 上記以外の上昇局面
    """
    # テクニカル生値
    ma200_dev   = row.get("ma200_dev",   0) or 0
    ma200_mom   = row.get("ma200_mom",   0) or 0
    from_peak   = row.get("from_peak",   0) or 0
    price_mom3m = row.get("price_mom3m", 0) or 0
    rsi         = row.get("rsi",        50) or 50
    vol_surge   = row.get("vol_surge",   1) or 1

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

    # ── S3: 陶酔期 ──────────────────────────────────────────
    # 【核心】期待が実体を大幅に超過している過熱状態
    # 条件A: MA200乖離が大きく、かつ上昇継続中
    if ma200_dev > 40:
        return 3
    if ma200_dev > 25 and rsi > 50:
        return 3
    # 条件B: バリュエーション過熱（forwardPE or PEGが異常）+ テクニカル過熱
    if forward_pe is not None and forward_pe > 60 and ma200_dev > 15:
        return 3
    if peg is not None and peg > 2.5 and ma200_dev > 10 and rsi > 55:
        return 3
    # 条件C: Z-scoreベース
    if e > 0.7 and m > 0.5:
        return 3

    # ── S4: 期待剥落期 ──────────────────────────────────────
    # 【核心】S3から転落開始、または下落継続中
    # 条件A: 慣性ルール（直前S4 + 下落継続）
    if prev_stage == 4 and from_peak < -8 and ma200_dev < 20:
        return 4
    # 条件B: MA200乖離が急速に悪化（方向性の転換を捉える）
    if from_peak < -8 and rsi < 55 and ma200_mom < -10:
        return 4
    # 条件C: MA200割れ + 下落継続
    if ma200_dev < 0 and from_peak < -15 and price_mom3m < -3:
        return 4
    # 条件D: まだMA200上だが急落局面（RSI<40 + ピーク比-15%）
    if from_peak < -15 and rsi < 40 and ma200_mom < -15:
        return 4

    # ── S0: 失望/蓄積期 ──────────────────────────────────────
    # 【核心】機関未参入・深い低迷・スマートマネー仕込み段階
    # 条件A: MA200を大きく下回り長期低迷
    if ma200_dev < -20 and m < -0.3:
        return 0
    # 条件B: 空売り比率が高く市場の懐疑が強い + 低迷
    if short_pct is not None and short_pct > 0.08 and ma200_dev < -10:
        return 0
    # 条件C: 深い下落
    if from_peak < -50 and ma200_dev < -15:
        return 0

    # ── S1: 期待覚醒期 ──────────────────────────────────────
    # 【核心】底打ち確認 + 新しいトリガー + 出来高急増
    # 条件A: MA200下から回復モメンタム
    if ma200_dev < -10 and price_mom3m > 5:
        return 1
    # 条件B: 出来高急増 + 低迷圏からの回復
    if vol_surge > 1.5 and ma200_dev < 0 and price_mom3m > 3:
        return 1
    # 条件C: アナリストが強気転換し始め（rec_mean < 2 = Buy方向）+ 底値圏
    if rec_mean is not None and rec_mean < 2.0 and ma200_dev < -5 and price_mom3m > 0:
        return 1
    # 条件D: Z-scoreベース
    if e < -0.3 and m > 0.5:
        return 1

    # ── S2: 期待拡大期 ──────────────────────────────────────
    # 【核心】実体成長 + マルチプル拡大中。過熱でも低迷でもない上昇局面
    return 2


def run_poc(ticker: str = "PLTR") -> dict:
    """PoC実行"""
    print(f"\n{'='*55}")
    print(f"HypeCore PoC v2 - {ticker}")
    print(f"{'='*55}")

    df = compute_scores(ticker)

    # ステージ判定（慣性ルールのため順番に処理）
    stages = []
    prev = 2
    for _, row in df.iterrows():
        s = determine_stage(row, prev_stage=prev)
        stages.append(s)
        prev = s
    df["stage"] = stages
    df["stage_label"] = df["stage"].map(STAGE_LABELS)

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
            return None if (v is None or (isinstance(v, float) and np.isnan(v))) else round(float(v), 3)
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
            # スコア
            "expectation_score":  safe(row.get("expectation_score")),
            "fundamental_score":  safe(row.get("fundamental_score")),
            "momentum_score":     safe(row.get("momentum_score")),
            # IV
            "price_iv_ratio":     safe(row.get("price_iv_ratio")),
        })

    result = {
        "ticker":    ticker,
        "generated": date.today().isoformat(),
        "monthly":   out,
    }
    out_path = _OUT_DIR / f"{ticker}_poc.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n保存完了: {out_path}")
    return result


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "PLTR"
    run_poc(ticker)
