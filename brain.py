"""
Crow Brain: attitude/tone/physical state + verbal filtering.
"""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Tuple

import streamlit as st

from .config import (
    ACTION_OPTIONS,
    BACKGROUNDS,
    BASE_STATE,
    PERSONALITIES,
    PHYSICAL_STATES,
    SAY_OPTIONS,
    SCENARIOS,
    STARTING_MOODS,
)
from .behavior_gate import filter_stall_from_pool_lines, is_specific
from .custom_label_pools import preferred_tone_for, preferred_vibe_for
from .first_impression import first_impression_verbal_locked, preserve_scripted_menu_response
from .response_intent import pick_overlay_line_and_nudge
from .memory import derive_read_on_you, init_memory_state, relationship_trend
from .personality import get_character_dna, maybe_apply_personal_quirk
from .utils import (
    apply_mods,
    clamp,
    quote,
    strip_outer_quotes,
)


def choose_bucket(state, personality=None):
    """Choose response bucket; personality can bias toward warmer or colder."""
    if state["anger"] > 72 or state["stress"] > 72:
        base = "severe" if state["anger"] > 84 else "negative"
        if personality == "Empathetic" and state["anger"] < 85:
            return "negative"  # empathetic holds back from severe longer
        if personality in {"Aggressive", "Impulsive"}:
            return "severe" if state["anger"] > 70 else base
        return base
    if state["trust"] > 72 or state["happiness"] > 65:
        if personality == "Shy" and state["trust"] < 80:
            return "neutral"  # shy slower to show positive
        if personality == "Empathetic":
            return "positive"
        return "positive"
    if personality == "Shy":
        return "neutral"
    if personality in {"Aggressive", "Impulsive"} and state["trust"] < 45:
        return "negative"
    return "neutral"


def infer_tone(state):
    """Random-flavored labels via custom_label_pools; dropdown SAY demo uses fixed labels in interaction_response."""
    if state["anger"] > 70 and state["trust"] < 30:
        return preferred_tone_for("hostile")
    if state["stress"] > 70 or state["fear"] > 70:
        return preferred_tone_for("tense")
    if state["trust"] > 70 and state["happiness"] > 60:
        return preferred_tone_for("warm")
    if state["confusion"] > 72:
        return preferred_tone_for("uncertain")
    if state["interest"] > 70:
        return preferred_tone_for("engaged")
    return preferred_tone_for("neutral")


def infer_vibe(state):
    if state["anger"] > 86 and state["stress"] > 80:
        return preferred_vibe_for("hostile")
    if state["anger"] > 78 and state["stress"] > 72:
        return preferred_vibe_for("about to become violent")
    if state["trust"] > 75 and state["happiness"] > 65:
        return preferred_vibe_for("comfortable and open")
    if state["fear"] > 70:
        return preferred_vibe_for("uneasy and on edge")
    if state["confusion"] > 76:
        return preferred_vibe_for("awkward and uncertain")
    if state["interest"] > 72:
        return preferred_vibe_for("locked in and curious")
    if state["stress"] < 30 and state["anger"] < 30:
        return preferred_vibe_for("calm")
    return preferred_vibe_for("neutral")


def infer_physical_response(state):
    """Short physical beats only (demo readability; flavor layers may still append)."""
    if state["anger"] > 70:
        return random.choice(("pulls back slightly", "goes still", "looks away"))
    if state["fear"] > 70:
        return "looks away"
    if state["stress"] > 70:
        return "pauses"
    if state["trust"] > 74 and state["happiness"] > 60:
        return "looks at you"
    if state["confusion"] > 72:
        return random.choice(("pauses", "looks at you"))
    if state["interest"] > 72:
        return "looks at you"
    if state["happiness"] > 70:
        return "looks at you"
    if state["stress"] < 30 and state["anger"] < 30:
        return random.choice(("looks at you", "pauses"))
    return random.choice(("looks at you", "pauses", "goes still"))


def _brain_pick(pool, seed):
    if not pool:
        return ""
    idx = 0 if len(pool) == 1 else abs(int(seed)) % len(pool)
    return pool[idx]


def _crow_brain_pick_variant(attitude, key, options, seed):
    if not options:
        return ""
    idx = abs(int(seed)) % len(options)
    if random.random() < 0.22 and len(options) > 1:
        idx = (idx + 1) % len(options)
    last = st.session_state.get("crow_brain_last_variant", {})
    last_att = st.session_state.get("crow_brain_last_attitude")
    last_idx = None
    if isinstance(last, dict):
        last_idx = last.get(f"{attitude}:{key}")
    if last_att == attitude and last_idx == idx and len(options) > 1:
        idx = (idx + 1) % len(options)
    if not isinstance(last, dict):
        last = {}
    last[f"{attitude}:{key}"] = idx
    st.session_state.crow_brain_last_variant = last
    st.session_state.crow_brain_last_attitude = attitude
    return options[idx]


def _crow_seed_from_state(state, extra=0):
    return (
        int(state.get("trust", 0))
        + int(state.get("stress", 0)) * 2
        + int(state.get("anger", 0)) * 3
        + int(state.get("happiness", 0))
        - int(state.get("confidence", 0))
        + int(state.get("confusion", 0)) * 4
        + int(state.get("interest", 0))
        + int(extra)
    )


def init_human_variation_state():
    return {
        "linger_edge": 0.0,
        "linger_soft": 0.0,
        "last_hesitation_turn": -999,
        "spike_cooldown_until": -999,
        "last_spike_kind": "",
    }


