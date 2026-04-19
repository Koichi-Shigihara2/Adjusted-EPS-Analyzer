"""
TANUKI VALUATION - Adjustments
FCF補正、RPO補正、α計算、成長オプション補正、FCFベース判定

責務: 各種調整・補正ロジック

v6.1 追加:
  - GrowthOptionResult / calculate_growth_option_pv()
  - calculate_intrinsic_value() に growth_option_pv 引数追加

v6.2 追加:
  - FCFBaseResult / determine_fcf_base()
    FCFリストのトレンドから5年平均 or 直近2年平均を自動判定
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class FCFAdjustmentResult:
    """FCF補正結果"""
    adjusted_fcf: float
    original_fcf: float
    floor_applied: float
    method: str  # "none" | "revenue_floor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adjusted_fcf": self.adjusted_fcf,
            "original_fcf": self.original_fcf,
            "floor_applied": self.floor_applied,
            "method": self.method
        }


@dataclass
class RPOAdjustmentResult:
    """RPO補正結果"""
    rpo_pv: float
    rpo_raw: float
    discount_rate: float
    assumed_years: float
    applied: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rpo_pv": self.rpo_pv,
            "rpo_raw": self.rpo_raw,
            "discount_rate": self.discount_rate,
            "assumed_realization_years": self.assumed_years,
            "applied": self.applied
        }


@dataclass
class AlphaResult:
    """α計算結果"""
    alpha: float
    alpha_uncapped: float
    was_capped: bool
    roe: float
    retention_rate: float
    wacc: float
    g_individual: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "alpha_uncapped": self.alpha_uncapped,
            "was_capped": self.was_capped,
            "roe": self.roe,
            "retention_rate": self.retention_rate,
            "wacc": self.wacc,
            "g_individual": self.g_individual
        }


@dataclass
class GrowthOptionResult:
    """成長オプション（仮説セグメント）PV計算結果"""
    total_pv: float
    options: List[Dict[str, Any]]
    count: int
    applied: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pv": self.total_pv,
            "count": self.count,
            "applied": self.applied,
            "options": [
                {
                    "name": o["name"],
                    "tam": o["tam"],
                    "penetration": o["penetration"],
                    "fcf_margin": o["fcf_margin"],
                    "probability": o["probability"],
                    "delay_years": o["delay_years"],
                    "expected_fcf": o["expected_fcf"],
                    "pv": o["pv"],
                    "note": o.get("note", "")
                }
                for o in self.options
            ]
        }


@dataclass
class FCFBaseResult:
    """
    FCFベース判定結果 v6.3

    DCFの出発点となるベースFCFと、その選択根拠を保持する。

    v6.3変更: ratio方式 → CV（変動係数）方式
        recent_2yr がデフォルト。FCFが安定している場合のみ avg_5yr を使用。
    """
    base_fcf: float       # 採用したベースFCF
    method: str           # "avg_5yr" | "recent_2yr"
    fcf_5yr_avg: float    # 5年平均（参考値）
    fcf_2yr_avg: float    # 直近2年平均（参考値）
    cv: float             # 変動係数 std/|mean|（安定性の指標）
    cv_threshold: float   # CV判定閾値

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_fcf": self.base_fcf,
            "method": self.method,
            "fcf_5yr_avg": self.fcf_5yr_avg,
            "fcf_2yr_avg": self.fcf_2yr_avg,
            "cv": round(self.cv, 3),
            "cv_threshold": self.cv_threshold,
            # 後方互換: ratio/thresholdはcv/cv_thresholdのエイリアス
            "ratio": round(self.cv, 3),
            "threshold": self.cv_threshold
        }


# ========================================
# FCFベース自動判定 v6.3（CV方式）
# ========================================

DEFAULT_FCF_CV_THRESHOLD = 0.5  # CV≤この値なら安定→avg_5yr

def determine_fcf_base(
    fcf_5yr_avg: float,
    fcf_2yr_avg: float,
    fcf_list: List[float],
    threshold: float = DEFAULT_FCF_CV_THRESHOLD
) -> FCFBaseResult:
    """
    FCFの変動係数（CV）で安定性を判定し、ベースFCFを自動選択

    判定ロジック（v6.3）:
        CV = std(fcf_list) / |mean(fcf_list)|
        CV ≤ threshold（安定） → avg_5yr（成熟企業: KO, MSFT等）
        CV > threshold（不安定）→ recent_2yr（成長企業: NVDA, AMD等）

    旧ratio方式との違い:
        旧: 5年平均がデフォルト、急成長時だけ2年平均
        新: 2年平均がデフォルト、安定時だけ5年平均
        → 成長企業のFCF過小評価を構造的に解消

    特殊ケース（CVより優先）:
        fcf_2yr_avg ≤ 0（直近赤字）  → avg_5yr（FCF補正に委ねる）
        fcf_5yr_avg ≤ 0（過去赤字含む）→ recent_2yr
        データ不足（< 3年）           → recent_2yr（保守的にデフォルト）

    Args:
        fcf_5yr_avg  : 5年平均FCF
        fcf_2yr_avg  : 直近2年平均FCF
        fcf_list     : FCFリスト（CV計算用）
        threshold    : CV閾値（デフォルト0.5）

    Returns:
        FCFBaseResult
    """
    import statistics

    # ── 特殊ケース（データ不足）──
    if len(fcf_list) < 3:
        return FCFBaseResult(
            base_fcf=fcf_2yr_avg if fcf_2yr_avg > 0 else fcf_5yr_avg,
            method="recent_2yr" if fcf_2yr_avg > 0 else "avg_5yr",
            fcf_5yr_avg=fcf_5yr_avg,
            fcf_2yr_avg=fcf_2yr_avg,
            cv=999.0,
            cv_threshold=threshold
        )

    # ── 特殊ケース（直近赤字）──
    # ①2年平均がマイナス または ②直近1年がマイナス → avg_5yrにフォールバック
    # CELHのような「最新年マイナス・前年プラス」で平均がほぼゼロになるケースを防ぐ
    latest_year_negative = len(fcf_list) >= 1 and fcf_list[0] < 0
    if fcf_2yr_avg <= 0 or latest_year_negative:
        return FCFBaseResult(
            base_fcf=fcf_5yr_avg,
            method="avg_5yr",
            fcf_5yr_avg=fcf_5yr_avg,
            fcf_2yr_avg=fcf_2yr_avg,
            cv=999.0,
            cv_threshold=threshold
        )

    # ── 特殊ケース（過去赤字含む）──
    if fcf_5yr_avg <= 0:
        return FCFBaseResult(
            base_fcf=fcf_2yr_avg,
            method="recent_2yr",
            fcf_5yr_avg=fcf_5yr_avg,
            fcf_2yr_avg=fcf_2yr_avg,
            cv=999.0,
            cv_threshold=threshold
        )

    # ── CV計算 ──
    try:
        mean_fcf = abs(statistics.mean(fcf_list))
        std_fcf  = statistics.stdev(fcf_list)
        cv = std_fcf / mean_fcf if mean_fcf > 0 else 999.0
    except Exception:
        cv = 999.0

    # ── CV判定 ──
    if cv <= threshold:
        # 安定 → avg_5yr（成熟企業）
        return FCFBaseResult(
            base_fcf=fcf_5yr_avg,
            method="avg_5yr",
            fcf_5yr_avg=fcf_5yr_avg,
            fcf_2yr_avg=fcf_2yr_avg,
            cv=cv,
            cv_threshold=threshold
        )
    else:
        # 不安定・成長 → recent_2yr
        return FCFBaseResult(
            base_fcf=fcf_2yr_avg,
            method="recent_2yr",
            fcf_5yr_avg=fcf_5yr_avg,
            fcf_2yr_avg=fcf_2yr_avg,
            cv=cv,
            cv_threshold=threshold
        )


# ========================================
# 既存関数（変更なし）
# ========================================

def adjust_fcf(
    fcf_avg: float,
    latest_revenue: float,
    revenue_floor_ratio: float = 0.08
) -> FCFAdjustmentResult:
    """FCF補正（マイナスFCF対応）"""
    if fcf_avg > 0:
        return FCFAdjustmentResult(
            adjusted_fcf=fcf_avg,
            original_fcf=fcf_avg,
            floor_applied=0.0,
            method="none"
        )

    if latest_revenue <= 0:
        return FCFAdjustmentResult(
            adjusted_fcf=fcf_avg,
            original_fcf=fcf_avg,
            floor_applied=0.0,
            method="none"
        )

    fcf_floor = latest_revenue * revenue_floor_ratio
    adjusted_fcf = max(fcf_avg, fcf_floor)
    floor_applied = adjusted_fcf - fcf_avg

    return FCFAdjustmentResult(
        adjusted_fcf=adjusted_fcf,
        original_fcf=fcf_avg,
        floor_applied=floor_applied,
        method="revenue_floor"
    )


def adjust_rpo(
    rpo: float,
    discount_rate: float = 0.15,
    assumed_realization_years: float = 1.5
) -> RPOAdjustmentResult:
    """RPO補正（残存履行義務の現在価値化）"""
    if rpo <= 0:
        return RPOAdjustmentResult(
            rpo_pv=0.0,
            rpo_raw=0.0,
            discount_rate=discount_rate,
            assumed_years=assumed_realization_years,
            applied=False
        )

    rpo_pv = rpo / (1 + discount_rate) ** assumed_realization_years

    return RPOAdjustmentResult(
        rpo_pv=rpo_pv,
        rpo_raw=rpo,
        discount_rate=discount_rate,
        assumed_years=assumed_realization_years,
        applied=True
    )


def calculate_alpha(
    roe: float,
    wacc: float,
    retention_rate: float = 0.60,
    alpha_cap: float = 1.0,
    discount_factor: float = 0.7
) -> AlphaResult:
    """α（成長期待プレミアム）計算"""
    g_individual = max(0.0, roe * retention_rate)

    if wacc <= 0:
        alpha_raw = 0.0
    else:
        alpha_raw = (g_individual / wacc) * discount_factor

    alpha_uncapped = max(0.0, alpha_raw)
    alpha = min(alpha_cap, alpha_uncapped)

    return AlphaResult(
        alpha=alpha,
        alpha_uncapped=alpha_uncapped,
        was_capped=alpha_uncapped > alpha_cap,
        roe=roe,
        retention_rate=retention_rate,
        wacc=wacc,
        g_individual=g_individual
    )


def calculate_intrinsic_value(
    v0: float,
    rpo_pv: float,
    alpha: float,
    growth_option_pv: float = 0.0
) -> Tuple[float, float]:
    """本質的価値（P_t）計算"""
    v0_adjusted = v0 + rpo_pv + growth_option_pv
    intrinsic_value_pt = v0_adjusted * (1 + alpha)
    return v0_adjusted, intrinsic_value_pt


def calculate_per_share_value(
    intrinsic_value_pt: float,
    diluted_shares: int
) -> float:
    """1株あたり本質的価値計算"""
    if diluted_shares <= 0:
        return 0.0
    return intrinsic_value_pt / diluted_shares


def calculate_upside(
    intrinsic_value_per_share: float,
    current_price: float
) -> float:
    """乖離率計算"""
    if current_price <= 0:
        return 0.0
    return ((intrinsic_value_per_share / current_price) - 1) * 100


def calculate_growth_option_pv(ticker: str) -> GrowthOptionResult:
    """仮説セグメント（成長オプション）の合計PVを計算"""
    try:
        from segment_config import calculate_growth_option_total_pv
        result = calculate_growth_option_total_pv(ticker)
        return GrowthOptionResult(
            total_pv=result["total_pv"],
            options=result["options"],
            count=result["count"],
            applied=result["count"] > 0
        )
    except ImportError:
        return GrowthOptionResult(
            total_pv=0.0,
            options=[],
            count=0,
            applied=False
        )


# ========================================
# BS評価補正 v7.0 新規
# ========================================

@dataclass
class BSAdjustmentResult:
    """
    BSネットキャッシュ補正結果

    理論株価への加算方式:
        PT = DCF理論株価 + net_cash_per_share
    純負債の場合はマイナス（理論株価を引き下げ）
    """
    cash: float                    # 現金・現金同等物
    short_term_investments: float  # 短期投資
    long_term_debt: float          # 長期有利子負債
    short_term_debt: float         # 短期有利子負債
    net_cash: float                # ネットキャッシュ（+/-）
    net_cash_per_share: float      # 1株あたりネットキャッシュ
    fiscal_year: int               # 取得会計年度
    applied: bool                  # 補正適用フラグ

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cash":                   self.cash,
            "short_term_investments": self.short_term_investments,
            "long_term_debt":         self.long_term_debt,
            "short_term_debt":        self.short_term_debt,
            "net_cash":               self.net_cash,
            "net_cash_per_share":     self.net_cash_per_share,
            "fiscal_year":            self.fiscal_year,
            "applied":                self.applied
        }


def calculate_bs_adjustment(
    net_cash_data: dict,
    diluted_shares: int
) -> BSAdjustmentResult:
    """
    BSネットキャッシュ補正値を計算

    Args:
        net_cash_data: SECReader.get_net_cash()の返却値
        diluted_shares: 希薄化後株式数

    Returns:
        BSAdjustmentResult
    """
    net_cash = net_cash_data.get("net_cash", 0.0)
    available = net_cash_data.get("available", False)

    net_cash_per_share = (
        net_cash / diluted_shares
        if diluted_shares > 0 and available
        else 0.0
    )

    return BSAdjustmentResult(
        cash=net_cash_data.get("cash", 0.0),
        short_term_investments=net_cash_data.get("short_term_investments", 0.0),
        long_term_debt=net_cash_data.get("long_term_debt", 0.0),
        short_term_debt=net_cash_data.get("short_term_debt", 0.0),
        net_cash=net_cash,
        net_cash_per_share=net_cash_per_share,
        fiscal_year=net_cash_data.get("fiscal_year", 0),
        applied=available and net_cash != 0.0
    )



# ========================================
# FCF外れ値分析 v7.1（EPSアナライザー連携）
# ========================================

# 一過性費用として認識するカテゴリ
TRANSIENT_CATEGORIES = {
    "リストラ・事業再編関連",
    "在庫・サプライチェーン関連",
    "金融関連",
}

# FCF外れ値判定の閾値（CV区分別）
FCF_OUTLIER_THRESHOLDS = {
    "mature":  0.20,   # CV≤0.5（成熟企業）: 5年平均から±20%超で外れ値候補
    "growth":  0.60,   # CV>0.5 （成長企業）: 5年平均から±60%超で外れ値候補
}


@dataclass
class FCFOutlierResult:
    """
    FCF外れ値分析結果

    detected     : 外れ値ルールがトリガーされたか
    rule         : トリガーされたルール名
    fiscal_year  : 対象会計年度（fcf_list[0]の年度）
    fcf_value    : 問題のFCF値
    threshold_pct: 適用した閾値（%）
    transient_found   : EPSアナライザーで一過性費用が確認されたか
    transient_items   : 一過性費用の詳細リスト
    transient_total   : 一過性費用の合計（税前）
    action       : "excluded" | "flagged" | "none"
    note         : 人間が読める説明文
    """
    detected: bool
    rule: str                    # "none" | "latest_negative" | "deviation_large"
    fiscal_year: int
    fcf_value: float
    threshold_pct: float         # 適用した乖離閾値（%）
    transient_found: bool
    transient_items: List[Dict[str, Any]]
    transient_total: float       # 一過性費用の合計（税前）
    action: str                  # "excluded" | "flagged" | "none"
    note: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "rule": self.rule,
            "fiscal_year": self.fiscal_year,
            "fcf_value": self.fcf_value,
            "threshold_pct": self.threshold_pct,
            "transient_evidence": {
                "found": self.transient_found,
                "source": "adjusted_eps_analyzer" if self.transient_found else None,
                "items": self.transient_items,
                "total_transient_amount": self.transient_total,
            },
            "action": self.action,
            "note": self.note,
        }


def _load_eps_annual(ticker: str, eps_data_dir: str) -> Optional[Dict[str, Any]]:
    """
    EPSアナライザーのannual.jsonを読み込む

    パス: docs/value-monitor/adjusted_eps_analyzer/data/{TICKER}/annual.json
    """
    import os, json
    path = os.path.join(eps_data_dir, ticker.upper(), "annual.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _find_transient_items(
    eps_annual: Dict[str, Any],
    target_year: int,
) -> List[Dict[str, Any]]:
    """
    指定年度のEPSアナライザー調整項目から一過性費用を抽出

    Returns:
        一過性費用の詳細リスト（カテゴリが TRANSIENT_CATEGORIES に該当するもの）
    """
    items = []
    for yr in eps_annual.get("years", []):
        # 年度文字列 "2025" を int 2025 として比較
        try:
            yr_int = int(yr.get("year", 0))
        except (ValueError, TypeError):
            continue
        if yr_int != target_year:
            continue

        for adj in yr.get("adjustments", []):
            if adj.get("category") in TRANSIENT_CATEGORIES:
                items.append({
                    "category":  adj["category"],
                    "item_name": adj.get("item_name", ""),
                    "amount":    adj.get("amount", 0),
                    "reason":    adj.get("reason", ""),
                })
    return items


def analyze_fcf_outlier(
    ticker: str,
    fcf_list: List[float],
    fcf_5yr_avg: float,
    cv: float,
    fiscal_year_of_latest: int,
    eps_data_dir: str = "",
    cv_threshold: float = DEFAULT_FCF_CV_THRESHOLD,
) -> FCFOutlierResult:
    """
    FCF外れ値を分析し、EPSアナライザーと突合して一過性判定を行う

    Args:
        ticker             : ティッカーシンボル
        fcf_list           : FCFリスト（新しい順、fcf_list[0]が直近）
        fcf_5yr_avg        : 5年平均FCF
        cv                 : 変動係数（determine_fcf_baseで計算済み）
        fiscal_year_of_latest: fcf_list[0]の会計年度（例: 2025）
        eps_data_dir       : EPSアナライザーのdataディレクトリパス
        cv_threshold       : 成熟/成長の分岐CV閾値

    Returns:
        FCFOutlierResult
    """
    NO_OUTLIER = FCFOutlierResult(
        detected=False, rule="none",
        fiscal_year=fiscal_year_of_latest,
        fcf_value=fcf_list[0] if fcf_list else 0,
        threshold_pct=0.0,
        transient_found=False, transient_items=[], transient_total=0.0,
        action="none", note=""
    )

    if not fcf_list or fcf_5yr_avg == 0:
        return NO_OUTLIER

    latest_fcf = fcf_list[0]

    # ── ルール1: 直近1年がマイナス ──
    if latest_fcf < 0:
        rule = "latest_negative"
        threshold_pct = 0.0
    else:
        # ── ルール2: 5年平均からの乖離が閾値超 ──
        is_mature = cv <= cv_threshold
        threshold_pct = FCF_OUTLIER_THRESHOLDS["mature"] if is_mature else FCF_OUTLIER_THRESHOLDS["growth"]
        deviation = abs(latest_fcf - fcf_5yr_avg) / abs(fcf_5yr_avg)
        if deviation > threshold_pct:
            rule = "deviation_large"
        else:
            return NO_OUTLIER  # 外れ値なし

    # ── EPSアナライザーとの突合 ──
    transient_items = []
    transient_total = 0.0
    transient_found = False

    if eps_data_dir:
        eps_annual = _load_eps_annual(ticker, eps_data_dir)
        if eps_annual:
            transient_items = _find_transient_items(eps_annual, fiscal_year_of_latest)
            # マイナス値（評価益等）は除外してプラスのみ合計
            transient_total = max(0.0, sum(
                item["amount"] for item in transient_items if item["amount"] > 0
            ))
            transient_found = len(transient_items) > 0 and transient_total > 0

    # ── アクション決定 ──
    # 一過性費用がFCF乖離の20%未満の場合は除外しない（金額が小さすぎる）
    fcf_deviation = abs(latest_fcf - fcf_5yr_avg) if fcf_5yr_avg != 0 else abs(latest_fcf)
    # latest_negativeの場合: 一過性費用の金額が5年平均の10%以上なら除外
    # deviation_largeの場合:  一過性費用の金額がFCF乖離の20%以上なら除外
    if rule == "latest_negative":
        transient_explains = transient_found and transient_total >= abs(fcf_5yr_avg) * 0.10
    else:
        transient_explains = transient_found and transient_total >= fcf_deviation * 0.20

    if transient_explains:
        action = "excluded"
        # 一過性費用の内訳を文字列化
        summary = "、".join(
            "{cat}({name} ${amt:.0f}M)".format(
                cat=it["category"], name=it["item_name"], amt=it["amount"]/1e6
            )
            for it in transient_items
        )
        if rule == "latest_negative":
            note = (
                "FY{yr} FCF(${val:.1f}M)がマイナス。"
                "一過性費用合計${total:.0f}M({summary})による影響と判断し除外。"
                "5年平均(${avg:.0f}M)を採用。"
            ).format(
                yr=fiscal_year_of_latest,
                val=latest_fcf/1e6,
                total=transient_total/1e6,
                summary=summary,
                avg=fcf_5yr_avg/1e6,
            )
        else:
            deviation_pct = abs(latest_fcf - fcf_5yr_avg) / abs(fcf_5yr_avg) * 100
            note = (
                "FY{yr} FCF(${val:.0f}M)が5年平均(${avg:.0f}M)から{dev:.0f}%乖離。"
                "一過性費用合計${total:.0f}M({summary})による影響と判断し除外。"
            ).format(
                yr=fiscal_year_of_latest,
                val=latest_fcf/1e6,
                avg=fcf_5yr_avg/1e6,
                dev=deviation_pct,
                total=transient_total/1e6,
                summary=summary,
            )
    else:
        action = "flagged"
        if rule == "latest_negative":
            note = (
                "FY{yr} FCF(${val:.1f}M)がマイナス。"
                "一過性費用の証拠はEPSアナライザーで確認されず。要確認。"
            ).format(yr=fiscal_year_of_latest, val=latest_fcf/1e6)
        else:
            deviation_pct = abs(latest_fcf - fcf_5yr_avg) / abs(fcf_5yr_avg) * 100
            note = (
                "FY{yr} FCF(${val:.0f}M)が5年平均(${avg:.0f}M)から{dev:.0f}%乖離。"
                "一過性費用の証拠はEPSアナライザーで確認されず。要確認。"
            ).format(
                yr=fiscal_year_of_latest,
                val=latest_fcf/1e6,
                avg=fcf_5yr_avg/1e6,
                dev=deviation_pct,
            )

    return FCFOutlierResult(
        detected=True,
        rule=rule,
        fiscal_year=fiscal_year_of_latest,
        fcf_value=latest_fcf,
        threshold_pct=threshold_pct,
        transient_found=transient_found,
        transient_items=transient_items,
        transient_total=transient_total,
        action=action,
        note=note,
    )


# デフォルトパラメータ
DEFAULT_RETENTION_RATE = 0.60
DEFAULT_ALPHA_CAP = 1.0
DEFAULT_RPO_DISCOUNT_RATE = 0.15
DEFAULT_FCF_FLOOR_RATIO = 0.08
DEFAULT_FCF_BASE_THRESHOLD = 1.5


if __name__ == "__main__":
    print("=== FCFベース自動判定テスト ===\n")

    # AMZN相当（急拡大 → recent_2yr期待）
    r1 = determine_fcf_base(
        fcf_5yr_avg=8_234_200_000,
        fcf_2yr_avg=50_000_000_000,
        fcf_list=[2e9, 3e9, 5e9, 25e9, 75e9]
    )
    print(f"AMZN相当: method={r1.method}  ratio={r1.ratio:.2f}  base=${r1.base_fcf/1e9:.1f}B")

    # MSFT相当（安定 → avg_5yr期待）
    r2 = determine_fcf_base(
        fcf_5yr_avg=65_284_800_000,
        fcf_2yr_avg=70_000_000_000,
        fcf_list=[55e9, 60e9, 65e9, 68e9, 72e9]
    )
    print(f"MSFT相当: method={r2.method}  ratio={r2.ratio:.2f}  base=${r2.base_fcf/1e9:.1f}B")

    # SOFI相当（5年平均マイナス → recent_2yr）
    r3 = determine_fcf_base(
        fcf_5yr_avg=-4_269_811_800,
        fcf_2yr_avg=500_000_000,
        fcf_list=[-3e9, -2e9, -1e9, 0.2e9, 0.8e9]
    )
    print(f"SOFI相当: method={r3.method}  ratio={r3.ratio:.2f}  base=${r3.base_fcf/1e9:.2f}B")


# ── FCF実力推定（調整済みEPS × FCF転換率）v7.2 ──────────────────────

@dataclass
class FCFEstimationResult:
    """EPSベースFCF推定結果"""
    applied: bool                  # 新方式が適用されたか
    method: str                    # "adj_eps_estimated" or "raw_fcf"
    adj_net_income: float          # 調整済み純利益
    conversion_rate: float         # FCF転換率
    estimated_fcf: float           # 推定FCF
    raw_fcf: float                 # 従来のFCFベース
    sector: str                    # セクター
    note: str                      # 理由

    def to_dict(self):
        return {
            "applied": self.applied,
            "method": self.method,
            "adj_net_income": self.adj_net_income,
            "conversion_rate": self.conversion_rate,
            "estimated_fcf": self.estimated_fcf,
            "raw_fcf": self.raw_fcf,
            "sector": self.sector,
            "note": self.note,
        }


def estimate_fcf_from_eps(
    ticker: str,
    raw_fcf: float,
    diluted_shares: int,
    sector: str,
    eps_data_dir: str,
    config_path: str = None,
) -> FCFEstimationResult:
    """
    調整済みEPS × FCF転換率 によるFCF実力推定（v7.2）

    EPSアナライザーのannual.jsonが存在する場合に常時適用。
    調整済みEPSがマイナスの場合は従来FCFにフォールバック。

    Args:
        ticker: 銘柄コード
        raw_fcf: 従来のFCFベース（5年平均 or 直近2年平均）
        diluted_shares: 希薄化後株式数
        sector: セクター（beta_config.jsonのsector値）
        eps_data_dir: EPSアナライザーのdataディレクトリ
        config_path: fcf_conversion_config.jsonのパス（Noneで自動探索）

    Returns:
        FCFEstimationResult
    """
    import json, os

    # ── 設定ファイルの読み込み ──
    if config_path is None:
        # pipelineから見た相対パス候補
        candidates = [
            os.path.join(os.path.dirname(__file__), 'fcf_conversion_config.json'),
            os.path.join(os.path.dirname(__file__), '..', 'fcf_conversion_config.json'),
            'fcf_conversion_config.json',
        ]
        config_path = next((p for p in candidates if os.path.exists(p)), None)

    if config_path is None or not os.path.exists(config_path):
        return FCFEstimationResult(
            applied=False, method="raw_fcf",
            adj_net_income=0, conversion_rate=0,
            estimated_fcf=raw_fcf, raw_fcf=raw_fcf,
            sector=sector, note="fcf_conversion_config.json が見つからない"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    # ── FCF転換率の決定 ──
    ticker_overrides = cfg.get('ticker_overrides', {})
    sector_rates = cfg.get('sector_conversion_rates', {})

    if ticker in ticker_overrides:
        conversion_rate = ticker_overrides[ticker]['conversion_rate']
        rate_source = f"ticker_override({ticker_overrides[ticker]['reason'][:30]})"
    else:
        conversion_rate = sector_rates.get(sector, sector_rates.get('default', 0.70))
        rate_source = f"sector({sector})"

    # ── EPSアナライザーから調整済みEPSを取得 ──
    eps_file = os.path.join(eps_data_dir, ticker, 'annual.json')
    if not os.path.exists(eps_file):
        return FCFEstimationResult(
            applied=False, method="raw_fcf",
            adj_net_income=0, conversion_rate=conversion_rate,
            estimated_fcf=raw_fcf, raw_fcf=raw_fcf,
            sector=sector, note=f"EPSデータなし({eps_file})"
        )

    with open(eps_file, 'r', encoding='utf-8') as f:
        eps_data = json.load(f)

    # 直近年度の調整済み純利益を取得
    years = eps_data.get('years', [])
    if not years:
        return FCFEstimationResult(
            applied=False, method="raw_fcf",
            adj_net_income=0, conversion_rate=conversion_rate,
            estimated_fcf=raw_fcf, raw_fcf=raw_fcf,
            sector=sector, note="EPSデータ年度なし"
        )

    # 直近年度の調整済み純利益
    latest = years[0]
    adj_net_income = latest.get('adjusted_net_income', 0)

    # ── フォールバック条件 ──
    # 調整済み純利益がマイナスの場合は従来FCFを使用
    if adj_net_income <= 0:
        return FCFEstimationResult(
            applied=False, method="raw_fcf",
            adj_net_income=adj_net_income, conversion_rate=conversion_rate,
            estimated_fcf=raw_fcf, raw_fcf=raw_fcf,
            sector=sector,
            note=f"調整済み純利益がマイナス(${adj_net_income/1e6:.0f}M) → 従来FCFを使用"
        )

    # ── FCF推定 ──
    estimated_fcf = adj_net_income * conversion_rate

    note = (
        f"調整済み純利益${adj_net_income/1e9:.2f}B × 転換率{conversion_rate:.0%}"
        f"[{rate_source}] = 推定FCF${estimated_fcf/1e9:.2f}B"
        f"（従来${raw_fcf/1e9:.2f}Bの{estimated_fcf/raw_fcf:.1f}倍）"
        if raw_fcf != 0 else
        f"調整済み純利益${adj_net_income/1e9:.2f}B × 転換率{conversion_rate:.0%}"
        f"[{rate_source}] = 推定FCF${estimated_fcf/1e9:.2f}B"
    )

    return FCFEstimationResult(
        applied=True,
        method="adj_eps_estimated",
        adj_net_income=adj_net_income,
        conversion_rate=conversion_rate,
        estimated_fcf=estimated_fcf,
        raw_fcf=raw_fcf,
        sector=sector,
        note=note,
    )
