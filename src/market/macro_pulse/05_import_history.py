#!/usr/bin/env python3
"""
MACRO PULSE v6.0 — 過去データ一括投入スクリプト
================================================
使用方法:
  python 05_import_history.py fred --from 2001-01-01
  python 05_import_history.py csv --source <CSV_FILE> --indicator <INDICATOR_NAME>
  python 05_import_history.py liquidity --from 2023-01-01

機能:
  1. fred: common/macro_data/series/（common.macro_data.reader経由）
     から過去データを一括取得して 05_events.csv に投入
  2. csv: tradingeconomics 等から手動DLした CSV を変換して投入
  3. liquidity: common/macro_data/series/ から過去の流動性データを
     一括取得して 05_liquidity.csv にバックフィル

対応指標（FRED自動、05_main.py::INDICATOR_CONFIGを単一の正として参照。
MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1対応、2026-08-15、独自辞書は
廃止済み）:
  Philadelphia Fed Manufacturing, Chicago Fed National Activity,
  NFP, Initial Claims 4W MA, Michigan Inflation 1Y, Michigan Inflation 5Y,
  Michigan Consumer Sentiment, Building Permits,
  Sahm Rule Recession Indicator,
  Yield Curve 10Y-2Y, HY Spread, VIX

手入力指標（FREDに月次公式データなし）:
  ※ ISM PMIは8指標体制から除外済み（スコア計算対象外）
  → csv サブコマンド（--source）でCSVを渡す（各指標公式サイトまたはFREDから手動DL）

入力CSVフォーマット（手入力指標用）:
  date,actual,consensus
  2024-01-02,47.4,47.0
  2024-02-01,49.1,49.5
  ...

注意:
  - 既存 event_id は上書きしない（--overwrite フラグで上書き可）
  - 金融環境（regime/ff_rate/yc_10y2y/hy_spread/vix）はcommon.macro_
    data.readerのローカルJSONから履歴日付ごとに取得する
  - sp500_t0〜t20 は後から --fill-returns で補完
  - fred/liquidityサブコマンドはFRED APIを直接呼ばず、common/macro_
    data/fetcher.pyが定期取得ワークフローで蓄積済みのローカルデータ
    （series/{ID}.json）のみを参照する。対象系列が未蓄積の場合は
    common/macro_data/側の取得を先に完了させること
"""

import os, sys, json, logging, argparse
from datetime import datetime, timedelta, date

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# 05_main.py と同じパス・定数を参照
sys.path.insert(0, os.path.dirname(__file__))

import importlib.util, pathlib

_main_path = pathlib.Path(__file__).parent / "05_main.py"
_spec = importlib.util.spec_from_file_location("main05", _main_path)
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)

# 出力先は _m からそのまま継承（既に docs/market-monitor/macro-pulse/data/ に変更済み）
EVENTS_PATH      = _m.EVENTS_PATH
SCHEDULE_PATH    = _m.SCHEDULE_PATH
FED_CONTEXT_PATH = _m.FED_CONTEXT_PATH
EVENTS_COLUMNS   = _m.EVENTS_COLUMNS
INDICATOR_CONFIG = _m.INDICATOR_CONFIG

make_event_id        = _m.make_event_id
load_events          = _m.load_events
save_events          = _m.save_events
fred_latest          = _m.fred_latest
get_ff_current       = _m.get_ff_current
_fmt                 = _m._fmt
_safe_float          = _m._safe_float
LIQUIDITY_PATH       = _m.LIQUIDITY_PATH
LIQUIDITY_COLUMNS    = _m.LIQUIDITY_COLUMNS
update_liquidity_csv = _m.update_liquidity_csv

# common/macro_data - MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1対応
# （2026-08-15）: 旧`get_fred()`（05_main.pyがMACRODATA-LAYER-
# CONSTRUCTION-1実装時〈2026-08-12〉に削除済み）への依存を撤去し、
# `_m`（05_main.py）が既に確立済みのHAS_MACRO_DATAガード・_md_reader
# をそのまま再利用する（このファイルは`_spec.loader.exec_module(_m)`で
# 05_main.pyを完全実行済みのため、sys.path解決を再度行う必要はない）。
HAS_MACRO_DATA = _m.HAS_MACRO_DATA
_md_reader     = _m._md_reader

