# -*- coding: utf-8 -*-
"""
Character archetype lens: biases bucket/tier/callback/finisher/physical without new dialogue.

All spoken lines remain from quarks/canon. Numeric weights only.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Mapping, Optional, Tuple

from canon_prompts import normalize_prompt_key
from scenario_layer import get_scenario_profile

ArchetypeId = str

ARCHETYPE_PROFILES: Dict[ArchetypeId, Dict[str, Any]] = {
    "playful": {
        "openness": 0.78,
        "confrontation_tendency": 0.32,
        "flirt_boldness": 0.72,
        "awkwardness_expression": 0.28,
        "patience": 0.62,
        "ego_sensitivity": 0.38,
        "severity_tendency": 0.22,
        "signature_nuclear_appetite": 0.55,
        "callback_sharpness": 0.72,
        "tier_bonus": (-3, 8, 3),
        "finisher_tier_bias": (-4, 5, 2),
        "finisher_tag_weights": {
            "final": 0.4,
            "dismissive": -0.35,
            "judgment": 0.25,
        },
    },
    "guarded": {
        "openness": 0.35,
        "confrontation_tendency": 0.42,
        "flirt_boldness": 0.25,
        "awkwardness_expression": 0.4,
        "patience": 0.45,
        "ego_sensitivity": 0.55,
        "severity_tendency": 0.38,
        "signature_nuclear_appetite": 0.35,
        "callback_sharpness": 1.22,
        "tier_bonus": (9, -1, -3),
        "finisher_tier_bias": (6, 1, -2),
        "finisher_tag_weights": {
            "boundary": 1.6,
            "persistence": 0.9,
            "cold": 0.6,
        },
    },
    "cocky": {
        "openness": 0.55,
        "confrontation_tendency": 0.72,
        "flirt_boldness": 0.58,
        "awkwardness_expression": 0.2,
        "patience": 0.4,
        "ego_sensitivity": 0.82,
        "severity_tendency": 0.58,
        "signature_nuclear_appetite": 0.78,
        "callback_sharpness": 1.08,
        "tier_bonus": (-7, 5, 12),
        "finisher_tier_bias": (-6, 4, 8),
        "finisher_tag_weights": {
            "disrespect": 2.0,
            "judgment": 1.4,
            "dismissive": 0.8,
        },
    },
    "awkward": {
        "openness": 0.48,
        "confrontation_tendency": 0.28,
        "flirt_boldness": 0.35,
        "awkwardness_expression": 0.78,
        "patience": 0.5,
        "ego_sensitivity": 0.48,
        "severity_tendency": 0.3,
        "signature_nuclear_appetite": 0.4,
        "callback_sharpness": 0.95,
        "tier_bonus": (10, 2, -2),
        "finisher_tier_bias": (5, 2, -1),
        "finisher_tag_weights": {
            "dismissive": 0.9,
            "cold": 0.5,
            "final": 0.35,
        },
    },
    "cold": {
        "openness": 0.22,
        "confrontation_tendency": 0.48,
        "flirt_boldness": 0.15,
        "awkwardness_expression": 0.25,
        "patience": 0.38,
        "ego_sensitivity": 0.35,
        "severity_tendency": 0.68,
        "signature_nuclear_appetite": 0.62,
        "callback_sharpness": 1.12,
        "tier_bonus": (5, -2, 9),
        "finisher_tier_bias": (3, -1, 10),
        "finisher_tag_weights": {
            "final": 1.1,
            "dismissive": 1.5,
            "cold": 1.4,
            "judgment": 0.9,
        },
    },
}

PERSONALITY_DEFAULT_ARCHETYPE: Dict[str, ArchetypeId] = {
    "Confident": "cocky",
    "Shy": "awkward",
    "Aggressive": "cocky",
    "Empathetic": "playful",
    "Analytical": "cold",
    "Impulsive": "playful",
}

ARCHETYPE_OPTIONS: Tuple[str, ...] = ("Auto", "playful", "guarded", "cocky", "awkward", "cold")

_N_WHAT_GIVES = normalize_prompt_key("What gives you the right?")
_N_WHO_THINK = normalize_prompt_key("Who do you think you are?")

ARCHETYPE_DEBUG_KEY = "_archetype_debug"

_PHYSICAL_SUFFIXES: Dict[ArchetypeId, Tuple[str, ...]] = {
    "playful": (
        "mouth twitching like they’re trying not to laugh",
        "looser posture, a little too comfortable",
    ),
    "guarded": (
        "subtle distance, arms folded without making a show of it",
        "short eye contact, chin tucked",
    ),
    "cocky": (
        "slow smirk, weight on the back foot",
        "lingering eye contact like they’re scoring you",
    ),
    "awkward": (
        "fidgets with a sleeve, looks past you for a beat",
        "uneven pause before answering, glance away",
    ),
    "cold": (
        "stillness, flat gaze",
        "detached posture, minimal movement",
    ),
}


def resolve_archetype_id(build_snapshot: Mapping[str, Any]) -> ArchetypeId:
    snap = dict(build_snapshot or {})
    explicit = snap.get("Archetype")
    if explicit and str(explicit).strip() and str(explicit) != "Auto":
        eid = str(explicit).strip().lower()
        if eid in ARCHETYPE_PROFILES:
            return eid
    pers = str(snap.get("Personality") or "Confident")
    return PERSONALITY_DEFAULT_ARCHETYPE.get(pers, "guarded")


def resolve_archetype_adjustments(
    prompt_ui: str,
    archetype_id: ArchetypeId,
    scenario_display: str,
    interaction_profile: Mapping[str, Any],
    callback_signals: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Returns tier bonuses, callback multiplier, finisher weights, physical pool, bucket hints.
    All additive with scenario/callback layers elsewhere.
    """
    aid = archetype_id if archetype_id in ARCHETYPE_PROFILES else "guarded"
    prof = dict(ARCHETYPE_PROFILES[aid])
    scen = get_scenario_profile(scenario_display)
    pn = normalize_prompt_key(prompt_ui)
    esc = int(interaction_profile.get("escalation_score", 0) or 0)
    disrespect = bool(interaction_profile.get("disrespect_flag"))

    tier_bonus: Tuple[int, int, int] = tuple(prof.get("tier_bonus", (0, 0, 0)))  # type: ignore[assignment]
    ftier_bias: Tuple[int, int, int] = tuple(prof.get("finisher_tier_bias", (0, 0, 0)))  # type: ignore[assignment]
    ftag_w = dict(prof.get("finisher_tag_weights") or {})

    cb_mult = float(prof.get("callback_sharpness", 1.0))
    if aid == "awkward" and bool(scen.get("is_public")):
        cb_mult *= 1.08
        tier_bonus = (tier_bonus[0] + 2, tier_bonus[1], tier_bonus[2])
    if aid == "cocky" and (disrespect or pn == _N_WHAT_GIVES or pn == _N_WHO_THINK):
        tier_bonus = (tier_bonus[0] - 2, tier_bonus[1] + 1, tier_bonus[2] + 3)
        ftag_w = {**ftag_w, "disrespect": ftag_w.get("disrespect", 0) + 0.8}
    if aid == "guarded" and esc >= 6:
        tier_bonus = (tier_bonus[0] + 2, tier_bonus[1], tier_bonus[2])
    if int(callback_signals.get("theme_streak", 0) or 0) >= 3 and aid == "playful":
        tier_bonus = (tier_bonus[0] - 1, tier_bonus[1] + 2, tier_bonus[2])

    physical_suffixes = _PHYSICAL_SUFFIXES.get(aid, ("",))

    return {
        "archetype_id": aid,
        "profile": prof,
        "tier_bonus": tier_bonus,
        "finisher_tier_bias": ftier_bias,
        "finisher_tag_weights": ftag_w,
        "callback_probability_mult": cb_mult,
        "physical_suffixes": physical_suffixes,
        "severity_tendency": float(prof.get("severity_tendency", 0.5)),
        "openness": float(prof.get("openness", 0.5)),
    }


