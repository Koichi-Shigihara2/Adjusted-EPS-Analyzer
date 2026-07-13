"""
common/sec_data/contracts.py
責務: quarterly.py / normalizer.py / data_fetcher.py が共有する正規化契約
（フィールド形状・順序規約・出所メタデータ）を型で表現するバリデーション層。

QUALITY-GATES-EPIC-1 Phase 3a（Gate2第一段階）。

設計方針:
- JSON on-disk形式は変更しない。json.load()直後・json.dump()直前に本モジュールの
  型を経由させ、これまでdocstring/コメントのみで表現されていた暗黙規約を実行時に
  検証する（違反時は ContractViolation を送出する）。
- 検証は「構築して確認するだけ」に留め、検証結果のオブジェクトを呼び出し元の
  戻り値・保存対象データにそのまま流用しない（既存の辞書ベースの出力形式を
  一切変えないため）。ただし _provenance キーのように、既存キーを変更せず
  追加のみを行うケースは対象外（quarterly.py 側で明示的に付与する）。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional


class ContractViolation(ValueError):
    """正規化契約（暗黙規約の型表現）への違反を表す例外。

    ValueError のサブクラスとするため、既存コード側の `except Exception` は
    従来通り本例外も捕捉できる（update.py の per-ticker try/except 等、
    フェイルセーフな既存の失敗ハンドリングを壊さない）。
    """


# ---------------------------------------------------------------------------
# 規約③: 出所・充足度メタデータの統一置き場所
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EntryProvenance:
    """「なぜこの値が採用されたか」を示す任意メタデータの統一置き場所。

    既存のJSON出力キー（is_annual/is_ytd等）とは別に、今回新設する唯一の
    ネストされたメタデータキー。両フィールドともNoneの場合はエントリのJSON
    表現から `_provenance` キー自体を省略する（既存ファイルとの互換性維持・
    無用なサイズ増加の回避のため、通常ケース＝primaryタグがヒットした場合は
    付与しない。フォールバック採用時・ticker_restrictions オーバーライド時
    のみ付与する）。

    source_tag    : 実際に採用されたXBRL概念名
                    （例: "DebtLongtermAndShorttermCombinedAmount"）
    duration_days : end-start日数（365日への近さがtie-break根拠になった場合）。
                    quarterly.py側では現状使用しない（parser.py側の
                    annual_durations相当。parser.pyはPhase 3aのスコープ外の
                    ため今回は配線しない。将来parser.pyを対象にする際の
                    受け皿として型のみ用意する）。
    """
    source_tag: Optional[str] = None
    duration_days: Optional[int] = None

    def is_empty(self) -> bool:
        return self.source_tag is None and self.duration_days is None

    def to_dict(self) -> dict:
        d: dict = {}
        if self.source_tag is not None:
            d["source_tag"] = self.source_tag
        if self.duration_days is not None:
            d["duration_days"] = self.duration_days
        return d

    @classmethod
    def from_dict(cls, d: Optional[dict]) -> "EntryProvenance":
        if not d:
            return cls()
        if not isinstance(d, dict):
            raise ContractViolation(f"_provenance は辞書である必要があります: {d!r}")
        return cls(
            source_tag=d.get("source_tag"),
            duration_days=d.get("duration_days"),
        )


# ---------------------------------------------------------------------------
# 規約B: quarterly.py標準エントリ形状
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = (
    "end", "start", "val", "accn", "fp", "fy", "form", "filed",
    "period_days", "is_ytd", "is_annual",
)


@dataclass
class FinancialEntry:
    """quarterly.py::_process_entries() が生成する標準エントリ形状の型表現。

    必須キー: end/start/val/accn/fp/fy/form/filed/period_days/is_ytd/is_annual
    任意キー: is_implied/anomaly/backfilled/_provenance

    生成元辞書のキー欠落・形状崩れを construction 時に検知する。従来は
    dict.get() による暗黙の None フォールバックで検知不能だった
    （キー名のtypo等が実行時エラーにならず、下流で静かに欠損値扱いされていた）。
    """
    end: str
    start: str
    val: Any
    accn: str
    fp: str
    fy: Any
    form: str
    filed: str
    period_days: Any
    is_ytd: bool
    is_annual: bool
    is_implied: bool = False
    anomaly: bool = False
    backfilled: bool = False
    provenance: EntryProvenance = field(default_factory=EntryProvenance)

    @classmethod
    def from_dict(cls, d: dict) -> "FinancialEntry":
        if not isinstance(d, dict):
            raise ContractViolation(f"エントリは辞書である必要があります: {d!r}")
        missing = [k for k in _REQUIRED_KEYS if k not in d]
        if missing:
            raise ContractViolation(
                f"必須キー欠落 {missing} (end={d.get('end')!r} val={d.get('val')!r})"
            )
        return cls(
            end=d["end"], start=d["start"], val=d["val"], accn=d["accn"],
            fp=d["fp"], fy=d["fy"], form=d["form"], filed=d["filed"],
            period_days=d["period_days"],
            is_ytd=bool(d["is_ytd"]), is_annual=bool(d["is_annual"]),
            is_implied=bool(d.get("is_implied", False)),
            anomaly=bool(d.get("anomaly", False)),
            backfilled=bool(d.get("backfilled", False)),
            provenance=EntryProvenance.from_dict(d.get("_provenance")),
        )

    def to_dict(self) -> dict:
        d: dict = {
            "end": self.end, "start": self.start, "val": self.val,
            "accn": self.accn, "fp": self.fp, "fy": self.fy, "form": self.form,
            "filed": self.filed, "period_days": self.period_days,
            "is_ytd": self.is_ytd, "is_annual": self.is_annual,
        }
        if self.is_implied:
            d["is_implied"] = True
        if self.anomaly:
            d["anomaly"] = True
        if self.backfilled:
            d["backfilled"] = True
        if not self.provenance.is_empty():
            d["_provenance"] = self.provenance.to_dict()
        return d


def validate_entries(field_name: str, entries: list) -> list[FinancialEntry]:
    """1フィールド分のエントリ辞書リストを検証する（構築のみ・戻り値は未使用でも良い）。

    規約違反時は ContractViolation を送出する（field_name をメッセージに含め、
    どのフィールドで違反したかを特定しやすくする）。
    """
    try:
        return [FinancialEntry.from_dict(e) for e in entries]
    except ContractViolation as e:
        raise ContractViolation(f"[{field_name}] {e}") from e


def validate_fields(fields: dict) -> None:
    """raw/normalized JSON の "fields" 辞書全体を検証する（副作用なし・戻り値なし）。

    quarterly.py::save_raw_table() / normalizer.py::save_normalized() の
    json.dump() 直前で呼び出す想定。検証結果のオブジェクトは破棄し、
    呼び出し元が保存しようとしている元の辞書はそのまま使う
    （JSON on-disk形式を一切変えないため）。
    """
    for field_name, entries in fields.items():
        validate_entries(field_name, entries)


# ---------------------------------------------------------------------------
# 規約A: fcf_listの順序規約（新しい順、[0]が直近）
# ---------------------------------------------------------------------------

class FCFSeries(Sequence):
    """fcf_listを裸のlist[float]として扱わず、順序規約を型レベルで保証するラッパー。

    GROWTH-CAGR-SIGN-1（calculate_fcf_cagr()内でstart_value/end_valueの割り当てを
    取り違えた符号反転バグ）の再発防止を狙う。fcf_list[0]/fcf_list[-1]という
    裸のインデックスアクセスは「どちらが直近でどちらが最古か」を毎回コメントで
    確認する必要があり、取り違えの温床だった。`.newest`/`.oldest`/`.newest_n()`
    という named accessor を用意し、正しい使い方を選びやすくする。

    既存コード（adjustments.py・growth.py等）とのAPI互換性のため、list風の
    __getitem__/__len__/__iter__ を実装し、fcf_list[:5] のようなスライスも
    従来通り動作する（collections.abc.Sequence 経由）。

    dates（end日文字列のリスト）が渡された場合のみ、新しい順（降順）である
    ことを construction 時に検証する。datesを渡さない場合は検証をスキップし、
    値のみのSequenceとして振る舞う（reader.py::get_fcf_list() のように、
    呼び出し時点で既に日付情報が失われている経路向け。QUALITY-GATES-EPIC-1
    Phase 3aのスコープはnormalizer.py/quarterly.py/data_fetcher.py内の
    fcf_list生成箇所に限定されており、reader.py自体の改修はスコープ外・
    別課題として報告する）。

    重要: 本クラスのインスタンスはJSONシリアライズ不可能。json.dump()の
    対象になりうる辞書（例: core_calculator.pyのcomponents["fcf_list_raw"]）に
    そのまま格納してはならない。data_fetcher.py側では検証のみに使用し、
    呼び出し元へは `.as_list()` で素の list[float] に変換してから返すこと。
    """

    __slots__ = ("_values", "_dates")

    def __init__(self, values: list, dates: Optional[list] = None):
        values = list(values)
        if dates is not None:
            dates = list(dates)
            if len(dates) != len(values):
                raise ContractViolation(
                    f"FCFSeries: values({len(values)}件)とdates({len(dates)}件)の件数不一致"
                )
            for i in range(len(dates) - 1):
                if dates[i] < dates[i + 1]:
                    raise ContractViolation(
                        "FCFSeries: 新しい順（降順）規約違反 "
                        f"index={i} date={dates[i]!r} < index={i + 1} date={dates[i + 1]!r}"
                    )
        self._values = values
        self._dates = dates

    def __getitem__(self, idx):
        return self._values[idx]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator:
        return iter(self._values)

    def __repr__(self) -> str:
        return f"FCFSeries({self._values!r})"

    def __eq__(self, other) -> bool:
        if isinstance(other, FCFSeries):
            return self._values == other._values
        if isinstance(other, list):
            return self._values == other
        return NotImplemented

    @property
    def newest(self):
        """最も直近の値（fcf_list[0]相当）。空の場合はNone。"""
        return self._values[0] if self._values else None

    @property
    def oldest(self):
        """最も古い値（fcf_list[-1]相当）。空の場合はNone。"""
        return self._values[-1] if self._values else None

    def newest_n(self, n: int) -> "FCFSeries":
        """直近n件を新しい順で返す（fcf_list[:n]相当。[-n:]との取り違え防止）。"""
        dates = self._dates[:n] if self._dates is not None else None
        return FCFSeries(self._values[:n], dates)

    def as_list(self) -> list:
        """素の list[float] に変換する（JSONシリアライズ・既存API互換用）。"""
        return list(self._values)
