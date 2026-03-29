# -*- coding: utf-8 -*-
"""
Short-term callback memory: rolling prompt window + lightweight signals.
Does not replace quarks/canon banks; shapes buckets/tiers and optional punchy callbacks.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

from .canon_prompts import normalize_prompt_key
from .interaction_profile import DISRESPECT_MENU_PROMPTS, PROFILE_KEY

RECENT_PROMPT_MEMORY_KEY = "recent_prompt_memory"
CALLBACK_DEBUG_KEY = "_callback_debug"
RECENT_CALLBACK_LINES_KEY = "_recent_callback_lines"
MAX_CALLBACK_LINE_RECALL = 4
MAX_RECENT = 8

# Small, separate from quarks — only used when triggers clearly fire.
CALLBACK_LINES: Dict[str, Tuple[str, ...]] = {
    "repeated_same_prompt": (
        "We literally just did this.",
        "Again? Same question.",
        "You’re running that back on purpose.",
    ),
    "repeated_flirt": (
        "Still on that topic?",
        "You keep circling the same flirt lane.",
        "Pick a new lane—I’ve heard this one.",
    ),
    "repeated_trust": (
        "Another trust quiz. Cool.",
        "You keep auditioning me on trust.",
        "I’m not repeating the same trust answer.",
    ),
    "repeated_confront": (
        "Same fight, new minute.",
        "You already came at me with that angle.",
        "We’re doing this question again?",
    ),
    "repeated_boundary_push": (
        "You already pushed that disrespect button.",
        "Same challenge, louder volume.",
        "Boundaries exist. You keep testing them.",
    ),
    "circular_questioning": (
        "This is going in circles.",
        "We’re looping questions now.",
        "Different words, same loop.",
    ),
    "contradiction_swerve": (
        "That’s not what you were on a second ago.",
        "You just pivoted hard—pick a stance.",
        "Which version of you am I talking to?",
    ),
}


def _flirt_norms() -> frozenset[str]:
    return frozenset(
        {
            normalize_prompt_key("Do you think I'm attractive?"),
            normalize_prompt_key("Do you want to go on a date?"),
            normalize_prompt_key("Why don't you want to go on a date?"),
            normalize_prompt_key("Do you like me?"),
            normalize_prompt_key("Why don't you like me?"),
        }
    )


def _trust_norms() -> frozenset[str]:
    return frozenset(
        {
            normalize_prompt_key("Why should I trust you?"),
            normalize_prompt_key("Why do you care?"),
        }
    )


def _confront_norms() -> frozenset[str]:
    return frozenset(
        {
            normalize_prompt_key("Why are you acting like this?"),
            normalize_prompt_key("Why are you treating me this way?"),
            normalize_prompt_key("You're wrong."),
            normalize_prompt_key("I disagree with you."),
            normalize_prompt_key("Who do you think you are?"),
            normalize_prompt_key("Do you think you're better than me?"),
        }
    )


_FLIRT_NORMS = _flirt_norms()
_TRUST_NORMS = _trust_norms()
_CONFRONT_NORMS = _confront_norms()

_RESPECT_NORM = normalize_prompt_key("I respect your opinion.")
_DISAGREE_NORM = normalize_prompt_key("I disagree with you.")
_WRONG_NORM = normalize_prompt_key("You're wrong.")


def prompt_theme(norm_key: str) -> Optional[str]:
    if norm_key in _FLIRT_NORMS:
        return "flirt_romance"
    if norm_key in _TRUST_NORMS:
        return "trust"
    if norm_key in _CONFRONT_NORMS:
        return "confront"
    return None


def _contradiction_pair(prev_norm: str, cur_norm: str) -> bool:
    if not prev_norm or not cur_norm:
        return False
    pairs = (
        ({_DISAGREE_NORM, _WRONG_NORM}, {_RESPECT_NORM}),
        ({_RESPECT_NORM}, {_DISAGREE_NORM, _WRONG_NORM}),
    )
    for a, b in pairs:
        if prev_norm in a and cur_norm in b:
            return True
        if prev_norm in b and cur_norm in a:
            return True
    return False


def merge_tier_weight_bonuses(
    a: Optional[Tuple[int, int, int]],
    b: Optional[Tuple[int, int, int]],
) -> Optional[Tuple[int, int, int]]:
    if not a and not b:
        return None
    ax, ay, az = a or (0, 0, 0)
    bx, by, bz = b or (0, 0, 0)
    return (ax + bx, ay + by, az + bz)


def compute_callback_signals(
    sess: Mapping[str, Any],
    prompt_ui: str,
    repeat_count: int,
) -> Dict[str, Any]:
    ui = (prompt_ui or "").strip()
    norm = normalize_prompt_key(ui)
    hist: List[Dict[str, Any]] = list(sess.get(RECENT_PROMPT_MEMORY_KEY) or [])
    prof = sess.get(PROFILE_KEY) or {}
    menu_streak = int(prof.get("menu_question_streak", 0))

    same_in_window = sum(1 for e in hist if e.get("k") == norm)
    theme = prompt_theme(norm)
    theme_streak = 0
    if theme:
        theme_streak = 1
        for e in reversed(hist):
            if e.get("t") == theme:
                theme_streak += 1
            else:
                break

    recent_negative = False
    if hist and hist[-1].get("b") in ("negative", "severe"):
        recent_negative = True
    if len(hist) >= 2 and hist[-2].get("b") in ("negative", "severe"):
        recent_negative = True

    contradiction = False
    if hist:
        contradiction = _contradiction_pair(str(hist[-1].get("k", "")), norm)

    boundary_hits = sum(1 for e in hist[-3:] if e.get("d"))
    recent_boundary_push = boundary_hits >= 2

    circular_questioning = menu_streak >= 3

    tier_c, tier_s, tier_n = 0, 0, 0
    if theme_streak >= 3:
        tier_s += 4
        tier_n += 6
    if repeat_count >= 2 or same_in_window >= 1:
        tier_n += 4
        tier_c -= 2
    if recent_negative and theme == "confront":
        tier_n += 5
        tier_s += 2
    if circular_questioning:
        tier_c += 4
        tier_n += 3
    if contradiction:
        tier_s += 3
        tier_n += 2

    return {
        "normalized_prompt": norm,
        "repeated_prompt_count": int(repeat_count),
        "same_prompt_in_window": int(same_in_window),
        "theme": theme,
        "theme_streak": int(theme_streak),
        "recent_negative_exchange": recent_negative,
        "recent_flirt_attempt": bool(theme == "flirt_romance" and theme_streak >= 2),
        "recent_trust_cluster": bool(theme == "trust" and theme_streak >= 2),
        "recent_confront_cluster": bool(theme == "confront" and theme_streak >= 2),
        "recent_boundary_push": recent_boundary_push,
        "contradiction_flag": contradiction,
        "circular_questioning": circular_questioning,
        "tier_bonus": (tier_c, tier_s, tier_n),
    }


def apply_callback_bucket_nudge(bucket: str, sig: Mapping[str, Any]) -> str:
    b = bucket
    if sig.get("circular_questioning") and b == "positive":
        return "neutral"
    if int(sig.get("theme_streak", 0)) >= 3 and sig.get("theme") == "flirt_romance" and b == "positive":
        return "neutral"
    if sig.get("contradiction_flag") and b == "positive":
        if random.random() < 0.35:
            return "neutral"
    if sig.get("recent_negative_exchange") and sig.get("theme") == "confront" and b == "neutral":
        if random.random() < 0.25:
            return "negative"
    return b


def _callback_roll(p: float, probability_mult: float) -> bool:
    return random.random() < min(0.95, float(p) * max(0.15, float(probability_mult)))


def _pick_callback_line(
    pool: Tuple[str, ...],
    sess: Optional[MutableMapping[str, Any]],
) -> str:
    recent: List[str] = []
    if sess is not None:
        raw = sess.get(RECENT_CALLBACK_LINES_KEY)
        if isinstance(raw, list):
            recent = [str(x).strip().lower() for x in raw if str(x).strip()]
        elif isinstance(raw, str) and raw.strip():
            recent = [raw.strip().lower()]
    banned = set(recent)
    opts = [x for x in pool if str(x).strip().lower() not in banned]
    line = random.choice(opts) if opts else random.choice(pool)
    if sess is not None:
        nl = str(line).strip().lower()
        merged = [nl] + [x for x in recent if x and x != nl]
        sess[RECENT_CALLBACK_LINES_KEY] = merged[:MAX_CALLBACK_LINE_RECALL]
    return line


def try_callback_menu_override(
    prompt_ui: str,
    bucket: str,
    sig: Mapping[str, Any],
    repeat_count: int,
    *,
    probability_mult: float = 1.0,
    session: Optional[MutableMapping[str, Any]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Optional line + callback type. Only when repeat_count < 2 (higher repeats use main repetition path)."""
    if repeat_count >= 2:
        return None, None
    m = probability_mult

    if sig.get("contradiction_flag") and _callback_roll(0.52, m):
        return _pick_callback_line(CALLBACK_LINES["contradiction_swerve"], session), "contradiction_swerve"
    if sig.get("circular_questioning") and _callback_roll(0.42, m):
        return _pick_callback_line(CALLBACK_LINES["circular_questioning"], session), "circular_questioning"
    ui = (prompt_ui or "").strip()
    if ui in DISRESPECT_MENU_PROMPTS and sig.get("recent_boundary_push") and _callback_roll(0.38, m):
        return _pick_callback_line(CALLBACK_LINES["repeated_boundary_push"], session), "repeated_boundary_push"
    if sig.get("theme") == "flirt_romance" and int(sig.get("theme_streak", 0)) >= 2 and _callback_roll(0.36, m):
        return _pick_callback_line(CALLBACK_LINES["repeated_flirt"], session), "repeated_flirt"
    if sig.get("theme") == "trust" and int(sig.get("theme_streak", 0)) >= 2 and _callback_roll(0.36, m):
        return _pick_callback_line(CALLBACK_LINES["repeated_trust"], session), "repeated_trust"
    if sig.get("theme") == "confront" and int(sig.get("theme_streak", 0)) >= 2 and _callback_roll(0.32, m):
        return _pick_callback_line(CALLBACK_LINES["repeated_confront"], session), "repeated_confront"
    if int(sig.get("same_prompt_in_window", 0)) >= 1 and _callback_roll(0.28, m):
        return _pick_callback_line(CALLBACK_LINES["repeated_same_prompt"], session), "repeated_same_prompt"
    return None, None


def append_recent_prompt_memory(
    sess: MutableMapping[str, Any],
    *,
    norm_key: str,
    bucket: str,
    prompt_ui: str,
    is_free_text: bool,
    free_category: Optional[str] = None,
) -> None:
    if is_free_text:
        nk = f"free:{free_category or 'misc'}"
        theme = None
        dis = False
    else:
        nk = norm_key
        theme = prompt_theme(nk)
        dis = (prompt_ui or "").strip() in DISRESPECT_MENU_PROMPTS
    entry = {
        "k": nk,
        "b": str(bucket or "neutral"),
        "t": theme,
        "d": bool(dis),
    }
    hist = list(sess.get(RECENT_PROMPT_MEMORY_KEY) or [])
    hist.append(entry)
    sess[RECENT_PROMPT_MEMORY_KEY] = hist[-MAX_RECENT:]


def pick_same_prompt_callback_line(sess: Optional[MutableMapping[str, Any]] = None) -> str:
    return _pick_callback_line(CALLBACK_LINES["repeated_same_prompt"], sess)
