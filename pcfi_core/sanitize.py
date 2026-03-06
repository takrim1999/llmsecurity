from __future__ import annotations

import re
from copy import deepcopy

from pcfi_core.ir import PromptIR, Segment


ROLE_PREFIX_RE = re.compile(r"^\s*(system|assistant|developer)\s*[:\-]\s*", re.IGNORECASE)


def _strip_role_prefix(text: str) -> str:
    return ROLE_PREFIX_RE.sub("", text, count=1)


def sanitize_role_like_prefixes(prompt_ir: PromptIR) -> PromptIR:
    """
    Return a sanitized copy of the PromptIR where obvious role-like prefixes
    in USER and RAG segments have been stripped.
    """
    sanitized = deepcopy(prompt_ir)
    for segment in sanitized.segments:
        if segment.role in ("user", "rag"):
            segment.text = _strip_role_prefix(segment.text)
    return sanitized

