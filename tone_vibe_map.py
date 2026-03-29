# -*- coding: utf-8 -*-
"""
Deterministic tone + vibe resolution: aligned pairs from category, ending state,
verbal/physical heuristics, then stats (no random label pools).
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple

from utils import strip_outer_quotes

# Free-text category → (tone, vibe) — HOW delivery + WHAT the moment feels like
_CATEGORY_TONE_VIBE: dict[str, Tuple[str, str]] = {
    "apology": ("calm", "chill"),
    "absurd": ("intrigued", "interesting"),
    "aggressive_light": ("tense", "uncomfortable"),
    "aggressive_medium": ("hostile", "not chill"),
    "aggressive_hard": ("furious", "unfathomable"),
    "joking": ("playful", "chill"),
    "awkward": ("hesitant", "awkward"),
    "friendly": ("curious", "chill"),
    "neutral": ("neutral", "open"),
}


def _state_int(state: Mapping[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(state.get(key, default))
    except (TypeError, ValueError):
        return default


def deterministic_tone_vibe_from_state(state: Mapping[str, Any]) -> Tuple[str, str]:
    """Same priority order as infer_tone / infer_vibe, but fixed pairs (no preferred_* random)."""
    a = _state_int(state, "anger")
    t = _state_int(state, "trust")
    s = _state_int(state, "stress")
    h = _state_int(state, "happiness")
    c = _state_int(state, "confusion")
    i = _state_int(state, "interest")
    f = _state_int(state, "fear")

    if a > 70 and t < 30:
        return "hostile", "not chill"
    if a > 86 and s > 80:
        return "furious", "unfathomable"
    if a > 78 and s > 72:
        return "hostile", "intense"
    if s > 70 or f > 70:
        return "tense", "on edge"
    if t > 75 and h > 65:
        return "warm", "comfortable"
    if f > 70:
        return "uncertain", "uneasy"
    if c > 76:
        return "confused", "interesting"
    if i > 72:
        return "engaged", "curious"
    if s < 30 and a < 30:
        return "calm", "chill"
    return "neutral", "open"


def _maybe_adjust_category_for_state(
    pair: Tuple[str, str], state: Mapping[str, Any], category: str
) -> Tuple[str, str]:
    tone, vibe = pair
    a = _state_int(state, "anger")
    s = _state_int(state, "stress")
    if category == "joking" and (a > 52 or s > 62):
        return "tense", "awkward"
    if category in ("friendly", "neutral") and a > 65:
        return "guarded", "uncomfortable"
    if category == "apology" and a > 60:
        return "cool", "tense"
    return tone, vibe


def _classify_from_text(inner_l: str, phy_l: str, prompt_l: str, kind: str) -> Optional[Tuple[str, str]]:
    """Keyword / pattern pass; first match wins (deterministic order)."""
    blob = f"{inner_l} {phy_l} {prompt_l}"

    if "overstimulated" in inner_l or inner_l.strip() == "overstimulated":
        return "electric", "overstimulated"

    surreal_tokens = (
        "moonwalk",
        "fuck it up",
        "simulation",
        "glitch",
        "universe",
        "rulerz",
    )
    if any(tok in blob for tok in surreal_tokens):
        return "electric", "vibing"

    hostile_tokens = (
        "back off",
        "step back",
        "touch me",
        "i'm done",
        "i'm leaving",
        "we're done",
        "shut up",
        "shut it",
        "enough",
        "stop that",
        "stop doing",
        "before i",
        "a problem",
        "storm",
        "slaps",
        "snaps",
        "squares up",
        "i'm out",
        "nope.",
        "conversation over",
    )
    if any(tok in blob for tok in hostile_tokens):
        return "furious", "uncomfortable"

    calm_tokens = (
        "apology accepted",
        "we're fine",
        "water under",
        "appreciate you",
        "thanks for saying",
        "we're cool",
        "don't worry about it",
        "hear you",
    )
    if any(tok in inner_l for tok in calm_tokens):
        return "calm", "chill"

    repeat_tokens = (
        "repeating yourself",
        "just asked",
        "asking that again",
        "said that",
        "you already said",
        "looping",
        "weirdly familiar",
        "say that again",
    )
    if any(tok in inner_l for tok in repeat_tokens):
        return "tense", "awkward"

    confused_tokens = (
        "what are you",
        "what's that",
        "what does that",
        "not following",
        "doesn't parse",
        "make sense",
        "repeat",
        "again?",
        "you just",
        "why are you",
    )
    if any(tok in inner_l for tok in confused_tokens):
        return "confused", "interesting"

    if inner_l.endswith("?") and len(inner_l) < 120:
        if any(w in inner_l for w in ("why", "what", "how", "who", "you good", "okay")):
            return "curious", "interesting"

    if kind == "do" and not inner_l.strip() and phy_l:
        if any(x in phy_l for x in ("smile", "grin", "handshake")):
            return "warm", "chill"
        if any(x in phy_l for x in ("irritated", "annoyed", "stiff", "pulls away", "crosses arms")):
            return "tense", "awkward"

    return None


_SURREAL_GUARD = (
    "moonwalk",
    "fuck it up",
    "simulation",
    "glitch",
    "universe",
    "rulerz",
)


def _coherence_adjust(
    inner_l: str, phy_l: str, tone: str, vibe: str, *, prompt_l: str = ""
) -> Tuple[str, str]:
    """Last pass: align tone/vibe with obvious verbal + physical cues (deterministic)."""
    blob = f"{inner_l} {phy_l} {prompt_l}".lower()
    il = (inner_l or "").strip().lower()
    t_lo = (tone or "").strip().lower()
    v_lo = (vibe or "").strip().lower()

    if "overstimulated" in blob or il == "overstimulated":
        return "electric", "overstimulated"

    if any(s in blob for s in _SURREAL_GUARD):
        soft_tone = frozenset({"calm", "warm", "neutral", "playful", "gentle", "cool", "curious"})
        soft_vibe = frozenset({"chill", "open", "comfortable", "calm", "neutral", "promising", "interesting"})
        if t_lo in soft_tone or v_lo in soft_vibe:
            return "electric", "vibing"

    threat_tokens = (
        "back off",
        "step back",
        "touch me",
        "i'm done",
        "i'm leaving",
        "we're done",
        "shut up",
        "kill",
        "fight",
        "hurt you",
        "hurt me",
        "punch",
        "knife",
        "gun",
        "weapon",
        "slaps",
        "slap ",
        "squares up",
        "storm off",
        "storms off",
        "snaps at",
        "destroy",
        "ruin you",
        "choke",
        "bleed",
    )
    threat = any(tok in blob for tok in threat_tokens)
    soft_tone = frozenset({"calm", "warm", "curious", "playful", "neutral", "gentle", "cool"})
    soft_vibe = frozenset({"chill", "open", "comfortable", "calm", "promising", "vibing", "neutral"})
    if threat and (t_lo in soft_tone or v_lo in soft_vibe):
        return "furious", "uncomfortable"

    hesitant = any(
        h in blob
        for h in (
            "i don't know",
            "not sure",
            "i'm not sure",
            "uh…",
            "uh...",
            "um…",
            "um...",
            "tilts head",
            "furrows brow",
            "hesitat",
            "lost me",
            "confusing",
        )
    )
    hard_t = frozenset({"furious", "hostile", "mad", "angry"})
    hard_v = frozenset({"murdered", "unfathomable", "intense", "done"})
    if hesitant and (t_lo in hard_t or v_lo in hard_v):
        return "uncertain", "interesting"

    polite = any(
        p in il
        for p in (
            "nice to meet you",
            "nice to meet",
            "thanks for saying",
            "apology accepted",
            "i appreciate you",
            "i appreciate that",
            "glad we",
            "we're good",
            "we're fine",
            "water under",
            "don't worry about it",
        )
    )
    if polite and not threat:
        if t_lo in hard_t or v_lo in hard_v:
            return "calm", "chill"

    return tone, vibe


def resolve_tone_and_vibe(
    *,
    kind: str,
    is_free_text: bool,
    free_text_category: Optional[str],
    state: Mapping[str, Any],
    verbal_quoted: str,
    physical: str,
    prompt: str,
    source: str,
    ended: bool,
    apply_murdered_state: bool,
    ending_message: str,
    special_ending: Optional[str],
    preliminary_tone: str,
    preliminary_vibe: str,
) -> Tuple[str, str]:
    """
    Priority:
    1) Dropdown menu SAY (authored ladder) — keep preliminary
    2) Authored non-ending DO beats (e.g. moonwalk quarks) — keep preliminary
    3) Terminal endings (VM, overstim, hard conv end)
    4) Free-text category table (+ light state adjustment)
    5) Verbal / physical / prompt heuristics
    6) Stats-derived pair
    """
    if kind == "say" and not is_free_text:
        return preliminary_tone, preliminary_vibe

    if kind == "do" and source == "authored" and not ended:
        return preliminary_tone, preliminary_vibe

    if apply_murdered_state or (ending_message or "").strip() == "VIBES MURDERED":
        return "furious", "murdered"
    if special_ending == "overstimulated":
        return "electric", "overstimulated"
    inner_check = strip_outer_quotes(verbal_quoted or "").strip().lower()
    if inner_check == "overstimulated":
        return "electric", "overstimulated"
    if ended and (ending_message or "").strip() == "CONVERSATION ENDED":
        return "hostile", "done"

    inner = strip_outer_quotes(verbal_quoted or "").strip()
    inner_l = inner.lower()
    phy_l = (physical or "").strip().lower()
    prompt_l = (prompt or "").strip().lower()

    # Content signals before broad category (e.g. repeat warnings vs "friendly" classifier)
    hit = _classify_from_text(inner_l, phy_l, prompt_l, kind)
    if hit:
        return _coherence_adjust(inner_l, phy_l, hit[0], hit[1], prompt_l=prompt_l)

    if kind == "say" and is_free_text and free_text_category:
        cat = str(free_text_category)
        base = _CATEGORY_TONE_VIBE.get(cat)
        if base:
            pair = _maybe_adjust_category_for_state(base, state, cat)
            return _coherence_adjust(inner_l, phy_l, pair[0], pair[1], prompt_l=prompt_l)

    stp = deterministic_tone_vibe_from_state(state)
    return _coherence_adjust(inner_l, phy_l, stp[0], stp[1], prompt_l=prompt_l)
