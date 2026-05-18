import os
import sys
import urllib.request
import feedparser
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
import json
import csv
import re
import requests   # 追加: requests で非ASCII URLを扱う

# --- 必須環境変数チェック ---
required_env_vars = ["XAI_API_KEY", "GMAIL_USER", "GMAIL_PASSWORD"]
missing = [v for v in required_env_vars if not os.getenv(v)]
if missing:
    print(f"[ERROR] 必須環境変数が設定されていません: {', '.join(missing)}")
    sys.exit(1)

# --- 設定 ---
XAI_API_KEY  = os.getenv("XAI_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
# RSSファイルはスクリプトと同じ scr/ ディレクトリに配置
RSS_LIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_market_rss.txt")

JST = timezone(timedelta(hours=9))

# データ保存先（GitHub Pages 配信対象の docs/market-monitor/market-pulse/data/）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(REPO_ROOT, "docs", "market-monitor", "market-pulse", "data")
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")
CSV_PATH = os.path.join(DATA_DIR, "market_data.csv")
BREADTH_JSON = os.path.join(DATA_DIR, "breadth_data.json")

# CSVのカラム定義（必要に応じて拡張）
CSV_COLUMNS = [
    "date", "judgment",
    "VIX指数_value", "VIX指数_change", "VIX指数_change_percent",
    "VIX9D（短期VIX）_value", "VIX9D（短期VIX）_change_percent", "VIX9D対VIX比_value", "VIX9D対VIX比_contango",
    "日経平均_value", "日経平均_change", "日経平均_change_percent",
    "ドル円_value", "ドル円_change", "ドル円_change_percent",
    "米10年債_value", "米10年債_change", "米10年債_change_percent",
    "S&P500_value", "S&P500_change", "S&P500_change_percent",
    "WTI原油_value", "WTI原油_change", "WTI原油_change_percent",
    "金（GOLD）_value", "金（GOLD）_change", "金（GOLD）_change_percent",
    "HYG（ハイイールド債ETF）_value", "HYG（ハイイールド債ETF）_change", "HYG（ハイイールド債ETF）_change_percent",
    "LQD（投資適格債ETF）_value", "LQD（投資適格債ETF）_change", "LQD（投資適格債ETF）_change_percent",
    "NYSE Composite_value", "NYSE Composite_change_percent", "NYSE Composite_volume_ratio",
    "S&P500グロース(IVW)_value", "S&P500グロース(IVW)_change_percent",
    "S&P500バリュー(IVE)_value", "S&P500バリュー(IVE)_change_percent",
    "Russell2000小型(RUT)_value", "Russell2000小型(RUT)_change_percent",
    "グロース対バリュー比_diff_percent",
    "大型対小型比_diff_percent",
    "HYG対LQD比_value", "HYG対LQD比_change",
    "sentiment_score", "sentiment_label",
    "summary"
]


def fetch_hist(ticker, period="5d"):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        return hist if not hist.empty else None
    except Exception:
        return None


def format_line(name, hist):
    if hist is None:
        return f"● {name}: 取得制限あり\n"
    try:
        latest = hist['Close'].iloc[-1]
        last_date = hist.index[-1].astimezone(JST).strftime('%m/%d')
        diff, pct, vol_msg = 0.0, 0.0, ""
        if len(hist) >= 2:
            prev = hist['Close'].iloc[-2]
            diff = latest - prev
            pct = (diff / prev) * 100
            vol_latest = hist['Volume'].iloc[-1]
            vol_prev = hist['Volume'].iloc[-2]
            if vol_latest > 0 and vol_prev > 0:
                vol_msg = f" | 前日比出来高比:{vol_latest / vol_prev:.2f}"
        return f"● {name}: {latest:.2f} [{diff:+.2f} ({pct:+.2f}%){vol_msg}] ({last_date} 確定)\n"
    except Exception as e:
        return f"● {name}: 解析エラー ({e})\n"


# ──────────────────────────────────────────────────────
# センチメントスコア算出（Phase 1: 5指標版）
# ──────────────────────────────────────────────────────
def clamp01(v):
    """0.0〜1.0にクランプ"""
    return max(0.0, min(1.0, v))


def compute_sentiment(structured_data):
    """
    structured_data + breadth_data.json から7指標でセンチメントスコア(0-100)を算出。
    0=EXTREME FEAR, 50=NEUTRAL, 100=EXTREME GREED

    サブ指標 (Phase 2 — 7指標版):
      1. VIX水準             (Weight 25%) — 12→100, 35→0
      2. S&P500 vs 50日MA乖離 (Weight 20%) — -8%→0, +8%→100
      3. AD Ratio (5日)       (Weight 15%) — 0.5→0, 2.0→100
      4. HYG/LQD比 変化方向   (Weight 12%) — 下落→0, 上昇→100
      5. NH-NL差分            (Weight 10%) — -50→0, +50→100
      6. グロース対バリュー比  (Weight 10%) — バリュー優勢→0, グロース優勢→100
      7. 出来高比(Distribution)(Weight  8%) — 出来高比>1.1+下落→0, 通常→100
    """
    sub_scores = {}

    # breadth_data.json を読み込み
    breadth = _load_latest_breadth()

    # --- 1. VIX水準 (25%) --- ※VIX9D逆転（短期リスクオフ）で補正あり
    vix_data   = structured_data.get("VIX指数")
    vix9d_ratio = structured_data.get("VIX9D対VIX比")
    if vix_data and vix_data.get("value") is not None:
        vix = vix_data["value"]
        score = clamp01((35 - vix) / (35 - 12))
        # VIX9D逆転（VIX9D > VIX）= 短期リスクオフ準備 → -0.05補正
        if vix9d_ratio and vix9d_ratio.get("contango") is False:
            score = clamp01(score - 0.05)
        sub_scores["vix_level"] = {"score": score, "weight": 0.25, "raw": vix}
    else:
        sub_scores["vix_level"] = {"score": 0.5, "weight": 0.25, "raw": None}

    # --- 2. S&P500 vs 50日MA乖離率 (20%) ---
    sp500_ma_dev = _get_sp500_ma_deviation()
    if sp500_ma_dev is not None:
        score = clamp01((sp500_ma_dev + 8) / 16)
        sub_scores["sp500_ma_dev"] = {"score": score, "weight": 0.20, "raw": round(sp500_ma_dev, 2)}
    else:
        sub_scores["sp500_ma_dev"] = {"score": 0.5, "weight": 0.20, "raw": None}

    # --- 3. AD Ratio 5日 (15%) ---
    if breadth and breadth.get("ad_ratio_5d") is not None:
        ad5 = breadth["ad_ratio_5d"]
        # 0.5→0(FEAR), 2.0→100(GREED) の線形補間
        score = clamp01((ad5 - 0.5) / (2.0 - 0.5))
        sub_scores["ad_ratio"] = {"score": score, "weight": 0.15, "raw": ad5}
    else:
        sub_scores["ad_ratio"] = {"score": 0.5, "weight": 0.15, "raw": None}

    # --- 4. HYG/LQD比 変化方向 (12%) ---
    hyg_lqd = structured_data.get("HYG対LQD比")
    if hyg_lqd and hyg_lqd.get("change") is not None:
        chg = hyg_lqd["change"]
        score = clamp01((chg + 0.005) / 0.01)
        sub_scores["hyg_lqd_dir"] = {"score": score, "weight": 0.12, "raw": round(chg, 6)}
    else:
        sub_scores["hyg_lqd_dir"] = {"score": 0.5, "weight": 0.12, "raw": None}

    # --- 5. NH-NL差分 (10%) ---
    if breadth and breadth.get("nh_nl_diff") is not None:
        nh_nl = breadth["nh_nl_diff"]
        # -50→0(FEAR), +50→100(GREED) の線形補間
        score = clamp01((nh_nl + 50) / 100)
        sub_scores["nh_nl"] = {"score": score, "weight": 0.10, "raw": nh_nl}
    else:
        sub_scores["nh_nl"] = {"score": 0.5, "weight": 0.10, "raw": None}

    # --- 6. グロース対バリュー比 (10%) ---
    gv = structured_data.get("グロース対バリュー比")
    if gv and gv.get("diff_percent") is not None:
        diff = gv["diff_percent"]
        score = clamp01((diff + 3) / 6)
        sub_scores["growth_value"] = {"score": score, "weight": 0.10, "raw": round(diff, 2)}
    else:
        sub_scores["growth_value"] = {"score": 0.5, "weight": 0.10, "raw": None}

    # --- 7. Distribution判定 (8%) ---
    sp_data = structured_data.get("S&P500")
    if sp_data and sp_data.get("volume_ratio") is not None and sp_data.get("change_percent") is not None:
        vol_ratio = sp_data["volume_ratio"]
        chg_pct = sp_data["change_percent"]
        if vol_ratio > 1.1 and chg_pct < -0.3:
            score = 0.0  # Distribution
        elif vol_ratio > 1.1 and chg_pct > 0.3:
            score = 1.0  # Accumulation
        else:
            score = 0.5  # Neutral
        sub_scores["distribution"] = {"score": score, "weight": 0.08, "raw": {"vol_ratio": vol_ratio, "chg_pct": chg_pct}}
    else:
        sub_scores["distribution"] = {"score": 0.5, "weight": 0.08, "raw": None}

    # --- 加重平均 ---
    total_score = sum(s["score"] * s["weight"] for s in sub_scores.values())
    total_weight = sum(s["weight"] for s in sub_scores.values())
    final_score = round((total_score / total_weight) * 100, 1) if total_weight > 0 else 50.0

    # ラベル判定
    if final_score <= 20:
        label = "EXTREME FEAR"
    elif final_score <= 35:
        label = "FEAR"
    elif final_score <= 50:
        label = "CAUTION"
    elif final_score <= 65:
        label = "NEUTRAL"
    elif final_score <= 80:
        label = "GREED"
    else:
        label = "EXTREME GREED"

    # サブスコアを100点満点に変換して記録
    sub_detail = {}
    for k, v in sub_scores.items():
        sub_detail[k] = {
            "score": round(v["score"] * 100, 1),
            "weight": v["weight"],
            "raw": v["raw"]
        }

    # breadthデータもsentimentに含める（フロントエンド表示用）
    breadth_summary = None
    if breadth:
        breadth_summary = {
            "advances": breadth.get("advances"),
            "declines": breadth.get("declines"),
            "ad_ratio_5d": breadth.get("ad_ratio_5d"),
            "new_highs_52w": breadth.get("new_highs_52w"),
            "new_lows_52w": breadth.get("new_lows_52w"),
            "nh_nl_diff": breadth.get("nh_nl_diff"),
            "pct_above_50ma": breadth.get("pct_above_50ma"),
            "pct_above_200ma": breadth.get("pct_above_200ma"),
            "date": breadth.get("date"),
        }

    return {
        "score": final_score,
        "label": label,
        "sub_scores": sub_detail,
        "breadth": breadth_summary,
    }


def _load_latest_breadth():
    """breadth_data.json から最新のブレッスデータを読み込む"""
    if not os.path.exists(BREADTH_JSON):
        print("[INFO] breadth_data.json が見つかりません（breadth_calculator.py 未実行）")
        return None
    try:
        with open(BREADTH_JSON, 'r', encoding='utf-8') as f:
            all_breadth = json.load(f)
        if not all_breadth:
            return None
        # 最新のエントリを返す（日付順ソート済み前提）
        latest = all_breadth[-1]
        print(f"[INFO] ブレッスデータ読み込み: {latest.get('date')} "
              f"ADV={latest.get('advances')} DEC={latest.get('declines')} "
              f"NH={latest.get('new_highs_52w')} NL={latest.get('new_lows_52w')}")
        return latest
    except Exception as e:
        print(f"[WARN] breadth_data.json読み込み失敗: {e}")
        return None


def _get_sp500_ma_deviation():
    """S&P500の現在値と50日移動平均の乖離率(%)を返す"""
    try:
        t = yf.Ticker("^GSPC")
        hist = t.history(period="3mo")
        if hist is None or len(hist) < 50:
            return None
        latest = hist['Close'].iloc[-1]
        ma50 = hist['Close'].iloc[-50:].mean()
        deviation = (latest - ma50) / ma50 * 100
        return deviation
    except Exception as e:
        print(f"[WARN] S&P500 MA乖離率の取得失敗: {e}")
        return None


# ──────────────────────────────────────────────────────
# Tech Pulse — QQQ/VXN/F&Gベースのナスダック感情指数
# ──────────────────────────────────────────────────────
def fetch_qqq_tech_data():
    """QQQのMA125乖離率とQQQ/SPY 20日相対強度を返す（%表示）"""
    try:
        hist_qqq = yf.Ticker("QQQ").history(period="200d")
        hist_spy = yf.Ticker("SPY").history(period="200d")
        # 市場開場前・開場中は当日データが不確定なため除外
        today = datetime.now(JST).date()
        hist_qqq = hist_qqq[hist_qqq.index.date < today]
        hist_spy = hist_spy[hist_spy.index.date < today]
        if hist_qqq is None or len(hist_qqq) < 125:
            print("[WARN] QQQデータ不足。Tech Pulseスキップ。")
            return None, None
        qqq_latest = hist_qqq['Close'].iloc[-1]
        ma125 = hist_qqq['Close'].iloc[-125:].mean()
        qqq_vs_ma125 = round((qqq_latest / ma125 - 1) * 100, 2)
        qqq_vs_spy_20d = None
        if hist_spy is not None and len(hist_spy) >= 21 and len(hist_qqq) >= 21:
            qqq_ret = (hist_qqq['Close'].iloc[-1] / hist_qqq['Close'].iloc[-21] - 1) * 100
            spy_ret = (hist_spy['Close'].iloc[-1] / hist_spy['Close'].iloc[-21] - 1) * 100
            if abs(spy_ret) >= 0.01:
                qqq_vs_spy_20d = round((qqq_ret / spy_ret - 1) * 100, 2)
            else:
                print(f"[WARN] spy_ret極小({spy_ret:.4f}%)のためqqq_vs_spy_20dをスキップ")
        print(f"[INFO] QQQ: {qqq_latest:.2f}, vs_MA125={qqq_vs_ma125:+.2f}%, vs_SPY_20d={qqq_vs_spy_20d}")
        return qqq_vs_ma125, qqq_vs_spy_20d
    except Exception as e:
        print(f"[WARN] QQQデータ取得失敗: {e}")
        return None, None


def fetch_vxn_from_fred():
    """FREDからVXNCLS（ナスダック恐怖指数）を取得しMA50乖離率（%）を返す"""
    fred_api_key = os.getenv("FRED_API_KEY")
    if not fred_api_key:
        print("[WARN] FRED_API_KEY未設定。VXN取得スキップ。")
        return None, None
    try:
        from fredapi import Fred
        fred = Fred(api_key=fred_api_key)
        start = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
        vxn = fred.get_series("VXNCLS", observation_start=start).dropna()
        if len(vxn) < 50:
            print("[WARN] VXNデータが不足しています。")
            return None, None
        vxn_latest = float(vxn.iloc[-1])
        ma50 = float(vxn.iloc[-50:].mean())
        vxn_vs_ma50 = round((vxn_latest / ma50 - 1) * 100, 2)
        print(f"[INFO] VXN: {vxn_latest:.2f}, MA50={ma50:.2f}, vs_MA50={vxn_vs_ma50:+.2f}%")
        return round(vxn_latest, 2), vxn_vs_ma50
    except Exception as e:
        print(f"[WARN] VXN取得失敗: {e}")
        return None, None


def fetch_fg_score_from_feargreedchart():
    """feargreedchart.com APIからF&Gスコア（0〜100）を取得する"""
    try:
        resp = requests.get(
            "https://feargreedchart.com/api/?action=all",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        score = float(resp.json()["score"]["score"])
        print(f"[INFO] feargreedchart.com F&G score: {score}")
        return score
    except Exception as e:
        print(f"[WARN] feargreedchart.com F&G取得失敗: {e}")
        return None


def _load_tech_pulse_history(json_path, window=90):
    """market_data.jsonから過去window日分のTech Pulse指標リストを返す"""
    hist = {"qqq_vs_ma125": [], "vxn_vs_ma50": [], "qqq_vs_spy_20d": []}
    if not os.path.exists(json_path):
        return hist
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except Exception:
        return hist
    cutoff = datetime.now(timezone.utc) - timedelta(days=window)
    for entry in all_data:
        try:
            d = datetime.fromisoformat(entry.get("date", ""))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if d < cutoff:
            continue
        comp = ((entry.get("tech_pulse") or {}).get("components") or {})
        for key in hist:
            v = comp.get(key)
            if v is not None:
                hist[key].append(float(v))
    return hist


def _load_prev_tech_pulse_score(json_path):
    """market_data.jsonから直近のTech Pulseスコアを返す（なければNone）"""
    if not os.path.exists(json_path):
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        for entry in reversed(all_data):
            score = (entry.get("tech_pulse") or {}).get("score")
            if score is not None:
                return float(score)
    except Exception:
        pass
    return None


def _load_div_history(json_path, window=90):
    """過去window日分の乖離値（TP score − F&G score）リストを返す"""
    if not os.path.exists(json_path):
        return []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except Exception:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=window)
    result = []
    for entry in all_data:
        try:
            d = datetime.fromisoformat(entry.get("date", ""))
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if d < cutoff:
            continue
        tp_s = (entry.get("tech_pulse") or {}).get("score")
        fg_s = (entry.get("fear_greed") or {}).get("score")
        if tp_s is not None and fg_s is not None:
            result.append(float(tp_s) - float(fg_s))
    return result


def _calc_divergence_zscore(div_history):
    """乖離値リストの最後の値のZスコアを返す（履歴不足の場合はNone）"""
    import statistics as _stats
    if len(div_history) < 5:
        return None
    mean = _stats.mean(div_history)
    stdev = _stats.stdev(div_history)
    if stdev == 0:
        return 0.0
    return round((div_history[-1] - mean) / stdev, 2)


def _get_tp_signal(div_value, div_zscore, fg_score):
    """3条件シグナル文字列を返す"""
    if div_value is None or div_zscore is None or fg_score is None:
        return ""
    if fg_score < 30 and div_value > 10 and div_zscore > 1.0:
        return "ハイテク先行反発シグナル"
    if div_value < -10 and div_zscore < -1.0:
        return "ハイテク先行下落注意"
    return ""


def _tp_label(score):
    if score <= 20: return "EXTREME FEAR"
    if score <= 35: return "FEAR"
    if score <= 50: return "CAUTION"
    if score <= 65: return "NEUTRAL"
    if score <= 80: return "GREED"
    return "EXTREME GREED"


def calc_tech_pulse_score(qqq_vs_ma125, vxn_vs_ma50, qqq_vs_spy_20d, history_90d):
    """Tech Pulseスコアを算出する（0〜100）— 過去90日パーセンタイル正規化"""
    try:
        from scipy.stats import percentileofscore
    except ImportError:
        print("[WARN] scipy未インストール。Tech Pulse固定50を返します。")
        return 50
    percentiles = []
    hist = history_90d or {}
    if qqq_vs_ma125 is not None and hist.get("qqq_vs_ma125"):
        percentiles.append(percentileofscore(hist["qqq_vs_ma125"], qqq_vs_ma125))
    if vxn_vs_ma50 is not None and hist.get("vxn_vs_ma50"):
        percentiles.append(100 - percentileofscore(hist["vxn_vs_ma50"], vxn_vs_ma50))
    if qqq_vs_spy_20d is not None and hist.get("qqq_vs_spy_20d"):
        percentiles.append(percentileofscore(hist["qqq_vs_spy_20d"], qqq_vs_spy_20d))
    if not percentiles:
        return 50
    score = max(0, min(100, round(sum(percentiles) / len(percentiles))))
    if vxn_vs_ma50 is None:
        capped = min(score, 75)
        if capped < score:
            print(f"[WARN] VXN欠落のためスコアをキャップ（上限75）: {score} → {capped}")
        score = capped
    return score


def get_realtime_data():
    """表示用テキストと構造化データを返す"""
    summary = ""
    data = {}

    # 主要指標
    main_tickers = {
        "米10年債": "^TNX",
        "VIX指数": "^VIX",
        "VIX9D（短期VIX）": "^VIX9D",
        "ドル円": "JPY=X",
        "日経平均": "^N225",
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "WTI原油": "CL=F",
        "金（GOLD）": "GC=F",
    }
    for name, ticker in main_tickers.items():
        hist = fetch_hist(ticker)
        summary += format_line(name, hist)
        if hist is not None and len(hist) >= 2:
            latest = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = latest - prev
            change_percent = (change / prev) * 100
            vol_latest = hist['Volume'].iloc[-1]
            vol_prev = hist['Volume'].iloc[-2]
            volume_ratio = vol_latest / vol_prev if vol_prev > 0 else None
            data[name] = {
                "value": round(latest, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
                "date": hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
            }
        else:
            data[name] = None

    # NYSE Composite
    summary += "\n--- NYSE騰落統計（代替指標） ---\n"
    nya_hist = fetch_hist("^NYA")
    sp_hist = fetch_hist("^GSPC")
    nya_data = None
    if nya_hist is not None and len(nya_hist) >= 2:
        nya_latest = nya_hist['Close'].iloc[-1]
        nya_prev = nya_hist['Close'].iloc[-2]
        nya_pct = (nya_latest - nya_prev) / nya_prev * 100
        vol_latest = nya_hist['Volume'].iloc[-1]
        vol_prev = nya_hist['Volume'].iloc[-2]
        vol_ratio = vol_latest / vol_prev if vol_prev > 0 else None
        vol_ratio_str = f"{vol_ratio:.2f}" if vol_ratio is not None else "N/A"
        last_date = nya_hist.index[-1].astimezone(JST).strftime('%m/%d')
        summary += f"● NYSE Composite(^NYA): {nya_latest:.2f} [{nya_pct:+.2f}%] | 前日比出来高比:{vol_ratio_str} ({last_date} 確定)\n"
        if sp_hist is not None and len(sp_hist) >= 2:
            sp_pct = (sp_hist['Close'].iloc[-1] - sp_hist['Close'].iloc[-2]) / sp_hist['Close'].iloc[-2] * 100
            divergence = nya_pct - sp_pct
            summary += f"● NYA対S&P500乖離（騰落代理）: {divergence:+.2f}%pt"
            if divergence < -0.5:
                summary += " → 中小型株が大型株を下回る＝市場内部の弱さ\n"
            elif divergence > 0.5:
                summary += " → 中小型株が大型株を上回る＝市場の広がり確認\n"
            else:
                summary += " → 概ね連動\n"
        nya_data = {
            "value": round(nya_latest, 2),
            "change_percent": round(nya_pct, 2),
            "volume_ratio": round(vol_ratio, 2) if vol_ratio is not None else None,
            "date": nya_hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
        }
        if sp_hist is not None and len(sp_hist) >= 2:
            nya_data["divergence_vs_sp"] = round(divergence, 2)
    else:
        summary += "● NYSE騰落統計（代替）: 取得制限あり\n"
    data["NYSE Composite"] = nya_data

    # スタイル・規模
    summary += "\n--- スタイル・規模間相対パフォーマンス ---\n"
    style_tickers = {
        "S&P500グロース(IVW)": "IVW",
        "S&P500バリュー(IVE)": "IVE",
        "Russell2000小型(RUT)": "^RUT",
    }
    style_data = {}
    for name, ticker in style_tickers.items():
        hist = fetch_hist(ticker)
        summary += format_line(name, hist)
        if hist is not None and len(hist) >= 2:
            latest = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            pct = (latest - prev) / prev * 100
            style_data[name] = pct
            data[name] = {
                "value": round(latest, 2),
                "change_percent": round(pct, 2),
                "date": hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
            }
        else:
            data[name] = None

    if "S&P500グロース(IVW)" in style_data and "S&P500バリュー(IVE)" in style_data:
        gv_diff = style_data["S&P500グロース(IVW)"] - style_data["S&P500バリュー(IVE)"]
        direction = "グロース優勢（リスクオン）" if gv_diff > 0 else "バリュー優勢（ディフェンシブ）"
        summary += f"  グロース対バリュー比（日次）: {gv_diff:+.2f}%pt → {direction}\n"
        data["グロース対バリュー比"] = {"diff_percent": round(gv_diff, 2)}

    sp500_hist = fetch_hist("^GSPC")
    if sp500_hist is not None and "Russell2000小型(RUT)" in style_data and len(sp500_hist) >= 2:
        sp_pct = (sp500_hist['Close'].iloc[-1] - sp500_hist['Close'].iloc[-2]) / sp500_hist['Close'].iloc[-2] * 100
        lsv_diff = sp_pct - style_data["Russell2000小型(RUT)"]
        direction = "大型優勢（質への逃避）" if lsv_diff > 0 else "小型優勢（リスク選好）"
        summary += f"  大型対小型比（日次、S&P500対RUT）: {lsv_diff:+.2f}%pt → {direction}\n"
        data["大型対小型比"] = {"diff_percent": round(lsv_diff, 2)}

    # VIX9D vs VIX比較
    summary += "\n--- VIX9D vs VIX（短期・中期リスク比較） ---\n"
    vix9d_hist = fetch_hist("^VIX9D")
    vix_hist2  = fetch_hist("^VIX")
    if vix9d_hist is not None and vix_hist2 is not None and len(vix9d_hist) >= 2 and len(vix_hist2) >= 2:
        vix9d_now  = float(vix9d_hist['Close'].iloc[-1])
        vix9d_prev = float(vix9d_hist['Close'].iloc[-2])
        vix_now    = float(vix_hist2['Close'].iloc[-1])
        vix9d_chg  = vix9d_now - vix9d_prev
        vix9d_pct  = vix9d_chg / vix9d_prev * 100 if vix9d_prev > 0 else 0
        ratio      = vix9d_now / vix_now if vix_now > 0 else None
        contango   = vix9d_now < vix_now  # True=順鞘(通常), False=逆転(短期リスクオフ)
        state      = "順鞘（通常）" if contango else "逆転（短期リスクオフ準備）"
        last_date  = vix9d_hist.index[-1].astimezone(JST).strftime('%m/%d')
        summary += f"● VIX9D: {vix9d_now:.2f} [{vix9d_chg:+.2f} ({vix9d_pct:+.1f}%)] ({last_date} 確定) → {state}\n"
        if ratio is not None:
            summary += f"  VIX9D対VIX比: {ratio:.3f} (VIX9D {'>' if not contango else '<'} VIX={vix_now:.2f})\n"
        data["VIX9D（短期VIX）"] = {
            "value": round(vix9d_now, 2),
            "change": round(vix9d_chg, 2),
            "change_percent": round(vix9d_pct, 2),
            "date": vix9d_hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
        }
        data["VIX9D対VIX比"] = {
            "value": round(ratio, 3) if ratio is not None else None,
            "contango": contango,
            "date": vix9d_hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
        }
    else:
        summary += "● VIX9D: 取得失敗\n"
        data["VIX9D（短期VIX）"] = None
        data["VIX9D対VIX比"] = None

    # クレジット
    summary += "\n--- クレジット・金融コンディション ---\n"
    hyg_hist = fetch_hist("HYG")
    lqd_hist = fetch_hist("LQD")
    summary += format_line("HYG（ハイイールド債ETF）", hyg_hist)
    summary += format_line("LQD（投資適格債ETF）", lqd_hist)

    if hyg_hist is not None and lqd_hist is not None:
        for hist, name in [(hyg_hist, "HYG（ハイイールド債ETF）"), (lqd_hist, "LQD（投資適格債ETF）")]:
            latest = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = latest - prev
            change_percent = (change / prev) * 100
            vol_latest = hist['Volume'].iloc[-1]
            vol_prev = hist['Volume'].iloc[-2]
            volume_ratio = vol_latest / vol_prev if vol_prev > 0 else None
            data[name] = {
                "value": round(latest, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
                "date": hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
            }
        try:
            ratio_now = hyg_hist['Close'].iloc[-1] / lqd_hist['Close'].iloc[-1]
            ratio_prev = hyg_hist['Close'].iloc[-2] / lqd_hist['Close'].iloc[-2]
            ratio_chg = ratio_now - ratio_prev
            last_date = hyg_hist.index[-1].astimezone(JST).strftime('%m/%d')
            direction = "HY優勢＝リスクオン" if ratio_chg > 0 else "スプレッド拡大示唆＝リスクオフ"
            summary += f"● HYG対LQD比（クレジット代理）: {ratio_now:.4f} [{ratio_chg:+.6f}] ({last_date} 確定) → {direction}\n"
            data["HYG対LQD比"] = {
                "value": round(ratio_now, 4),
                "change": round(ratio_chg, 6),
                "date": hyg_hist.index[-1].astimezone(JST).strftime('%Y-%m-%d')
            }
        except Exception as e:
            summary += f"● HYG/LQD比率: 計算エラー ({e})\n"
    else:
        data["HYG（ハイイールド債ETF）"] = None
        data["LQD（投資適格債ETF）"] = None

    return summary, data


def get_market_news():
    """RSSフィードからニュース取得（requests使用）"""
    if not os.path.exists(RSS_LIST_FILE):
        print(f"[WARN] RSSファイルが見つかりません: {RSS_LIST_FILE}")
        return []
    with open(RSS_LIST_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    all_entries = []
    for url in urls:
        try:
            # requests で取得（非ASCII文字列でも自動処理）
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            for e in feed.entries[:8]:
                all_entries.append(f"T: {e.title}\nS: {e.get('summary', '')}")
        except Exception as e:
            print(f"[WARN] RSS取得失敗: {url} ({e})")
    print(f"[INFO] RSS取得件数: {len(all_entries)} 件")
    return all_entries


def analyse_market(realtime_data, news_context):
    """xAI Grok API（OpenAI互換エンドポイント）で市場分析を実行する"""
    news_section = news_context if news_context.strip() else "（ニュース取得なし）"
    prompt = f"""
あなたはプロの機関投資家専属アナリストだ。以下の最新数値と需給・ニュースを統合し報告せよ。

【全体要約】
最初に必ず以下の形式で全体要約を書け（他の項目より前に置くこと）。
  結論：[市場フェーズ判定]。[現状の核心を1文で]。
  行動示唆：[具体的な投資行動の示唆を1〜2文で。「様子見」「買い場探し」「利確検討」等の具体的方向性を示せ]。

1. 市場フェーズ判定（晴れ・曇り・嵐）
結論（例：「判定：曇り」）を必ず冒頭の一文に置き、その後に根拠を続けよ。
根拠には必ずVIXと前日比出来高比を含めること。価格下落＋出来高増なら「嵐」の予兆として厳しく判定せよ。

2. 金利・債券（米10年債）
1行解説：現在の利回り水準と方向を端的に述べよ。
なぜ重要か：株式バリュエーションと資金フローへの影響を投資判断の観点から1文で示せ。

3. 恐怖指数・心理（VIX）
1行解説：現在のVIX水準と示す心理状態を端的に述べよ。
なぜ重要か：エントリー・エグジットタイミングの判断基準としての意味を1文で示せ。

4. 通貨の勢い（ドル円）
1行解説：現在のドル円水準と方向を端的に述べよ。
なぜ重要か：日本株・輸出株への影響と円ヘッジコストの観点から1文で示せ。

5. 指数・需給（日経平均、S&P500、NYSE騰落統計）
1行解説：主要指数の方向と出来高の特徴を端的に述べよ。
なぜ重要か：市場の内部構造（広がりか集中か）の観点から投資判断への意味を1文で示せ。
出来高比1.1以上かつ価格下落があればディストリビューション（大口売り抜け）の疑いを指摘せよ。
安値圏からの反発局面において、反発4日目以降に出来高増加を伴う大幅上昇（+1.7%以上）が確認された場合はフォロースルーデイ（買い転換シグナル）として明示せよ。
NYSE騰落比率が指数と逆行していればヒンデンブルグ・オーメン的な市場内部の脆弱性を指摘せよ。

6. スタイル・規模間相対パフォーマンス（グロース対バリュー比、大型対小型比）
1行解説：グロース対バリュー・大型対小型の方向を端的に述べよ。
なぜ重要か：リスク選好度の変化とポートフォリオ傾斜判断への意味を1文で示せ。
グロース対バリュー比（日次）とその解釈（リスクオン/ディフェンシブ）を一行で述べよ。
大型対小型比（日次）と質への逃避の有無を一行で述べよ。
これを踏まえ指数コメントと接続し、市場の立体的な需給構造を考察せよ。

7. コモディティ（原油、金）
1行解説：原油・金の方向と水準を端的に述べよ。
なぜ重要か：インフレ期待とリスク回避需要の読み方を投資判断の観点から1文で示せ。
金対原油比の方向にも触れ、インフレヘッジ需要とリスク回避の強弱を読み解け。
原油下落時は「地政学リスクの緩和」か「需要減退懸念」かを必ず区別して明記せよ。

8. クレジット・金融コンディション（HYG、LQD、HYG対LQD比）
1行解説：HYG・LQD・比率の方向と示すクレジット環境を端的に述べよ。
なぜ重要か：信用収縮リスクの先行指標としての意味を1文で示せ。
以下の三点を必ず個別に一行ずつ明記した上で総合判定せよ。
  株（S&P500の方向）→ リスクオン/リスクオフ
  債券（米10年債利回りの方向）→ リスクオン/リスクオフ
  クレジット（HYG対LQD比の方向）→ リスクオン/リスクオフ
週次レベルの変化でも有意な動きがあれば言及せよ。

9. 短期警戒ポイント（重要イベント）
冒頭の説明文は不要。イベントの列挙から直接始めよ。
今後5営業日以内に予定される具体的なイベントを列挙し、各イベントに「予想値・前回値・市場への影響シナリオ」を一行で添えよ。
ニュースから読み取れる情報がない場合でも、現在の市場フェーズに照らして最も注視すべき指標を根拠とともに示せ。
「地政学的リスク」「各国中央銀行の発言」等の汎用表現のみの列挙は禁止。

10. 総評・相関分析（需給面からの踏み込んだ考察）

制約：
- 出力の先頭は必ず【全体要約】から始めること。【全体要約】の前に他のテキストを置くことは禁止。
- 各項目（1〜10）の冒頭に、その項目に関連する数値を「● 指標名: 数値 増減 前日比出来高比 確定日」の形式で必ず1行書くこと。冒頭に全指標をまとめて列挙することは禁止。各項目内に分散して記載せよ。
- 比較・相対表現は必ず「○○対△△比」の形式で統一すること（例：グロース対バリュー比、大型対小型比、HYG対LQD比）。
- スタイル・規模比較は日次変化に基づく分析である旨を明記すること。
- 総評では現在のデータから導ける具体的なシグナルや閾値を示せ。「○○する可能性も否定できない」等の汎用的な免責表現は使用禁止。
- 地政学リスクに言及する場合は必ず具体的な地域・事象・発言者を明記せよ。「地政学リスク」単独の抽象表現は禁止。
- 出力は必ず日本語（ひらがな・カタカナ・漢字・英数字・記号）のみ使用すること。韓国語・中国語・その他外国語文字の混入は厳禁。
- Markdown記法（##、**、--- 等）は一切使用禁止。プレーンテキストのみで出力せよ。
- 仮想通貨は無視。日本語回答。最後に俳句を一句（5-7-5）のみ添えること。複数句・改行は禁止し必ず一行で書くこと。音数（5-7-5）を厳守せよ。
- 総評・各項目の締め文として「注意が必要である」「注視が必要である」「懸念される」等の汎用表現で終えることは禁止。必ず具体的なシグナルや水準で締めくくれ。

【最新データ】:
{realtime_data}

【背景ニュース】:
{news_section}
"""
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}",
    }
    models = ["grok-3-mini", "grok-3", "grok-2-1212"]
    last_error = None
    for model in models:
        try:
            print(f"[INFO] Grokモデル試行中: {model}")
            resp = requests.post(url, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4096,
                "temperature": 0.3,
            }, timeout=120)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            print(f"[OK] Grokモデル成功: {model}")
            return text
        except Exception as e:
            print(f"[WARN] Grokモデル失敗 ({model}): {e}")
            last_error = e
    print("[ERROR] すべてのGrokモデルで失敗しました")
    raise last_error


def extract_judgment(report_text):
    # 全角・半角コロンどちらにも対応。文字列中の最初の判定を返す。
    match = re.search(r'判定[：:]\s*(嵐|曇り|晴れ)', report_text)
    return match.group(1) if match else "不明"



def collect_asset_flow():
    """
    資産クラス間資金フロービジュアライザー用データ収集
    並び順（安全→リスク）: 超短期国債→短期国債→金→長期国債→投資適格社債→HY社債→株式
    """
    ASSETS = [
        {"key": "ultra_short", "label": "超短期国債", "ticker": "SHV",  "desc": "1-3ヶ月T-Bill ETF"},
        {"key": "short_bond",  "label": "短期国債",   "ticker": "^IRX", "desc": "3ヶ月T-Bill利回り"},
        {"key": "gold",        "label": "金",          "ticker": "GLD",  "desc": "金ETF"},
        {"key": "long_bond",   "label": "長期国債",    "ticker": "TLT",  "desc": "20年超米国債ETF"},
        {"key": "ig_bond",     "label": "投資適格社債","ticker": "LQD",  "desc": "投資適格社債ETF"},
        {"key": "hy_bond",     "label": "HY社債",      "ticker": "HYG",  "desc": "ハイイールド社債ETF"},
        {"key": "equity",      "label": "株式",         "ticker": "SPY",  "desc": "S&P500 ETF"},
    ]
    result = {}
    for a in ASSETS:
        try:
            hist = fetch_hist(a["ticker"], period="5d")
            if hist is None or len(hist) < 2:
                result[a["key"]] = None
                continue
            latest = float(hist["Close"].iloc[-1])
            prev   = float(hist["Close"].iloc[-2])
            chg_pct = (latest - prev) / prev * 100 if prev > 0 else 0
            date_str = hist.index[-1].astimezone(JST).strftime("%Y-%m-%d")
            result[a["key"]] = {
                "label":    a["label"],
                "ticker":   a["ticker"],
                "desc":     a["desc"],
                "value":    round(latest, 4),
                "change_pct": round(chg_pct, 3),
                "date":     date_str,
            }
            print(f"[INFO] asset_flow {a['label']}({a['ticker']}): {chg_pct:+.2f}%")
        except Exception as e:
            print(f"[WARN] asset_flow {a['ticker']}: {e}")
            result[a["key"]] = None
    return result

def save_data_to_json_and_csv(report_text, structured_data, sentiment_data, fear_greed_data=None, tech_pulse_data=None, asset_flow_data=None):
    os.makedirs(DATA_DIR, exist_ok=True)
    jst_now = datetime.now(JST)
    date_str = jst_now.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    judgment = extract_judgment(report_text)

    # JSON
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    all_data = []
                else:
                    f.seek(0)
                    all_data = json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[WARN] JSONファイルが破損しています。新しく作成します: {JSON_PATH} (エラー: {e})")
            all_data = []
    else:
        all_data = []

    new_entry = {
        "date": date_str,
        "judgment": judgment,
        "indicators": structured_data,
        "sentiment": sentiment_data,
        "fear_greed": fear_greed_data,
        "tech_pulse": tech_pulse_data,
        "asset_flow": asset_flow_data,
        "summary": report_text
    }
    # 同日の既存エントリを削除して上書き（同日に複数回実行された場合の重複防止）
    today = date_str[:10]
    all_data = [d for d in all_data if d.get("date", "")[:10] != today]
    all_data.append(new_entry)

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] JSON保存完了: {JSON_PATH} (全{len(all_data)}件)")

    # CSV
    row = {"date": date_str, "judgment": judgment}
    for key, value in structured_data.items():
        if value is None:
            continue
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                col_name = f"{key}_{subkey}"
                row[col_name] = subvalue
        else:
            row[key] = value
    row["sentiment_score"] = sentiment_data.get("score", "")
    row["sentiment_label"] = sentiment_data.get("label", "")
    row["summary"] = report_text

    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"[INFO] CSV保存完了: {CSV_PATH}")


