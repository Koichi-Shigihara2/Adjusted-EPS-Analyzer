"""
tests/test_pipeline_logic.py

TANUKI VALUATION pipeline のユニットテスト。
外部API・実ファイルを使わずモックデータで動作する。

実行方法:
    venv/Scripts/python.exe -m pytest tests/test_pipeline_logic.py -v
"""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# ─────────────────────────────────────────────
# sys.path 設定と依存モジュールのスタブ化
# pipeline.py は src/value/tanuki_valuation/ 直下にあり
# 相対インポート（from data_fetcher import ...）を使うため
# ─────────────────────────────────────────────
_PIPELINE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "value", "tanuki_valuation")
)
sys.path.insert(0, _PIPELINE_DIR)

# xlrd（Damodaran XLS 読込）をスタブ化してから growth_sanity を実際にインポート
# テスト6（growth_sanity）では本物の check_growth_sanity ロジックを検証する
sys.modules.setdefault("xlrd", MagicMock())
import growth_sanity as _gs  # 本物のモジュール参照を保存（後でも参照できるよう変数に束縛）

# pipeline の依存モジュールをスタブ化してから pipeline をインポート
# growth_sanity は _gs に保持済みだが pipeline 側ではスタブで十分
for _mod_name in ("data_fetcher", "core_calculator", "validator", "growth_sanity"):
    sys.modules[_mod_name] = MagicMock()

import pipeline  # noqa: E402
from pipeline import TanukiValuationPipeline  # noqa: E402

# ─────────────────────────────────────────────
# hypecore の detect_substage をインポート
# pandas は venv に存在する前提
# ─────────────────────────────────────────────
_HYPECORE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "value", "hypecore")
)
sys.path.insert(0, _HYPECORE_DIR)
import pandas as pd
from hypecore import detect_substage  # noqa: E402


# ─────────────────────────────────────────────
# テスト共通ヘルパー
# ─────────────────────────────────────────────

def _make_pipe(tmp_path) -> TanukiValuationPipeline:
    """TanukiValuationPipeline のテスト用インスタンスを生成する。

    pipeline.__init__ の repo_root 計算式:
        repo_root = dirname(dirname(dirname(output_dir)))
    output_dir を tmp_path の 3 階層下に設定することで repo_root = tmp_path になる。
    （実ファイルのパスが all: tmp_path/docs/value-monitor/... と一致する）
    """
    output_dir = tmp_path / "out" / "tanuki" / "data"
    output_dir.mkdir(parents=True)
    pipe = TanukiValuationPipeline(output_dir=str(output_dir), use_ai_validation=False)
    # _load_eps_map のキャッシュを空に初期化（実ファイルを読まない）
    pipe._eps_summary_cache = {}
    return pipe


def _minimal_valuation(upside: float = 50.0) -> dict:
    """_generate_report に渡す最小限の valuation dict。"""
    return {
        "calculation_date": "2026-05-30",
        "components": {
            "current_price": 100.0,
            "beta": 1.0,
            "sector": "software",
            "industry": "Software",
            "rpo_pv": 0,
            "roe_10yr_avg": None,
            "ma200": 90.0,
            "fcf_base_used": None,
            "latest_revenue": None,
        },
        "upside_percent": upside,
        "intrinsic_value_per_share": 150.0,
        "wacc": {"value": 0.10},
        "alpha": 1.0,
        "rice": {
            "available": True,
            "note": "",
            "base": {"rice": 5.0},
            "q": 0.8,
            "cf_conversion": 4.0,
            "wacc": 0.10,
            "bear": {},
            "bull": {},
        },
        "scenario_valuations": {
            "bear": {"growth_rate": 0.20, "intrinsic_value_per_share": 130.0},
            "base": {"growth_rate": 0.30, "intrinsic_value_per_share": 150.0},
            "bull": {"growth_rate": 0.40, "intrinsic_value_per_share": 180.0},
        },
        "fcf_estimation": {
            "estimated_fcf": 1_000_000,
            "fcf_margin": 20.0,
            "conversion_rate": 0.8,
            "sector": "Software",
        },
        "fcf_base": {"base_fcf": 1_000_000.0},
        "growth_scenarios": {"primary": {"rate": 0.30}},
    }


def _minimal_score_data() -> dict:
    return {"score": "BUY", "funda_score": 75, "score_comment": "テストコメント"}


def _minimal_extra() -> dict:
    return {
        "fcf_history": [],
        "financial_health": {},
        "segments": [],
        "next_earnings_date": "N/A",
    }


def _write_poc_json(tmp_path, ticker: str, substage_label: str, substage_watch: str) -> None:
    """poc.json を tmp_path/docs/value-monitor/hypecore/data/ に作成する。
    pipe.repo_root = tmp_path のとき、pipeline が読みに来るパスと一致する。
    """
    poc_dir = tmp_path / "docs" / "value-monitor" / "hypecore" / "data"
    poc_dir.mkdir(parents=True, exist_ok=True)
    poc_data = {
        "monthly": [{
            "stage": 2,
            "stage_label": "期待拡大期",
            "substage_label": substage_label,
            "substage_watch": substage_watch,
            "short_pct_float": 0.012,
            "rev_yoy": 20.0,
            "recommendation_mean": 2.0,
        }]
    }
    (poc_dir / f"{ticker}_poc.json").write_text(
        json.dumps(poc_data, ensure_ascii=False), encoding="utf-8"
    )


def _write_stonks_json(tmp_path, tickers_data: dict) -> None:
    """stonks-silo の results.json を tmp_path/docs/value-monitor/stonks-silo/data/ に作成する。
    tickers_data: {"TICKER": {"runway": {"runway_months": N}}} 形式
    pipe.repo_root = tmp_path のとき、pipeline が読みに来るパスと一致する。
    stonks-silo は本番でも常に存在するファイルなので、ticker がない場合も
    ファイル自体は作成してエントリなしにする。
    """
    stonks_dir = tmp_path / "docs" / "value-monitor" / "stonks-silo" / "data"
    stonks_dir.mkdir(parents=True, exist_ok=True)
    data = {"tickers": tickers_data}
    (stonks_dir / "results.json").write_text(json.dumps(data), encoding="utf-8")


# ─────────────────────────────────────────────
# 1. FCFコメント判定
#    _generate_score_comment は純粋関数（ファイルI/Oなし）なので直接呼び出せる
# ─────────────────────────────────────────────

class TestFcfComment:
    def test_negative_fcf_latest_shows_fcf_minus(self, tmp_path):
        """直近FCFがマイナス → Comment に「FCFマイナス」を含む（投資フェーズ判定）"""
        pipe = _make_pipe(tmp_path)
        comment = pipe._generate_score_comment(
            "BUY", upside=50.0, rev_yoy=20.0, rule40=40.0,
            fcf_base=1_000_000.0, funda=75, fcf_latest=-50_000.0,
        )
        assert "FCFマイナス" in comment

    def test_positive_fcf_latest_shows_fcf_profit(self, tmp_path):
        """直近FCFがプラス かつ fcf_base もプラス → Comment に「FCF黒字」を含む"""
        pipe = _make_pipe(tmp_path)
        comment = pipe._generate_score_comment(
            "BUY", upside=50.0, rev_yoy=20.0, rule40=40.0,
            fcf_base=1_000_000.0, funda=75, fcf_latest=50_000.0,
        )
        assert "FCF黒字" in comment


# ─────────────────────────────────────────────
# 2. HYPE_Signal EPS条件
#    _generate_report 内の後処理ロジック（substage_watch テキスト置換）を検証
# ─────────────────────────────────────────────

class TestHypeSignal:
    def test_negative_eps_yoy_removes_eps_strong_text(self, tmp_path):
        """EPS YoY がマイナス → HYPE_Signal に「EPSは強い」を含まない（置換される）"""
        pipe = _make_pipe(tmp_path)
        # EPS マイナス成長（-10%）を EPS キャッシュに直接セット
        pipe._eps_summary_cache = {
            "TEST": {"yoy_growth": -0.10, "gaap_eps": -1.0}
        }
        _write_poc_json(tmp_path, "TEST",
                        substage_label="上昇継続中",
                        substage_watch="売上・EPSは強い。推進力がある局面。")

        report = pipe._generate_report(
            "TEST", _minimal_valuation(), _minimal_score_data(), _minimal_extra()
        )

        # 「売上・EPSは強い」が「売上は強いがEPS前年比マイナス」に置換されているはず
        assert "EPSは強い" not in report
        assert "EPS前年比マイナス" in report

    def test_positive_eps_yoy_with_eps_warning_replaces_to_improving(self, tmp_path):
        """EPS YoY がプラス かつ substage_watch に「EPSの悪化も確認」→「EPS改善中」に置換"""
        pipe = _make_pipe(tmp_path)
        # EPS 改善（+15%）をセット
        pipe._eps_summary_cache = {
            "TEST": {"yoy_growth": 0.15, "gaap_eps": 0.5}
        }
        _write_poc_json(tmp_path, "TEST",
                        substage_label="下落警戒中",
                        substage_watch=(
                            "売上・EPSの悪化も確認される本格的な下落局面。"
                            "実体も崩壊中"
                        ))

        report = pipe._generate_report(
            "TEST", _minimal_valuation(), _minimal_score_data(), _minimal_extra()
        )

        # 「実体も崩壊中」が「売上低迷・EPS改善中」に置換されているはず
        assert "実体も崩壊中" not in report
        assert "EPS改善中" in report


# ─────────────────────────────────────────────
# 3. Matrix Label
#    upside の正負で「割安」「割高」が決まることを検証
# ─────────────────────────────────────────────

class TestMatrixLabel:
    def test_positive_upside_label_contains_undervalued(self, tmp_path):
        """upside >= 0 → Matrix の Label: 行に「割安」を含む"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}

        report = pipe._generate_report(
            "TEST", _minimal_valuation(upside=30.0),
            _minimal_score_data(), _minimal_extra()
        )

        # "Label: 割安×高効率" のように Label 行に「割安」が現れる
        assert "Label: 割安" in report

    def test_negative_upside_label_contains_overvalued(self, tmp_path):
        """upside < 0 → Matrix の Label: 行に「割高」を含む"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}

        report = pipe._generate_report(
            "TEST", _minimal_valuation(upside=-25.0),
            _minimal_score_data(), _minimal_extra()
        )

        assert "Label: 割高" in report


# ─────────────────────────────────────────────
# 3b. RICE三分類ラベル (DESIGN-10)
#     RICE値に応じて 高効率/中効率/低効率 の三分類が正しく表示されることを検証
# ─────────────────────────────────────────────

class TestRiceEfficiencyLabel:
    def _make_report_with_rice(self, tmp_path, rice_val: float) -> str:
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = _minimal_valuation(upside=30.0)
        val["rice"]["base"] = {"rice": rice_val}
        return pipe._generate_report("TEST", val, _minimal_score_data(), _minimal_extra())

    def test_rice_above_3_shows_high_efficiency(self, tmp_path):
        """RICE >= 3.0 → Label に「高効率」が含まれる"""
        report = self._make_report_with_rice(tmp_path, 4.0)
        assert "高効率" in report

    def test_rice_between_1_and_3_shows_medium_efficiency(self, tmp_path):
        """1.0 <= RICE < 3.0 → Label に「中効率」が含まれる"""
        report = self._make_report_with_rice(tmp_path, 2.0)
        assert "中効率" in report

    def test_rice_below_1_shows_low_efficiency(self, tmp_path):
        """RICE < 1.0 → Label に「低効率」が含まれる"""
        report = self._make_report_with_rice(tmp_path, 0.5)
        assert "低効率" in report

    def test_rice_exactly_3_shows_high_efficiency(self, tmp_path):
        """RICE = 3.0（境界値）→「高効率」"""
        report = self._make_report_with_rice(tmp_path, 3.0)
        assert "高効率" in report

    def test_rice_exactly_1_shows_medium_efficiency(self, tmp_path):
        """RICE = 1.0（均衡点・境界値）→「中効率」"""
        report = self._make_report_with_rice(tmp_path, 1.0)
        assert "中効率" in report


# ─────────────────────────────────────────────
# 4. Funda_Score ペナルティ
#    _compute_tanuki_score のペナルティ適用ロジックを検証
#    poc.json・EPS キャッシュなしで基本スコアを固定し、ペナルティ量を確認する
#
#    注意: stonks-silo ファイルは本番でも常に存在するため
#    テストでも必ずファイルを作成し、ticker エントリの有無でシナリオを分ける
# ─────────────────────────────────────────────

class TestFundaScorePenalty:
    def test_runway_under_12_applies_30pt_penalty(self, tmp_path):
        """Runway_Months < 12 → funda_score から 30点ペナルティが適用される"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        # stonks-silo に TEST の runway = 6ヶ月 をセット
        _write_stonks_json(tmp_path, {"TEST": {"runway": {"runway_months": 6.0}}})

        # fcf_base > 0 のみで基本スコア 25点。runway ペナルティ -30 → max(0, -5) = 0
        valuation = {"upside_percent": 50.0, "fcf_base": {"base_fcf": 100.0}}
        result = pipe._compute_tanuki_score("TEST", valuation)

        assert result["funda_score"] == 0

    def test_dilution_over_20_applies_15pt_penalty(self, tmp_path):
        """dilution > 20%/yr → funda_score から 15点ペナルティが適用される"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        # stonks-silo に TEST エントリなし（runway ペナルティは発動しない）
        _write_stonks_json(tmp_path, {})

        valuation = {
            "upside_percent": 50.0,
            "fcf_base": {"base_fcf": 100.0},
            "financial_health": {"dilution_3yr_annual_pct": 25.0},  # 20%超
        }
        result = pipe._compute_tanuki_score("TEST", valuation)

        # 基本スコア 25 → -15 = 10
        assert result["funda_score"] == 10

    def test_dilution_over_40_applies_25pt_penalty(self, tmp_path):
        """dilution > 40%/yr → -25点ペナルティ（-15より大きいことを確認）"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        _write_stonks_json(tmp_path, {})

        valuation = {
            "upside_percent": 50.0,
            "fcf_base": {"base_fcf": 100.0},
            "financial_health": {"dilution_3yr_annual_pct": 45.0},  # 40%超
        }
        result = pipe._compute_tanuki_score("TEST", valuation)

        # 基本スコア 25 → -25 = 0
        assert result["funda_score"] == 0


# ─────────────────────────────────────────────
# 5. Runway フォールバック
#    stonks-silo にない銘柄でも computed_runway_months があれば
#    _compute_tanuki_score がペナルティを適用することを検証
#
#    実装上、fallback は stonks-silo ファイルが存在し ticker エントリが
#    ない場合（runway_months = None）に機能する。
#    ファイルごと存在しない場合は if os.path.exists(...) でブロック全体がスキップされるため、
#    テストでも「ファイルあり・TEST エントリなし」で検証する。
# ─────────────────────────────────────────────

class TestRunwayFallback:
    def test_computed_runway_used_when_ticker_absent_from_stonks(self, tmp_path):
        """stonks-silo ファイルはあるが ticker エントリなし → computed_runway_months でペナルティ適用"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        # stonks-silo ファイルは存在するが TEST エントリはない
        _write_stonks_json(tmp_path, {})

        # _load_extra_data が計算済みの computed_runway_months を valuation に含める想定
        valuation = {
            "upside_percent": 50.0,
            "fcf_base": {"base_fcf": 100.0},
            "computed_runway_months": 3.2,  # 3.2ヶ月 < 12 → ペナルティ対象
        }
        result = pipe._compute_tanuki_score("TEST", valuation)

        # 基本スコア 25 → computed_runway < 12 で -30 → 0
        assert result["funda_score"] == 0
        assert result["score"] == "PASS"

    def test_negative_fcf_triggers_penalty_despite_positive_gaap_eps(self, tmp_path):
        """一時的黒字（GAAP EPS プラス）でも直近FCFがマイナスなら Runway ペナルティが発動する
        （computed_runway_months の計算条件: FCF < 0 も含まれる）
        """
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        # stonks-silo ファイルはあるが TEST エントリなし
        _write_stonks_json(tmp_path, {})

        # GAAP EPS はプラスだが FCF はマイナス（一時的黒字）の場合を想定
        # _load_extra_data は FCF < 0 条件で computed_runway_months を計算するため
        # ここでは計算済みの値を valuation に直接セットして _compute_tanuki_score を検証する
        valuation = {
            "upside_percent": 50.0,
            "fcf_base": {"base_fcf": 100.0},
            "fcf_history": [{"year": 2025, "fcf": -92_600_000, "fcf_margin": -30.0}],
            "computed_runway_months": 3.2,  # cash / (|FCF| / 12) で計算済みと仮定
        }
        result = pipe._compute_tanuki_score("TEST", valuation)

        # 一時的黒字でも FCF ベースの runway ペナルティが適用される
        assert result["funda_score"] == 0
        assert result["score"] == "PASS"


