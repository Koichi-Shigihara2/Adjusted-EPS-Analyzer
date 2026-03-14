"""
extract_key_facts.py - SEC EDGAR から全 filing のキーファクトを取得
edgartools の CompanyFacts を使って全期間の財務データを取得し、
filing ごとにマッチングして返す。
"""
import json
import os
import sys
from typing import Optional

from edgar import Company, set_identity

set_identity("jamablue01@gmail.com")

# ─── 設定ロード ────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "..", "config", "adjustment_items.json")


def _load_all_xbrl_tags() -> list[str]:
    """adjustment_items.json から全 XBRL タグを収集"""
    tags = set()
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            config = json.load(f)
        for cat in config.get("categories", []):
            for item in cat.get("sub_items", []):
                for tag in item.get("xbrl_tags", []):
                    tags.add(tag)
    except Exception as e:
        print(f"[WARN] adjustment_items.json 読み込みエラー: {e}")
    return list(tags)


# 取得する標準財務タグ（調整項目以外）
_CORE_TAGS = [
    "us-gaap:NetIncomeLoss",
    "us-gaap:NetIncomeLossAttributableToParent",
    "us-gaap:NetIncomeLossAttributableToNoncontrollingInterest",
    "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
    "us-gaap:IncomeTaxExpenseBenefit",
    "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
    "dei:EntityCommonStockSharesOutstanding",
    "us-gaap:EarningsPerShareDiluted",
    "us-gaap:EarningsPerShareBasic",
    "us-gaap:Revenues",
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:GrossProfit",
]


def _strip_ns(tag: str) -> str:
    """us-gaap:NetIncomeLoss → NetIncomeLoss"""
    return tag.split(":")[-1] if ":" in tag else tag


def _get_val_col(df) -> Optional[str]:
    """DataFrame の値カラム名を推定（val / value / Value）"""
    for col in ("val", "value", "Value"):
        if col in df.columns:
            return col
    return None


def _build_facts_map(facts, all_tags: list[str]) -> dict:
    """
    CompanyFacts から {full_tag: DataFrame} のマップを構築
    各 DataFrame 列: end, val_col, accn, form, filed, fy, fp  (など)
    """
    facts_map = {}
    for tag in all_tags:
        concept = _strip_ns(tag)
        # edgartools は namespace なしの concept 名でアクセス
        try:
            df = facts.to_pandas(concept)
            if df is not None and not df.empty:
                facts_map[tag] = df
        except Exception:
            pass
        # フォールバック: full tag で試す
        if tag not in facts_map:
            try:
                df = facts.to_pandas(tag)
                if df is not None and not df.empty:
                    facts_map[tag] = df
            except Exception:
                pass
    return facts_map


def _pick_value(df, accession: str, period_end: str):
    """
    特定の accession_no または period_end に対応する値を取得。
    優先順位: accession_no → period_end → 最新
    """
    if df is None or df.empty:
        return None

    val_col = _get_val_col(df)
    if not val_col:
        return None

    # 正規化列名
    cols = {c.lower(): c for c in df.columns}

    def safe_col(name):
        return cols.get(name)

    accn_col   = safe_col("accn") or safe_col("accession_no")
    end_col    = safe_col("end")

    # 1) accession_no でフィルタ
    if accn_col and accession:
        norm_acc = accession.replace("-", "")
        filtered = df[df[accn_col].astype(str).str.replace("-", "") == norm_acc]
        if not filtered.empty:
            try:
                return float(filtered.sort_values(end_col or accn_col).iloc[-1][val_col])
            except Exception:
                pass

    # 2) period_end でフィルタ
    if end_col and period_end:
        filtered = df[df[end_col].astype(str).str[:10] == period_end[:10]]
        if not filtered.empty:
            try:
                return float(filtered.iloc[-1][val_col])
            except Exception:
                pass

    # 3) 最新値
    try:
        return float(df.iloc[-1][val_col])
    except Exception:
        return None


def _infer_period_type(form: str) -> str:
    """フォーム種別から期間タイプ推定"""
    form_upper = (form or "").upper()
    if "10-K" in form_upper:
        return "A"
    return "Q"


def _infer_fiscal_quarter(period_of_report: str, form: str) -> Optional[int]:
    """fiscal_quarter を推定 (10-K なら 4)"""
    if _infer_period_type(form) == "A":
        return 4
    try:
        month = int(period_of_report[5:7])
        return (month - 1) // 3 + 1
    except Exception:
        return None


# ─── メイン公開関数 ────────────────────────────────────────────────

