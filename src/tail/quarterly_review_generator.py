#!/usr/bin/env python3
"""
TANUKI TAIL — quarterly_review_generator.py

review_queue.json の pending エントリに対して Grok を2回呼び出し、
四半期レビューレポートを生成する。

Stage 1: 投資テーゼ健全度評価（自然言語）
Stage 2: DCF入力用パラメータ生成（構造化JSON）

使用方法:
    python src/tail/quarterly_review_generator.py
    python src/tail/quarterly_review_generator.py --dry-run

出力: docs/portfolio/tail/data/reviews/{ticker}_{quarter}_review.json
環境変数:
    XAI_API_KEY  xAI Grok API キー（必須）
"""

import os
import sys
import json
import re
import csv
import time
import argparse
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

# ── パス設定 ──────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))

DATA_DIR          = os.path.join(repo_root, "docs", "portfolio", "tail", "data")
POSITIONS_DIR     = os.path.join(DATA_DIR, "positions")
KPI_DIR           = os.path.join(DATA_DIR, "kpi")
KPI_PROPOSALS_DIR = os.path.join(DATA_DIR, "kpi_proposals")
REVIEWS_DIR       = os.path.join(DATA_DIR, "reviews")
REVIEW_QUEUE_PATH = os.path.join(DATA_DIR, "review_queue.json")
TANUKI_DATA_DIR   = os.path.join(repo_root, "docs", "value-monitor", "tanuki_valuation", "data")
MACRO_DATA_DIR    = os.path.join(repo_root, "docs", "market-monitor", "macro-pulse", "data")
PORTFOLIO_PATH    = os.path.join(repo_root, "docs", "portfolio", "data", "portfolio.json")

JST = ZoneInfo("Asia/Tokyo")

