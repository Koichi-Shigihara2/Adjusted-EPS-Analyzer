"""
adjustment_detector.py - XBRL データから調整項目を検出
adjustment_items.json の設定に従い、XBRLタグ→キーワードの順で照合。
"""
import json
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_SCRIPT_DIR, "..", "config", "adjustment_items.json")

# モジュール読み込み時に設定をキャッシュ
_config_cache = None


def _get_config(override_config=None):
    global _config_cache
    if override_config:
        return override_config
    if _config_cache is None:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _config_cache = json.load(f)
    return _config_cache


def _normalize_tag(tag: str) -> str:
    """us-gaap:RestructuringCharges → RestructuringCharges"""
    return tag.split(":")[-1] if ":" in tag else tag


def detect_adjustments(raw_facts: dict, config=None) -> list[dict]:
    """
    raw_facts: {full_tag: value, full_tag_snippet: "..."} の辞書
               例: {"us-gaap:RestructuringCharges": 50000000,
                    "us-gaap:RestructuringCharges_snippet": "XBRL tag: ..."}
    config: adjustment_items.json (省略時はファイルから読み込み)

    Returns: 調整項目リスト
    """
    cfg = _get_config(config)
    adjustments = []

    # raw_facts の検索用: full_tag → value、short_name → value の両方
    facts_full  = {k: v for k, v in raw_facts.items() if not k.endswith("_snippet")}
    facts_short = {_normalize_tag(k): v for k, v in facts_full.items()}

    for cat in cfg.get("categories", []):
        category_name = cat.get("category_name", "")
        for item in cat.get("sub_items", []):
            amount = 0
            source_tag = None
            snippet = None
            ai_confidence = "low"

            # ─ ① XBRL タグ優先検索（full tag / short tag 両対応）─
            for tag in item.get("xbrl_tags", []):
                # full tag で検索
                if tag in facts_full and facts_full[tag]:
                    amount     = abs(float(facts_full[tag]))  # 符号は direction で管理
                    source_tag = tag
                    snippet    = raw_facts.get(f"{tag}_snippet", f"XBRL: {tag} = {amount:,.0f}")
                    ai_confidence = "high"
                    break
                # short tag で検索
                short = _normalize_tag(tag)
                if short in facts_short and facts_short[short]:
                    amount     = abs(float(facts_short[short]))
                    source_tag = tag
                    snippet    = raw_facts.get(f"{tag}_snippet",
                                               f"XBRL: {short} = {amount:,.0f}")
                    ai_confidence = "high"
                    break

            # ─ ② キーワード検索（テキスト形式 snippet の中を探索）─
            if not amount:
                raw_str = " ".join(
                    str(v) for k, v in raw_facts.items() if k.endswith("_snippet")
                ).lower()
                for kw in item.get("keywords", []):
                    if kw.lower() in raw_str:
                        # 値は取れないので 0 のまま — amount は不明
                        snippet       = f"keyword match: '{kw}'"
                        ai_confidence = "low"
                        # キーワードのみヒットでは金額が不明なので追加しない
                        # （将来: テキスト抽出 NLP でフォールバック）
                        break

            # ─ ③ 検出された場合のみ追加 ─
            if amount > 0:
                adjustments.append({
                    "category":       category_name,
                    "item_name":      item.get("item_name", ""),
                    "amount":         amount,
                    "direction":      item.get("direction", "add_back"),
                    "pre_tax":        item.get("pre_tax", True),
                    "reason":         item.get("reason", ""),
                    "extracted_from": source_tag or "keyword",
                    "context_snippet": snippet,
                    "ai_confidence":  ai_confidence,
                    "special":        item.get("special"),
                })

    return adjustments
