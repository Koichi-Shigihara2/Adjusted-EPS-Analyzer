"""
eps_calculator.py - 実質 EPS 計算
計算式:
  Adjusted Net Income = GAAP Net Income + total_net_adjustment
  Adjusted EPS (Diluted) = Adjusted Net Income
                           / Weighted Average Diluted Shares Outstanding
"""


def calculate_eps(filing_data: dict, net_adjustment: float,
                  detailed_adjustments: list) -> dict:
    """
    Parameters
    ----------
    filing_data        : extract_key_facts の出力 dict
    net_adjustment     : tax_adjuster の税後調整合計（正=加算）
    detailed_adjustments : 調整項目詳細リスト

    Returns
    -------
    filing_data に EPS 関連フィールドを追加した dict
    """
    # ① 基礎数値取得
    gaap_net_income  = float(filing_data.get("net_income")  or 0)
    # 希薄化後 加重平均株式数（Weighted Average Diluted Shares）
    # ← 期末残高(期末点)ではなく期間中の加重平均を使用することが必須要件
    diluted_shares   = float(filing_data.get("diluted_shares") or
                             filing_data.get("shares")          or 1)
    gaap_eps_diluted = float(filing_data.get("gaap_eps") or
                             (gaap_net_income / diluted_shares if diluted_shares else 0))

    # ② 調整後純利益
    adjusted_net_income = gaap_net_income + net_adjustment

    # ③ 調整後 EPS（希薄化後）
    adjusted_eps = adjusted_net_income / diluted_shares if diluted_shares else 0

    # ④ 結果 dict 構築（filing_data を base にして EPS フィールドを追加）
    result = {**filing_data}
    result.update({
        "gaap_net_income":       gaap_net_income,
        "gaap_eps":              round(gaap_eps_diluted, 4),
        "adjusted_net_income":   round(adjusted_net_income, 2),
        "adjusted_eps":          round(adjusted_eps, 4),
        "diluted_shares_used":   diluted_shares,
        # 計算式を JSON に記録（透明性・監査対応）
        "eps_formula":           (
            f"Adjusted EPS = {adjusted_net_income:,.0f} / {diluted_shares:,.0f}"
            f" = {adjusted_eps:.4f}"
        ),
        "adjustments":           detailed_adjustments,
        # raw_facts は保存データサイズ削減のため省略（必要なら True に）
        # "raw_facts": filing_data.get("raw_facts", {}),
    })
    # raw_facts は出力から除外（大容量・UI 不要）
    result.pop("raw_facts", None)

    return result
