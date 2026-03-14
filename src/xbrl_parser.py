from edgar import Filing
from typing import Dict, Any, Optional

def parse_xbrl(filing: Filing) -> Optional[Dict[str, Any]]:
    """
    Parse XBRL from SEC Filing using latest edgartools API.
    Returns key financials + raw facts dict.
    """
    try:
        xbrl = filing.xbrl()
        if not xbrl:
            print(f"No XBRL instance in filing {filing.accession_no} (amended or missing)")
            return None

        # Safe getter for single fact value
        def get_fact_value(concept: str, default=None):
            fact = xbrl.get_fact(concept)
            return fact.value if fact else default

        # Core metrics (use standard us-gaap tags)
        diluted_shares = get_fact_value("us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding") or \
                         get_fact_value("dei:EntityCommonStockSharesOutstanding")

        net_income = get_fact_value("us-gaap:NetIncomeLoss") or \
                     get_fact_value("us-gaap:ProfitLoss") or \
                     get_fact_value("us-gaap:NetIncomeLossAttributableToParent")

        tax_expense = get_fact_value("us-gaap:IncomeTaxExpenseBenefit")

        pretax_income = get_fact_value("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest") or \
                        get_fact_value("us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxes")

        # All facts as dict (for adjustment_detector to search)
        # Use query() to make iterable safely
        raw_facts = {}
        try:
            for fact in xbrl.facts.query():  # query() returns iterable Fact results
                concept_name = fact.concept.name
                raw_facts[concept_name] = fact.value
        except Exception as qe:
            print(f"Query iteration failed for {filing.accession_no}: {qe}")
            # Fallback: if query() fails, use get_fact for known tags only
            pass

        return {
            "net_income": net_income,
            "diluted_shares": diluted_shares,
            "tax_expense": tax_expense,
            "pretax_income": pretax_income,
            "raw_facts": raw_facts,
            "period_end": str(filing.period_end_date),
            "form": filing.form
        }

    except AttributeError as ae:
        print(f"API mismatch (likely old edgartools): {ae} for {filing.accession_no}")
        return None
    except Exception as e:
        print(f"General XBRL parse error for {filing.accession_no}: {e}")
        return None