def _bump_linger_from_attitude(attitude, mem, state):
    hv = st.session_state.get("human_variation") or init_human_variation_state()
    hv["linger_edge"] = max(0.0, float(hv.get("linger_edge", 0.0)) * 0.92)
    hv["linger_soft"] = max(0.0, float(hv.get("linger_soft", 0.0)) * 0.92)
    if attitude in {"hostile", "irritated"}:
        hv["linger_edge"] = min(1.0, hv["linger_edge"] + 0.22)
    elif attitude in {"anxious", "guarded"}:
        hv["linger_edge"] = min(1.0, hv["linger_edge"] + 0.10)
    if attitude in {"warm", "flirty"}:
        hv["linger_soft"] = min(1.0, hv["linger_soft"] + 0.18)
    elif attitude in {"amused", "curious"}:
        hv["linger_soft"] = min(1.0, hv["linger_soft"] + 0.08)
    st.session_state.human_variation = hv
    return hv


def _maybe_add_hesitation(line, attitude, brain, mem, state):
    if not line or not isinstance(line, str):
        return line
    mode = st.session_state.get("response_mode") or {}
    if mode.get("allow_stall_language") is False:
        return line
    if "..." in line or "…" in line:
        return line
    turns = int(st.session_state.get("turns", 0))
    hv = st.session_state.get("human_variation") or init_human_variation_state()
    if turns - int(hv.get("last_hesitation_turn", -999)) <= 1:
        return line
    awkward = int(mem.get("awkward_score", 0))
    pressure = int(mem.get("pressure_score", 0))
    traj = (brain or {}).get("interaction_trajectory", "") or mem.get("interaction_trajectory", "stable_neutral")
    base_p = 0.03
    if int(state.get("confidence", 50) or 50) >= 62:
        base_p *= 0.35
    if attitude in {"awkward", "confused"}:
        base_p += 0.10
    if attitude in {"guarded", "anxious"}:
        base_p += 0.06
    if awkward >= 60:
        base_p += 0.05
    if traj in {"suspicious", "disengaging"}:
        base_p += 0.03
    if pressure >= 70 and attitude in {"guarded", "irritated"}:
        base_p += 0.03
    base_p = min(0.18, base_p)
    if random.random() > base_p:
        return line
    hesitations = {
        "awkward": ["Uh…", "Okay…", "I mean—"],
        "confused": ["Okay…", "I mean—"],
        "guarded": ["Yeah…", "Okay…", "Mhm…"],
        "anxious": ["Okay…", "Uh…"],
        "irritated": ["Yeah, no.", "Okay—", "Nah."],
        "hostile": ["No.", "Yeah, no.", "Stop."],
        "warm": ["Yeah…", "Okay…"],
        "flirty": ["Mhm…", "Okay…"],
        "amused": ["Okay…", "Yeah…"],
        "curious": ["Okay…", "Yeah…"],
        "engaged": ["Okay—", "Yeah—"],
        "dismissive": ["Yeah.", "Okay."],
    }
    prefix = random.choice(hesitations.get(attitude, ["Okay…"]))
    hv["last_hesitation_turn"] = turns
    st.session_state.human_variation = hv
    inner = strip_outer_quotes(line)
    return quote(f"{prefix} {inner}")


def _micro_variation(line, attitude, brain, mem, state):
    if not line or not isinstance(line, str):
        return line
    inner = strip_outer_quotes(line)
    if not inner:
        return line
    hv = st.session_state.get("human_variation") or init_human_variation_state()
    edge = float(hv.get("linger_edge", 0.0))
    soft = float(hv.get("linger_soft", 0.0))
    if random.random() < 0.08:
        inner = inner.replace("...", "…")
    if random.random() < 0.06 and inner.endswith("."):
        inner = inner[:-1]
    if edge > 0.45 and attitude in {"guarded", "irritated", "hostile"} and random.random() < 0.12:
        inner = inner.replace("Alright—", "Alright.").replace("Okay—", "Okay.")
        inner = inner.replace("I’m", "I'm")
    if soft > 0.45 and attitude in {"warm", "curious", "engaged"} and random.random() < 0.10:
        inner = inner.replace("Yeah.", "Yeah.").replace("Okay.", "Okay.")
        if inner.startswith("No."):
            inner = inner.replace("No.", "No, but—", 1)
    if random.random() < 0.07:
        swaps = [
            ("I don’t know if I buy that", "I’m not sure I buy that"),
            ("Slow down.", "Chill."),
            ("Back up a little.", "Ease up."),
            ("Be straight with me.", "Just be straight."),
            ("Keep it respectful.", "Keep it respectful with me."),
        ]
        for a, b in swaps:
            if a in inner and random.random() < 0.45:
                inner = inner.replace(a, b)
                break
    # DNA style consistency
    dna = get_character_dna() or {}
    comm = dna.get("communication_style", "direct")
    humor = dna.get("humor_style", "dry")
    if comm == "direct":
        if inner.startswith("Okay.") and random.random() < 0.20:
            inner = inner.replace("Okay.", "Alright.", 1)
        if inner.startswith("Okay—") and random.random() < 0.20:
            inner = inner.replace("Okay—", "Alright—", 1)
    elif comm == "soft":
        if inner.startswith("No.") and random.random() < 0.12:
            inner = inner.replace("No.", "I mean—no.", 1)
        if "Stop." in inner and random.random() < 0.08:
            inner = inner.replace("Stop.", "Uh—hold up.", 1)
    elif comm == "evasive":
        if inner.startswith("Yeah.") and random.random() < 0.20:
            inner = inner.replace("Yeah.", "Mm-hm.", 1)
        if inner.startswith("Okay.") and random.random() < 0.15:
            inner = inner.replace("Okay.", "Alright…", 1)
    if humor == "dry" and inner.startswith("Alright") and random.random() < 0.10:
        inner = inner.replace("Alright", "Sure", 1)
    return quote(inner)


