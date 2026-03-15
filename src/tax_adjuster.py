"""
tax_adjuster.py
税効果適用モジュール
- 検出された調整項目（税前/税後）に実効税率を適用
- 各項目に net_amount を追加
- 純額合計と詳細リストを返す
"""
from typing import Dict, List, Any, Tuple

def apply_tax_adjustments(adjustments: List[Dict[str, Any]], period_data: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
    """
    調整項目に税効果を適用する
    Args:
        adjustments: detect_adjustments で得られた調整項目リスト
        period_data: 当該四半期のデータ（実効税率を取得するために使用）
    Returns:
        Tuple[float, List[Dict]]:
            - net_adjustment_total: 税効果適用後の調整額合計（純利益への加算額）
            - detailed: 税効果適用後の詳細リスト（各項目に net_amount を追加）
    """
    # 実効税率を取得（デフォルト0.21、period_data にあればそれを使う）
    # 注意：period_data 内の tax_expense と pretax_income から計算するのが理想的だが、
    # 簡易的に config や固定値を使うこともある。ここでは固定値を使用。
    # 必要に応じて period_data から動的に計算するロジックに変更可能。
    tax_rate = 0.21  # デフォルト税率
    
    # period_data から税引前利益と税費用が取得できれば計算する（オプション）
    if 'pretax_income' in period_data and 'tax_expense' in period_data:
        from extract_key_facts import normalize_value
        pretax = normalize_value(period_data['pretax_income'])
        tax = normalize_value(period_data['tax_expense'])
        if pretax != 0:
            # 実効税率 = 税費用 / 税引前利益（ただしマイナスの場合は絶対値で計算することも）
            # 簡易的に絶対値で計算（税利益の場合もあるので注意）
            computed_rate = abs(tax / pretax) if pretax != 0 else 0.21
            # 常識的な範囲内かチェック（0%〜50%）
            if 0.0 <= computed_rate <= 0.5:
                tax_rate = computed_rate
                print(f"      Using computed tax rate: {tax_rate:.2%}")
    
    detailed = []
    net_total = 0.0
    
    for adj in adjustments:
        # 単位情報を保持したままコピー
        new_adj = adj.copy()
        
        amount = adj['amount']
        unit = adj.get('unit', 'USD')
        pre_tax = adj['pre_tax']
        
        if pre_tax:
            # 税前項目 → 税効果適用
            # 金額は単位付きなので、一旦数値として扱い、net_amount も同じ単位とする
            # ただし、計算上は単位を気にせず数値として扱う（すべて USD と仮定）
            net_amount = amount * (1 - tax_rate)
        else:
            # 税後項目 → そのまま
            net_amount = amount
        
        new_adj['net_amount'] = net_amount
        new_adj['tax_rate_applied'] = tax_rate if pre_tax else 0.0
        
        detailed.append(new_adj)
        net_total += net_amount
    
    return net_total, detailed

# テスト用
if __name__ == "__main__":
    # 簡易テスト
    sample_adjustments = [
        {
            "item_name": "株式報酬費用",
            "amount": 155339000,
            "unit": "USD",
            "direction": "add_back",
            "pre_tax": True,
            "reason": "非現金費用",
            "extracted_from": "us-gaap:ShareBasedCompensation",
            "category": "株式報酬 (SBC)"
        },
        {
            "item_name": "非継続事業損益",
            "amount": -5000000,
            "unit": "USD",
            "direction": "add_back",
            "pre_tax": False,
            "reason": "継続事業ベース調整",
            "extracted_from": "us-gaap:IncomeLossFromDiscontinuedOperationsNetOfTax",
            "category": "非継続事業"
        }
    ]
    
    sample_period = {
        "pretax_income": {"value": 1000000000, "unit": "USD"},
        "tax_expense": {"value": 210000000, "unit": "USD"}
    }
    
    total, details = apply_tax_adjustments(sample_adjustments, sample_period)
    print(f"Net adjustment total: {total:,.0f} USD")
    for d in details:
        print(f"  {d['item_name']}: gross={d['amount']:,.0f} {d['unit']}, net={d['net_amount']:,.0f} (tax rate: {d.get('tax_rate_applied',0):.2%})")
