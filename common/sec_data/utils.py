"""
共通ユーティリティ関数
"""
from datetime import date, datetime


def determine_fiscal_year(end_date, fiscal_end_month: int) -> int:
    """
    期末日と会計年度末月から、その期間が属する会計年度を返す。

    Args:
        end_date: datetime.date または datetime.datetime
        fiscal_end_month: 会計年度末の月（1-12）

    Returns:
        int: 会計年度（西暦4桁）

    Examples:
        AAPL (fiscal_end_month=9):  end_date=2024-12-28 → 2025
        MSFT (fiscal_end_month=6):  end_date=2024-09-30 → 2025
        NVDA (fiscal_end_month=1):  end_date=2025-04-27 → 2026
        Dec  (fiscal_end_month=12): end_date=2025-03-31 → 2025
    """
    if end_date.month > fiscal_end_month:
        return end_date.year + 1
    else:
        return end_date.year