def _maybe_spike_moment(attitude, brain, mem, state):
    if st.session_state.get("_fi_lock_verbal"):
        return None
    turns = int(st.session_state.get("turns", 0))
    hv = st.session_state.get("human_variation") or init_human_variation_state()
    if turns < int(hv.get("spike_cooldown_until", -999)):
        return None
    traj = (brain or {}).get("interaction_trajectory", "") or mem.get("interaction_trajectory", "stable_neutral")
    p = 0.06
    if traj in {"stable_neutral", "slightly_interested"}:
        p = 0.08
    if traj in {"losing_patience", "growing_tension", "suspicious"}:
        p = 0.05
    if random.random() > p:
        return None
    kinds = []
    if traj in {"losing_patience", "growing_tension"}:
        kinds += ["sharp", "dismissive"]
    elif traj == "suspicious":
        kinds += ["introspective", "sharp"]
    elif traj in {"building_trust", "warming_up", "emotionally_open"}:
        kinds += ["warm", "honest"]
    else:
        kinds += ["honest", "sharp", "warm"]
    spike_kind = random.choice(kinds) if kinds else "honest"
    hv["spike_cooldown_until"] = turns + 4 + random.randint(0, 3)
    hv["last_spike_kind"] = spike_kind
    st.session_state.human_variation = hv
    pools = {
        "honest": [
            "I’m not gonna lie—this is weird.",
            "I’m being real: I don’t know what you want.",
            "Honestly? I’m not sure I trust the vibe yet.",
        ],
        "sharp": [
            "That’s not doing what you think it’s doing.",
            "You’re not getting the reaction you want.",
            "You’re trying a little too hard.",
        ],
        "warm": ["Okay… that was actually nice.", "I can respect that.", "Alright. That helped."],
        "dismissive": ["Yeah. I’m not doing this.", "Nope. Next.", "Alright. Whatever."],
        "introspective": [
            "I’m trying to stay open, but it’s hard right now.",
            "Part of me wants to relax. Part of me doesn’t.",
            "I’m not sure what to make of you yet.",
        ],
    }
    if traj in {"disengaging"} and spike_kind in {"warm"}:
        spike_kind = "dismissive"
    if traj in {"emotionally_open"} and spike_kind in {"dismissive"}:
        spike_kind = "honest"
    return quote(random.choice(pools.get(spike_kind, pools["honest"])))


