"""
common/market_data/fetcher.py

yfinance統合層のデータ取得モジュール（BACKLOG [[MARKETDATA-LAYER-CONSTRUCTION-1]]、
2026-08-08確定の設計に基づく実装）。3つの独立したサブレイヤーごとに
取得関数を提供する:

    fetch_daily_prices(symbols)      日次価格層   → daily/{SYMBOL}.json
    fetch_weekly_attributes(symbols) 週次準静的属性層 → attributes/{SYMBOL}.json
    fetch_analyst_events(symbols)    イベント履歴層  → analyst_history/{SYMBOL}.json

いずれも保存前に恒等式検証（validate_price_record / validate_attributes_record）
を行うが、検証失敗時も保存は拒否しない（_validation_warningsフィールドに
記録した上で保存継続。common/sec_data/parser.py の fy_collision_log.json と
同じ「検知のみ・自動修正なし」方針を踏襲、日次連続性に穴を作らないため）。
検証結果は毎回 {SYMBOL}/market_data_violations_log.json に書き込む（0件でも
書き込む、fy_collision_log.json型の化石ファイル対策）。

daily/・attributes/・analyst_history/・violations_logの書き込みは全て
tempfile→os.replace()でアトミック化する（BACKLOG確定事項3）。

本番消費者切替（BACKLOG着手順序4）が開始しており、
src/value/tanuki_valuation/beta_fetcher.py がcommon.market_data.reader
経由で本モジュールの生成データ（attributes/）に依存する最初の消費者と
なった（2026-08-11）。残り7本番消費者・2診断ツール・2周辺ツールの切替は
順次対応する。
"""

import io
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import yaml
import yfinance as yf
import pandas_market_calendars as mcal

# ── パス設定 ──────────────────────────────────────────────
MARKET_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(MARKET_DATA_DIR))  # common/market_data -> common -> リポジトリルート
_MONITOR_TICKERS_YAML = os.path.join(_REPO_ROOT, "config", "monitor_tickers.yaml")
_SP500_CACHE_FILENAME = "_sp500_constituents_cache.json"

# common.yfinance_utils.safe_yf_ticker()（リトライ2回・待機3秒）経由で
# .info を呼ぶための準備（src/value/tanuki_valuation/beta_fetcher.pyと同型
# パターン）。本ファイルはGitHub Actions上で`python common/market_data/
# fetcher.py ...`のようにスクリプトとして直接実行されるため、リポジトリ
# ルートがsys.pathに乗っていないと`from common.yfinance_utils import ...`
# が失敗する（相対importは`python -m`経由でない直接実行では使えないため
# 採用しない。実測確認済み）。
_repo_str = str(_REPO_ROOT)
if _repo_str not in sys.path:
    sys.path.insert(0, _repo_str)

try:
    from common.yfinance_utils import safe_yf_ticker as _safe_yf_ticker
    _USE_SAFE_YF = True
except ImportError:
    _USE_SAFE_YF = False

# 指数/ETF/商品ユニバース（既存消費者12ファイルの実使用実態から抽出、
# BACKLOG [[MARKETDATA-LAYER-CONSTRUCTION-1]]投資調査参照）。網羅リストでは
# なく、本番消費者切替時（着手順序3・4）に個別ファイルの参照銘柄と突合して
# 追加検討する前提の初期セット。
INDEX_ETF_COMMODITY_SYMBOLS: List[str] = [
    # 指数（Market Pulse: collect_and_send.py）
    "^GSPC", "^IXIC", "^DJI", "^NYA", "^RUT", "^VIX", "^VIX9D", "^TNX", "^N225",
    # ETF（Market Pulse: collect_and_send.py・breadth_calculator.py）
    "SPY", "QQQ", "GLD", "TLT", "HYG",
    # 商品先物（Market Pulse: collect_and_send.py）
    "CL=F", "GC=F",
]


# ── 汎用ユーティリティ ────────────────────────────────────

def _resolve_base_dir(base_dir: Optional[str]) -> str:
    return base_dir if base_dir is not None else MARKET_DATA_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe_symbols(symbols: Optional[List[str]]) -> List[str]:
    seen = set()
    result: List[str] = []
    for s in symbols or []:
        s = str(s).strip().upper()
        if not s or s in seen:
            continue
        seen.add(s)
        result.append(s)
    return result


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def _to_int(value: Any) -> Optional[int]:
    f = _to_float(value)
    return int(f) if f is not None else None


