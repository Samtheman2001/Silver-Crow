"""
Personality DNA + identity locking.

This module is allowed to touch Streamlit session_state because DNA is stored per-session.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Optional

import streamlit as st

from .config import BASE_STATE
from .utils import (
    _dna_clamp_trait,
    _stable_seed_from_text,
    apply_mods,
    apply_ripple_effects,
    clamp,
    clamp01,
    quote,
    strip_outer_quotes,
)


def generate_personality_dna(
    personality: str,
    background: str,
    physical_state: str,
    mood: str,
    character_name: str,
    jitter_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fixed identity anchor (does not change after creation).
    Values are 0–100. A little jitter adds replayability without chaos.
    """
    base: Dict[str, Any] = {
        "openness": 55,
        "agreeableness": 50,
        "emotional_reactivity": 50,
        "trust_baseline": 45,
        "patience": 55,
        "assertiveness": 55,
        "humor_style": "dry",  # dry / playful / none
        "communication_style": "direct",  # direct / soft / evasive
        "bias": "slightly_guarded",  # subtle default lean
    }

    # Personality anchors
    if personality == "Confident":
        base.update(
            {
                "assertiveness": 72,
                "patience": 62,
                "trust_baseline": 48,
                "agreeableness": 50,
                "emotional_reactivity": 46,
                "communication_style": "direct",
            }
        )
    elif personality == "Shy":
        base.update(
            {
                "assertiveness": 34,
                "patience": 60,
                "trust_baseline": 34,
                "agreeableness": 60,
                "emotional_reactivity": 62,
                "communication_style": "soft",
                "bias": "slightly_guarded",
            }
        )
    elif personality == "Aggressive":
        base.update(
            {
                "assertiveness": 82,
                "patience": 30,
                "trust_baseline": 30,
                "agreeableness": 22,
                "emotional_reactivity": 70,
                "communication_style": "direct",
                "bias": "slightly_intense",
            }
        )
    elif personality == "Empathetic":
        base.update(
            {
                "assertiveness": 52,
                "patience": 74,
                "trust_baseline": 58,
                "agreeableness": 80,
                "emotional_reactivity": 58,
                "communication_style": "soft",
                "bias": "slightly_warm",
            }
        )
    elif personality == "Analytical":
        base.update(
            {
                "assertiveness": 58,
                "patience": 68,
                "trust_baseline": 42,
                "agreeableness": 46,
                "emotional_reactivity": 40,
                "communication_style": "direct",
                "openness": 70,
                "bias": "slightly_skeptical",
            }
        )
    elif personality == "Impulsive":
        base.update(
            {
                "assertiveness": 66,
                "patience": 40,
                "trust_baseline": 44,
                "agreeableness": 44,
                "emotional_reactivity": 76,
                "communication_style": "direct",
                "humor_style": "playful",
                "bias": "slightly_intense",
            }
        )

    # Background nudges (subtle)
    if background == "Military Veteran":
        base["patience"] -= 4
        base["assertiveness"] += 6
        base["communication_style"] = "direct"
        base["trust_baseline"] -= 3
    elif background == "Artist":
        base["openness"] += 8
        base["emotional_reactivity"] += 4
        base["humor_style"] = "playful" if base["humor_style"] != "none" else "playful"
    elif background == "Office Worker":
        base["patience"] += 3
        base["communication_style"] = "evasive" if base["communication_style"] == "direct" else base["communication_style"]
    elif background == "Entrepreneur":
        base["assertiveness"] += 4
        base["openness"] += 3
    elif background == "Athlete":
        base["assertiveness"] += 3
        base["agreeableness"] -= 2

    # Mood/physical tweak (tiny; identity stays mostly personality)
    if mood == "Irritated":
        base["patience"] -= 6
        base["emotional_reactivity"] += 4
    elif mood == "Calm":
        base["emotional_reactivity"] -= 5
        base["patience"] += 4
    elif mood == "Anxious":
        base["trust_baseline"] -= 4
        base["communication_style"] = "soft" if base["communication_style"] != "direct" else base["communication_style"]
    elif mood == "Excited":
        base["openness"] += 4
        base["emotional_reactivity"] += 3

    if physical_state in {"Tired", "Sick"}:
        base["patience"] -= 5
        base["agreeableness"] -= 2
    if physical_state == "Relaxed":
        base["patience"] += 3

    # Controlled per-session jitter
    seed_text = f"{jitter_seed or 0}|{character_name}|{personality}|{background}|{physical_state}|{mood}"
    rng = random.Random(_stable_seed_from_text(seed_text))
    jitter = lambda spread: rng.randint(-spread, spread)
    for k in ("openness", "agreeableness", "emotional_reactivity", "trust_baseline", "patience", "assertiveness"):
        base[k] = _dna_clamp_trait(base[k] + jitter(6))

    # Derived quirks (rare behaviors; felt not seen)
    base["quirks"] = {
        "follow_up_q": clamp01((base["openness"] - 45) / 120) * 0.20,
        "deflect": clamp01((60 - base["trust_baseline"]) / 110) * 0.18
        + (0.06 if base["communication_style"] == "evasive" else 0.0),
        "challenge": clamp01((base["assertiveness"] - 45) / 110) * 0.20,
        "reframe": clamp01((base["openness"] - 50) / 110) * 0.18 + (0.04 if personality == "Analytical" else 0.0),
    }
    return base


