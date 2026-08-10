"""
common/market_data — yfinance統合層（新DB構築プロジェクト フェーズ1）

BACKLOG [[MARKETDATA-LAYER-CONSTRUCTION-1]] の設計に基づく一次データ層。
common/sec_data/ と同型構成（fetcher.py がネットワーク取得・保存前検証・
保存を担当、reader.py が読み取りAPIを提供）。

保存構造:
    common/market_data/
        daily/{SYMBOL}.json            日次価格層（.history()/yf.download()由来）
        attributes/{SYMBOL}.json       週次準静的属性層（.info由来のスナップショット）
        analyst_history/{SYMBOL}.json  イベント履歴層（upgrades_downgrades由来）
        {SYMBOL}/market_data_violations_log.json  保存前検証の結果ログ

reader.py は未実装（次ステップ）。現時点の消費者はまだ存在しない
グリーンフィールドモジュールであり、既存システムへの依存・影響はない。
"""