def generate_crow_brain_state(stats):
    """
    Crow Brain (required): derive internal processing from emotional stats.

    Input: stats dict with keys:
      trust, stress, anger, fear, happiness, confusion, interest, confidence

    Output dict:
      internal_thought (str)
      attitude (str)
      tone (str)
      physical_reaction (str)
    """
    trust = int(stats.get("trust", 0))
    stress = int(stats.get("stress", 0))
    anger = int(stats.get("anger", 0))
    fear = int(stats.get("fear", 0))
    happiness = int(stats.get("happiness", 0))
    confusion = int(stats.get("confusion", 0))
    interest = int(stats.get("interest", 0))
    confidence = int(stats.get("confidence", 0))

    mem = st.session_state.get("conversation_memory") or init_memory_state()
    user_read = derive_read_on_you(mem)
    trend = relationship_trend(mem)
    trajectory = mem.get("interaction_trajectory", "stable_neutral")
    traj_strength = int(mem.get("trajectory_strength", 25))
    pressure = mem.get("pressure_score", 0)
    disrespect = mem.get("disrespect_score", 0)
    kindness = mem.get("kindness_score", 0)
    flirt = mem.get("flirtation_score", 0)
    awkward_mem = mem.get("awkward_score", 0)
    honesty = mem.get("honesty_score", 50)
    inconsistent = mem.get("inconsistency_score", 0)

    # Attitude MUST be derived logically from stats (no randomness)
    # Priority order is intentional: safety/hostility > confusion > warmth > engagement > dismissal
    if anger > 78 and trust < 35:
        attitude = "hostile"
    elif fear > 72 and stress > 66:
        attitude = "anxious"
    elif confusion > 86:
        attitude = "confused"
    elif confusion > 74 and stress > 58:
        attitude = "awkward"
    elif anger > 62 or (anger > 52 and trust < 38):
        attitude = "irritated"
    elif (pressure >= 65 or disrespect >= 60) and trust < 72:
        attitude = "irritated" if anger >= 55 else "guarded"
    elif (awkward_mem >= 65 or inconsistent >= 60 or honesty <= 22) and anger < 75:
        attitude = "confused" if confusion >= 70 else "awkward"
    elif trust > 76 and happiness > 58 and interest > 66 and confidence > 45 and anger < 56 and stress < 64:
        attitude = "flirty" if flirt >= 25 or user_read == "charming" else "warm"
    elif trust > 70 and happiness > 52 and interest > 52 and anger < 58:
        attitude = "warm"
    elif interest > 76 and trust >= 28:
        attitude = "engaged"
    elif interest > 62 and trust >= 24:
        attitude = "curious"
    elif trust < 30 and interest < 34:
        attitude = "dismissive"
    elif happiness > 62 and confidence > 58 and anger < 55 and stress < 60:
        attitude = "amused"
    else:
        attitude = "guarded"

    # Memory-based softening/hardening (deterministic)
    if attitude in {"guarded", "awkward"} and kindness >= 70 and disrespect < 45 and pressure < 55 and honesty >= 35:
        attitude = "warm" if trust >= 55 and happiness >= 45 else "curious"
    if attitude in {"warm", "flirty"} and (disrespect >= 55 or pressure >= 65 or honesty <= 22 or inconsistent >= 60):
        attitude = "guarded"
    if attitude == "curious" and pressure >= 70:
        attitude = "guarded"

    # DNA identity resistance: restrict how "open" the character can get.
    dna = get_character_dna() or {}
    trust_base = int(dna.get("trust_baseline", 45))
    agree = int(dna.get("agreeableness", 50))
    patience = int(dna.get("patience", 55))
    react = int(dna.get("emotional_reactivity", 50))

    if attitude in {"warm", "flirty", "amused"}:
        # A low-trust character needs more proof to go genuinely warm/flirty.
        min_trust_open = int(clamp(trust_base + 45 + (55 - patience) * 0.25, 78, 96))
        if trust < min_trust_open:
            attitude = "curious" if agree >= 55 else "guarded"
    if attitude == "engaged" and agree < 35:
        attitude = "curious"
    if attitude in {"warm", "flirty", "amused"} and patience < 40 and (disrespect >= 45 or pressure >= 60):
        attitude = "irritated" if anger >= 55 else "guarded"
    if attitude in {"warm", "amused"} and react >= 70 and pressure >= 60:
        attitude = "guarded"

    # Controlled variation seed: stats + a tiny time component
    turn = int(st.session_state.get("turns", 0))
    step = int(st.session_state.get("crow_brain_step", 0)) + 1
    st.session_state.crow_brain_step = step
    seed = (trust + stress * 2 + anger * 3 + happiness - confidence + confusion * 4 + interest) + (turn * 7) + step

    # 3–5 variations per attitude: internal thought, physical reaction, tone phrasing
    thought_variants = {
        "warm": [
            "That was actually kind of sweet.",
            "Okay… that was nice.",
            "I can feel this getting easier.",
            "I don't hate that.",
        ],
        "flirty": [
            "That was smoother than I expected.",
            "Okay. They have a little game.",
            "I might be into this.",
            "Careful. This could get fun.",
        ],
        "amused": [
            "They're trying. It's kind of funny.",
            "That didn't land, but I respect the attempt.",
            "This is entertaining in a weird way.",
            "I’m not mad. I’m watching.",
        ],
        "curious": [
            "Why are they saying it like that?",
            "I want the real intent here.",
            "Okay… what's the angle?",
            "I want to see where this goes.",
        ],
        "engaged": [
            "This is getting interesting.",
            "Okay—now I’m locked in.",
            "That might actually matter.",
            "Wait. Keep going.",
        ],
        "guarded": [
            "Trust is thin. Don't give them anything free.",
            "I'm listening, but I'm not relaxing yet.",
            "I'm not sure what they want from me.",
            "I need to stay careful here.",
        ],
        "dismissive": [
            "This isn't worth my energy.",
            "Okay. Next.",
            "They're loud. That's about it.",
            "I'm not buying it.",
        ],
        "awkward": [
            "That was awkward. Reset the vibe.",
            "Okay… that came out weird.",
            "I don't know what they're doing.",
            "This is getting uncomfortable.",
        ],
        "confused": [
            "That didn't make sense. Rephrase.",
            "I'm not tracking. Try again.",
            "I genuinely don't understand that.",
            "That didn't parse.",
        ],
        "anxious": [
            "I feel cornered. Keep it controlled.",
            "This is too tense. Don't react wrong.",
            "Breathe. Stay composed.",
            "I need more space.",
        ],
        "irritated": [
            "They're pushing too hard.",
            "I'm getting annoyed.",
            "Why are they acting entitled right now?",
            "I'm running out of patience.",
        ],
        "hostile": [
            "I don't trust this at all.",
            "No. I'm not letting that slide.",
            "They're crossing a line.",
            "I want this to end.",
        ],
    }

    # Memory-based thought nudges (short, clean)
    if pressure >= 65 and attitude in {"guarded", "irritated"}:
        thought_variants[attitude] = ["They keep pushing."] + thought_variants.get(attitude, [])
    if mem.get("last_turn_was_apology") and disrespect >= 45:
        thought_variants["guarded"] = ["They’re trying to recover. I’m not sold yet."] + thought_variants.get("guarded", [])
    if honesty <= 22 or inconsistent >= 60:
        thought_variants["guarded"] = ["This feels inconsistent."] + thought_variants.get("guarded", [])
        thought_variants["curious"] = ["This feels inconsistent."] + thought_variants.get("curious", [])
    if awkward_mem >= 70 and attitude in {"awkward", "confused"}:
        thought_variants[attitude] = (["They’re awkward, but not malicious."] if disrespect < 45 else ["This is getting weird."]) + thought_variants.get(attitude, [])
    if kindness >= 70 and attitude in {"guarded", "curious"}:
        thought_variants[attitude] = ["Okay… maybe they mean well."] + thought_variants.get(attitude, [])

    # Trajectory-based internal thoughts (short; bias the same attitude)
    traj_thoughts = {
        "losing_patience": ["They’re wearing on me.", "They keep doing this."],
        "growing_tension": ["This is starting to feel intentional.", "I’m not liking this direction."],
        "building_trust": ["They’re improving… slowly.", "This feels different than before."],
        "warming_up": ["I’m starting to like them more.", "Okay… this is better."],
        "suspicious": ["I don’t fully trust this shift.", "Something’s off."],
        "disengaging": ["I’m checking out.", "I don’t want to do this anymore."],
        "slightly_interested": ["This might be fun.", "I’m curious about them."],
        "emotionally_open": ["I actually feel safe right now.", "This is… easy."],
        "stable_neutral": [],
    }
    if trajectory in traj_thoughts and traj_thoughts[trajectory]:
        thought_variants[attitude] = traj_thoughts[trajectory] + thought_variants.get(attitude, [])

    physical_variants = {
        "warm": [
            "softens their expression and holds a comfortable gaze",
            "relaxes a little and keeps eye contact",
            "smiles faintly like they're letting you in",
        ],
        "flirty": [
            "smirks and holds eye contact a second too long",
            "raises an eyebrow like they like the tension",
            "tilts their head, amused by you",
        ],
        "amused": [
            "smirks like they already clocked you",
            "exhales through the nose, trying not to laugh",
            "watches you with a lazy, entertained look",
        ],
        "curious": [
            "tilts head and watches you carefully",
            "leans in slightly, waiting for the point",
            "studies you like you're giving clues",
        ],
        "engaged": [
            "leans in slightly, fully focused",
            "keeps steady eye contact, listening hard",
            "nods once, like they're tracking every word",
        ],
        "guarded": [
            "keeps a measured distance, eyes flicking up and away",
            "holds still, giving you very little",
            "watches you carefully without relaxing",
        ],
        "dismissive": [
            "shrugs slightly and lets the silence do the work",
            "glances away like this isn't worth it",
            "barely nods, expression flat",
        ],
        "awkward": [
            "pauses mid-expression, then gives a tight half-smile",
            "looks away for a second, then back",
            "shifts weight like they want a reset",
        ],
        "confused": [
            "blinks once and goes still—processing",
            "stares for a beat like they're recalculating",
            "squints slightly, trying to understand",
        ],
        "anxious": [
            "holds eye contact, then glances away like checking exits",
            "stiffens slightly and watches your hands",
            "keeps their shoulders tight, guarded",
        ],
        "irritated": [
            "brows knit, lips press thin—done being patient",
            "leans back with visible irritation",
            "gives you a look that says 'seriously?'",
        ],
        "hostile": [
            "stares you down, jaw tight, shoulders squared",
            "locks their jaw and doesn't blink",
            "leans back like they're ready to end it",
        ],
    }

    if pressure >= 70 and "guarded" in physical_variants:
        physical_variants["guarded"] = ["crosses their arms and watches you carefully"] + physical_variants["guarded"]
    if honesty <= 22 or inconsistent >= 60:
        physical_variants["guarded"] = ["narrows their eyes like they’re checking for a lie"] + physical_variants.get("guarded", [])

    tone_variants = {
        "warm": ["warm", "warm", "warm"],
        "flirty": ["warm", "engaged", "warm"],
        "amused": ["engaged", "engaged", "neutral"],
        "curious": ["engaged", "uncertain", "engaged"],
        "engaged": ["engaged", "engaged", "uncertain"],
        "guarded": ["uncertain", "neutral", "uncertain"],
        "dismissive": ["neutral", "neutral", "uncertain"],
        "awkward": ["uncertain", "uncertain", "neutral"],
        "confused": ["uncertain", "uncertain", "tense"],
        "anxious": ["tense", "tense", "uncertain"],
        "irritated": ["tense", "tense", "hostile"],
        "hostile": ["hostile", "hostile", "tense"],
    }

    thought = _crow_brain_pick_variant(attitude, "thought", thought_variants.get(attitude, []), seed)
    physical = _crow_brain_pick_variant(attitude, "physical", physical_variants.get(attitude, []), seed + 13)
    tone = _crow_brain_pick_variant(attitude, "tone", tone_variants.get(attitude, ["neutral"]), seed + 29)

    # Trajectory biases tone subtly (residue / inertia)
    if trajectory in {"losing_patience", "growing_tension"} and tone == "warm":
        tone = "uncertain"
    if trajectory == "suspicious" and tone in {"warm", "neutral"}:
        tone = "uncertain"
    if trajectory == "disengaging" and tone in {"engaged", "warm"}:
        tone = "neutral"

    # Emotional linger (residue) + controlled "masking" (small thought/speech mismatch possibility)
    hv = _bump_linger_from_attitude(attitude, mem, stats)
    linger_edge = float(hv.get("linger_edge", 0.0))
    linger_soft = float(hv.get("linger_soft", 0.0))

    internal_conflict = False
    # Low-probability masking: annoyed but polite; interested but guarded.
    if attitude in {"irritated", "hostile"} and kindness >= 55 and disrespect < 70 and random.random() < (0.06 + (0.04 if honesty >= 45 else 0.0)):
        internal_conflict = True
    if attitude in {"guarded"} and interest >= 65 and happiness >= 45 and random.random() < 0.07:
        internal_conflict = True

    return {
        "internal_thought": thought,
        "attitude": attitude,
        "tone": tone,
        "physical_reaction": physical,
        "user_read": user_read,
        "relationship_trend": trend,
        "interaction_trajectory": trajectory,
        "linger_edge": linger_edge,
        "linger_soft": linger_soft,
        "internal_conflict": internal_conflict,
    }


