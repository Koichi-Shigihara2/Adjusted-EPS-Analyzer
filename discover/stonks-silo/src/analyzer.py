# discover/stonks-silo/src/analyzer.py
"""
Stonks Silo Analyzer
3本柱の計算ロジック。

① 良い赤字 vs 悪い赤字
   → 売上成長率 × R&D・S&M比率で「攻めの赤字」か「沈みゆく赤字」かを判定

② 生存能力（Runway）
   → 現金 ÷ 月次バーン（OCF + CapEx）で何ヶ月戦えるか

③ 隠れ黒字化の標準フォーマット
   → R&D・S&M除外後の本業利益
   → OCF改善の角度（速度・加速度）
   → 素直な黒字化 / 隠れ黒字化の時期予測
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# データクラス
# ---------------------------------------------------------------------------

@dataclass
class DeficitQuality:
    """① 良い赤字 vs 悪い赤字"""

    # 入力サマリー（最新年）
    latest_year: int
    revenue: Optional[float]
    net_income: Optional[float]

    # 成長率系列 (year → YoY成長率 %)
    revenue_growth_pct: dict[int, Optional[float]] = field(default_factory=dict)
    cagr_3yr: Optional[float] = None          # 3年CAGR (%)

    # コスト比率（対Revenue）最新年
    rnd_ratio: Optional[float] = None         # R&D / Revenue
    sm_ratio: Optional[float] = None          # S&M / Revenue
    gross_margin: Optional[float] = None      # GrossProfit / Revenue

    # 総合判定
    verdict: str = "UNKNOWN"                  # GOOD_DEFICIT / BAD_DEFICIT / PROFITABLE / UNKNOWN
    verdict_reason: str = ""
    score: Optional[float] = None             # 0-100 (高いほど「攻めの赤字」)


@dataclass
class RunwayAnalysis:
    """② 生存能力"""

    latest_year: int
    cash: Optional[float]                     # 現金+短期投資
    monthly_burn: Optional[float]             # 月次バーン (負値 = 流出)
    runway_months: Optional[float]            # 生存可能月数
    ocf_annual: Optional[float]
    capex_annual: Optional[float]

    verdict: str = "UNKNOWN"                  # SAFE / WATCH / DANGER / UNKNOWN
    verdict_reason: str = ""
    score: Optional[float] = None             # 0-100


@dataclass
class ProfitabilityPath:
    """③ 隠れ黒字化パス"""

    # R&D・S&M除外後の本業利益（各年）
    core_profit: dict[int, Optional[float]] = field(default_factory=dict)  # OCF + RnD + SM

    # OCF改善速度・加速度（年次）
    ocf_annual: dict[int, Optional[float]] = field(default_factory=dict)
    ocf_yoy_change: dict[int, Optional[float]] = field(default_factory=dict)    # 速度
    ocf_acceleration: dict[int, Optional[float]] = field(default_factory=dict)  # 加速度

    # OCF改善トレンドの向き
    ocf_trend: str = "UNKNOWN"   # ACCELERATING / IMPROVING / FLAT / DETERIORATING

    # 黒字化予測
    gaap_breakeven_year: Optional[int] = None     # GAAP純利益ベース
    ocf_breakeven_year: Optional[int] = None      # OCFベース（隠れ黒字化）
    hidden_profit_already: bool = False            # OCFが既に黒字かどうか

    verdict_reason: str = ""
    score: Optional[float] = None             # 0-100


@dataclass
class StonksAnalysis:
    """3本柱まとめ"""

    ticker: str
    years: list[int]

    deficit_quality: DeficitQuality
    runway: RunwayAnalysis
    profitability_path: ProfitabilityPath

    # 総合スコア（0-100）
    overall_score: Optional[float] = None
    overall_verdict: str = "UNKNOWN"
    summary: str = ""


# ---------------------------------------------------------------------------
# メイン計算クラス
# ---------------------------------------------------------------------------

class StonksAnalyzer:

    def analyze(self, data: dict) -> StonksAnalysis:
        """
        fetcher.load_annual_data() の戻り値を受け取り、StonksAnalysis を返す。
        """
        ticker = data["ticker"]
        years = data["years"]
        records = data["records"]

        dq = self._analyze_deficit_quality(years, records)
        ra = self._analyze_runway(years, records)
        pp = self._analyze_profitability_path(years, records)

        overall_score, overall_verdict = self._overall(dq, ra, pp)
        summary = self._build_summary(ticker, dq, ra, pp, overall_verdict)

        return StonksAnalysis(
            ticker=ticker,
            years=years,
            deficit_quality=dq,
            runway=ra,
            profitability_path=pp,
            overall_score=overall_score,
            overall_verdict=overall_verdict,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # ① 良い赤字 vs 悪い赤字
    # ------------------------------------------------------------------

    def _analyze_deficit_quality(self, years: list[int], records: dict) -> DeficitQuality:
        latest_year = years[-1]
        latest = records[latest_year]
        pl = latest["pl"]

        revenue = pl.get("revenue")
        net_income = pl.get("net_income")

        # 売上成長率（YoY）
        rev_growth: dict[int, Optional[float]] = {}
        revenues = {}
        for yr in years:
            rev = records[yr]["pl"].get("revenue")
            revenues[yr] = rev

        for i, yr in enumerate(years):
            if i == 0:
                rev_growth[yr] = None
                continue
            prev_yr = years[i - 1]
            curr = revenues[yr]
            prev = revenues[prev_yr]
            if curr is not None and prev and prev > 0:
                rev_growth[yr] = (curr / prev - 1) * 100
            else:
                rev_growth[yr] = None

        # 3年CAGR
        cagr_3yr = None
        if len(years) >= 4:
            y_end = years[-1]
            y_start = years[-4]
            r_end = revenues.get(y_end)
            r_start = revenues.get(y_start)
            if r_end and r_start and r_start > 0:
                cagr_3yr = ((r_end / r_start) ** (1 / 3) - 1) * 100

        # 最新年コスト比率
        rnd_ratio = sm_ratio = gross_margin = None
        if revenue and revenue > 0:
            rnd = pl.get("research_and_development")
            sm = pl.get("selling_and_marketing")
            gp = pl.get("gross_profit")
            if rnd is not None:
                rnd_ratio = rnd / revenue * 100
            if sm is not None:
                sm_ratio = sm / revenue * 100
            if gp is not None:
                gross_margin = gp / revenue * 100

        # 判定ロジック
        verdict, reason, score = self._deficit_verdict(
            net_income, cagr_3yr, rev_growth, rnd_ratio, sm_ratio, gross_margin
        )

        return DeficitQuality(
            latest_year=latest_year,
            revenue=revenue,
            net_income=net_income,
            revenue_growth_pct=rev_growth,
            cagr_3yr=cagr_3yr,
            rnd_ratio=rnd_ratio,
            sm_ratio=sm_ratio,
            gross_margin=gross_margin,
            verdict=verdict,
            verdict_reason=reason,
            score=score,
        )

    def _deficit_verdict(
        self,
        net_income: Optional[float],
        cagr_3yr: Optional[float],
        rev_growth: dict,
        rnd_ratio: Optional[float],
        sm_ratio: Optional[float],
        gross_margin: Optional[float],
    ) -> tuple[str, str, float]:
        """
        総合判定。スコアリング方式で0-100点を算出。

        スコア構成:
          売上成長  (40pt): CAGR >50%=40, >30%=30, >20%=20, >10%=10, else=0
          投資姿勢  (30pt): R&D+SM >60%=30, >40%=20, >20%=10, else=5
          粗利率    (20pt): >70%=20, >50%=15, >30%=8,  else=0
          赤字状況  (10pt): 純赤字=5 (赤字でも投資中), 純黒字=10
        """
        is_profitable = net_income is not None and net_income > 0

        score = 0.0
        reasons = []

        # 売上成長 (40pt)
        if cagr_3yr is not None:
            if cagr_3yr >= 50:
                score += 40; reasons.append(f"売上CAGR +{cagr_3yr:.0f}% (超高成長)")
            elif cagr_3yr >= 30:
                score += 30; reasons.append(f"売上CAGR +{cagr_3yr:.0f}% (高成長)")
            elif cagr_3yr >= 20:
                score += 20; reasons.append(f"売上CAGR +{cagr_3yr:.0f}% (成長中)")
            elif cagr_3yr >= 10:
                score += 10; reasons.append(f"売上CAGR +{cagr_3yr:.0f}% (緩成長)")
            else:
                reasons.append(f"売上CAGR {cagr_3yr:.0f}% (成長鈍化)")
        else:
            reasons.append("成長率計算不可")

        # 投資姿勢 (30pt) — R&D + S&M 合計対Revenue
        invest_ratio = 0.0
        if rnd_ratio is not None:
            invest_ratio += rnd_ratio
        if sm_ratio is not None:
            invest_ratio += sm_ratio
        if invest_ratio >= 60:
            score += 30; reasons.append(f"R&D+SM {invest_ratio:.0f}% (積極投資)")
        elif invest_ratio >= 40:
            score += 20; reasons.append(f"R&D+SM {invest_ratio:.0f}% (投資中)")
        elif invest_ratio >= 20:
            score += 10; reasons.append(f"R&D+SM {invest_ratio:.0f}% (標準)")
        elif invest_ratio > 0:
            score += 5; reasons.append(f"R&D+SM {invest_ratio:.0f}% (低投資)")
        else:
            reasons.append("投資比率計算不可")

        # 粗利率 (20pt)
        if gross_margin is not None:
            if gross_margin >= 70:
                score += 20; reasons.append(f"粗利率 {gross_margin:.0f}% (高収益構造)")
            elif gross_margin >= 50:
                score += 15; reasons.append(f"粗利率 {gross_margin:.0f}% (良好)")
            elif gross_margin >= 30:
                score += 8;  reasons.append(f"粗利率 {gross_margin:.0f}% (普通)")
            else:
                reasons.append(f"粗利率 {gross_margin:.0f}% (低い)")
        else:
            reasons.append("粗利率計算不可")

        # 黒字状況 (10pt)
        if is_profitable:
            score += 10; reasons.append("純利益黒字")
        elif net_income is not None:
            score += 5

        # 最終判定
        if is_profitable:
            verdict = "PROFITABLE"
        elif score >= 65:
            verdict = "GOOD_DEFICIT"
        elif score >= 35:
            verdict = "WATCH"
        else:
            verdict = "BAD_DEFICIT"

        return verdict, " / ".join(reasons), round(score, 1)

    # ------------------------------------------------------------------
    # ② 生存能力（Runway）
    # ------------------------------------------------------------------

    def _analyze_runway(self, years: list[int], records: dict) -> RunwayAnalysis:
        latest_year = years[-1]
        latest = records[latest_year]
        bs = latest["bs"]
        cf = latest["cf"]

        cash = _sum_not_none(
            bs.get("cash_and_equivalents"),
            bs.get("short_term_investments"),
        )
        ocf = cf.get("operating_cash_flow")
        capex = cf.get("capital_expenditure")

        # 月次バーン = (OCF + CapEx) / 12
        # OCF が正なら現金消費なし（CapEx分は流出）
        # CapEx は通常マイナス値で格納
        monthly_burn = None
        if ocf is not None and capex is not None:
            annual_burn = ocf + capex  # CapEx がマイナスなら OCF から差し引かれる
            monthly_burn = annual_burn / 12
        elif ocf is not None:
            monthly_burn = ocf / 12

        # Runway 計算
        runway_months = None
        if cash is not None and monthly_burn is not None:
            if monthly_burn >= 0:
                # 現金が増えている or トントン → Runway 無限大扱い
                runway_months = float("inf")
            else:
                runway_months = cash / abs(monthly_burn)

        # 判定
        verdict, reason = self._runway_verdict(runway_months, monthly_burn, cash)

        return RunwayAnalysis(
            latest_year=latest_year,
            cash=cash,
            monthly_burn=monthly_burn,
            runway_months=runway_months,
            ocf_annual=ocf,
            capex_annual=capex,
            verdict=verdict,
            verdict_reason=reason,
        )

    def _runway_verdict(
        self,
        runway_months: Optional[float],
        monthly_burn: Optional[float],
        cash: Optional[float],
    ) -> tuple[str, str]:
        if runway_months is None:
            return "UNKNOWN", "データ不足"
        if runway_months == float("inf") or (monthly_burn is not None and monthly_burn >= 0):
            return "SAFE", "キャッシュフロー黒字またはトントン"
        if runway_months >= 24:
            return "SAFE", f"Runway {runway_months:.0f}ヶ月（2年超）"
        if runway_months >= 12:
            return "WATCH", f"Runway {runway_months:.0f}ヶ月（1-2年）要注意"
        return "DANGER", f"Runway {runway_months:.0f}ヶ月（1年未満）危険"

    # ------------------------------------------------------------------
    # ③ 隠れ黒字化パス
    # ------------------------------------------------------------------

    def _analyze_profitability_path(self, years: list[int], records: dict) -> ProfitabilityPath:
        # OCF 年次
        ocf_annual = {}
        for yr in years:
            ocf_annual[yr] = records[yr]["cf"].get("operating_cash_flow")

        # コア利益 = OCF + R&D + S&M（投資的コストを足し戻した本業キャッシュ）
        # ※ R&D・SM は P/L 上の費用。OCF はその後の現金収支なので厳密には別軸だが、
        #   「投資費用を除いた収益力」の代理指標として利用する。
        core_profit = {}
        for yr in years:
            pl = records[yr]["pl"]
            ocf = ocf_annual[yr]
            rnd = pl.get("research_and_development")
            sm = pl.get("selling_and_marketing")
            if ocf is not None:
                add_back = (rnd or 0) + (sm or 0)
                core_profit[yr] = ocf + add_back
            else:
                core_profit[yr] = None

        # OCF YoY 変化（速度）
        ocf_yoy: dict[int, Optional[float]] = {}
        for i, yr in enumerate(years):
            if i == 0:
                ocf_yoy[yr] = None
                continue
            prev_yr = years[i - 1]
            curr = ocf_annual[yr]
            prev = ocf_annual[prev_yr]
            if curr is not None and prev is not None:
                ocf_yoy[yr] = curr - prev
            else:
                ocf_yoy[yr] = None

        # OCF YoY 加速度（2階微分）
        ocf_accel: dict[int, Optional[float]] = {}
        for i, yr in enumerate(years):
            if i < 2:
                ocf_accel[yr] = None
                continue
            prev_yr = years[i - 1]
            curr_v = ocf_yoy[yr]
            prev_v = ocf_yoy[prev_yr]
            if curr_v is not None and prev_v is not None:
                ocf_accel[yr] = curr_v - prev_v
            else:
                ocf_accel[yr] = None

        # OCF トレンド判定
        ocf_trend = self._ocf_trend(years, ocf_annual, ocf_yoy, ocf_accel)

        # 黒字化予測
        gaap_be, ocf_be, hidden_already, reason = self._breakeven_estimate(
            years, records, ocf_annual
        )

        return ProfitabilityPath(
            core_profit=core_profit,
            ocf_annual=ocf_annual,
            ocf_yoy_change=ocf_yoy,
            ocf_acceleration=ocf_accel,
            ocf_trend=ocf_trend,
            gaap_breakeven_year=gaap_be,
            ocf_breakeven_year=ocf_be,
            hidden_profit_already=hidden_already,
            verdict_reason=reason,
        )

    def _ocf_trend(
        self,
        years: list[int],
        ocf_annual: dict,
        ocf_yoy: dict,
        ocf_accel: dict,
    ) -> str:
        """直近2年の速度と加速度からトレンドを判定"""
        if len(years) < 2:
            return "UNKNOWN"

        # 直近2年の速度
        recent_yoys = [
            ocf_yoy[yr] for yr in years[-2:]
            if ocf_yoy.get(yr) is not None
        ]
        if not recent_yoys:
            return "UNKNOWN"

        positive_yoys = sum(1 for v in recent_yoys if v > 0)
        latest_ocf = ocf_annual.get(years[-1])

        # 加速度（直近）
        latest_accel = None
        for yr in reversed(years):
            if ocf_accel.get(yr) is not None:
                latest_accel = ocf_accel[yr]
                break

        if positive_yoys == len(recent_yoys) and latest_accel is not None and latest_accel > 0:
            return "ACCELERATING"
        if positive_yoys >= 1:
            return "IMPROVING"
        if latest_ocf is not None and latest_ocf > 0:
            return "FLAT"  # 黒字だが改善なし
        return "DETERIORATING"

    def _breakeven_estimate(
        self,
        years: list[int],
        records: dict,
        ocf_annual: dict,
    ) -> tuple[Optional[int], Optional[int], bool, str]:
        """
        簡易線形外挿で黒字化年を予測。
        直近3年の改善トレンドを用いる。
        Returns: (gaap_be_year, ocf_be_year, hidden_already, reason)
        """
        reasons = []

        # GAAP 純利益 黒字化（最新年が既にプラスなら予測不要）
        gaap_be = None
        net_incomes = {yr: records[yr]["pl"].get("net_income") for yr in years}
        latest_ni = net_incomes.get(years[-1])
        if latest_ni is not None and latest_ni > 0:
            gaap_reason = "純利益黒字達成済み"
        else:
            gaap_be, gaap_reason = _linear_breakeven(years, net_incomes)
        reasons.append(gaap_reason)

        # OCF 黒字化
        latest_ocf = ocf_annual.get(years[-1])
        hidden_already = latest_ocf is not None and latest_ocf > 0

        ocf_be = None
        if not hidden_already:
            ocf_be, ocf_reason = _linear_breakeven(years, ocf_annual)
            reasons.append(ocf_reason)
        else:
            reasons.append("OCFは既に黒字（隠れ黒字達成済み）")

        return gaap_be, ocf_be, hidden_already, " | ".join(reasons)

    # ------------------------------------------------------------------
    # 総合スコア・サマリー
    # ------------------------------------------------------------------

    def _overall(
        self, dq: DeficitQuality, ra: RunwayAnalysis, pp: ProfitabilityPath
    ) -> tuple[Optional[float], str]:
        """
        3本柱を統合したスコア。
        - 赤字品質  40%
        - 生存能力  30%
        - 黒字化パス 30%
        """
        weights = {"deficit": 0.4, "runway": 0.3, "path": 0.3}

        # 赤字品質スコア (0-100)
        dq_score = dq.score or 0

        # 生存能力スコア (0-100)
        runway_map = {"SAFE": 100, "WATCH": 60, "DANGER": 20, "UNKNOWN": 0}
        ra_score = runway_map.get(ra.verdict, 0)

        # 黒字化パス (0-100)
        trend_map = {
            "ACCELERATING": 100,
            "IMPROVING": 75,
            "FLAT": 50,
            "DETERIORATING": 20,
            "UNKNOWN": 0,
        }
        path_score = trend_map.get(pp.ocf_trend, 0)
        if pp.hidden_profit_already:
            path_score = max(path_score, 80)

        ra.score = float(ra_score)
        pp.score = float(path_score)

        overall = (
            dq_score * weights["deficit"]
            + ra_score * weights["runway"]
            + path_score * weights["path"]
        )

        if overall >= 75:
            verdict = "10x_CANDIDATE"
        elif overall >= 55:
            verdict = "PROMISING"
        elif overall >= 35:
            verdict = "WATCH"
        else:
            verdict = "AVOID"

        return round(overall, 1), verdict

    def _build_summary(
        self,
        ticker: str,
        dq: DeficitQuality,
        ra: RunwayAnalysis,
        pp: ProfitabilityPath,
        overall_verdict: str,
    ) -> str:
        verdict_ja = {
            "GOOD_DEFICIT": "良い赤字",
            "BAD_DEFICIT":  "悪い赤字",
            "PROFITABLE":   "純利益黒字",
            "UNKNOWN":      "不明",
        }
        trend_ja = {
            "ACCELERATING": "加速中",
            "IMPROVING":    "改善中",
            "FLAT":         "横ばい",
            "DETERIORATING":"悪化中",
            "UNKNOWN":      "不明",
        }

        def _fix(s: str) -> str:
            return s.replace("R&D+SM", "研究開発+販売管理").replace("CAGR", "成長率")

        dq_v = verdict_ja.get(dq.verdict, dq.verdict)
        trend_str = trend_ja.get(pp.ocf_trend, pp.ocf_trend)

        lines = [
            f"[{ticker}] 総合判定: {overall_verdict}",
            f"① 赤字品質 : {dq_v} (スコア {dq.score}) — {_fix(dq.verdict_reason[:60])}",
        ]

        if ra.runway_months == float("inf"):
            runway_str = "∞（CF黒字）"
        elif ra.runway_months is not None:
            runway_str = f"{ra.runway_months:.0f}ヶ月"
        else:
            runway_str = "N/A"

        lines.append(f"② 生存能力 : {ra.verdict} Runway={runway_str} — {ra.verdict_reason}")

        hidden = "✅ 営業CF黒字達成済み" if pp.hidden_profit_already else f"営業CF黒字化予測: {pp.ocf_breakeven_year or '不明'}"
        lines.append(f"③ 黒字化   : 営業CFトレンド={trend_str} / {hidden}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def _sum_not_none(*values) -> Optional[float]:
    """None を除いた値の合計。全て None なら None を返す。"""
    result = None
    for v in values:
        if v is not None:
            result = (result or 0) + v
    return result


def _linear_breakeven(
    years: list[int],
    series: dict[int, Optional[float]],
    horizon: int = 5,
) -> tuple[Optional[int], str]:
    """
    直近3年の有効データで線形回帰し、ゼロクロス年を推定する。
    """
    valid = [(yr, v) for yr in years[-3:] if (v := series.get(yr)) is not None]
    if len(valid) < 2:
        return None, "データ不足のため予測不可"

    latest_yr, latest_val = valid[-1]
    if latest_val > 0:
        return latest_yr, "既に黒字"

    # 簡易傾き（最終2点）
    (yr0, v0), (yr1, v1) = valid[-2], valid[-1]
    if yr1 == yr0:
        return None, "同年データのため計算不可"
    slope = (v1 - v0) / (yr1 - yr0)

    if slope <= 0:
        return None, "改善トレンドなし（予測不可）"

    years_to_be = -latest_val / slope
    be_year = int(latest_yr + years_to_be + 0.5)

    if be_year > latest_yr + horizon:
        return None, f"黒字化まで{years_to_be:.1f}年（{horizon}年超のため対象外）"

    return be_year, f"線形外挿で{be_year}年頃に黒字化予測"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from fetcher import load_annual_data

    ticker = sys.argv[1] if len(sys.argv) > 1 else "PLTR"
    data = load_annual_data(ticker, years=5)

    analyzer = StonksAnalyzer()
    result = analyzer.analyze(data)

    print("\n" + "=" * 60)
    print(result.summary)
    print("=" * 60)

    dq = result.deficit_quality
    ra = result.runway
    pp = result.profitability_path

    print(f"\n【① 赤字品質詳細】")
    print(f"  粗利率: {_pct(dq.gross_margin)}  R&D比: {_pct(dq.rnd_ratio)}  S&M比: {_pct(dq.sm_ratio)}")
    print(f"  3年CAGR: {_pct(dq.cagr_3yr)}")
    print(f"  売上成長YoY: ", end="")
    for yr, g in dq.revenue_growth_pct.items():
        print(f"{yr}={_pct(g)}", end="  ")
    print()

    print(f"\n【② 生存能力詳細】")
    print(f"  現金: {_fmt(ra.cash)}  月次バーン: {_fmt(ra.monthly_burn)}/月")

    print(f"\n【③ 黒字化パス詳細】")
    print(f"  年度     OCF          OCF速度      OCF加速度    コア利益")
    for yr in result.years:
        o = _fmt(pp.ocf_annual.get(yr))
        v = _fmt(pp.ocf_yoy_change.get(yr))
        a = _fmt(pp.ocf_acceleration.get(yr))
        c = _fmt(pp.core_profit.get(yr))
        print(f"  {yr}  {o:>12}  {v:>12}  {a:>12}  {c:>12}")

    print(f"\n  GAAP黒字化予測: {result.profitability_path.gaap_breakeven_year or '不明'}")
    print(f"  OCF黒字化予測 : {result.profitability_path.ocf_breakeven_year or '既に黒字' if pp.hidden_profit_already else '不明'}")


def _pct(v) -> str:
    if v is None: return "N/A"
    return f"{v:.1f}%"

def _fmt(v) -> str:
    if v is None: return "N/A"
    if abs(v) >= 1e9: return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6: return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"
