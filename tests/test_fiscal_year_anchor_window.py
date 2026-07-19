"""
tests/test_fiscal_year_anchor_window.py

ARCH-DATA-1ステージ2（決算アンカー日ウィンドウ方式）の回帰テスト。

common/sec_data/utils.py::determine_fiscal_year()の「month > fiscal_end_month」
片方向月比較方式を、決算アンカー日（月+日）を中心とした前後日数ウィンドウ判定に
置き換えた際、2026-07-17の事前調査で「既存テストに一切カバーされていない」と
判明した境界条件を明示的にカバーする：
- 12月決算企業での月またぎ非対応（CDNS型）
- end_date.month == fiscal_end_monthの等号ケース
- 52/53週企業の月境界またぎ（DELL型）
- アンカー日が2/29の非うるう年フォールバック
- 60日超の異常値でのWARN+フォールバック動作
- _own_override_is_safe条件2のCDNS FY2015相当の回帰
- Dec31/Jan1の年境界をまたぐ(月,日)分布のクラスタリング（JNJ/TDY型）

JNJ/TDY型の背景（2026-07-17の実データ検証で発見）:
決算日が12月末〜1月頭を往復する52/53週企業では、(月,日)の完全一致最頻値だけを
見るとDec側（12/28,12/29,12/30,12/31等、年によって微妙にずれる）とJan側
（1/1,1/2,1/3等）に票が割れ、たまたまJan側の特定の1日が単独最多になることが
ある。これをアンカーに使うと候補年度の距離計算が「Dec31基準」と「Jan1基準」で
逆転し、JNJの実データで企業自身のfyタグと矛盾する年度判定（本来2013年である
べきend=2013-12-29が2014年と誤判定）が発生した。circular clusteringで
年境界をまたぐ(月,日)を1つのクラスタに統合することで解消する。

実行方法:
    python -m pytest tests/test_fiscal_year_anchor_window.py -v
"""
from datetime import date, datetime, timedelta

from common.sec_data.utils import (
    determine_fiscal_year,
    detect_fiscal_anchor_date,
    detect_fiscal_end_month,
    _cluster_fiscal_anchor_candidates,
)
from common.sec_data.parser import SECParser


# ============================================
# determine_fiscal_year(): アンカー日ウィンドウ方式
# ============================================

def test_cdns_type_december_fiscal_year_end_month_crossing():
    """12月決算企業（fiscal_end_month=12）で決算日が翌年1月にずれるケース（CDNS型）。

    旧ロジック（month > fiscal_end_monthのみ）はmonth > 12が恒常的にFalseのため
    年またぎ補正が原理的に機能せず、2015-01-03（真のFY2014）がbucket 2015に
    誤って配置されていた。アンカー日ウィンドウ方式では2014-12-31に最も近いと
    正しく判定される。
    """
    end_date = datetime(2015, 1, 3)
    result = determine_fiscal_year(end_date, fiscal_end_month=12, anchor_month=12, anchor_day=31)
    assert result == 2014


def test_equal_month_boundary_uses_anchor_day():
    """end_date.month == fiscal_end_monthの等号ケース（AAPL型: fiscal_end_month=9）"""
    end_date = datetime(2024, 9, 28)
    result = determine_fiscal_year(end_date, fiscal_end_month=9, anchor_month=9, anchor_day=30)
    assert result == 2024


def test_dell_type_month_boundary_crossing_both_directions():
    """DELL型: 決算日が1月末⇔2月初で年により往復するケース（fiscal_end_month=1）"""
    # 2023-02-03（アンカーより後ろへずれた年）→ FY2023
    assert determine_fiscal_year(datetime(2023, 2, 3), fiscal_end_month=1,
                                  anchor_month=1, anchor_day=29) == 2023
    # 2022-01-28（アンカーより前へずれた年）→ FY2022
    assert determine_fiscal_year(datetime(2022, 1, 28), fiscal_end_month=1,
                                  anchor_month=1, anchor_day=29) == 2022


def test_leap_year_anchor_229_fallback_to_228_in_non_leap_candidate_year():
    """アンカー日が2/29のケースで、非うるう年の候補年度はdate()生成不可のため
    2/28を基準に日数差を計算する（2023年は非うるう年）"""
    result = determine_fiscal_year(datetime(2023, 3, 1), fiscal_end_month=2,
                                    anchor_month=2, anchor_day=29)
    assert result == 2023


