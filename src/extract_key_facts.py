"""
SEC EDGARから企業の財務データを抽出するモジュール（最終版・10-K対応版）
- CIKマップファイルから銘柄のCIKを取得
- SECのCompany Facts APIから直接XBRLデータを取得
- 10-Qから四半期データ（Q1～Q3）を取得
- 10-Kから通期データを取得し、Q4を計算（通期 - Q1~Q3合計）
- 期間の長さ（60〜100日）で四半期データのみをフィルタリング
- 複数クラス株式（PLTRなど）の希薄化後株式数を合算
- 調整項目は元のXBRLタグ名で保存
- 詳細なデバッグ出力とエラーハンドリング
"""
import os
import csv
import json
import requests
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# ============================================
# 定数設定
# ============================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
CIK_FILE = os.path.join(CONFIG_DIR, "cik_lookup.csv")

HEADERS = {
    'User-Agent': 'jamablue01@gmail.com',  # 必須：連絡先メールアドレス
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

# 四半期とみなす期間の範囲（日数）
QUARTER_DAYS_MIN = 60
QUARTER_DAYS_MAX = 100

# ============================================
# CIKマップ管理
# ============================================
def load_cik_map() -> Dict[str, str]:
    """CIKマップをCSVから読み込む"""
    cik_map = {}
    try:
        if not os.path.exists(CIK_FILE):
            print(f"Warning: {CIK_FILE} not found. Creating empty mapping.")
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CIK_FILE, 'w', encoding='utf-8') as f:
                f.write("ticker,cik,name\n")
            return cik_map
        
        with open(CIK_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['ticker'] and row['cik']:
                    cik = row['cik'].strip().zfill(10)
                    cik_map[row['ticker'].strip().upper()] = cik
        print(f"Loaded {len(cik_map)} CIK mappings from {CIK_FILE}")
        return cik_map
    except Exception as e:
        print(f"Error loading CIK map: {e}")
        return {}

def save_cik_map(cik_map: Dict[str, str]) -> bool:
    """CIKマップをCSVに保存"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CIK_FILE, 'w', encoding='utf-8') as f:
            f.write("ticker,cik,name\n")
            for ticker, cik in sorted(cik_map.items()):
                f.write(f"{ticker},{cik},\n")
        print(f"Saved {len(cik_map)} CIK mappings to {CIK_FILE}")
        return True
    except Exception as e:
        print(f"Error saving CIK map: {e}")
        return False

def get_cik(ticker: str) -> str:
    """ティッカーからCIKを取得"""
    ticker = ticker.strip().upper()
    cik_map = load_cik_map()
    
    if ticker in cik_map:
        return cik_map[ticker]
    
    # SEC APIから直接取得
    print(f"CIK not found for {ticker} in local file. Trying SEC API...")
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.values():
                if item['ticker'] and item['ticker'].upper() == ticker:
                    cik = str(item['cik_str']).zfill(10)
                    cik_map[ticker] = cik
                    save_cik_map(cik_map)
                    return cik
    except Exception as e:
        print(f"SEC API lookup failed: {e}")
    
    raise Exception(f"CIK not found for {ticker}. Please add to {CIK_FILE}")

# ============================================
# SEC Company Facts APIからデータ取得
# ============================================
def fetch_company_facts(cik: str) -> Dict:
    """
    SEC Company Facts APIから企業の全XBRLファクトを取得
    Args:
        cik: 10桁のCIK番号
    Returns:
        Dict: 企業ファクトデータ
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    print(f"Fetching company facts from {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching company facts: {e}")
        return {}

def extract_value_from_facts(facts_data: Dict, us_gaap_tag: str, form_type: Optional[str] = None, limit: int = 40) -> List[Dict]:
    """
    Company Factsから特定タグの時系列データを抽出（オプションでフォーム種類でフィルタ）
    Args:
        facts_data: Company Facts APIのレスポンス
        us_gaap_tag: タグ名（例: 'NetIncomeLoss'）
        form_type: フォーム種類（'10-Q', '10-K'）でフィルタする場合は指定
        limit: 取得する最大件数
    Returns:
        List[Dict]: 各期のデータ（期間フィルタはかけない。後で必要に応じてフィルタ）
    """
    results = []
    try:
        if 'facts' not in facts_data or 'us-gaap' not in facts_data['facts']:
            return results
        
        if us_gaap_tag not in facts_data['facts']['us-gaap']:
            return results
        
        units_data = facts_data['facts']['us-gaap'][us_gaap_tag]['units']
        for unit_key in units_data:
            if 'USD' in unit_key or 'shares' in unit_key:
                for item in units_data[unit_key]:
                    if form_type and not item.get('form', '').startswith(form_type):
                        continue
                    # 期間情報があるものだけ採用（instantではなくduration）
                    if 'start' in item and 'end' in item:
                        results.append({
                            'end': item.get('end'),
                            'val': item.get('val'),
                            'filed': item.get('filed'),
                            'form': item.get('form'),
                            'unit': unit_key,
                            'start': item.get('start')
                        })
                break
    except Exception as e:
        print(f"Error extracting {us_gaap_tag}: {e}")
    
    # 日付でソート（新しい順）
    results.sort(key=lambda x: x['end'], reverse=True)
    return results[:limit]

def get_diluted_shares_from_facts(facts_data: Dict, form_type: Optional[str] = None, limit: int = 40) -> List[Dict]:
    """
    希薄化後株式数を取得（複数クラスがある場合は合算）
    戻り値の各要素は {'end': str, 'val': float, 'filed': str, 'form': str, 'unit': str, 'start': str} の形式
    """
    tag = "WeightedAverageNumberOfDilutedSharesOutstanding"
    try:
        if 'facts' not in facts_data or 'us-gaap' not in facts_data['facts']:
            return []
        if tag not in facts_data['facts']['us-gaap']:
            return []
        
        units_data = facts_data['facts']['us-gaap'][tag]['units']
        # 通常は 'shares' 単位
        for unit_key in units_data:
            if 'shares' in unit_key:
                # 同じend日付のものをグループ化して合計
                period_map = {}
                for item in units_data[unit_key]:
                    if form_type and not item.get('form', '').startswith(form_type):
                        continue
                    if 'start' in item and 'end' in item:
                        key = item['end']
                        if key not in period_map:
                            period_map[key] = {
                                'end': key,
                                'val': 0,
                                'filed': item.get('filed'),
                                'form': item.get('form'),
                                'unit': unit_key,
                                'start': item.get('start')
                            }
                        period_map[key]['val'] += item.get('val', 0)
                
                # マップをリストに変換
                results = list(period_map.values())
                results.sort(key=lambda x: x['end'], reverse=True)
                return results[:limit]
    except Exception as e:
        print(f"Error getting diluted shares: {e}")
    return []

# ============================================
# メイン抽出関数（10-K対応版）
# ============================================
def extract_quarterly_facts(ticker: str, years: int = 10) -> List[Dict[str, Any]]:
    """
    四半期データを取得（SEC API直アクセス＋期間フィルタリング＋10-KからのQ4補完）
    Args:
        ticker: 銘柄ティッカー
        years: 取得する年数
    Returns:
        List[Dict]: 四半期データのリスト（Q1～Q4が含まれる）
    """
    try:
        # CIK取得
        cik = get_cik(ticker)
        print(f"CIK: {cik}")
        
        # Company Facts取得
        facts = fetch_company_facts(cik)
        if not facts:
            print(f"No facts data for {ticker}")
            return []
        
        # ---------- 10-QからQ1～Q3を取得（期間フィルタリングあり）----------
        net_income_10q = extract_value_from_facts(facts, 'NetIncomeLoss', form_type="10-Q", limit=years*6)
        # 期間フィルタ（60～100日）を適用して四半期データのみ残す
        quarterly_10q = []
        for item in net_income_10q:
            start = datetime.strptime(item['start'], '%Y-%m-%d')
            end = datetime.strptime(item['end'], '%Y-%m-%d')
            days_diff = (end - start).days
            if QUARTER_DAYS_MIN <= days_diff <= QUARTER_DAYS_MAX:
                quarterly_10q.append(item)
        
        # 希薄化後株式数（10-Q）
        diluted_10q_raw = get_diluted_shares_from_facts(facts, form_type="10-Q", limit=years*6)
        diluted_10q = {}
        for item in diluted_10q_raw:
            start = datetime.strptime(item['start'], '%Y-%m-%d')
            end = datetime.strptime(item['end'], '%Y-%m-%d')
            days_diff = (end - start).days
            if QUARTER_DAYS_MIN <= days_diff <= QUARTER_DAYS_MAX:
                diluted_10q[item['end']] = item['val']
        
        # その他の主要項目（必要に応じて）
        # （SBCなどはadjustment_detectorで使うため、後でperiod_dataに含める）
        sbc_10q = extract_value_from_facts(facts, 'ShareBasedCompensation', form_type="10-Q", limit=years*6)
        # 期間フィルタ（簡略化のため、後でend日付でマッチングする方式でも可）
        
        # ---------- 10-Kから通期データを取得 ----------
        net_income_10k = extract_value_from_facts(facts, 'NetIncomeLoss', form_type="10-K", limit=years*2)
        diluted_10k_raw = get_diluted_shares_from_facts(facts, form_type="10-K", limit=years*2)
        # 通期の希薄化後株式数（複数あれば合算）
        diluted_10k = {}
        for item in diluted_10k_raw:
            diluted_10k[item['end']] = item['val']
        
        # ---------- 10-Qデータを period_data 形式に変換 ----------
        quarters_map = {}  # key: end_date
        for item in quarterly_10q:
            end_date = item['end']
            quarters_map[end_date] = {
                'filing_date': end_date,
                'form': '10-Q',
                'net_income': {'value': item['val'], 'unit': item['unit']},
                'start': item['start'],
                'end': item['end']
            }
            # 希薄化後株式数を追加
            if end_date in diluted_10q:
                quarters_map[end_date]['diluted_shares'] = {'value': diluted_10q[end_date], 'unit': 'shares'}
        
        # 他のタグも追加（例：SBC）
        for item in sbc_10q:
            end_date = item['end']
            if end_date in quarters_map:
                quarters_map[end_date]['us-gaap:ShareBasedCompensation'] = {'value': item['val'], 'unit': item['unit']}
        # 必要に応じて他の調整項目も同様に追加
        
        # ---------- 10-KからQ4を計算して追加 ----------
        # 年度ごとに10-Kの通期データを整理
        for k_item in net_income_10k:
            end_date = k_item['end']  # 10-Kの提出日（例：2026-01-25）
            # 通期の年度を特定（提出日の年）
            fiscal_year = end_date[:4]
            
            # 同じ年度のQ1～Q3を quarters_map から抽出
            q1_q3 = []
            for q_date, q_data in quarters_map.items():
                if q_data.get('form') == '10-Q' and q_date[:4] == fiscal_year:
                    # 期間のstart～endが約90日であることを前提に、Q1～Q3とみなす
                    q_start = datetime.strptime(q_data['start'], '%Y-%m-%d')
                    q_end = datetime.strptime(q_data['end'], '%Y-%m-%d')
                    days = (q_end - q_start).days
                    if QUARTER_DAYS_MIN <= days <= QUARTER_DAYS_MAX:
                        q1_q3.append(q_data)
            
            if len(q1_q3) == 3:
                # Q1～Q3のnet_income合計
                q1q3_sum = sum(normalize_value(q['net_income']) for q in q1_q3)
                annual_net = k_item['val']
                q4_net = annual_net - q1q3_sum
                
                # 希薄化後株式数（通期のものを代用）
                diluted_val = diluted_10k.get(end_date, 0)
                if diluted_val == 0 and len(q1_q3) > 0:
                    # フォールバック：Q3の株式数を使う
                    diluted_val = normalize_value(q1_q3[-1].get('diluted_shares', {'value':0}))
                
                # Q4のデータを作成
                q4_data = {
                    'filing_date': end_date,
                    'form': '10-K',
                    'net_income': {'value': q4_net, 'unit': 'USD'},
                    'diluted_shares': {'value': diluted_val, 'unit': 'shares'},
                    'start': None,  # 期間情報は不要
                    'end': end_date
                }
                # quarters_mapに追加（end_dateが重複する可能性は低い）
                quarters_map[f"{fiscal_year}-Q4"] = q4_data  # キーは便宜上
                print(f"  Calculated Q4 for {fiscal_year}: net_income={q4_net:,.0f}, diluted_shares={diluted_val:,.0f}")
            else:
                print(f"  Warning: Incomplete Q1-Q3 for fiscal year {fiscal_year} (found {len(q1_q3)} quarters)")
        
        # ---------- 最終的なリストに変換 ----------
        quarterly_list = []
        for key, data in sorted(quarters_map.items(), reverse=True):
            # 必須データの確認
            if 'net_income' in data and 'diluted_shares' in data:
                # 元のend_dateをfiling_dateとして保持（キーがQ4の場合はend_dateを使う）
                if 'filing_date' not in data:
                    data['filing_date'] = data['end']
                quarterly_list.append(data)
                net_val = normalize_value(data['net_income'])
                shr_val = normalize_value(data['diluted_shares'])
                print(f"  ✓ {data['filing_date']}: net_income={net_val:,.0f}, diluted_shares={shr_val:,.0f}")
            else:
                missing = []
                if 'net_income' not in data:
                    missing.append('net_income')
                if 'diluted_shares' not in data:
                    missing.append('diluted_shares')
                print(f"  ✗ {data.get('filing_date', 'unknown')}: missing {', '.join(missing)}")
        
        print(f"\n{ticker}: {len(quarterly_list)}件の四半期データを取得")
        return quarterly_list
        
    except Exception as e:
        print(f"{ticker} データ取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return []

def normalize_value(value_dict: Optional[Dict]) -> float:
    """
    単位正規化（すべてUSD absolute valueに統一）
    Args:
        value_dict: {"value": 数値, "unit": "USD"|"shares"|"thousands"|...}
    Returns:
        float: 正規化された値
    """
    if not value_dict:
        return 0.0
    
    value = float(value_dict.get("value", 0))
    unit = value_dict.get("unit", "USD").lower()
    
    if unit in ["thousands", "thousand"]:
        return value * 1_000
    elif unit in ["millions", "million"]:
        return value * 1_000_000
    elif unit in ["billions", "billion"]:
        return value * 1_000_000_000
    else:
        return value

# ============================================
# テスト用メイン関数
# ============================================
def main():
    """テスト実行用"""
    ticker = "NVDA"  # PLTRでもテスト可能
    print(f"Testing data extraction for {ticker}...")
    
    data = extract_quarterly_facts(ticker, years=5)
    
    if data:
        print(f"\nSuccessfully extracted {len(data)} quarters:")
        for i, quarter in enumerate(data[:5]):
            print(f"\nQuarter {i+1}: {quarter['filing_date']} ({quarter.get('form', 'unknown')})")
            net = normalize_value(quarter.get('net_income'))
            shares = normalize_value(quarter.get('diluted_shares'))
            print(f"  Net Income: {net:,.0f} USD")
            print(f"  Diluted Shares: {shares:,.0f}")
            if shares > 0:
                eps = net / shares
                print(f"  Implied EPS: {eps:.4f} USD")
            
            # 調整項目の例
            sbc = quarter.get('us-gaap:ShareBasedCompensation')
            if sbc:
                sbc_val = normalize_value(sbc)
                print(f"  SBC: {sbc_val:,.0f} USD")
    else:
        print("No data extracted")

if __name__ == "__main__":
    main()
