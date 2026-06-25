#!/usr/bin/env python3
"""
src/discover/catalyst.py
HypeCoreの全銘柄を対象に、Grok Web検索でカタリスト（株価インパクト要因）を
発掘・追跡する。毎週日曜 JST 23:30 に自動実行。

使い方:
  python src/discover/catalyst.py             # 全銘柄処理
  python src/discover/catalyst.py --all       # 同上（明示）
  python src/discover/catalyst.py --ticker NVDA,IONQ
  python src/discover/catalyst.py --dry-run   # API呼び出しなし・構造確認のみ
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve()
PROJECT_ROOT = _HERE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from common.sec_data.tickers import get_hypecore_tickers

XAI_API_KEY = os.getenv("XAI_API_KEY")
JST = timezone(timedelta(hours=9))
GROK_URL = "https://api.x.ai/v1/chat/completions"
OUT_PATH = PROJECT_ROOT / "docs" / "discover" / "data" / "catalyst.json"


# ── Grok 呼び出し ──────────────────────────────────────────

def call_grok(prompt: str, max_tokens: int = 1500) -> str:
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY が設定されていません")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}",
    }
    resp = requests.post(GROK_URL, headers=headers, json={
        "model": "grok-3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }, timeout=180)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json_object(text: str) -> dict:
    text = text.replace("```json", "").replace("```", "").strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group())
    raise ValueError("JSONオブジェクトが見つかりません")


def _extract_json_array(text: str) -> list:
    text = text.replace("```json", "").replace("```", "").strip()
    # 配列優先、なければオブジェクト内のリストを探す
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        return json.loads(m.group())
    # {"updates": [...]} 形式への対応
    m2 = re.search(r'\{.*\}', text, re.DOTALL)
    if m2:
        obj = json.loads(m2.group())
        for v in obj.values():
            if isinstance(v, list):
                return v
    raise ValueError("JSON配列が見つかりません")


# ── ID採番 ─────────────────────────────────────────────────

def next_id(ticker: str, year: int, existing_ids: set) -> str:
    prefix = f"{ticker}-{year}-"
    seq = 1
    while True:
        cid = f"{prefix}{seq:03d}"
        if cid not in existing_ids:
            return cid
        seq += 1


# ── Grok プロンプト ─────────────────────────────────────────

def discover_catalysts(ticker: str) -> list:
    prompt = f"""{ticker}について今後12ヶ月以内に「カタリストになり得る事象」を幅広く列挙してください。
確定イベント（決算・製品ローンチ・FDA申請等）だけでなく、
不確定だが実現すれば株価インパクトが大きい事象も含めてください。
例: 黒字化転換、指数採用、大型契約獲得、競合の失速、規制緩和等

以下のJSON形式で回答してください（日本語）。JSON以外のテキストは不要です。
{{
  "catalysts": [
    {{
      "title": "カタリストの短いタイトル（20字以内）",
      "detail": "詳細説明（100字以内）",
      "timing": "予定・想定時期（例: 2026 Q3, 2026年内, 2027年以降）",
      "importance": "高|中|低",
      "type": "確定イベント|不確定シナリオ",
      "probability": "高|中|低"
    }}
  ]
}}"""
    text = call_grok(prompt)
    data = _extract_json_object(text)
    items = data.get("catalysts", [])
    if not isinstance(items, list):
        raise ValueError("catalysts がリストではありません")
    return items


def reevaluate_catalysts(ticker: str, pending: list) -> dict:
    """既存「未達」カタリストのstatus更新。{id: new_status} を返す"""
    if not pending:
        return {}
    items_json = json.dumps(
        [{"id": c["id"], "title": c["title"], "detail": c["detail"]} for c in pending],
        ensure_ascii=False, indent=2
    )
    prompt = f"""{ticker}の以下のカタリスト候補について、最新情報をweb検索で確認してください。
各カタリストが現時点で「未達」「達成済み」「消滅」のどれに該当するかを判定してください。

status の定義:
- 未達: まだ実現していない（引き続き可能性あり）
- 達成済み: 実現・達成された
- 消滅: 実現の可能性がなくなった、またはシナリオ自体が消えた

以下のJSON配列形式で回答してください。JSON以外のテキストは不要です。
[
  {{"id": "カタリストID", "status": "未達|達成済み|消滅"}}
]