def _to_str_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def _atomic_write_json(path: str, payload: Any) -> None:
    """tempfile→os.replace()でアトミック書き込みする（BACKLOG確定事項3）。

    書き込み中にプロセスが中断しても、os.replace()は同一ファイルシステム内
    でアトミックなrenameのため、既存ファイルは最後まで完了した版のまま残る
    （中断時に破損した中間状態が観測されることはない）。
    """
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def _load_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return json.loads(json.dumps(default))
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"   [WARN] {path} 読み込み失敗（初期値で継続）: {e}")
        return json.loads(json.dumps(default))


# ── NYSE営業日カレンダー（BACKLOG確定事項1） ──────────────

_NYSE_CALENDAR = None


def get_nyse_calendar():
    """pandas_market_calendarsのNYSEカレンダーを返す（プロセス内でキャッシュ）。"""
    global _NYSE_CALENDAR
    if _NYSE_CALENDAR is None:
        _NYSE_CALENDAR = mcal.get_calendar("NYSE")
    return _NYSE_CALENDAR


def is_trading_day(day: Any, calendar=None) -> bool:
    """指定日がNYSE営業日かを判定する。

    day: date/datetime または 'YYYY-MM-DD' 文字列。
    層またぎ再計算の禁止（BACKLOG確定事項4）によりreader.py側の連続性
    保証（get_price_series()）とは別の軽量な単日判定ユーティリティ。
    """
    cal = calendar or get_nyse_calendar()
    day_str = day.isoformat() if hasattr(day, "isoformat") else str(day)
    valid_days = cal.valid_days(start_date=day_str, end_date=day_str)
    return len(valid_days) > 0


# ── 保存前検証（BACKLOG確定事項5） ────────────────────────

def validate_price_record(record: Dict[str, Any]) -> List[str]:
    """日次価格レコードの恒等式検証。検証失敗時も保存は拒否しない
    （呼び出し側が_validation_warningsとして記録した上で保存する）。

    検証項目:
        - open/high/low/close（存在するもののみ） > 0
        - volume > 0
        - high >= close >= low
        - fifty_two_week_high >= fifty_two_week_low（両方存在する場合のみ。
          fetch_daily_prices()は.history()/yf.download()のみを使うため
          通常はこのフィールド自体が存在しない。将来的にyfinance側の値を
          付与するケースに備えた任意項目）
    """
    warnings: List[str] = []

    for field in ("open", "high", "low", "close"):
        if field not in record:
            continue
        value = record.get(field)
        if value is None or not (isinstance(value, (int, float)) and value > 0):
            warnings.append(f"{field} must be > 0 (got {value!r})")

    if "volume" in record:
        volume = record.get("volume")
        if volume is None or not (isinstance(volume, (int, float)) and volume > 0):
            warnings.append(f"volume must be > 0 (got {volume!r})")

    high, close, low = record.get("high"), record.get("close"), record.get("low")
    if high is not None and close is not None and low is not None:
        if not (high >= close >= low):
            warnings.append(
                f"expected high >= close >= low (got high={high}, close={close}, low={low})"
            )

    wk_high = record.get("fifty_two_week_high")
    wk_low = record.get("fifty_two_week_low")
    if wk_high is not None and wk_low is not None:
        if not (wk_high >= wk_low):
            warnings.append(
                f"expected fifty_two_week_high >= fifty_two_week_low "
                f"(got high={wk_high}, low={wk_low})"
            )

    return warnings


def validate_attributes_record(record: Dict[str, Any]) -> List[str]:
    """週次属性レコードの恒等式検証（時価総額 ≈ 株価×発行済株式数）。

    許容範囲: 相対2%または絶対$1,000,000のいずれか大きい方
    （common/sec_data/parser.py の _BS_IDENTITY_TOL_REL=0.02 を踏襲し、
    小型株向けに絶対フロアを追加。BACKLOG確定事項5）。
    current_price/shares_outstanding/market_cap のいずれかが欠落している
    場合（指数等）は検証をスキップする。
    """
    warnings: List[str] = []
    price = record.get("current_price")
    shares = record.get("shares_outstanding")
    reported_mcap = record.get("market_cap")

    if price is not None and shares is not None and reported_mcap is not None:
        computed_mcap = price * shares
        tolerance = max(reported_mcap * 0.02, 1_000_000)
        if abs(computed_mcap - reported_mcap) > tolerance:
            warnings.append(
                f"market_cap mismatch: reported={reported_mcap}, "
                f"computed(price*shares)={computed_mcap}, tolerance={tolerance}"
            )

    return warnings


# ── 検証結果ログ（fy_collision_log.json型） ────────────────

def _violations_log_path(symbol: str, base_dir: str) -> str:
    return os.path.join(base_dir, symbol, "market_data_violations_log.json")


