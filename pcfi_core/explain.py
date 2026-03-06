from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    # Imported only for type checking; avoids a runtime circular import.
    from pcfi_core.engine import Decision


def build_explanation(decision: "Decision") -> Dict[str, Any]:
    """
    Construct a structured explanation object that can be logged or returned
    from the gateway for debugging and analysis.
    """
    explanation: Dict[str, Any] = {
        "outcome": decision.outcome,
        "reasons": decision.reasons,
        "stage_timings_ms": decision.stage_timings_ms,
    }

    if decision.lexical is not None:
        explanation["lexical"] = {
            "score": decision.lexical.score,
            "severity": decision.lexical.severity,
            "rules": [f.rule_id for f in decision.lexical.findings],
        }

    if decision.role_switch is not None:
        explanation["role_switch"] = {
            "num_findings": len(decision.role_switch.findings),
            "severity": decision.role_switch.severity,
        }

    if hasattr(decision, "hierarchical") and decision.hierarchical is not None:
        explanation["hierarchical"] = {
            "num_violations": len(decision.hierarchical.violations),
            "directive_ids": [v.directive_id for v in decision.hierarchical.violations],
        }

    return explanation