def send_email(body, sentiment_data):
    jst_now = datetime.now(JST)
    score = sentiment_data.get("score", "?")
    label = sentiment_data.get("label", "")
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = f"\U0001f99d02_\u3010\u5e02\u6cc1\u5206\u6790\u3011{label} ({score}) {jst_now.strftime('%m/%d %H:%M')}"
    msg['From'], msg['To'] = GMAIL_USER, GMAIL_USER
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.send_message(msg)
        print("[INFO] メール送信成功")
    except Exception as e:
        print(f"[ERROR] メール送信失敗: {e}")
        raise


def fetch_cnn_fear_greed():
    """CNN Fear & Greed Indexを取得する"""
    try:
        import fear_greed as fg
        data = fg.get()
        score = data.get("score")
        rating = data.get("rating", "")
        history = data.get("history", {})
        print(f"[INFO] CNN Fear & Greed: {score:.1f} ({rating})")
        return {
            "score": round(score, 1) if score is not None else None,
            "rating": rating,
            "previous_close": history.get("1w"),
            "one_week_ago": history.get("1w"),
            "one_month_ago": history.get("1m"),
        }
    except ImportError:
        print("[WARN] fear-greed パッケージ未インストール。CNN F&Gスキップ。")
        return None
    except Exception as e:
        print(f"[WARN] CNN Fear & Greed取得失敗: {e}")
        return None


