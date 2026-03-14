from edgar import Filing
from typing import Dict, Any, Optional

def parse_xbrl(filing: Filing) -> Optional[Dict[str, Any]]:
    """
    SECのFilingからXBRLデータを安全に抽出（最新edgartools対応）
    """
    try:
        # XBRLインスタンスを取得
        xbrl = filing.xbrl()
        if not xbrl:
            print(f"XBRLデータなし: {filing.accession_no} (修正申告や欠損の可能性)")
            return None

        # 単一の事実値を取得する安全関数
        def get_value(tag: str, default=None):
            try:
                fact = xbrl.get_fact(tag)
                return fact.value if fact else default
            except AttributeError:
                print(f"get_factメソッドが見つかりません: {tag}")
                return default
            except Exception as e:
                print(f"get_factエラー {tag}: {e}")
                return default

        # 重要な項目を取得
        diluted_shares = get_value("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding") or \
                         get_value("dei:EntityCommonStockSharesOutstanding")

        net_income = get_value("us-gaap:NetIncomeLoss") or \
                     get_value("us-gaap:NetIncomeLossAttributableToParent")

        tax_expense = get_value("us-gaap:IncomeTaxExpenseBenefit")

        pretax_income = get_value("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes")

        # 全事実を辞書化（調整検知用）※イテレーションエラー回避
        raw_facts = {}
        try:
            # query()を使って安全にイテレート
            facts_query = xbrl.facts.query()
            for fact in facts_query:
                concept = fact.concept.name
                raw_facts[concept] = fact.value
        except Exception as qe:
            print(f"facts.query()失敗: {qe} → フォールバック")
            # フォールバック：主要タグだけ手動取得
            for tag in ["us-gaap:Revenues", "us-gaap:CostOfRevenue", "us-gaap:RestructuringCharges"]:
                val = get_value(tag)
                if val:
                    raw_facts[tag] = val

        return {
            "net_income": net_income,
            "diluted_shares": diluted_shares,
            "tax_expense": tax_expense,
            "pretax_income": pretax_income,
            "raw_facts": raw_facts,
            "period": str(filing.period_end_date),
            "form": filing.form
        }

    except Exception as e:
        print(f"XBRL解析エラー {filing.accession_no}: {e}")
        return None
