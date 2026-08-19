#!/usr/bin/env python3
"""
TANUKI TAIL — thesis_utils.py

thesisファイルのスキーマ差（core/satellite）を吸収する共通ユーティリティ。

`quarterly_review_generator.py`（四半期レビュー生成）と`kpi_proposer.py`
（KPI提案生成）の両方がAIプロンプトへ投資テーゼを埋め込む際に必要と
なるため、複製を避けてここに共通化する（2026-08-19④、
`[[TAIL-KPI-PROPOSER-CORE-ONLY-GATE-1]]`対応時に
`quarterly_review_generator.py`から抽出・移動）。
"""

from typing import Any, Dict, Tuple


def thesis_narrative_fields(thesis: Dict[str, Any]) -> Tuple[str, str, str]:
    """thesisのスキーマ差（core: thesis/entry_story/exit_guide、
    satellite: strategy_name/entry_condition/exit_condition/
    holding_period）を吸収し、プロンプトに埋め込む3項目
    （投資テーゼ本文, エントリーストーリー, エグジットの目安）を
    type非依存の文字列として返す。

    **2026-08-19発見・修正**: 本関数導入前は`thesis.get('thesis', ...)`
    等でcoreスキーマの3フィールドを直接読んでいたため、satelliteの
    thesisファイル（strategy_name等の別フィールド名）に対しては全て
    デフォルト値「未設定」が返り、実際にはテーゼが設定されているにも
    かかわらずGrokへのプロンプトが「テーゼ未設定」と表示していた
    （`[[TAIL-COVERAGE-POLICY-UNDECIDED-1]]`のsatellite監視対象拡大に
    伴う実地検証で発見。ADBE・APGEで実際にレビューを生成し、両方とも
    health_score大幅減点・recommendation=EXITという内容破綻を確認して
    修正した）。

    **2026-08-19④**: `kpi_proposer.py::build_kpi_prompt()`にも同型の
    バグが存在することが判明したため、`quarterly_review_generator.py`
    から本モジュールへ抽出し、両方から共通利用する形にした。
    """
    if thesis.get("type") == "satellite":
        strategy = thesis.get("strategy_name") or "未設定"
        holding  = thesis.get("holding_period") or "未設定"
        thesis_text = f"戦略: {strategy}（想定保有期間: {holding}）"
        entry_story = thesis.get("entry_condition") or "未設定"
        exit_guide  = thesis.get("exit_condition") or "未設定"
    else:
        thesis_text = thesis.get("thesis") or "未設定"
        entry_story = thesis.get("entry_story") or "未設定"
        exit_guide  = thesis.get("exit_guide") or "未設定"
    return thesis_text, entry_story, exit_guide
