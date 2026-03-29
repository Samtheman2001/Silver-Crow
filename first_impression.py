"""
First-turn calibration for polite scripted openers (dropdown lines).

Keeps early greetings socially believable unless DNA, mood, scenario, memory,
or state justify a colder read.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from .config import SAY_OPTIONS, SCENARIOS
from .memory import init_memory_state
from .personality import get_character_dna
from .scenario_layer import get_scenario_profile

# Exact SAY_OPTIONS keys we treat as polite first-impression openers.
POLITE_SCRIPTED_OPENERS = frozenset(
    {
        "Hello, nice to meet you.",
        "Nice to meet you",
        "Hey, how are you?",
        "What's up?",
    }
)


def _memory_justifies_coldness(mem: Dict[str, Any], *, turn_zero: bool = False) -> bool:
    if int(mem.get("disrespect_score", 0)) >= 16:
        return True
    if bool(mem.get("last_turn_was_rude")):
        return True
    if int(mem.get("pressure_score", 0)) >= 35:
        return True
    if turn_zero:
        # First user line: don't treat trajectory labels alone as "cold OK" — no real history yet.
        return False
    traj = str(mem.get("interaction_trajectory", "") or "")
    if traj in {"losing_patience", "growing_tension", "suspicious"}:
        return True
    return False


def normalize_for_greeting_match(text: str) -> str:
    t = (text or "").strip().lower()
    for ch in ("'", "'"):  # noqa: RUF001
        t = t.replace(ch, "")
    for ch in "?!.,":
        t = t.replace(ch, " ")
    t = " ".join(t.split())
    return t


def is_polite_opener_user_input(user_input: Optional[str]) -> bool:
    """Scripted menu lines + common typed variants (e.g. 'What is up')."""
    if not user_input or not str(user_input).strip():
        return False
    u = user_input.strip()
    if u in POLITE_SCRIPTED_OPENERS:
        return True
    n = normalize_for_greeting_match(u)
    if "nice to meet" in n:
        return True
    if "how are you" in n or "how r you" in n:
        return True
    if (
        "what's up" in n
        or "whats up" in n
        or "what is up" in n
        or "what are you up to" in n
        or n in {"sup", "wassup", "whats good", "what's good"}
    ):
        return True
    if n in {"hi", "hello", "hey"} or n.startswith(("hello ", "hi ", "hey ")):
        return len(n) <= 48
    return False


def allows_cold_first_impression(
    state: Dict[str, Any],
    dna: Dict[str, Any],
    mood: str,
    scenario_name: str,
    memory: Dict[str, Any],
    brain_attitude: str = "",
    turns_before_reply: int = 99,
) -> bool:
    """True when a curt / skeptical first line is justified."""
    if mood in ("Irritated", "Anxious"):
        return True
    sp = float(get_scenario_profile(scenario_name).get("social_pressure", 0.5))
    if sp >= 0.62:
        return True
    sens = float(SCENARIOS.get(scenario_name, {}).get("sensitivity", 1.0))
    if sens >= 1.17:
        return True
    tz = turns_before_reply == 0
    if _memory_justifies_coldness(memory, turn_zero=tz):
        return True
    if int(state.get("anger", 0)) > 58 or int(state.get("trust", 0)) < 30:
        return True
    if int(state.get("stress", 0)) > 68:
        return True

    pat = int(dna.get("patience", 55)) if dna else 55
    agree = int(dna.get("agreeableness", 50)) if dna else 50
    bias = str(dna.get("bias", "") or "") if dna else ""
    if pat <= 33 or agree <= 26:
        return True
    if bias == "slightly_intense" and pat <= 42:
        return True

    if brain_attitude in {"hostile", "irritated"} and int(state.get("anger", 0)) > 48:
        return True
    return False


def calibrate_bucket_for_polite_opener(
    bucket: str,
    action_text: str,
    turns_before_reply: int,
    state: Dict[str, Any],
    dna: Optional[Dict[str, Any]],
    mood: str,
    scenario_name: str,
    memory: Dict[str, Any],
) -> str:
    """Soften negative/severe buckets for early polite openers when unjustified."""
    if not is_polite_opener_user_input(action_text):
        return bucket
    if turns_before_reply >= 2:
        return bucket
    dna = dna or {}
    if allows_cold_first_impression(
        state, dna, mood, scenario_name, memory, "", turns_before_reply=turns_before_reply
    ):
        return bucket
    if bucket == "severe":
        return "neutral"
    if bucket == "negative":
        return "neutral"
    return bucket


def first_turn_social_safe_zone(
    turns_before_reply: int,
    state: Dict[str, Any],
    dna: Dict[str, Any],
    mood: str,
    scenario_name: str,
    memory: Dict[str, Any],
    brain_attitude: str,
) -> bool:
    """True when we should not replace the greeting line with generic brain templates."""
    if turns_before_reply >= 2:
        return False
    if mood not in ("Neutral", "Calm", "Excited"):
        return False
    if allows_cold_first_impression(
        state, dna, mood, scenario_name, memory, brain_attitude, turns_before_reply=turns_before_reply
    ):
        return False
    return True


def first_impression_verbal_locked(
    user_input: Optional[str],
    turns_before_reply: int,
    state: Dict[str, Any],
    brain_attitude: str,
) -> bool:
    """
    Hard guardrail: keep build_response / rewrite output; no spike, quirk, or attitude one-liner.
    """
    if not is_polite_opener_user_input(user_input):
        return False
    if turns_before_reply >= 2:
        return False
    mem = st.session_state.get("conversation_memory") or init_memory_state()
    mood = (st.session_state.get("build_snapshot") or {}).get("Mood", "Neutral")
    scenario = str(st.session_state.get("selected_scenario") or "")
    dna = get_character_dna()
    return first_turn_social_safe_zone(
        turns_before_reply, state, dna, mood, scenario, mem, brain_attitude
    )


def should_preserve_scripted_greeting_verbal(
    user_input: Optional[str],
    turns_before_reply: int,
    state: Dict[str, Any],
    brain_attitude: str,
) -> bool:
    """If True, keep crow_brain output instead of attitude one-liners (alias for guardrail)."""
    return first_impression_verbal_locked(user_input, turns_before_reply, state, brain_attitude)


def preserve_scripted_menu_response(user_input: Optional[str], free_text_category=None) -> bool:
    """
    Dropdown lines with scripted response tables must keep build_response wording.
    Stops ?-marked social prompts from being treated as generic "confusing questions"
    and rewritten into clarification pools / curious attitude one-liners.
    """
    if free_text_category:
        return False
    u = (user_input or "").strip()
    if not u:
        return False
    opt = SAY_OPTIONS.get(u)
    return isinstance(opt, dict) and "responses" in opt