# ─────────────────────────────────────────────
# 6. growth_sanity
#    check_growth_sanity の判定ロジックを、Damodaran データをモックして検証
#
#    注意: sys.modules["growth_sanity"] は MagicMock に差し替え済みのため
#    @patch("growth_sanity.get_industry_benchmark") は効かない。
#    _gs（本物のモジュール参照）に patch.object を使う。
# ─────────────────────────────────────────────

class TestGrowthSanity:
    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor",
        "g_ebit": 0.096,   # 業界平均 9.6%
        "roc": 0.10,
        "rr": 0.50,
    })
    def test_growth_2_5x_above_benchmark_adds_warning(self, _mock):
        """phase1_growth が業界平均の2.5倍超 → warnings に ⚠️ が含まれ verdict が REVIEW になる"""
        # 9.6% × 2.5 = 24% を超える 40% を設定
        result = _gs.check_growth_sanity("TEST", phase1_growth=0.40, sector="semiconductor")

        assert any("⚠️" in w for w in result["warnings"]), \
            f"warnings に ⚠️ が見つからない: {result['warnings']}"
        assert result["verdict"] == "REVIEW"

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor",
        "g_ebit": 0.096,
        "roc": 0.10,
        "rr": 0.50,
    })
    def test_growth_at_or_below_benchmark_is_plausible(self, _mock):
        """phase1_growth が業界平均以下 → warnings なし・verdict が PLAUSIBLE"""
        # 業界平均 9.6% 以下の 8% を設定
        result = _gs.check_growth_sanity("TEST", phase1_growth=0.08, sector="semiconductor")

        assert result["verdict"] == "PLAUSIBLE"
        assert not any("⚠️" in w for w in result["warnings"]), \
            f"warnings に予期しない ⚠️: {result['warnings']}"


# ─────────────────────────────────────────────
# 7. recommended_g
#    check_growth_sanity の recommended_g 算出ロジックを検証
# ─────────────────────────────────────────────

class TestRecommendedGrowth:
    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor",
        "g_ebit": 0.096,
        "roc": 0.10,
        "rr": 0.50,
    })
    def test_recommended_g_is_median_of_two_candidates(self, _mock):
        """industry_g + g_fundamental の2候補 → recommended_g が中央値になる"""
        # annual_revenues 3件 → cagr_3yr/5yr = None（len<4 なので算出不可）
        result = _gs.check_growth_sanity(
            "ALAB", phase1_growth=0.934, sector="Semiconductor",
            annual_revenues=[100.0, 200.0, 400.0],
            g_fundamental=0.026,
        )
        # candidates: [0.096, 0.026] → sorted: [0.026, 0.096] → median = 0.061
        assert "recommended_g" in result
        assert result["recommended_g"] is not None
        assert abs(result["recommended_g"] - 0.061) < 0.001

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Software (System & Application)",
        "g_ebit": 0.216,
        "roc": 0.20,
        "rr": 0.60,
    })
    def test_recommended_g_is_median_of_four_candidates(self, _mock):
        """4候補 → recommended_g が中央値（中央2要素の平均）になる"""
        # annual_revenues 6件 → cagr_3yr/5yr 両方算出可
        result = _gs.check_growth_sanity(
            "NOW", phase1_growth=0.221, sector="Software_System",
            annual_revenues=[500.0, 650.0, 900.0, 1200.0, 1700.0, 2300.0],
            g_fundamental=0.014,
        )
        assert "recommended_g" in result
        # candidates 4つすべて > 0 → median = 中央2要素の平均
        # cagr_3yr/5yr の実計算値 + industry=0.216 + g_fundamental=0.014
        # 候補は4個 → recommended_g は None でない
        assert result["recommended_g"] is not None

    @patch.object(_gs, "get_industry_benchmark", return_value=None)
    def test_single_candidate_gives_none_recommended_g(self, _mock):
        """industry_g=None + cagr 不可 → 候補1件 → recommended_g = None"""
        result = _gs.check_growth_sanity(
            "TEST", phase1_growth=0.20, sector=None,
            annual_revenues=[100.0, 200.0],  # 2件 → cagr 計算不可
            g_fundamental=0.03,
        )
        # candidates = [0.03] のみ（1件）→ None
        assert result.get("recommended_g") is None

    def test_segment_configured_no_auto_adjusted_in_report(self, tmp_path):
        """segment_configured=True → レポートに Growth_Rate_Original/Adjusted が出力されない"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}

        extra = {
            **_minimal_extra(),
            "segment_configured": True,
            "segment_ttm_applied": False,
            "phase1_growth_auto_adjusted": False,
            "phase1_growth_original": None,
            "recommended_g": None,
        }
        report = pipe._generate_report(
            "NVDA", _minimal_valuation(), _minimal_score_data(), extra
        )

        assert "Growth_Rate_Original" not in report
        assert "Growth_Rate_Adjusted" not in report

    def test_segment_unconfigured_auto_adjusted_shows_in_report(self, tmp_path):
        """segment_configured=False + auto_adjusted=True → Growth_Rate_Original/Adjusted が出力される"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}

        extra = {
            **_minimal_extra(),
            "segment_configured": False,
            "segment_ttm_applied": True,
            "phase1_growth_auto_adjusted": True,
            "phase1_growth_original": 0.934,   # TTM: 93.4%
            "recommended_g": 0.061,             # 推奨: 6.1%
        }
        report = pipe._generate_report(
            "ALAB", _minimal_valuation(), _minimal_score_data(), extra
        )

        assert "Growth_Rate_Original: 93.4% (TTM実績)" in report
        assert "Growth_Rate_Adjusted: 6.1% (推奨値・中央値ベース)" in report
        assert "（推奨値ベース）" in report


# ─────────────────────────────────────────────
# 8. 高成長逓減モデル vs 中央値モデル
# ─────────────────────────────────────────────

class TestGrowthDecayModel:
    """TTM > 50% → 逓減モデル、≤ 50% → 中央値モデルのテスト"""

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor", "g_ebit": 0.096, "roc": 0.20, "rr": 0.60,
    })
    def test_high_ttm_uses_decay_model(self, _mock):
        """TTM 93% (cagr_3yr) → 逓減モデル適用"""
        # revenues[-1]/revenues[-4] = 719/100 = 7.19 → cagr_3yr ≈ 93%
        result = _gs.check_growth_sanity(
            "TEST", phase1_growth=0.93, sector="Semiconductor",
            annual_revenues=[100.0, 200.0, 400.0, 719.0],
        )
        assert result["growth_model"] == "decay"
        assert result["recommended_g"] is not None
        # (min(0.93, 1.0) + 0.096) / 2 ≈ 0.513
        expected = (0.93 + 0.096) / 2
        assert abs(result["recommended_g"] - expected) < 0.01

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Software (System & Application)", "g_ebit": 0.10, "roc": 0.20, "rr": 0.60,
    })
    def test_low_ttm_uses_median_model(self, _mock):
        """TTM 30% (cagr_3yr) → 中央値モデル維持"""
        # revenues[-1]/revenues[-4] = 220/100 = 2.2 → cagr_3yr ≈ 30%
        result = _gs.check_growth_sanity(
            "TEST", phase1_growth=0.30, sector="Software_System",
            annual_revenues=[100.0, 140.0, 180.0, 220.0],
        )
        assert result["growth_model"] == "median"

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Software (System & Application)", "g_ebit": 0.10, "roc": 0.20, "rr": 0.60,
    })
    def test_boundary_ttm_50_uses_median(self, _mock):
        """TTM exactly 50% → 境界値は中央値モデル（> 50% でなければ逓減不適用）"""
        # revenues[-1]/revenues[-4] = 337/100 = 3.37 → cagr_3yr ≈ 49.9%
        result = _gs.check_growth_sanity(
            "TEST", phase1_growth=0.50, sector="Software_System",
            annual_revenues=[100.0, 150.0, 200.0, 337.0],
        )
        assert result["growth_model"] == "median"

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor", "g_ebit": 0.096, "roc": 0.20, "rr": 0.60,
    })
    def test_ttm_actual_triggers_decay_without_cagr_data(self, _mock):
        """ttm_actual=93.4% のみで逓減モデルがトリガーされる（CAGR履歴なし）"""
        result = _gs.check_growth_sanity(
            "ALAB", phase1_growth=0.934, sector="Semiconductor",
            annual_revenues=None,  # CAGR データなし
            ttm_actual=0.934,
        )
        assert result["growth_model"] == "decay"
        # (min(0.934, 1.0) + 0.096) / 2 ≈ 0.515
        expected = (0.934 + 0.096) / 2
        assert abs(result["recommended_g"] - expected) < 0.005


# ─────────────────────────────────────────────
# GROWTH-1: HypeCoreフェーズ別逓減モデル重み調整
#    check_growth_sanity の hype_phase パラメータで
#    TTM / 業界平均の重みが変わることを検証
# ─────────────────────────────────────────────

class TestGrowthDecayModelPhaseWeight:
    """GROWTH-1: フェーズ別逓減カーブの傾き調整テスト"""

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor", "g_ebit": 0.096, "roc": 0.20, "rr": 0.60,
    })
    def test_phase1_gives_ttm_heavy_recommended_g(self, _mock):
        """Phase1（黎明期）→ TTM重み65%: recommended_g がフェーズなし(50%)より高い"""
        ttm, industry = 0.80, 0.096
        result_phase1 = _gs.check_growth_sanity(
            "ALAB", phase1_growth=ttm, sector="Semiconductor",
            annual_revenues=None, ttm_actual=ttm, hype_phase=1,
        )
        result_no_phase = _gs.check_growth_sanity(
            "ALAB", phase1_growth=ttm, sector="Semiconductor",
            annual_revenues=None, ttm_actual=ttm, hype_phase=None,
        )
        assert result_phase1["growth_model"] == "decay"
        # Phase1: TTM×0.65 + industry×0.35
        expected_phase1 = ttm * 0.65 + industry * 0.35
        assert abs(result_phase1["recommended_g"] - expected_phase1) < 0.001
        # Phase1 は フェーズなし(50:50) より recommended_g が高い
        assert result_phase1["recommended_g"] > result_no_phase["recommended_g"]

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor", "g_ebit": 0.096, "roc": 0.20, "rr": 0.60,
    })
    def test_phase4_gives_industry_heavy_recommended_g(self, _mock):
        """Phase4（剥落期）→ 業界平均重み65%: recommended_g がフェーズなし(50%)より低い"""
        ttm, industry = 0.80, 0.096
        result_phase4 = _gs.check_growth_sanity(
            "ALAB", phase1_growth=ttm, sector="Semiconductor",
            annual_revenues=None, ttm_actual=ttm, hype_phase=4,
        )
        result_no_phase = _gs.check_growth_sanity(
            "ALAB", phase1_growth=ttm, sector="Semiconductor",
            annual_revenues=None, ttm_actual=ttm, hype_phase=None,
        )
        assert result_phase4["growth_model"] == "decay"
        # Phase4: TTM×0.35 + industry×0.65
        expected_phase4 = ttm * 0.35 + industry * 0.65
        assert abs(result_phase4["recommended_g"] - expected_phase4) < 0.001
        # Phase4 は フェーズなし(50:50) より recommended_g が低い
        assert result_phase4["recommended_g"] < result_no_phase["recommended_g"]

    @patch.object(_gs, "get_industry_benchmark", return_value={
        "industry": "Semiconductor", "g_ebit": 0.096, "roc": 0.20, "rr": 0.60,
    })
    def test_phase3_equals_default_50_50(self, _mock):
        """Phase3（陶酔期）→ 従来と同じ50:50の挙動"""
        ttm, industry = 0.80, 0.096
        result_phase3 = _gs.check_growth_sanity(
            "ALAB", phase1_growth=ttm, sector="Semiconductor",
            annual_revenues=None, ttm_actual=ttm, hype_phase=3,
        )
        expected_50_50 = ttm * 0.50 + industry * 0.50
        assert abs(result_phase3["recommended_g"] - expected_50_50) < 0.001
        # 戻り値に hype_phase_used が記録されている
        assert result_phase3["hype_phase_used"] == 3


# ─────────────────────────────────────────────
# 10. hypecore substage_watch の eps_surprise 分岐
#    detect_substage() が eps_surprise の実際の値に応じて
#    「大幅ミス」か「軽微なミス」かを正しく出力することを検証
#
#    Stage4 中盤A ブランチ到達条件:
#      stage=4, stage_months>2, real_strong=False（rev_yoy<=15 かつ eps_surp<=0）,
#      eps_surp is not None, rev_yoy > 5
# ─────────────────────────────────────────────

def _make_stage4_row(rev_yoy: float, eps_surprise: float) -> pd.Series:
    """Stage4 中盤A ブランチに到達するための最小限の pd.Series を生成する。
    real_strong=False になるよう rev_yoy を 15% 以下に設定する。
    """
    return pd.Series({
        "ma200_dev":    -15.0,   # MA200 を下回っている（Stage4 らしい状態）
        "from_peak":    -20.0,   # 高値から -20%
        "rsi":           35.0,   # RSI 低下
        "price_mom3m":  -10.0,
        "ma200_mom":     -3.0,
        "rev_yoy":      rev_yoy,
        "eps_surprise": eps_surprise,
        "price_iv_ratio": None,
        "forward_pe":     None,
    })


class TestHypecoreSubstageWatch:
    def test_minor_eps_miss_does_not_say_large_miss(self):
        """eps_surprise=-0.46%（軽微なミス）→ substage_watch に「大幅ミス」を含まない"""
        row = _make_stage4_row(rev_yoy=10.0, eps_surprise=-0.46)
        result = detect_substage(row, stage=4, stage_months=3)

        assert result["label"] == "実体軟化・期待崩壊中"
        assert "大幅ミス" not in result["watch"], \
            f"軽微なミスなのに「大幅ミス」が含まれている: {result['watch']}"
        # 実際の eps_surprise 値がテキストに反映されているか
        assert "-0.46" in result["watch"] or "わずかに" in result["watch"], \
            f"予想比の値が watch に含まれていない: {result['watch']}"

    def test_large_eps_miss_says_large_miss(self):
        """eps_surprise=-10%（大幅ミス）→ substage_watch に「大幅ミス」を含む"""
        row = _make_stage4_row(rev_yoy=10.0, eps_surprise=-10.0)
        result = detect_substage(row, stage=4, stage_months=3)

        assert result["label"] == "実体軟化・期待崩壊中"
        assert "大幅ミス" in result["watch"], \
            f"大幅ミスなのに「大幅ミス」が含まれていない: {result['watch']}"
        # 実際の eps_surprise 値（-10.0）がテキストに反映されているか
        assert "-10.0" in result["watch"], \
            f"予想比の値が watch に含まれていない: {result['watch']}"


