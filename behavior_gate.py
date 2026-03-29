"""
Behavioral gating: question typing + response mode before Crow Brain / intent overlay.

Runs early in the say pipeline (after repeat count is known).
"""

from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from .emotional_subtype import (
    classify_emotional_subtype,
    get_recent_subtype_history,
    refine_emotional_subtype,
)
from .utils import apply_mods, strip_outer_quotes

# Question / input types (string tags)
FACTUAL_PERSONAL = "FACTUAL_PERSONAL"
OPINION = "OPINION"
NEUTRAL_SOCIAL = "NEUTRAL_SOCIAL"
EMOTIONAL_PRESSURE = "EMOTIONAL_PRESSURE"
CHALLENGE = "CHALLENGE"
REPEAT_REDUNDANT = "REPEAT_REDUNDANT"
NONSENSE_RANDOM = "NONSENSE_RANDOM"
DEFAULT_MIXED = "DEFAULT_MIXED"

GREEN_TYPES: Set[str] = {FACTUAL_PERSONAL, OPINION, NEUTRAL_SOCIAL}

# Substrings that indicate last line was a stall (block echo on next turn)
STALL_MARKERS = (
    "need a second",
    "give me a second",
    "hold on",
    "hang on",
    "one second",
    "wait.",
    "wait—",
    "wait,",
    "slow down",
    "hold up",
)

SESSION_MODE_KEY = "response_mode"
LAST_STALL_CHECK_KEY = "last_response_stall_norm"


def classify_question_type(text: str) -> str:
    """Semantic classification from user text (repeat handled in resolve_response_mode)."""
    raw = (text or "").strip()
    if not raw:
        return NEUTRAL_SOCIAL

    low = raw.lower()
    # Chaotic / empty meaning
    alnum = sum(1 for c in low if c.isalnum())
    if len(low) > 2 and alnum < len(low) * 0.25:
        return NONSENSE_RANDOM
    if len(low) <= 2 and low.isalpha() and low not in {"hi", "ok", "no", "so"}:
        return NONSENSE_RANDOM

    # Challenge / hostility
    if any(
        p in low
        for p in (
            "you're wrong",
            "you are wrong",
            "youre wrong",
            "shut up",
            "who do you think you are",
            "how dare you",
            "bite me",
            "you suck",
            "you're lying",
            "you are lying",
            "fuck you",
            "watch yourself",
            "you don't know me",
        )
    ):
        return CHALLENGE
    if low in {"you're wrong.", "you are wrong.", "wrong."} or low.startswith("you're wrong") or low.startswith("you are wrong"):
        return CHALLENGE

    # Emotional pressure / intimacy
    if any(
        p in low
        for p in (
            "why don't you like",
            "why dont you like",
            "do you like me",
            "do you love me",
            "go on a date",
            "want to date",
            "will you marry",
            "kiss me",
            "are we together",
            "why are you mad at me",
            "why won't you",
            "why wont you",
            "am i ugly",
            "do you find me attractive",
            "think of me so far",
            "think about me so far",
            "do you want to go on a date",
            "why don't you want to go on a date",
            "why are you treating me",
            "why are you acting like this",
            "treating me this way",
        )
    ):
        return EMOTIONAL_PRESSURE

    # Opinion / evaluation
    if "attractive" in low and ("history" in low or "in history" in low or "ever" in low):
        return OPINION
    if any(
        p in low
        for p in (
            "what do you think",
            "your opinion",
            "your thoughts on",
            "thoughts on the",
            "thoughts on this",
            "what's your take",
            "whats your take",
            "how do you feel about",
            "do you prefer",
            "which do you like",
            "better than",
            "favorite ",
            "favourite ",
            " overrated",
            " underrated",
        )
    ):
        return OPINION

    if "can you help" in low or "could you help" in low:
        return NEUTRAL_SOCIAL

    # Factual-personal (possessions, biography-lite, concrete attributes)
    if any(
        p in low
        for p in (
            "do you own",
            "do you have a",
            "do you have any",
            "did you buy",
            "where did you get",
            "where'd you get",
            "whered you get",
            "are you from ",
            "what do you drive",
            "what phone",
            "jetski",
            "jet ski",
            "do you live",
            "have you ever been to",
            "have you ever ",
            "did you go to",
            "what's your job",
            "whats your job",
            "where do you work",
        )
    ):
        return FACTUAL_PERSONAL

    # Neutral social / rapport
    if any(
        p in low
        for p in (
            "nice to meet",
            "good morning",
            "good evening",
            "how are you",
            "how's it going",
            "hows it going",
            "how you doing",
            "what's up",
            "whats up",
            "you good",
            "everything good",
            "thank you",
            "thanks",
            "i appreciate",
            "respect your opinion",
            "fair point",
            "tell me more",
            "that's interesting",
            "thats interesting",
        )
    ):
        return NEUTRAL_SOCIAL
    if re.match(r"^(hi|hey|hello|yo|sup)\b", low) or low in {"hi", "hey", "hello", "yo", "sup"}:
        return NEUTRAL_SOCIAL

    return DEFAULT_MIXED


