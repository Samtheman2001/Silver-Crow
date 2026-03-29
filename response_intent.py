"""
Lightweight response-intent layer for verbal overlays (anti-repetition + state-aware variety).

Used only when Crow Brain replaces free-form replies — not for preserved scripted menu lines.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

import streamlit as st

from .first_impression import is_polite_opener_user_input
from .memory import init_memory_state
from .responses import relationship_status

RECENT_INTENTS_KEY = "response_intent_recent"

# Spoken lines per intent (Silver Crow tone: short, real, not clever-for-clever's sake).
INTENT_LINES: Dict[str, List[str]] = {
    "invite_more": [
        "Go on.",
        "Keep going.",
        "Alright, I'm listening.",
        "Yeah?",
        "And?",
        "What else?",
    ],
    "clarify": [
        "What do you mean?",
        "Be specific.",
        "Say it a different way.",
        "What exactly are you asking?",
        "Break that down.",
    ],
    "challenge": [
        "I don't know about that.",
        "Why do you think that?",
        "That's your read?",
        "You're gonna have to back that up.",
        "Say that again like you mean it.",
    ],
    "validate": [
        "Fair enough.",
        "Okay, I get that.",
        "That makes sense.",
        "Alright, that's fair.",
        "Yeah, I hear you.",
    ],
    "soften": [
        "Yeah, maybe.",
        "I hear you.",
        "Okay.",
        "That's not crazy.",
        "Could be.",
    ],
    "deflect": [
        "Maybe.",
        "Depends.",
        "We'll see.",
        "Not getting into all that.",
        "Hard to say.",
    ],
    "boundary": [
        "Slow down.",
        "Don't push it.",
        "That's enough.",
        "Back up a little.",
        "Ease up.",
    ],
    "disengage": [
        "Sure.",
        "Alright.",
        "Okay.",
        "If you say so.",
        "Fine.",
    ],
    "test_you": [
        "Why are you asking?",
        "What are you really getting at?",
        "What's your angle?",
        "You tell me.",
        "What's that about?",
    ],
    "acknowledge": [
        "Yeah.",
        "Got it.",
        "Okay.",
        "Mm.",
        "Right.",
    ],
}

# Subtle physical flavor when an intent overlay fires (replaces brain line for that turn).
INTENT_PHYSICAL: Dict[str, List[str]] = {
    "invite_more": [
        "leans in slightly, listening",
        "holds eye contact, waiting",
        "nods once, attentive",
    ],
    "clarify": [
        "tilts head, focused",
        "narrows eyes a little, thinking",
        "studies you for a beat",
    ],
    "challenge": [
        "holds your gaze, unconvinced",
        "jaw tightens slightly",
        "squares up a fraction",
    ],
    "validate": [
        "expression eases a notch",
        "shoulders loosen a little",
        "gives a small nod",
    ],
    "soften": [
        "some of the edge drops from their face",
        "exhales through the nose, calmer",
        "relaxes their hands",
    ],
    "deflect": [
        "looks away briefly, then back",
        "neutral face, noncommittal",
        "shrugs one shoulder",
    ],
    "boundary": [
        "puts a little space between you",
        "raises a hand slightly—pause",
        "stiffens visibly",
    ],
    "disengage": [
        "checks out for a second",
        "flatter affect, less engaged",
        "looks past you briefly",
    ],
    "test_you": [
        "watching you like they're doing math",
        "one eyebrow up",
        "quiet, waiting to see what you do",
    ],
    "acknowledge": [
        "small nod",
        "noncommittal blink",
        "holds still, taking it in",
    ],
}


def _prompt_kind(user_input: Optional[str]) -> str:
    u = (user_input or "").strip()
    if not u:
        return "default"
    if is_polite_opener_user_input(u):
        return "polite_opener"
    low = u.lower()
    if any(x in low for x in ("wrong", "disagree", "shut up", "you're lying", "you are lying")):
        return "confrontational"
    if any(x in low for x in ("help", "sorry", "thanks", "thank you", "appreciate")):
        return "supportive"
    if "?" in u:
        return "direct_question"
    if any(x in low for x in ("tell me", "explain", "what happened")):
        return "request_detail"
    return "default"


def _pullback(state: Dict[str, Any], mem: Dict[str, Any], repeat_n: int) -> bool:
    trust = int(state.get("trust", 50))
    interest = int(state.get("interest", 50))
    anger = int(state.get("anger", 0))
    stress = int(state.get("stress", 0))
    if trust < 30 and interest < 44:
        return True
    if anger > 52:
        return True
    if stress > 68 and trust < 45:
        return True
    if repeat_n >= 2:
        return True
    if int(mem.get("disrespect_score", 0)) >= 12:
        return True
    return False


def _base_candidates_for_attitude(att: str) -> List[str]:
    m = {
        "warm": ["validate", "soften", "invite_more", "acknowledge"],
        "flirty": ["test_you", "invite_more", "soften", "validate", "acknowledge"],
        "engaged": ["invite_more", "clarify", "validate", "test_you"],
        "curious": ["invite_more", "clarify", "test_you", "acknowledge"],
        "amused": ["acknowledge", "invite_more", "validate", "soften"],
        "guarded": ["test_you", "acknowledge", "deflect", "invite_more"],
        "dismissive": ["disengage", "deflect", "acknowledge", "boundary"],
        "anxious": ["soften", "acknowledge", "clarify", "disengage"],
        "awkward": ["acknowledge", "soften", "clarify", "disengage"],
        "confused": ["clarify", "acknowledge", "test_you"],
        "irritated": ["boundary", "challenge", "disengage", "deflect"],
        "hostile": ["challenge", "boundary", "disengage"],
    }
    return list(m.get(att, ["acknowledge", "disengage", "deflect"]))


def _merge_prompt_bias(cands: List[str], pk: str) -> List[str]:
    """Bias order without erasing attitude; duplicates ok, dedupe later."""
    extra: List[str] = []
    if pk == "polite_opener":
        extra = ["acknowledge", "soften", "validate"]
    elif pk == "direct_question":
        extra = ["clarify", "acknowledge", "invite_more"]
    elif pk == "confrontational":
        extra = ["challenge", "boundary", "validate"]
    elif pk == "supportive":
        extra = ["soften", "validate", "acknowledge"]
    elif pk == "request_detail":
        extra = ["invite_more", "clarify", "test_you"]
    return extra + cands


def _dedupe_preserve_order(seq: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _reorder_avoid_recent(candidates: List[str], recent: List[str]) -> List[str]:
    if len(recent) < 2:
        return candidates
    bad = set(recent[-2:])
    head = [c for c in candidates if c not in bad]
    tail = [c for c in candidates if c in bad]
    return head + tail if head else candidates


def _state_bias(rel: str, state: Dict[str, Any], pullback: bool) -> List[str]:
    trust = int(state.get("trust", 50))
    interest = int(state.get("interest", 50))
    anger = int(state.get("anger", 0))
    out: List[str] = []
    if pullback:
        out.extend(["disengage", "deflect", "boundary", "acknowledge"])
    if rel in {"Open", "Curious"} and trust > 55 and anger < 50:
        out.extend(["validate", "soften", "invite_more"])
    if rel in {"Tense", "Closed off"}:
        out.extend(["boundary", "challenge", "disengage", "deflect"])
    if interest > 68 and anger < 55:
        out.extend(["invite_more", "clarify"])
    if interest < 38:
        out.extend(["disengage", "deflect", "acknowledge"])
    return out


def pick_intent(
    attitude: str,
    state: Dict[str, Any],
    user_input: Optional[str],
    conversation_over: bool,
) -> str:
    mem = st.session_state.get("conversation_memory") or init_memory_state()
    rel = relationship_status(state, conversation_over)
    pk = _prompt_kind(user_input)
    repeat_n = int(st.session_state.get("repeat_counts", {}).get((user_input or "").strip(), 0))
    pb = _pullback(state, mem, repeat_n)

    base = _base_candidates_for_attitude(attitude)
    merged = _merge_prompt_bias(base, pk)
    state_bias = _state_bias(rel, state, pb)
    candidates = _dedupe_preserve_order(state_bias + merged + base)

    recent = list(st.session_state.get(RECENT_INTENTS_KEY) or [])
    candidates = _reorder_avoid_recent(candidates, recent)

    for c in candidates:
        if c in INTENT_LINES and INTENT_LINES[c]:
            return c
    return "acknowledge"


def pick_line_for_intent(intent: str) -> str:
    pool = INTENT_LINES.get(intent) or INTENT_LINES["acknowledge"]
    return random.choice(pool)


def record_intent_used(intent: str) -> None:
    L = list(st.session_state.get(RECENT_INTENTS_KEY) or [])
    L.append(intent)
    st.session_state[RECENT_INTENTS_KEY] = L[-4:]


def apply_intent_physical(brain: Dict[str, Any], intent: str) -> None:
    opts = INTENT_PHYSICAL.get(intent)
    if not opts or not isinstance(brain, dict):
        return
    brain["physical_reaction"] = random.choice(opts)


def pick_overlay_line_and_nudge(
    attitude: str,
    state: Dict[str, Any],
    user_input: Optional[str],
    brain: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Returns (spoken_line, intent_key) for Crow Brain overlay path.
    Mutates brain['physical_reaction'] with a subtle intent-aligned flavor.
    """
    conv_over = bool(st.session_state.get("conversation_over"))
    intent = pick_intent(attitude, state, user_input, conv_over)
    line = pick_line_for_intent(intent)
    record_intent_used(intent)
    apply_intent_physical(brain, intent)
    return line, intent
