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
    config/tail_kpi_map.json（auto_fetchable=true 分を自動追記、2026-08-15
    docs/portfolio/tail/data/から移動）
環境変数:
    XAI_API_KEY  xAI Grok API キー（必須）
"""

import os
import sys
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

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from src.tail.thesis_utils import thesis_narrative_fields  # noqa: E402
from src.tail.xbrl_segment_fetcher import (  # noqa: E402
    get_10q_filings, download_xbrl, extract_segment_members,
)

# 実XBRLタグ抽出で「セグメント区分」とみなすディメンションのローカル名
# キーワード（大文字小文字区別なし）。extract_segment_members()が返す
# 全ディメンション（持分・公正価値階層等の無関係な軸を含む75件規模）
# から、セグメント・製品・地域区分に絞り込むための簡易フィルタ
# （2026-08-19⑥、[[TAIL-XBRL-MEMBER-VALIDATION-GAP-1]]対応）。
_SEGMENT_DIMENSION_KEYWORDS = ("segment", "productorservice", "geographical", "geographic")

DATA_DIR          = os.path.join(repo_root, "docs", "portfolio", "tail", "data")
POSITIONS_DIR     = os.path.join(DATA_DIR, "positions")
KPI_PROPOSALS_DIR = os.path.join(DATA_DIR, "kpi_proposals")
# tail_kpi_map.jsonはPythonバックエンド専用の手動設定ファイルのため
# config/配下に配置（TAILKPI-CONFIG-LOCATION-1、2026-08-15移動）
KPI_MAP_PATH      = os.path.join(repo_root, "config", "tail_kpi_map.json")
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


def fetch_real_segment_tags(ticker: str, cik: Optional[str]) -> List[Dict[str, str]]:
    """直近10-QのXBRLから、実際に使用されているセグメント関連タグ
    （dimension, member の組）を取得する。

    `xbrl_segment_fetcher.py::extract_segment_members()`（parse_
    contexts()の抽出ロジックを再利用した既存関数）をそのまま呼ぶ。
    取得したdimension/member全件（equity・fair value階層等の無関係な
    軸を含む）のうち、`_SEGMENT_DIMENSION_KEYWORDS`に一致するものだけ
    を返す（2026-08-19⑥、[[TAIL-XBRL-MEMBER-VALIDATION-GAP-1]]対応:
    Grokにタグ名を記憶から生成させず、実際に提出書類に存在するタグから
    選ばせるための土台）。

    取得できない場合（CIK不明・10-Q取得失敗等）は空リストを返す。
    呼び出し側はこれを「セグメント指標を提案しない」の判断材料とする。
    """
    if not cik:
        return []
    try:
        filings = get_10q_filings(cik, n=1)
        if not filings:
            return []
        f = filings[0]
        xml_text = download_xbrl(cik, f["accn"], f["xml"])
        if not xml_text:
            return []
        all_members = extract_segment_members(xml_text)
    except Exception as e:
        print(f"  [WARN] 実XBRLタグ取得失敗: {e}")
        return []

    return [
        m for m in all_members
        if any(kw in m["dimension"].lower() for kw in _SEGMENT_DIMENSION_KEYWORDS)
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# プロンプト構築
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_kpi_prompt(
    thesis: Dict[str, Any],
    cik: Optional[str] = None,
    existing_kpi_map: Optional[List[Dict[str, Any]]] = None,
    real_segment_tags: Optional[List[Dict[str, str]]] = None,
) -> str:
    ticker  = thesis.get("ticker", "")
    cik_str = cik or "不明"

    # thesisのスキーマ差（core/satellite）を吸収する。修正前は
    # thesis.get('thesis', ...)/thesis.get('exit_guide', ...)で
    # coreスキーマのフィールド名を直接読んでおり、satelliteの
    # thesisファイルに対しては常に「未設定」が返っていた
    # （quarterly_review_generator.pyで発見・修正した実バグと同型、
    # [[TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1]]対応、2026-08-19④）。
    thesis_text, _entry_story, exit_guide_text = thesis_narrative_fields(thesis)

    existing_section = ""
    if existing_kpi_map:
        names = [e.get("kpi_name", "") for e in existing_kpi_map if e.get("kpi_name")]
        if names:
            existing_section = "\n## 既存の自動取得KPI（tail_kpi_map登録済み）\n" + "\n".join(f"- {n}" for n in names) + "\n"

    # 実XBRLタグ一覧セクション（2026-08-19⑥、[[TAIL-XBRL-MEMBER-
    # VALIDATION-GAP-1]]対応）。修正前はxbrl_memberを"{ticker}:XxxMember"
    # 形式で記憶から生成させており、実測で一致率32%（今回一括生成分は
    # 14%）という低さだった。実際の直近10-QのXBRLから抽出した
    # dimension/memberの組を提示し、その中からのみ選ばせることで、
    # 「Grokが正しいタグ名を知っている」という検証していない前提への
    # 依存をなくす。
    if real_segment_tags:
        tag_lines = "\n".join(
            f"- dimension={t['dimension']}, member={t['member']}"
            for t in real_segment_tags
        )
        segment_tags_section = f"""
## この企業が実際に使用しているセグメント関連タグ（直近10-Qより抽出）
{tag_lines}