def get_character_dna() -> Dict[str, Any]:
    dna = st.session_state.get("character_dna")
    if isinstance(dna, dict) and dna:
        return dna
    return {}


def init_identity_state() -> Dict[str, Any]:
    return {
        "last_quirk_turn": -999,
        "last_quirk_kind": "",
    }


def dna_scaled_mods(mods: Dict[str, int], dna: Dict[str, Any], kind: Optional[str] = None, free_text_category: Optional[str] = None):
    """Scale stat deltas by DNA tendencies (subtle; anchors identity)."""
    if not mods or not isinstance(mods, dict) or not dna:
        return mods

    agree = int(dna.get("agreeableness", 50))
    react = int(dna.get("emotional_reactivity", 50))
    trust_base = int(dna.get("trust_baseline", 45))
    patience = int(dna.get("patience", 55))
    assertive = int(dna.get("assertiveness", 55))

    out: Dict[str, int] = {}
    for k, v in mods.items():
        if k not in BASE_STATE:
            continue
        dv = float(v)
        if k == "trust":
            if dv > 0:
                dv *= (0.82 + agree / 260.0) * (0.85 + trust_base / 260.0)
            else:
                dv *= (1.00 + (55 - trust_base) / 220.0)
        elif k == "anger":
            if dv > 0:
                dv *= (0.88 + react / 220.0) * (0.88 + (60 - patience) / 260.0)
            else:
                dv *= (0.85 + agree / 260.0) * (0.90 + patience / 300.0)
        elif k == "stress":
            if dv > 0:
                dv *= (0.90 + react / 260.0)
            else:
                dv *= (0.90 + patience / 320.0)
        elif k == "confidence":
            if dv > 0:
                dv *= (0.90 + assertive / 260.0)
            else:
                dv *= (0.92 + (70 - assertive) / 320.0)
        elif k == "interest":
            dv *= (0.92 + int(dna.get("openness", 55)) / 320.0)
        elif k == "fear":
            if dv > 0:
                dv *= (0.92 + react / 280.0)
            else:
                dv *= (0.95 + patience / 340.0)
        elif k == "happiness":
            if dv < 0 and agree >= 70:
                dv *= 0.92

        if kind == "say" and free_text_category and str(free_text_category).startswith(("aggressive_",)):
            if k in {"anger", "stress"} and dv > 0:
                dv *= (0.92 + (60 - patience) / 260.0)
            if k == "trust" and dv < 0 and trust_base < 45:
                dv *= 1.06

        out[k] = int(round(dv))
    return out


