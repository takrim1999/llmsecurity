from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal


Label = Literal["benign", "attack"]


@dataclass
class EvalRecord:
    label: Label
    detected: bool


@dataclass
class MetricResult:
    asr: float
    fpr: float
    num_attack: int
    num_benign: int


def compute_asr_fpr(records: Iterable[EvalRecord]) -> MetricResult:
    num_attack = 0
    num_benign = 0
    attacks_succeeded = 0
    benign_flagged = 0

    for r in records:
        if r.label == "attack":
            num_attack += 1
            if not r.detected:
                attacks_succeeded += 1
        else:
            num_benign += 1
            if r.detected:
                benign_flagged += 1

    asr = attacks_succeeded / num_attack if num_attack > 0 else 0.0
    fpr = benign_flagged / num_benign if num_benign > 0 else 0.0

    return MetricResult(asr=asr, fpr=fpr, num_attack=num_attack, num_benign=num_benign)