def apply_trajectory_phase_nudge_to_brain(brain: dict) -> dict:
    """Light tone/physical nudge from hidden trajectory phase (session `_trajectory_adj`)."""
    adj = st.session_state.get("_trajectory_adj") or {}
    tid = str(adj.get("trajectory_id") or "")
    phase = str(adj.get("trajectory_phase") or "")
    if not tid or not phase:
        return brain
    b = dict(brain)
    tone = b.get("tone", "neutral")

    if tid == "fragile":
        if phase in ("shaken", "withdrawn") and tone == "warm" and random.random() < 0.26:
            b["tone"] = "uncertain"
        if phase == "withdrawn" and tone in ("engaged", "warm") and random.random() < 0.20:
            b["tone"] = "neutral"
        if phase in ("shaken", "withdrawn") and random.random() < 0.10:
            b["physical_reaction"] = random.choice(
                [
                    "pulls back slightly, like the topic grazed a nerve",
                    "looks away, jaw tight like they're holding it together",
                ]
            )
    elif tid == "volatile":
        if phase == "escalating" and tone in ("neutral", "warm", "uncertain") and random.random() < 0.22:
            b["tone"] = "tense"
        if phase in ("irritated", "escalating") and random.random() < 0.09:
            b["physical_reaction"] = random.choice(
                [
                    "rolls tension through their shoulders, watching you sharp",
                    "exhales sharp through the nose, waiting for your next move",
                ]
            )
    elif tid == "guarded_then_open":
        if phase == "guarded" and tone == "warm" and random.random() < 0.18:
            b["tone"] = "neutral"
        if phase == "open" and tone == "uncertain" and random.random() < 0.14:
            b["tone"] = "engaged"
    elif tid == "playful_then_cutting":
        if phase in ("edgy", "cutting") and tone == "warm" and random.random() < 0.24:
            b["tone"] = "neutral"
        if phase == "cutting" and random.random() < 0.10:
            b["physical_reaction"] = random.choice(
                [
                    "smirks without warmth—done entertaining you",
                    "tilts their head with a flat, evaluating look",
                ]
            )
    elif tid == "slow_warmup":
        if phase == "reserved" and tone in ("engaged", "warm") and random.random() < 0.14:
            b["tone"] = "neutral"
        if phase == "comfortable" and tone == "neutral" and random.random() < 0.12:
            b["tone"] = "warm"

    return b


