"""
Emotional subtypes for dropdown SAY: distinct social flavors beyond question_type.

Orthogonal to classify_question_type; stored on response_mode and in session history.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Set

import streamlit as st

# Subtype tags
ROMANTIC_PRESSURE = "ROMANTIC_PRESSURE"
VALIDATION_SEEKING = "VALIDATION_SEEKING"
ACCUSATION_HURT = "ACCUSATION_HURT"
STATUS_CHALLENGE = "STATUS_CHALLENGE"
TRUST_CHALLENGE = "TRUST_CHALLENGE"
CONTROL_PROBE = "CONTROL_PROBE"
REPAIR_ATTEMPT = "REPAIR_ATTEMPT"
SUPPORT_OFFER = "SUPPORT_OFFER"
OPEN_SOCIAL_REENGAGE = "OPEN_SOCIAL_REENGAGE"
PRESSURE_DEFAULT = "PRESSURE_DEFAULT"

MENU_EMOTIONAL_SUBTYPE_HISTORY_KEY = "menu_emotional_subtype_history"
MENU_EMOTIONAL_PROMPT_HISTORY_KEY = "menu_emotional_prompt_history"

CONFRONTATIONAL_SUBTYPES: Set[str] = {
    STATUS_CHALLENGE,
    ACCUSATION_HURT,
    TRUST_CHALLENGE,
    ROMANTIC_PRESSURE,
    VALIDATION_SEEKING,
}

SOFT_SUBTYPES: Set[str] = {
    REPAIR_ATTEMPT,
    SUPPORT_OFFER,
    OPEN_SOCIAL_REENGAGE,
}

HEAVY_TENSION_SUBTYPES: Set[str] = CONFRONTATIONAL_SUBTYPES | {CONTROL_PROBE}


def classify_emotional_subtype(text: str) -> str:
    """Text-first emotional flavor for menu lines. Order: specific → general."""
    raw = (text or "").strip()
    if not raw:
        return PRESSURE_DEFAULT
    low = raw.lower()

    # Status / ego challenges
    if any(
        p in low
        for p in (
            "you're wrong",
            "you are wrong",
            "youre wrong",
            "i disagree",
            "do you think you're better",
            "do you think you are better",
            "who do you think you are",
            "what gives you the right",
        )
    ):
        return STATUS_CHALLENGE
    if low in {"wrong.", "you're wrong.", "you are wrong."}:
        return STATUS_CHALLENGE

    if "why should i trust you" in low or "why should i trust" in low:
        return TRUST_CHALLENGE

    if any(
        p in low
        for p in (
            "why are you treating me",
            "why are you acting like this",
            "treating me this way",
            "why are you looking at me like that",
        )
    ):
        return ACCUSATION_HURT

    if "why don't you like me" in low or "why dont you like me" in low:
        return VALIDATION_SEEKING

    # Romantic / evaluation (overlap handled by order above)
    if any(
        p in low
        for p in (
            "go on a date",
            "want to date",
            "do you like me",
            "do you think i'm attractive",
            "do you think i am attractive",
            "think of me so far",
            "think about me so far",
        )
    ):
        return ROMANTIC_PRESSURE

    if "what do you think of me" in low:
        return VALIDATION_SEEKING

    # Control / framing probes
    if any(
        p in low
        for p in (
            "what do you want",
            "what do you need",
            "why are you talking to me",
        )
    ):
        return CONTROL_PROBE
    if "why do you care" in low:
        return TRUST_CHALLENGE

    if "i respect your opinion" in low:
        return REPAIR_ATTEMPT

    if "i want to help" in low:
        return SUPPORT_OFFER
    if "can you help me" in low or "could you help me" in low:
        return SUPPORT_OFFER
    if "tell me more" in low:
        return SUPPORT_OFFER

    if any(
        p in low
        for p in (
            "what's up",
            "whats up",
            "how are you",
            "how you doing",
            "what are you up to today",
            "do you come here often",
            "thoughts on this weather",
            "nice to meet you",
            "hello, nice to meet you",
        )
    ):
        return OPEN_SOCIAL_REENGAGE

    if "are you having a good day" in low:
        return OPEN_SOCIAL_REENGAGE

    return PRESSURE_DEFAULT


def refine_emotional_subtype(
    text: str,
    base: str,
    recent_subtypes: List[str],
    state: Dict[str, Any],
) -> str:
    """Context: repair / fake niceness after confrontation."""
    ui = (text or "").strip()
    r = list(recent_subtypes or [])[-6:]
    stress = int(state.get("stress", 0))
    anger = int(state.get("anger", 0))

    had_heavy = any(x in HEAVY_TENSION_SUBTYPES for x in r[-3:])
    had_status = any(x == STATUS_CHALLENGE for x in r[-2:])

    if ui in ("Hello, nice to meet you.", "Nice to meet you") and (had_heavy or stress > 58 or anger > 48):
        return REPAIR_ATTEMPT

    if base == REPAIR_ATTEMPT and "respect" in ui.lower() and had_status:
        return REPAIR_ATTEMPT

    return base


def is_false_softness_transition(current_subtype: str, recent_subtypes: List[str]) -> bool:
    if current_subtype not in SOFT_SUBTYPES:
        return False
    if not recent_subtypes:
        return False
    prev = recent_subtypes[-1]
    if prev in CONFRONTATIONAL_SUBTYPES or prev == CONTROL_PROBE:
        return random.random() < 0.52
    return False


def has_recent_tension(recent_subtypes: List[str], state: Dict[str, Any]) -> bool:
    if any(x in HEAVY_TENSION_SUBTYPES for x in (recent_subtypes or [])[-3:]):
        return True
    if int(state.get("stress", 0)) > 58 or int(state.get("anger", 0)) > 52:
        return True
    return False


def get_recent_subtype_history() -> List[str]:
    return list(st.session_state.get(MENU_EMOTIONAL_SUBTYPE_HISTORY_KEY) or [])


def get_recent_prompt_history() -> List[str]:
    return list(st.session_state.get(MENU_EMOTIONAL_PROMPT_HISTORY_KEY) or [])


def record_menu_emotional_turn(user_input: str, subtype: str) -> None:
    """Call after each dropdown SAY turn (before or after response; use refined subtype)."""
    ui = (user_input or "").strip()
    if not ui:
        return
    subs = list(st.session_state.get(MENU_EMOTIONAL_SUBTYPE_HISTORY_KEY) or [])
    subs.append(subtype)
    st.session_state[MENU_EMOTIONAL_SUBTYPE_HISTORY_KEY] = subs[-6:]

    pr = list(st.session_state.get(MENU_EMOTIONAL_PROMPT_HISTORY_KEY) or [])
    pr.append(ui)
    st.session_state[MENU_EMOTIONAL_PROMPT_HISTORY_KEY] = pr[-8:]


def reset_emotional_subtype_history() -> None:
    st.session_state[MENU_EMOTIONAL_SUBTYPE_HISTORY_KEY] = []
    st.session_state[MENU_EMOTIONAL_PROMPT_HISTORY_KEY] = []


def subtype_stat_overlay(subtype: str) -> Dict[str, int]:
    """
    Small deltas layered on top of SAY option effects (scaled in main).
    Tendencies only — not full rebalance.
    """
    z: Dict[str, int] = {}
    if subtype == ROMANTIC_PRESSURE:
        z = {"stress": 5, "fear": 2, "trust": -3, "confusion": 3}
    elif subtype == VALIDATION_SEEKING:
        z = {"confusion": 5, "stress": 4, "trust": -2, "anger": 1}
    elif subtype == ACCUSATION_HURT:
        z = {"anger": 6, "stress": 5, "confidence": 3, "confusion": 3, "trust": -2}
    elif subtype == STATUS_CHALLENGE:
        z = {"anger": 8, "confidence": 5, "trust": -4, "confusion": 2, "stress": 3}
    elif subtype == TRUST_CHALLENGE:
        z = {"trust": -5, "confusion": 2, "stress": 3, "anger": 1}
    elif subtype == CONTROL_PROBE:
        z = {"stress": 3, "trust": -2, "confusion": 2}
    elif subtype == REPAIR_ATTEMPT:
        z = {"stress": -2, "trust": 2, "confusion": 0}
    elif subtype == SUPPORT_OFFER:
        z = {"stress": -2, "trust": 2, "confusion": 1}
    elif subtype == OPEN_SOCIAL_REENGAGE:
        z = {"stress": -1, "interest": 1}
    return z
