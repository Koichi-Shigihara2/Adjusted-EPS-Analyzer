"""
共通ユーティリティ関数
"""
from datetime import date, datetime, timedelta
from typing import Any, Sequence, Tuple


def quarters_in_trailing_window(
    quarters: Sequence[Tuple[str, Any]],
    fy_end: str,
    window_days: int = 370,
) -> list:
    """
    会計年度end日を起点に、trailing window_days日以内の四半期エントリの値を抽出する。

    暦年ラベル（end[:4]）での四半期グルーピングは非12月決算企業（KLAC/LRCX等）で
    誤判定を起こす（CHECK-QREV-FYE-1・DILUTION-FYE-1で同型バグとして独立に
    発見・修正されていた。ARCH-DATA-1残課題①として本関数へ一本化）。

    Args:
        quarters: (end日文字列, 値) のタプルのリスト（四半期エントリのみ・is_annual除外済み前提）
        fy_end: 年次end日文字列（ISO形式 "YYYY-MM-DD"）
        window_days: 窓の日数（デフォルト370日）

    Returns:
        list: window_start(=fy_end - window_days) < end <= fy_end を満たすエントリの値
              （入力の並び順を保持。ちょうど4件揃っているかの判定・合計/中央値等の
              集計方法は呼び出し元の責務とする——用途によって要件が異なるため）
    """
    fy_end_dt = date.fromisoformat(fy_end)
    window_start = fy_end_dt - timedelta(days=window_days)
    return [
        v for e, v in quarters
        if window_start < date.fromisoformat(e) <= fy_end_dt
    ]


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