def test_leap_year_anchor_229_exact_match_in_leap_candidate_year():
    """アンカー日が2/29のケースで、うるう年の候補年度は2/29そのものを使う"""
    result = determine_fiscal_year(datetime(2024, 2, 29), fiscal_end_month=2,
                                    anchor_month=2, anchor_day=29)
    assert result == 2024


def test_diff_exactly_60_days_uses_anchor_window_not_fallback(capsys):
    """最小日数差がちょうど60日はアンカー日ウィンドウ判定を採用する（フォールバックしない）"""
    anchor = date(2024, 6, 30)
    end_date = datetime.combine(anchor + timedelta(days=60), datetime.min.time())
    result = determine_fiscal_year(end_date, fiscal_end_month=6, anchor_month=6, anchor_day=30)
    assert result == 2024
    captured = capsys.readouterr()
    assert "[WARN]" not in captured.out


def test_diff_61_days_triggers_warn_and_month_only_fallback(capsys):
    """最小日数差が60日を超えるとWARNログを出力し月のみ比較にフォールバックする
    （未知の異常パターンへの安全弁。silent failさせない）"""
    anchor = date(2024, 6, 30)
    end_date = datetime.combine(anchor + timedelta(days=61), datetime.min.time())
    # 月のみ比較: end_date.month(8) > fiscal_end_month(6) → True → year+1
    result = determine_fiscal_year(end_date, fiscal_end_month=6, anchor_month=6, anchor_day=30)
    assert result == 2025
    captured = capsys.readouterr()
    assert "[WARN]" in captured.out
    assert "determine_fiscal_year" in captured.out


def test_no_anchor_falls_back_to_month_only_silently(capsys):
    """anchor_month/anchor_day省略時は従来の月のみ比較にフォールバックする（WARNなし。
    アンカー日が未検出＝異常ではなく単なるデータ不足のため、警告を出す必要はない）"""
    result = determine_fiscal_year(datetime(2024, 3, 31), fiscal_end_month=12)
    assert result == 2024
    captured = capsys.readouterr()
    assert "[WARN]" not in captured.out


# ============================================
# detect_fiscal_anchor_date() / detect_fiscal_end_month()
# ============================================

def test_detect_fiscal_anchor_date_finds_most_common_month_day():
    """本人10-K annualエントリ（340〜380日）のend日からmonth+dayの最頻値を検出する。
    91日間の四半期比較開示混入（form=='10-K'・fp=='FY'だがduration外）は除外される"""
    us_gaap = {
        "NetIncomeLoss": {"units": {"USD": [
            {"form": "10-K", "fp": "FY", "start": "2012-01-01", "end": "2012-12-29", "val": 1},
            {"form": "10-K", "fp": "FY", "start": "2013-01-01", "end": "2013-12-28", "val": 2},
            {"form": "10-K", "fp": "FY", "start": "2013-12-29", "end": "2014-12-28", "val": 2},
            {"form": "10-K", "fp": "FY", "start": "2014-12-29", "end": "2015-12-28", "val": 3},
            # 91日間の四半期比較開示混入（duration外のため除外されるべき）
            {"form": "10-K", "fp": "FY", "start": "2015-10-01", "end": "2015-12-28", "val": 999},
        ]}},
    }
    result = detect_fiscal_anchor_date(us_gaap, ["NetIncomeLoss"])
    assert result == (12, 28)


def test_detect_fiscal_anchor_date_returns_none_when_no_qualifying_entries():
    """本人年次エントリが1件もない場合はNoneを返す
    （determine_fiscal_year側で月のみ比較にフォールバックさせるための明示的シグナル）"""
    assert detect_fiscal_anchor_date({}, ["NetIncomeLoss"]) is None


def test_detect_fiscal_end_month_excludes_10ka_matching_parser_behavior():
    """detect_fiscal_end_month: form=='10-K'完全一致（10-K/Aは対象外）。
    10-K/Aを含めると月4が多数派になってしまう構成だが、除外により正しく月9を検出する"""
    us_gaap = {
        "NetIncomeLoss": {"units": {"USD": [
            {"form": "10-K/A", "fp": "FY", "end": "2018-04-30", "val": 1},
            {"form": "10-K/A", "fp": "FY", "end": "2019-04-30", "val": 1},
            {"form": "10-K/A", "fp": "FY", "end": "2020-04-30", "val": 1},
            {"form": "10-K", "fp": "FY", "end": "2020-09-30", "val": 2},
            {"form": "10-K", "fp": "FY", "end": "2021-09-30", "val": 3},
        ]}},
    }
    assert detect_fiscal_end_month(us_gaap, ["NetIncomeLoss"]) == 9


