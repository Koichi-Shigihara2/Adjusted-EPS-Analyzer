#!/usr/bin/env python3
"""
src/discover/impact_predictor.py
ニュース(news_history)・カタリスト(catalyst)の新規項目に対し、
株価/シナリオへの影響予測（方向・度合い・保有テーゼへの影響）を1行サマリで生成する。

collect.py（毎日 JST 7:03）・catalyst.py（毎週日曜 JST 23:30）の実行後に
それぞれ呼び出す独立パイプライン。既存スクリプト自体は変更しない。

使い方:
  python src/discover/impact_predictor.py --source news       # collect.py実行後
  python src/discover/impact_predictor.py --source catalyst   # catalyst.py実行後
  python src/discover/impact_predictor.py --source news --dry-run
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_HERE = Path(__file__).resolve()
PROJECT_ROOT = _HERE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests

XAI_API_KEY = os.getenv("XAI_API_KEY")
JST = timezone(timedelta(hours=9))
GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODELS = ["grok-3-mini", "grok-3", "grok-2-1212"]
DATA_DIR = PROJECT_ROOT / "docs" / "discover" / "data"

VALID_DIRECTION = {"positive", "negative", "neutral"}
VALID_MAGNITUDE = {"高", "中", "低"}
VALID_EFFECT = {"補強", "弱化", "中立"}


# ── Grok 呼び出し ──────────────────────────────────────────

def call_grok(prompt: str, max_tokens: int = 1200) -> str:
    if not XAI_API_KEY:
        raise RuntimeError("XAI_API_KEY が設定されていません")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {XAI_API_KEY}"}
    last_error = None
    for model in GROK_MODELS:
        try:
            resp = requests.post(GROK_URL, headers=headers, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            }, timeout=120)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
    raise last_error


def _extract_json_object(text: str) -> dict:
    text = text.replace("```json", "").replace("```", "").strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        return json.loads(m.group())
    raise ValueError("JSONオブジェクトが見つかりません")


def _normalize_prediction(p: dict) -> dict:
    direction = p.get("direction") if p.get("direction") in VALID_DIRECTION else "neutral"
    magnitude = p.get("magnitude") if p.get("magnitude") in VALID_MAGNITUDE else "低"
    effect = p.get("thesis_effect") if p.get("thesis_effect") in VALID_EFFECT else "中立"
    summary = str(p.get("summary", ""))[:80]
    return {"direction": direction, "magnitude": magnitude, "thesis_effect": effect, "summary": summary}


def predict_for_items(ticker: str, prompt_items: list) -> dict:
    """prompt_items: [{"id": "...", "title": "...", "context": "..."}] → {id: prediction}"""
    lines = "\n".join(
        f'- id={it["id"]}: {it["title"]}' + (f'（{it["context"]}）' if it.get("context") else "")
        for it in prompt_items
    )
    prompt = f"""あなたは投資アナリストです。以下は{ticker}に関する項目一覧です。
各項目について、株価・投資シナリオへの影響を分析してください。

項目一覧：
{lines}

