from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pcfi_core.engine import PCFIEngine, DecisionOutcome
from pcfi_core.ir import Priority, PromptIR, Provenance, Segment

from .metrics import EvalRecord, MetricResult, compute_asr_fpr


def _percentile(sorted_values: list[float], p: float) -> float:
    """Return p-th percentile (0--100)."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_values) else f
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


@dataclass
class SampleWithDecision:
    example_id: str
    label: str
    attack_family: str | None
    outcome: str
    lexical_severity: str
    role_switch_severity: str
    has_hierarchical_violation: bool


def _prompt_ir_from_record(record: Dict[str, Any]) -> PromptIR:
    segments: List[Segment] = []
    idx = 0

    system_text = record.get("system_policy", "")
    if system_text:
        segments.append(
            Segment(
                text=system_text,
                role="system",
                priority=Priority.SYSTEM,
                provenance=Provenance(source="dataset", index=idx),
            )
        )
        idx += 1

    dev_text = record.get("developer_prompt")
    if dev_text:
        segments.append(
            Segment(
                text=dev_text,
                role="developer",
                priority=Priority.DEVELOPER,
                provenance=Provenance(source="dataset", index=idx),
            )
        )
        idx += 1

    user_text = record.get("user_prompt", "")
    segments.append(
        Segment(
            text=user_text,
            role="user",
            priority=Priority.USER,
            provenance=Provenance(source="dataset", index=idx),
        )
    )
    idx += 1

    for rag_idx, rag in enumerate(record.get("rag_docs", [])):
        segments.append(
            Segment(
                text=str(rag.get("content", "")),
                role="rag",
                priority=Priority.RAG,
                provenance=Provenance(
                    source="rag",
                    index=idx + rag_idx,
                    doc_id=str(rag.get("id", "")),
                    metadata={"source": rag.get("source"), "score": rag.get("score")},
                ),
            )
        )

    return PromptIR(segments=segments)


def _decision_to_records(example_label: str, decision_outcome: str, detected: bool) -> EvalRecord:
    label: str
    if example_label == "attack":
        label = "attack"
    else:
        label = "benign"
    return EvalRecord(label=label, detected=detected)


def run_evaluation(datasets_dir: Path, output_path: Path) -> None:
    # Resolve policy path relative to repo root so it works when run as module.
    _repo_root = Path(__file__).resolve().parent.parent
    _policy_path = _repo_root / "policies" / "default_policy.yaml"
    engine = PCFIEngine(policy_path=str(_policy_path))

    dataset_files = [
        datasets_dir / "pcfi_benign.jsonl",
        datasets_dir / "pcfi_direct_injection.jsonl",
        datasets_dir / "pcfi_indirect_rag_injection.jsonl",
    ]

    full_records: list[EvalRecord] = []
    samples: list[SampleWithDecision] = []
    latency_ms_list: list[float] = []

    for ds_path in dataset_files:
        if not ds_path.exists():
            continue
        with ds_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                prompt_ir = _prompt_ir_from_record(record)
                decision = engine.run(prompt_ir)

                label = record.get("label", "benign")
                attack_family = record.get("attack_family")

                # Detection regimes:
                baseline_detect = False
                lexical_detect = decision.lexical is not None and bool(decision.lexical.findings)
                role_detect = decision.role_switch is not None and bool(
                    decision.role_switch.findings
                )
                hierarchical_detect = (
                    decision.hierarchical is not None
                    and decision.hierarchical.has_violations  # type: ignore[union-attr]
                )
                full_pcfi_detect = decision.outcome in (
                    DecisionOutcome.BLOCK,
                    DecisionOutcome.SANITIZE,
                )

                # Collect per-variant metrics.
                full_records.append(
                    _decision_to_records(label, decision.outcome, full_pcfi_detect)
                )

                samples.append(
                    SampleWithDecision(
                        example_id=str(record.get("id")),
                        label=label,
                        attack_family=attack_family,
                        outcome=decision.outcome,
                        lexical_severity=decision.lexical.severity
                        if decision.lexical is not None
                        else "none",
                        role_switch_severity=decision.role_switch.severity
                        if decision.role_switch is not None
                        else "none",
                        has_hierarchical_violation=hierarchical_detect,
                    )
                )
                total_ms = sum(decision.stage_timings_ms.values()) if decision.stage_timings_ms else 0.0
                latency_ms_list.append(total_ms)

    metrics = compute_asr_fpr(full_records)
    latency_ms_list.sort()
    latency_median = _percentile(latency_ms_list, 50) if latency_ms_list else 0.0
    latency_p95 = _percentile(latency_ms_list, 95) if latency_ms_list else 0.0
    latency_p99 = _percentile(latency_ms_list, 99) if latency_ms_list else 0.0

    output: dict[str, Any] = {
        "overall": asdict(metrics),
        "latency_ms": {
            "median": round(latency_median, 2),
            "p95": round(latency_p95, 2),
            "p99": round(latency_p99, 2),
            "num_samples": len(latency_ms_list),
        },
        "samples": [asdict(s) for s in samples],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PCFI evaluation on datasets.")
    parser.add_argument(
        "--datasets-dir",
        type=Path,
        default=Path("datasets"),
        help="Directory containing pcfi_*.jsonl files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eval/results/pcfi_eval_full.json"),
        help="Where to write aggregated metrics JSON.",
    )
    args = parser.parse_args()

    run_evaluation(args.datasets_dir, args.output)


if __name__ == "__main__":
    main()

