"""
xbrl_parser.py - XBRL データ取得ヘルパー
個別 filing の XBRL インスタンスからファクトを抽出するユーティリティ。
pipeline では extract_key_facts が CompanyFacts を使う方式を採用しているが、
個別 filing の詳細 XBRL 取得が必要な場合はこのモジュールを使用する。
"""
from typing import Optional


def parse_xbrl(filing) -> dict:
    """
    edgartools の Filing オブジェクトから XBRL データを取得し、
    {tag: value, tag_snippet: "..."} の辞書として返す。

    Parameters
    ----------
    filing : edgartools の Filing オブジェクト

    Returns
    -------
    raw_facts dict ({full_tag: value})
    """
    raw_facts = {}

    # ─ XBRL インスタンス取得 ─
    try:
        xbrl = filing.xbrl()
    except Exception as e:
        print(f"    [WARN] xbrl() 取得失敗: {e}")
        return raw_facts

    if xbrl is None:
        return raw_facts

    # ─ facts 列挙 ─
    try:
        # edgartools 4.x の XBRL オブジェクトは .facts または .labels でアクセス
        if hasattr(xbrl, "facts"):
            for fact in xbrl.facts:
                try:
                    tag   = str(getattr(fact, "concept", "") or
                                getattr(fact, "tag",     "") or "")
                    value = getattr(fact, "value", None)
                    if not tag or value is None:
                        continue
                    try:
                        num_val = float(str(value).replace(",", ""))
                    except Exception:
                        continue
                    # 既存値より新しい（または未登録）場合に上書き
                    if tag not in raw_facts or num_val != 0:
                        raw_facts[tag] = num_val
                        raw_facts[f"{tag}_snippet"] = (
                            f"XBRL: {tag} = {num_val:,.0f} "
                            f"(period: {getattr(fact, 'period', 'N/A')})"
                        )
                except Exception:
                    continue
    except Exception as e:
        print(f"    [WARN] facts 列挙失敗: {e}")

    return raw_facts


def get_income_statement_facts(filing) -> Optional[dict]:
    """
    TenQ / TenK オブジェクト経由で損益計算書の主要数値を取得する高レベルAPI。
    edgartools の型付きオブジェクトを使用。
    """
    try:
        obj = filing.obj()  # TenQ or TenK
        if obj is None:
            return None

        result = {}

        # 損益計算書
        if hasattr(obj, "income_statement") and obj.income_statement:
            is_df = obj.income_statement
            # DataFrame 形式か dict 形式かに対応
            if hasattr(is_df, "to_dict"):
                result["income_statement"] = is_df.to_dict()
            elif hasattr(is_df, "__dict__"):
                result["income_statement"] = vars(is_df)

        return result
    except Exception as e:
        print(f"    [WARN] get_income_statement_facts 失敗: {e}")
        return None
