from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from time import perf_counter
from typing import Dict, List

from pcfi_core import explain, sanitize
from pcfi_core.checks import (
    HierarchicalResult,
    LexicalResult,
    RoleSwitchResult,
    run_hierarchical_checks,
    run_lexical_checks,
    run_role_switch_checks,
)
from pcfi_core.ir import PromptIR
from pcfi_core.policy.loaders import load_policy


class DecisionOutcome(str):
    ALLOW = "allow"
    BLOCK = "block"
    SANITIZE = "sanitize"


@dataclass
class Decision:
    outcome: str
    reasons: List[str] = field(default_factory=list)
    stage_timings_ms: Dict[str, float] = field(default_factory=dict)
    lexical: LexicalResult | None = None
    role_switch: RoleSwitchResult | None = None
    hierarchical: HierarchicalResult | None = None
    sanitized_ir: PromptIR | None = None
    explanation: Dict[str, object] | None = None


class PCFIEngine:
    """
    Orchestrates the PCFI check pipeline.

    At this stage, only lexical checks are implemented; later phases will add
    role-switch and hierarchical checks and may update the decision outcome.
    """

    def __init__(self, policy_path: str | None = None) -> None:
        self._policy_path = policy_path or "policies/default_policy.yaml"

    @property
    @lru_cache(maxsize=1)
    def policy(self):
        return load_policy(self._policy_path)

    def run(self, prompt_ir: PromptIR) -> Decision:
        timings: dict[str, float] = {}

        t0 = perf_counter()
        lexical_result = run_lexical_checks(prompt_ir)
        timings["lexical_ms"] = (perf_counter() - t0) * 1000.0

        t1 = perf_counter()
        role_switch_result = run_role_switch_checks(prompt_ir)
        timings["role_switch_ms"] = (perf_counter() - t1) * 1000.0

        t2 = perf_counter()
        hierarchical_result = run_hierarchical_checks(prompt_ir, self.policy)
        timings["hierarchical_ms"] = (perf_counter() - t2) * 1000.0

        reasons: list[str] = []
        if lexical_result.findings:
            reasons.append(f"lexical:{lexical_result.severity}")
        if role_switch_result.findings:
            reasons.append(f"role_switch:{role_switch_result.severity}")

        outcome = DecisionOutcome.ALLOW
        sanitized_ir: PromptIR | None = None

        # As an intermediate measure, mark the request as requiring sanitization
        # when role-switch findings are strong, and compute a sanitized IR.
        if role_switch_result.severity in {"medium", "high"}:
            outcome = DecisionOutcome.SANITIZE
            sanitized_ir = sanitize.sanitize_role_like_prefixes(prompt_ir)

        # Hierarchical violations are treated as hard blocks.
        if hierarchical_result.has_violations:
            outcome = DecisionOutcome.BLOCK

        decision = Decision(
            outcome=outcome,
            reasons=reasons,
            stage_timings_ms=timings,
            lexical=lexical_result,
            role_switch=role_switch_result,
            hierarchical=hierarchical_result,
            sanitized_ir=sanitized_ir,
        )

        decision.explanation = explain.build_explanation(decision)
        return decision

