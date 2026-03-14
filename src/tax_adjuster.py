def apply_tax(adjustments, data):
    """
    調整項目ごとに実効税率を適用し、Net of Tax（税後影響額）を算出する。
    """
    # 実効税率 (Effective Tax Rate) の算出
    # 税引前利益が0以下の場合は、標準税率（例: 21%）をフォールバックとして使用
    if data["pretax_income"] and data["pretax_income"] > 0:
        etr = data["tax_expense"] / data["pretax_income"]
    else:
        etr = 0.21 

    total_net_adjustment = 0
    for adj in adjustments:
        if adj["pretax"]:
            # 費用（ポジティブ調整）なら節税効果分を差し引く
            # 収益（ネガティブ調整）なら税負担分を差し引く
            net_amount = adj["amount"] * (1 - etr)
        else:
            # すでに税引後の項目（非継続事業など）はそのまま
            net_amount = adj["amount"]
        
        adj["net_amount"] = net_amount
        total_net_adjustment += net_amount
        
    return total_net_adjustment
