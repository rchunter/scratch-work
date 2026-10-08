"""Data-only public contracts for the reviewed test-author phase."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class Match:
    field: str
    operator: Literal['exact', 'contains', 'contains_all']
    values: tuple[str, ...]


@dataclass(frozen=True)
class And:
    left: Expression
    right: Expression


@dataclass(frozen=True)
class Or:
    left: Expression
    right: Expression


@dataclass(frozen=True)
class Not:
    operand: Expression


Expression = Match | And | Or | Not


@dataclass(frozen=True)
class Translation:
    metadata: dict
    detection: Expression | None
    detection_complete: bool
    diagnostics: list[Diagnostic]


@dataclass(frozen=True)
class ConversionResult:
    document: dict
    diagnostics: list[Diagnostic]
    detection_complete: bool


class VendorAdapter(Protocol):
    def translate(self, source: dict) -> Translation: ...