def _write_violations_section(symbol: str, section_key: str, section_value: Dict[str, Any],
                               base_dir: str) -> None:
    """market_data_violations_log.json の指定セクションのみを更新する。

    daily_price_validation（日次）とattributes_validation（週次）は独立した
    頻度で実行されるため、片方の実行が他方の最新記録を上書きしないよう
    セクション単位でread-modify-writeする。0件でも毎回書き込む
    （fy_collision_log.json型の化石ファイル対策）。
    """
    path = _violations_log_path(symbol, base_dir)
    payload = _load_json(path, default={"ticker": symbol})
    payload["ticker"] = symbol
    payload[section_key] = section_value
    _atomic_write_json(path, payload)


# ── 日次価格層 ────────────────────────────────────────────

def _download_daily_bars(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """yf.download()で複数銘柄の直近日足を一括取得し、銘柄ごとの最新1営業日分
    のOHLCVをdictで返す（取得できなかった銘柄はキーごと欠落する）。
    """
    if not symbols:
        return {}
    try:
        raw = yf.download(symbols, period="5d", group_by="ticker",
                           auto_adjust=False, progress=False, threads=True)
    except Exception as e:
        print(f"   [WARN] yf.download失敗: {e}")
        return {}
    if raw is None or raw.empty:
        return {}

    results: Dict[str, Dict[str, Any]] = {}
    for symbol in symbols:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                if symbol not in raw.columns.get_level_values(0):
                    print(f"   [{symbol}] 日次データが取得結果に含まれない（スキップ）")
                    continue
                sub = raw[symbol]
            else:
                sub = raw
            sub = sub.dropna(how="all")
            if sub.empty:
                print(f"   [{symbol}] 日次データが空（スキップ）")
                continue
            last_row = sub.iloc[-1]
            last_date = sub.index[-1]
            results[symbol] = {
                "date": last_date.strftime("%Y-%m-%d"),
                "open": _to_float(last_row.get("Open")),
                "high": _to_float(last_row.get("High")),
                "low": _to_float(last_row.get("Low")),
                "close": _to_float(last_row.get("Close")),
                "volume": _to_int(last_row.get("Volume")),
            }
        except Exception as e:
            print(f"   [{symbol}] 日次データ解析エラー: {e}")
    return results


def _append_daily_record(symbol: str, record: Dict[str, Any], base_dir: str) -> None:
    """daily/{symbol}.json に1営業日分のレコードを追記する（同一dateは上書き、
    記録キーは日付ベースで重複排除するリポジトリ規約に準拠）。
    """
    path = os.path.join(base_dir, "daily", f"{symbol}.json")
    payload = _load_json(path, default={"symbol": symbol, "records": []})
    records = [r for r in payload.get("records", []) if r.get("date") != record["date"]]
    records.append(record)
    records.sort(key=lambda r: r.get("date", ""))
    payload["symbol"] = symbol
    payload["records"] = records
    _atomic_write_json(path, payload)


def fetch_daily_prices(symbols: List[str], base_dir: Optional[str] = None) -> None:
    """日次価格層を取得・保存する。

    yf.download()で対象銘柄を一括取得し、銘柄ごとに直近1営業日分のOHLCVを
    daily/{SYMBOL}.jsonへ追記する。保存前にvalidate_price_record()で検証し、
    失敗しても保存は拒否しない（_validation_warningsに記録の上で保存継続）。
    検証結果は{SYMBOL}/market_data_violations_log.jsonへ毎回書き込む。

    本番バッチではsymbolsにget_default_symbol_universe()（S&P500構成銘柄＋
    監視銘柄＋指数/ETF/商品の和集合）を渡す想定。
    """
    base = _resolve_base_dir(base_dir)
    target_symbols = _dedupe_symbols(symbols)
    if not target_symbols:
        return

    bars = _download_daily_bars(target_symbols)
    for symbol in target_symbols:
        bar = bars.get(symbol)
        if bar is None:
            print(f"   [{symbol}] 日次データ取得失敗（スキップ）")
            continue

        record = dict(bar)
        record_warnings = validate_price_record(record)
        record["_validation_warnings"] = record_warnings

        _append_daily_record(symbol, record, base_dir=base)
        _write_violations_section(
            symbol, "daily_price_validation",
            {"checked_at": _now_iso(), "date": record["date"], "warnings": record_warnings},
            base_dir=base,
        )
        if record_warnings:
            print(f"   [{symbol}] 保存前検証で{len(record_warnings)}件の警告を検知（保存は継続）")


# ── 週次準静的属性層 ──────────────────────────────────────

def fetch_weekly_attributes(symbols: List[str], base_dir: Optional[str] = None) -> None:
    """週次準静的属性層を取得・保存する。

    銘柄ごとに.infoを1回呼び出し、PER/PEG/PSR/EV_EBITDA/β/セクター/業種/
    配当/株式数/Forward EPS/アナリスト目標株価コンセンサス/totalDebtを抽出し、
    fetched_at（ISO8601 UTC）を付与してattributes/{SYMBOL}.jsonへ保存する。
    保存前にvalidate_attributes_record()で時価総額恒等式を検証するが、
    失敗しても保存は拒否しない。twoHundredDayAverageは保存しない
    （BACKLOG確定事項7、get_ma_deviation()がprice_seriesから都度計算する
    設計のため）。

    .info呼び出しはcommon.yfinance_utils.safe_yf_ticker()（リトライ2回・
    待機3秒、beta_fetcher.py::fetch_yfinance_beta()と同型）経由で行う
    （import失敗時は無リトライの直接呼び出しにフォールバック）。全銘柄
    バッチ実行時の一時的なネットワーク不調による取りこぼしを減らすため。
    """
    base = _resolve_base_dir(base_dir)
    target_symbols = _dedupe_symbols(symbols)

    for symbol in target_symbols:
        if _USE_SAFE_YF:
            t = _safe_yf_ticker(symbol)
            if t is None:
                print(f"   [{symbol}] .info取得失敗（リトライ後もNone、スキップ）")
                continue
            try:
                info = t.info
            except Exception as e:
                print(f"   [{symbol}] .info取得失敗（スキップ）: {e}")
                continue
        else:
            try:
                info = yf.Ticker(symbol).info
            except Exception as e:
                print(f"   [{symbol}] .info取得失敗（スキップ）: {e}")
                continue
        if not info:
            print(f"   [{symbol}] .info が空（スキップ）")
            continue

        fetched_at = _now_iso()
        record: Dict[str, Any] = {
            "symbol": symbol,
            "fetched_at": fetched_at,
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "peg_ratio": info.get("trailingPegRatio") or info.get("pegRatio"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "beta": info.get("beta"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "dividend_yield": info.get("dividendYield"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "forward_eps": info.get("forwardEps"),
            "target_mean_price": info.get("targetMeanPrice"),
            "total_debt": info.get("totalDebt"),
        }

        record_warnings = validate_attributes_record(record)
        record["_validation_warnings"] = record_warnings

        path = os.path.join(base, "attributes", f"{symbol}.json")
        _atomic_write_json(path, record)
        _write_violations_section(
            symbol, "attributes_validation",
            {"checked_at": fetched_at, "warnings": record_warnings},
            base_dir=base,
        )
        if record_warnings:
            print(f"   [{symbol}] 保存前検証で{len(record_warnings)}件の警告を検知（保存は継続）")


# ── イベント履歴層 ────────────────────────────────────────

def _event_dedup_key(event: Dict[str, Any]):
    return (
        event.get("date"), event.get("firm"),
        event.get("to_grade"), event.get("from_grade"), event.get("action"),
    )


def fetch_analyst_events(symbols: List[str], base_dir: Optional[str] = None) -> None:
    """イベント履歴層を取得・保存する。

    銘柄ごとにupgrades_downgradesを取得し、analyst_history/{SYMBOL}.jsonへ
    追記型で保存する。(date, firm, to_grade, from_grade, action)をキーに
    重複イベントを排除する（同一イベントの再取得で無限増殖しない）。
    """
    base = _resolve_base_dir(base_dir)
    target_symbols = _dedupe_symbols(symbols)

    for symbol in target_symbols:
        try:
            df = yf.Ticker(symbol).upgrades_downgrades
        except Exception as e:
            print(f"   [{symbol}] upgrades_downgrades取得失敗（スキップ）: {e}")
            continue

        new_events: List[Dict[str, Any]] = []
        if df is not None and not df.empty:
            for grade_date, row in df.iterrows():
                date_str = grade_date.strftime("%Y-%m-%d") if hasattr(grade_date, "strftime") else str(grade_date)
                new_events.append({
                    "date": date_str,
                    "firm": _to_str_or_none(row.get("Firm")),
                    "to_grade": _to_str_or_none(row.get("ToGrade")),
                    "from_grade": _to_str_or_none(row.get("FromGrade")),
                    "action": _to_str_or_none(row.get("Action")),
                    "price_target_action": _to_str_or_none(row.get("priceTargetAction")),
                    "current_price_target": _to_float(row.get("currentPriceTarget")),
                    "prior_price_target": _to_float(row.get("priorPriceTarget")),
                })

        path = os.path.join(base, "analyst_history", f"{symbol}.json")
        payload = _load_json(path, default={"symbol": symbol, "events": []})
        merged = {_event_dedup_key(e): e for e in payload.get("events", [])}
        for e in new_events:
            merged[_event_dedup_key(e)] = e
        events = sorted(merged.values(), key=lambda e: e.get("date", ""), reverse=True)

        payload["symbol"] = symbol
        payload["events"] = events
        _atomic_write_json(path, payload)


# ── 銘柄ユニバース構築（S&P500 + 監視銘柄 + 指数/ETF/商品） ──

def get_monitor_tickers(config_path: Optional[str] = None) -> List[str]:
    """config/monitor_tickers.yaml の監視銘柄リストを返す。"""
    path = config_path or _MONITOR_TICKERS_YAML
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return _dedupe_symbols(data.get("tickers", []))
    except Exception as e:
        print(f"   [WARN] monitor_tickers.yaml 読み込み失敗: {e}")
        return []


def get_sp500_constituents(base_dir: Optional[str] = None, max_age_days: int = 7) -> List[str]:
    """S&P500構成銘柄リストを取得する（Wikipedia→GitHub CSVフォールバック、
    {max_age_days}日キャッシュ）。

    src/market/market_pulse/breadth_calculator.py::get_sp500_tickers() と
    同じ取得ロジックだが、market_dataは一次データ層として他レイヤーの
    consumerスクリプトに依存すべきではないため独立実装として保持する
    （意図的な重複であり、DRY違反の見落としではない）。
    """
    base = _resolve_base_dir(base_dir)
    cache_path = os.path.join(base, _SP500_CACHE_FILENAME)

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            fetched_at = datetime.fromisoformat(cache["fetched_at"])
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - fetched_at).days
            if age_days < max_age_days and cache.get("tickers"):
                return cache["tickers"]
        except Exception:
            pass

    tickers: Optional[List[str]] = None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MarketDataFetcher/1.0)"}
        resp = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers=headers, timeout=30,
        )
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
        df = tables[0]
        tickers = [t.strip() for t in df["Symbol"].str.replace(".", "-", regex=False).tolist() if t.strip()]
    except Exception as e:
        print(f"   [WARN] S&P500構成銘柄のWikipedia取得失敗: {e}")

    if not tickers:
        try:
            csv_url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
            resp = requests.get(csv_url, timeout=30)
            resp.raise_for_status()
            df = pd.read_csv(io.StringIO(resp.text))
            tickers = [t.strip() for t in df["Symbol"].str.replace(".", "-", regex=False).tolist() if t.strip()]
        except Exception as e:
            print(f"   [WARN] S&P500構成銘柄のGitHub CSV取得失敗: {e}")

    if tickers and len(tickers) >= 400:
        _atomic_write_json(cache_path, {
            "fetched_at": _now_iso(), "count": len(tickers), "tickers": tickers,
        })
        return tickers

    # 両ソースとも失敗した場合、期限切れキャッシュがあればそれを返す
    # （完全な空リストで日次バッチを回すよりは安全）
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f).get("tickers", [])
        except Exception:
            pass
    return []