# ─────────────────────────────────────────────
# 9b. GROWTH_PREMIUM 判定（DCF-2）
#     逆DCF Required Growth が TTM 成長率を下回る場合に GROWTH_PREMIUM が返ることを検証
# ─────────────────────────────────────────────

class TestGrowthPremiumScore:
    """_compute_tanuki_score の GROWTH_PREMIUM 判定を検証"""

    def _make_pipe(self, tmp_path):
        from pipeline import TanukiValuationPipeline  # type: ignore[import]
        output_dir = tmp_path / "out" / "tanuki" / "data"
        output_dir.mkdir(parents=True)
        pipe = TanukiValuationPipeline(output_dir=str(output_dir), use_ai_validation=False)
        pipe._eps_summary_cache = {}
        return pipe

    def _base_valuation(self, upside: float, ttm_growth: float, req_growth_factor: float = 0.5) -> dict:
        """テスト用 valuation dict。req_growth が ttm_growth の req_growth_factor 倍になるよう設定"""
        # price * shares = EV。fcf_base から逆算して required_growth = ttm_growth * factor になるよう調整
        # required_fcf5 = EV*(wacc-tvg)/(1+tvg) = fcf_base * (1+req_g)^5
        # EV = required_fcf5 / (wacc-tvg) * (1+tvg)
        fcf_base = 1_000_000_000  # $1B
        wacc, tvg = 0.10, 0.03
        req_g = ttm_growth * req_growth_factor
        required_fcf5 = fcf_base * (1 + req_g) ** 5
        ev = required_fcf5 * (1 + tvg) / (wacc - tvg)
        shares = 1_000_000_000  # 10億株
        price = ev / shares
        return {
            "upside_percent": upside,
            "components": {
                "current_price": price,
                "diluted_shares": shares,
                "fcf_base_used": fcf_base,
            },
            "financial_health": {"net_debt": 0},
            "wacc": {"value": wacc, "market_return": wacc},
            "growth_sanity": {"phase1_growth": ttm_growth},
        }

    def test_growth_premium_when_required_growth_below_ttm(self, tmp_path):
        """Required Growth < TTM 成長率 → GROWTH_PREMIUM"""
        pipe = self._make_pipe(tmp_path)
        # upside=-40%, stage=3, funda>=50 の状態でテストするため poc.json をモック不要
        # _compute_tanuki_score を直接呼ぶかわりに _calc_required_growth をテスト
        val = self._base_valuation(upside=-40.0, ttm_growth=0.80, req_growth_factor=0.5)
        req = pipe._calc_required_growth(val)
        assert req is not None
        assert req < val["growth_sanity"]["phase1_growth"], \
            "Required Growth が TTM を下回るはず（GROWTH_PREMIUM の条件）"

    def test_trim_when_required_growth_exceeds_ttm(self, tmp_path):
        """Required Growth > TTM 成長率 → TRIM（GROWTH_PREMIUM にならない）"""
        pipe = self._make_pipe(tmp_path)
        val = self._base_valuation(upside=-40.0, ttm_growth=0.20, req_growth_factor=2.0)
        req = pipe._calc_required_growth(val)
        assert req is not None
        assert req > val["growth_sanity"]["phase1_growth"], \
            "Required Growth が TTM を上回るはず（TRIM の条件）"

    def test_required_growth_returns_none_without_price(self, tmp_path):
        """株価データ不足のとき None を返す"""
        pipe = self._make_pipe(tmp_path)
        val = {"components": {"current_price": 0}, "financial_health": {}, "wacc": {}, "growth_sanity": {}}
        assert pipe._calc_required_growth(val) is None


# ─────────────────────────────────────────────
# 9. _calc_q: GAAP赤字年スキップ（BUG-2b）
#    NI<0 の年は SBC で earnings がプラスになっても Q 計算から除外されることを検証
#    背景: MRVL TTM2025-02-01 で NI=-469M, SBC=+608M → earnings=139M
#          Q = 1871M/139M = 13.43 という偽高Q が発生し Q異常値誤判定が起きていた
# ─────────────────────────────────────────────

from calculator.rice import _calc_q, calculate_rice  # type: ignore[import]
import maturity_config as _mc  # type: ignore[import]


def _make_entry(ni: float, sbc: float, ocf: float, rev: float) -> dict:
    return {
        "cf": {"operating_cash_flow": ocf, "stock_based_compensation": sbc},
        "pl": {"net_income": ni, "revenue": rev},
    }


# ─────────────────────────────────────────────
# RICE-1: 価値創造係数（roic_wacc_ratio）テスト
#    ROIC/WACC が RICE 計算に正しく反映されることを検証
# ─────────────────────────────────────────────

_RICE_MOCK_ANNUAL = [
    # FY2023（最新）
    {"period": "FY2023",
     "pl": {"revenue": 26_000e6, "net_income": 3_000e6, "research_and_development": 2_000e6},
     "cf": {"operating_cash_flow": 5_000e6, "capital_expenditure": -500e6, "stock_based_compensation": 400e6},
     "data_quality": {}},
    # FY2022
    {"period": "FY2022",
     "pl": {"revenue": 20_000e6, "net_income": 2_500e6, "research_and_development": 1_800e6},
     "cf": {"operating_cash_flow": 4_000e6, "capital_expenditure": -400e6, "stock_based_compensation": 350e6},
     "data_quality": {}},
    # FY2021
    {"period": "FY2021",
     "pl": {"revenue": 16_000e6, "net_income": 2_000e6, "research_and_development": 1_600e6},
     "cf": {"operating_cash_flow": 3_200e6, "capital_expenditure": -350e6, "stock_based_compensation": 300e6},
     "data_quality": {}},
    # FY2020
    {"period": "FY2020",
     "pl": {"revenue": 13_000e6, "net_income": 1_600e6, "research_and_development": 1_400e6},
     "cf": {"operating_cash_flow": 2_600e6, "capital_expenditure": -300e6, "stock_based_compensation": 280e6},
     "data_quality": {}},
]
_RICE_MOCK_SCENARIOS = {
    "bear": {"growth_rate": 0.15, "intrinsic_value_per_share": 200.0},
    "base": {"growth_rate": 0.25, "intrinsic_value_per_share": 280.0},
    "bull": {"growth_rate": 0.35, "intrinsic_value_per_share": 360.0},
}


class TestRiceValueCreationFactor:
    """RICE-1: roic_wacc_ratio による価値創造係数のテスト"""

    def test_high_roic_wacc_amplifies_rice(self):
        """ROIC/WACC=2.0（ROIC=20%・WACC=10%）→ vc_factor=2.0でRICEが2倍になる"""
        base = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=None,
        )
        boosted = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=2.0,
        )
        assert base.available and boosted.available
        assert boosted.base.rice == pytest.approx(base.base.rice * 2.0, rel=1e-6)
        assert boosted.vc_factor == pytest.approx(2.0, rel=1e-6)

    def test_low_roic_wacc_penalizes_rice(self):
        """ROIC/WACC=0.5（ROIC=5%・WACC=10%）→ vc_factor=0.5でRICEが半減"""
        base = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=None,
        )
        penalized = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=0.5,
        )
        assert base.available and penalized.available
        assert penalized.base.rice == pytest.approx(base.base.rice * 0.5, rel=1e-6)
        assert penalized.vc_factor == pytest.approx(0.5, rel=1e-6)

    def test_no_roic_wacc_is_backward_compatible(self):
        """roic_wacc_ratio=None → vc_factor=None、RICE値は従来と同じ"""
        result = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=None,
        )
        assert result.available
        assert result.vc_factor is None
        assert result.roic_wacc_ratio is None

    def test_vc_factor_floor_at_0_3(self):
        """roic_wacc_ratio=0.1（極端に低いROIC）→ vc_factor は 0.3 でフロアされる"""
        result = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=0.1,
        )
        assert result.available
        assert result.vc_factor == pytest.approx(0.3, rel=1e-6)

    def test_vc_factor_cap_at_2_0(self):
        """roic_wacc_ratio=5.0（極端に高いROIC）→ vc_factor は 2.0 でキャップされる"""
        result = calculate_rice(
            annual_data=_RICE_MOCK_ANNUAL,
            wacc=0.10,
            scenario_valuations=_RICE_MOCK_SCENARIOS,
            roic_wacc_ratio=5.0,
        )
        assert result.available
        assert result.vc_factor == pytest.approx(2.0, rel=1e-6)


class TestCalcQNegativeNI:
    def test_negative_ni_skipped_even_when_sbc_makes_earnings_positive(self):
        """NI<0 かつ SBC で earnings>0 になる年はスキップされる（MRVLケース）"""
        data = [
            _make_entry(ni=-469e6, sbc=608e6, ocf=1871e6, rev=6424e6),  # earns=139M, Q=13.4 → SKIP
        ]
        q, used, _ = _calc_q(data)
        assert used == 0, "GAAP赤字年はSBCでelearnings>0でもスキップされるべき"

    def test_positive_ni_year_is_included(self):
        """NI>0 の年は通常通り計算に含まれる"""
        data = [
            _make_entry(ni=2888e6, sbc=592e6, ocf=1791e6, rev=8518e6),  # Q=0.51
        ]
        q, used, _ = _calc_q(data)
        assert used == 1
        assert abs(q - 1791e6 / (2888e6 + 592e6)) < 0.01

    def test_mrvl_pattern_excludes_negative_ni_year(self):
        """MRVLパターン: 赤字TTM年を除外し黒字年のみでQ平均を計算"""
        data = [
            _make_entry(ni=2888e6,  sbc=592e6, ocf=1791e6, rev=8518e6),  # Q=0.51  ✓
            _make_entry(ni=-469e6,  sbc=608e6, ocf=1871e6, rev=6424e6),  # SKIP（NI<0）
            _make_entry(ni=-1157e6, sbc=622e6, ocf=1709e6, rev=5612e6),  # SKIP（NI<0）
            _make_entry(ni=-13e6,   sbc=552e6, ocf=1446e6, rev=5891e6),  # SKIP（NI<0）
        ]
        q, used, _ = _calc_q(data, years=3)
        # years=3 なので先頭3件のみ参照 → 黒字は先頭1件のみ
        assert used == 1
        assert q < 5.0, f"Q={q:.2f} が Q_MAX=5.0 を超えてはならない（Q異常値誤判定防止）"


# ─────────────────────────────────────────────
# 10. calculate_tapering_dcf（DCF-1）
#     Phase1内で成長率を線形逓減させるDCFの年次成長率と価値計算を検証
# ─────────────────────────────────────────────

_CALC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "src", "value", "tanuki_valuation", "calculator")
)
sys.path.insert(0, _CALC_DIR)
from dcf import calculate_tapering_dcf, calculate_two_stage_dcf  # type: ignore[import]


class TestTaperingDCF:
    def test_year1_equals_g_start(self):
        """Year1の成長率がg_startと一致する"""
        result = calculate_tapering_dcf(
            base_fcf=1_000_000, g_start=0.50, g_end=0.10,
            wacc=0.12, high_growth_years=5,
        )
        assert abs(result.high_growth_detail[0]["growth_rate"] - 0.50) < 1e-9

    def test_last_year_equals_g_end(self):
        """Year5の成長率がg_endと一致する"""
        result = calculate_tapering_dcf(
            base_fcf=1_000_000, g_start=0.50, g_end=0.10,
            wacc=0.12, high_growth_years=5,
        )
        assert abs(result.high_growth_detail[-1]["growth_rate"] - 0.10) < 1e-9

    def test_growth_rates_are_linearly_decreasing(self):
        """中間年の成長率が線形補間になっている"""
        result = calculate_tapering_dcf(
            base_fcf=1_000_000, g_start=0.50, g_end=0.10,
            wacc=0.12, high_growth_years=5,
        )
        rates = [d["growth_rate"] for d in result.high_growth_detail]
        # Year2 = 0.50 + (0.10-0.50)*1/4 = 0.40
        assert abs(rates[1] - 0.40) < 1e-9
        # Year3 = 0.50 + (0.10-0.50)*2/4 = 0.30
        assert abs(rates[2] - 0.30) < 1e-9

    def test_tapering_gives_lower_value_than_fixed_high_growth(self):
        """逓減DCFは高成長固定DCFより低い価値を返す（高成長銘柄への保守的評価）"""
        base_fcf, wacc = 1_000_000, 0.12
        tapering = calculate_tapering_dcf(
            base_fcf=base_fcf, g_start=0.50, g_end=0.10,
            wacc=wacc, high_growth_years=5,
        )
        fixed = calculate_two_stage_dcf(
            base_fcf=base_fcf, high_growth_rate=0.50,
            wacc=wacc, high_growth_years=5,
        )
        assert tapering.v0 < fixed.v0, "逓減DCFは固定高成長DCFより低い価値であるべき"

    def test_equal_start_end_matches_two_stage(self):
        """g_start == g_end の場合は2段階DCFと同等になる"""
        base_fcf, wacc, g = 1_000_000, 0.12, 0.20
        tapering = calculate_tapering_dcf(
            base_fcf=base_fcf, g_start=g, g_end=g,
            wacc=wacc, high_growth_years=5,
        )
        fixed = calculate_two_stage_dcf(
            base_fcf=base_fcf, high_growth_rate=g,
            wacc=wacc, high_growth_years=5,
        )
        assert abs(tapering.v0 - fixed.v0) < 1.0, "g_start==g_endのとき2段階DCFと同値になるべき"


# ─────────────────────────────────────────────
# WACC-1: セクター別ターミナル成長率
#    get_terminal_growth() のフォールバックロジックを検証
# ─────────────────────────────────────────────

class TestTerminalGrowthBySector:
    """WACC-1: get_terminal_growth() のセクター別フォールバック検証"""

    def test_software_industry_returns_35_pct(self):
        """Software (System & Application) 銘柄 → tv_g = 3.5%"""
        with patch.object(_mc, "_lookup_tv_g_by_industry", return_value=0.035):
            result = _mc.get_terminal_growth("NOW")
        assert result == pytest.approx(0.035, rel=1e-6)

    def test_consumer_industry_returns_25_pct(self):
        """Restaurant/Dining 銘柄 → tv_g = 2.5%"""
        with patch.object(_mc, "_lookup_tv_g_by_industry", return_value=0.025):
            result = _mc.get_terminal_growth("CAKE")
        assert result == pytest.approx(0.025, rel=1e-6)

    def test_unknown_ticker_returns_default_30_pct(self):
        """業種不明銘柄 → tv_g = 3.0%（デフォルト）"""
        with patch.object(_mc, "_lookup_tv_g_by_industry", return_value=None):
            result = _mc.get_terminal_growth("UNKNOWN_XYZ")
        assert result == pytest.approx(0.030, rel=1e-6)

    def test_damodaran_tv_g_table_has_software_35_pct(self):
        """_DAMODARAN_TV_G テーブルに Software (System & Application) → 3.5% が含まれる"""
        assert _mc._DAMODARAN_TV_G.get("Software (System & Application)") == pytest.approx(0.035)

    def test_damodaran_tv_g_table_has_restaurant_25_pct(self):
        """_DAMODARAN_TV_G テーブルに Restaurant/Dining → 2.5% が含まれる"""
        assert _mc._DAMODARAN_TV_G.get("Restaurant/Dining") == pytest.approx(0.025)

    def test_damodaran_tv_g_table_has_utility_20_pct(self):
        """_DAMODARAN_TV_G テーブルに Power → 2.0% が含まれる"""
        assert _mc._DAMODARAN_TV_G.get("Power") == pytest.approx(0.020)

    def test_calc_required_growth_uses_tv_g_parameter(self, tmp_path):
        """_calc_required_growth は tv_g パラメータを正しく使用する"""
        pipe = _make_pipe(tmp_path)
        # 同じ valuation でも tv_g が違えば Required Growth が変わる
        val = {
            "components": {
                "current_price": 100.0,
                "diluted_shares": 1_000_000_000,
                "fcf_base_used": 5_000_000_000,
            },
            "financial_health": {"net_debt": 0},
            "wacc": {"value": 0.10, "market_return": 0.10},
        }
        req_30 = pipe._calc_required_growth(val, tv_g=0.030)
        req_35 = pipe._calc_required_growth(val, tv_g=0.035)
        assert req_30 is not None and req_35 is not None
        # tv_g が高いほど分子(wacc - tv_g)が小さくなり required_fcf5 が小さくなる
        # → 必要成長率は低下する
        assert req_35 < req_30, "tv_g=3.5% のとき required_growth は tv_g=3.0% より低いはず"