def apply_mods_with_identity(
    state: Dict[str, int],
    mods: Dict[str, int],
    scale: float = 1.0,
    kind: Optional[str] = None,
    free_text_category: Optional[str] = None,
    sassy_comeback: bool = False,
):
    """Apply identity-anchored deltas + matching ripple effects."""
    dna = get_character_dna()
    mods_scaled = dna_scaled_mods(mods, dna, kind=kind, free_text_category=free_text_category)
    apply_mods(state, mods_scaled, scale)
    apply_ripple_effects(state, mods_scaled, scale, sassy_comeback=sassy_comeback)
    state["interest"] = min(int(state.get("interest", 50)), 75)
    return mods_scaled


def maybe_apply_personal_quirk(verbal, brain, state, user_input=None, free_text_category=None):
    """Rare style-consistent quirk layer: follow-up / deflect / challenge / reframe."""
    if not isinstance(verbal, str) or not verbal:
        return verbal
    if free_text_category and str(free_text_category).startswith(("aggressive_", "absurd", "apology")):
        return verbal
    from .first_impression import first_impression_verbal_locked, preserve_scripted_menu_response

    att0 = (brain or {}).get("attitude", "guarded")
    t0 = int(st.session_state.get("turns", 0))
    if user_input and (
        first_impression_verbal_locked(user_input, t0, state, att0)
        or preserve_scripted_menu_response(user_input, free_text_category)
    ):
        return verbal
    if (st.session_state.get("response_mode") or {}).get("skip_crow_brain_rewrite"):
        return verbal

    dna = get_character_dna()
    if not dna:
        return verbal

    turns = int(st.session_state.get("turns", 0))
    ident = st.session_state.get("identity_state") or init_identity_state()
    if turns - int(ident.get("last_quirk_turn", -999)) <= 2:
        return verbal

    att = (brain or {}).get("attitude", "guarded")
    traj = (brain or {}).get("interaction_trajectory", "") or (st.session_state.get("conversation_memory") or {}).get(
        "interaction_trajectory", "stable_neutral"
    )
    inner = strip_outer_quotes(verbal)
    if len(inner) > 120:
        return verbal

    q = dna.get("quirks") or {}
    damp = 0.65 if traj in {"disengaging"} else 1.0
    if att in {"hostile"}:
        damp = 0.35

    candidates = []
    if random.random() < float(q.get("follow_up_q", 0.0)) * damp and att in {"curious", "engaged", "warm"}:
        candidates.append(("follow_up_q", random.choice(["What do you mean?", "Why?", "Like—what’s the point?", "So what are you actually asking?"])))
    if random.random() < float(q.get("deflect", 0.0)) * damp and att in {"guarded", "anxious"}:
        candidates.append(("deflect", random.choice(["Anyway. What’s your angle?", "Let’s not do the personal stuff yet.", "Mm. What are you getting at?"])))
    if random.random() < float(q.get("challenge", 0.0)) * damp and att in {"guarded", "irritated", "curious"}:
        candidates.append(("challenge", random.choice(["Say it straight.", "Be specific.", "Don’t dance around it."])))
    if random.random() < float(q.get("reframe", 0.0)) * damp and att in {"curious", "engaged", "guarded"}:
        candidates.append(("reframe", random.choice(["So you’re basically saying you want a reaction.", "Sounds like you’re testing me.", "Feels like you want me to pick a side."])))

    if not candidates:
        return verbal

    kind2, addon = random.choice(candidates)
    ident["last_quirk_turn"] = turns
    ident["last_quirk_kind"] = kind2
    st.session_state.identity_state = ident

    combo = f"{inner} {addon}"
    if len(combo) > 140:
        return verbal
    return quote(combo)