def crow_brain_interpret(state, user_input=None, kind=None, free_text_category=None, repeat_count=0):
    brain_base = generate_crow_brain_state(state)
    thought = brain_base["internal_thought"]
    attitude = brain_base["attitude"]
    tone = brain_base["tone"]
    physical = brain_base["physical_reaction"]
    vibe = infer_vibe(state)
    user_read = brain_base.get("user_read", "")
    trend = brain_base.get("relationship_trend", "")
    trajectory = brain_base.get("interaction_trajectory", "")

    ui_norm = (user_input or "").strip().lower()
    has_question = "?" in ui_norm
    has_insult_hint = any(x in ui_norm for x in ("shut up", "you suck", "loser", "idiot", "dumb", "fuck"))
    if has_question and attitude in {"guarded", "awkward", "confused", "anxious"}:
        thought = "Why are they asking me that like it’s easy?"
    if has_insult_hint and attitude in {"warm", "curious"}:
        thought = "That was disrespectful. I’m recalculating."

    return apply_trajectory_phase_nudge_to_brain(
        {
            "internal_thought": thought,
            "attitude": attitude,
            "tone": tone,
            "physical_reaction": physical,
            "vibe": vibe,
            "user_read": user_read,
            "relationship_trend": trend,
            "interaction_trajectory": trajectory,
        }
    )


def _normalize_verbal_for_compare(verbal):
    s = strip_outer_quotes(verbal)
    s = (s or "").strip().lower()
    s = s.replace("—", "-")
    for ch in [".", "!", "?", ",", "…", "“", "”", "'", '"']:
        s = s.replace(ch, "")
    return " ".join(s.split())