# ─────────────────────────────────────────────────────────────────
# safe_yf_utils テスト
# ─────────────────────────────────────────────────────────────────
_REPO_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT_DIR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_DIR)

from common.yfinance_utils import safe_yf_ticker, safe_yf_history


class TestSafeYfTicker:
    def test_returns_none_on_network_failure(self):
        """fast_info アクセスで例外が出たとき None を返す"""
        with patch("common.yfinance_utils.yf.Ticker") as mock_cls:
            mock_instance = MagicMock()
            type(mock_instance).fast_info = PropertyMock(
                side_effect=Exception("network error")
            )
            mock_cls.return_value = mock_instance
            result = safe_yf_ticker("AAPL", retries=0, wait=0)
            assert result is None

    def test_returns_ticker_on_success(self):
        """fast_info が正常に返ったとき Ticker オブジェクトを返す"""
        with patch("common.yfinance_utils.yf.Ticker") as mock_cls:
            mock_instance = MagicMock()
            # fast_info は例外を出さない（MagicMock デフォルト）
            mock_cls.return_value = mock_instance
            result = safe_yf_ticker("AAPL", retries=0, wait=0)
            assert result is mock_instance

    def test_retries_on_failure(self):
        """retries=1 のとき sleep が1回呼ばれる（リトライ発生の証拠）"""
        with patch("common.yfinance_utils.yf.Ticker") as mock_cls, \
             patch("common.yfinance_utils.time.sleep") as mock_sleep:
            mock_instance = MagicMock()
            type(mock_instance).fast_info = PropertyMock(
                side_effect=Exception("flaky")
            )
            mock_cls.return_value = mock_instance
            result = safe_yf_ticker("AAPL", retries=1, wait=0)
        assert result is None
        assert mock_sleep.call_count == 1  # retries=1 → 1回スリープ


class TestSafeYfHistory:
    def test_returns_empty_df_on_failure(self):
        """例外が出たとき空 DataFrame を返す"""
        import pandas as pd
        with patch("common.yfinance_utils.yf.Ticker") as mock_cls:
            mock_cls.return_value.history.side_effect = Exception("timeout")
            result = safe_yf_history("AAPL", period="5d", retries=0)
            assert isinstance(result, pd.DataFrame)
            assert result.empty

    def test_returns_data_on_success(self):
        """正常時は DataFrame を返す"""
        import pandas as pd
        fake_df = pd.DataFrame({"Close": [100.0, 101.0]})
        with patch("common.yfinance_utils.yf.Ticker") as mock_cls:
            mock_cls.return_value.history.return_value = fake_df
            result = safe_yf_history("AAPL", period="5d", retries=0)
            assert not result.empty
            assert "Close" in result.columns

    def test_accepts_start_end_kwargs(self):
        """start/end キーワード引数を history に渡せる"""
        import pandas as pd
        fake_df = pd.DataFrame({"Close": [150.0]})
        with patch("common.yfinance_utils.yf.Ticker") as mock_cls:
            mock_cls.return_value.history.return_value = fake_df
            result = safe_yf_history("AAPL", period=None, start="2026-01-01", end="2026-01-05", retries=0)
            mock_cls.return_value.history.assert_called_once_with(
                period=None, start="2026-01-01", end="2026-01-05"
            )
            assert not result.empty


# ─────────────────────────────────────────────
# 14. determine_stage: S0→S1昇格ロジック
# ─────────────────────────────────────────────
from hypecore import determine_stage  # noqa: E402


def _make_row(**kwargs) -> pd.Series:
    """determine_stage 用の最小 pd.Series を生成する"""
    defaults = dict(
        ma200_dev=0, ma200_mom=0, from_peak=0, price_mom3m=0,
        rsi=50, vol_surge=1.0,
        sell_on_good_news=0, eps_surprise=None, analyst_upgrade_rate=None,
        buy_hold_ratio=None, forward_pe=None, peg_ratio=None,
        revenue_growth=None, earnings_growth=None,
        short_pct_float=None, recommendation_mean=None,
        expectation_score=0, fundamental_score=0, momentum_score=0,
    )
    defaults.update(kwargs)
    return pd.Series(defaults)


class TestDetermineStageS0S1Promotion:
    """S0条件でも反発モメンタムが強ければS1に昇格する"""

    def test_deep_s0_weak_rebound_stays_s0(self):
        """深い低迷（MA200=-23%）+ 反発+14% → S0維持（昇格条件 +20% 未達）"""
        row = _make_row(ma200_dev=-23, price_mom3m=14, rsi=45)
        assert determine_stage(row, prev_stage=2) == 0

    def test_deep_s0_strong_rebound_promotes_to_s1(self):
        """深い低迷（MA200=-23%）+ 強反発+22% → S1昇格"""
        row = _make_row(ma200_dev=-23, price_mom3m=22, rsi=48)
        assert determine_stage(row, prev_stage=2) == 1

    def test_shallow_s0_moderate_rebound_promotes_to_s1(self):
        """浅い低迷（MA200=-15%, short>8%）+ 反発+12% → S1昇格"""
        row = _make_row(ma200_dev=-15, price_mom3m=12, short_pct_float=0.10, rsi=47)
        assert determine_stage(row, prev_stage=2) == 1

    def test_shallow_s0_insufficient_rebound_stays_s0(self):
        """浅い低迷（MA200=-15%, short>8%）+ 反発+8% → S0維持（+10% 未達）"""
        row = _make_row(ma200_dev=-15, price_mom3m=8, short_pct_float=0.10, rsi=45)
        assert determine_stage(row, prev_stage=2) == 0


# ─────────────────────────────────────────────
# 15. adjust_rpo: RPO比率条件ゲート (B-5 whitelist方式+比率条件)
# ─────────────────────────────────────────────
from calculator.adjustments import adjust_rpo, _get_rpo_application_rate  # type: ignore[import]


class TestRpoRatioGate:
    """whitelist通過/keyword通過+比率条件/keyword通過+比率未達を検証"""

    def test_whitelist_ticker_bypasses_ratio_check(self):
        """whitelist登録銘柄は比率<0.3でも exclusion_reason が設定されない"""
        # ratio=0.03 < 0.30: 非whitelist銘柄なら除外されるが GOOGL(whitelist) は免除
        result_wl = adjust_rpo(
            rpo=3_000_000_000,   # RPO $3B
            sector="Communication Services",
            ticker="GOOGL",      # whitelist登録済み
            industry="Internet Content & Information",
            op_margin=0.30,
            rev_ttm=100_000_000_000,  # ratio=0.03 < 0.30
        )
        result_nwl = adjust_rpo(
            rpo=3_000_000_000,
            sector="Technology",
            ticker="NONWHITE",   # whitelist未登録
            industry="Software - Application",
            op_margin=0.30,
            rev_ttm=100_000_000_000,  # ratio=0.03 < 0.30
        )
        # whitelist → 比率チェック免除 → exclusion_reason なし
        assert result_wl.exclusion_reason == ""
        # 非whitelist → 比率チェックで除外
        assert "not applied" in result_nwl.exclusion_reason

    def test_keyword_ticker_below_ratio_is_excluded(self):
        """softwareキーワードで通過しても RPO/Revenue<0.3 なら除外される"""
        result = adjust_rpo(
            rpo=2_000_000_000,   # RPO $2B
            sector="Technology",
            ticker="TESTSOFT",   # whitelist未登録
            industry="Software - Application",
            op_margin=0.25,
            rev_ttm=20_000_000_000,  # Revenue $20B → ratio=0.10 < 0.30
        )
        assert result.rpo_pv == 0.0
        assert "not applied" in result.exclusion_reason
        assert "0.10" in result.exclusion_reason

    def test_keyword_ticker_above_ratio_is_applied(self):
        """softwareキーワードで通過し RPO/Revenue>=0.3 なら exclusion_reason なしで適用"""
        # rpo=25B > rev_ttm=20B → rpo_incremental>0 かつ ratio=1.25 >= 0.30
        result = adjust_rpo(
            rpo=25_000_000_000,  # RPO $25B
            sector="Technology",
            ticker="TESTSOFT2",  # whitelist未登録
            industry="Software - Application",
            op_margin=0.20,
            rev_ttm=20_000_000_000,  # Revenue $20B → ratio=1.25 >= 0.30
        )
        assert result.exclusion_reason == ""
        assert result.rpo_pv > 0


# ─────────────────────────────────────────────
# 16. _compute_tanuki_score: DCF_Reliability=LOW → WATCH丸め
# ─────────────────────────────────────────────

class TestDcfReliabilityLowRounding:
    """DCF_Reliability=LOW (fcf_floor_applied>0) のとき WATCH に丸められる"""

    def test_low_reliability_rounds_hold_to_watch(self, tmp_path):
        """HOLD銘柄でfcf_floor_applied>0 → WATCH に丸められ、コメントにLOW旨が入る"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        valuation = {
            "upside_percent": -5.0,   # HOLDになる条件
            "components": {
                "fcf_floor_applied": 1_000_000_000,  # LOW判定トリガー
                "diluted_shares": None,
            },
            "fcf_base": {"base_fcf": 500_000_000},
            "financial_health": {},
            "fcf_estimation": {},
        }
        result = pipe._compute_tanuki_score("LOWTEST", valuation)
        assert result["score"] == "WATCH"
        assert "LOW" in result["score_comment"]

    def test_low_reliability_keeps_sell(self, tmp_path):
        """ファンダ劣化SELLはfcf_floor_applied>0でもSELLのまま維持される"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        # SELLになる条件: 25 <= funda < 50 かつ sell_funda=True
        # sell_funda = rev_yoy<0 and rule40<20 and fcf_est < fcf_base*0.8
        # funda: rev_yoy=-5 → +0, rule40=15 → +0, eps_yoy=None → +0, fcf_base>0 → +25 = 25
        poc_dir = tmp_path / "docs" / "value-monitor" / "hypecore" / "data"
        poc_dir.mkdir(parents=True, exist_ok=True)
        (poc_dir / "SELLTEST_poc.json").write_text(json.dumps({
            "monthly": [{"stage": 2, "rev_yoy": -5.0, "rule40": 15.0}]
        }), encoding="utf-8")
        valuation = {
            "upside_percent": 30.0,
            "components": {
                "fcf_floor_applied": 1_000_000_000,  # LOW判定トリガー
                "diluted_shares": None,
            },
            "fcf_base": {"base_fcf": 1_000_000},      # FCF正（funda+25）
            "financial_health": {},
            "fcf_estimation": {                         # fcf_est < fcf_base*0.8 → sell_funda
                "estimated_fcf": 600_000,
            },
        }
        result = pipe._compute_tanuki_score("SELLTEST", valuation)
        # funda=25, sell_funda=True → SELL。LOW丸め対象外（SELL維持）
        assert result["score"] == "SELL"


class TestDcfReliabilityPolicyB:
    """
    DCF-RELIABILITY-1: FCF_Conversion_Rate方式向けDCF_Reliability判定（Policy B）

    判定表（DCF-REL-SYNC-1 2026-07-11修正: transient_found→action=="excluded"に変更。
    証拠が"存在するか"ではなく乖離を"金額として説明しきれているか"で判定する）:
      eps_invalid=true                                       → LOW（最優先）
      eps_invalid=false, detected=true,  action!="excluded"  → LOW
      eps_invalid=false, detected=true,  action=="excluded"  → NORMAL
      eps_invalid=false, detected=false                      → NORMAL
    """

    @staticmethod
    def _valuation(detected: bool, explained: bool, divergence_warning: str = "") -> dict:
        return {
            "fcf_outlier": {
                "detected": detected,
                "action": "excluded" if explained else "flagged",
            },
            "fcf_estimation": {
                "applied": True,
                "divergence_warning": divergence_warning,
            },
        }

    def test_detected_true_not_explained_is_low(self):
        v = self._valuation(detected=True, explained=False)
        assert TanukiValuationPipeline._calc_dcf_reliability_policy_b(v) == "LOW"

    def test_detected_true_explained_is_normal(self):
        v = self._valuation(detected=True, explained=True)
        assert TanukiValuationPipeline._calc_dcf_reliability_policy_b(v) == "NORMAL"

    def test_detected_true_flagged_with_partial_evidence_is_low(self):
        """一過性費用の証拠(transient_evidence.found)はあるが乖離を説明しきれない(action=flagged)場合はLOW
        （DCF-REL-SYNC-1: FLYW型の回帰防止。旧ロジックはfoundのみを見てNORMAL誤判定していた）"""
        v = {
            "fcf_outlier": {
                "detected": True,
                "action": "flagged",
                "transient_evidence": {"found": True},
            },
            "fcf_estimation": {"applied": True, "divergence_warning": ""},
        }
        assert TanukiValuationPipeline._calc_dcf_reliability_policy_b(v) == "LOW"

    def test_detected_false_eps_valid_is_normal(self):
        v = self._valuation(detected=False, explained=False)
        assert TanukiValuationPipeline._calc_dcf_reliability_policy_b(v) == "NORMAL"

    def test_detected_false_eps_invalid_is_low(self):
        v = self._valuation(detected=False, explained=False, divergence_warning="乖離警告")
        assert TanukiValuationPipeline._calc_dcf_reliability_policy_b(v) == "LOW"

    def test_eps_invalid_overrides_explained_true(self):
        """eps_invalid=true は detected×explained=true（本来NORMAL）より優先してLOWにする"""
        v = self._valuation(detected=True, explained=True, divergence_warning="乖離警告")
        assert TanukiValuationPipeline._calc_dcf_reliability_policy_b(v) == "LOW"

    def test_compute_tanuki_score_rounds_to_watch_when_policy_b_low(self, tmp_path):
        """fcf_estimation.applied=True & Policy B=LOW → WATCHに丸められる"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        valuation = {
            "upside_percent": -5.0,  # HOLDになる条件
            "components": {"diluted_shares": None},
            "fcf_base": {"base_fcf": 500_000_000},
            "financial_health": {},
            "fcf_estimation": {"applied": True, "divergence_warning": ""},
            "fcf_outlier": {
                "detected": True,
                "transient_evidence": {"found": False},
            },
        }
        result = pipe._compute_tanuki_score("POLICYB_LOW", valuation)
        assert result["score"] == "WATCH"
        assert "LOW" in result["score_comment"]

    def test_compute_tanuki_score_not_rounded_when_policy_b_normal(self, tmp_path):
        """fcf_estimation.applied=True だが Policy B=NORMAL → 通常判定のまま（WATCHに強制されない）"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        valuation = {
            "upside_percent": -5.0,  # HOLDになる条件（upside<=0 かつ <-30でないため）
            "components": {"diluted_shares": None},
            "fcf_base": {"base_fcf": 500_000_000},
            "financial_health": {},
            "fcf_estimation": {"applied": True, "divergence_warning": ""},
            "fcf_outlier": {
                "detected": False,
                "transient_evidence": {"found": False},
            },
        }
        result = pipe._compute_tanuki_score("POLICYB_NORMAL", valuation)
        assert result["score"] == "HOLD"

    def test_compute_tanuki_score_keeps_sell_when_policy_b_low(self, tmp_path):
        """ファンダ劣化SELLはPolicy B=LOWでもSELLのまま維持される"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        poc_dir = tmp_path / "docs" / "value-monitor" / "hypecore" / "data"
        poc_dir.mkdir(parents=True, exist_ok=True)
        (poc_dir / "POLICYB_SELL_poc.json").write_text(json.dumps({
            "monthly": [{"stage": 2, "rev_yoy": -5.0, "rule40": 15.0}]
        }), encoding="utf-8")
        valuation = {
            "upside_percent": 30.0,
            "components": {"diluted_shares": None},
            "fcf_base": {"base_fcf": 1_000_000},
            "financial_health": {},
            "fcf_estimation": {
                "applied": True,
                "estimated_fcf": 600_000,  # fcf_est < fcf_base*0.8 → sell_funda
                "divergence_warning": "",
            },
            "fcf_outlier": {
                "detected": True,
                "transient_evidence": {"found": False},
            },
        }
        result = pipe._compute_tanuki_score("POLICYB_SELL", valuation)
        assert result["score"] == "SELL"

    def test_policy_a_and_b_mutually_exclusive(self, tmp_path):
        """fcf_estimation.applied=False（Policy A対象）のときPolicy Bは発火しない"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        valuation = {
            "upside_percent": -5.0,
            "components": {"diluted_shares": None},  # fcf_floor_applied未設定 → Policy A発火なし
            "fcf_base": {"base_fcf": 500_000_000},
            "financial_health": {},
            "fcf_estimation": {"applied": False, "divergence_warning": ""},
            "fcf_outlier": {
                "detected": True,
                "transient_evidence": {"found": False},  # Policy Bなら本来LOW相当の条件
            },
        }
        result = pipe._compute_tanuki_score("POLICYAB_EXCL", valuation)
        # Policy Aもapplied=FalseでfloorはunsetなのでLOW判定されず、Policy Bもapplied=Falseで対象外
        assert result["score"] == "HOLD"


