from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Mapping, MutableMapping, Optional


SegmentRole = Literal["system", "developer", "user", "assistant", "rag"]


class Priority(str, Enum):
    SYSTEM = "SYSTEM"
    DEVELOPER = "DEVELOPER"
    USER = "USER"
    RAG = "RAG"


@dataclass(frozen=True)
class Provenance:
    """
    Describes where a segment originated from.
    """

    source: str
    index: int
    doc_id: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class Segment:
    """
    A contiguous span of text with a role, priority, and provenance.
    """

    text: str
    role: SegmentRole
    priority: Priority
    provenance: Provenance
    metadata: MutableMapping[str, Any] = field(default_factory=dict)


@dataclass
class PromptIR:
    """
    The full prompt seen by the gateway as a flat sequence of segments.
    """

    segments: list[Segment]

    def by_priority(self, priority: Priority) -> list[Segment]:
        return [s for s in self.segments if s.priority is priority]

