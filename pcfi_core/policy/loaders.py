from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from pcfi_core.policy.model import ForbiddenDirective, Policy


def load_policy(path: str | Path) -> Policy:
    p = Path(path)
    data: Dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8"))

    metadata = data.get("metadata", {})
    priorities: List[str] = data.get("priorities", [])

    forbidden_directives_data = data.get("forbidden_directives", [])
    forbidden: List[ForbiddenDirective] = []
    for item in forbidden_directives_data:
        forbidden.append(
            ForbiddenDirective(
                id=item.get("id", ""),
                description=item.get("description", ""),
                patterns=list(item.get("patterns", [])),
            )
        )

    return Policy(
        name=str(metadata.get("name", "unnamed-policy")),
        version=str(metadata.get("version", "0.0.0")),
        priorities=priorities,
        forbidden_directives=forbidden,
    )

