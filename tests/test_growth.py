"""
tests/test_growth.py

calculator/growth.py の get_segment_growth() 回帰テスト（GROWTH-SOURCE-LABEL-1）。
segment_detail.source が segment_config.py から返された実際の出所
（"segment_config" / "growth_override"）を転記することを検証する。
"""

import sys
import os
from unittest.mock import patch

_PIPELINE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "value", "tanuki_valuation")
)
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from calculator import growth as growth_module  # noqa: E402


def test_segment_detail_source_reflects_growth_override():
    """recommended_g自動注入（growth_override）時はsourceがgrowth_overrideになる"""
    fake_config = {
        "enabled": True,
        "weighted_growth": 0.18,
        "source": "growth_override",
    }
    with patch.object(growth_module, "_get_segment_growth_from_config", return_value=fake_config):
        with patch.object(growth_module, "HAS_SEGMENT_CONFIG", True):
            result = growth_module.get_segment_growth("DUMMY")

    assert result is not None
    assert result.segment_detail["source"] == "growth_override"


def test_segment_detail_source_reflects_segment_config():
    """10-Kセグメント内訳が設定済みの場合はsourceがsegment_configになる"""
    fake_config = {
        "enabled": True,
        "weighted_growth": 0.12,
        "fiscal_year": 2025,
        "source": "segment_config",
    }
    with patch.object(growth_module, "_get_segment_growth_from_config", return_value=fake_config):
        with patch.object(growth_module, "HAS_SEGMENT_CONFIG", True):
            result = growth_module.get_segment_growth("DUMMY")

    assert result is not None
    assert result.segment_detail["source"] == "segment_config"
