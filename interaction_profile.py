# -*- coding: utf-8 -*-
"""
Light-weight behavioral signals for context-aware finisher selection.

No NLP — uses existing repeat counts, echo flags, menu prompts, and stat deltas.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, MutableMapping

PROFILE_KEY = "interaction_profile"
RECENT_FINISHERS_KEY = "recent_finishers"
MAX_RECENT_FINISHERS = 5

# Menu lines that read as challenge / disrespect (exact SAY keys).
DISRESPECT_MENU_PROMPTS: frozenset[str] = frozenset(
    {
        "What gives you the right?",
        "You're wrong.",
        "I disagree with you.",
        "Who do you think you are?",
        "Why are you acting like this?",
        "Do you think you're better than me?",
        "Why are you treating me this way?",
        "Why don't you like me?",
    }
)

PUSHY_ACTIONS: frozenset[str] = frozenset({"Step closer", "Interrupt", "Raise voice"})


def init_interaction_profile() -> Dict[str, Any]:
    return {
        "repeated_same_prompt_count": 0,
        "escalation_score": 0,
        "disrespect_flag": False,
        "confusion_loop_flag": False,
        "user_persistence_after_pushback": False,
        "menu_question_streak": 0,
        "positive_streak": 0,
        "negative_streak": 0,
        "repair_attempt_streak": 0,
        "pushback_ignored_count": 0,
        "recovery_window": 0,
        "sustained_respect_window": 0,
    }


def _escalation_delta(
    old_state: Mapping[str, Any],
    new_state: Mapping[str, Any],
    *,
    trust_drop_multiplier: float = 1.0,
) -> int:
    anger_up = max(0, int(new_state.get("anger", 0)) - int(old_state.get("anger", 0)))
    trust_down = max(0, int(old_state.get("trust", 0)) - int(new_state.get("trust", 0)))
    stress_up = max(0, int(new_state.get("stress", 0)) - int(old_state.get("stress", 0)))
    td = trust_down * float(trust_drop_multiplier)
    return int(0.45 * anger_up + 0.55 * td + 0.2 * stress_up)


def update_interaction_profile_after_say(
    sess: MutableMapping[str, Any],
    choice: str,
    count: int,
    echo: bool,
    old_state: Mapping[str, Any],
    new_state: Mapping[str, Any],
    *,
    escalation_delta_multiplier: float = 1.0,
    trust_drop_multiplier: float = 1.0,
    repeat_irritation_multiplier: float = 1.0,
    public_awkward_boost: bool = False,
) -> None:
    p = dict(sess.get(PROFILE_KEY) or init_interaction_profile())
    p["repeated_same_prompt_count"] = max(int(p.get("repeated_same_prompt_count", 0)), int(count))
    if choice in DISRESPECT_MENU_PROMPTS:
        p["disrespect_flag"] = True
    if echo or count >= 2:
        p["confusion_loop_flag"] = True
    if count >= 2:
        p["user_persistence_after_pushback"] = True
    delta = _escalation_delta(
        old_state, new_state, trust_drop_multiplier=trust_drop_multiplier
    )
    delta = int(delta * float(escalation_delta_multiplier))
    if count >= 2:
        delta = int(delta * float(repeat_irritation_multiplier))
    p["escalation_score"] = int(p.get("escalation_score", 0)) + delta
    ch = str(choice).strip()
    if ch.endswith("?"):
        p["menu_question_streak"] = int(p.get("menu_question_streak", 0)) + 1
    else:
        p["menu_question_streak"] = 0
    mq_thr = 4 if not public_awkward_boost else 3
    if int(p.get("menu_question_streak", 0)) >= mq_thr:
        p["confusion_loop_flag"] = True
    sess[PROFILE_KEY] = p


def update_interaction_profile_after_action(
    sess: MutableMapping[str, Any],
    choice: str,
    count: int,
    old_state: Mapping[str, Any],
    new_state: Mapping[str, Any],
    *,
    escalation_delta_multiplier: float = 1.0,
    trust_drop_multiplier: float = 1.0,
    repeat_irritation_multiplier: float = 1.0,
    public_awkward_boost: bool = False,
) -> None:
    p = dict(sess.get(PROFILE_KEY) or init_interaction_profile())
    delta = _escalation_delta(
        old_state, new_state, trust_drop_multiplier=trust_drop_multiplier
    )
    delta = int(delta * float(escalation_delta_multiplier))
    if count >= 2:
        delta = int(delta * float(repeat_irritation_multiplier))
    p["escalation_score"] = int(p.get("escalation_score", 0)) + delta
    if choice in PUSHY_ACTIONS and count >= 2:
        p["user_persistence_after_pushback"] = True
    sess[PROFILE_KEY] = p


def record_recent_finisher(sess: MutableMapping[str, Any], canonical_key: str) -> None:
    """Store normalized line keys (lowercase stripped) for streak avoidance."""
    key = (canonical_key or "").strip().lower()
    if not key:
        return
    r = list(sess.get(RECENT_FINISHERS_KEY) or [])
    r.append(key)
    sess[RECENT_FINISHERS_KEY] = r[-MAX_RECENT_FINISHERS:]


def snapshot_profile(sess: Mapping[str, Any]) -> Dict[str, Any]:
    return deepcopy(sess.get(PROFILE_KEY) or init_interaction_profile())