# ─────────────────────────────────────────────────────────────────
#  金融環境コンテキスト（common.macro_data.reader経由、ローカルJSON
#  読み取りのみのためAPIキャッシュは不要——旧_CTX_CACHE/_load_ctx_cache()
#  はfredapi直接呼び出し時代のAPIコール削減策だったが、reader.get_
#  value_as_of()はファイル読み取りのみで完結するため毎回呼び出して
#  も軽量。get_value_as_of()のdocstring自身が本関数の旧実装
#  （_lookup_ctxの「target_date以前・lookback日以内の直近値」
#  パターン）を踏襲した設計である旨を明記している）
# ─────────────────────────────────────────────────────────────────
def _lookup_ctx(series_id: str, target_date):
    if not HAS_MACRO_DATA:
        return None
    rec = _md_reader.get_value_as_of(series_id, target_date, lookback_days=45)
    return rec["value"] if rec else None

def get_historical_context(target_date) -> dict:
    """common.macro_data.reader経由で指定日付の金融環境スナップショットを返す"""
    ctx = {"regime": "", "ff_rate": "", "yc_10y2y": "", "hy_spread": "", "vix": "", "cuts_implied": ""}
    yc    = _lookup_ctx("T10Y2Y",       target_date)
    hy    = _lookup_ctx("BAMLH0A0HYM2", target_date)
    vx    = _lookup_ctx("VIXCLS",       target_date)
    ff_hi = _lookup_ctx("DFEDTARU",     target_date)
    ff_lo = _lookup_ctx("DFEDTARL",     target_date)
    if ff_hi and ff_lo: ctx["ff_rate"]  = str(round((ff_hi + ff_lo) / 2, 4))
    if yc: ctx["yc_10y2y"]  = str(round(yc, 4))
    if hy: ctx["hy_spread"]  = str(round(hy, 4))
    if vx: ctx["vix"]        = str(round(vx, 2))
    return ctx