各項目について以下のJSON形式で回答してください（他のテキスト不要、idは入力と完全一致させること）：
{{"predictions": [{{"id": "入力と同じid", "direction": "positive/negative/neutralのいずれか（株価・シナリオへの影響方向）", "magnitude": "高/中/低のいずれか（影響の度合い）", "thesis_effect": "補強/弱化/中立のいずれか（保有テーゼへの影響）", "summary": "30字以内の日本語1行要約"}}]}}"""
    text = call_grok(prompt)
    data = _extract_json_object(text)
    preds = data.get("predictions", [])
    result = {}
    for p in preds:
        pid = p.get("id")
        if pid is not None:
            result[str(pid)] = _normalize_prediction(p)
    return result


def _load_or_init(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"news": {}, "catalyst": {}}


# ── news モード（collect.py後）────────────────────────────

def run_news(today_str: str, dry_run: bool) -> None:
    ym = today_str[:7].replace("-", "_")
    hist_path = DATA_DIR / f"news_history_{ym}.json"
    if not hist_path.exists():
        print(f"[WARN] {hist_path} が存在しません")
        return
    try:
        history = json.loads(hist_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] {hist_path} 読み込み失敗: {e}")
        return
    day_data = history.get(today_str, {})
    if not day_data:
        print(f"[INFO] {today_str} のニュースデータなし")
        return

    out_path = DATA_DIR / f"impact_predictions_{ym}.json"
    out = _load_or_init(out_path)
    day_out = out.setdefault("news", {}).setdefault(today_str, {})

    processed, failed = 0, 0
    for ticker, td in day_data.items():
        items = td.get("items", [])
        # id未付与（前提整備前の旧データ）の項目は対象外
        prompt_items = [
            {"id": it["id"], "title": it.get("title", ""), "context": it.get("summary", "")}
            for it in items if it.get("id")
        ]
        if not prompt_items:
            continue
        if dry_run:
            print(f"  [dry-run] news {ticker}: {len(prompt_items)}件")
            continue
        try:
            preds = predict_for_items(ticker, prompt_items)
            day_out[ticker] = preds
            processed += len(preds)
            print(f"  [{ticker}] news予測 {len(preds)}件完了")
        except Exception as e:
            failed += 1
            print(f"  [WARN] {ticker} news予測失敗: {e}")

    if dry_run:
        return
    out["generated_at"] = datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存完了: {out_path}（news予測 {processed}件 / 失敗{failed}銘柄）")


# ── catalyst モード（catalyst.py後）─────────────────────────

def run_catalyst(today_str: str, dry_run: bool) -> None:
    cat_path = DATA_DIR / "catalyst.json"
    if not cat_path.exists():
        print(f"[WARN] {cat_path} が存在しません")
        return
    try:
        catalyst_data = json.loads(cat_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] {cat_path} 読み込み失敗: {e}")
        return
    tickers = catalyst_data.get("tickers", {})

    ym = today_str[:7].replace("-", "_")
    out_path = DATA_DIR / f"impact_predictions_{ym}.json"
    out = _load_or_init(out_path)
    cat_out = out.setdefault("catalyst", {})

    processed, failed = 0, 0
    for ticker, td in tickers.items():
        catalysts = td.get("catalysts", [])
        # 今回の実行で新規発掘された分のみ対象（first_detected==本日）。
        # 既存の累積分は対象外（再評価はreevaluate_catalystsの役割・コスト抑制のため）。
        new_items = [c for c in catalysts if c.get("first_detected") == today_str]
        if not new_items:
            continue
        prompt_items = [
            {"id": c["id"], "title": c.get("title", ""), "context": c.get("detail", "")}
            for c in new_items
        ]
        if dry_run:
            print(f"  [dry-run] catalyst {ticker}: {len(prompt_items)}件")
            continue
        try:
            preds = predict_for_items(ticker, prompt_items)
            cat_out.setdefault(ticker, {}).update(preds)
            processed += len(preds)
            print(f"  [{ticker}] catalyst予測 {len(preds)}件完了")
        except Exception as e:
            failed += 1
            print(f"  [WARN] {ticker} catalyst予測失敗: {e}")

    if dry_run:
        return
    out["generated_at"] = datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存完了: {out_path}（catalyst予測 {processed}件 / 失敗{failed}銘柄）")


def main():
    parser = argparse.ArgumentParser(description="ニュース・カタリストの影響予測（独立パイプライン）")
    parser.add_argument("--source", choices=["news", "catalyst"], required=True,
                        help="news=collect.py実行後 / catalyst=catalyst.py実行後")
    parser.add_argument("--dry-run", action="store_true", help="Grok API呼び出しなし・対象件数確認のみ")
    args = parser.parse_args()

    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.source == "news":
        run_news(today_str, args.dry_run)
    else:
        run_catalyst(today_str, args.dry_run)


if __name__ == "__main__":
    main()
