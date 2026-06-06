#!/usr/bin/env python3
"""
TANUKI TAIL — text_kpi_extractor.py

kpi_proposals/{ticker}_proposal.json の auto_fetchable=false のKPIを
EDGAR 10-Q MD&A + 8-K Exhibit 99.1 のテキストからGrokで抽出する（Layer 3）。

使用方法:
    python src/tail/text_kpi_extractor.py --ticker PLTR
    python src/tail/text_kpi_extractor.py --ticker PLTR SOFI TSLA

出力: docs/portfolio/tail/data/kpi/{ticker}_layer3.json
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
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List, Tuple

# ── パス設定 ──────────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root  = os.path.abspath(os.path.join(script_dir, "..", ".."))

DATA_DIR          = os.path.join(repo_root, "docs", "portfolio", "tail", "data")
KPI_DIR           = os.path.join(DATA_DIR, "kpi")
KPI_PROPOSALS_DIR = os.path.join(DATA_DIR, "kpi_proposals")
CIK_LOOKUP_PATH   = os.path.join(repo_root, "config", "cik_lookup.csv")

JST = ZoneInfo("Asia/Tokyo")

EDGAR_BASE  = "https://www.sec.gov"
EDGAR_DATA  = "https://data.sec.gov"
EDGAR_HDR   = {"User-Agent": "TANUKI-TAIL-Bot contact@example.com", "Accept-Encoding": "gzip, deflate"}

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_URL    = "https://api.x.ai/v1/chat/completions"
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]

EXTRACT_SYSTEM = (
    "あなたは決算資料からKPI数値を抽出する専門家です。"
    "数値が明示されていない場合はnullを返してください。"
    "推測・計算による補完は禁止です。"
    "回答はJSON形式のみで返してください。"
    "回答はすべて日本語で記述してください。"
)

MAX_TEXT_CHARS = 12000

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Grok API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def call_grok(user_prompt: str, system_prompt: str = "", max_tokens: int = 3000) -> str:
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY が設定されていません")
    headers  = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
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
                json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.1},
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
# CIK・Proposal 読み込み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_cik(ticker: str) -> Optional[str]:
    if not os.path.exists(CIK_LOOKUP_PATH):
        return None
    with open(CIK_LOOKUP_PATH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("ticker", "").upper() == ticker.upper():
                return row.get("cik", "").strip()
    return None


def load_proposal(ticker: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(KPI_PROPOSALS_DIR, f"{ticker}_proposal.json")
    if not os.path.exists(path):
        print(f"  [WARN] proposal未発見: {path}")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_manual_kpis(proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [k for k in proposal.get("proposed_kpis", []) if not k.get("auto_fetchable")]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EDGAR テキスト取得
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def edgar_get(url: str, timeout: int = 30) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, headers=EDGAR_HDR, timeout=timeout)
        resp.raise_for_status()
        time.sleep(0.15)
        return resp
    except Exception as e:
        print(f"  [EDGAR] 取得失敗 {url}: {e}")
        return None


def get_recent_filings(cik: str, form_type: str, count: int = 5) -> List[Dict[str, Any]]:
    cik_int = int(cik.lstrip("0") or "0")
    url  = f"{EDGAR_DATA}/submissions/CIK{cik_int:010d}.json"
    resp = edgar_get(url)
    if not resp:
        return []

    data    = resp.json()
    recent  = data.get("filings", {}).get("recent", {})
    forms   = recent.get("form", [])
    accns   = recent.get("accessionNumber", [])
    dates   = recent.get("filingDate", [])
    reports = recent.get("reportDate", [])
    pdocs   = recent.get("primaryDocument", [])

    result: List[Dict[str, Any]] = []
    for i, form in enumerate(forms):
        if form.strip().upper() == form_type.upper():
            result.append({
                "form":            form,
                "accession":       accns[i] if i < len(accns) else "",
                "filing_date":     dates[i] if i < len(dates) else "",
                "report_date":     reports[i] if i < len(reports) else "",
                "primary_document": pdocs[i] if i < len(pdocs) else "",
            })
            if len(result) >= count:
                break

    return result


def strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;",  "&", text)
    text = re.sub(r"&lt;",   "<", text)
    text = re.sub(r"&gt;",   ">", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s{3,}", "\n", text)
    return text.strip()


def extract_mda_section(text: str, max_chars: int = 8000) -> str:
    # 目次に Item2/Item3 が連続して出るため、すべての "Item 2" 出現位置を探し
    # 最も長いセクション（ToC外の本文）を選ぶ
    item2_re = re.compile(r"(?i)item\s+2[\.\s]")
    item3_re = re.compile(r"(?i)item\s+3[\.\s]")

    starts = [m.start() for m in item2_re.finditer(text)]
    if not starts:
        return text[:max_chars]

    best_start = starts[0]
    best_length = 0
    for s in starts:
        m_end = item3_re.search(text, s + 200)
        end = m_end.start() if m_end else s + max_chars * 2
        length = end - s
        if length > best_length:
            best_length = length
            best_start  = s

    m_end = item3_re.search(text, best_start + 200)
    end = m_end.start() if m_end else best_start + max_chars * 2
    return text[best_start:end][:max_chars]


def fetch_10q_mda(cik: str) -> Tuple[Optional[str], Optional[str]]:
    """最新10-QのMD&Aテキストと四半期文字列(e.g. "2026Q1")を返す"""
    filings = get_recent_filings(cik, "10-Q", count=1)
    if not filings:
        print("  [EDGAR] 10-Q が見つかりません")
        return None, None

    filing   = filings[0]
    accn     = filing["accession"]
    pdoc     = filing["primary_document"]
    report   = filing["report_date"]
    cik_int  = int(cik.lstrip("0") or "0")
    accn_nd  = accn.replace("-", "")

    if not pdoc:
        print(f"  [EDGAR] primaryDocument なし ({accn})")
        return None, None

    url  = f"{EDGAR_BASE}/Archives/edgar/data/{cik_int}/{accn_nd}/{pdoc}"
    print(f"  [EDGAR] 10-Q 取得: {url}")
    resp = edgar_get(url, timeout=90)
    if not resp:
        return None, None

    # inline XBRL は数MBになるため、後半だけ使う（MD&A は後半にある）
    html = resp.text
    if len(html) > 400_000:
        # 前半の目次・財務諸表を飛ばして MD&A が存在しやすい中盤から取得
        html = html[len(html) // 4:]
    raw_text = strip_html(html)
    mda_text = extract_mda_section(raw_text)

    quarter = _report_date_to_quarter(report)
    print(f"  [EDGAR] 10-Q MD&A 取得完了 ({len(mda_text)}文字, {quarter})")
    return mda_text, quarter


def fetch_8k_exhibit99(cik: str) -> Optional[str]:
    """最新8-KのExhibit 99.1テキストを返す"""
    filings = get_recent_filings(cik, "8-K", count=5)
    if not filings:
        print("  [EDGAR] 8-K が見つかりません")
        return None

    cik_int = int(cik.lstrip("0") or "0")

    for filing in filings:
        accn    = filing["accession"]
        accn_nd = accn.replace("-", "")
        idx_url = f"{EDGAR_BASE}/Archives/edgar/data/{cik_int}/{accn_nd}/{accn}-index.htm"
        resp    = edgar_get(idx_url)
        if not resp:
            continue

        # EX-99.1 のリンクを探す
        m = re.search(
            r'<td[^>]*>EX-99\.1</td>.*?<a[^>]+href="([^"]+)"',
            resp.text, re.DOTALL | re.IGNORECASE
        )
        if not m:
            continue

        ex_path = m.group(1)
        if not ex_path.startswith("http"):
            ex_path = EDGAR_BASE + ex_path
        ex_resp = edgar_get(ex_path, timeout=60)
        if not ex_resp:
            continue

        text = strip_html(ex_resp.text)[:6000]
        print(f"  [EDGAR] 8-K EX-99.1 取得完了 ({len(text)}文字)")
        return text

    print("  [EDGAR] 8-K EX-99.1 見つからず")
    return None


def _report_date_to_quarter(report_date: str) -> str:
    """'2026-03-31' → '2026Q1'"""
    if not report_date or len(report_date) < 7:
        return "不明"
    year  = int(report_date[:4])
    month = int(report_date[5:7])
    q     = (month - 1) // 3 + 1
    return f"{year}Q{q}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Grokプロンプト構築
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_extract_prompt(
    ticker: str,
    quarter: str,
    kpis: List[Dict[str, Any]],
    filing_text: str,
) -> str:
    kpi_list = json.dumps(
        [{"name": k["name"], "extraction_hint": k.get("extraction_hint", "")} for k in kpis],
        ensure_ascii=False, indent=2
    )
    return f"""## 抽出対象KPI（extraction_hint付き）
{kpi_list}

