#!/usr/bin/env python3
"""
TANUKI TAIL — kpi_proposer.py

投資テーゼとエグジット条件をGrokに渡し、
四半期監視KPIの候補を提案して保存する（Step 0）。

使用方法:
    python src/tail/kpi_proposer.py --ticker PLTR
    python src/tail/kpi_proposer.py --ticker PLTR SOFI TSLA
    python src/tail/kpi_proposer.py --ticker PLTR --dry-run

出力:
    docs/portfolio/tail/data/kpi_proposals/{ticker}_proposal.json
    docs/portfolio/tail/data/tail_kpi_map.json（auto_fetchable=true 分を自動追記）
環境変数:
    XAI_API_KEY  xAI Grok API キー（必須）
"""

import os
import csv
import json
import re
import time
import argparse
import requests
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List

# ── パス設定 ──────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))

DATA_DIR          = os.path.join(repo_root, "docs", "portfolio", "tail", "data")
POSITIONS_DIR     = os.path.join(DATA_DIR, "positions")
KPI_PROPOSALS_DIR = os.path.join(DATA_DIR, "kpi_proposals")
KPI_MAP_PATH      = os.path.join(DATA_DIR, "tail_kpi_map.json")
CIK_LOOKUP_PATH   = os.path.join(repo_root, "config", "cik_lookup.csv")

JST = ZoneInfo("Asia/Tokyo")

# ── Grok API 設定 ──────────────────────────────────────────────
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_URL    = "https://api.x.ai/v1/chat/completions"
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]