# ============================================
# JNJ/TDY型: Dec31/Jan1境界をまたぐ(月,日)分布のクラスタリング
# ============================================

def test_detect_fiscal_anchor_date_merges_year_boundary_cluster_dec_side_wins():
    """JNJ/TDY型: Dec側（多数）とJan側（少数）に分散したend日が1つの循環クラスタに
    統合され、多数派のDec側が採用されること（完全一致最頻値だとJan側の1日が
    単独最多になり得るため、クラスタリングで年境界をまたいだ集計が必須）"""
    us_gaap = {
        "NetIncomeLoss": {"units": {"USD": [
            {"form": "10-K", "fp": "FY", "start": "2011-12-31", "end": "2012-12-28", "val": 1},
            {"form": "10-K", "fp": "FY", "start": "2012-12-29", "end": "2013-12-28", "val": 2},
            {"form": "10-K", "fp": "FY", "start": "2013-12-29", "end": "2014-12-28", "val": 3},
            {"form": "10-K", "fp": "FY", "start": "2012-01-02", "end": "2012-12-29", "val": 4},
            {"form": "10-K", "fp": "FY", "start": "2013-01-02", "end": "2013-12-29", "val": 5},
            # Jan側は1件のみ（少数派）
            {"form": "10-K", "fp": "FY", "start": "2011-01-02", "end": "2012-01-01", "val": 6},
        ]}},
    }
    result = detect_fiscal_anchor_date(us_gaap, ["NetIncomeLoss"])
    # Dec側(5件: 12/28×3, 12/29×2)がJan側(1件: 1/1)より多数派 → Dec側を採用
    assert result == (12, 28)


def test_cluster_fiscal_anchor_candidates_merges_across_year_boundary():
    """_cluster_fiscal_anchor_candidates: 12/28〜1/2の6点が、年境界をまたいで
    1つのクラスタに統合されること（隣接する循環距離がいずれも7日以内のため）"""
    day_counts = {
        (12, 28): 1, (12, 29): 1, (12, 30): 1, (12, 31): 1,
        (1, 1): 1, (1, 2): 1,
    }
    clusters = _cluster_fiscal_anchor_candidates(day_counts)
    assert len(clusters) == 1
    assert sum(len(c) for c in clusters) == 6


def test_cluster_fiscal_anchor_candidates_splits_distant_dates():
    """_cluster_fiscal_anchor_candidates: 12月末クラスタと6月末クラスタのように
    循環距離が7日を大きく超える場合は別クラスタに分離されること"""
    day_counts = {(12, 30): 3, (12, 31): 2, (6, 30): 1}
    clusters = _cluster_fiscal_anchor_candidates(day_counts)
    assert len(clusters) == 2
    sizes = sorted(sum(p[3] for p in c) for c in clusters)
    assert sizes == [1, 5]


def test_jnj_type_early_january_end_date_maps_to_prior_year():
    """TDY型: アンカー(12,28)の場合、end=2012-01-01（TDY自身がfy=2011と申告した
    実データ）が正しくFY2011と判定されること（2026-07-17実データ検証で発見した
    Dec31/Jan1境界問題の直接的な回帰テスト）"""
    result = determine_fiscal_year(datetime(2012, 1, 1), fiscal_end_month=12,
                                    anchor_month=12, anchor_day=28)
    assert result == 2011


# ============================================
# _own_override_is_safe(): 条件2のCDNS FY2015相当の回帰
# ============================================

