"""
Lightweight voice tuning: fewer hedges, tighter phrasing, slightly higher commitment.

Applied after menu intelligence picks a line; re-validation happens in menu_responses.
"""

from __future__ import annotations

import random
import re
from typing import Dict

_HEDGE_HINTS = (
    "maybe",
    "depends",
    "kind of",
    "kinda",
    "sort of",
    "i guess",
    "i don't know",
    "don't know",
    "not sure",
    "probably",
    "might be",
    "could be",
    "i'm not sure",
    "honestly?",
    "to be honest",
    "fair enough",
    "that's valid",
    "thats valid",
    "makes sense",
    "i suppose",
    "in a sense",
)

_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"^I don't really think that\s+", ""),
    (r"^I don't really think\s+", ""),
    (r"^I don't think that\s+", ""),
    (r"^I don't think\s+", ""),
    (r"^I guess\s+", ""),
    (r"^Maybe\.?\s+", ""),
    (r"^Um[,.…]?\s*", ""),
    (r"^Uh[,.…]?\s*", ""),
    (r"\bkind of\b", ""),
    (r"\bkinda\b", ""),
    (r"\bsort of\b", ""),
    (r"^Honestly\?\s+", ""),
    (r"^To be honest,?\s+", ""),
    (r"\s+though\.$", "."),
)


def maybe_sharpen_response(
    text: str,
    state: Dict[str, int | float],
    personality: str = "",
    *,
    voice_sharpen_bias: float = 0.0,
) -> str:
    """Optionally tighten phrasing; returns original if nothing safe applies."""
    if not text or not str(text).strip():
        return text
    original = text.strip()
    low = original.lower()

    conf = int(state.get("confidence", 50) or 50)
    stress = int(state.get("stress", 30) or 30)

    p_base = 0.40 + float(voice_sharpen_bias or 0.0)
    if personality == "Confident":
        p_base += 0.12
    elif personality == "Aggressive":
        p_base += 0.10
    elif personality == "Impulsive":
        p_base += 0.06
    elif personality == "Shy":
        p_base -= 0.12
    elif personality == "Empathetic":
        p_base -= 0.05
    p_base += (conf - 50) * 0.0035
    p_base -= (stress - 30) * 0.0025
    p_base += random.uniform(-0.032, 0.032)
    p_base = max(0.12, min(0.86, p_base))

    has_hedge = any(h in low for h in _HEDGE_HINTS)
    short_cutoff = 34 + random.randint(-3, 5)
    if not has_hedge and len(original) < short_cutoff:
        if random.random() > 0.14 + random.uniform(0, 0.06):
            return text
    if random.random() > p_base and not has_hedge:
        return text

    out = original
    for pat, repl in _REPLACEMENTS:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)

    out = re.sub(r"\s+", " ", out).strip()
    if not out or len(out) < 2:
        return text

    if out[0].islower():
        out = out[0].upper() + out[1:]

    # Fix broken starts from aggressive stripping
    if out.lower().startswith("that 's "):
        out = "That's " + out[7:].lstrip()
    if out.lower().startswith("that s "):
        out = "That's " + out[7:].lstrip()

    return out