# ─────────────────────────────────────────────────────────────────
#  FRED 一括取得（common.macro_data.reader経由、ローカルJSON読み取り）
#  MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1対応（2026-08-15）:
#  独自FRED_INDICATORS辞書（INDICATOR_CONFIGと乖離していた）を廃止し、
#  05_main.py::INDICATOR_CONFIGを唯一の正とする。common/macro_data/
#  fetcher.pyが定期取得ワークフローで既に深い履歴を蓄積済みのため、
#  本関数はFRED APIを直接呼ばずcommon/macro_data/series/{ID}.jsonを
#  読み取るだけで完結する（外部API呼び出し・レート制限対策は不要）。
# ─────────────────────────────────────────────────────────────────
def import_from_fred(from_date: str, to_date: str, overwrite: bool = False,
                     indicators: list = None):
    if not HAS_MACRO_DATA:
        logger.error("common.macro_data.reader が利用できません（import失敗）。")
        sys.exit(1)

    events    = load_events()
    existing  = set(events["event_id"].tolist()) if not events.empty else set()
    new_rows  = []

    target_indicators = indicators or list(INDICATOR_CONFIG.keys())

    for ind_name in target_indicators:
        fred_id = INDICATOR_CONFIG.get(ind_name, {}).get("fred_id")
        if not fred_id:
            logger.warning(f"[{ind_name}] FRED IDなし（INDICATOR_CONFIG未登録）。スキップ。")
            continue

        logger.info(f"[{ind_name}] FRED ID={fred_id} をcommon/macro_data/から取得中...")
        try:
            records = _md_reader.get_series(fred_id, start=from_date, end=to_date)
            if not records:
                logger.warning(f"[{ind_name}] データなし（common/macro_data/series/{fred_id}.json未生成の可能性）")
                continue

            s = pd.Series({pd.Timestamp(r["as_of"]): r["value"] for r in records}).sort_index()

            if ind_name == "NFP":
                # MACRO-NFP-1: PAYEMSは雇用者数の「水準」のため、
                # 前月からの増減（人）に変換してから格納する（05_main.pyのfetch_event_rowと揃える）
                s = (s.diff() * 1000).dropna()

            for obs_date, val in s.items():
                rd     = obs_date.date()
                rd_str = rd.strftime("%Y-%m-%d")
                eid    = make_event_id(ind_name, rd)

                if eid in existing and not overwrite:
                    continue

                ctx = get_historical_context(rd)
                row = {col: "" for col in EVENTS_COLUMNS}
                row.update({
                    "event_id":      eid,
                    "indicator":     ind_name,
                    "release_date":  rd_str,
                    "actual":        str(round(float(val), 4)),
                    "consensus":     "",
                    "surprise":      "",
                    "surprise_pct":  "",
                    "regime":        ctx["regime"],
                    "ff_rate":       ctx["ff_rate"],
                    "yc_10y2y":      ctx["yc_10y2y"],
                    "hy_spread":     ctx["hy_spread"],
                    "vix":           ctx["vix"],
                    "cuts_implied":  ctx["cuts_implied"],
                    "forecast_source": "FRED",
                    "data_source":   "FRED",
                    "updated_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                new_rows.append(row)

            logger.info(f"[{ind_name}] {len(s)} 件取得完了")

        except Exception as e:
            logger.error(f"[{ind_name}] エラー: {e}")

    if not new_rows:
        logger.info("新規データなし。終了。")
        return

    new_df  = pd.DataFrame(new_rows, columns=EVENTS_COLUMNS)
    key_new = set(new_df["event_id"])
    existing_filtered = events[~events["event_id"].isin(key_new)]
    combined = pd.concat([existing_filtered, new_df], ignore_index=True)
    save_events(combined)
    logger.info(f"インポート完了: {len(new_rows)} 行追加 → {EVENTS_PATH}")

# ─────────────────────────────────────────────────────────────────
#  手動 CSV 投入
# ─────────────────────────────────────────────────────────────────
def import_from_csv(source_path: str, indicator: str, overwrite: bool = False):
    if not os.path.exists(source_path):
        logger.error(f"ファイルが見つかりません: {source_path}")
        sys.exit(1)

    try:
        src_df = pd.read_csv(source_path, dtype=str).fillna("")
    except Exception as e:
        logger.error(f"CSV読み込みエラー: {e}")
        sys.exit(1)

    src_df.columns = [c.strip().lower() for c in src_df.columns]

    required = ["date", "actual"]
    missing  = [c for c in required if c not in src_df.columns]
    if missing:
        logger.error(f"必須列なし: {missing}。列名確認: {list(src_df.columns)}")
        sys.exit(1)

    events = load_events()
    existing = set(events["event_id"].tolist()) if not events.empty else set()
    new_rows = []
    skipped  = 0

    for _, src_row in src_df.iterrows():
        date_raw = src_row["date"].strip()
        rd = None
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d/%m/%Y"]:
            try:
                rd = datetime.strptime(date_raw, fmt).date()
                break
            except ValueError:
                continue
        if rd is None:
            logger.warning(f"日付パース失敗: {date_raw} → スキップ")
            skipped += 1
            continue

        try:
            actual_val = float(src_row["actual"].replace(",", ""))
        except (ValueError, AttributeError):
            logger.warning(f"実際値パース失敗: {src_row['actual']} ({rd}) → スキップ")
            skipped += 1
            continue

        eid = make_event_id(indicator, rd)
        if eid in existing and not overwrite:
            skipped += 1
            continue

        consensus_val = None
        surprise      = None
        surprise_pct  = None
        if "consensus" in src_row and src_row["consensus"].strip():
            try:
                consensus_val = float(src_row["consensus"].replace(",", ""))
                surprise      = round(actual_val - consensus_val, 4)
                surprise_pct  = round(surprise / abs(consensus_val) * 100, 4) if consensus_val != 0 else 0.0
            except (ValueError, AttributeError):
                pass

        ctx = get_historical_context(rd) if HAS_MACRO_DATA else {}
        rd_str = rd.strftime("%Y-%m-%d")

        row = {col: "" for col in EVENTS_COLUMNS}
        row.update({
            "event_id":       eid,
            "indicator":      indicator,
            "release_date":   rd_str,
            "actual":         str(actual_val),
            "consensus":      str(consensus_val) if consensus_val is not None else "",
            "surprise":       str(surprise)      if surprise is not None else "",
            "surprise_pct":   str(surprise_pct)  if surprise_pct is not None else "",
            "regime":         ctx.get("regime", ""),
            "ff_rate":        ctx.get("ff_rate", ""),
            "yc_10y2y":       ctx.get("yc_10y2y", ""),
            "hy_spread":      ctx.get("hy_spread", ""),
            "vix":            ctx.get("vix", ""),
            "cuts_implied":   ctx.get("cuts_implied", ""),
            "forecast_source": "user_retroactive" if consensus_val is not None else "actual_as_forecast",
            "data_source":    "manual_import",
            "updated_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        new_rows.append(row)

    if not new_rows:
        logger.info(f"新規データなし（スキップ: {skipped}件）。終了。")
        return

    new_df = pd.DataFrame(new_rows, columns=EVENTS_COLUMNS)
    key_new = set(new_df["event_id"])
    existing_filtered = events[~events["event_id"].isin(key_new)] if overwrite else \
                        events[~events["event_id"].isin(key_new)]
    combined = pd.concat([existing_filtered, new_df], ignore_index=True)
    save_events(combined)
    logger.info(f"インポート完了: {len(new_rows)} 行追加、{skipped} 行スキップ → {EVENTS_PATH}")

# ─────────────────────────────────────────────────────────────────
#  流動性CSVバックフィル
# ─────────────────────────────────────────────────────────────────
def backfill_liquidity(from_date: str, to_date: str, overwrite: bool = False) -> None:
    """
    common.macro_data.reader経由で過去の流動性データ（M2/HYスプレッド/
    FRBバランスシート/TGA/RRP）を一括取得して05_liquidity.csvに
    バックフィルする（MACRODATA-IMPORT-HISTORY-CONFIG-DRIFT-1対応、
    2026-08-15、FRED API直接呼び出しから切替）。

    Args:
        from_date: 開始日（YYYY-MM-DD）
        to_date:   終了日（YYYY-MM-DD）
        overwrite: Trueの場合、既存日付も上書き
    """
    import pandas as pd
    from datetime import datetime, timedelta

    if not HAS_MACRO_DATA:
        logger.error("common.macro_data.reader が利用できません（backfill失敗）。")
        return

    start = datetime.strptime(from_date, "%Y-%m-%d").date()
    end   = datetime.strptime(to_date,   "%Y-%m-%d").date()

    # 既存データ読み込み
    existing_dates = set()
    existing_rows  = []
    if pathlib.Path(LIQUIDITY_PATH).exists():
        try:
            df_ex = pd.read_csv(LIQUIDITY_PATH, dtype=str)
            existing_rows  = df_ex.to_dict("records")
            existing_dates = set(df_ex["date"].tolist())
        except Exception:
            pass

    # common/macro_data/series/から一括取得（期間を広めに指定）
    logger.info(f"common/macro_data/データ取得中: {from_date} 〜 {to_date}")
    lookback_start = (start - timedelta(days=90)).strftime("%Y-%m-%d")

    def fetch_series(series_id):
        records = _md_reader.get_series(series_id, start=lookback_start, end=to_date)
        if not records:
            logger.warning(f"  [{series_id}] データなし")
            return None
        return pd.Series({pd.Timestamp(r["as_of"]): r["value"] for r in records}).sort_index()

    s_m2    = fetch_series("M2SL")
    s_hy    = fetch_series("BAMLH0A0HYM2")
    s_walcl = fetch_series("WALCL")
    s_tga   = fetch_series("WTREGEN")
    s_rrp   = fetch_series("RRPONTSYD")

    def latest_val(series, target_date, lookback=90):
        """target_date以前の直近値を返す"""
        if series is None:
            return None
        cutoff = pd.Timestamp(target_date)
        s_before = series[series.index <= cutoff]
        if s_before.empty:
            return None
        # lookback日以内のみ有効
        if (cutoff - s_before.index[-1]).days > lookback:
            return None
        return float(s_before.iloc[-1])

    # 日次でループ（営業日のみ）
    added = skipped = 0
    current = start
    new_rows = []

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        if date_str in existing_dates and not overwrite:
            skipped += 1
            current += timedelta(days=1)
            continue

        m2_val    = latest_val(s_m2,    current, lookback=45)   # M2は月次
        hy_val    = latest_val(s_hy,    current, lookback=7)    # HYは日次
        walcl_val = latest_val(s_walcl, current, lookback=10)   # 週次
        tga_val   = latest_val(s_tga,   current, lookback=10)
        rrp_val   = latest_val(s_rrp,   current, lookback=10)

        # 主要データが全てNullの日はスキップ
        if all(v is None for v in (m2_val, hy_val, walcl_val)):
            current += timedelta(days=1)
            continue

        # NET LIQUIDITY計算
        if walcl_val and tga_val and rrp_val:
            net_liq = round((walcl_val - tga_val - rrp_val) / 1_000_000, 4)
        else:
            net_liq = None

        new_rows.append({
            "date":          date_str,
            "m2":            str(round(m2_val, 4))    if m2_val    is not None else "",
            "hy_spread":     str(round(hy_val, 4))    if hy_val    is not None else "",
            "fed_balance":   str(round(walcl_val, 4)) if walcl_val is not None else "",
            "tga":           str(round(tga_val, 4))   if tga_val   is not None else "",
            "rrp":           str(round(rrp_val, 4))   if rrp_val   is not None else "",
            "net_liquidity": str(net_liq)              if net_liq   is not None else "",
        })
        added += 1
        current += timedelta(days=1)

    if not new_rows:
        logger.info(f"新規データなし（スキップ: {skipped}日）")
        return

    # 既存データとマージして日付順ソート
    if overwrite:
        new_dates = {r["date"] for r in new_rows}
        existing_rows = [r for r in existing_rows if r["date"] not in new_dates]

    all_rows = existing_rows + new_rows
    all_rows.sort(key=lambda r: r["date"])

    # 重複除去（同日は後勝ち）
    seen = {}
    for r in all_rows:
        seen[r["date"]] = r
    all_rows = sorted(seen.values(), key=lambda r: r["date"])

    pathlib.Path(LIQUIDITY_PATH).parent.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame(all_rows, columns=LIQUIDITY_COLUMNS)
    df_out.to_csv(LIQUIDITY_PATH, index=False, encoding="utf-8")
    logger.info(f"バックフィル完了: {added}日追加 / {skipped}日スキップ → {LIQUIDITY_PATH}")


# ─────────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="MACRO PULSE v6.0 — 過去データ一括投入")
    sub = p.add_subparsers(dest="mode", required=True)

    fred_p = sub.add_parser("fred", help="FRED から過去データを一括取得")
    fred_p.add_argument("--from",  dest="from_date", default="2001-01-01", help="開始日 YYYY-MM-DD（デフォルト: 2001-01-01）")
    fred_p.add_argument("--to",    dest="to_date",   default=date.today().strftime("%Y-%m-%d"), help="終了日")
    fred_p.add_argument("--indicators", nargs="*",   help="取得する指標名（省略時は全FRED指標）")
    fred_p.add_argument("--overwrite", action="store_true", help="既存データを上書き")

    csv_p = sub.add_parser("csv", help="手動DLしたCSVを投入")
    csv_p.add_argument("--source",    required=True, help="入力CSVファイルパス")
    csv_p.add_argument("--indicator", required=True, help="指標名（例: 'Michigan Consumer Sentiment'）")
    csv_p.add_argument("--overwrite", action="store_true")

    # liquidity サブコマンド
    liq_p = sub.add_parser("liquidity", help="流動性CSV（05_liquidity.csv）を過去データでバックフィル")
    liq_p.add_argument("--from",      dest="from_date",  default="2023-01-01", help="開始日（デフォルト: 3年前）")
    liq_p.add_argument("--to",        dest="to_date",    default=date.today().strftime("%Y-%m-%d"), help="終了日")
    liq_p.add_argument("--overwrite", action="store_true", help="既存日付も上書き")

    args = p.parse_args()

    if args.mode == "fred":
        import_from_fred(args.from_date, args.to_date, args.overwrite, args.indicators)
    elif args.mode == "csv":
        import_from_csv(args.source, args.indicator, args.overwrite)
    elif args.mode == "liquidity":
        backfill_liquidity(args.from_date, args.to_date, args.overwrite)

if __name__ == "__main__":
    main()