def get_default_symbol_universe(base_dir: Optional[str] = None) -> List[str]:
    """S&P500構成銘柄＋監視銘柄＋指数/ETF/商品の和集合を返す
    （BACKLOG [[MARKETDATA-LAYER-CONSTRUCTION-1]]設計。fetch_daily_prices()の
    本番バッチ実行が対象とすべき銘柄ユニバース）。
    """
    universe: List[str] = []
    universe.extend(get_sp500_constituents(base_dir=base_dir))
    universe.extend(get_monitor_tickers())
    universe.extend(INDEX_ETF_COMMODITY_SYMBOLS)
    return _dedupe_symbols(universe)


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(description="common/market_data 取得CLI")
    arg_parser.add_argument("symbols", nargs="*", help="対象銘柄（省略時はデフォルトユニバース）")
    arg_parser.add_argument("--layer", choices=["daily", "attributes", "analyst", "all"], default="all")
    args = arg_parser.parse_args()

    symbols_arg = _dedupe_symbols(args.symbols) if args.symbols else get_default_symbol_universe()
    print(f"対象銘柄数: {len(symbols_arg)}")

    if args.layer in ("daily", "all"):
        fetch_daily_prices(symbols_arg)
    if args.layer in ("attributes", "all"):
        fetch_weekly_attributes(symbols_arg)
    if args.layer in ("analyst", "all"):
        fetch_analyst_events(symbols_arg)
