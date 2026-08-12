"""
common/macro_data — FRED統合層（新DB構築プロジェクト フェーズ1）

BACKLOG [[MACRODATA-LAYER-CONSTRUCTION-1]] の設計に基づく一次データ層。
common/market_data/ と同型構成（fetcher.py がネットワーク取得・保存前
検証・保存を担当、reader.py が読み取りAPIを提供）。

保存構造:
    common/macro_data/
        series/{SERIES_ID}.json          系列単位の時系列ストア
        series_meta.json                  系列単位のメタ情報（fred_release_id等）
        macro_data_violations_log.json    保存前検証の結果ログ

【スコープ（2026-08-12時点）】
fetcher.py/reader.py本体・`.github/workflows/Macro_Data_Update.yml`
（定期実行cron・workflow_dispatch）まで構築済み。`05_main.py`（MACRO
PULSE）・`collect_and_send.py`（Market Pulse）側の本番消費者切替
（重複3系列BAMLH0A0HYM2/T10Y2Y/VIXCLSの解消を含む）・過去データの
一括投入（フェーズ2）はいずれも次段階で扱う。現時点でこのモジュールを
参照する本番消費者は存在しない（グリーンフィールド実装、定期実行のみ
稼働）。

使用例:
    from common.macro_data import reader

    latest = reader.get_latest("BAMLH0A0HYM2")
    series = reader.get_series("T10Y2Y", start="2026-01-01")
    val_on = reader.get_value_as_of("PAYEMS", "2026-07-15")
"""

from . import fetcher
from . import reader

__all__ = ["fetcher", "reader"]
