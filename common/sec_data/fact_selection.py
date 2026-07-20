"""
common/sec_data/fact_selection.py
fact競合解決の共通プリミティブ（EPS-ANALYZER-NORMALIZE-SCOPE-1）

同一期間（同一end_date、または同一(start, end)）に複数のXBRL factが競合する
場合（株式分割による比較年度再掲・10-K/A訂正申告等、SEC-TAG-FICO-CPRT-1と
同型のパターン）、「filed日が最新のものを優先する」という単一規則を
common/sec_data/quarterly.py（`_process_entries`・`_select_best_filing`）と
src/value/adjusted_eps_analyzer/extract_key_facts.py（SPLIT-AUTO-CHECK-1）が
それぞれ独立に実装していたのを、この最小プリミティブに切り出した。

parser.py本体（本人データ優先・fy一致・期間近似等を含む多段規則）は対象外。
本関数はあくまで「同一期間の複数候補からfiled日最新の1件を選ぶ」という
末端の判定ロジックのみを担う。
"""
from typing import Any, Sequence


def select_latest_filed(candidates: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """同一期間内の複数候補factから、filed日が最新のものを返す。

    Args:
        candidates: 各要素が"filed"キー（文字列、ISO8601日付相当）を持つdictの列。
                     空でないことを呼び出し元が保証すること。

    Returns:
        "filed"が最大（辞書順で最新）の要素。同着の場合はcandidates内で
        最初に出現した要素を返す（Pythonのmax()は最初の最大値を保持する）。

    Raises:
        ValueError: candidatesが空の場合。
    """
    if not candidates:
        raise ValueError("select_latest_filed: candidates must not be empty")
    return max(candidates, key=lambda c: c.get("filed", ""))
