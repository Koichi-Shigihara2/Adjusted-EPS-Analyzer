#!/usr/bin/env python3
"""
05_backfill_nfp_mom.py — NFP既存履歴の水準→前月比 一括変換（MACRO-NFP-HIST-1）

背景:
  MACRO-NFP-1（2026-07-07完了）でNFPの新規fetchロジックを「雇用者数の水準」から
  「前月比（人）」に修正したが、05_events.csv内の既存NFP行（全期間）は
  水準値のまま据え置かれていた。本スクリプトはそれを一括で前月比に変換する。

変換方式（import_from_fred() の NFP 分岐と同一）:
  (level_now - level_prev) * 1000

対象月の判定ルール:
  - release_date の日が「01」の行（旧FRED一括投入 or スケジュール未一致の
    refresh_monthly_indicators() 由来）: release_date の月そのものが観測月
  - release_date の日が「01」以外の行（実際のBLS発表日でスケジュール一致した
    refresh_monthly_indicators() 由来。例: 2026-04-03）: 発表日は「前月分」の
    データを報じるため、release_date の月の1ヶ月前が観測月
  （NFPのスケジュール発表日はBLS慣行上、月初1日になることはないため両者は
   曖昧なく判別できる。05_indicator_schedule.csv の実データでも確認済み）

consensus/surprise の扱い:
  forecast_source="actual_as_forecast"（consensusがactualのコピー）の行は
  consensus/surprise/surprise_pctも新しいactualに合わせて更新する。
  それ以外（consensus空欄の履歴行）はactualのみ更新する。

使い方:
  python src/market/macro_pulse/05_backfill_nfp_mom.py --dry-run
  python src/market/macro_pulse/05_backfill_nfp_mom.py
"""
import os
import sys
import shutil
import argparse
import logging
from datetime import datetime, date

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(__file__))
import importlib.util, pathlib

_main_path = pathlib.Path(__file__).parent / "05_main.py"
_spec = importlib.util.spec_from_file_location("main05_backfill", _main_path)
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)

EVENTS_PATH    = _m.EVENTS_PATH
load_events    = _m.load_events
save_events    = _m.save_events
get_fred       = _m.get_fred

FRED_ID = "PAYEMS"


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _prev_month_start(d: date) -> date:
    if d.month == 1:
        return date(d.year - 1, 12, 1)
    return date(d.year, d.month - 1, 1)


def _obs_month_for_row(release_date: date) -> date:
    """release_dateからNFPの観測月（PAYEMS obs_date）を判定する。"""
    if release_date.day == 1:
        return _month_start(release_date)
    return _prev_month_start(release_date)


def backfill(dry_run: bool = False) -> int:
    fred = get_fred()
    if fred is None:
        logger.error("FRED_API_KEY が設定されていません。")
        sys.exit(1)

    events = load_events()
    nfp_mask = events["indicator"] == "NFP"
    nfp_count = int(nfp_mask.sum())
    if nfp_count == 0:
        logger.info("NFP行が存在しません。終了。")
        return 0
    logger.info(f"NFP行数: {nfp_count}")

    # 全期間のPAYEMS水準系列を取得（最古行の観測月-1ヶ月分の余裕を持たせる）
    logger.info(f"FRED [{FRED_ID}] 全期間を取得中...")
    s = fred.get_series(FRED_ID, observation_start="1990-01-01",
                        observation_end=date.today().strftime("%Y-%m-%d"))
    s = s.dropna().sort_index()
    level_by_month = {ts.date(): float(v) for ts, v in s.items()}
    logger.info(f"PAYEMS観測数: {len(level_by_month)}件 "
                f"({min(level_by_month)} 〜 {max(level_by_month)})")

    updated = 0
    skipped = []

    for idx in events[nfp_mask].index:
        row = events.loc[idx]
        try:
            rd = datetime.strptime(str(row["release_date"]), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            skipped.append((row["event_id"], "release_date不正"))
            continue

        obs_month = _obs_month_for_row(rd)
        prev_month = _prev_month_start(obs_month)

        level_now = level_by_month.get(obs_month)
        level_prev = level_by_month.get(prev_month)

        if level_now is None or level_prev is None:
            skipped.append((row["event_id"], f"obs={obs_month} prev={prev_month} のFREDデータなし"))
            continue

        old_actual = row["actual"]
        new_actual = round((level_now - level_prev) * 1000, 4)

        events.at[idx, "actual"] = str(new_actual)
        if str(row.get("forecast_source", "")).strip() == "actual_as_forecast":
            events.at[idx, "consensus"] = str(new_actual)
            events.at[idx, "surprise"] = "0.0"
            events.at[idx, "surprise_pct"] = "0.0"

        logger.info(f"[{row['event_id']}] release={rd} obs_month={obs_month} "
                    f"actual: {old_actual} → {new_actual}")
        updated += 1

    if skipped:
        logger.warning(f"スキップ: {len(skipped)}件")
        for eid, reason in skipped:
            logger.warning(f"  {eid}: {reason}")

    logger.info(f"変換対象: {updated}件 / スキップ: {len(skipped)}件")

    if dry_run:
        logger.info("[dry-run] 書き込みは行いません。")
        return updated

    backup_path = f"{EVENTS_PATH}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(EVENTS_PATH, backup_path)
    logger.info(f"バックアップ作成: {backup_path}")

    save_events(events)
    logger.info(f"書き込み完了: {EVENTS_PATH}")
    return updated


def main():
    p = argparse.ArgumentParser(description="NFP既存履歴の水準→前月比一括変換")
    p.add_argument("--dry-run", action="store_true", help="変換結果を表示するのみで書き込まない")
    args = p.parse_args()
    backfill(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
