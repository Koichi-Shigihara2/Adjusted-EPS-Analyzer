from edgar import Filing  # Filingオブジェクトを直接使う
import pandas as pd

def parse_xbrl(filing: Filing):
    """
    EDGAR FilingからXBRLデータを抽出。
    最新edgartoolsでは filing.xbrl() でXBRLインスタンスを取得。
    """
    try:
        # XBRLインスタンスを取得（10-Q/10-Kで利用可能）
        xbrl = filing.xbrl()
        if not xbrl:
            print(f"No XBRL data in filing {filing.accession_no}")
            return None

        # 主要事実を取得（get_factで安全に）
        def safe_get(tag, fallback=None):
            try:
                fact = xbrl.get_fact(tag)
                return fact.value if fact else fallback
            except:
                return fallback

        # 1. 希薄化後加重平均株式数（Diluted Weighted Average Shares）
        diluted_shares = safe_get("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding") or \
                         safe_get("dei:EntityCommonStockSharesOutstanding")

        # 2. 当期純利益（親会社帰属）
        net_income = safe_get("us-gaap:NetIncomeLoss") or \
                     safe_get("us-gaap:ProfitLoss") or \
                     safe_get("us-gaap:NetIncomeLossAttributableToParent")

        # 3. 法人税費用
        tax_expense = safe_get("us-gaap:IncomeTaxExpenseBenefit")

        # 4. 税引前利益
        pretax_income = safe_get("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest") or \
                        safe_get("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes")

        # 全factsを辞書化（調整検知用）
        raw_data = {fact.concept.name: fact.value for fact in xbrl.facts}

        return {
            "net_income": net_income,
            "diluted_shares": diluted_shares,
            "tax_expense": tax_expense,
            "pretax_income": pretax_income,
            "raw_facts": raw_data,
            # 追加: スニペット保存用（要件対応）
            "snippets": {fact.concept.name: fact.context_id for fact in xbrl.facts}  # 後で拡張
        }

    except AttributeError as ae:
        print(f"AttributeError parsing XBRL for {filing.accession_no}: {ae}")
        return None
    except Exception as e:
        print(f"Error parsing XBRL for {filing.accession_no}: {e}")
        return None