対象カタリスト:
{items_json}"""
    text = call_grok(prompt, max_tokens=800)
    updates = _extract_json_array(text)
    result = {}
    for u in updates:
        cid = u.get("id")
        status = u.get("status")
        if cid and status in ("未達", "達成済み", "消滅"):
            result[cid] = status
    return result


# ── 銘柄処理 ────────────────────────────────────────────────

def process_ticker(ticker: str, existing: dict, today: str, dry_run: bool) -> dict:
    ticker_data = existing.get(ticker, {"updated_at": today, "catalysts": []})
    existing_catalysts = list(ticker_data.get("catalysts", []))
    existing_ids = {c["id"] for c in existing_catalysts}
    year = date.today().year

    if dry_run:
        print(f"  [dry-run] {ticker}: 既存{len(existing_catalysts)}件")
        return ticker_data

    # ── 呼び出し①: 新規カタリスト発掘 ────────────────────────
    print(f"  [{ticker}] 新規カタリスト発掘中...")
    new_catalysts = []
    try:
        raw_items = discover_catalysts(ticker)
        print(f"    Grok → {len(raw_items)}件取得")
        for item in raw_items:
            cid = next_id(ticker, year, existing_ids)
            existing_ids.add(cid)
            new_catalysts.append({
                "id":             cid,
                "title":          str(item.get("title", ""))[:40],
                "detail":         str(item.get("detail", ""))[:200],
                "timing":         str(item.get("timing", "")),
                "importance":     item.get("importance", "中") if item.get("importance") in ("高", "中", "低") else "中",
                "type":           item.get("type", "不確定シナリオ") if item.get("type") in ("確定イベント", "不確定シナリオ") else "不確定シナリオ",
                "probability":    item.get("probability", "中") if item.get("probability") in ("高", "中", "低") else "中",
                "status":         "未達",
                "first_detected": today,
                "last_updated":   today,
            })
    except Exception as e:
        print(f"    [WARN] 発掘失敗: {e}")

    # ── 呼び出し②: 既存「未達」カタリストの再評価 ─────────────
    pending = [c for c in existing_catalysts if c.get("status") == "未達"]
    if pending:
        print(f"  [{ticker}] 既存{len(pending)}件を再評価中...")
        try:
            status_map = reevaluate_catalysts(ticker, pending)
            updated_count = 0
            for c in existing_catalysts:
                new_status = status_map.get(c["id"])
                if new_status and new_status != c.get("status"):
                    print(f"    {c['id']}: {c['status']} → {new_status}")
                    c["status"] = new_status
                    c["last_updated"] = today
                    updated_count += 1
            print(f"    status更新: {updated_count}件")
        except Exception as e:
            print(f"    [WARN] 再評価失敗: {e}")

    merged = existing_catalysts + new_catalysts
    print(f"  [{ticker}] 完了: 既存{len(existing_catalysts)} + 新規{len(new_catalysts)} = 合計{len(merged)}件")
    return {
        "updated_at": today,
        "catalysts":  merged,
    }


# ── メイン ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="HypeCore銘柄のカタリスト発掘・追跡")
    parser.add_argument("--ticker",  help="カンマ区切りで銘柄指定 (例: NVDA,IONQ)")
    parser.add_argument("--all",     dest="run_all", action="store_true", default=False,
                        help="全銘柄処理（--ticker 未指定時と同じ）")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true",
                        help="Grok API呼び出しをスキップ、既存データの構造確認のみ")
    args = parser.parse_args()

    # 対象銘柄を決定
    if args.ticker:
        tickers = [t.strip().upper() for t in args.ticker.split(",") if t.strip()]
        print(f"[INFO] 指定銘柄: {len(tickers)}件 {tickers}")
    else:
        try:
            tickers = get_hypecore_tickers()
            print(f"[INFO] hypecore対象: {len(tickers)}銘柄 (cik_lookup.csv)")
        except Exception as e:
            print(f"[ERROR] get_hypecore_tickers失敗: {e}")
            sys.exit(1)

    if not tickers:
        print("[ERROR] 対象銘柄なし")
        sys.exit(1)

    # 既存データ読み込み
    existing_tickers: dict = {}
    if OUT_PATH.exists():
        try:
            data = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            existing_tickers = data.get("tickers", {})
            print(f"[INFO] 既存データ: {len(existing_tickers)}銘柄分 ({OUT_PATH.name})")
        except Exception as e:
            print(f"[WARN] 既存データ読み込み失敗（新規作成します）: {e}")

    today = date.today().isoformat()
    success, failed = [], []

    for ticker in tickers:
        print(f"\n── {ticker} ──")
        try:
            result = process_ticker(ticker, existing_tickers, today, args.dry_run)
            existing_tickers[ticker] = result
            success.append(ticker)
        except Exception as e:
            print(f"  [ERROR] {ticker}: {e}")
            failed.append(ticker)

    # 保存
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "tickers": existing_tickers,
    }
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"保存完了: {OUT_PATH}")
    print(f"完了: {len(success)}銘柄成功 / {len(failed)}銘柄失敗")
    if failed:
        print(f"失敗銘柄: {', '.join(failed)}")


if __name__ == "__main__":
    main()
