"""
tests/test_fy_collision_log_dedup.py

FY-COLLISION-LOG-NONDETERMINISTIC-1の回帰テスト。

common/sec_data/parser.py::_save_fy_collision_log() が、
(field, fy, end_dates, resolution) をキーに完全同一内容のエントリを
重複排除してから fy_collision_log.json に書き込むことを確認する。

_extract_values_best_candidate() が候補XBRLタグごとに_collect_own_data
を独立呼び出しするため、複数の候補タグが同一衝突を検出すると
collisions_out に内容が完全同一のエントリが複数回appendされる
（AVAV/CAKE/COHR/CRM/FCX/FICO/HONで実在確認済み）。この重複は決定的で
毎回同じ件数だけ発生するが、根本原因（値選択ロジックと密結合した
候補タグループ）には手を入れず、_save_fy_collision_log()側での
重複排除ガード（対症療法）で対応した。

実行方法:
    python -m pytest tests/test_fy_collision_log_dedup.py -v
"""

import json
import os

from common.sec_data.parser import SECParser


class TestSaveFyCollisionLogDedup:
    def test_identical_duplicate_entries_are_removed(self, tmp_path):
        """FICOのrpoで実際に確認されたパターン（4個の候補タグが同一衝突を
        独立検出し4件重複）を模した合成データで、1件に排除されることを確認"""
        p = SECParser(data_dir=str(tmp_path))
        collisions = [
            {"field": "rpo", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            {"field": "rpo", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            {"field": "rpo", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            {"field": "rpo", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
        ]
        p._save_fy_collision_log("FICO", collisions)
        path = os.path.join(str(tmp_path), "FICO", "fy_collision_log.json")
        saved = json.load(open(path, encoding="utf-8"))
        assert len(saved["collisions"]) == 1

    def test_distinct_fields_are_not_merged(self, tmp_path):
        """異なるfieldの衝突は別エントリとして保持されること
        （total_liabilities 2件・long_term_debt 3件のように、フィールドが
        異なれば重複排除の対象外）"""
        p = SECParser(data_dir=str(tmp_path))
        collisions = [
            {"field": "total_liabilities", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            {"field": "total_liabilities", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            {"field": "long_term_debt", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
        ]
        p._save_fy_collision_log("FICO", collisions)
        path = os.path.join(str(tmp_path), "FICO", "fy_collision_log.json")
        saved = json.load(open(path, encoding="utf-8"))
        fields = sorted(c["field"] for c in saved["collisions"])
        assert fields == ["long_term_debt", "total_liabilities"]

    def test_distinct_end_dates_are_not_merged(self, tmp_path):
        """同一field/fyでもend_datesが異なれば別の衝突として保持されること
        （真に異なる衝突をfalse positiveで潰さないための回帰テスト）"""
        p = SECParser(data_dir=str(tmp_path))
        collisions = [
            {"field": "rpo", "fy": 2019, "end_dates": ["2019-09-30", "2020-09-30"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
            {"field": "rpo", "fy": 2019, "end_dates": ["2019-08-31", "2020-08-31"],
             "resolution": "fyタグ衝突だがフォールバック年度で自然分離"},
        ]
        p._save_fy_collision_log("FICO", collisions)
        path = os.path.join(str(tmp_path), "FICO", "fy_collision_log.json")
        saved = json.load(open(path, encoding="utf-8"))
        assert len(saved["collisions"]) == 2

    def test_empty_collisions_still_writes_file(self, tmp_path):
        """0件でも毎回書き込む既存仕様（化石ファイル対策）が維持されること"""
        p = SECParser(data_dir=str(tmp_path))
        p._save_fy_collision_log("FICO", [])
        path = os.path.join(str(tmp_path), "FICO", "fy_collision_log.json")
        assert os.path.exists(path)
        saved = json.load(open(path, encoding="utf-8"))
        assert saved["collisions"] == []