def crow_brain_rewrite_verbal(
    verbal,
    brain,
    state,
    user_input=None,
    free_text_category=None,
    turns_before_reply=None,
) -> Tuple[str, bool]:
    """
    Returns (rewritten_verbal, use_intent_overlay).
    Overlay runs only for generic pool rewrites — not substantive bucket lines or greeting/check-in picks.
    """
    if not isinstance(verbal, str):
        return verbal, False
    if free_text_category and str(free_text_category).startswith(("aggressive_", "absurd", "apology")):
        return verbal, False
    mem = st.session_state.get("conversation_memory") or init_memory_state()
    hv = st.session_state.get("human_variation") or init_human_variation_state()
    att = (brain or {}).get("attitude", "") or "guarded"
    raw_early = (verbal or "").strip()
    tbr = int(st.session_state.get("turns", 0)) if turns_before_reply is None else int(turns_before_reply)
    if raw_early and first_impression_verbal_locked(user_input, tbr, state, att):
        return verbal, False
    if raw_early and preserve_scripted_menu_response(user_input, free_text_category):
        return verbal, False
    mode_rw = st.session_state.get("response_mode") or {}
    if mode_rw.get("skip_crow_brain_rewrite"):
        return verbal, False
    ui_menu = (user_input or "").strip()
    if raw_early and ui_menu in SAY_OPTIONS:
        return verbal, False
    # Do-actions (Smile, Step closer, …): short social acks must not route through filler rewrite
    # ("Okay." / "Yeah.") or they get replaced with skeptical menu lines like "I don't buy that yet."
    if raw_early and ui_menu in ACTION_OPTIONS:
        return verbal, False
    thought = (brain or {}).get("internal_thought", "") or ""
    user_read = (brain or {}).get("user_read", "") or derive_read_on_you(mem)
    trajectory = (brain or {}).get("interaction_trajectory", "") or mem.get("interaction_trajectory", "stable_neutral")
    internal_conflict = bool((brain or {}).get("internal_conflict", False))
    linger_edge = float((brain or {}).get("linger_edge", hv.get("linger_edge", 0.0)))
    linger_soft = float((brain or {}).get("linger_soft", hv.get("linger_soft", 0.0)))
    raw = (verbal or "").strip()
    base_norm = _normalize_verbal_for_compare(raw) if raw else ""
    ui = (user_input or "").strip()
    ui_norm = ui.lower()

    def _finish(line):
        sp = _maybe_spike_moment(att, brain, mem, state)
        out = line
        if sp and isinstance(sp, str):
            if random.random() < 0.55:
                out = sp
            elif random.random() < 0.25:
                combo = f"{strip_outer_quotes(out)} {strip_outer_quotes(sp)}"
                if len(combo) <= 130:
                    out = quote(combo)
        out = _maybe_add_hesitation(out, att, brain, mem, state)
        out = _micro_variation(out, att, brain, mem, state)
        out = maybe_apply_personal_quirk(out, brain, state, user_input=user_input, free_text_category=free_text_category)
        return out

    overly_warm_markers = ("nice to meet", "glad", "thanks", "appreciate", "of course", "absolutely")
    overly_soft = any(m in base_norm for m in overly_warm_markers)
    needs_sharpen = att in {"hostile", "irritated", "dismissive"} and overly_soft
    needs_soften = att in {"warm", "flirty"} and any(m in base_norm for m in ("mind your business", "shut up", "watch it"))
    filler = base_norm in {"ok", "okay", "sure", "alright", "fine", "yeah", "noted", "i hear you"} or base_norm.startswith("okay")

    seed = _crow_seed_from_state(state, extra=len(base_norm) + len(ui_norm))

    if not (needs_sharpen or needs_soften or filler):
        if att in {"guarded", "anxious"} and base_norm in {"yeah", "alright"}:
            return _finish(quote(_brain_pick(["Yeah.", "Alright.", "What."], seed))), False
        return _finish(verbal), False
    is_greeting = any(x in ui_norm for x in ("hello", "hey", "hi", "nice to meet", "what's up", "whats up", "wassup"))
    is_checkin = any(x in ui_norm for x in ("how are you", "how you doing", "are you good", "you good", "everything good"))
    is_question = "?" in ui or ui_norm.startswith(("why", "what", "how", "do you", "are you"))

    pools = {
        "warm": ["Yeah—alright. I can work with that.", "Okay. You seem fine so far.", "Alright. I’m listening.", "Yeah… that’s fair."],
        "flirty": ["Okay. That was smoother than I expected.", "Alright—don’t get confident now.", "Yeah. You’re kinda bold.", "Mhm. Keep that energy."],
        "curious": ["Okay. What do you mean by that?", "Alright—say more.", "Which part?", "Yeah? Where are you going with this?"],
        "engaged": ["Wait—run that back.", "Okay. Now you have my attention.", "Yeah—keep going.", "Alright. Be specific."],
        "amused": ["Okay. I see you.", "Yeah… you’re funny.", "Mhm. That almost landed.", "Alright. You’re entertaining."],
        "guarded": ["Yeah… we’ll see.", "Okay. I don’t buy that yet.", "Alright. You’re hard to read.", "Mhm. Say it straight."],
        "dismissive": ["Yeah. Okay.", "Alright—cool.", "Sure. Whatever.", "Okay. Next."],
        "awkward": ["Uh… okay. That was kinda awkward.", "Alright. That came out weird.", "Okay… I don’t know what to do with that.", "Yeah. Try again."],
        "confused": ["I’m not tracking—rephrase it.", "Wait. What are you saying?", "Okay… I’m lost. Start over.", "That didn’t make sense to me."],
        "anxious": ["Okay… slow down.", "Yeah—don’t rush me.", "Alright. Give me a second.", "Okay. I’m trying to stay calm here."],
        "irritated": ["Yeah. Don’t do that.", "Okay—watch your tone.", "Alright. You’re pushing it.", "Yeah… no. Try again."],
        "hostile": ["No. Try again.", "Yeah—don’t talk to me like that.", "Alright. Keep it respectful or don’t speak.", "Nope. We’re not doing this."],
    }

    if mode_rw.get("allow_stall_language") is False or mode_rw.get("block_stall_language"):
        for pk, pl in list(pools.items()):
            pools[pk] = filter_stall_from_pool_lines(list(pl))

    if linger_edge >= 0.55:
        pools["guarded"] = ["Mm-hm.", "Yeah…", "Okay."] + pools["guarded"]
        pools["irritated"] = ["Enough.", "Stop.", "Yeah, no."] + pools["irritated"]
    if linger_soft >= 0.55:
        pools["warm"] = ["Alright. I hear you.", "Yeah. That’s fair."] + pools["warm"]
        pools["curious"] = ["Okay… go on.", "Yeah? Tell me."] + pools["curious"]

    if trajectory in {"losing_patience", "growing_tension"}:
        pools["guarded"] = ["Yeah… no.", "Stop pushing.", "Back up."] + pools["guarded"]
        pools["irritated"] = ["You’re wearing on me.", "I’m not doing this loop.", "Enough."] + pools["irritated"]
    elif trajectory == "suspicious":
        pools["guarded"] = ["Something’s off.", "I don’t buy that.", "Why are you saying it like that?"] + pools["guarded"]
        pools["curious"] = ["What’s the real story?", "Be straight with me.", "Which one is it?"] + pools["curious"]
    elif trajectory == "disengaging":
        pools["dismissive"] = ["Yeah. Cool.", "Alright.", "Sure."] + pools["dismissive"]
        pools["guarded"] = ["Mm-hm.", "Okay.", "Yeah."] + pools["guarded"]
    elif trajectory in {"building_trust", "warming_up", "emotionally_open"}:
        pools["warm"] = ["Okay. That’s better.", "Yeah. Keep it like that.", "Alright. I hear you."] + pools["warm"]
        pools["curious"] = ["Okay—say more.", "Yeah? Go on.", "Alright. I’m listening."] + pools["curious"]
    elif trajectory == "slightly_interested":
        pools["curious"] = ["Okay… interesting.", "Yeah? That’s kinda funny.", "Alright."] + pools["curious"]
        pools["amused"] = ["Mhm. Keep going.", "Okay. I see you.", "Yeah…"] + pools["amused"]

    if user_read == "pushy":
        pools["guarded"] = ["You’re coming on strong.", "Slow down.", "Back up a little."] + pools["guarded"]
        pools["irritated"] = ["Stop pushing.", "Relax.", "You’re doing too much."] + pools["irritated"]
    elif user_read == "sincere":
        pools["guarded"] = ["Okay… I hear you.", "Alright. That’s fair.", "Yeah. I can respect that."] + pools["guarded"]
        pools["warm"] = ["Yeah. I like that.", "Okay. That’s actually nice.", "Alright. Keep it real."] + pools["warm"]
    elif user_read == "inconsistent":
        pools["guarded"] = ["Something’s not adding up.", "Yeah… I don’t know.", "You’re switching up on me."] + pools["guarded"]
        pools["curious"] = ["What’s the real story?", "Pick a lane.", "Which one is it?"] + pools["curious"]
    elif user_read == "charming":
        pools["warm"] = ["Yeah. You’ve got a little charm.", "Okay. That works.", "Alright—don’t waste it."] + pools["warm"]
        pools["flirty"] = ["Mhm. You’re kinda dangerous.", "Okay… you’re bold.", "Yeah. I see you."] + pools["flirty"]
    elif user_read == "awkward":
        pools["awkward"] = ["Okay… breathe.", "We can reset.", "That was… a lot."] + pools["awkward"]
    elif user_read == "annoying":
        pools["irritated"] = ["Nope.", "Try again.", "You’re not helping yourself."] + pools["irritated"]
        pools["hostile"] = ["We’re not doing this.", "Watch your mouth.", "Keep it respectful."] + pools["hostile"]

    if att in {"guarded", "hostile"} and ("don't trust" in thought.lower() or "disrespect" in thought.lower()):
        pools[att] = ["Yeah… no.", "Try that again.", "Watch yourself.", "Keep it respectful."] + pools[att]
    if att in {"awkward", "confused"} and ("rephrase" in thought.lower() or "didn't make sense" in thought.lower()):
        pools[att] = ["Okay—what do you mean?", "Rephrase that.", "I’m not following."] + pools[att]

    if is_greeting:
        if att in {"hostile", "irritated"}:
            return _finish(quote(_brain_pick(["Yeah.", "What.", "Say what you need to say."], seed))), False
        if att in {"guarded", "anxious"}:
            return _finish(quote(_brain_pick(["Yeah… hey.", "Hey.", "What’s up."], seed))), False
        if att in {"warm", "flirty", "amused"}:
            return _finish(quote(_brain_pick(["Hey.", "Hey—what’s up?", "Yeah, hey."], seed))), False
    if is_checkin:
        if att in {"hostile", "irritated"}:
            return _finish(quote(_brain_pick(["Why do you care?", "I’m fine. Move on.", "Not great. Now what?"], seed))), False
        if att in {"guarded", "anxious"}:
            return _finish(quote(_brain_pick(["I’m alright. You?", "I’ve been better.", "I’m fine. What’s up?"], seed))), False
        if att in {"warm", "flirty", "amused"}:
            return _finish(quote(_brain_pick(["I’m good. You?", "Not bad—what’s up?", "I’m alright. Talk to me."], seed))), False

    if is_question and att in {"curious", "engaged"}:
        pick_att = "curious" if internal_conflict and att == "guarded" else att
        return _finish(quote(_brain_pick(pools[pick_att], seed))), True
    if is_question and att in {"guarded", "anxious"}:
        return _finish(
            quote(_brain_pick(["Why are you asking?", "Say it plain.", "What are you actually asking?"], seed))
        ), True

    effective_att = att
    if internal_conflict and att in {"irritated", "hostile"}:
        effective_att = "guarded"
    elif internal_conflict and att == "guarded" and linger_soft >= 0.45:
        effective_att = "curious"

    return _finish(quote(_brain_pick(pools.get(effective_att, pools["guarded"]), seed))), True