class TestAnalyzeFcfOutlierDeviationPct:
    """DCF-REL-SYNC-1: analyze_fcf_outlier()のdeviation_pctフィールドのテスト"""

    @staticmethod
    def _import_analyze_fcf_outlier():
        from calculator.adjustments import analyze_fcf_outlier
        return analyze_fcf_outlier

    def test_deviation_large_populates_deviation_pct(self):
        """rule=deviation_large型はnote文字列と同一の乖離%を数値で保持する（FLYW型: 215%乖離）"""
        analyze_fcf_outlier = self._import_analyze_fcf_outlier()
        fcf_list = [163_819_000] + [52_000_000] * 4
        result = analyze_fcf_outlier(
            ticker="FLYW_TEST", fcf_list=fcf_list, fcf_5yr_avg=52_000_000,
            cv=0.3, fiscal_year_of_latest=2025, eps_data_dir="",
        )
        assert result.rule == "deviation_large"
        assert result.deviation_pct == pytest.approx(215.0, abs=1.0)

    def test_latest_negative_deviation_pct_is_none(self):
        """rule=latest_negative型（FCFマイナス）は乖離%の概念が成立しないためNone"""
        analyze_fcf_outlier = self._import_analyze_fcf_outlier()
        fcf_list = [-100_000_000] + [50_000_000] * 4
        result = analyze_fcf_outlier(
            ticker="NEG_TEST", fcf_list=fcf_list, fcf_5yr_avg=50_000_000,
            cv=0.3, fiscal_year_of_latest=2025, eps_data_dir="",
        )
        assert result.rule == "latest_negative"
        assert result.deviation_pct is None

    def test_no_outlier_deviation_pct_is_none(self):
        """外れ値なし（detected=False）の場合もdeviation_pctはNone"""
        analyze_fcf_outlier = self._import_analyze_fcf_outlier()
        fcf_list = [50_000_000] * 5
        result = analyze_fcf_outlier(
            ticker="FLAT_TEST", fcf_list=fcf_list, fcf_5yr_avg=50_000_000,
            cv=0.3, fiscal_year_of_latest=2025, eps_data_dir="",
        )
        assert result.detected is False
        assert result.deviation_pct is None

    def test_to_dict_includes_deviation_pct(self):
        """to_dict()の出力にdeviation_pctが含まれる"""
        analyze_fcf_outlier = self._import_analyze_fcf_outlier()
        fcf_list = [163_819_000] + [52_000_000] * 4
        result = analyze_fcf_outlier(
            ticker="FLYW_TEST2", fcf_list=fcf_list, fcf_5yr_avg=52_000_000,
            cv=0.3, fiscal_year_of_latest=2025, eps_data_dir="",
        )
        d = result.to_dict()
        assert "deviation_pct" in d
        assert d["deviation_pct"] == pytest.approx(215.0, abs=1.0)


# ─────────────────────────────────────────────
# 17. 汎用性検証: 新規銘柄自動適用 (回帰防止)
#
#     「実績FCF全年マイナス・RPO比率0.1・上場2年・ROEに損失年含む」
#     相当の新規銘柄に対して全修正が自動適用されることを確認する。
#     個別銘柄のif分岐ではなく汎用ロジックが駆動することを証明する。
# ─────────────────────────────────────────────

_SEC_READER_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SEC_READER_DIR not in sys.path:
    sys.path.insert(0, _SEC_READER_DIR)
from common.sec_data.reader import SECReader  # type: ignore[import]


class TestNewTickerIntegration:
    """
    汎用性検証: 「実績FCF全年マイナス・RPO比率0.10・上場2年・ROEに損失年含む」
    相当の新規銘柄 (NEWCO) に対し、全修正が特定銘柄ハードコードなしで
    自動適用されることを確認する回帰防止テスト群。
    """

    @staticmethod
    def _make_neg_fcf_valuation(upside: float = -5.0) -> dict:
        """実績FCF全年マイナス新規銘柄のバリュエーション dict（_minimal_valuation ベース）"""
        val = _minimal_valuation(upside=upside)
        # FCF全年マイナス → revenue_floor適用 → FCF_Reliability=LOW
        val["fcf_estimation"] = {"applied": False, "sector": "Technology"}
        val["components"].update({
            "fcf_base_used":    900_000_000,
            "fcf_floor_applied": 900_000_000,   # > 0 → DCF_Reliability=LOW
            "fcf_5yr_avg":     -6_000_000_000,  # 実績avg negative
            "fcf_base_method": "avg_5yr",
            "fcf_list_raw":    [-8e9, -6e9, -4e9],
        })
        # RICE未計算 → Matrix④ を使わせる
        val["rice"] = {"available": False, "note": ""}
        return val

    def test_dcf_reliability_low_shown_in_report_for_negative_fcf_ticker(self, tmp_path):
        """新規銘柄: 実績FCF全年マイナス → DCF_Reliability=LOW が report に自動表示される"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = self._make_neg_fcf_valuation()
        score_data = {"score": "WATCH", "funda_score": 25, "score_comment": "DCF信頼性LOW"}
        report = pipe._generate_report("NEWCO", val, score_data, _minimal_extra())
        assert "DCF_Reliability: LOW" in report

    def test_rpo_ratio_below_threshold_auto_excluded_for_new_ticker(self):
        """新規銘柄: RPO/Revenue=0.10 → whitelist未登録の場合に自動的に rpo_pv=0 かつ除外理由が設定される"""
        result = adjust_rpo(
            rpo=5_000_000_000,         # RPO $5B
            sector="Technology",
            ticker="NEWCO",             # whitelist未登録
            industry="Software - Application",
            op_margin=0.25,
            rev_ttm=50_000_000_000,    # Revenue $50B → ratio=0.10 < 0.30
        )
        assert result.rpo_pv == 0.0
        assert "not applied" in result.exclusion_reason
        assert "0.10" in result.exclusion_reason

    def test_matrix4_uses_actual_negative_fcf_margin_for_new_ticker(self, tmp_path):
        """新規銘柄: rice未計算 → Matrix④ が fcf_history の実績マイナスマージンを使う"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = self._make_neg_fcf_valuation(upside=-5.0)
        extra = _minimal_extra()
        extra["fcf_history"] = [{"fcf": -500_000_000, "fcf_margin": -125.0, "year": 2024}]
        score_data = {"score": "WATCH", "funda_score": 25, "score_comment": "test"}
        report = pipe._generate_report("NEWCO", val, score_data, extra)
        assert "④キャッシュ創出力系" in report
        assert "FCF_Margin = -125.0%" in report

    def test_roe_avg_includes_negative_year_in_calculation(self, tmp_path):
        """新規銘柄: reader.py が損失年度を除外せず全期間平均でROEを算出する"""
        sec_dir = tmp_path / "NEWCO"
        sec_dir.mkdir()
        # 2022: -20%、2023: -10%、2024: +6% → 平均 -8%
        for yr, ni in [(2022, -200_000_000), (2023, -100_000_000), (2024, 60_000_000)]:
            (sec_dir / f"annual_{yr}.json").write_text(json.dumps({
                "pl": {"net_income": ni},
                "bs": {"stockholders_equity": 1_000_000_000},
            }), encoding="utf-8")

        reader = SECReader(data_dir=str(tmp_path))
        avg, years_used, _ = reader.get_roe_avg_detail("NEWCO", years=10)

        assert years_used == 3, f"損失年を含む全3年が計算に使われるべき (got {years_used})"
        assert avg < 0, f"損失年込み平均はマイナスになるべき (got {avg:.2%})"
        assert abs(avg - (-0.08)) < 0.005, f"平均ROE ≈ -8% のはず (got {avg:.2%})"

    def test_watch_score_auto_applied_for_negative_fcf_new_ticker(self, tmp_path):
        """新規銘柄: FCF全年マイナス(floor適用) → SCORE が WATCH に自動丸めされる"""
        pipe = _make_pipe(tmp_path)
        _write_stonks_json(tmp_path, {})
        valuation = {
            "upside_percent": -5.0,
            "components": {
                "fcf_floor_applied": 900_000_000,  # LOW判定トリガー
                "diluted_shares": None,
            },
            "fcf_base": {"base_fcf": 900_000_000},
            "financial_health": {},
            "fcf_estimation": {},
        }
        result = pipe._compute_tanuki_score("NEWCO", valuation)
        assert result["score"] == "WATCH"
        assert "LOW" in result["score_comment"]


# ─────────────────────────────────────────────
# 18. BUG-MATRIX4-1追補: fcf_history末尾None銘柄のMatrix④回帰防止
#
#     上場後まもない / SEC年次未取得年が末尾にある銘柄（RCATパターン）で
#     fcf_history[-1]がNoneのとき、実績マイナスのマージンを正しく採用し
#     revenue_floor正値にフォールバックしないことを確認する。
# ─────────────────────────────────────────────

class TestMatrix4TailNoneRegression:
    """
    BUG-MATRIX4-1追補:
    fcf_history の末尾エントリーが fcf=None/fcf_margin=None の銘柄(RCATパターン)で
    Matrix④ Key_Metric_Y が実績マイナスマージンを採用することを保証する回帰防止テスト。
    """

    @staticmethod
    def _make_tail_none_valuation(upside: float = -67.0) -> dict:
        """末尾None + floor適用 のバリュエーション dict（RCATパターン）"""
        val = _minimal_valuation(upside=upside)
        val["fcf_estimation"] = {"applied": False, "sector": "Technology"}
        val["components"].update({
            "fcf_base_used":     41_393_459.0,   # revenue_floor適用後の正値
            "fcf_floor_applied": 41_393_459.0,   # > 0 → DCF_Reliability=LOW
            "fcf_5yr_avg":      -16_000_000.0,
            "fcf_base_method":  "avg_5yr",
            "fcf_list_raw":     [-1.4e6, -16.4e6, -31.6e6],
            "latest_revenue":    101_800_000.0,
        })
        val["rice"] = {"available": False, "note": ""}
        return val

    def test_matrix4_tail_none_uses_last_real_margin(self, tmp_path):
        """末尾None銘柄: reversed()で2023年(-319.3%)を採用、+40.7%にフォールバックしない"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = self._make_tail_none_valuation()
        extra = _minimal_extra()
        # 2024/2025 は fcf=None/fcf_margin=None（SEC未取得）、2023 が最後の実績
        extra["fcf_history"] = [
            {"year": 2021, "fcf": -1_399_001,  "fcf_margin": -28.0},
            {"year": 2022, "fcf": -16_383_009, "fcf_margin": -254.8},
            {"year": 2023, "fcf": -31_649_633, "fcf_margin": -319.3},
            {"year": 2024, "fcf": None,         "fcf_margin": None},
            {"year": 2025, "fcf": None,         "fcf_margin": None},
        ]
        score_data = {"score": "WATCH", "funda_score": 25, "score_comment": "DCF信頼性LOW"}
        report = pipe._generate_report("RCATLIKE", val, score_data, extra)

        # 実績マイナスマージン(2023年=-319.3%)が使われること
        assert "FCF_Margin = -319.3%" in report, (
            "末尾NoneのときKey_Metric_Yが revenue_floor正値(+40.7%)を使うリグレッション"
        )
        # 高FCFラベルになっていないこと
        assert "割高×高FCF" not in report
        assert "低FCF" in report

    def test_matrix4_all_none_floor_applied_shows_na(self, tmp_path):
        """全年None + floor適用: revenue_floor正値でなくN/Aを表示する"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = self._make_tail_none_valuation()
        extra = _minimal_extra()
        # 全年 None（理論上の極端ケース）
        extra["fcf_history"] = [
            {"year": 2024, "fcf": None, "fcf_margin": None},
            {"year": 2025, "fcf": None, "fcf_margin": None},
        ]
        score_data = {"score": "WATCH", "funda_score": 25, "score_comment": "DCF信頼性LOW"}
        report = pipe._generate_report("ALLNONE", val, score_data, extra)

        # floor適用時は revenue_floor正値でなく N/A になること
        assert "FCF_Margin = N/A" in report
        # 40.7% のような正値が出ていないこと
        import re
        m = re.search(r'FCF_Margin = ([+-]?\d+\.?\d*)%', report)
        assert m is None, f"floor適用時に正値が表示された: {m.group(0)}"


# ─────────────────────────────────────────────
# 19. 回帰防止: Fix1/Fix2/Fix3 (2026-06-11 バグ修正)
#
#   Fix1: scenario_valuations を growth source に関わらず全銘柄で計算する
#   Fix2: segment_config.json 未登録銘柄に segment_configured=False をセット
#   Fix3: Matrix② 定義文の ROE 年数を roe_years_used から動的に生成する
# ─────────────────────────────────────────────

