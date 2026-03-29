# -*- coding: utf-8 -*-
"""
Scenario context lens: shapes behavior (weights, buckets, profile) without new dialogue.

All SAY text still comes from quarks / existing banks. This module only classifies prompts
and returns numeric / structural adjustments.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Literal, Mapping, Optional, Tuple

from canon_prompts import normalize_prompt_key

ScenarioId = Literal["living_room", "waiting_in_line", "bus_stop", "movie_theater", "first_date"]
PromptClass = Literal["natural", "awkward", "risky", "absurd"]

DISPLAY_TO_SCENARIO_ID: Dict[str, ScenarioId] = {
    "Living Room": "living_room",
    "Waiting in Line": "waiting_in_line",
    "Bus Stop": "bus_stop",
    "Movie Theater": "movie_theater",
    "First Date": "first_date",
}

SCENARIO_PROFILES: Dict[ScenarioId, Dict[str, Any]] = {
    "living_room": {
        "baseline_vibe": "relaxed",
        "awkwardness": 0.22,
        "risk_tolerance": 0.72,
        "social_pressure": 0.28,
        "openness": 0.78,
        "patience": 0.72,
        "trust_sensitivity": 0.42,
        "is_public": False,
    },
    "waiting_in_line": {
        "baseline_vibe": "impatient_public",
        "awkwardness": 0.55,
        "risk_tolerance": 0.45,
        "social_pressure": 0.48,
        "openness": 0.38,
        "patience": 0.32,
        "trust_sensitivity": 0.48,
        "is_public": True,
    },
    "bus_stop": {
        "baseline_vibe": "transient_public",
        "awkwardness": 0.52,
        "risk_tolerance": 0.52,
        "social_pressure": 0.44,
        "openness": 0.42,
        "patience": 0.40,
        "trust_sensitivity": 0.46,
        "is_public": True,
    },
    "movie_theater": {
        "baseline_vibe": "hushed_social",
        "awkwardness": 0.48,
        "risk_tolerance": 0.40,
        "social_pressure": 0.62,
        "openness": 0.45,
        "patience": 0.48,
        "trust_sensitivity": 0.52,
        "is_public": True,
    },
    "first_date": {
        "baseline_vibe": "romantic_high_stakes",
        "awkwardness": 0.62,
        "risk_tolerance": 0.38,
        "social_pressure": 0.70,
        "openness": 0.55,
        "patience": 0.50,
        "trust_sensitivity": 0.82,
        "is_public": True,
    },
}

# Optional physical flavor (additive only; not dialogue).
PHYSICAL_FLAVOR_BY_SCENARIO: Dict[ScenarioId, str] = {
    "living_room": "",
    "waiting_in_line": "glances ahead, clearly distracted",
    "bus_stop": "shifts weight, scanning surroundings",
    "movie_theater": "keeps voice low, eyes flicking toward the screen",
    "first_date": "tries to read your face without staring",
}

# Normalized keys hidden from SAY dropdown for a scenario (content unchanged elsewhere).
HIDDEN_PROMPT_KEYS_BY_SCENARIO: Dict[ScenarioId, frozenset[str]] = {
    "movie_theater": frozenset({normalize_prompt_key("Cash me outside, how 'bout that?")}),
}

_N_DATE = normalize_prompt_key("Do you want to go on a date?")
_N_WANT = normalize_prompt_key("What do you want?")
_N_ACTING = normalize_prompt_key("Why are you acting like this?")

# Per user spec: same prompt classified differently by scenario.
_DATE_CLASS: Dict[ScenarioId, PromptClass] = {
    "living_room": "natural",
    "waiting_in_line": "awkward",
    "bus_stop": "awkward",
    "movie_theater": "risky",
    "first_date": "risky",
}

_WANT_CLASS: Dict[ScenarioId, PromptClass] = {
    "living_room": "natural",
    "waiting_in_line": "awkward",
    "bus_stop": "awkward",
    "movie_theater": "risky",
    "first_date": "risky",
}

_ACTING_CLASS: Dict[ScenarioId, PromptClass] = {
    "living_room": "risky",
    "waiting_in_line": "risky",
    "bus_stop": "awkward",
    "movie_theater": "risky",
    "first_date": "risky",
}


def scenario_id_from_display(scenario_display_name: str) -> ScenarioId:
    sid = DISPLAY_TO_SCENARIO_ID.get(str(scenario_display_name or "").strip())
    if sid:
        return sid
    return "living_room"


def get_scenario_profile(scenario_display_name: str) -> Dict[str, Any]:
    return dict(SCENARIO_PROFILES[scenario_id_from_display(scenario_display_name)])


def evaluate_prompt_in_scenario(prompt: str, scenario_display_name: str) -> PromptClass:
    pn = normalize_prompt_key(prompt)
    sid = scenario_id_from_display(scenario_display_name)
    if pn == _N_DATE:
        return _DATE_CLASS[sid]
    if pn == _N_WANT:
        return _WANT_CLASS[sid]
    if pn == _N_ACTING:
        return _ACTING_CLASS[sid]
    prof = SCENARIO_PROFILES[sid]
    # Light heuristics — no NLP; keyword buckets only.
    low = (prompt or "").lower()
    absurd_markers = ("jetski", "jet ski", "moonwalk", "sam howell", "playboi", "carti", "peta", "mink")
    if any(m in low for m in absurd_markers):
        return "absurd"
    romantic_markers = ("date", "attractive", "like me", "sleep at your house", "kiss")
    confront_markers = ("wrong", "disagree", "who do you think", "better than me", "gives you the right")
    if any(m in low for m in confront_markers):
        return "risky" if prof["social_pressure"] >= 0.5 else "awkward"
    if any(m in low for m in romantic_markers):
        return "risky" if sid in ("first_date", "movie_theater") else "awkward" if prof["is_public"] else "natural"
    if prof["awkwardness"] >= 0.5 and prof["is_public"]:
        return "awkward"
    return "natural"


def _class_to_tier_bias(pclass: PromptClass, prof: Mapping[str, Any]) -> Tuple[int, int, int]:
    """Additive (common, signature, nuclear) tier weights for canon line selection."""
    awk = float(prof.get("awkwardness", 0.5))
    press = float(prof.get("social_pressure", 0.5))
    if pclass == "natural":
        return (6, 0, -4)
    if pclass == "awkward":
        # Favor shorter / blunt reads: more common tier mass
        return (12, int(-4 * awk), int(-8 * awk))
    if pclass == "risky":
        return (int(-6 * press), 2, int(10 + 8 * press))
    # absurd
    return (-4, 6, 14)


def resolve_scenario_adjustments(
    prompt: str,
    scenario_display_name: str,
    interaction_profile: Mapping[str, Any],
    *,
    current_bucket: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns modifiers for canon tier weights, bucket escalation odds, and profile scaling.

    Keys:
      - scenario_id, prompt_class
      - tier_weight_bonus: (c, s, n) added to tier weights before clamp
      - bucket_escalate_probability: P(one step harsher), only meaningful for neutral/negative
      - escalation_delta_multiplier: scales interaction_profile escalation increment
      - trust_drop_multiplier: scales trust-down component inside escalation
      - repeat_irritation_multiplier: scales escalation when same SAY repeats
      - public_awkward_boost: if True, question-streak threshold for confusion_loop is tighter (line/bus)
    """
    sid = scenario_id_from_display(scenario_display_name)
    prof = SCENARIO_PROFILES[sid]
    pclass: PromptClass
    if not (prompt or "").strip():
        pclass = "natural"
    else:
        pclass = evaluate_prompt_in_scenario(prompt, scenario_display_name)
    tier_bonus = _class_to_tier_bias(pclass, prof)

    press = float(prof["social_pressure"])
    ts = float(prof["trust_sensitivity"])
    patience = float(prof["patience"])
    risk_map = {"natural": 0.08, "awkward": 0.18, "risky": 0.32, "absurd": 0.40}
    class_r = risk_map[pclass]
    bucket_p = min(0.42, press * class_r * (0.55 if current_bucket == "negative" else 0.28))

    esc_mult = 1.0 + 0.35 * press * class_r
    if sid == "waiting_in_line":
        esc_mult += 0.22 * (1.0 - patience)
    if sid == "first_date":
        esc_mult += 0.18 * ts

    trust_mult = 1.0 + 0.55 * ts * class_r
    repeat_mult = 1.0
    if sid == "waiting_in_line":
        repeat_mult += 0.45 * (1.0 - patience)
    if sid == "bus_stop":
        repeat_mult += 0.25 * float(prof.get("awkwardness", 0.5))

    return {
        "scenario_id": sid,
        "prompt_class": pclass,
        "tier_weight_bonus": tier_bonus,
        "bucket_escalate_probability": bucket_p,
        "escalation_delta_multiplier": esc_mult,
        "trust_drop_multiplier": trust_mult,
        "repeat_irritation_multiplier": repeat_mult,
        "public_awkward_boost": sid in ("waiting_in_line", "bus_stop"),
    }