def apply_archetype_bucket_nudge(
    bucket: str,
    adj: Mapping[str, Any],
    state: Mapping[str, Any],
    prompt_ui: str,
    interaction_profile: Mapping[str, Any],
    scenario_display: str,
) -> Tuple[str, bool]:
    """
    Returns (new_bucket, influenced_flag). Light probabilistic nudges.
    """
    aid = str(adj.get("archetype_id", "guarded"))
    sev = float(adj.get("severity_tendency", 0.5))
    open_ = float(adj.get("openness", 0.5))
    trust = int(state.get("trust", 40) or 0)
    pn = normalize_prompt_key(prompt_ui)
    disrespect = bool(interaction_profile.get("disrespect_flag"))
    scen_pub = bool(get_scenario_profile(scenario_display).get("is_public"))

    b = bucket
    influenced = False

    if aid == "cold":
        if b == "positive" and random.random() < 0.1 + 0.12 * sev:
            b, influenced = "neutral", True
        elif b == "neutral" and random.random() < 0.06 + 0.1 * sev:
            b, influenced = "negative", True

    if aid == "playful":
        if b == "severe" and int(state.get("happiness", 50) or 0) > 52 and random.random() < 0.14:
            b, influenced = "negative", True
        elif b == "negative" and random.random() < 0.09 * open_:
            b, influenced = "neutral", True

    if aid == "guarded":
        if b == "positive" and random.random() < 0.2:
            b, influenced = "neutral", True
        if b == "neutral" and trust < 34 and random.random() < 0.14:
            b, influenced = "negative", True

    if aid == "cocky":
        if b in ("positive", "neutral") and (disrespect or pn == _N_WHAT_GIVES or pn == _N_WHO_THINK):
            if random.random() < 0.16 + 0.08 * sev:
                b, influenced = "negative", True

    if aid == "awkward" and scen_pub and b == "positive" and random.random() < 0.11:
        b, influenced = "neutral", True

    return b, influenced


def append_archetype_physical_flavor(physical: str, adj: Mapping[str, Any]) -> str:
    pool = adj.get("physical_suffixes") or ()
    if not pool:
        return physical
    flavor = random.choice(tuple(pool))
    if not str(flavor).strip():
        return physical
    base = (physical or "").strip()
    if not base:
        return str(flavor)
    if str(flavor).lower() in base.lower():
        return physical
    return f"{base} — {flavor}"


def merge_tier_triples(
    *parts: Optional[Tuple[int, int, int]],
) -> Optional[Tuple[int, int, int]]:
    out = [0, 0, 0]
    any_ = False
    for p in parts:
        if not p:
            continue
        any_ = True
        out[0] += int(p[0])
        out[1] += int(p[1])
        out[2] += int(p[2])
    if not any_:
        return None
    return (out[0], out[1], out[2])