class TestScenarioValuationsAlwaysRendered:
    """Fix1 回帰防止: scenario_valuations が None のとき BEAR/BULL が $0.00 になるリグレッション検出"""

    def test_bear_bull_non_zero_when_scenario_valuations_populated(self, tmp_path):
        """scenario_valuations に BEAR/BULL が設定されていれば report に非ゼロ IV が表示される"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = _minimal_valuation(upside=30.0)
        val["scenario_valuations"] = {
            "bear": {"growth_rate": 0.15, "intrinsic_value_per_share": 110.0},
            "base": {"growth_rate": 0.25, "intrinsic_value_per_share": 140.0},
            "bull": {"growth_rate": 0.35, "intrinsic_value_per_share": 175.0},
        }
        score_data = _minimal_score_data()
        report = pipe._generate_report("SCENTEST", val, score_data, _minimal_extra())

        # BEAR/BULL の IV が 0.00 でないこと（旧バグでは segment_weighted 以外は $0.00 になっていた）
        assert "BEAR: Growth=15.0%, IV=$110.00" in report, \
            "BEAR IV が正しく表示されていない (segment_weighted 以外でシナリオが計算されないリグレッション)"
        assert "BULL: Growth=35.0%, IV=$175.00" in report, \
            "BULL IV が正しく表示されていない"

    def test_bear_bull_show_zero_when_scenario_valuations_absent(self, tmp_path):
        """scenario_valuations が None のときは BEAR/BULL が $0.00 になること（旧バグ再現・検出用）"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = _minimal_valuation(upside=30.0)
        val["scenario_valuations"] = None  # 旧バグ: segment_weighted 以外はここが None だった
        score_data = _minimal_score_data()
        report = pipe._generate_report("SCENTEST_NULL", val, score_data, _minimal_extra())

        assert "BEAR: Growth=0.0%, IV=$0.00" in report
        assert "BULL: Growth=0.0%, IV=$0.00" in report


class TestSegmentConfiguredFalseForUnconfiguredTicker:
    """Fix2 回帰防止: segment_config.json 未登録銘柄に segment_configured=False がセットされること"""

    def test_absent_ticker_gets_segment_configured_false(self, tmp_path):
        """segment_config.json に存在しない銘柄は segment_configured=False になる"""
        pipe = _make_pipe(tmp_path)
        # repo_root/config/segment_config.json を作成（OTHERTICKER のみ登録）
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "segment_config.json").write_text(
            json.dumps({"OTHERTICKER": {"segments": {"Cloud": {"weight": 1.0, "growth": 0.15}}}}),
            encoding="utf-8",
        )
        valuation = {"components": {"latest_revenue": 1_000_000_000}}
        result = pipe._load_extra_data("NEWTICKER", valuation)

        assert result.get("segment_configured") is False, (
            "segment_config.json 未登録銘柄で segment_configured=False がセットされていない"
            " (旧バグ: キーが存在せず extra.get('segment_configured', True) が True になっていた)"
        )

    def test_registered_ticker_gets_segment_configured_true(self, tmp_path):
        """segment_config.json に登録済みの銘柄は segment_configured=True になる"""
        pipe = _make_pipe(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "segment_config.json").write_text(
            json.dumps({"REGTICKER": {"segments": {"Cloud": {"weight": 1.0, "growth": 0.20}}}}),
            encoding="utf-8",
        )
        valuation = {"components": {"latest_revenue": 5_000_000_000}}
        result = pipe._load_extra_data("REGTICKER", valuation)

        assert result.get("segment_configured") is True, \
            "登録済み銘柄で segment_configured=True がセットされていない"


class TestMatrix2ROEDefinitionDynamicYear:
    """Fix3 回帰防止: Matrix② 定義文の ROE 年数が roe_years_used から動的に生成されること"""

    @staticmethod
    def _make_sector_excluded_valuation(roe_years_used: int = 6) -> dict:
        """Matrix②（セクター除外）を使うバリュエーション dict"""
        val = _minimal_valuation(upside=20.0)
        val["rice"] = {
            "available": False,
            "note": "セクター除外",
            "base": {},
            "bear": {},
            "bull": {},
        }
        val["components"]["roe_10yr_avg"] = 0.18
        val["components"]["roe_years_used"] = roe_years_used
        return val

    def test_matrix2_definition_uses_roe_years_used(self, tmp_path):
        """roe_years_used=6 のとき Matrix② 定義文に ROE_6yr_avg が含まれる"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = self._make_sector_excluded_valuation(roe_years_used=6)
        score_data = _minimal_score_data()
        report = pipe._generate_report("ROE6TEST", val, score_data, _minimal_extra())

        assert "Matrix②(収益性系): Y=ROE_6yr_avg, X=Deviation Rate" in report, \
            "roe_years_used=6 のとき ROE_6yr_avg が表示されるべき (旧バグ: 固定 ROE_10yr_avg)"
        assert "ROE_10yr_avg" not in report.split("[2. MATRIX POSITION]")[1].split("[3.")[0], \
            "roe_years_used=6 なのに ROE_10yr_avg が残っている"

    def test_matrix2_definition_default_10yr(self, tmp_path):
        """roe_years_used が未設定のとき Matrix② 定義文に ROE_10yr_avg が含まれる"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = self._make_sector_excluded_valuation()
        val["components"].pop("roe_years_used", None)  # キーを削除してデフォルト動作を確認
        score_data = _minimal_score_data()
        report = pipe._generate_report("ROE10DEFAULT", val, score_data, _minimal_extra())

        assert "Matrix②(収益性系): Y=ROE_10yr_avg, X=Deviation Rate" in report, \
            "roe_years_used 未設定のとき ROE_10yr_avg がデフォルト値として表示されるべき"


# ─────────────────────────────────────────────
# 20. 回帰防止: SEC-REV-FINTECH-1 (2026-06-11)
#
#   金融セクター銘柄(SOFI等)で parser.py が狭義 revenue タグ
#   (RevenueFromContract...) を採用し annual revenue が過小になる問題。
#   quarterly.py の TICKER_RESTRICTIONS[ticker]["revenue_concept"] で
#   指定されたタグのみを使うことで広義 revenue を採用する。
# ─────────────────────────────────────────────

class TestFinancialSectorRevenueParsing:
    """
    SEC-REV-FINTECH-1 回帰防止:
    TICKER_RESTRICTIONS に revenue_concept が設定されている銘柄では
    parser.py が指定タグのみを使って annual revenue を取得することを保証する。
    """

    def test_revenue_concept_override_uses_single_tag(self, tmp_path):
        """revenue_concept 指定銘柄では指定タグのみが使われ広義 revenue が採用される"""
        import sys
        sys.path.insert(0, str(tmp_path))

        from common.sec_data.parser import SECParser
        from common.sec_data.quarterly import TICKER_RESTRICTIONS

        # TICKER_RESTRICTIONS に revenue_concept が登録されていること
        assert "SOFI" in TICKER_RESTRICTIONS, "SOFI が TICKER_RESTRICTIONS に未登録"
        assert "revenue_concept" in TICKER_RESTRICTIONS["SOFI"], \
            "SOFI の revenue_concept が TICKER_RESTRICTIONS に未設定"
        override_concept = TICKER_RESTRICTIONS["SOFI"]["revenue_concept"]
        assert override_concept == "RevenuesNetOfInterestExpense"

        # parser が SOFI の company_facts.json を読んで正しい revenue を返すこと
        # (実際のファイルが存在する場合のみテスト)
        import os
        facts_path = os.path.join(
            os.path.dirname(__file__), "..", "common", "sec_data", "data", "SOFI", "company_facts.json"
        )
        if not os.path.exists(facts_path):
            return  # CI 環境でファイルがない場合はスキップ

        p = SECParser()
        result = p.parse_company_facts("SOFI")
        assert result is not None

        # FY2025 の revenue が RevenuesNetOfInterestExpense の値 ($3.61B) に近いこと
        # (RevenueFromContractWithCustomer の狭義値 $619M ではないこと)
        fy2025_rev = result["annual"].get(2025, {}).get("pl", {}).get("revenue")
        assert fy2025_rev is not None, "FY2025 revenue が None"
        assert fy2025_rev > 1_000_000_000, (
            f"SOFI FY2025 revenue = ${fy2025_rev/1e9:.2f}B が $1B 未満 "
            f"(狭義 revenue タグ ${619e6/1e9:.2f}B が採用されるリグレッション)"
        )

    def test_revenue_concept_not_applied_to_normal_ticker(self, tmp_path):
        """revenue_concept 未設定銘柄は通常の MERGE_ALL_TAGS 動作を使う"""
        from common.sec_data.quarterly import TICKER_RESTRICTIONS

        # AAPL には revenue_concept が設定されていないこと
        aapl_restrictions = TICKER_RESTRICTIONS.get("AAPL", {})
        assert "revenue_concept" not in aapl_restrictions, \
            "AAPL に revenue_concept が誤って設定されている"

    def test_ticker_restrictions_revenue_concept_values_are_valid_xbrl_tags(self):
        """TICKER_RESTRICTIONS の revenue_concept 値が有効な XBRL タグ形式であること"""
        from common.sec_data.quarterly import TICKER_RESTRICTIONS
        from common.sec_data.parser import SECParser

        valid_tags = set(SECParser.XBRL_MAPPING.get("revenue", []))
        for ticker, restrictions in TICKER_RESTRICTIONS.items():
            concept = restrictions.get("revenue_concept")
            if concept:
                assert concept in valid_tags, (
                    f"{ticker}: revenue_concept='{concept}' が "
                    f"SECParser.XBRL_MAPPING['revenue'] に含まれていない "
                    "(parser.py が採用できないタグが指定されている)"
                )


# =============================================================================
# Section 21: BUG-NETDEBT-2 LongTermDebt二重計上修正 回帰テスト
# =============================================================================

class TestLongTermDebtPriorityNoncurrent:
    """BUG-NETDEBT-2: LongTermDebt (total) と LongTermDebtCurrent の二重計上防止"""

    def test_xbrl_mapping_priority_noncurrent_first(self):
        """XBRL_MAPPING の long_term_debt は LongTermDebtNoncurrent が最優先"""
        from common.sec_data.parser import SECParser

        priority = SECParser.XBRL_MAPPING["long_term_debt"]
        assert priority[0] == "LongTermDebtNoncurrent", (
            f"long_term_debt[0]={priority[0]!r} should be 'LongTermDebtNoncurrent'. "
            "BUG-NETDEBT-2: LongTermDebt (total) が先頭だと LongTermDebtCurrent との二重計上が発生する"
        )
        assert "LongTermDebt" in priority, "LongTermDebt フォールバックが priority リストに必要"
        # LongTermDebt は LongTermDebtNoncurrent より後ろ
        assert priority.index("LongTermDebt") > priority.index("LongTermDebtNoncurrent"), \
            "LongTermDebt は LongTermDebtNoncurrent より後ろに位置すること"

    def test_short_term_debt_uses_current_tag(self):
        """short_term_debt は LongTermDebtCurrent タグを持つこと（total との分離確認）"""
        from common.sec_data.parser import SECParser

        st_priority = SECParser.XBRL_MAPPING.get("short_term_debt", [])
        assert "LongTermDebtCurrent" in st_priority, \
            "short_term_debt mapping に LongTermDebtCurrent がない"

    def test_docn_total_debt_corrected(self):
        """DOCN の annual JSON で Total_Debt が是正されていること (BUG-NETDEBT-2 後)"""
        import os, json

        annual_path = os.path.join(
            os.path.dirname(__file__), "..", "common", "sec_data", "data", "DOCN", "annual.json"
        )
        if not os.path.exists(annual_path):
            return  # データファイル非存在時はスキップ

        with open(annual_path, encoding="utf-8") as f:
            data = json.load(f)

        # FY2024 の Total_Debt を確認（LTD_total+LTDcurrent の二重計上なら ~$1.62B になる）
        fy2024 = data.get("2024", {})
        lt = fy2024.get("bs", {}).get("long_term_debt")
        st = fy2024.get("bs", {}).get("short_term_debt", 0) or 0
        if lt is None:
            return  # データ構造が異なる場合はスキップ

        total = lt + st
        assert total < 1_500_000_000, (
            f"DOCN FY2024 Total_Debt=${total/1e9:.2f}B が $1.5B 超 "
            "— BUG-NETDEBT-2 が再発している可能性 (修正後は ~$1.30B が期待値)"
        )


# =============================================================================
# Section 22: BUG-REV-SPAC-1 / A-2-TTM 回帰テスト (2026-06-12)
# =============================================================================

class TestIonqRevenueSPACBug:
    """BUG-REV-SPAC-1: IONQの2022年10-K Revenuesタグ($1,235M)誤採用防止"""

    def test_ionq_revenue_concept_restriction_defined(self):
        """IONQ が TICKER_RESTRICTIONS に revenue_concept を持つこと"""
        from common.sec_data.quarterly import TICKER_RESTRICTIONS

        assert "IONQ" in TICKER_RESTRICTIONS, "IONQ が TICKER_RESTRICTIONS に未登録"
        assert "revenue_concept" in TICKER_RESTRICTIONS["IONQ"], \
            "IONQ の revenue_concept が TICKER_RESTRICTIONS に未設定"
        assert TICKER_RESTRICTIONS["IONQ"]["revenue_concept"] == \
            "RevenueFromContractWithCustomerExcludingAssessedTax", \
            "IONQ の revenue_concept が期待値と異なる"

    def test_ionq_annual_2022_revenue_corrected(self):
        """IONQ annual_2022.json の revenue が $1,235M ではなく ~$11M であること"""
        import os, json

        annual_path = os.path.join(
            os.path.dirname(__file__), "..", "common", "sec_data", "data", "IONQ", "annual_2022.json"
        )
        if not os.path.exists(annual_path):
            return

        with open(annual_path, encoding="utf-8") as f:
            data = json.load(f)

        rev = data.get("pl", {}).get("revenue")
        assert rev is not None, "IONQ annual_2022.json に revenue が存在しない"
        assert rev < 100_000_000, (
            f"IONQ 2022 revenue=${rev/1e6:.1f}M が $100M 超 "
            "— BUG-REV-SPAC-1 が再発している可能性 (正しい値は ~$11M)"
        )

    def test_ionq_fcf_margin_2022_not_anomalous(self):
        """IONQ FCF_Margin 2022 が他年と同程度の桁であること (孤立年でないこと)"""
        import os, json

        sec_dir = os.path.join(
            os.path.dirname(__file__), "..", "common", "sec_data", "data", "IONQ"
        )
        if not os.path.exists(sec_dir):
            return

        margins = {}
        for yr in [2021, 2022, 2023, 2024, 2025]:
            p = os.path.join(sec_dir, f"annual_{yr}.json")
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            rev = d.get("pl", {}).get("revenue") or 0
            fcf = d.get("cf", {}).get("free_cash_flow")
            if fcf is not None and rev > 0:
                margins[yr] = abs(fcf / rev * 100)

        if 2022 not in margins or len(margins) < 3:
            return

        other_margins = [v for y, v in margins.items() if y != 2022]
        avg_other = sum(other_margins) / len(other_margins)
        margin_2022 = margins[2022]
        assert margin_2022 > avg_other / 100, (
            f"IONQ FCF_Margin 2022 ({margin_2022:.1f}%) が他年平均 ({avg_other:.1f}%) の"
            "1/100未満 — BUG-REV-SPAC-1 型の孤立年異常が再発している可能性"
        )


