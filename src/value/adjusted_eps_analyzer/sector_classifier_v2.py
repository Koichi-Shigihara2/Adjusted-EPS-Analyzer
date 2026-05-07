"""
セクター分類モジュール（VER2）
- SICコードとキーワードによる業種判定
- セクター別デフォルト除外項目の取得
"""
import csv
import yaml
import os
import re
from typing import Optional, List, Dict

class SectorClassifierV2:
    """VER2基準に基づく業種分類（SICコード対応）"""

    def __init__(self, config_path: str, cik_lookup_path: str = None):
        """
        Args:
            config_path: sectors.yaml のパス
            cik_lookup_path: cik_lookup.csv のパス（eps_sector 手動設定の読み込みに使用）
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.sectors = yaml.safe_load(f)['sectors']

        # キーワード検索用に正規表現パターンを事前コンパイル
        # ★修正: \b（単語境界）でマッチさせ、'O' が 'Technologies' 内の 'o' に
        #         誤マッチするバグを修正。ティッカーシンボルは必ず単語として完全一致させる。
        self.patterns = {}
        for sector in self.sectors:
            # 各キーワードを \b で囲んで単語境界マッチにする
            parts = [r'\b' + re.escape(kw) + r'\b' for kw in sector['keywords']]
            self.patterns[sector['name']] = re.compile('|'.join(parts), re.IGNORECASE)

        self._eps_sector_map: Dict[str, str] = {}
        if cik_lookup_path:
            self._load_eps_sector_map(cik_lookup_path)

    def _load_eps_sector_map(self, cik_lookup_path: str) -> None:
        """cik_lookup.csv の eps_sector 列を読み込み、ティッカー→セクターのマップを構築する"""
        try:
            with open(cik_lookup_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ticker = row.get('ticker', '').strip().upper()
                    eps_sector = row.get('eps_sector', '').strip()
                    if ticker and eps_sector:
                        self._eps_sector_map[ticker] = eps_sector
        except Exception as e:
            print(f"Warning: eps_sector の読み込み失敗 ({cik_lookup_path}): {e}")

    def classify_by_sic(self, sic_code: str) -> Optional[str]:
        """SICコードで業種判定（最も正確）"""
        if not sic_code:
            return None

        for sector in self.sectors:
            if 'sic_codes' in sector and sic_code in sector['sic_codes']:
                return sector['name']
        return None

    def classify_by_keywords(self, text: str) -> Optional[str]:
        """キーワードで業種判定（フォールバック）"""
        if not text:
            return None

        for sector_name, pattern in self.patterns.items():
            if pattern.search(text):
                return sector_name
        return None

    def get_exclusions_for_sector(self, sector: str) -> List[Dict]:
        """セクターのデフォルト除外項目を取得"""
        for s in self.sectors:
            if s['name'] == sector:
                return s.get('exclusions', [])
        return []

    def get_maturity_watch_items(self, sector: str) -> List[str]:
        """成熟度監視対象の項目IDを取得（SBCなど）"""
        watch_items = []
        for s in self.sectors:
            if s['name'] == sector:
                for ex in s.get('exclusions', []):
                    if ex.get('maturity_watch', False):
                        watch_items.append(ex['item_id'])
        return watch_items

    def classify(self, ticker: str, sic_code: str = None, company_name: str = None) -> Optional[str]:
        """優先順位: eps_sector(手動設定) > SICコード > キーワード(会社名) > キーワード(ティッカー)"""
        if ticker and ticker.upper() in self._eps_sector_map:
            return self._eps_sector_map[ticker.upper()]
        if sic_code:
            result = self.classify_by_sic(sic_code)
            if result:
                return result
        if company_name:
            result = self.classify_by_keywords(company_name)
            if result:
                return result
        if ticker:
            result = self.classify_by_keywords(ticker)
            if result:
                return result
        return None

    def get_all_sectors(self) -> List[str]:
        """全セクター名のリストを取得（UI用）"""
        return [s['name'] for s in self.sectors]
