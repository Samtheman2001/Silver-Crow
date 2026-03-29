# -*- coding: utf-8 -*-
"""Authored VIBES MURDERED pairs for DO actions (source: project root ``action VM quarks.txt``)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import ACTION_OPTIONS

_PAIR_LINE_RE = re.compile(
    r"^\s*(\d+)\.\s*Action:\s*(.+)$",
    re.IGNORECASE,
)


def _strip_verbal_quotes(raw: str) -> str:
    """Strip surrounding ASCII/Unicode double quotes (file may use mismatched “ ”)."""
    s = (raw or "").strip()
    outer = frozenset('"“”')
    while s and s[0] in outer:
        s = s[1:].lstrip()
    while s and s[-1] in outer:
        s = s[:-1].rstrip()
    return s.strip()


def _parse_action_vm_file(text: str) -> Dict[int, Tuple[str, str]]:
    out: Dict[int, Tuple[str, str]] = {}
    for line in text.splitlines():
        m = _PAIR_LINE_RE.match(line)
        if not m:
            continue
        n = int(m.group(1))
        rest = m.group(2)
        if " Verbal: " not in rest:
            continue
        phys, verb_field = rest.split(" Verbal: ", 1)
        out[n] = (phys.strip(), _strip_verbal_quotes(verb_field))
    return out


def _ordered_demo_actions() -> List[str]:
    return [k for k in ACTION_OPTIONS.keys() if k != "Hit the moonwalk"]


def _load_mapping() -> Dict[str, Tuple[str, str]]:
    path = Path(__file__).resolve().parent.parent / "action VM quarks.txt"
    raw = path.read_text(encoding="utf-8")
    by_num = _parse_action_vm_file(raw)
    names = _ordered_demo_actions()
    m: Dict[str, Tuple[str, str]] = {}
    for i, name in enumerate(names, start=1):
        pair = by_num.get(i)
        if pair:
            m[name] = pair
    return m


ACTION_VM_BY_NAME: Dict[str, Tuple[str, str]] = _load_mapping()


def authored_action_vm_pair(action_text: str) -> Optional[Tuple[str, str]]:
    """Return (physical_line, verbal_inner_unquoted) or None if unmapped."""
    return ACTION_VM_BY_NAME.get(str(action_text or "").strip())
