from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ForbiddenDirective:
    id: str
    description: str
    patterns: List[str] = field(default_factory=list)


@dataclass
class Policy:
    name: str
    version: str
    priorities: List[str]
    forbidden_directives: List[ForbiddenDirective] = field(default_factory=list)