def apply_scenario_bucket_nudge(
    bucket: str,
    prompt: str,
    scenario_display_name: str,
    interaction_profile: Mapping[str, Any],
) -> str:
    if bucket not in ("neutral", "negative"):
        return bucket
    adj = resolve_scenario_adjustments(
        prompt, scenario_display_name, interaction_profile, current_bucket=bucket
    )
    p = float(adj.get("bucket_escalate_probability", 0.0))
    if p <= 0 or random.random() >= p:
        return bucket
    order = ("positive", "neutral", "negative", "severe")
    try:
        i = order.index(bucket)
    except ValueError:
        return bucket
    if i + 1 < len(order):
        return order[i + 1]
    return bucket


def append_physical_flavor(physical: str, scenario_display_name: str) -> str:
    sid = scenario_id_from_display(scenario_display_name)
    flavor = (PHYSICAL_FLAVOR_BY_SCENARIO.get(sid) or "").strip()
    if not flavor:
        return physical
    base = (physical or "").strip()
    if not base:
        return flavor
    if flavor.lower() in base.lower():
        return physical
    return f"{base} — {flavor}"


def filter_say_options_for_scenario(
    options: Mapping[str, Any],
    scenario_display_name: str,
) -> Dict[str, Any]:
    """Drop only keys listed in HIDDEN_PROMPT_KEYS_BY_SCENARIO for this scenario."""
    sid = scenario_id_from_display(scenario_display_name)
    hide = HIDDEN_PROMPT_KEYS_BY_SCENARIO.get(sid, frozenset())
    if not hide:
        return dict(options)
    out: Dict[str, Any] = {}
    for k, v in options.items():
        if normalize_prompt_key(str(k)) in hide:
            continue
        out[str(k)] = v
    return out
