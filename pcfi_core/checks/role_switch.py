from __future__ import annotations

import re
from dataclasses import dataclass, field

from pcfi_core.ir import Priority, PromptIR, Segment


@dataclass
class RoleSwitchFinding:
    segment_index: int
    snippet: str
    kind: str
    confidence: float


@dataclass
class RoleSwitchResult:
    findings: list[RoleSwitchFinding] = field(default_factory=list)

    @property
    def severity(self) -> str:
        if not self.findings:
            return "none"
        max_conf = max(f.confidence for f in self.findings)
        if max_conf >= 0.8:
            return "high"
        if max_conf >= 0.5:
            return "medium"
        return "low"


ROLE_HEADER_RE = re.compile(r"^\s*(system|assistant|developer)\s*[:\-]", re.IGNORECASE)
JSON_ROLE_RE = re.compile(r'\"role\"\s*:\s*\"(system|assistant|developer)\"', re.IGNORECASE)
XML_ROLE_RE = re.compile(r"<\s*(system|assistant|developer)\s*>", re.IGNORECASE)


def _check_segment_for_role_switch(segment: Segment, index: int) -> list[RoleSwitchFinding]:
    text = segment.text
    findings: list[RoleSwitchFinding] = []

    if ROLE_HEADER_RE.search(text):
        findings.append(
            RoleSwitchFinding(
                segment_index=index,
                snippet=text[:120],
                kind="header_prefix",
                confidence=0.8,
            )
        )

    if JSON_ROLE_RE.search(text):
        findings.append(
            RoleSwitchFinding(
                segment_index=index,
                snippet=text[:160],
                kind="json_role_field",
                confidence=0.7,
            )
        )

    if XML_ROLE_RE.search(text):
        findings.append(
            RoleSwitchFinding(
                segment_index=index,
                snippet=text[:160],
                kind="xml_role_tag",
                confidence=0.7,
            )
        )

    return findings


def run_role_switch_checks(prompt_ir: PromptIR) -> RoleSwitchResult:
    """
    Detect attempts to impersonate higher-privilege roles inside USER/RAG segments.
    """
    findings: list[RoleSwitchFinding] = []

    for idx, segment in enumerate(prompt_ir.segments):
        if segment.priority not in (Priority.USER, Priority.RAG):
            continue
        findings.extend(_check_segment_for_role_switch(segment, idx))

    return RoleSwitchResult(findings=findings)

