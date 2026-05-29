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
from unittest.mock import MagicMock, patch

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
# 7. hypecore substage_watch の eps_surprise 分岐
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
