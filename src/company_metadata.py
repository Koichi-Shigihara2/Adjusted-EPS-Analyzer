"""
企業メタデータ取得モジュール
- SECのSubmissions APIから企業情報（SICコード、会社名など）を取得
"""
import requests
from typing import Dict, Optional

HEADERS = {
    'User-Agent': 'jamablue01@gmail.com',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

def get_company_metadata(cik: str) -> Dict:
    """
    CIKから企業メタデータを取得
    Args:
        cik: 10桁のCIK番号（例: '0001321655'）
    Returns:
        Dict: {
            'name': 会社名,
            'sic': SICコード,
            'sic_description': SIC説明,
            'exchange': 取引所,
            'tickers': ティッカーリスト
        }
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data.get('name', ''),
                'sic': data.get('sic', ''),
                'sic_description': data.get('sicDescription', ''),
                'exchange': data.get('exchange', ''),
                'tickers': data.get('tickers', [])
            }
        else:
            print(f"SEC API returned status {response.status_code} for CIK {cik}")
    except Exception as e:
        print(f"Error fetching metadata for CIK {cik}: {e}")
    return {}