# ── Grok API 設定 ──────────────────────────────────────────────
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_URL    = "https://api.x.ai/v1/chat/completions"
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Grok API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def call_grok(
    user_prompt: str,
    system_prompt: str = "",
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str:
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY が設定されていません")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}",
    }
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    last_error: Optional[Exception] = None
    for model in GROK_MODELS:
        try:
            print(f"  [Grok] モデル試行: {model}")
            resp = requests.post(
                GROK_URL,
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
            print(f"  [Grok] 成功: {model}")
            return text
        except Exception as e:
            print(f"  [Grok] 失敗 ({model}): {e}")
            last_error = e
            time.sleep(1)
    raise RuntimeError(f"すべてのGrokモデルで失敗: {last_error}")


def extract_json_from_response(text: str) -> Dict[str, Any]:
    # ```json ... ``` ブロックを優先して抽出
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # フォールバック: 生テキストから { } を探す
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError(f"JSONが見つかりません: {text[:300]}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# データ読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_thesis(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(POSITIONS_DIR, f"{ticker}_thesis.json")
    if not os.path.exists(path):
        print(f"  [WARN] thesis.json 未発見: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_layer2_kpi(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(KPI_DIR, f"{ticker}_layer2.json")
    if not os.path.exists(path):
        print(f"  [WARN] layer2.json 未発見: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_layer3_kpi(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(KPI_DIR, f"{ticker}_layer3.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_tanuki_valuation(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(TANUKI_DATA_DIR, ticker, "latest.json")
    if not os.path.exists(path):
        print(f"  [WARN] latest.json 未発見: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    comp = data.get("components", {})
    return {
        "intrinsic_value": round(data.get("intrinsic_value_per_share") or 0, 2),
        "current_price":   round(comp.get("current_price") or 0, 2),
        "deviation_rate":  round(data.get("upside_percent") or 0, 1),
        "tanuki_score":    data.get("tanuki_score", "N/A"),
    }


def load_macro_context() -> Optional[Dict[str, Any]]:
    wa_path = os.path.join(MACRO_DATA_DIR, "05_weekly_analysis.csv")
    lq_path = os.path.join(MACRO_DATA_DIR, "05_liquidity.csv")

    ctx: Dict[str, Any] = {}

    if os.path.exists(wa_path):
        with open(wa_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if rows:
            last = rows[-1]
            ctx.update({
                "score":            last.get("score", ""),
                "phase":            last.get("phase", ""),
                "score_change_1w":  last.get("score_change_1w", ""),
                "score_change_1m":  last.get("score_change_1m", ""),
                "watchpoints":      last.get("watchpoints", ""),
                "indicator_deltas": last.get("indicator_deltas", ""),
            })

    if os.path.exists(lq_path):
        with open(lq_path, encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("date")]
        if rows:
            last = rows[-1]
            ctx.update({
                "stealth_signal": last.get("stealth_signal", ""),
                "stealth_alert":  last.get("stealth_alert", ""),
            })

    return ctx if ctx else None


def get_avg_cost(ticker: str) -> Optional[float]:
    if not os.path.exists(PORTFOLIO_PATH):
        return None
    with open(PORTFOLIO_PATH, encoding="utf-8") as f:
        portfolio = json.load(f)
    total_cost   = 0.0
    total_shares = 0.0
    for broker_data in portfolio.get("brokers", {}).values():
        pos = broker_data.get("positions", {}).get(ticker)
        if pos:
            shares   = float(pos.get("shares",   0))
            avg_cost = float(pos.get("avg_cost",  0))
            total_cost   += avg_cost * shares
            total_shares += shares
    if total_shares == 0:
        return None
    return round(total_cost / total_shares, 2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI テーブル整形
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _fmt_kpi_value(value: Any, unit: str = "") -> str:
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)

    if unit == "USD":
        if abs(v) < 2:  # 比率（貢献利益率等）→ パーセント表示
            return f"{v * 100:.1f}%"
        elif abs(v) >= 1_000_000_000:
            return f"${v / 1_000_000_000:.2f}B"
        elif abs(v) >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        else:
            return f"${v:,.0f}"
    elif unit == "%":
        return f"{v:.1f}%"
    else:
        return str(v)


def build_kpi_table(kpi_data: Dict[str, Any], max_quarters: int = 8) -> str:
    kpis = kpi_data.get("kpis", {})
    if not kpis:
        return "（KPIデータなし）"

    all_quarters: set = set()
    for kinfo in kpis.values():
        for dp in kinfo.get("data", []):
            all_quarters.add(dp["quarter"])

    sorted_q = sorted(all_quarters, reverse=True)[:max_quarters]

    header = "| KPI | " + " | ".join(sorted_q) + " |"
    sep    = "| --- | " + " | ".join(["---"] * len(sorted_q)) + " |"

    rows = [header, sep]
    for kname, kinfo in kpis.items():
        unit   = kinfo.get("unit", "")
        dp_map = {dp["quarter"]: dp["value"] for dp in kinfo.get("data", [])}
        vals   = [_fmt_kpi_value(dp_map.get(q), unit) for q in sorted_q]
        rows.append(f"| {kname} | " + " | ".join(vals) + " |")

    return "\n".join(rows)


def build_kpi_snapshot(kpi_data: Dict[str, Any], max_quarters: int = 4) -> Dict[str, Any]:
    kpis = kpi_data.get("kpis", {})
    all_quarters: set = set()
    for kinfo in kpis.values():
        for dp in kinfo.get("data", []):
            all_quarters.add(dp["quarter"])
    recent_q = sorted(all_quarters, reverse=True)[:max_quarters]

    snapshot: Dict[str, Any] = {}
    for kname, kinfo in kpis.items():
        dp_map = {dp["quarter"]: dp["value"] for dp in kinfo.get("data", [])}
        snapshot[kname] = {q: dp_map.get(q) for q in recent_q}
    return snapshot


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# プロンプト構築
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STAGE1_SYSTEM = (
    "あなたは長期投資家Koichiの投資テーゼ検証パートナーです。"
    "感情的な応援ではなく、証拠に基づいた冷静な評価をしてください。"
    "楽観的バイアスには明示的に警告を発してください。"
    "回答はすべて日本語で記述してください。"
)

STAGE2_SYSTEM = (
    "あなたはDCFモデルの入力パラメータを生成する専門家です。"
    "楽観バイアスを避け、ベア/ベース/ブルの3シナリオを必ず提示してください。"
    "経営者の発言は10%割り引いて解釈してください。"
    "rationale・key_assumptions・risk_factorsはすべて日本語で記述してください。"
)

CALL2_SYSTEM = (
    "あなたは長期投資家Koichiの広い視野を補う投資パートナーです。"
    "定量データではなく、定性的な視点・歴史的類比・構造的問いかけを提供してください。"
    "「売れ」「買え」は言わない。最後は必ず問いかけで締める。"
    "根拠がある事象のみ言及し、データ不足時は「確認が必要」と明示する。"
    "必ずWeb検索を使って前回レビュー以降の最新情報を調べてください。"
    "検索した情報には出典（メディア名・日付）を明示してください。"
    "テーゼに書かれていることの言い換えは禁止です。"
    "Koichiさんが気づいていない視点・盲点を提供してください。"
    "回答はすべて日本語で記述してください。"
)


def _build_macro_text(macro_ctx: Optional[Dict[str, Any]]) -> str:
    if not macro_ctx:
        return "（マクロデータ未取得）"
    lines = []
    score = macro_ctx.get("score", "")
    if score:
        lines.append(
            f"景気スコア: {score} ({macro_ctx.get('phase', '')}) "
            f"週次変化: {macro_ctx.get('score_change_1w', 'N/A')} / "
            f"月次変化: {macro_ctx.get('score_change_1m', 'N/A')}"
        )
    if macro_ctx.get("watchpoints"):
        lines.append(f"注視点: {macro_ctx['watchpoints']}")
    if macro_ctx.get("indicator_deltas"):
        lines.append(f"指標デルタ: {macro_ctx['indicator_deltas']}")
    if macro_ctx.get("stealth_signal"):
        lines.append(f"ステルス流動性シグナル: {macro_ctx['stealth_signal']}")
    if macro_ctx.get("stealth_alert"):
        lines.append(f"流動性アラート: {macro_ctx['stealth_alert']}")
    return "\n".join(lines) or "（主要フィールドが空）"


def _build_kpi_monitoring_section(
    thesis: Dict[str, Any],
    kpi_data_layer2: Optional[Dict[str, Any]] = None,
    kpi_data_layer3: Optional[Dict[str, Any]] = None,
    quarter: str = "",
) -> str:
    kpis = thesis.get("kpis") or []
    if not kpis:
        return ""
    table = _build_kpi_status_table(kpis, kpi_data_layer2, kpi_data_layer3, quarter)
    return (
        f"\n## 監視KPI実績（{quarter}）\n{table}\n\n"
        "※ 各KPIの実績値と警戒ラインとの距離感を評価に含めること。\n"
        "※ 実績値が「— 未取得」のKPIも次四半期の確認優先度に含めること。\n"
    )


def _lookup_layer2_value(kpi: Dict[str, Any], kpi_data_layer2: Dict[str, Any], quarter: str) -> Optional[Any]:
    lookup_key = kpi.get("layer2_name") or kpi.get("name", "")
    kpis = kpi_data_layer2.get("kpis", {})
    for name, kinfo in kpis.items():
        if name == lookup_key:
            for dp in kinfo.get("data", []):
                if dp.get("quarter") == quarter:
                    return dp.get("value")
    return None


def _build_kpi_status_table(
    thesis_kpis: List[Dict[str, Any]],
    kpi_data_layer2: Optional[Dict[str, Any]],
    kpi_data_layer3: Optional[Dict[str, Any]],
    quarter: str,
) -> str:
    header = "| KPI名 | 実績値 | 警戒ライン | エグジット閾値 | 状態 |"
    sep    = "| --- | --- | --- | --- | --- |"
    rows   = [header, sep]

    l3_kpis = (kpi_data_layer3 or {}).get("kpis", {})

    for k in thesis_kpis:
        name      = k.get("name", "")
        warn      = k.get("warning_threshold", "—")
        exit_thr  = k.get("exit_threshold", "—")
        auto_f    = k.get("auto_fetchable", False)

        actual_val: Optional[Any] = None
        confidence = "high"

        if auto_f and kpi_data_layer2:
            actual_val = _lookup_layer2_value(k, kpi_data_layer2, quarter)
        elif name in l3_kpis:
            entry      = l3_kpis[name]
            actual_val = entry.get("value")
            confidence = entry.get("confidence", "medium")

        if actual_val is not None:
            if confidence == "high":
                status = "✅ 取得済"
            elif confidence == "medium":
                status = "⚠ 中精度"
            else:
                status = "❌ 低精度"
            display = str(actual_val)
        else:
            status  = "— 未取得"
            display = "—"

        rows.append(f"| {name} | {display} | {warn} | {exit_thr} | {status} |")

    return "\n".join(rows)


def build_stage1_prompt(
    thesis: Dict[str, Any],
    kpi_table: str,
    macro_ctx: Optional[Dict[str, Any]],
    valuation: Optional[Dict[str, Any]],
    ticker: str,
    quarter: str,
    entry_price: Optional[float] = None,
    kpi_data_layer2: Optional[Dict[str, Any]] = None,
    kpi_data_layer3: Optional[Dict[str, Any]] = None,
) -> str:
    val_section = ""
    if valuation:
        val_section = (
            f"\n## 理論株価との乖離\n"
            f"現在価格: ${valuation['current_price']}\n"
            f"理論株価（WACC Rm=10%）: ${valuation['intrinsic_value']}\n"
            f"乖離率（upside）: {valuation['deviation_rate']}%\n"
            f"TANUKI判定: {valuation['tanuki_score']}\n"
        )
        if entry_price is not None:
            val_section += f"加重平均取得単価: ${entry_price}\n"
    elif entry_price is not None:
        val_section = f"\n## 取得コスト\n加重平均取得単価: ${entry_price}\n"

    return f"""## 投資テーゼ（{ticker}）
{thesis.get('thesis', '未設定')}

## エントリーストーリー
{thesis.get('entry_story', '未設定')}

## エグジットの目安
{thesis.get('exit_guide', '未設定')}

## 直近KPI実績（{quarter}）
{kpi_table}

## マクロ環境
{_build_macro_text(macro_ctx)}
{val_section}{_build_kpi_monitoring_section(thesis, kpi_data_layer2, kpi_data_layer3, quarter)}
## 評価してください

1. テーゼ健全度（0-100点）と根拠
   - KPIはテーゼの方向と一致しているか
   - 想定外の変化はあるか
   - 楽観バイアスの兆候はあるか

2. 今四半期の注目点（良い点・懸念点 各2-3項目）

3. テーゼ継続/修正/撤退の推奨
   - CONTINUE: テーゼは健全
   - WATCH: 一部懸念あり・次回要確認
   - REVISE: テーゼの修正が必要
   - EXIT: テーゼが崩れている

4. 次四半期に確認すべきKPI（優先度順）
   （監視KPI設定がある場合、警戒ラインへの接近度も含めて評価すること）

5. 上記エグジット条件との距離感（現在どの程度近いか）

以下のJSON形式のみで回答してください（説明文・前置き不要）：
{{
  "health_score": 75,
  "health_label": "WATCH",
  "summary": "...",
  "positives": ["...", "..."],
  "concerns": ["...", "..."],
  "recommendation": "WATCH",
  "recommendation_reason": "...",
  "next_kpis": ["...", "..."],
  "exit_distance": "遠い",
  "exit_distance_reason": "...",
  "optimism_bias_warning": null
}}"""


def _calc_yoy_text(kpi_data: Optional[Dict[str, Any]]) -> str:
    if not kpi_data:
        return ""
    kpis = kpi_data.get("kpis", {})
    lines: List[str] = []
    for kname, kinfo in kpis.items():
        dp = {d["quarter"]: d["value"] for d in kinfo.get("data", [])}
        # 最新四半期を探して前年同期と比較
        for q in sorted(dp, reverse=True):
            year = int(q[:4])
            qnum = q[4:]
            prev_q = f"{year - 1}{qnum}"
            if prev_q in dp:
                curr, prev = dp[q], dp[prev_q]
                unit = kinfo.get("unit", "")
                if unit == "USD" and abs(curr) >= 2:
                    yoy = (curr - prev) / abs(prev) * 100 if prev else 0
                    lines.append(f"  {kname}: {q}={_fmt_kpi_value(curr, unit)} vs {prev_q}={_fmt_kpi_value(prev, unit)} → YoY {yoy:+.1f}%")
                else:
                    diff = (curr - prev) * 100
                    lines.append(f"  {kname}: {q}={curr*100:.1f}% vs {prev_q}={prev*100:.1f}% → 前年比 {diff:+.1f}pt")
                break
    return "\n".join(lines)


def build_stage2_prompt(
    ticker: str,
    quarter: str,
    kpi_table: str,
    stage1: Dict[str, Any],
    kpi_data: Optional[Dict[str, Any]] = None,
) -> str:
    yoy_text = _calc_yoy_text(kpi_data)
    yoy_section = f"\n## KPI 前年同期比（参考）\n{yoy_text}\n" if yoy_text else ""
    concerns_str = json.dumps(stage1.get("concerns", []), ensure_ascii=False)
    return f"""## 銘柄: {ticker}
## 対象四半期: {quarter}

## 直近KPI
{kpi_table}
{yoy_section}
## Stage 1 評価結果
健全度: {stage1.get('health_score', 'N/A')}点 ({stage1.get('health_label', 'N/A')})
懸念点: {concerns_str}

## DCFパラメータを生成してください

以下のJSONフォーマットのみで出力してください（説明文不要）：
{{
  "ticker": "{ticker}",
  "quarter": "{quarter}",
  "scenarios": {{
    "bear": {{
      "revenue_growth_y1": 0.15,
      "revenue_growth_y2": 0.12,
      "revenue_growth_y3": 0.10,
      "terminal_growth": 0.03,
      "operating_margin_terminal": 0.20,
      "rationale": "..."
    }},
    "base": {{
      "revenue_growth_y1": 0.25,
      "revenue_growth_y2": 0.20,
      "revenue_growth_y3": 0.18,
      "terminal_growth": 0.03,
      "operating_margin_terminal": 0.25,
      "rationale": "..."
    }},
    "bull": {{
      "revenue_growth_y1": 0.35,
      "revenue_growth_y2": 0.30,
      "revenue_growth_y3": 0.25,
      "terminal_growth": 0.035,
      "operating_margin_terminal": 0.30,
      "rationale": "..."
    }}
  }},
  "key_assumptions": ["...", "..."],
  "risk_factors": ["...", "..."]
}}"""


def _load_past_call2(ticker: str, current_quarter: str, max_items: int = 2) -> List[Dict[str, Any]]:
    """同一tickerの直近2回分のcall2結果を返す（current_quarterを除く）"""
    if not os.path.exists(REVIEWS_DIR):
        return []
    candidates: List[tuple] = []
    for fname in os.listdir(REVIEWS_DIR):
        if fname.startswith(f"{ticker}_") and fname.endswith("_review.json"):
            q = fname[len(ticker) + 1 : -len("_review.json")]
            if q != current_quarter:
                candidates.append((q, fname))
    candidates.sort(key=lambda x: x[0], reverse=True)

    results: List[Dict[str, Any]] = []
    for q, fname in candidates[:max_items]:
        fpath = os.path.join(REVIEWS_DIR, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                rv = json.load(f)
            c2 = rv.get("call2")
            if c2:
                results.append({"quarter": q, "call2": c2})
        except Exception:
            pass
    return results


def build_call2_prompt(
    ticker: str,
    quarter: str,
    thesis: Dict[str, Any],
    stage1: Dict[str, Any],
    macro_ctx: Optional[Dict[str, Any]],
    kpi_status_table: str = "",
    past_call2: Optional[List[Dict[str, Any]]] = None,
) -> str:
    concerns_str = "\n".join(f"・{c}" for c in (stage1.get("concerns") or []))
    bias_warning = stage1.get("optimism_bias_warning") or "なし"
    macro_score  = (macro_ctx or {}).get("score", "不明")
    macro_phase  = (macro_ctx or {}).get("phase", "不明")
    entry_story  = (thesis.get("entry_story") or "未設定")[:500]
    last_quarter = (past_call2[0]["quarter"] if past_call2 else "前回") if past_call2 else "前回"

    # 過去Call2の引き継ぎセクション
    past_section = ""
    if past_call2:
        parts: List[str] = []
        for item in past_call2:
            q = item["quarter"]
            c2 = item["call2"]
            q_parts: List[str] = []
            if c2.get("thesis_questions"):
                q_parts.append(f"前回の問いかけ ({q}):\n" + "\n".join(f"・{x}" for x in c2["thesis_questions"]))
            if c2.get("next_review_focus"):
                q_parts.append(f"前回の次回確認論点 ({q}):\n" + "\n".join(f"・{x}" for x in c2["next_review_focus"]))
            if q_parts:
                parts.append("\n".join(q_parts))
        if parts:
            past_section = "\n## 過去レビューの引き継ぎ事項\n" + "\n\n".join(parts) + "\n"

    # KPIステータステーブルセクション
    kpi_section = ""
    if kpi_status_table:
        kpi_section = (
            f"\n## 今四半期のKPIステータス（{quarter}）\n"
            f"{kpi_status_table}\n"
            "各KPIの現状値と警戒ライン対比を参照して定性分析に活かしてください。\n"
        )

    return f"""## 銘柄: {ticker}
## 対象四半期: {quarter}

## 投資テーゼ
{thesis.get('thesis', '未設定')}

## エントリーストーリー
{entry_story}

## Call 1 評価結果サマリー
健全度: {stage1.get('health_score', 'N/A')}点 ({stage1.get('health_label', 'N/A')})
主な懸念:
{concerns_str if concerns_str else '（なし）'}
楽観バイアス警告: {bias_warning}

## マクロ環境
{_build_macro_text(macro_ctx)}
{past_section}{kpi_section}
## 以下の7項目を分析してください:

1. 5観点での気になる点（Web検索必須）
   Web検索で{ticker}の{last_quarter}以降のニュース・アナリストレポート・競合動向を調べて分析してください。
   テーゼに書かれていることの繰り返しは禁止。
   Koichiさんが見落としている可能性がある点を重点的に指摘してください。
   検索した情報には出典（メディア名・日付）を明示してください。
   ビジネスモデル・成長性・競争優位・経営・市場環境の5軸で回答してください。

2. エントリーストーリーの進捗
   「{entry_story[:100]}」は現在どの程度実現しているか。
   Web検索で最新情報を確認して回答してください。

3. 世の中の注目ポイント
   Web検索でこの銘柄に対して市場・メディア・アナリストが今最も注目している点を調べてください。
   出典（メディア名・日付）を明示してください。

4. 歴史的類比
   {ticker}のビジネスモデル・成長軌跡・リスク構造が最も似ている歴史的企業を1社選んでください。
   その企業が最終的にどうなったか・何が転換点だったかを{ticker}のテーゼに当てはめて具体的に論じてください。
   一般的な類比（SaaSはSalesforce等）は禁止。テーゼ固有の課題に対応した類比を選んでください。

5. マクロ環境を踏まえた留意点
   現在のマクロ環境（スコア{macro_score}・{macro_phase}）がこの銘柄のテーゼに与える影響。

6. テーゼへの問いかけ
   以下の注意を守ってください：
   ・テーゼに書かれていることの言い換えになっている問いは禁止
   ・Koichiさんが見落としている盲点・反論・構造的リスクを3つ問いかけてください
   ・テーゼの前提そのものを揺るがす問いを作ってください
   ・過去の問いかけと重複する問いも禁止

7. 次回確認すべき論点
   次の四半期決算（{ticker} 次回）で実際に確認できる具体的な論点を
   優先度順に3つ挙げてください。
   過去の次回確認論点と重複するものは除いてください。

以下のJSON形式のみで回答してください（説明文・前置き不要）：
{{
  "five_perspectives": {{
    "business_model": "...",
    "growth": "...",
    "competitive_advantage": "...",
    "management": "...",
    "market": "..."
  }},
  "entry_story_progress": "...",
  "market_attention": "...",
  "historical_analogy": {{
    "company": "...",
    "similarity": "...",
    "outcome": "...",
    "implication": "..."
  }},
  "macro_implications": "...",
  "thesis_questions": ["問い1", "問い2", "問い3"],
  "next_review_focus": ["論点1", "論点2", "論点3"]
}}"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# キュー I/O
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_queue() -> Dict[str, Any]:
    if os.path.exists(REVIEW_QUEUE_PATH):
        with open(REVIEW_QUEUE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"queue": []}


def save_queue(queue: Dict[str, Any]) -> None:
    with open(REVIEW_QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1銘柄レビュー生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _mark_older_reviews_not_latest(ticker: str) -> None:
    if not os.path.exists(REVIEWS_DIR):
        return
    for fname in os.listdir(REVIEWS_DIR):
        if fname.startswith(f"{ticker}_") and fname.endswith("_review.json"):
            fpath = os.path.join(REVIEWS_DIR, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    existing = json.load(f)
                if existing.get("is_latest"):
                    existing["is_latest"] = False
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(existing, f, ensure_ascii=False, indent=2)
            except Exception:
                pass


def generate_review(entry: Dict[str, Any], dry_run: bool = False) -> Optional[str]:
    ticker  = entry["ticker"]
    quarter = entry["quarter"]
    accn    = entry.get("accn", "")
    now_jst = datetime.now(JST)

    print(f"\n{'─' * 60}")
    print(f"  {ticker} {quarter} レビュー生成開始")
    print(f"{'─' * 60}")

    thesis     = load_thesis(ticker)
    kpi_data   = load_layer2_kpi(ticker)
    kpi_layer3 = load_layer3_kpi(ticker)
    macro_ctx  = load_macro_context()
    valuation  = load_tanuki_valuation(ticker)

    if not thesis:
        print(f"  [ERROR] {ticker} の thesis.json がないためスキップ")
        return None

    entry_price: Optional[float] = thesis.get("entry_price")
    if entry_price is None:
        entry_price = get_avg_cost(ticker)
        if entry_price is not None:
            print(f"  [INFO] entry_price: portfolio.jsonから取得 ${entry_price}")

    kpi_table    = build_kpi_table(kpi_data)    if kpi_data else "（KPIデータなし）"
    kpi_snapshot = build_kpi_snapshot(kpi_data) if kpi_data else {}
    macro_snapshot = {
        "score":          macro_ctx.get("score")          if macro_ctx else None,
        "phase":          macro_ctx.get("phase")          if macro_ctx else None,
        "stealth_signal": macro_ctx.get("stealth_signal") if macro_ctx else None,
    }

    stage1_prompt = build_stage1_prompt(
        thesis=thesis,
        kpi_table=kpi_table,
        macro_ctx=macro_ctx,
        valuation=valuation,
        ticker=ticker,
        quarter=quarter,
        entry_price=entry_price,
        kpi_data_layer2=kpi_data,
        kpi_data_layer3=kpi_layer3,
    )

    if dry_run:
        print("\n=== [DRY-RUN] Stage 1 プロンプト（先頭1000文字） ===")
        print(stage1_prompt[:1000])
        print("...\n=== DRY-RUN 完了（Grok呼び出しなし） ===")
        return None

    # 成功フラグ
    call1_success:     bool = False
    stage2_json_valid: bool = False
    call2_success:     bool = False
    stage2:            Dict[str, Any] = {}
    call2:             Optional[Dict[str, Any]] = None

    # Stage 1 — 失敗時は例外を再 raise
    print(f"\n  ── Stage 1: テーゼ健全度評価 ({ticker} {quarter}) ──")
    try:
        stage1_raw = call_grok(
            user_prompt=stage1_prompt,
            system_prompt=STAGE1_SYSTEM,
            max_tokens=2000,
            temperature=0.3,
        )
        stage1 = extract_json_from_response(stage1_raw)
        call1_success = True
        print(f"  → health_score={stage1.get('health_score')}, recommendation={stage1.get('recommendation')}")
    except Exception as e:
        print(f"  [ERROR] Stage 1 失敗: {e}")
        raise

    # Stage 2 — 失敗しても継続
    stage2_prompt = build_stage2_prompt(ticker, quarter, kpi_table, stage1, kpi_data)
    print(f"\n  ── Stage 2: DCFパラメータ生成 ({ticker} {quarter}) ──")
    try:
        stage2_raw = call_grok(
            user_prompt=stage2_prompt,
            system_prompt=STAGE2_SYSTEM,
            max_tokens=2000,
            temperature=0.2,
        )
        stage2 = extract_json_from_response(stage2_raw)
        stage2_json_valid = True
        print(f"  → シナリオ: {list(stage2.get('scenarios', {}).keys())}")
    except Exception as e:
        print(f"  [WARN] Stage 2 失敗（スキップ）: {e}")

    # Call 2 — 定性分析、失敗しても継続
    call2_kpi_table = _build_kpi_status_table(
        thesis.get("kpis") or [], kpi_data, kpi_layer3, quarter
    ) if thesis.get("kpis") else ""
    past_call2_items = _load_past_call2(ticker, quarter)
    if past_call2_items:
        print(f"  [INFO] 過去Call2引き継ぎ: {[x['quarter'] for x in past_call2_items]}")
    call2_prompt = build_call2_prompt(
        ticker, quarter, thesis, stage1, macro_ctx,
        kpi_status_table=call2_kpi_table,
        past_call2=past_call2_items,
    )
    print(f"\n  ── Call 2: 定性分析 ({ticker} {quarter}) ──")
    try:
        call2_raw = call_grok(
            user_prompt=call2_prompt,
            system_prompt=CALL2_SYSTEM,
            max_tokens=3000,
            temperature=0.5,
        )
        call2 = extract_json_from_response(call2_raw)
        call2_success = True
        print(f"  → 5観点・歴史的類比・問いかけ 生成完了")
    except Exception as e:
        print(f"  [WARN] Call 2 失敗（スキップ）: {e}")

    # 同一tickerの既存レビューをis_latest=falseに更新してから保存
    _mark_older_reviews_not_latest(ticker)

    os.makedirs(REVIEWS_DIR, exist_ok=True)
    output_path = os.path.join(REVIEWS_DIR, f"{ticker}_{quarter}_review.json")

    review = {
        "ticker":               ticker,
        "quarter":              quarter,
        "generated_at":         now_jst.isoformat(),
        # idempotencyフィールド
        "data_version":         accn,
        "is_latest":            True,
        "layer1_complete":      bool(accn),
        "layer2_complete":      kpi_data.get("layer2_complete", False) if kpi_data else False,
        "layer2_missing_kpis":  kpi_data.get("missing_kpis", []) if kpi_data else [],
        "stage2_json_valid":    stage2_json_valid,
        "grok_call1_success":   call1_success,
        "grok_call2_success":   call2_success,
        "transcript_available": False,
        # コンテンツ
        "stage1":          stage1,
        "stage2":          stage2,
        "call2":           call2,
        "kpi_snapshot":    kpi_snapshot,
        "layer3_snapshot": kpi_layer3.get("kpis", {}) if kpi_layer3 else {},
        "macro_snapshot":  macro_snapshot,
        "thesis_version":  thesis.get("version", 1),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ レビュー保存: {output_path}")
    return output_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エントリーポイント
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    parser = argparse.ArgumentParser(description="TANUKI TAIL — 四半期レビュー生成")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Grok呼び出しをスキップしてプロンプト内容を確認する",
    )
    args = parser.parse_args()

    now_jst = datetime.now(JST)
    print(f"TANUKI TAIL 四半期レビュー生成 — {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 60)

    queue   = load_queue()
    pending = [e for e in queue.get("queue", []) if e.get("status") == "pending"]

    if not pending:
        print("pending エントリなし → 終了")
        sys.exit(0)

    print(f"pending: {len(pending)} 件")
    for e in pending:
        print(f"  {e['ticker']} {e['quarter']} (filed: {e.get('filed', '')})")

    generated: List[str] = []
    failed:    List[str] = []

    for entry in pending:
        try:
            output_path = generate_review(entry, dry_run=args.dry_run)
            if output_path:
                entry["status"]       = "completed"
                entry["completed_at"] = now_jst.isoformat()
                entry["review_path"]  = output_path
                generated.append(f"{entry['ticker']} {entry['quarter']}")
        except Exception as e:
            print(f"  [ERROR] {entry['ticker']} {entry['quarter']} 失敗: {e}")
            entry["status"] = "error"
            entry["error"]  = str(e)
            failed.append(f"{entry['ticker']} {entry['quarter']}")

    if not args.dry_run:
        save_queue(queue)
        print("\n✓ review_queue.json 更新完了")

    print(f"\n{'━' * 60}")
    print(f"完了: 生成 {len(generated)} 件 / 失敗 {len(failed)} 件")
    for g in generated:
        print(f"  OK: {g}")
    for f_item in failed:
        print(f"  NG: {f_item}")


if __name__ == "__main__":
    main()