class TestTTMTerminologyDistinction:
    """A-2-TTM: TTM_YoY_Growth (実績) と CAGR_max (成長モデル判定指標) の区別
    注意: _gs は test_pipeline_logic.py 先頭で import された本物の growth_sanity モジュール。
          sys.modules["growth_sanity"] は MagicMock に差し替え済みのため _gs を直接使う。
    """

    def test_growth_model_reason_no_bare_ttm_in_median_label(self):
        """中央値モデル reason に 'TTM' を単独使用しないこと (CAGR_max= で表示)"""
        # cagr_3yr < 50%・cagr_5yr < 50% のケース → 中央値モデル
        result = _gs.check_growth_sanity(
            ticker="TEST_MEDIAN",
            phase1_growth=0.15,
            annual_revenues=[100e6, 110e6, 120e6, 135e6, 150e6],  # ~11% CAGR
            ttm_actual=0.15,
        )
        reason = result.get("growth_model_reason", "")
        model = result.get("growth_model")

        if model == "median":
            # "CAGR_max=" で始まる形式に変わっているはず
            assert not reason.startswith("TTM"), (
                f"中央値モデルの reason='{reason}' が 'TTM' で始まる "
                "(旧形式 'TTMxx%のため中央値...' → 新形式 'CAGR_max=xx%のため...' に変更すべき)"
            )

    def test_growth_model_decay_uses_cagr_max_label_when_cagr_triggers(self):
        """CAGR > 50% で逓減モデルが発動する場合 reason に 'CAGR_max' が含まれること"""
        # IONQ修正後相当: cagr_3yr ≈ 127% が逓減トリガー、phase1_growth=15%
        result = _gs.check_growth_sanity(
            ticker="TEST_IONQ",
            phase1_growth=0.15,
            annual_revenues=[2.1e6, 11.1e6, 22.0e6, 43.1e6, 130.0e6],
            ttm_actual=0.15,
        )
        model = result.get("growth_model")
        reason = result.get("growth_model_reason", "")

        assert model == "decay", f"逓減モデルが発動されるべき (actual model={model}, reason={reason})"
        assert "CAGR_max" in reason, (
            f"reason='{reason}' に 'CAGR_max' が含まれない "
            "(CAGR_3yr>50%が逓減トリガーのため CAGR_max= で表示すべき)"
        )
        assert "TTM_YoY" not in reason, (
            f"reason='{reason}' に 'TTM_YoY' が含まれる "
            "(CAGR起動の逓減モデルで TTM_YoY ラベルは不正確)"
        )


# =====================================================================
# Section 23: BUG-NETDEBT-5 回帰テスト
# ST_Investの期ズレ修正: CashはBUG-NETDEBT-1で最新四半期値に更新済みだが
# ST_Investはannual年次のままだったバグ。最新quarterly_*.jsonのbs値に上書き。
# =====================================================================

class TestSTInvestQuarterlyOverride:
    """BUG-NETDEBT-5: ST_Investが最新四半期bsから上書きされること

    IONQ FY2025 annual: ST_Invest=$1,361M
    IONQ Q1 2026 quarterly: ST_Invest=$1,539M (→ 修正後の正値)
    修正後 Net_Debt: -$1.85B → -$2.03B
    """

    def test_ionq_st_invest_uses_quarterly_value(self):
        """IONQ: latest.json の ST_Invest が quarterly_2026Q1 の値 ($1,539M) であること"""
        import json, os
        latest_path = os.path.join(
            os.path.dirname(__file__), "..",
            "docs", "value-monitor", "tanuki_valuation", "data", "IONQ", "latest.json"
        )
        if not os.path.exists(latest_path):
            return
        with open(latest_path, encoding="utf-8") as f:
            latest = json.load(f)
        fh = latest.get("financial_health", {})
        st_invest = fh.get("short_term_investments", 0) or 0
        # quarterly_2026Q1 のST_Invest = $1,539,932,000
        # annual_2025 のST_Invest      = $1,361,291,000 (旧バグ値)
        assert st_invest > 1_400_000_000, (
            f"IONQ ST_Invest={st_invest/1e6:.0f}M が年次値($1,361M)に近い。"
            "BUG-NETDEBT-5: quarterly値($1,539M)で上書きされていない可能性"
        )

    def test_ionq_net_debt_corrected(self):
        """IONQ: Net_Debt が -$2.03B 近辺 (旧バグ値 -$1.85B でないこと)"""
        import json, os
        latest_path = os.path.join(
            os.path.dirname(__file__), "..",
            "docs", "value-monitor", "tanuki_valuation", "data", "IONQ", "latest.json"
        )
        if not os.path.exists(latest_path):
            return
        with open(latest_path, encoding="utf-8") as f:
            latest = json.load(f)
        fh = latest.get("financial_health", {})
        net_debt = fh.get("net_debt")
        if net_debt is None:
            return
        # 正しいNet_Debt ≈ -$2.03B (旧バグ値は -$1.85B)
        assert net_debt < -1_900_000_000, (
            f"IONQ Net_Debt={net_debt/1e9:.2f}B が -$1.9B より大きい。"
            "BUG-NETDEBT-5: ST_Invest期ズレが再発している可能性"
        )

    def test_ionq_quarterly_st_invest_exists_and_differs_from_annual(self):
        """IONQ: 最新quarterlyのST_Investがannualと異なること(テスト前提確認)"""
        import json, os, glob as _glob
        sec_dir = os.path.join(
            os.path.dirname(__file__), "..", "common", "sec_data", "data", "IONQ"
        )
        ann_files = sorted(_glob.glob(os.path.join(sec_dir, "annual_*.json")))
        q_files   = sorted(_glob.glob(os.path.join(sec_dir, "quarterly_*.json")))
        if not ann_files or not q_files:
            return
        with open(ann_files[-1], encoding="utf-8") as f:
            ann_sti = json.load(f).get("bs", {}).get("short_term_investments", 0) or 0
        with open(q_files[-1], encoding="utf-8") as f:
            q_sti = json.load(f).get("bs", {}).get("short_term_investments", 0) or 0
        assert q_sti != ann_sti, (
            f"IONQ annual_ST_Invest={ann_sti/1e6:.0f}M == quarterly_ST_Invest={q_sti/1e6:.0f}M "
            "テストの前提が崩れた(期が一致するか値が同じ)"
        )


class TestRiceNegativeLabel:
    """RICE-3 回帰防止: OCF赤字で RICE < 0 のとき Matrix Label が 'N/A (OCF赤字)' になること"""

    def test_negative_rice_label_contains_ocf_loss(self, tmp_path):
        """rice.base.rice < 0 のとき Label が 'N/A (OCF赤字)' を含む"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = _minimal_valuation(upside=10.0)
        val["rice"] = {
            "available": True,
            "note": "",
            "base": {"rice": -0.55},
            "q": -0.25,
            "cf_conversion": 0.40,
            "wacc": 0.10,
            "bear": {"rice": -0.38},
            "bull": {"rice": -0.65},
        }
        score_data = _minimal_score_data()
        report = pipe._generate_report("NEGRICE", val, score_data, _minimal_extra())

        assert "N/A (OCF赤字)" in report, (
            "RICE < 0 のとき Matrix Label に 'N/A (OCF赤字)' が含まれていない"
            " (RICE-3 回帰: rice_efficiency が '低効率' に戻った可能性)"
        )

    def test_zero_rice_label_is_low_efficiency(self, tmp_path):
        """rice.base.rice == 0.0 は '低効率' (負値と境界を明確にする)"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = _minimal_valuation(upside=10.0)
        val["rice"] = {
            "available": True,
            "note": "",
            "base": {"rice": 0.0},
            "q": 0.0,
            "cf_conversion": 0.5,
            "wacc": 0.10,
            "bear": {},
            "bull": {},
        }
        score_data = _minimal_score_data()
        report = pipe._generate_report("ZERORICE", val, score_data, _minimal_extra())

        assert "低効率" in report, (
            "RICE == 0.0 のとき '低効率' が表示されていない (負値との境界が崩れた可能性)"
        )
        assert "N/A (OCF赤字)" not in report, (
            "RICE == 0.0 は '低効率' であり 'N/A (OCF赤字)' ではない"
        )

    def test_positive_rice_label_is_not_ocf_loss(self, tmp_path):
        """rice.base.rice > 0 は 'N/A (OCF赤字)' を含まない (正常系の非汚染確認)"""
        pipe = _make_pipe(tmp_path)
        pipe._eps_summary_cache = {}
        val = _minimal_valuation(upside=30.0)
        score_data = _minimal_score_data()
        report = pipe._generate_report("POSRICE", val, score_data, _minimal_extra())

        assert "N/A (OCF赤字)" not in report, (
            "RICE > 0 なのに 'N/A (OCF赤字)' ラベルが出現した (正常系への誤波及)"
        )


# =============================================================================
# Section 25: ANNUAL-FY-1 回帰テスト (2026-06-13)
# aggregate_annual が fiscal_year フィールドベースで集計すること
# 非12月FY企業で filing_date[:4] 年跨ぎ混合が発生しないことを保証
# =============================================================================

class TestAnnualFYConsistency:
    """ANNUAL-FY-1: annual.json の各年が単一FYの4Qで構成されること

    aggregate_annual の filing_date[:4] → fiscal_year フィールドへの変更により
    非12月FY企業（NVDA/AAPL/MSFT/INTU等）の年跨ぎFY混合を解消。
    """

    def test_aggregate_annual_uses_fiscal_year_field(self):
        """fiscal_year フィールドがあればそれを優先してグループ化すること"""
        from src.value.adjusted_eps_analyzer.pipeline import aggregate_annual

        # NVDA FY2026 (1月決算): Q1-Q4 全て fiscal_year=2026
        quarters_fy2026 = [
            {"gaap_net_income": 18e9, "net_adjustment_total": 1e9,
             "diluted_shares_used": 24.6e9, "adjusted_eps": 0.82,
             "filing_date": "2025-04-27", "fiscal_year": 2026, "quarter": 1, "adjustments": []},
            {"gaap_net_income": 26e9, "net_adjustment_total": 1.4e9,
             "diluted_shares_used": 24.5e9, "adjusted_eps": 1.14,
             "filing_date": "2025-07-27", "fiscal_year": 2026, "quarter": 2, "adjustments": []},
            {"gaap_net_income": 32e9, "net_adjustment_total": 1.5e9,
             "diluted_shares_used": 24.5e9, "adjusted_eps": 1.36,
             "filing_date": "2025-10-26", "fiscal_year": 2026, "quarter": 3, "adjustments": []},
            {"gaap_net_income": 43e9, "net_adjustment_total": 1.2e9,
             "diluted_shares_used": 24.5e9, "adjusted_eps": 1.81,
             "filing_date": "2026-01-25", "fiscal_year": 2026, "quarter": 4, "adjustments": []},
        ]
        # FY2025 Q4: filing_date=2025-01-26 → 旧ロジックでは year=2025 グループに混入
        quarters_fy2025_q4 = [
            {"gaap_net_income": 22e9, "net_adjustment_total": 1.0e9,
             "diluted_shares_used": 24.8e9, "adjusted_eps": 0.93,
             "filing_date": "2025-01-26", "fiscal_year": 2025, "quarter": 4, "adjustments": []},
        ]
        all_quarters = quarters_fy2025_q4 + quarters_fy2026

        result = aggregate_annual(all_quarters)
        fy2026 = next((r for r in result if r["year"] == "2026"), None)

        assert fy2026 is not None, "FY2026 が集計されていない"
        # FY2026 の4Q合計: (18+26+32+43)B + (1+1.4+1.5+1.2)B = 119B + 5.1B = 124.1B
        expected_adj_ni = (18 + 26 + 32 + 43 + 1 + 1.4 + 1.5 + 1.2) * 1e9
        assert abs(fy2026["adjusted_net_income"] - expected_adj_ni) < 1e9, (
            f"FY2026 adjusted_net_income={fy2026['adjusted_net_income']/1e9:.1f}B "
            f"が期待値 {expected_adj_ni/1e9:.1f}B と乖離 "
            "— fiscal_year ベース集計が機能していない可能性"
        )

        # FY2025 Q4 が FY2026 グループに混入していないこと
        fy2025 = next((r for r in result if r["year"] == "2025"), None)
        assert fy2025 is None, (
            "FY2025 が4件未満なのに集計されている（Q4のみのため正しくはスキップ）"
        )

    def test_aggregate_annual_fallback_without_fiscal_year(self):
        """fiscal_year フィールドが無い場合は filing_date[:4] にフォールバックすること"""
        from src.value.adjusted_eps_analyzer.pipeline import aggregate_annual

        quarters = [
            {"gaap_net_income": 10e9, "net_adjustment_total": 0.5e9,
             "diluted_shares_used": 10e9, "adjusted_eps": 1.05,
             "filing_date": "2025-03-31", "quarter": 1, "adjustments": []},
            {"gaap_net_income": 11e9, "net_adjustment_total": 0.5e9,
             "diluted_shares_used": 10e9, "adjusted_eps": 1.15,
             "filing_date": "2025-06-30", "quarter": 2, "adjustments": []},
            {"gaap_net_income": 12e9, "net_adjustment_total": 0.5e9,
             "diluted_shares_used": 10e9, "adjusted_eps": 1.25,
             "filing_date": "2025-09-30", "quarter": 3, "adjustments": []},
            {"gaap_net_income": 13e9, "net_adjustment_total": 0.5e9,
             "diluted_shares_used": 10e9, "adjusted_eps": 1.35,
             "filing_date": "2025-12-31", "quarter": 4, "adjustments": []},
        ]
        result = aggregate_annual(quarters)
        assert len(result) == 1, f"結果が1件でない: {len(result)}"
        assert result[0]["year"] == "2025", f"year が 2025 でない: {result[0]['year']}"

    def test_nvda_annual_json_fy_not_mixed(self):
        """NVDA annual.json の各 year エントリが単一FYの4Qで構成されること（年跨ぎ混合なし）"""
        import json, os

        annual_path = os.path.join(
            os.path.dirname(__file__), "..",
            "docs", "value-monitor", "adjusted_eps_analyzer", "data", "NVDA", "annual.json"
        )
        q_path = os.path.join(
            os.path.dirname(__file__), "..",
            "docs", "value-monitor", "adjusted_eps_analyzer", "data", "NVDA", "quarterly.json"
        )
        if not os.path.exists(annual_path) or not os.path.exists(q_path):
            return

        with open(annual_path, encoding="utf-8") as f:
            annual = json.load(f)
        with open(q_path, encoding="utf-8") as f:
            q_data = json.load(f)

        # quarterly.json の fiscal_year → year マッピングを構築
        fy_to_quarters = {}
        for q in q_data.get("quarters", []):
            fy = q.get("fiscal_year")
            if fy is not None:
                fy_to_quarters.setdefault(str(fy), []).append(q)

        for year_entry in annual.get("years", []):
            yr = year_entry["year"]
            qs_in_fy = fy_to_quarters.get(yr, [])
            if not qs_in_fy:
                continue  # quarterly.json に対応FYなし（古いデータ等）はスキップ

            # 各QのFYが全て yr と一致するか
            mixed = [q for q in qs_in_fy if str(q.get("fiscal_year", "")) != yr]
            assert not mixed, (
                f"NVDA annual.json year={yr} に異なる fiscal_year の四半期が混入: "
                f"{[q['filing_date'] for q in mixed]}"
            )


# ─────────────────────────────────────────────
# 20. DuPont分解 (TANUKI-ROE-3): _load_extra_data の dupont ブロック検証
#
#   BUG-DUPONT-1 / TANUKI-ROE-3 で追加した以下の挙動を検証する:
#   - 正常計算（NI/Revenue/Assets/Equity 全て正値）
#   - Equity<=0 銘柄は dupont キー自体が付与されない（除外）
#   - TTM Revenue < $15M 銘柄は dupont={"excluded": True, "reason": "revenue_too_small"}
#   - 単四半期NI集中（最大1Q/4Q合計 > 0.6）で reliability="LOW"
#   - |ROE|>100% となる極端値ケースでも roe_decomposed が正しく計算される
#     （表示バッジ自体は index.html 側のJSロジックでありPythonテスト対象外）
# ─────────────────────────────────────────────