def resolve_response_mode(user_input: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gates downstream Crow Brain rewrite, stall language, and intent overlay.
    Uses session repeat_counts and speech-echo flag set by main.
    """
    ui = (user_input or "").strip()
    low = ui.lower()
    qt = classify_question_type(ui)
    rc = int(st.session_state.get("repeat_counts", {}).get(ui, 0))
    echo = bool(st.session_state.get("_speech_echo_this_turn", False))

    # Repeated benign social lines → mild repeat mode (not full hostility)
    if rc >= 2 and qt in {NEUTRAL_SOCIAL, DEFAULT_MIXED}:
        if echo or rc >= 2:
            if any(w in low for w in ("hello", "hi", "hey", "what's up", "whats up", "sup", "morning", "evening")):
                qt = REPEAT_REDUNDANT

    last_norm = (st.session_state.get(LAST_STALL_CHECK_KEY) or "").strip()
    block_stall = any(m in last_norm for m in STALL_MARKERS)

    mode: Dict[str, Any] = {
        "question_type": qt,
        "block_stall_language": block_stall,
        "allow_defensive_rewrite": qt in {CHALLENGE, EMOTIONAL_PRESSURE, REPEAT_REDUNDANT, NONSENSE_RANDOM},
        "allow_stall_language": qt in {CHALLENGE, EMOTIONAL_PRESSURE, NONSENSE_RANDOM, DEFAULT_MIXED},
        "use_intent_overlay": True,
        "skip_crow_brain_rewrite": False,
        "soft_echo_penalty": False,
        "apply_stat_relief": False,
        "emotional_intensity": qt in {CHALLENGE, EMOTIONAL_PRESSURE},
    }

    if qt in GREEN_TYPES:
        mode["allow_defensive_rewrite"] = False
        mode["allow_stall_language"] = False
        mode["use_intent_overlay"] = False
        mode["skip_crow_brain_rewrite"] = True
        mode["soft_echo_penalty"] = True
        mode["apply_stat_relief"] = True
    elif qt == REPEAT_REDUNDANT:
        mode["allow_defensive_rewrite"] = False
        mode["allow_stall_language"] = False
        mode["use_intent_overlay"] = False
        mode["skip_crow_brain_rewrite"] = True
        mode["soft_echo_penalty"] = True
    elif qt == CHALLENGE:
        mode["use_intent_overlay"] = False
        # build_response + menu intelligence already commit wording; do not replace with generic pools
        mode["skip_crow_brain_rewrite"] = True
    elif qt == EMOTIONAL_PRESSURE:
        mode["use_intent_overlay"] = False
        mode["skip_crow_brain_rewrite"] = True
    elif qt == NONSENSE_RANDOM:
        mode["skip_crow_brain_rewrite"] = False
        mode["use_intent_overlay"] = True

    if block_stall:
        mode["allow_stall_language"] = False

    # Clear, low-stakes questions — avoid confused/defensive rewrites
    if qt == DEFAULT_MIXED:
        if any(
            h in low
            for h in (
                "what time",
                "where is",
                "where's",
                "wheres ",
                "how much",
                "quick question",
                "which way",
                "can i ask",
                "could i ask",
            )
        ):
            mode["skip_crow_brain_rewrite"] = True
            mode["use_intent_overlay"] = False
            mode["apply_stat_relief"] = True
            mode["grounded_inquiry_relief"] = True
            mode["allow_stall_language"] = False
            mode["allow_defensive_rewrite"] = False

    recent_subs = get_recent_subtype_history()
    est = classify_emotional_subtype(ui)
    est = refine_emotional_subtype(ui, est, recent_subs, state)
    mode["emotional_subtype"] = est

    return mode


def record_last_response_for_stall_gate(verbal: str) -> None:
    inner = strip_outer_quotes(verbal).strip().lower()
    for ch in "…!?\"'“”":
        inner = inner.replace(ch, "")
    inner = " ".join(inner.split())
    st.session_state[LAST_STALL_CHECK_KEY] = inner


def apply_question_type_stat_relief(state: Dict[str, int], question_type: str, scale: float) -> None:
    """Reduce confusion/stress spiral on clear, grounded inputs."""
    if question_type in {FACTUAL_PERSONAL, OPINION}:
        apply_mods(state, {"confusion": -random.randint(10, 20)}, scale)
    if question_type in GREEN_TYPES | {REPEAT_REDUNDANT}:
        apply_mods(state, {"stress": -random.randint(2, 5)}, scale)
    if question_type == NEUTRAL_SOCIAL:
        apply_mods(
            state,
            {"stress": -random.randint(1, 4), "confusion": -random.randint(2, 6)},
            scale,
        )


def clamp_interest_ceiling(state: Dict[str, int], ceiling: int = 75) -> None:
    state["interest"] = min(int(state.get("interest", 50)), ceiling)


GENERIC_DEFLECTION_SNIPPETS = (
    "go on.",
    "say more.",
    "yeah?",
    "what?",
    "wait.",
    "anyway",
    "mhm.",
    "mm.",
    "huh?",
)


def is_specific(
    response: str,
    user_input: Optional[str] = None,
    emotional_context: bool = False,
) -> bool:
    """True if the line is plausibly grounded (not a pure generic deflection)."""
    if emotional_context:
        return True
    inner = strip_outer_quotes(response).strip().lower()
    inner_compact = " ".join(inner.split())
    if len(inner_compact) >= 36:
        return True
    if inner_compact in GENERIC_DEFLECTION_SNIPPETS or inner_compact in {"alright.", "okay.", "sure.", "fine."}:
        return False
    if any(inner_compact.startswith(g) and len(inner_compact) < 14 for g in ("wait", "hold on", "anyway")):
        return False
    if user_input:
        words = re.findall(r"[a-z0-9']{4,}", (user_input or "").lower())
        stop = {
            "that",
            "this",
            "what",
            "your",
            "with",
            "have",
            "just",
            "like",
            "about",
            "really",
            "something",
            "anything",
        }
        for w in words:
            if w in stop:
                continue
            if w in inner_compact:
                return True
    return len(inner_compact.split()) >= 5


def try_direct_free_text_answer(raw_text: str, personality: str, question_type: str) -> Optional[str]:
    """
    Short, grounded replies for free-text when mode skips Crow Brain rewrite.
    Returns inner line (no outer quotes) or None to fall through.
    """
    low = (raw_text or "").strip().lower()
    if not low:
        return None

    if "what time" in low:
        return random.choice(
            [
                "No idea—what's it say on your phone?",
                "Couldn't tell you.",
                "You're asking me?",
            ]
        )
    if "where" in low and any(x in low for x in ("bathroom", "restroom", "exit", "door")):
        return random.choice(["Over there, I think.", "Not sure—probably that way.", "I'd follow the signs."])

    if question_type not in GREEN_TYPES:
        return None

    factual_no = [
        "Nah.",
        "Nope.",
        "I don't.",
        "I wish.",
        "Not really.",
        "Why—do you?",
        "Random question, but no.",
    ]
    factual_yesish = [
        "Yeah, I do.",
        "Yeah.",
        "A little bit.",
        "Sometimes.",
        "Depends on the day.",
    ]
    if question_type == FACTUAL_PERSONAL:
        if any(k in low for k in ("jetski", "jet ski", "boat", "yacht")):
            return random.choice(factual_no + ["No lol.", "I wish I had that problem."])
        if "own" in low or "have a" in low or "got a" in low:
            if any(x in low for x in ("car", "bike", "house", "pet", "dog", "cat")):
                return random.choice(factual_yesish + factual_no)
            return random.choice(factual_no + factual_yesish)

    if any(p in low for p in ("what's up", "whats up", "wassup", "sup")):
        return random.choice(
            [
                "Long day.",
                "Not much—you?",
                "Same as usual. You?",
                "Eh, surviving. What's up with you?",
            ]
        )
    if "how are you" in low or "how you doing" in low or "you good" in low:
        return random.choice(
            [
                "I'm alright. You?",
                "Fine. You?",
                "Been better, been worse. You?",
                "Okay. What's up?",
            ]
        )
    if "thank" in low or "appreciate" in low or "respect your opinion" in low:
        blend = {
            "Shy": "Oh—thanks.",
            "Aggressive": "Yeah. Thanks.",
            "Empathetic": "That means a lot, actually.",
            "Analytical": "Noted. Thanks.",
            "Impulsive": "Aight, appreciate it.",
            "Confident": "Thanks. I can work with that.",
        }
        return blend.get(personality, "Thanks. I hear you.")
    if "tell me more" in low:
        return random.choice(
            [
                "Alright—what part?",
                "About what specifically?",
                "Sure. Where do you want to start?",
            ]
        )
    if question_type == OPINION and "think" in low:
        return random.choice(
            [
                "Honestly? Mixed feelings.",
                "Depends on the context.",
                "I could go either way.",
                "I'm not trying to die on that hill.",
            ]
        )
    return None


def filter_stall_from_pool_lines(lines: List[str]) -> List[str]:
    """Drop pure stall beats; keep lines where wait/hold-on carries a real follow-up."""
    out = []
    for line in lines:
        low = line.lower().strip()
        if "give me a second" in low or "need a second" in low:
            continue
        if "i'm trying to stay calm" in low:
            continue
        if len(line) <= 24 and low.rstrip(".!?") in ("wait", "hold on", "slow down", "hang on"):
            continue
        if low in ("wait.", "hold on.", "slow down.", "hang on.", "hold on—", "wait—"):
            continue
        out.append(line)
    return out if out else lines
