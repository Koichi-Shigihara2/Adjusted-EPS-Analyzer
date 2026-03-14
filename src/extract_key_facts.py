"""
SEC EDGARから企業の財務データを抽出するモジュール（SEC API直アクセス版・最終調整版）
- CIKマップファイルから銘柄のCIKを取得
- SECのCompany Facts APIから直接XBRLデータを取得
- 複数クラス株式（PLTRなど）にも対応（数値の合算）
- YTDとQuarterの混同を回避するための会計期間フィルタリング
- SEC APIのレートリミット対策（リトライ＋待機）
"""
import os
import csv
import json
import time
import random
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

# リトライ設定付きセッション
def get_requests_session():
    """リトライ機能付きのrequestsセッションを返す"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

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
        session = get_requests_session()
        url = "https://www.sec.gov/files/company_tickers.json"
        response = session.get(url, headers=HEADERS, timeout=10)
        time.sleep(0.1)  # レートリミット対策
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
        session = get_requests_session()
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        # レートリミット対策：ランダムな待機時間を入れる（0.1〜0.3秒）
        time.sleep(random.uniform(0.1, 0.3))
        return response.json()
    except Exception as e:
        print(f"Error fetching company facts: {e}")
        return {}

def is_quarterly_period(item: Dict) -> bool:
    """
    アイテムが四半期（3ヶ月）のデータかどうかを判定する。
    YTD（Year-to-Date）やAnnualと混同しないようにするためのフィルター。
    """
    # フォームが10-Qであれば基本的に四半期
    if item.get('form', '').startswith('10-Q'):
        # より厳密にする場合は、期間の長さをチェックすることも可能
        # 例：startとendの差が80〜100日程度かを確認するロジックを追加
        # ここでは簡易的にfp（fiscal period）がQ1,Q2,Q3であることを確認
        fp = item.get('fp')
        if fp in ['Q1', 'Q2', 'Q3']:
            return True
        # fpがない場合でも、startとendが存在すれば期間の長さをチェック
        if 'start' in item and 'end' in item:
            try:
                start = datetime.strptime(item['start'], '%Y-%m-%d')
                end = datetime.strptime(item['end'], '%Y-%m-%d')
                days_diff = (end - start).days
                # 四半期はおおよそ90日前後（80〜100日を許容）
                if 80 <= days_diff <= 100:
                    return True
            except:
                pass
    return False

def extract_value_from_facts(facts_data: Dict, us_gaap_tag: str, form_type: str = "10-Q", limit: int = 40) -> List[Dict]:
    """
    Company Factsから特定タグの時系列データを抽出
    - YTDとQuarterの混同を防ぐため、is_quarterly_periodでフィルタリング
    - 複数クラスがある場合も、すべての値を合算する（'concept'が同一なら、units内の全アイテムを対象とする）
    Args:
        facts_data: Company Facts APIのレスポンス
        us_gaap_tag: タグ名（例: 'NetIncomeLoss'）
        form_type: フォーム種類（'10-K', '10-Q'）
        limit: 取得する最大件数
    Returns:
        List[Dict]: 各期のデータ（同一periodの値は合算される）
    """
    results_dict = {}  # key: end_date, value: 合計値と情報
    try:
        if 'facts' not in facts_data or 'us-gaap' not in facts_data['facts']:
            return []
        if us_gaap_tag not in facts_data['facts']['us-gaap']:
            return []

        units_data = facts_data['facts']['us-gaap'][us_gaap_tag]['units']
        # 全ての単位をチェック（USD, sharesなど）
        for unit_key, items in units_data.items():
            for item in items:
                # フォーム種類でフィルタ（'10-Q'で始まるもの）
                if not item.get('form', '').startswith(form_type):
                    continue
                # 四半期データのみを対象とする
                if form_type == "10-Q" and not is_quarterly_period(item):
                    # デバッグ用：除外されたアイテムを確認したい場合はコメント解除
                    # print(f"    Skipping non-quarterly item: {item.get('end')} ({item.get('fp')})")
                    continue

                end_date = item.get('end')
                if not end_date:
                    continue

                val = item.get('val', 0)
                # 同じend_dateの値を合算（複数クラス対応）
                if end_date not in results_dict:
                    results_dict[end_date] = {
                        'end': end_date,
                        'val': val,
                        'filed': item.get('filed'),
                        'form': item.get('form'),
                        'unit': unit_key,
                        'fp': item.get('fp'),
                        'start': item.get('start')
                    }
                else:
                    # 同じend_dateの別クラスの値を加算
                    results_dict[end_date]['val'] += val
                    # 必要に応じて他の情報もマージ
    except Exception as e:
        print(f"Error extracting {us_gaap_tag}: {e}")

    # 辞書をリストに変換し、日付でソート（新しい順）
    results = list(results_dict.values())
    results.sort(key=lambda x: x['end'], reverse=True)
    return results[:limit]

def extract_quarterly_facts(ticker: str, years: int = 10) -> List[Dict[str, Any]]:
    """
    四半期データを取得（SEC API直アクセス版・期間判定・複数クラス合算対応）
    Args:
        ticker: 銘柄ティッカー
        years: 取得する年数
    Returns:
        List[Dict]: 四半期データのリスト
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

        # 各タグのデータを取得（四半期のみ）
        net_income_data = extract_value_from_facts(facts, 'NetIncomeLoss', form_type="10-Q", limit=years*4)
        diluted_shares_data = extract_value_from_facts(facts, 'WeightedAverageNumberOfDilutedSharesOutstanding', form_type="10-Q", limit=years*4)
        basic_shares_data = extract_value_from_facts(facts, 'WeightedAverageNumberOfSharesOutstandingBasic', form_type="10-Q", limit=years*4)
        pretax_data = extract_value_from_facts(facts, 'IncomeLossFromContinuingOperationsBeforeIncomeTaxes', form_type="10-Q", limit=years*4)
        tax_data = extract_value_from_facts(facts, 'IncomeTaxExpenseBenefit', form_type="10-Q", limit=years*4)
        sbc_data = extract_value_from_facts(facts, 'ShareBasedCompensation', form_type="10-Q", limit=years*4)

        # 期間をキーにマップ作成
        quarterly_map = {}

        # Net Income
        for item in net_income_data:
            end_date = item['end']
            if end_date not in quarterly_map:
                quarterly_map[end_date] = {'filing_date': end_date, 'form': '10-Q'}
            quarterly_map[end_date]['net_income'] = {
                'value': item['val'],
                'unit': item['unit'],
                'filed': item['filed']
            }

        # Diluted Shares
        for item in diluted_shares_data:
            end_date = item['end']
            if end_date not in quarterly_map:
                quarterly_map[end_date] = {'filing_date': end_date, 'form': '10-Q'}
            quarterly_map[end_date]['diluted_shares'] = {
                'value': item['val'],
                'unit': item['unit'],
                'filed': item['filed']
            }

        # フォールバック：Basic Shares（Dilutedがない場合）
        for item in basic_shares_data:
            end_date = item['end']
            if end_date in quarterly_map and 'diluted_shares' not in quarterly_map[end_date]:
                quarterly_map[end_date]['diluted_shares'] = {
                    'value': item['val'],
                    'unit': item['unit'],
                    'filed': item['filed']
                }

        # Pretax Income
        for item in pretax_data:
            end_date = item['end']
            if end_date in quarterly_map:
                quarterly_map[end_date]['pretax_income'] = {
                    'value': item['val'],
                    'unit': item['unit']
                }

        # Tax Expense
        for item in tax_data:
            end_date = item['end']
            if end_date in quarterly_map:
                quarterly_map[end_date]['tax_expense'] = {
                    'value': item['val'],
                    'unit': item['unit']
                }

        # SBC
        for item in sbc_data:
            end_date = item['end']
            if end_date in quarterly_map:
                quarterly_map[end_date]['sbc'] = {
                    'value': item['val'],
                    'unit': item['unit']
                }

        # リストに変換し、必須データが揃っているものだけ抽出
        quarterly_list = []
        for end_date, data in sorted(quarterly_map.items(), reverse=True):
            if 'net_income' in data and 'diluted_shares' in data:
                quarterly_list.append(data)
                print(f"  ✓ {end_date}: net_income={data['net_income']['value']:,.0f}, diluted_shares={data['diluted_shares']['value']:,.0f}")
            else:
                missing = []
                if 'net_income' not in data:
                    missing.append('net_income')
                if 'diluted_shares' not in data:
                    missing.append('diluted_shares')
                print(f"  ✗ {end_date}: missing {', '.join(missing)}")

        print(f"\n{ticker}: {len(quarterly_list)}件の四半期データを取得")
        return quarterly_list

    except Exception as e:
        print(f"{ticker} データ取得エラー: {e}")
        import traceback
        traceback.print_exc()
        return []

def normalize_value(value_dict: Optional[Dict]) -> float:
    """単位正規化（すべてUSD absolute valueに統一）"""
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
    return value

# ============================================
# テスト用メイン関数
# ============================================
def main():
    """テスト実行用"""
    ticker = "PLTR"
    print(f"Testing data extraction for {ticker}...")

    data = extract_quarterly_facts(ticker, years=5)

    if data:
        print(f"\nSuccessfully extracted {len(data)} quarters:")
        for i, quarter in enumerate(data[:5]):
            print(f"\nQuarter {i+1}: {quarter['filing_date']}")
            net = normalize_value(quarter.get('net_income'))
            shares = normalize_value(quarter.get('diluted_shares'))
            print(f"  Net Income: {net:,.0f} USD")
            print(f"  Diluted Shares: {shares:,.0f}")
            if shares > 0:
                eps = net / shares
                print(f"  Implied EPS: {eps:.4f} USD")
    else:
        print("No data extracted")

if __name__ == "__main__":
    main()