def extract_all_filings_for_ticker(ticker: str) -> list[dict]:
    """
    ticker の全 filing（最大 45 件）についてキーファクトを返す。
    Returns: list of filing_facts dict
    """
    try:
        company = Company(ticker)
    except Exception as e:
        print(f"  [ERROR] Company({ticker}) 失敗: {e}")
        return []

    # ① 全 filing のメタデータ取得
    try:
        filings_obj = company.get_filings(form=["10-Q", "10-K"])
        filings_list = list(filings_obj[:45])
    except Exception as e:
        print(f"  [ERROR] get_filings 失敗: {e}")
        return []

    if not filings_list:
        return []

    # ② CompanyFacts 取得（全期間一括）
    try:
        facts = company.get_facts()
    except Exception as e:
        print(f"  [WARN] get_facts 失敗、個別取得へフォールバック: {e}")
        facts = None

    # 取得対象タグ: コアタグ + 調整項目タグ
    all_tags = _CORE_TAGS + _load_all_xbrl_tags()
    all_tags = list(set(all_tags))  # 重複除去

    # ③ facts_map 構築
    facts_map = _build_facts_map(facts, all_tags) if facts else {}

    # ④ filing ごとにデータ構築
    results = []
    for filing in filings_list:
        try:
            accession_no      = str(getattr(filing, "accession_no",    "") or "")
            period_of_report  = str(getattr(filing, "period_of_report","") or "")
            form              = str(getattr(filing, "form",            "") or "")
            filed_at          = str(getattr(filing, "filing_date",     "") or
                                    getattr(filing, "filed",           "") or "")

            if not period_of_report:
                continue

            period_type     = _infer_period_type(form)
            fiscal_quarter  = _infer_fiscal_quarter(period_of_report, form)
            try:
                fiscal_year = int(period_of_report[:4])
            except Exception:
                fiscal_year = None

            def gv(tag):
                """get value for this filing"""
                df = facts_map.get(tag)
                return _pick_value(df, accession_no, period_of_report)

            # 純利益（NCI 調整済み親会社帰属）
            net_income_total = gv("us-gaap:NetIncomeLoss")
            net_income_parent= gv("us-gaap:NetIncomeLossAttributableToParent")
            nci              = gv("us-gaap:NetIncomeLossAttributableToNoncontrollingInterest") or 0
            # 親会社帰属を優先; なければ total - nci
            net_income = (net_income_parent or
                          (net_income_total - nci if net_income_total is not None else None) or
                          net_income_total or 0)

            # 税金関連
            tax_expense    = gv("us-gaap:IncomeTaxExpenseBenefit") or 0
            pretax_income  = gv("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes") or 0

            # 希薄化後加重平均株式数（Weighted Average — 期末点ではない）
            diluted_shares = (gv("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding") or
                              gv("us-gaap:WeightedAverageNumberOfSharesOutstandingBasic") or
                              gv("dei:EntityCommonStockSharesOutstanding") or 1)

            # GAAP EPS
            gaap_eps_diluted = (gv("us-gaap:EarningsPerShareDiluted") or
                                (net_income / diluted_shares if diluted_shares else 0))
            gaap_eps_basic   = (gv("us-gaap:EarningsPerShareBasic") or gaap_eps_diluted)

            # 売上
            revenue = (gv("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax") or
                       gv("us-gaap:Revenues") or 0)

            # 調整項目検出用の raw_facts（full tag 名でキー）
            raw_facts = {}
            for tag in all_tags:
                val = gv(tag)
                if val is not None:
                    raw_facts[tag] = val
                    # snippet（UIで表示する元データ文字列）
                    raw_facts[f"{tag}_snippet"] = (
                        f"XBRL tag: {_strip_ns(tag)} = {val:,.0f} "
                        f"(period: {period_of_report}, form: {form})"
                    )

            results.append({
                "ticker":           ticker,
                "accession_no":     accession_no,
                "period_of_report": period_of_report,
                "fiscal_year":      fiscal_year,
                "fiscal_quarter":   fiscal_quarter,
                "period_type":      period_type,
                "form":             form,
                "filed_at":         filed_at,
                "net_income":       net_income,
                "tax_expense":      tax_expense,
                "pretax_income":    pretax_income,
                "diluted_shares":   diluted_shares,
                "gaap_eps":         gaap_eps_diluted,
                "gaap_eps_basic":   gaap_eps_basic,
                "revenue":          revenue,
                "raw_facts":        raw_facts,
            })

        except Exception as e:
            print(f"    [WARN] filing {getattr(filing, 'accession_no','?')} エラー: {e}")
            continue

    return results
