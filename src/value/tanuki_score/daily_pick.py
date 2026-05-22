"""
daily_pick.py
TANUKI SCOREの特選銘柄を毎日選出し、Grok AIによる投資判断レポートを生成する。

フロー:
  1. 全銘柄をスコアリング（ファンダ/タイミング/分類）
  2. 選出ロジック（優先①分類変化 → ②Grokニュース → ③ファンダ上位未選出）
  3. GrokでAIレポート生成
  4. daily_pick.json / history.json を保存
"""
import json
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCS         = PROJECT_ROOT / "docs"
TANUKI_DATA  = DOCS / "value-monitor" / "tanuki_valuation" / "data"
HYPE_DATA    = DOCS / "value-monitor" / "hypecore" / "data"
EPS_DATA     = DOCS / "value-monitor" / "adjusted_eps_analyzer" / "data"
MKT_PATH     = DOCS / "market-monitor" / "market-pulse" / "data" / "market_data.json"
OUT_DIR      = DOCS / "integrated-dashboard"
PICK_FILE    = OUT_DIR / "daily_pick.json"
HIST_FILE    = OUT_DIR / "history.json"

JST = timezone(timedelta(hours=9))

XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"

# ── Scoring（index.htmlのJS実装と同一ロジック） ───────────────
def _pt(cond_hi, cond_mid, pts_hi, pts_mid, val):
    if val is None:
        return 0
    if cond_hi(val):
        return pts_hi
    if cond_mid(val):
        return pts_mid
    return 0

def calc_funda(rev_yoy, rule40, eps_yoy_pct, fcf_base):
    s = 0
    s += _pt(lambda v: v > 20,  lambda v: v >= 0,  25, 15, rev_yoy)
    s += _pt(lambda v: v > 40,  lambda v: v >= 20, 25, 15, rule40)
    s += _pt(lambda v: v > 20,  lambda v: v >= 0,  25, 15, eps_yoy_pct)
    s += 25 if (fcf_base is not None and fcf_base > 0) else 0
    return s

def calc_timing(upside, fg, stage):
    s = 0
    if upside is not None:
        s += 40 if upside > 30 else 25 if upside >= 10 else 10 if upside >= 0 else 0
    s += 40 if fg < 30 else 25 if fg < 50 else 10 if fg < 70 else 0
    if stage is not None:
        s += 20 if stage == 1 else 15 if stage == 2 else 5 if stage == 3 else 0
    return s

def classify(f, t):
    if f < 25:             return "論外"
    if f >= 50 and t >= 50: return "仕込み時"
    if f >= 50:             return "仕込み待ち"
    if t >= 60:             return "利確検討"
    return "様子見"

# ── Data loaders ──────────────────────────────────────────────
def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def load_tickers():
    d = load_json(TANUKI_DATA / "tickers.json")
    return d.get("tickers", []) if isinstance(d, dict) else []

def load_market():
    data = load_json(MKT_PATH)
    return data[-1] if isinstance(data, list) and data else {}

def load_tanuki(ticker):
    return load_json(TANUKI_DATA / ticker / "latest.json") or {}

def load_hype(ticker):
    d = load_json(HYPE_DATA / f"{ticker}_poc.json")
    if not isinstance(d, dict):
        return {}
    monthly = d.get("monthly", [])
    return monthly[-1] if monthly else {}

def load_eps_summary():
    d = load_json(EPS_DATA / "summary.json")
    if not isinstance(d, dict):
        return {}
    return {t["ticker"]: t for t in d.get("tickers", [])}

def load_eps_annual_latest(ticker):
    d = load_json(EPS_DATA / ticker / "annual.json")
    if not isinstance(d, dict):
        return {}
    years = d.get("years", [])
    return years[0] if years else {}

def load_history():
    h = load_json(HIST_FILE)
    return h if isinstance(h, list) else []