def test_own_override_is_safe_cdns_type_regression():
    """_own_override_is_safe条件2の回帰テスト（CDNS FY2015相当）。

    12月決算企業（fiscal_end_month=12）で、フォールバックがbucket[2015]に
    「真のFY2014データ」（end=2015-01-03）を自己整合的に採用してしまっている
    状態で、本人データ（真のFY2015、end=2016-01-02）による上書きが
    許可されるべきケース。

    旧ロジック（no_crossing_needed = existing_end_dt.month <= fiscal_end_month）は
    12月決算企業でmonth<=12が恒常的にTrueとなり、determine_fiscal_year()も
    月のみ比較のため自己整合(2015)と誤判定し、上書きをブロックしていた
    （CDNS FY2015のtotal_assets/revenueがFY2014値のまま保持される実害を
    発生させていた実例）。

    本テストではanchor_month/anchor_day省略（None）の呼び出しで旧ロジック相当の
    バグ（誤ブロック）を再現し、アンカー日ウィンドウ方式を指定した呼び出しで
    正しく上書きが許可されることを確認する。
    """
    parser = SECParser()
    annual_end_dates = {2015: "2015-01-03"}
    annual_durations = {2015: 365}
    annual_accn = {2015: "0000000000-14-000001"}
    # 既存accnがreportDateと一致しない（＝別の本人データとして採用済みではない）
    # 構成にして、accn一致による早期Falseを避け、条件2（月/アンカー判定）を検証する
    accn_reportdate = {"0000000000-14-000001": "2099-01-01"}

    # 旧ロジック相当（アンカー未指定）: 月のみ比較で自己整合し誤ってブロックされる
    is_safe_without_anchor = parser._own_override_is_safe(
        2015, "2016-01-02", 12, annual_end_dates, annual_durations, annual_accn, accn_reportdate,
    )
    assert is_safe_without_anchor is False

    # 新ロジック（アンカー日ウィンドウ方式）: 正しく上書きが許可される
    is_safe_with_anchor = parser._own_override_is_safe(
        2015, "2016-01-02", 12, annual_end_dates, annual_durations, annual_accn, accn_reportdate,
        anchor_month=12, anchor_day=31,
    )
    assert is_safe_with_anchor is True


# ============================================
# _is_boundary_collision() / _fiscal_anchors_far_apart():
# FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1（WARN-24）
# ============================================

def test_fiscal_anchors_far_apart_true_for_rcat_type_gap():
    """RCAT型: 決算日そのものが大きく動いた場合（4/30→12/31）はTrue"""
    assert SECParser._fiscal_anchors_far_apart("2024-04-30", "2024-12-31") is True


def test_fiscal_anchors_far_apart_false_for_same_anchor_adjacent_years():
    """ADSK/CRM型: 同一(月,日)・隣接暦年（fyタグの年ズレのみ）はFalse"""
    assert SECParser._fiscal_anchors_far_apart("2011-01-31", "2012-01-31") is False


def test_fiscal_anchors_far_apart_false_for_52_53_week_wobble():
    """CAKE/WST型: 52/53週企業の1日程度の前後変動はFalse"""
    assert SECParser._fiscal_anchors_far_apart("2017-12-31", "2018-01-01") is False


def test_fiscal_anchors_far_apart_handles_year_boundary_circular_distance():
    """年境界をまたぐ循環距離（12/31 vs 1/2、実質2日）はFalse"""
    assert SECParser._fiscal_anchors_far_apart("2020-12-31", "2021-01-02") is False


def test_is_boundary_collision_true_for_rcat_type():
    """RCAT型（本人データ側fy_tag≠既存側fy_tag・end_date異なる・決算日が大きく
    離れている）でTrue（WARN-24の発火条件）"""
    assert SECParser._is_boundary_collision(
        existing_end="2024-12-31", existing_fy_tag=2025,
        own_end="2024-04-30", own_fy_tag=2024,
    ) is True


def test_is_boundary_collision_false_when_fy_tag_matches():
    """通常ケース（fy_tag一致）ではFalse（そもそも競合ではない）"""
    assert SECParser._is_boundary_collision(
        existing_end="2024-04-30", existing_fy_tag=2024,
        own_end="2024-04-30", own_fy_tag=2024,
    ) is False


def test_is_boundary_collision_false_when_end_date_matches():
    """同一end_dateの比較年度再掲（fyタグだけが違う）はFalse
    （is_own_data=Falseのfyタグ違いとして常態的に発生する正常仕様、ARCH-DATA-1参照）"""
    assert SECParser._is_boundary_collision(
        existing_end="2019-12-31", existing_fy_tag=2021,
        own_end="2019-12-31", own_fy_tag=2019,
    ) is False


def test_is_boundary_collision_false_for_adsk_type_off_by_one_fy_tag():
    """ADSK/AVAV/CRM/CAKE型: 同一(月,日)・隣接暦年（fyタグが実際の期間より
    1年ずれるWARN-23既知パターン）はFalse（決算期変更ではなく単なるfyタグ誤り）"""
    assert SECParser._is_boundary_collision(
        existing_end="2011-01-31", existing_fy_tag=2010,
        own_end="2012-01-31", own_fy_tag=2011,
    ) is False


def test_is_boundary_collision_false_when_existing_end_is_none():
    """フォールバックが何も採用していない（既存end_dateなし）場合はFalse
    （比較対象がないため競合しようがない）"""
    assert SECParser._is_boundary_collision(
        existing_end=None, existing_fy_tag=None,
        own_end="2024-04-30", own_fy_tag=2024,
    ) is False
