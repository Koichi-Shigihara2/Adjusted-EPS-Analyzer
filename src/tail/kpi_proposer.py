#!/usr/bin/env python3
"""
TANUKI TAIL — kpi_proposer.py

投資テーゼとエグジット条件をGrokに渡し、
四半期監視KPIの候補を提案して保存する（Step 0）。

使用方法:
    python src/tail/kpi_proposer.py --ticker PLTR
    python src/tail/kpi_proposer.py --ticker PLTR SOFI TSLA
    python src/tail/kpi_proposer.py --ticker PLTR --dry-run

出力: docs/portfolio/tail/data/kpi_proposals/{ticker}_proposal.json
環境変数:
    XAI_API_KEY  xAI Grok API キー（必須）
"""

import os
import sys
import json
import re
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
KPI_PROPOSALS_DIR = os.path.join(DATA_DIR, "kpi_proposals")

JST = ZoneInfo("Asia/Tokyo")

# ── Grok API 設定 ──────────────────────────────────────────────
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_URL    = "https://api.x.ai/v1/chat/completions"
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]

KPI_SYSTEM = (
    "あなたは投資テーゼの監視指標設計の専門家です。"
    "テーゼとエグジット条件から、四半期ごとに確認すべき"
    "具体的なKPIを提案してください。"
    "回答はすべて日本語で記述してください。"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Grok API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def call_grok(user_prompt: str, system_prompt: str = "", max_tokens: int = 3000, temperature: float = 0.4) -> str:
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY が設定されていません")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    last_error: Optional[Exception] = None
    for model in GROK_MODELS:
        try:
            print(f"  [Grok] モデル試行: {model}")
            resp = requests.post(
                GROK_URL, headers=headers,
                json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
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
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# プロンプト構築
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_kpi_prompt(thesis: Dict[str, Any]) -> str:
    ticker = thesis.get("ticker", "")
    return f"""## 銘柄: {ticker}
## 投資テーゼ
{thesis.get('thesis', '未設定')}

## エグジット条件
{thesis.get('exit_guide', '未設定')}

## 以下のJSON形式でKPIを5〜8個提案してください:
{{
  "proposed_kpis": [
    {{
      "name": "NDR（ネット・ダラー・リテンション）",
      "description": "既存顧客からの売上維持・拡大率",
      "source": "決算資料（IR開示）",
      "warning_threshold": "110%以下",
      "exit_threshold": "110%未満が2四半期連続",
      "related_exit_condition": "エグジット条件①",
      "auto_fetchable": false
    }}
  ]
}}

auto_fetchable: EDGARのXBRLから自動取得できる場合true（売上・利益などの財務指標）。
非財務指標（NDR・解約率・顧客数など）はfalse。
JSONのみ返してください（説明文不要）。"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 提案生成・保存
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def propose_kpis(ticker: str, dry_run: bool = False) -> Optional[str]:
    ticker = ticker.upper()
    print(f"\n{'─' * 60}")
    print(f"  {ticker} KPI提案生成")
    print(f"{'─' * 60}")

    thesis = load_thesis(ticker)
    if not thesis:
        return None
    if thesis.get("type") != "core":
        print(f"  [SKIP] {ticker} は core 銘柄ではありません（type={thesis.get('type')}）")
        return None

    prompt = build_kpi_prompt(thesis)

    if dry_run:
        print("\n=== [DRY-RUN] KPIプロンプト ===")
        print(prompt[:600])
        print("...\n=== DRY-RUN 完了 ===")
        return None

    raw = call_grok(user_prompt=prompt, system_prompt=KPI_SYSTEM, max_tokens=3000, temperature=0.4)
    result = extract_json_from_response(raw)

    os.makedirs(KPI_PROPOSALS_DIR, exist_ok=True)
    now_jst = datetime.now(JST)
    output: Dict[str, Any] = {
        "ticker":         ticker,
        "generated_at":   now_jst.isoformat(),
        "thesis_version": thesis.get("version", 1),
        "proposed_kpis":  result.get("proposed_kpis", []),
    }
    out_path = os.path.join(KPI_PROPOSALS_DIR, f"{ticker}_proposal.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    kpis = output["proposed_kpis"]
    print(f"  ✓ {len(kpis)} 件のKPI提案を保存: {out_path}")
    for k in kpis:
        auto = "✓自動" if k.get("auto_fetchable") else "手動"
        print(f"    [{auto}] {k.get('name', '?')} — 警戒: {k.get('warning_threshold', '?')}")
    return out_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エントリーポイント
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    parser = argparse.ArgumentParser(description="TANUKI TAIL — KPI提案生成（Step 0）")
    parser.add_argument("--ticker", nargs="+", required=True, help="対象ティッカー（複数指定可）")
    parser.add_argument("--dry-run", action="store_true", help="Grok呼び出しをスキップしてプロンプト確認")
    args = parser.parse_args()

    now_jst = datetime.now(JST)
    print(f"TANUKI TAIL KPI提案生成 — {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 60)

    results: Dict[str, bool] = {}
    for t in args.ticker:
        try:
            path = propose_kpis(t, dry_run=args.dry_run)
            results[t.upper()] = path is not None or args.dry_run
        except Exception as e:
            print(f"  [ERROR] {t}: {e}")
            results[t.upper()] = False

    print(f"\n{'━' * 60}")
    for t, ok in results.items():
        print(f"  {'OK' if ok else 'NG'}: {t}")


if __name__ == "__main__":
    main()
