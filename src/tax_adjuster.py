"""
tax_adjuster.py - 調整項目を税後ベースに変換
各調整項目が税引前(pre_tax=True)か税引後かを判定し、
実効税率(ETR)を用いて Net of Tax 調整額を算出する。

計算式:
  add_back (費用除外): adjusted = gross * (1 - ETR)
    → 費用を戻すと税節約分が消えるため税後利益増加は gross*(1-ETR)
  subtract (収益除外): adjusted = gross * (1 - ETR)
    → 収益を除外すると税負担分も消えるため税後利益減少は gross*(1-ETR)
  after-tax (pre_tax=False): adjusted = gross（変換不要）
"""


def _clamp_etr(etr: float) -> float:
    """実効税率を [0, 0.60] にクランプ（異常値防止）"""
    return max(0.0, min(0.60, etr))


def apply_tax_adjustments(adjustments: list, filing_data: dict) -> tuple[float, list]:
    """
    Parameters
    ----------
    adjustments  : detect_adjustments() の出力リスト
    filing_data  : extract_key_facts からの dict（pretax_income, tax_expense を含む）

    Returns
    -------
    (total_net_adjustment: float, detailed_adjustments: list)
      total_net_adjustment は GAAP 純利益に加算する税後調整合計
    """
    # 実効税率計算（異常値ガード付き）
    pretax = float(filing_data.get("pretax_income") or 0)
    tax    = float(filing_data.get("tax_expense")   or 0)

    if pretax > 0 and tax > 0:
        etr = _clamp_etr(tax / pretax)
    elif pretax < 0:
        # 赤字期は保守的にデフォルト税率を使用（調整項目が利益を水増しするのを防ぐ）
        etr = 0.21
    else:
        etr = 0.21  # 米国法定税率デフォルト

    total_net = 0.0
    detailed  = []

    for adj in adjustments:
        gross     = float(adj.get("amount", 0))
        direction = adj.get("direction", "add_back")
        pre_tax   = adj.get("pre_tax", True)

        # 税後調整額
        if pre_tax:
            net = gross * (1.0 - etr)
        else:
            net = gross  # already after-tax

        adj["net_amount"]        = round(net, 2)
        adj["effective_tax_rate"] = round(etr, 4)

        # 合計への加算方向
        if direction == "add_back":
            total_net += net      # 費用を戻す → 純利益増加
        elif direction == "subtract":
            total_net -= net      # 収益を除外 → 純利益減少
        # else: neutral（将来拡張用）

        detailed.append(adj)

    return round(total_net, 2), detailed
