"""
Generic helpers (low-level). Keep import-safe and reusable.
"""

from __future__ import annotations

import random
import re
from copy import deepcopy

from .config import (
    BASE_STATE,
    PERSONALITIES,
    BACKGROUNDS,
    PHYSICAL_STATES,
    STARTING_MOODS,
    SCENARIOS,
)


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def clamp01(x):
    return max(0.0, min(1.0, float(x)))


def apply_mods(state, mods, scale=1.0):
    for key, delta in mods.items():
        if key in state:
            state[key] = clamp(state[key] + int(round(delta * scale)))
    return state


def scale_stat_mods(mods, factor):
    if not mods:
        return {}
    return {k: int(round(v * factor)) for k, v in mods.items() if k in BASE_STATE}


def say_option_stat_mods(option):
    if option is None:
        return {}
    if isinstance(option, dict) and "effects" in option:
        return option["effects"]
    if isinstance(option, dict) and "responses" not in option:
        return {k: v for k, v in option.items() if k in BASE_STATE}
    return {}


def apply_ripple_effects(state, mods, scale=1.0, sassy_comeback=False):
    """When sassy_comeback True, skip ripples that make a sharp comeback look emotionally defeated."""
    ripple = {}
    if mods.get("trust", 0) > 0:
        ripple["fear"] = ripple.get("fear", 0) - 1
    if mods.get("trust", 0) < 0:
        ripple["stress"] = ripple.get("stress", 0) + 1
    if mods.get("anger", 0) > 0 and not sassy_comeback:
        ripple["happiness"] = ripple.get("happiness", 0) - 1
    if mods.get("happiness", 0) > 0:
        ripple["stress"] = ripple.get("stress", 0) - 1
    if mods.get("interest", 0) > 0:
        ripple["confidence"] = ripple.get("confidence", 0) + 1
    if mods.get("confusion", 0) > 0 and not sassy_comeback:
        ripple["confidence"] = ripple.get("confidence", 0) - 1
    if mods.get("fear", 0) > 0:
        ripple["trust"] = ripple.get("trust", 0) - 1
    if ripple:
        apply_mods(state, ripple, scale)
    return state


def build_state(personality, background, physical_state, mood, scenario):
    state = deepcopy(BASE_STATE)
    for source in [
        PERSONALITIES[personality],
        BACKGROUNDS[background],
        PHYSICAL_STATES[physical_state],
        STARTING_MOODS[mood],
        SCENARIOS[scenario]["mods"],
    ]:
        apply_mods(state, source)
    return state


def quote(text):
    return f'"{text}"'


def strip_outer_quotes(verbal):
    if not verbal or not isinstance(verbal, str):
        return ""
    s = verbal.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


# Short engine physical lines only (demo readability).
_DEMO_PHYSICAL_FALLBACKS = (
    "looks at you",
    "pauses",
    "pulls back slightly",
    "goes still",
    "looks away",
    "shakes your hand",
)


def clamp_demo_physical_line(physical: str) -> str:
    """If stacked/generated physical is too long, replace with a short safe line."""
    s = (physical or "").strip()
    if len(s) <= 56:
        return s
    return random.choice(_DEMO_PHYSICAL_FALLBACKS)


def sanitize_live_verbal_inner(text: str, *, character_name: str = "") -> str:
    """Strip author notes, resolve common placeholders, drop unknown {tokens}."""
    s = str(text or "")
    s = re.sub(r"\[[^\]]*\]", "", s)
    cn = (character_name or "").strip()
    if cn:
        s = s.replace("{character_name}", cn).replace("{CHARACTER_NAME}", cn)
    s = s.replace("{name}", cn).replace("{NAME}", cn)
    s = re.sub(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    if not s:
        return "Yeah."
    return s


def sanitize_verbal_for_display(verbal: str, *, character_name: str = "") -> str:
    """Quoted hero line: clean inner text, then re-quote for UI."""
    if not str(verbal or "").strip():
        return ""
    inner = strip_outer_quotes(verbal or "").strip()
    clean = sanitize_live_verbal_inner(inner, character_name=character_name)
    if not clean:
        clean = "Yeah."
    return quote(clean)


def sanitize_physical_for_display(physical: str) -> str:
    """Drop only very long stacked/generated physical lines; keep normal authored sentences."""
    p = (physical or "").strip()
    if not p:
        return ""
    if len(p) <= 120:
        return p
    return clamp_demo_physical_line(p)


def murdered_state(state):
    state["interest"] = 2
    state["trust"] = min(state["trust"], 8)
    state["anger"] = max(state["anger"], 82)
    state["stress"] = max(state["stress"], 78)
    state["happiness"] = min(state["happiness"], 10)
    state["confidence"] = max(12, min(state["confidence"], 55))
    state["fear"] = max(state["fear"], 18)
    return state


def verbal_triggers_conversation_shutdown(verbal):
    s = strip_outer_quotes(verbal).lower()
    needles = (
        "conversation's over",
        "conversation’s over",
        "i'm not entertaining this",
        "i’m not entertaining this",
        "yeah, we're done if",
        "yeah, we’re done if",
        "we're done if that's how",
        "we’re done if that’s how",
    )
    return any(n in s for n in needles)


def normalize_speech(text):
    if not text or not str(text).strip():
        return ""
    s = str(text).strip().lower()
    out = []
    for ch in s:
        if ch.isalnum() or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


def _stable_seed_from_text(text):
    """Deterministic seed from text; avoids Python's randomized hash()."""
    s = str(text or "")
    acc = 1469598103934665603  # FNV-ish
    for ch in s:
        acc ^= ord(ch)
        acc *= 1099511628211
        acc &= (1 << 64) - 1
    return int(acc % 2_000_000_000)


def _dna_clamp_trait(x):
    return int(clamp(int(round(x)), 0, 100))

