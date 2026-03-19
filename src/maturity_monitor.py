"""
maturity_monitor.py
成熟度監視モジュール（SBC乖離率・SBC/売上高比率からアラート生成）
"""
from typing import Dict, List, Any

class MaturityMonitor:
    """SBCの成熟度を監視するクラス"""
    
    def __init__(self, config: Dict):
        self.threshold_ratio = config.get('threshold_ratio', 0.15)  # SBC乖離率
        self.threshold_sbc_to_revenue = config.get('threshold_sbc_to_revenue', 0.25)  # SBC/売上高
    
    def monitor(self, quarterly_results: List[Dict]) -> Dict:
        """
        最新の四半期データを分析し、アラートを返す
        """
        if not quarterly_results:
            return {"alert": None, "sbc_ratio": 0, "sbc_to_revenue": 0}
        
        latest = quarterly_results[-1]
        sbc_amount = 0
        revenue = latest.get('revenue', 0)  # 売上高が必要な場合（現在は未取得なので0になる）
        
        # adjustments から SBC を探す
        for adj in latest.get('adjustments', []):
            if adj.get('item_id') == 'sbc':
                sbc_amount = adj.get('net_amount', 0)
                break
        
        gaap_eps = latest.get('gaap_eps', 0)
        adjusted_eps = latest.get('adjusted_eps', 0)
        
        # SBC乖離率 = (adjusted_eps - gaap_eps) / gaap_eps（分母が0なら0扱い）
        if gaap_eps != 0:
            sbc_ratio = (adjusted_eps - gaap_eps) / gaap_eps
        else:
            sbc_ratio = 0
        
        # SBC/売上高（売上高がない場合は計算しない）
        sbc_to_revenue = sbc_amount / revenue if revenue and revenue != 0 else 0
        
        alert = None
        if sbc_ratio > self.threshold_ratio:
            alert = f"SBC乖離率が{self.threshold_ratio:.0%}を超えています（{sbc_ratio:.1%}）"
        elif sbc_to_revenue > self.threshold_sbc_to_revenue:
            alert = f"SBC/売上高が{self.threshold_sbc_to_revenue:.0%}を超えています（{sbc_to_revenue:.1%}）"
        
        return {
            "alert": alert,
            "sbc_ratio": sbc_ratio,
            "sbc_to_revenue": sbc_to_revenue,
            "threshold_ratio": self.threshold_ratio,
            "threshold_sbc_to_revenue": self.threshold_sbc_to_revenue
        }
