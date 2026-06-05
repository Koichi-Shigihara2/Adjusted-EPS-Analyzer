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


def build_stage1_prompt(
    thesis: Dict[str, Any],
    kpi_table: str,
    macro_ctx: Optional[Dict[str, Any]],
    valuation: Optional[Dict[str, Any]],
    ticker: str,
    quarter: str,
    entry_price: Optional[float] = None,
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
{val_section}
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


def build_stage2_prompt(
    ticker: str,
    quarter: str,
    kpi_table: str,
    stage1: Dict[str, Any],
) -> str:
    concerns_str = json.dumps(stage1.get("concerns", []), ensure_ascii=False)
    return f"""## 銘柄: {ticker}
## 対象四半期: {quarter}

## 直近KPI
{kpi_table}

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

def generate_review(entry: Dict[str, Any], dry_run: bool = False) -> Optional[str]:
    ticker  = entry["ticker"]
    quarter = entry["quarter"]
    now_jst = datetime.now(JST)

    print(f"\n{'─' * 60}")
    print(f"  {ticker} {quarter} レビュー生成開始")
    print(f"{'─' * 60}")

    thesis    = load_thesis(ticker)
    kpi_data  = load_layer2_kpi(ticker)
    macro_ctx = load_macro_context()
    valuation = load_tanuki_valuation(ticker)

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
    )

    if dry_run:
        print("\n=== [DRY-RUN] Stage 1 プロンプト（先頭1000文字） ===")
        print(stage1_prompt[:1000])
        print("...\n=== DRY-RUN 完了（Grok呼び出しなし） ===")
        return None

    # Stage 1
    print(f"\n  ── Stage 1: テーゼ健全度評価 ({ticker} {quarter}) ──")
    stage1_raw = call_grok(
        user_prompt=stage1_prompt,
        system_prompt=STAGE1_SYSTEM,
        max_tokens=2000,
        temperature=0.3,
    )
    stage1 = extract_json_from_response(stage1_raw)
    print(f"  → health_score={stage1.get('health_score')}, recommendation={stage1.get('recommendation')}")

    # Stage 2
    stage2_prompt = build_stage2_prompt(ticker, quarter, kpi_table, stage1)
    print(f"\n  ── Stage 2: DCFパラメータ生成 ({ticker} {quarter}) ──")
    stage2_raw = call_grok(
        user_prompt=stage2_prompt,
        system_prompt=STAGE2_SYSTEM,
        max_tokens=2000,
        temperature=0.2,
    )
    stage2 = extract_json_from_response(stage2_raw)
    print(f"  → シナリオ: {list(stage2.get('scenarios', {}).keys())}")

    # 出力保存
    os.makedirs(REVIEWS_DIR, exist_ok=True)
    output_path = os.path.join(REVIEWS_DIR, f"{ticker}_{quarter}_review.json")

    review = {
        "ticker":         ticker,
        "quarter":        quarter,
        "generated_at":   now_jst.isoformat(),
        "stage1":         stage1,
        "stage2":         stage2,
        "kpi_snapshot":   kpi_snapshot,
        "macro_snapshot": macro_snapshot,
        "thesis_version": thesis.get("version", 1),
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