## 決算資料テキスト（{ticker} {quarter}）
{filing_text}

## 出力形式（JSONのみ、説明文不要）:
{{
  "extracted_kpis": [
    {{
      "name": "NDR（ネット・ダラー・リテンション）",
      "value": "150%",
      "value_numeric": 150,
      "unit": "%",
      "source_text": "抽出元の原文（50文字以内）",
      "confidence": "high",
      "quarter": "{quarter}"
    }}
  ],
  "not_found": ["見つからなかったKPI名"]
}}

ルール:
- 数値が明示されている場合のみ value を記入（推測・計算禁止）
- 見つからない場合は not_found に名前を入れる
- confidence: high=原文に明記 / medium=文脈から判断 / low=推測要素あり"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1銘柄の Layer 3 生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def extract_layer3(ticker: str, dry_run: bool = False) -> Optional[str]:
    ticker = ticker.upper()
    print(f"\n{'─' * 60}")
    print(f"  {ticker} Layer 3 テキスト抽出")
    print(f"{'─' * 60}")

    cik = load_cik(ticker)
    if not cik:
        print(f"  [ERROR] {ticker} の CIK が見つかりません")
        return None

    proposal   = load_proposal(ticker)
    manual_kpis = get_manual_kpis(proposal) if proposal else []

    if not manual_kpis:
        print(f"  [SKIP] {ticker} に auto_fetchable=false のKPIがありません")
        return None

    print(f"  抽出対象KPI: {len(manual_kpis)} 件")
    for k in manual_kpis:
        print(f"    - {k['name']} (hint: {k.get('extraction_hint', '—')})")

    # EDGAR テキスト取得
    mda_text, quarter = fetch_10q_mda(cik)
    if not mda_text:
        print(f"  [ERROR] 10-Q MD&A テキスト取得失敗")
        return None

    ex99_text = fetch_8k_exhibit99(cik)

    # テキスト結合（最大MAX_TEXT_CHARS）
    combined = mda_text
    if ex99_text:
        remaining = MAX_TEXT_CHARS - len(combined)
        if remaining > 500:
            combined += f"\n\n--- 決算プレスリリース (8-K EX-99.1) ---\n{ex99_text[:remaining]}"

    if dry_run:
        print(f"\n=== [DRY-RUN] 取得テキスト（先頭500文字） ===")
        print(combined[:500])
        print(f"...\n=== DRY-RUN 完了（Grok呼び出しなし） ===")
        return None

    # Grok で KPI 抽出
    prompt = build_extract_prompt(ticker, quarter or "不明", manual_kpis, combined)
    print(f"\n  ── Grok KPI 抽出 ({ticker} {quarter}) ──")
    raw = call_grok(user_prompt=prompt, system_prompt=EXTRACT_SYSTEM, max_tokens=2000)
    result = extract_json_from_response(raw)

    extracted   = result.get("extracted_kpis", [])
    not_found   = result.get("not_found", [])

    print(f"  抽出結果: {len(extracted)} 件取得 / {len(not_found)} 件未発見")
    for e in extracted:
        print(f"    ✓ [{e.get('confidence','?')}] {e.get('name','?')}: {e.get('value','?')}")
    for nf in not_found:
        print(f"    ✗ 未発見: {nf}")

    kpis_map: Dict[str, Any] = {}
    for e in extracted:
        name = e.get("name", "")
        if name:
            kpis_map[name] = {
                "value":       e.get("value"),
                "value_numeric": e.get("value_numeric"),
                "unit":        e.get("unit", ""),
                "source_text": e.get("source_text", ""),
                "confidence":  e.get("confidence", "medium"),
                "quarter":     e.get("quarter", quarter),
            }

    os.makedirs(KPI_DIR, exist_ok=True)
    now_jst   = datetime.now(JST)
    out_path  = os.path.join(KPI_DIR, f"{ticker}_layer3.json")
    layer3_complete = len(not_found) == 0

    output = {
        "ticker":          ticker,
        "fetched_at":      now_jst.isoformat(),
        "quarter":         quarter,
        "layer3_complete": layer3_complete,
        "not_found":       not_found,
        "kpis":            kpis_map,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  ✓ layer3.json 保存: {out_path}")
    return out_path


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エントリーポイント
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    parser = argparse.ArgumentParser(description="TANUKI TAIL — Layer 3 テキストKPI抽出")
    parser.add_argument("--ticker", nargs="+", required=True, help="対象ティッカー（複数指定可）")
    parser.add_argument("--dry-run", action="store_true", help="Grok呼び出しをスキップ")
    args = parser.parse_args()

    now_jst = datetime.now(JST)
    print(f"TANUKI TAIL Layer 3 テキスト抽出 — {now_jst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 60)

    results: Dict[str, bool] = {}
    for t in args.ticker:
        try:
            path = extract_layer3(t, dry_run=args.dry_run)
            results[t.upper()] = path is not None or args.dry_run
        except Exception as e:
            print(f"  [ERROR] {t}: {e}")
            results[t.upper()] = False

    print(f"\n{'━' * 60}")
    for t, ok in results.items():
        print(f"  {'OK' if ok else 'NG'}: {t}")


if __name__ == "__main__":
    main()