**セグメント指標（特定事業区分・製品・地域別の指標）を提案する場合は、
必ず上記一覧の中からdimension・memberの組を選んでください。
一覧に無い名称を記憶や推測で生成しないこと。** 該当するものが一覧に
無い場合は、その指標をセグメント指標として提案せず、
`xbrl_dimension: null, xbrl_member: null`としてください（無理に
セグメント区分をでっち上げるより、全社ベースの指標として提案する方が
望ましい）。
"""
    else:
        segment_tags_section = """
## セグメント関連タグの実データ
取得できませんでした。**この場合、セグメント指標（xbrl_dimension・
xbrl_memberを伴う指標）は提案しないでください。** 全社ベースの指標
（xbrl_dimension: null, xbrl_member: null）のみを提案してください。
"""

    return f"""## 銘柄: {ticker}
## CIK: {cik_str}
## 投資テーゼ
{thesis_text}

## エグジット条件
{exit_guide_text}
{existing_section}{segment_tags_section}
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
  → xbrl_tagは標準的なus-gaap概念名で記入（会社全体の指標は
    xbrl_dimension: null, xbrl_member: nullでよい）
  → セグメント指標の場合のみ、xbrl_dimension・xbrl_memberを上記
    「実際に使用しているセグメント関連タグ」一覧から選んで記入する
    （一覧に無い名称は使わないこと）
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


def update_tail_kpi_map(
    ticker: str,
    proposed_kpis: List[Dict[str, Any]],
    real_segment_tags: Optional[List[Dict[str, str]]] = None,
) -> int:
    """提案されたKPIをtail_kpi_map.jsonへ登録する。

    `real_segment_tags`が渡された場合、セグメント指標（xbrl_dimension・
    xbrl_memberが設定されているKPI）については、その(dimension, member)
    が実際に企業のXBRLに存在するタグ一覧に含まれるかを照合する。
    含まれない場合は**登録せず、却下したことを明示的に表示する**
    （黙って捨てない、2026-08-19⑥、[[TAIL-XBRL-MEMBER-VALIDATION-
    GAP-1]]対応）。`real_segment_tags`が`None`の場合は照合をスキップ
    する（呼び出し元が実データを取得できなかった場合の後方互換）。
    """
    if os.path.exists(KPI_MAP_PATH):
        with open(KPI_MAP_PATH, encoding="utf-8") as f:
            kpi_map: Dict[str, Any] = json.load(f)
    else:
        kpi_map = {}

    valid_dim_members = None
    if real_segment_tags is not None:
        valid_dim_members = {(t["dimension"], t["member"]) for t in real_segment_tags}

    existing = kpi_map.get(ticker, [])
    existing_names = {e.get("kpi_name", "") for e in existing}
    # (revenue_tag, member_tag) で重複チェック（名前が違っても同一XBRLデータは追加しない）
    existing_tag_members = {
        (e.get("revenue_tag", ""), e.get("tag_history", [{}])[0].get("tag", ""))
        for e in existing
    }

    added = 0
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

        # セグメント指標のxbrl_member実在照合（却下は必ず表示する）
        if xbrl_dim and xbrl_mem and valid_dim_members is not None:
            if (xbrl_dim, xbrl_mem) not in valid_dim_members:
                print(
                    f"    [kpi_map] 却下（実XBRLに存在しないタグ）: "
                    f"{kpi_name} → dimension={xbrl_dim}, member={xbrl_mem}"
                )
                continue

        tag_key = (xbrl_tag, xbrl_mem)
        if tag_key in existing_tag_members:
            print(f"    [kpi_map] スキップ（tag+member重複）: {kpi_name}")
            continue

        entry: Dict[str, Any] = {
            "kpi_name":     kpi_name,
            "change_risk":  "medium",
            "tag_history":  [{"tag": xbrl_mem, "valid_from": "2010-01-01", "valid_to": None}],
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
    # core限定ゲートは2026-08-19④に撤廃した。撤廃前はbuild_kpi_prompt()が
    # coreスキーマのフィールド名（thesis/exit_guide）を直接読んでおり、
    # satelliteに適用するとスキーマ不整合により全て「未設定」を提案の
    # 根拠として使ってしまう実バグが存在した。このゲートは意図的な方針
    # ではなく、そのバグを偶然マスクしていただけだったため、
    # thesis_narrative_fields()によるスキーマ吸収（上記build_kpi_prompt()
    # 参照）を実装した上で撤廃した（[[TAIL-KPI-PROPOSER-CORE-ONLY-
    # GATE-1]]対応）。

    cik    = load_cik(ticker)
    existing_kpi_map  = load_kpi_map().get(ticker, [])
    real_segment_tags = fetch_real_segment_tags(ticker, cik)
    print(f"  実XBRLセグメントタグ: {len(real_segment_tags)}件抽出")
    prompt = build_kpi_prompt(thesis, cik, existing_kpi_map, real_segment_tags)

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

    # auto_fetchable=true のKPIをtail_kpi_map.jsonに自動追記
    # （tag+member重複・実XBRLに存在しないセグメントタグはスキップ）
    update_tail_kpi_map(ticker, kpis, real_segment_tags)

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
