from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pcfi_core.ir import Priority, PromptIR
from pcfi_core.policy.model import ForbiddenDirective, Policy


@dataclass
class HierarchicalViolation:
    directive_id: str
    segment_index: int
    snippet: str


@dataclass
class HierarchicalResult:
    violations: List[HierarchicalViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)


def _segment_is_low_priority(priority: Priority) -> bool:
    return priority in (Priority.USER, Priority.RAG)


def run_hierarchical_checks(prompt_ir: PromptIR, policy: Policy) -> HierarchicalResult:
    """
    Enforce the priority ordering specified by the policy.

    We approximate the hierarchy by requiring that any directive pattern that
    attempts to reinterpret the system policy must not appear in lower-priority
    segments (USER, RAG) when higher-priority segments exist.
    """
    has_higher_priority_segments = any(
        seg.priority in (Priority.SYSTEM, Priority.DEVELOPER) for seg in prompt_ir.segments
    )

    violations: List[HierarchicalViolation] = []
    if not has_higher_priority_segments:
        return HierarchicalResult(violations=violations)

    for idx, segment in enumerate(prompt_ir.segments):
        if not _segment_is_low_priority(segment.priority):
            continue

        text_lower = segment.text.lower()
        for directive in policy.forbidden_directives:
            for pattern in directive.patterns:
                if pattern.lower() in text_lower:
                    violations.append(
                        HierarchicalViolation(
                            directive_id=directive.id,
                            segment_index=idx,
                            snippet=segment.text[:160],
                        )
                    )

    return HierarchicalResult(violations=violations)