def _write_dupont_ttm(tmp_path, ticker: str, ni_ttm: float, revenue_ttm: float,
                       quarters_used: int = 4, ttm_end: str = "2026-03-31") -> None:
    """common/sec_data/ttm/{ticker}_ttm_series.json を作成する"""
    ttm_dir = tmp_path / "common" / "sec_data" / "ttm"
    ttm_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "ticker": ticker,
        "series": [{
            "ttm_end": ttm_end,
            "flow": {
                "NetIncome": {"val": ni_ttm, "quarters_used": quarters_used, "missing": 0},
                "Revenue": {"val": revenue_ttm, "quarters_used": quarters_used, "missing": 0},
            },
        }],
    }
    (ttm_dir / f"{ticker}_ttm_series.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


def _write_dupont_quarterly_bs(tmp_path, ticker: str, total_assets: float, equity: float,
                                period: str = "2026Q1", filename: str = "quarterly_2026Q1.json") -> None:
    """common/sec_data/data/{ticker}/{filename} を作成する（DuPontのBS取得元）"""
    sec_dir = tmp_path / "common" / "sec_data" / "data" / ticker
    sec_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "ticker": ticker,
        "period": period,
        "bs": {"total_assets": total_assets, "stockholders_equity": equity},
    }
    (sec_dir / filename).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _write_dupont_normalized_ni(tmp_path, ticker: str, quarterly_ni: list) -> None:
    """common/sec_data/normalized/{ticker}_quarterly_normalized.json を作成する。
    quarterly_ni: [(end_date, val), ...] 直近4四半期分（reliability判定の単四半期集中チェック用）"""
    norm_dir = tmp_path / "common" / "sec_data" / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)
    fields_ni = [
        {"end": end, "start": "", "val": val, "is_annual": False}
        for end, val in quarterly_ni
    ]
    data = {"ticker": ticker, "fields": {"NetIncome": fields_ni}}
    (norm_dir / f"{ticker.upper()}_quarterly_normalized.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


class TestDuPontNormalCalculation:
    """正常計算ケース: NI/Revenue/Assets/Equity が全て正常値のとき DuPont3要素を正しく算出する"""

    def test_normal_case_computes_three_factors_correctly(self, tmp_path):
        pipe = _make_pipe(tmp_path)
        _write_dupont_ttm(tmp_path, "NORMALCO", ni_ttm=100_000_000, revenue_ttm=1_000_000_000)
        _write_dupont_quarterly_bs(tmp_path, "NORMALCO", total_assets=2_000_000_000, equity=500_000_000)

        result = pipe._load_extra_data("NORMALCO", {"components": {}})
        dp = result.get("dupont")

        assert dp is not None
        assert dp["net_margin"] == 0.1          # 100M / 1000M
        assert dp["asset_turnover"] == 0.5       # 1000M / 2000M
        assert dp["financial_leverage"] == 4.0   # 2000M / 500M
        assert dp["roe_decomposed"] == 0.2       # 0.1 * 0.5 * 4.0
        assert dp["dupont_bs_period"] == "2026Q1"
        assert "reliability" not in dp           # 単四半期集中データなし＝判定スキップ
        assert "excluded" not in dp


class TestDuPontEquityExclusion:
    """Equity<=0（債務超過）の銘柄は dupont キー自体が付与されない"""

    def test_negative_equity_excludes_dupont(self, tmp_path):
        pipe = _make_pipe(tmp_path)
        _write_dupont_ttm(tmp_path, "DEFICITCO", ni_ttm=50_000_000, revenue_ttm=500_000_000)
        _write_dupont_quarterly_bs(tmp_path, "DEFICITCO", total_assets=1_000_000_000, equity=-100_000_000)

        result = pipe._load_extra_data("DEFICITCO", {"components": {}})

        assert result.get("dupont") is None, (
            "Equity<=0 の銘柄で dupont が付与されている"
            "（ABBV/BKNG/DELL等の純資産マイナス銘柄は除外される設計）"
        )


class TestDuPontRevenueThresholdExclusion:
    """TANUKI-ROE-3: TTM Revenue < $15M の銘柄は excluded=True になる"""

    def test_revenue_below_15m_is_excluded(self, tmp_path):
        pipe = _make_pipe(tmp_path)
        _write_dupont_ttm(tmp_path, "TINYCO", ni_ttm=-10_000_000, revenue_ttm=12_000_000)
        _write_dupont_quarterly_bs(tmp_path, "TINYCO", total_assets=1_000_000_000, equity=900_000_000)

        result = pipe._load_extra_data("TINYCO", {"components": {}})

        assert result.get("dupont") == {"excluded": True, "reason": "revenue_too_small"}

    def test_revenue_at_15m_is_not_excluded(self, tmp_path):
        """境界値: $15M ちょうどは除外されない（< $15M のみが除外条件）"""
        pipe = _make_pipe(tmp_path)
        _write_dupont_ttm(tmp_path, "BOUNDARYCO", ni_ttm=1_000_000, revenue_ttm=15_000_000)
        _write_dupont_quarterly_bs(tmp_path, "BOUNDARYCO", total_assets=100_000_000, equity=50_000_000)

        result = pipe._load_extra_data("BOUNDARYCO", {"components": {}})

        dp = result.get("dupont")
        assert dp is not None
        assert dp.get("excluded") is not True


class TestDuPontReliabilityLowFlag:
    """単四半期NI集中（最大1Q ÷ 直近4Q合計 > 0.6）で reliability=LOW になる"""

    def test_single_quarter_concentration_sets_reliability_low(self, tmp_path):
        pipe = _make_pipe(tmp_path)
        # 直近4Q: 10M, 10M, 10M, 100M (合計130M) → 最大Q比率 100/130 ≈ 0.77 > 0.6
        _write_dupont_ttm(tmp_path, "LYFTLIKE", ni_ttm=130_000_000, revenue_ttm=200_000_000,
                           quarters_used=4, ttm_end="2026-03-31")
        _write_dupont_quarterly_bs(tmp_path, "LYFTLIKE", total_assets=400_000_000, equity=100_000_000)
        _write_dupont_normalized_ni(tmp_path, "LYFTLIKE", [
            ("2026-03-31", 10_000_000),
            ("2025-12-31", 100_000_000),  # 一過性要因（DTA等）を想定した単四半期集中
            ("2025-09-30", 10_000_000),
            ("2025-06-30", 10_000_000),
        ])

        result = pipe._load_extra_data("LYFTLIKE", {"components": {}})
        dp = result.get("dupont")

        assert dp is not None
        assert dp.get("reliability") == "LOW"
        assert dp.get("reliability_reason") == "単四半期NI集中（一過性要因の可能性）"

    def test_evenly_distributed_quarters_no_reliability_flag(self, tmp_path):
        """4Qが均等に分散していれば reliability フラグは付与されない"""
        pipe = _make_pipe(tmp_path)
        # 直近4Q: 25M ずつ均等(合計100M) → 最大Q比率 25/100 = 0.25 < 0.6
        _write_dupont_ttm(tmp_path, "EVENCO", ni_ttm=100_000_000, revenue_ttm=200_000_000,
                           quarters_used=4, ttm_end="2026-03-31")
        _write_dupont_quarterly_bs(tmp_path, "EVENCO", total_assets=400_000_000, equity=100_000_000)
        _write_dupont_normalized_ni(tmp_path, "EVENCO", [
            ("2026-03-31", 25_000_000),
            ("2025-12-31", 25_000_000),
            ("2025-09-30", 25_000_000),
            ("2025-06-30", 25_000_000),
        ])

        result = pipe._load_extra_data("EVENCO", {"components": {}})
        dp = result.get("dupont")

        assert dp is not None
        assert "reliability" not in dp


class TestDuPontExtremeRoeCalculation:
    """|ROE|>100% となる極端値ケースで roe_decomposed が正しく算出される
    （表示バッジ自体は index.html 側のJSロジックであり本テストはPython側の計算正当性のみ検証）"""

    def test_high_margin_high_leverage_produces_roe_over_100_percent(self, tmp_path):
        pipe = _make_pipe(tmp_path)
        # net_margin=0.5, asset_turnover=1.0, financial_leverage=5.0 → roe=2.5 (250%)
        _write_dupont_ttm(tmp_path, "EXTREMECO", ni_ttm=50_000_000, revenue_ttm=100_000_000)
        _write_dupont_quarterly_bs(tmp_path, "EXTREMECO", total_assets=100_000_000, equity=20_000_000)

        result = pipe._load_extra_data("EXTREMECO", {"components": {}})
        dp = result.get("dupont")

        assert dp is not None
        assert dp["roe_decomposed"] == 2.5
        assert abs(dp["roe_decomposed"]) > 1.0, (
            "|ROE|>100% ケースで roe_decomposed が想定通り算出されていない"
            "（index.html の isExtreme バッジ判定 Math.abs(roe_decomposed)>1.0 が依拠する値）"
        )


# ─────────────────────────────────────────────
# 21. TTM-NULL-1: ttm_calculator.py の val=None 防御テスト（PREVENT-3）
#
#     calc_ttm() に val=None のエントリを含む normalized dict を渡しても
#     TypeError が発生せず、None を 0 として合算することを確認する。
# ─────────────────────────────────────────────

class TestTTMNullValGuard:
    """TTM-NULL-1: e['val']=None 時に TypeError が起きないことを保証する"""

    def test_flow_field_with_none_val_no_type_error(self):
        """FLOW_FIELDS の entry に val=None が含まれても calc_ttm がクラッシュしない"""
        import importlib.util, os, sys as _sys
        ttm_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "common", "sec_data", "ttm_calculator.py")
        )
        spec = importlib.util.spec_from_file_location("ttm_calculator", ttm_path)
        ttm_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ttm_mod)

        normalized = {
            "fields": {
                "OCF": [
                    {"end": "2026-03-31", "start": "2026-01-01", "val": None, "is_annual": False},
                    {"end": "2025-12-31", "start": "2025-10-01", "val": 100.0, "is_annual": False},
                    {"end": "2025-09-30", "start": "2025-07-01", "val": 200.0, "is_annual": False},
                    {"end": "2025-06-30", "start": "2025-04-01", "val": 150.0, "is_annual": False},
                ]
            }
        }
        result = ttm_mod.calc_ttm("TESTCO", normalized)
        ocf = result.get("flow", {}).get("OCF", {}).get("val")
        assert ocf == 450.0, f"None を 0 として合算した結果が 450.0 になるはず (got {ocf})"

    def test_q4_synthetic_with_none_val_no_type_error(self):
        """implied Q4 合成で top3 に val=None エントリが含まれても TypeError が起きない"""
        import importlib.util, os
        ttm_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "common", "sec_data", "ttm_calculator.py")
        )
        spec = importlib.util.spec_from_file_location("ttm_calculator_q4", ttm_path)
        ttm_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ttm_mod)

        normalized = {
            "fields": {
                "Revenue": [
                    {"end": "2025-09-30", "start": "2025-07-01", "val": None, "is_annual": False},
                    {"end": "2025-06-30", "start": "2025-04-01", "val": None, "is_annual": False},
                    {"end": "2025-03-31", "start": "2025-01-01", "val": None, "is_annual": False},
                    {"end": "2025-12-31", "start": "2025-01-01", "val": 1000.0, "is_annual": True},
                ]
            }
        }
        try:
            ttm_mod.calc_ttm("TESTCO2", normalized)
        except TypeError as e:
            pytest.fail(f"val=None 時に TypeError が発生した: {e}")


# ─────────────────────────────────────────────
# 22. STONKS-DIV-1: analyzer.py のゼロ除算防御テスト（PREVENT-3）
#
#     r_start=0 / rev=0 / avg_past=0 のエッジケースで
#     ZeroDivisionError が発生しないことを確認する。
#     （コード上はすでにガード済み; このテストでガードの継続的動作を担保する）
# ─────────────────────────────────────────────

class TestStonksDivisionGuards:
    """STONKS-DIV-1: analyzer.py のゼロ除算ガードが有効であることを保証する"""

    @staticmethod
    def _load_analyzer():
        import importlib.util, os, sys as _sys
        path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "discover", "stonks-silo", "src", "analyzer.py")
        )
        mod_name = "stonks_analyzer_test"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        mod = importlib.util.module_from_spec(spec)
        _sys.modules[mod_name] = mod  # dataclass が cls.__module__ を解決できるよう登録
        spec.loader.exec_module(mod)
        return mod

    @staticmethod
    def _make_record(rev_san, net_income, assets=5_000_000, debt=2_000_000, equity=500_000, ocf=-100_000):
        return {
            "pl": {"revenue_sanitized": rev_san, "net_income": net_income,
                   "research_and_development": None, "selling_and_marketing": None,
                   "gross_profit": None},
            "bs": {"total_assets": assets, "total_debt": debt, "stockholders_equity": equity},
            "cf": {"ocf": ocf},
        }

    def test_lpr_rev_zero_returns_none(self):
        """rev_sanitized=0 でも StonksAnalyzer.analyze() が ZeroDivisionError を起こさないこと"""
        mod = self._load_analyzer()
        data = {
            "ticker": "ZEROREV",
            "years": [2024],
            "records": {2024: self._make_record(rev_san=0.0, net_income=-1_000_000,
                                                equity=-500_000)},
        }
        try:
            mod.StonksAnalyzer().analyze(data)
        except ZeroDivisionError as e:
            pytest.fail(f"rev=0 で ZeroDivisionError が発生した: {e}")

    def test_cagr_r_start_zero_returns_none(self):
        """4年前の rev_sanitized=0 でも 3年CAGR 計算が ZeroDivisionError を起こさないこと"""
        mod = self._load_analyzer()
        data = {
            "ticker": "RSTART0",
            "years": [2021, 2022, 2023, 2024],
            "records": {
                2021: self._make_record(rev_san=0.0,        net_income=-500_000),
                2022: self._make_record(rev_san=1_000_000,  net_income=-400_000),
                2023: self._make_record(rev_san=2_000_000,  net_income=-300_000),
                2024: self._make_record(rev_san=3_000_000,  net_income=-200_000),
            },
        }
        try:
            mod.StonksAnalyzer().analyze(data)
        except ZeroDivisionError as e:
            pytest.fail(f"r_start=0 で ZeroDivisionError が発生した: {e}")

    def test_discontinuous_growth_avg_past_zero_skips_comparison(self):
        """
        過去YoYの平均が0（avg_past=0）でも _analyze_profitability_path が
        ZeroDivisionError を起こさず、非連続成長判定をスキップすること。

        直近YoYが200%以上（急拡大）かつ過去YoY平均がちょうど0%になるデータを構成し、
        analyzer.py L625 の `avg_past > 0` ガードが機能していることを確認する。
        """
        mod = self._load_analyzer()
        data = {
            "ticker": "AVGPAST0",
            "years": [2021, 2022, 2023],
            "records": {
                # 2021→2022: 売上横ばい(0%) → 過去YoY平均が0になる
                2021: self._make_record(rev_san=100_000, net_income=-50_000),
                2022: self._make_record(rev_san=100_000, net_income=-60_000),
                # 2022→2023: 売上4倍(+300%) → 直近YoYが200%以上の急拡大条件を満たす
                2023: self._make_record(rev_san=400_000, net_income=-70_000),
            },
        }
        try:
            result = mod.StonksAnalyzer().analyze(data)
        except ZeroDivisionError as e:
            pytest.fail(f"avg_past=0 で ZeroDivisionError が発生した: {e}")
        # avg_past=0 は「比較不可」としてスキップされ、非連続成長フラグは立たない
        assert result.profitability_path.discontinuous_growth is False