KPI_SYSTEM = (
    "あなたは投資テーゼの監視指標設計の専門家です。"
    "テーゼとエグジット条件から、四半期ごとに確認すべき具体的なKPIを提案してください。"
    "auto_fetchable=trueのKPIには必ずxbrl_tag・xbrl_dimension・xbrl_memberを記入してください。"
    "xbrl_tagはus-gaap名前空間またはカスタム名前空間で記述してください。"
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


def load_kpi_map() -> Dict[str, Any]:
    if not os.path.exists(KPI_MAP_PATH):
        return {}
    with open(KPI_MAP_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_cik(ticker: str) -> Optional[str]:
    if not os.path.exists(CIK_LOOKUP_PATH):
        return None
    with open(CIK_LOOKUP_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("ticker", "").upper() == ticker.upper():
                return row.get("cik", "").strip()
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# プロンプト構築
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_kpi_prompt(thesis: Dict[str, Any], cik: Optional[str] = None, existing_kpi_map: Optional[List[Dict[str, Any]]] = None) -> str:
    ticker  = thesis.get("ticker", "")
    cik_str = cik or "不明"

    existing_section = ""
    if existing_kpi_map:
        names = [e.get("kpi_name", "") for e in existing_kpi_map if e.get("kpi_name")]
        if names:
            existing_section = "\n## 既存の自動取得KPI（tail_kpi_map登録済み）\n" + "\n".join(f"- {n}" for n in names) + "\n"

    return f"""## 銘柄: {ticker}
## CIK: {cik_str}
## 投資テーゼ
{thesis.get('thesis', '未設定')}

## エグジット条件
{thesis.get('exit_guide', '未設定')}
{existing_section}
## 以下のJSON形式でKPIを5〜8個提案してください:
{{
  "proposed_kpis": [
    {{
      "name": "NDR（ネット・ダラー・リテンション）",
      "description": "既存顧客からの売上維持・拡大率",
      "source": "決算資料（IR開示）",
      "warning_threshold": "120%以下",
      "exit_threshold": "110%未満が2四半期連続",
      "related_exit_condition": "エグジット条件①",
      "auto_fetchable": false,
      "extraction_hint": "net dollar retention",
      "xbrl_tag": null,
      "xbrl_dimension": null,
      "xbrl_member": null,
      "layer2_name": null
    }},
    {{
      "name": "米民間売上成長率",
      "description": "US Commercial売上の前年同期比成長率",
      "source": "EDGAR XBRL",
      "warning_threshold": "40%以下",
      "exit_threshold": "30%未満が2四半期連続",
      "related_exit_condition": "エグジット条件②",
      "auto_fetchable": true,
      "extraction_hint": null,
      "xbrl_tag": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
      "xbrl_dimension": "us-gaap:StatementBusinessSegmentsAxis",
      "xbrl_member": "pltr:CommercialOperatingSegmentMember",
      "layer2_name": "Commercial売上"
    }}
  ]
}}

ルール:
- auto_fetchable=true: EDGARのXBRLから取得可能な財務指標（売上・利益・残高等）
  → xbrl_tag・xbrl_dimension・xbrl_memberを必ず具体的に記入
  → xbrl_memberは "{ticker.lower()}:XxxMember" 形式で記入
  → 上記「既存の自動取得KPI」のいずれかと同じXBRLデータを参照する場合、layer2_nameにその既存KPI名を記入（例: "layer2_name": "Commercial売上"）
- auto_fetchable=false: NDR・解約率・顧客数・規制状況等の非財務指標
  → extraction_hintに決算資料でよく使われる英語表現を記入
  → xbrl_tag/dimension/memberはnull、layer2_nameはnull
- JSONのみ返してください（説明文不要）"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# tail_kpi_map.json への自動追記
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def post_process_proposals(ticker: str, kpis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Grok提案にlayer2_nameが未設定の場合、xbrl_tag+memberが既存kpi_mapと一致すればセットする。"""
    kpi_map_entries = load_kpi_map().get(ticker, [])
    # (revenue_tag, member_tag) → kpi_name
    tag_to_name: Dict[tuple, str] = {}
    for e in kpi_map_entries:
        r_tag = e.get("revenue_tag", "")
        member = e.get("tag_history", [{}])[0].get("tag", "")
        if r_tag:
            tag_to_name[(r_tag, member)] = e.get("kpi_name", "")

    for kpi in kpis:
        if not kpi.get("auto_fetchable"):
            continue
        if kpi.get("layer2_name"):
            continue
        key = (kpi.get("xbrl_tag", ""), kpi.get("xbrl_member", "") or "")
        if key in tag_to_name:
            existing_name = tag_to_name[key]
            if existing_name != kpi.get("name"):
                kpi["layer2_name"] = existing_name
                print(f"    [post_process] layer2_name セット: {kpi['name']} → {existing_name}")
    return kpis


def update_tail_kpi_map(ticker: str, proposed_kpis: List[Dict[str, Any]]) -> int:
    if os.path.exists(KPI_MAP_PATH):
        with open(KPI_MAP_PATH, encoding="utf-8") as f:
            kpi_map: Dict[str, Any] = json.load(f)
    else:
        kpi_map = {}

    existing = kpi_map.get(ticker, [])
    existing_names = {e.get("kpi_name", "") for e in existing}
    # (revenue_tag, member_tag) で重複チェック（名前が違っても同一XBRLデータは追加しない）
    existing_tag_members = {
        (e.get("revenue_tag", ""), e.get("tag_history", [{}])[0].get("tag", ""))
        for e in existing
    }

    added = 0
    today = str(date.today())
    for kpi in proposed_kpis:
        if not kpi.get("auto_fetchable"):
            continue
        xbrl_tag  = kpi.get("xbrl_tag")
        xbrl_dim  = kpi.get("xbrl_dimension")
        xbrl_mem  = kpi.get("xbrl_member") or ""
        kpi_name  = kpi.get("name", "")

        if not xbrl_tag:
            continue
        if kpi_name in existing_names:
            continue
        tag_key = (xbrl_tag, xbrl_mem)
        if tag_key in existing_tag_members:
            print(f"    [kpi_map] スキップ（tag+member重複）: {kpi_name}")
            continue

        entry: Dict[str, Any] = {
            "kpi_name":     kpi_name,
            "change_risk":  "medium",
            "tag_history":  [{"tag": xbrl_mem, "valid_from": today, "valid_to": None}],
            "fallback_tags":    [],
            "fallback_action":  "alert",
            "revenue_tag":  xbrl_tag,
            "dimension":    xbrl_dim or "",
        }
        existing.append(entry)
        existing_names.add(kpi_name)
        existing_tag_members.add(tag_key)
        added += 1
        print(f"    [kpi_map] 追加: {kpi_name} → {xbrl_tag}")

    if added > 0:
        kpi_map[ticker] = existing
        with open(KPI_MAP_PATH, "w", encoding="utf-8") as f:
            json.dump(kpi_map, f, ensure_ascii=False, indent=2)
        print(f"  ✓ tail_kpi_map.json を更新 (+{added}件)")

    return added


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

    cik    = load_cik(ticker)
    existing_kpi_map = load_kpi_map().get(ticker, [])
    prompt = build_kpi_prompt(thesis, cik, existing_kpi_map)

    if dry_run:
        print("\n=== [DRY-RUN] KPIプロンプト ===")
        print(prompt[:800])
        print("...\n=== DRY-RUN 完了 ===")
        return None

    raw    = call_grok(user_prompt=prompt, system_prompt=KPI_SYSTEM, max_tokens=3000, temperature=0.4)
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
    # layer2_nameを自動補完（xbrl_tag+memberが既存kpi_mapと一致する場合）
    kpis = post_process_proposals(ticker, kpis)
    output["proposed_kpis"] = kpis
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  ✓ {len(kpis)} 件のKPI提案を保存: {out_path}")
    for k in kpis:
        auto = "✓自動" if k.get("auto_fetchable") else "手動"
        hint = k.get("xbrl_tag") or k.get("extraction_hint") or ""
        l2n = f" [layer2_name={k['layer2_name']}]" if k.get("layer2_name") else ""
        print(f"    [{auto}] {k.get('name', '?')} — 警戒: {k.get('warning_threshold', '?')} ({hint}){l2n}")

    # auto_fetchable=true のKPIをtail_kpi_map.jsonに自動追記（tag+member重複はスキップ）
    update_tail_kpi_map(ticker, kpis)

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