def save_history(history):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(HIST_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

# ── Score all stocks ──────────────────────────────────────────
def score_all(tickers, mkt):
    fg          = mkt.get("fear_greed", {}).get("score", 50)
    eps_summary = load_eps_summary()
    results     = []

    for ticker in tickers:
        tk = load_tanuki(ticker)
        hc = load_hype(ticker)
        ep = eps_summary.get(ticker, {})

        rev_yoy   = hc.get("rev_yoy")
        rule40    = hc.get("rule40")
        yoy_dec   = ep.get("yoy_growth")
        eps_yoy   = yoy_dec * 100 if yoy_dec is not None else None
        fcf_raw   = tk.get("fcf_base")
        fcf_base  = (
            fcf_raw.get("base_fcf") if isinstance(fcf_raw, dict)
            else fcf_raw if isinstance(fcf_raw, (int, float))
            else None
        )
        upside = tk.get("upside_percent")
        stage  = hc.get("stage")

        f   = calc_funda(rev_yoy, rule40, eps_yoy, fcf_base)
        t   = calc_timing(upside, fg, stage)
        cat = classify(f, t)

        results.append({
            "ticker":  ticker,
            "company": ep.get("company_name", ticker),
            "funda":   f,
            "timing":  t,
            "category": cat,
        })

    return results

# ── Selection logic ───────────────────────────────────────────
def select_ticker(stocks, history, today_str):
    """
    優先①: 前日から分類が変わった銘柄
    優先②: Grokニュース検索で重大ニュースのある銘柄
    優先③: ファンダ上位・最長未選出
    """
    today_cats = {s["ticker"]: s["category"] for s in stocks}

    # 優先①: 前日の全分類と比較
    if history:
        yesterday = history[0]
        prev_cats = yesterday.get("all_categories", {})
        if prev_cats:
            changed = [
                s for s in stocks
                if prev_cats.get(s["ticker"]) and prev_cats[s["ticker"]] != s["category"]
            ]
            if changed:
                # カテゴリ重要度（仕込み時 → 仕込み待ち → 利確検討 の順で優先）
                order = {"仕込み時": 0, "仕込み待ち": 1, "利確検討": 2, "様子見": 3, "論外": 4}
                changed.sort(key=lambda s: (order.get(s["category"], 9), -s["funda"]))
                best = changed[0]
                old_cat = prev_cats.get(best["ticker"], "不明")
                return best, f"分類変化: {old_cat} → {best['category']}"

    # 優先②: Grokニュース検索（API設定済みかつ良質銘柄のみ対象）
    if XAI_API_KEY:
        candidates = [s["ticker"] for s in stocks if s["category"] in ("仕込み時", "仕込み待ち")][:20]
        if candidates:
            pick, reason = grok_news_search(candidates, today_str)
            if pick:
                s = next((x for x in stocks if x["ticker"] == pick), None)
                if s:
                    return s, reason

    # 優先③: ファンダ上位・最長未選出（直近の選出銘柄は除外）
    last_pick = history[0]["ticker"] if history else None
    candidates = [s for s in stocks if s["ticker"] != last_pick] or stocks

    pick_idx = {h["ticker"]: i for i, h in enumerate(history)}
    candidates.sort(key=lambda s: (-pick_idx.get(s["ticker"], len(history) + 1), -s["funda"]))
    return candidates[0], "ファンダスコア上位・最長未選出"

# ── Grok API helpers（collect_and_send.py と同方式） ─────────
def _call_grok(messages, temperature=0.3, max_tokens=4096):
    """grok-3-mini → grok-3 → grok-2-1212 の順でフォールバック呼び出し"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}",
    }
    models = ["grok-3-mini", "grok-3", "grok-2-1212"]
    last_error = None
    for model in models:
        try:
            print(f"  [grok] 試行: {model}")
            resp = requests.post(
                XAI_API_URL,
                headers=headers,
                json={
                    "model":       model,
                    "messages":    messages,
                    "max_tokens":  max_tokens,
                    "temperature": temperature,
                },
                timeout=120,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            print(f"  [grok] 成功: {model}")
            return text
        except Exception as e:
            print(f"  [grok] 失敗 ({model}): {e}")
            last_error = e
    raise last_error

def _extract_json(text):
    """テキストからJSONオブジェクトを抽出する（マークダウンコードブロック対応）"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # ```json ... ``` や ``` ... ``` の中身を取り出す
    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None


def grok_news_search(ticker_list, date_str):
    """Grokで本日重大ニュースのある銘柄を1件検索する"""
    prompt = (
        f"以下の銘柄リストのうち、今日（{date_str}）重要なニュースがある"
        f"銘柄を1つ選び、その理由を50字以内で答えよ：{', '.join(ticker_list)}\n"
        f"回答はJSONオブジェクトのみ返すこと。\n"
        f'回答形式: {{"ticker": "XXXX", "reason": "理由"}}'
    )
    try:
        text   = _call_grok([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=256)
        parsed = _extract_json(text)
        if not parsed:
            print(f"  [news] JSON解析失敗: {text[:120]}")
            return None, None
        ticker = parsed.get("ticker", "").upper().strip()
        reason = parsed.get("reason", "")
        if ticker in ticker_list:
            return ticker, f"{reason}（Grok選出）"
        print(f"  [news] 返答ticker '{ticker}' がリストにない、スキップ")
    except Exception as e:
        print(f"  [news] Error: {e}")
    return None, None

# ── Report generation ─────────────────────────────────────────
def build_data_package(stock, mkt):
    """Grokに渡す統合データパッケージを構築する"""
    ticker = stock["ticker"]
    tk     = load_tanuki(ticker)
    hc     = load_hype(ticker)
    ann    = load_eps_annual_latest(ticker)

    fcf_raw  = tk.get("fcf_base")
    fcf_base = (
        fcf_raw.get("base_fcf") if isinstance(fcf_raw, dict)
        else fcf_raw if isinstance(fcf_raw, (int, float))
        else None
    )
    rpo_raw = tk.get("rpo_adjustment")
    rpo_pv  = rpo_raw.get("rpo_pv") if isinstance(rpo_raw, dict) else None

    return {
        "ticker":     ticker,
        "company":    stock["company"],
        "funda_score":  stock["funda"],
        "timing_score": stock["timing"],
        "category":   stock["category"],
        "tanuki": {
            "intrinsic_value_per_share": tk.get("intrinsic_value_per_share"),
            "upside_percent":            tk.get("upside_percent"),
            "fcf_base":                  fcf_base,
            "growth_rate":               tk.get("growth", {}).get("rate") if isinstance(tk.get("growth"), dict) else None,
            "wacc":                      tk.get("wacc", {}).get("value") if isinstance(tk.get("wacc"), dict) else None,
            "alpha":                     tk.get("alpha"),
            "rpo_pv":                    rpo_pv,
        },
        "hypecore": {
            "stage":              hc.get("stage"),
            "stage_label":        hc.get("stage_label"),
            "substage_label":     hc.get("substage_label"),
            "rev_yoy":            hc.get("rev_yoy"),
            "rule40":             hc.get("rule40"),
            "peg_ratio":          hc.get("peg_ratio"),
            "short_pct_float":    hc.get("short_pct_float"),
            "eps_surprise":       hc.get("eps_surprise"),
            "expectation_score":  hc.get("expectation_score"),
            "fundamental_score":  hc.get("fundamental_score"),
            "momentum_score":     hc.get("momentum_score"),
        },
        "eps_annual": {
            "gaap_eps":      ann.get("gaap_eps"),
            "adjusted_eps":  ann.get("adjusted_eps"),
            "adjustments":   ann.get("adjustments", [])[:5],
        },
        "market": {
            "fear_greed_score": mkt.get("fear_greed", {}).get("score"),
            "tech_pulse_score": mkt.get("tech_pulse", {}).get("score") if isinstance(mkt.get("tech_pulse"), dict) else None,
            "risk_off_score":   mkt.get("credit", {}).get("risk_off_score") if isinstance(mkt.get("credit"), dict) else None,
            "vix":              mkt.get("indicators", {}).get("VIX指数", {}).get("value") if isinstance(mkt.get("indicators"), dict) else None,
        },
    }

def generate_report(stock, mkt):
    """Grokで投資判断レポートを生成する"""
    data_pkg = build_data_package(stock, mkt)
    ticker   = stock["ticker"]
    company  = stock["company"]
    now_jst  = datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

    prompt = f"""あなたは投資アナリストです。以下のデータを統合して、\
{ticker}（{company}）の投資判断レポートを日本語で作成してください。

=== 指標の定義・コンセプト ===

【TANUKI VALUATION】
- 理論株価: Rm=10%固定（β=0）の市場独立DCFで算出。市場センチメントに依存しない内在価値。
- upside_percent: (理論株価 - 現在株価) / 現在株価 × 100。プラス=割安、マイナス=割高。
- alpha(α): ROE平均×内部留保率÷Rm×0.7で算出。企業の自己資本効率から導くプレミアム。セクター別上限あり。
- WACC: Rm=10%固定（β除外）。市場リスクに依存しない割引率。
- FCF: OCF - CapEx全額控除。SBCはOCFに含めたまま（意図的設計）。
- RPO_PV: 前年比超過の非連続需要分×営業利益率でPV化。αの外に加算。赤字企業はゼロ。
- P_t = V0×(1+α) + RPO_PV

【HypeCore】
- stage1=蓄積期: 実態改善中だが市場未認識。最良の仕込み場。
- stage2=上昇期: 市場が実態を認識し始めた局面。まだ上昇余地あり。
- stage3=陶酔期: 期待が実態を先行。過熱リスク。
- stage4=期待剥落期/崩壊期: 期待と実態の乖離が修正される局面。
- expectation_score: マイナス=市場の期待が過熱（株価が実態より高い）、プラス=過小評価。
- fundamental_score: プラス=ファンダが改善中。
- Rule of 40: 売上成長率(%) + FCFマージン(%)。40以上=健全、100超=極めて優秀。
- substage: フェーズ内の細分類。「入口」=まだ余地あり、「中盤」=継続、「出口」=転換注意。

【EPS Analyzer】
- GAAP EPS: 全コスト（SBC・のれん償却等）を含む法定EPS。
- Adjusted EPS: 一過性・非現金コストを除いた実力EPS。
- eps_ratio: (Adj - GAAP) / |GAAP| × 100。高いほど市場がGAAPで判断している場合に実力を過小評価しやすい。
- gaap_to_adj_positive: GAAPで赤字だがAdjでは黒字。市場の誤認リスクが最も高い状態。

【Market Pulse】
- fear_greed_score: 0=極度の恐怖（歴史的買い場）、50=中立、100=極度の強欲（売り検討）。
- risk_off_score: 0=RISK ON（株式に追い風）、67以上=RISK OFF（リスク回避）。
- tech_pulse: NASDAQベースのセンチメント。fear_greed_scoreとの乖離が大きい場合NASDAQ固有の動き。

【TANUKI SCORE分類】
- 仕込み時: ファンダスコア≥50 かつ タイミングスコア≥50
- 仕込み待ち: ファンダスコア≥50 かつ タイミングスコア<50
- 利確検討: ファンダスコア25-49 かつ タイミングスコア≥60
- 様子見: その他
- 論外: ファンダスコア<25

=== 記述ルール ===

1. 各指標の数値と結論を直接繋げず、必ず因果関係を説明すること。
   ×『売上YoY73%と市場期待は高い』
   ○『売上YoY73%・Rule of 40=136と事業の実力は極めて高く、その結果として市場の期待値も高止まりしている』

2. 理論株価と現在株価を必ず両方記載すること。
   例：『理論株価481ドル（現在株価219ドル、乖離+122%）』

3. HypeCoreフェーズとTANUKI SCOREカテゴリが一見矛盾する場合
   （例：陶酔期なのに仕込み時）は必ずその理由を説明すること。

=== 定量データ ===
{json.dumps(data_pkg, ensure_ascii=False, indent=2)}

【作成日時】{now_jst}

以下のJSONキーを持つオブジェクトを返してください。各値は200〜400字の分析文です：

{{
  "fundamental": "【ファンダメンタル評価】売上成長・収益性・FCF・理論株価と現在株価の両方を明記した上で乖離率を評価。企業のビジネスモデルの強み・弱みを踏まえ、数値から結論への因果関係を説明する。",
  "expectation": "【期待値評価】HypeCoreフェーズ・expectation_score・substageを分析。Non-GAAP調整による市場の誤認可能性を評価。フェーズとTANUKI SCOREカテゴリが矛盾する場合はその理由を説明する。",
  "news": "【最近のニュース・時事】{ticker}に関する直近の重要な事象（契約・決算・規制・競合動向等）を記載。知識ベースで把握できる情報に基づき、株価に影響する事象を述べる。",
  "timing": "【タイミング評価】market_pulse（fear_greed・risk_off・tech_pulse）・HypeCoreフェーズ・TANUKI乖離率を統合評価。今買うべきか/待つべきか/売るべきかを数値から因果関係で導いて明確に示す。",
  "summary": "【総合所見】上記を統合した投資判断（2〜3文）。注目すべき次のトリガーイベントを明記。"
}}

本日（{now_jst}）時点の情報として分析してください。"""

    print(f"  [report] Calling Grok for {ticker}...")
    try:
        text   = _call_grok([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=4096)
        parsed = _extract_json(text)
        if not parsed:
            raise ValueError(f"JSON解析失敗: {text[:200]}")
        # Ensure all required keys exist
        for key in ("fundamental", "expectation", "news", "timing", "summary"):
            if key not in parsed:
                parsed[key] = "（データ取得エラー）"
        return parsed
    except Exception as e:
        print(f"  [report] Error: {e}")
        return {
            "fundamental": "レポート生成エラー",
            "expectation": "レポート生成エラー",
            "news":        "レポート生成エラー",
            "timing":      "レポート生成エラー",
            "summary":     f"Grok APIの呼び出し中にエラーが発生しました: {e}",
        }

# ── Main ──────────────────────────────────────────────────────
def main():
    now_jst   = datetime.now(JST)
    today_str = now_jst.strftime("%Y-%m-%d")
    print(f"[daily_pick] Starting — {today_str} JST")

    mkt     = load_market()
    tickers = load_tickers()
    history = load_history()

    if not tickers:
        print("[daily_pick] No tickers found. Exiting.")
        sys.exit(1)

    # Score all
    print(f"[daily_pick] Scoring {len(tickers)} tickers...")
    stocks = score_all(tickers, mkt)
    stocks.sort(key=lambda s: (-s["funda"], -s["timing"]))

    # Select
    print("[daily_pick] Selecting ticker...")
    selected, reason = select_ticker(stocks, history, today_str)
    print(f"[daily_pick] Selected: {selected['ticker']} ({selected['category']}) — {reason}")

    # Generate report
    if not XAI_API_KEY:
        print("[daily_pick] XAI_API_KEY not set — skipping report.")
        report = {
            "fundamental": "APIキー未設定のためレポートを生成できません。",
            "expectation":  "APIキー未設定のためレポートを生成できません。",
            "news":         "APIキー未設定のためレポートを生成できません。",
            "timing":       "APIキー未設定のためレポートを生成できません。",
            "summary":      "XAI_API_KEY 環境変数を設定してください。",
        }
    else:
        report = generate_report(selected, mkt)

    # Build output
    generated_at = now_jst.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    output = {
        "generated_at":     generated_at,
        "ticker":           selected["ticker"],
        "company":          selected["company"],
        "selection_reason": reason,
        "funda_score":      selected["funda"],
        "timing_score":     selected["timing"],
        "category":         selected["category"],
        "report":           report,
    }

    # Save daily_pick.json
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(PICK_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[daily_pick] Saved → {PICK_FILE}")

    # Update history (keep 30 days, store all_categories for priority① detection)
    all_cats = {s["ticker"]: s["category"] for s in stocks}
    history.insert(0, {
        "date":           today_str,
        "ticker":         selected["ticker"],
        "company":        selected["company"],
        "reason":         reason,
        "category":       selected["category"],
        "funda_score":    selected["funda"],
        "timing_score":   selected["timing"],
        "all_categories": all_cats,
    })
    history = history[:30]
    save_history(history)
    print(f"[daily_pick] History updated ({len(history)} entries)")
    print("[daily_pick] Done.")

if __name__ == "__main__":
    main()
