"""
TANUKI VALUATION - History Backfill Script
May 14-16 の history ファイルを v8.2 ロジック（R&D資本化補正済み）で再計算して上書きする。

戦略:
  - DCF計算値（intrinsic_value_per_share, rd_capitalization 等）: latest.json から取得
  - 市場データ（current_price, ma200）: 元の歴史ファイルを保持
  - upside_percent: 新理論株価 / 元の current_price で再計算
  - history.json（グラフ用サマリ）も同時に更新
"""

import json
import os
import copy
from datetime import datetime

TARGET_DATES = ["2026-05-14", "2026-05-15", "2026-05-16"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
DATA_ROOT = os.path.join(REPO_ROOT, "docs", "value-monitor", "tanuki_valuation", "data")


def recalc_upside(intrinsic: float, current_price: float) -> float:
    if not current_price or current_price <= 0:
        return 0.0
    return round((intrinsic / current_price - 1) * 100, 1)


def backfill_ticker(ticker_dir: str, ticker: str) -> None:
    latest_path = os.path.join(ticker_dir, "latest.json")
    history_dir = os.path.join(ticker_dir, "history")
    history_json_path = os.path.join(ticker_dir, "history.json")

    if not os.path.exists(latest_path):
        print(f"  [{ticker}] latest.json なし → スキップ")
        return
    if not os.path.isdir(history_dir):
        print(f"  [{ticker}] history/ ディレクトリなし → スキップ")
        return

    with open(latest_path, encoding="utf-8") as f:
        latest = json.load(f)

    # rd_capitalization が latest.json に含まれているか確認
    if not latest.get("rd_capitalization"):
        print(f"  [{ticker}] latest.json に rd_capitalization なし → スキップ")
        return

    # history.json を読み込み
    history_summary = []
    if os.path.exists(history_json_path):
        try:
            with open(history_json_path, encoding="utf-8") as f:
                history_summary = json.load(f)
        except Exception:
            history_summary = []

    updated_dates = []

    for target_date in TARGET_DATES:
        hist_path = os.path.join(history_dir, f"{target_date}.json")
        if not os.path.exists(hist_path):
            print(f"  [{ticker}] {target_date}.json なし → スキップ")
            continue

        with open(hist_path, encoding="utf-8") as f:
            original = json.load(f)

        # 既に v8.2 適用済みならスキップ
        if original.get("rd_capitalization", {}).get("applied") is not None:
            if original.get("rd_capitalization", {}).get("applied") == latest.get("rd_capitalization", {}).get("applied"):
                # rd_capitalization が同じ applied 状態 かつ intrinsic も同値なら既適用
                if abs((original.get("intrinsic_value_per_share", 0) or 0) -
                       (latest.get("intrinsic_value_per_share", 0) or 0)) < 0.01:
                    print(f"  [{ticker}] {target_date}: 既に v8.2 適用済み → スキップ")
                    continue

        # 元ファイルの市場データを保存
        orig_comps = original.get("components", {})
        orig_current_price = orig_comps.get("current_price")
        orig_ma200 = orig_comps.get("ma200")

        # latest.json をベースに新レコードを作成
        new_record = copy.deepcopy(latest)
        new_record["calculation_date"] = target_date

        # 市場データを元の日付のものに戻す
        if "components" in new_record:
            if orig_current_price is not None:
                new_record["components"]["current_price"] = orig_current_price
            if orig_ma200 is not None:
                new_record["components"]["ma200"] = orig_ma200

        # upside_percent を元の株価で再計算
        new_intrinsic = new_record.get("intrinsic_value_per_share", 0)
        new_record["upside_percent"] = recalc_upside(new_intrinsic, orig_current_price)

        # history/YYYY-MM-DD.json を上書き
        with open(hist_path, "w", encoding="utf-8") as f:
            json.dump(new_record, f, ensure_ascii=False, indent=2)

        # history.json サマリを更新
        new_entry = {
            "date": target_date,
            "intrinsic_value_per_share": new_record.get("intrinsic_value_per_share"),
            "intrinsic_value_beta": new_record.get("intrinsic_value_beta"),
            "current_price": orig_current_price,
            "ma200": orig_ma200,
            "upside_percent": new_record["upside_percent"],
            "growth_rate": new_record.get("growth_scenarios", {}).get("primary", {}).get("rate"),
            "scenario_bear": new_record.get("scenario_valuations", {}).get("bear", {}).get("intrinsic_value_per_share"),
            "scenario_bull": new_record.get("scenario_valuations", {}).get("bull", {}).get("intrinsic_value_per_share"),
        }
        history_summary = [e for e in history_summary if e.get("date") != target_date]
        history_summary.append(new_entry)
        updated_dates.append(target_date)

        orig_iv = original.get("intrinsic_value_per_share", 0)
        print(f"  [{ticker}] {target_date}: {orig_iv:.2f} → {new_intrinsic:.2f} (current_price={orig_current_price})")

    if updated_dates:
        history_summary.sort(key=lambda e: e.get("date", ""))
        with open(history_json_path, "w", encoding="utf-8") as f:
            json.dump(history_summary, f, ensure_ascii=False, indent=2)
        print(f"  [{ticker}] history.json 更新済み ({', '.join(updated_dates)})")


def main():
    print("=" * 60)
    print("TANUKI VALUATION - May 14-16 History Backfill (v8.2)")
    print(f"  対象日: {', '.join(TARGET_DATES)}")
    print(f"  データルート: {DATA_ROOT}")
    print("=" * 60)

    ticker_dirs = sorted([
        d for d in os.listdir(DATA_ROOT)
        if os.path.isdir(os.path.join(DATA_ROOT, d))
    ])

    total = 0
    for ticker in ticker_dirs:
        ticker_dir = os.path.join(DATA_ROOT, ticker)
        backfill_ticker(ticker_dir, ticker)
        total += 1

    print(f"\n完了: {total} ティッカー処理")


if __name__ == "__main__":
    main()