if __name__ == "__main__":
    realtime_text, structured_data = get_realtime_data()

    # センチメントスコア算出
    sentiment_data = compute_sentiment(structured_data)
    print(f"[INFO] センチメントスコア: {sentiment_data['score']} ({sentiment_data['label']})")
    for k, v in sentiment_data["sub_scores"].items():
        print(f"  {k}: {v['score']:.1f} (weight={v['weight']}, raw={v['raw']})")

    # CNN Fear & Greed Index取得
    fear_greed_data = fetch_cnn_fear_greed()

    # Tech Pulse（ナスダック感情指数）算出
    qqq_vs_ma125, qqq_vs_spy_20d = fetch_qqq_tech_data()
    vxn_latest, vxn_vs_ma50 = fetch_vxn_from_fred()
    fg_score_tech = fetch_fg_score_from_feargreedchart()
    history_90d = _load_tech_pulse_history(JSON_PATH, window=90)
    tp_score = calc_tech_pulse_score(qqq_vs_ma125, vxn_vs_ma50, qqq_vs_spy_20d, history_90d)
    # 異常値ガード: score=100 かつ直前スコアとの差が20以上なら前回値を保持
    _prev_tp_score = _load_prev_tech_pulse_score(JSON_PATH)
    if tp_score == 100 and _prev_tp_score is not None and abs(tp_score - _prev_tp_score) >= 20:
        print(f"[WARN] Tech Pulse異常値検出: score={tp_score} (前回={_prev_tp_score}) → 前回値を保持")
        tp_score = _prev_tp_score
    tp_label = _tp_label(tp_score)

    # 乖離・Zスコア・シグナル
    div_value = round(float(tp_score) - float(fg_score_tech), 1) if fg_score_tech is not None else None
    div_hist = _load_div_history(JSON_PATH, window=90)
    if div_value is not None:
        div_hist.append(div_value)
    div_zscore = _calc_divergence_zscore(div_hist)
    tp_signal = _get_tp_signal(div_value, div_zscore, fg_score_tech)

    tech_pulse_data = {
        "score": tp_score,
        "label": tp_label,
        "components": {
            "qqq_vs_ma125": qqq_vs_ma125,
            "vxn_latest": vxn_latest,
            "vxn_vs_ma50": vxn_vs_ma50,
            "qqq_vs_spy_20d": qqq_vs_spy_20d,
            "fg_score": fg_score_tech,
            "vxn_available": vxn_vs_ma50 is not None,
        },
        "divergence": {
            "value": div_value,
            "zscore": div_zscore,
            "signal": tp_signal,
        },
    }
    print(f"[INFO] Tech Pulseスコア: {tp_score} ({tp_label}), 乖離={div_value}, Z={div_zscore}, シグナル={tp_signal or 'なし'}")

    news = get_market_news()
    if not news:
        print("[WARN] ニュースなしで分析を実行します。")
    report = analyse_market(realtime_text, "\n".join(news))
    asset_flow_data = collect_asset_flow()
    save_data_to_json_and_csv(report, structured_data, sentiment_data, fear_greed_data, tech_pulse_data, asset_flow_data)
    if GMAIL_USER and GMAIL_PASSWORD:
        send_email(report, sentiment_data)
    else:
        print("[INFO] メール送信スキップ（認証情報なし）")