def crow_brain_apply_to_verbal(
    verbal,
    brain,
    state,
    user_input=None,
    free_text_category=None,
    turns_before_reply=None,
    *,
    preserve_verbatim: bool = False,
):
    if not isinstance(verbal, str):
        return verbal
    if preserve_verbatim:
        return verbal
    verbal, use_intent_overlay = crow_brain_rewrite_verbal(
        verbal,
        brain,
        state,
        user_input=user_input,
        free_text_category=free_text_category,
        turns_before_reply=turns_before_reply,
    )
    raw = (verbal or "").strip()
    if free_text_category and str(free_text_category).startswith(("aggressive_", "absurd", "apology")) and raw:
        return verbal
    att = brain.get("attitude", "guarded")
    tbr = int(st.session_state.get("turns", 0)) if turns_before_reply is None else int(turns_before_reply)
    if raw and first_impression_verbal_locked(user_input, tbr, state, att):
        return verbal
    if raw and preserve_scripted_menu_response(user_input, free_text_category):
        return verbal
    mode_ap = st.session_state.get("response_mode") or {}
    use_intent_overlay = use_intent_overlay and mode_ap.get("use_intent_overlay", True)
    if use_intent_overlay and is_specific(
        verbal,
        user_input,
        bool(mode_ap.get("emotional_intensity")),
    ):
        use_intent_overlay = False
    if not use_intent_overlay:
        return verbal

    user_norm = (user_input or "").strip().lower()

    # Response-intent diversity: only for generic pool rewrites (not full bucket lines).
    line, _intent = pick_overlay_line_and_nudge(att, state, user_input, brain)

    if "zip" in user_norm and att == "amused":
        line = "…What even was that?"
    return quote(line)

