# -*- coding: utf-8 -*-
"""
Relationship trajectory: numeric biases over time. No new dialogue — shapes stats, selection, thresholds.

Works with scenario, archetype, callback, and interaction_profile layers (additive).
"""

from __future__ import annotations

import random
from typing import Any, Dict, Mapping, MutableMapping, Optional, Tuple

from .interaction_profile import (
    DISRESPECT_MENU_PROMPTS,
    PROFILE_KEY,
    PUSHY_ACTIONS,
    init_interaction_profile,
)

TrajectoryId = str

TRAJECTORY_PROFILES: Dict[TrajectoryId, Dict[str, Any]] = {
    "slow_warmup": {
        "trust_gain_rate": 0.84,
        "trust_loss_rate": 0.88,
        "irritation_growth": 0.82,
        "stress_mult": 0.9,
        "interest_pos_mult": 0.92,
        "interest_neg_mult": 0.95,
        "happiness_pos_mult": 1.05,
        "happiness_neg_mult": 0.9,
        "forgiveness": 0.72,
        "repetition_murder_threshold": 6,
        "recovery_relief_mult": 1.12,
        "escalation_delta_mult": 0.82,
        "trust_drop_mult": 0.88,
        "repeat_irritation_mult": 0.85,
        "callback_sensitivity_base": 0.92,
        "callback_sensitivity_per_neg_streak": -0.03,
        "severe_escalation_after_friction": 0.9,
        "tier_bonus": (4, 0, -2),
        "finisher_tier_bias": (4, 2, -2),
        "finisher_tag_weights": {
            "final": 0.5,
            "boundary": 0.35,
            "cold": -0.2,
        },
    },
    "volatile": {
        "trust_gain_rate": 1.05,
        "trust_loss_rate": 1.28,
        "irritation_growth": 1.14,
        "stress_mult": 1.14,
        "interest_pos_mult": 1.08,
        "interest_neg_mult": 1.22,
        "happiness_pos_mult": 1.0,
        "happiness_neg_mult": 1.25,
        "forgiveness": 0.35,
        "repetition_murder_threshold": 4,
        "recovery_relief_mult": 0.92,
        "escalation_delta_mult": 1.28,
        "trust_drop_mult": 1.22,
        "repeat_irritation_mult": 1.25,
        "callback_sensitivity_base": 1.12,
        "callback_sensitivity_per_neg_streak": 0.06,
        "severe_escalation_after_friction": 1.22,
        "tier_bonus": (-6, 2, 8),
        "finisher_tier_bias": (-8, 2, 10),
        "finisher_tag_weights": {
            "disrespect": 1.4,
            "judgment": 1.1,
            "dismissive": 0.6,
            "final": 0.25,
        },
    },
    "guarded_then_open": {
        "trust_gain_rate": 0.85,
        "trust_loss_rate": 1.05,
        "irritation_growth": 0.95,
        "stress_mult": 1.02,
        "interest_pos_mult": 0.88,
        "interest_neg_mult": 1.0,
        "happiness_pos_mult": 0.92,
        "happiness_neg_mult": 1.0,
        "forgiveness": 0.55,
        "repetition_murder_threshold": 5,
        "recovery_relief_mult": 1.05,
        "escalation_delta_mult": 0.95,
        "trust_drop_mult": 1.05,
        "repeat_irritation_mult": 1.02,
        "callback_sensitivity_base": 1.05,
        "callback_sensitivity_per_neg_streak": 0.02,
        "severe_escalation_after_friction": 1.05,
        "tier_bonus": (6, -2, -2),
        "finisher_tier_bias": (5, 0, -1),
        "finisher_tag_weights": {
            "boundary": 1.0,
            "persistence": 0.6,
            "final": 0.4,
        },
        "open_phase_trust_gain_bonus": 0.22,
        "open_after_pos_streak": 2,
        "open_after_turns": 4,
    },
    "playful_then_cutting": {
        "trust_gain_rate": 1.0,
        "trust_loss_rate": 1.12,
        "irritation_growth": 1.08,
        "stress_mult": 1.05,
        "interest_pos_mult": 1.12,
        "interest_neg_mult": 1.08,
        "happiness_pos_mult": 1.05,
        "happiness_neg_mult": 1.05,
        "forgiveness": 0.48,
        "repetition_murder_threshold": 5,
        "recovery_relief_mult": 1.0,
        "escalation_delta_mult": 1.05,
        "trust_drop_mult": 1.08,
        "repeat_irritation_mult": 1.08,
        "callback_sensitivity_base": 1.0,
        "callback_sensitivity_per_neg_streak": 0.04,
        "severe_escalation_after_friction": 1.22,
        "tier_bonus": (-4, 10, 2),
        "finisher_tier_bias": (-3, 6, 4),
        "finisher_tag_weights": {
            "dismissive": 0.5,
            "final": 0.2,
        },
        "cutting_tier_bonus": (-2, -4, 6),
        "cutting_tag_extra": {"dismissive": 1.2, "cold": 0.9, "judgment": 0.7},
        "cutting_neg_streak": 3,
        "cutting_escalation": 13,
        "cutting_exit_escalation": 7,
        "cutting_exit_neg": 1,
    },
    "fragile": {
        "trust_gain_rate": 0.62,
        "trust_loss_rate": 1.48,
        "irritation_growth": 1.15,
        "stress_mult": 1.35,
        "interest_pos_mult": 0.85,
        "interest_neg_mult": 1.32,
        "happiness_pos_mult": 0.88,
        "happiness_neg_mult": 1.28,
        "forgiveness": 0.28,
        "repetition_murder_threshold": 4,
        "recovery_relief_mult": 0.85,
        "escalation_delta_mult": 1.18,
        "trust_drop_mult": 1.32,
        "repeat_irritation_mult": 1.2,
        "callback_sensitivity_base": 1.08,
        "callback_sensitivity_per_neg_streak": 0.05,
        "severe_escalation_after_friction": 1.28,
        "tier_bonus": (8, 0, 4),
        "finisher_tier_bias": (6, -2, 4),
        "finisher_tag_weights": {
            "cold": 1.1,
            "judgment": 0.9,
            "boundary": 0.7,
            "final": 0.35,
            "disrespect": 0.5,
        },
    },
}

TRAJECTORY_OPTIONS: Tuple[str, ...] = (
    "slow_warmup",
    "volatile",
    "guarded_then_open",
    "playful_then_cutting",
    "fragile",
)

TRAJECTORY_DEBUG_KEY = "_trajectory_debug"


def resolve_initial_trajectory(
    personality_type: str,
    archetype_id: str,
    starting_mood: str,
    background: str,
    *,
    rng: Optional[random.Random] = None,
) -> TrajectoryId:
    """
    Pick a relationship trajectory from builder inputs (weighted, slightly random).
    `archetype_id` must be the resolved id (e.g. cocky, playful), not UI 'Auto'.
    """
    r = rng or random.Random()
    opts = list(TRAJECTORY_OPTIONS)
    w: Dict[str, float] = {tid: 1.0 for tid in opts}
    w["fragile"] = 0.36

    pers = str(personality_type or "").strip()
    arch = str(archetype_id or "").strip().lower()
    mood = str(starting_mood or "").strip()
    bg = str(background or "").strip()

    if arch == "cocky":
        w["volatile"] += 2.0
        w["playful_then_cutting"] += 1.85
        w["slow_warmup"] += 0.3
    if arch == "playful":
        w["playful_then_cutting"] += 1.95
        w["volatile"] += 0.8
        w["slow_warmup"] += 0.5
    if arch == "guarded":
        w["guarded_then_open"] += 2.5
        w["slow_warmup"] += 1.25
    if arch == "awkward":
        w["slow_warmup"] += 1.65
        w["guarded_then_open"] += 1.05
        w["fragile"] += 0.7
    if arch == "cold":
        w["guarded_then_open"] += 1.45
        w["fragile"] += 0.9
        w["slow_warmup"] += 0.6

    if pers in ("Confident", "Aggressive"):
        w["volatile"] += 1.05
        w["playful_then_cutting"] += 0.65
    if pers == "Shy":
        w["slow_warmup"] += 1.5
        w["guarded_then_open"] += 1.1
        w["fragile"] += 0.5
    if pers == "Empathetic":
        w["slow_warmup"] += 0.85
        w["guarded_then_open"] += 0.5
    if pers == "Analytical":
        w["guarded_then_open"] += 0.8
        w["slow_warmup"] += 0.4
    if pers == "Impulsive":
        w["volatile"] += 1.3
        w["playful_then_cutting"] += 0.6

    if mood == "Anxious":
        w["fragile"] += 1.35
        w["volatile"] += 0.5
        w["slow_warmup"] += 0.3
    if mood == "Irritated":
        w["volatile"] += 1.75
        w["fragile"] += 0.4
    if mood == "Calm":
        w["slow_warmup"] += 1.0
        w["guarded_then_open"] += 0.4
    if mood == "Excited":
        w["playful_then_cutting"] += 0.95
        w["volatile"] += 0.35
    if mood == "Neutral":
        w["slow_warmup"] += 0.3

    if bg in ("Office Worker", "College Student"):
        w["guarded_then_open"] += 0.5
        w["slow_warmup"] += 0.35
    if bg == "Military Veteran":
        w["volatile"] += 0.6
        w["guarded_then_open"] += 0.3
    if bg == "Artist":
        w["playful_then_cutting"] += 0.5
        w["fragile"] += 0.3
    if bg == "Entrepreneur":
        w["volatile"] += 0.5
        w["playful_then_cutting"] += 0.4
    if bg == "Athlete":
        w["volatile"] += 0.45
        w["playful_then_cutting"] += 0.35

    for tid in opts:
        w[tid] *= 0.82 + 0.36 * r.random()

    weights = [max(0.08, w[tid]) for tid in opts]
    return r.choices(opts, weights=weights, k=1)[0]


def resolve_trajectory_id(build_snapshot: Mapping[str, Any]) -> TrajectoryId:
    snap = dict(build_snapshot or {})
    t = str(snap.get("Trajectory") or "").strip()
    if t in TRAJECTORY_PROFILES:
        return t
    return "slow_warmup"


def _phase_open_guards_then_open(prof: Mapping[str, Any], turns: int, base: Dict[str, Any]) -> bool:
    ps = int(prof.get("positive_streak", 0) or 0)
    need_s = int(base.get("open_after_pos_streak", 2) or 2)
    need_t = int(base.get("open_after_turns", 5) or 5)
    return ps >= need_s or turns >= need_t


def _phase_cutting_playful(prof: Mapping[str, Any], base: Dict[str, Any]) -> bool:
    """True when friction warrants cutting-tier behavior (aligned with _compute playful phase)."""
    neg = int(prof.get("negative_streak", 0) or 0)
    esc = int(prof.get("escalation_score", 0) or 0)
    repair = int(prof.get("repair_attempt_streak", 0) or 0)
    sustained = int(prof.get("sustained_respect_window", 0) or 0)
    pos_s = int(prof.get("positive_streak", 0) or 0)
    exit_soft = (
        (repair >= 1 or sustained >= 2 or pos_s >= 2)
        and neg <= 1
        and esc <= int(base.get("cutting_exit_escalation", 7) or 7)
    )
    if neg >= int(base.get("cutting_neg_streak", 3) or 3):
        return True
    if esc >= int(base.get("cutting_escalation", 13) or 13):
        return True
    if neg >= 2 and esc >= 10:
        return True
    mid = (neg >= 2 and esc >= 9) or esc >= 12
    if mid and not exit_soft:
        return True
    return False


def _add_triple(
    a: Tuple[int, int, int],
    b: Tuple[int, int, int],
) -> Tuple[int, int, int]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _apply_demo_early_turn_overlays(
    out: Dict[str, Any],
    tid: str,
    phase: str,
    turns: int,
) -> None:
    """Lightweight first-replies feel (turns 0–2); additive only."""
    if int(turns) > 2:
        return
    cur_tb = tuple(out.get("tier_bonus_delta", (0, 0, 0)))

    if tid == "slow_warmup" and phase in ("reserved", "warming"):
        out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) - 0.04
        out["callback_probability_add"] = float(out.get("callback_probability_add", 0)) - 0.03
        if phase == "reserved":
            out["bucket_cold_push"] = float(out.get("bucket_cold_push", 0)) + 0.03
    elif tid == "guarded_then_open":
        if phase == "guarded":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) - 0.04
            out["bucket_cold_push"] = float(out.get("bucket_cold_push", 0)) + 0.05
            out["tier_bonus_delta"] = _add_triple(cur_tb, (2, -1, 0))
        elif phase == "testing":
            out["callback_probability_add"] = float(out.get("callback_probability_add", 0)) + 0.03
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) - 0.02
    elif tid == "volatile":
        if phase == "stable":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) + 0.035
            out["tier_bonus_delta"] = _add_triple(cur_tb, (-1, 3, -1))
        elif phase == "irritated":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) + 0.025
    elif tid == "playful_then_cutting":
        if phase == "playful":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) + 0.06
            out["tier_bonus_delta"] = _add_triple(cur_tb, (-1, 3, 0))
            out["bucket_warm_pull"] = float(out.get("bucket_warm_pull", 0)) + 0.04
        elif phase == "edgy":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) + 0.03
        elif phase == "cutting":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) + 0.02
            out["callback_probability_add"] = float(out.get("callback_probability_add", 0)) - 0.03
    elif tid == "fragile":
        if phase == "careful":
            out["voice_sharpen_bias"] = float(out.get("voice_sharpen_bias", 0)) - 0.05
            out["bucket_cold_push"] = float(out.get("bucket_cold_push", 0)) + 0.05
            out["tier_bonus_delta"] = _add_triple(cur_tb, (1, -2, 0))
        elif phase == "shaken" and int(turns) <= 1:
            out["bucket_severity_pull"] = float(out.get("bucket_severity_pull", 0)) + 0.04


def _compute_trajectory_phase(
    tid: TrajectoryId,
    prof: Mapping[str, Any],
    state: Mapping[str, Any],
    turns: int,
    raw: Dict[str, Any],
) -> str:
    pos_s = int(prof.get("positive_streak", 0) or 0)
    neg_s = int(prof.get("negative_streak", 0) or 0)
    esc = int(prof.get("escalation_score", 0) or 0)
    sustained = int(prof.get("sustained_respect_window", 0) or 0)
    push_ign = int(prof.get("pushback_ignored_count", 0) or 0)
    trust = int(state.get("trust", 40) or 0)
    anger = int(state.get("anger", 20) or 0)

    if tid == "slow_warmup":
        if pos_s >= 3 and (sustained >= 3 or trust >= 46):
            return "comfortable"
        if turns < 3 and pos_s < 2 and sustained < 2:
            return "reserved"
        return "warming"

    if tid == "guarded_then_open":
        open_gate = _phase_open_guards_then_open(prof, turns, raw)
        repair_s = int(prof.get("repair_attempt_streak", 0) or 0)
        disrespect = bool(prof.get("disrespect_flag"))
        conflict = neg_s >= 2 or esc >= 7 or disrespect
        if conflict and int(turns) >= 1:
            if pos_s >= 3 or trust >= 46 or (repair_s >= 1 and trust >= 42):
                return "open"
            return "testing"
        if not open_gate:
            return "guarded"
        if pos_s >= 3 or trust >= 46 or (repair_s >= 1 and sustained >= 2 and trust >= 40):
            return "open"
        return "testing"

    if tid == "volatile":
        t = int(turns)
        repair_s = int(prof.get("repair_attempt_streak", 0) or 0)
        early_vol = t <= 1 and neg_s == 0 and esc < 8 and push_ign <= 1
        if early_vol:
            if esc >= 5 or anger >= 66 or push_ign >= 2:
                return "irritated"
            return "stable"
        de_escalate = (repair_s >= 1 or (pos_s >= 2 and sustained >= 2)) and esc <= 11 and neg_s <= 1
        sticky_esc = (esc >= 11 or neg_s >= 2) and (anger >= 54 or esc >= 9)
        if sticky_esc and not de_escalate:
            return "escalating"
        hot = anger >= 70 or esc >= 22 or push_ign >= 4
        aggravated = (
            (neg_s >= 2 and (esc >= 12 or anger >= 58 or push_ign >= 2))
            or (neg_s >= 3)
            or (t >= 3 and anger >= 64 and neg_s >= 1)
            or (t >= 2 and esc >= 16)
        )
        if hot or aggravated:
            return "escalating"
        if neg_s >= 1 or esc >= 6 or anger >= 48 or push_ign >= 2:
            return "irritated"
        return "stable"

    if tid == "playful_then_cutting":
        repair_s = int(prof.get("repair_attempt_streak", 0) or 0)
        exit_soft = (
            (repair_s >= 1 or sustained >= 2 or pos_s >= 2)
            and neg_s <= 1
            and esc <= int(raw.get("cutting_exit_escalation", 7) or 7)
        )
        hard_cut = neg_s >= 3 or esc >= 14 or (neg_s >= 2 and esc >= 12)
        mid_cut = (neg_s >= 2 and esc >= 9) or esc >= 12
        if hard_cut or (mid_cut and not exit_soft):
            return "cutting"
        if neg_s >= 1 or esc >= 6:
            return "edgy"
        return "playful"

    if tid == "fragile":
        if neg_s >= 2 or trust < 34 or esc >= 9:
            return "withdrawn"
        if neg_s >= 1 or trust < 42 or esc >= 4:
            return "shaken"
        return "careful"

    return "warming"


def resolve_trajectory_runtime_profile(
    trajectory_id: TrajectoryId,
    interaction_profile: Mapping[str, Any],
    state: Mapping[str, Any],
    *,
    turns_before_this_reply: int = 0,
) -> Dict[str, Any]:
    """
    Live hidden phase + additive overlays (tier/callback/finisher/voice/physical/repetition/forgiveness).
    Base trajectory id never changes; phase evolves from interaction_profile + state.
    """
    tid = trajectory_id if trajectory_id in TRAJECTORY_PROFILES else "slow_warmup"
    raw = dict(TRAJECTORY_PROFILES[tid])
    turns = int(turns_before_this_reply or 0)
    phase = _compute_trajectory_phase(tid, interaction_profile, state, turns, raw)

    out: Dict[str, Any] = {
        "trajectory_id": tid,
        "trajectory_phase": phase,
        "tier_bonus_delta": (0, 0, 0),
        "finisher_tier_bias_delta": (0, 0, 0),
        "finisher_tag_delta": {},
        "callback_probability_add": 0.0,
        "voice_sharpen_bias": 0.0,
        "physical_phase_suffixes": (),
        "repetition_murder_threshold_delta": 0,
        "trust_gain_mult_add": 0.0,
        "trust_loss_mult_add": 0.0,
        "recovery_relief_mult_add": 0.0,
        "escalation_delta_mult_add": 0.0,
        "repeat_irritation_mult_add": 0.0,
        "forgiveness_repair_scale": 1.0,
        "bucket_warm_pull": 0.0,
        "bucket_cold_push": 0.0,
        "bucket_severity_pull": 0.0,
    }

    if tid == "slow_warmup":
        if phase == "reserved":
            out["tier_bonus_delta"] = (5, -4, -1)
            out["voice_sharpen_bias"] = -0.08
            out["callback_probability_add"] = -0.06
            out["physical_phase_suffixes"] = ("measured, unhurried posture", "keeps answers a little short on purpose")
            out["bucket_cold_push"] = 0.06
            out["recovery_relief_mult_add"] = 0.05
        elif phase == "warming":
            out["tier_bonus_delta"] = (2, 3, -1)
            out["voice_sharpen_bias"] = -0.02
            out["trust_gain_mult_add"] = 0.04
            out["physical_phase_suffixes"] = ("warming up by inches, not leaps",)
        else:  # comfortable
            out["tier_bonus_delta"] = (-4, 5, 0)
            out["voice_sharpen_bias"] = 0.03
            out["trust_gain_mult_add"] = 0.06
            out["recovery_relief_mult_add"] = 0.08
            out["callback_probability_add"] = -0.05
            out["bucket_warm_pull"] = 0.12
            out["physical_phase_suffixes"] = ("easier posture than before", "a little more room in how they answer")

    elif tid == "guarded_then_open":
        if phase == "guarded":
            out["tier_bonus_delta"] = (5, -3, -1)
            out["voice_sharpen_bias"] = -0.05
            out["bucket_cold_push"] = 0.14
            out["callback_probability_add"] = 0.04
            out["physical_phase_suffixes"] = ("closed shoulders, careful distance", "answers like they’re weighing risk")
        elif phase == "testing":
            out["tier_bonus_delta"] = (2, 1, 0)
            out["trust_gain_mult_add"] = 0.06
            out["physical_phase_suffixes"] = ("still guarded but listening closer",)
        else:  # open
            out["tier_bonus_delta"] = (-6, 5, 1)
            out["trust_gain_mult_add"] = 0.18
            out["recovery_relief_mult_add"] = 0.1
            out["bucket_warm_pull"] = 0.16
            out["voice_sharpen_bias"] = 0.02
            out["callback_probability_add"] = -0.04
            out["finisher_tag_delta"] = {"final": -0.25, "boundary": -0.15}
            out["physical_phase_suffixes"] = ("visibly softer than their default wall",)

    elif tid == "volatile":
        if phase == "stable":
            out["tier_bonus_delta"] = (4, 2, -2)
            out["callback_probability_add"] = -0.06
            out["bucket_warm_pull"] = 0.08
            out["bucket_cold_push"] = -0.04
        elif phase == "irritated":
            out["tier_bonus_delta"] = (-2, 0, 4)
            out["finisher_tier_bias_delta"] = (-2, 0, 3)
            out["callback_probability_add"] = 0.1
            out["voice_sharpen_bias"] = 0.08
            out["escalation_delta_mult_add"] = 0.08
            out["bucket_cold_push"] = 0.1
            out["bucket_severity_pull"] = 0.06
            out["physical_phase_suffixes"] = ("jaw tight, patience thinning", "reactive stillness before they snap")
        else:  # escalating
            out["tier_bonus_delta"] = (-4, -2, 8)
            out["finisher_tier_bias_delta"] = (-4, -2, 6)
            out["finisher_tag_delta"] = {"disrespect": 0.6, "judgment": 0.45, "dismissive": 0.35}
            out["callback_probability_add"] = 0.14
            out["voice_sharpen_bias"] = 0.14
            out["repetition_murder_threshold_delta"] = -1
            out["escalation_delta_mult_add"] = 0.12
            out["repeat_irritation_mult_add"] = 0.1
            out["bucket_severity_pull"] = 0.14
            out["bucket_cold_push"] = 0.12
            out["physical_phase_suffixes"] = ("coiled energy, ready to shut this down",)

    elif tid == "playful_then_cutting":
        if phase == "playful":
            out["tier_bonus_delta"] = (-2, 8, 0)
            out["finisher_tier_bias_delta"] = (-2, 4, 0)
            out["voice_sharpen_bias"] = -0.04
            out["bucket_warm_pull"] = 0.08
            out["physical_phase_suffixes"] = ("amused timing, a little theatrical", "loose, teasing energy")
        elif phase == "edgy":
            out["tier_bonus_delta"] = (-3, 2, 4)
            out["finisher_tag_delta"] = {"dismissive": 0.45, "cold": 0.25}
            out["voice_sharpen_bias"] = 0.06
            out["bucket_cold_push"] = 0.08
            out["physical_phase_suffixes"] = ("smile doesn’t quite reach the eyes",)
        else:  # cutting
            ct = tuple(raw.get("cutting_tier_bonus") or (-2, -4, 6))
            out["tier_bonus_delta"] = ct
            out["finisher_tier_bias_delta"] = (0, -4, 7)
            fd: Dict[str, float] = {}
            for k, v in (raw.get("cutting_tag_extra") or {}).items():
                fd[k] = float(v)
            out["finisher_tag_delta"] = fd
            out["voice_sharpen_bias"] = 0.12
            out["callback_probability_add"] = 0.06
            out["bucket_cold_push"] = 0.14
            out["bucket_severity_pull"] = 0.1
            out["physical_phase_suffixes"] = ("flat precision, done entertaining this", "cutting calm")

    elif tid == "fragile":
        if phase == "careful":
            out["tier_bonus_delta"] = (3, -1, 0)
            out["voice_sharpen_bias"] = -0.06
            out["trust_loss_mult_add"] = 0.05
            out["physical_phase_suffixes"] = ("small guarded movements", "watching for the next wrong tone")
        elif phase == "shaken":
            out["tier_bonus_delta"] = (4, -2, 2)
            out["trust_loss_mult_add"] = 0.12
            out["recovery_relief_mult_add"] = -0.1
            out["forgiveness_repair_scale"] = 0.88
            out["callback_probability_add"] = 0.06
            out["bucket_cold_push"] = 0.1
            out["voice_sharpen_bias"] = 0.02
            out["physical_phase_suffixes"] = ("visibly unsettled", "hesitates before answering")
        else:  # withdrawn
            out["tier_bonus_delta"] = (6, -4, 4)
            out["finisher_tier_bias_delta"] = (4, -3, 3)
            out["finisher_tag_delta"] = {"cold": 0.5, "final": 0.4, "boundary": 0.35}
            out["trust_loss_mult_add"] = 0.18
            out["recovery_relief_mult_add"] = -0.18
            out["forgiveness_repair_scale"] = 0.72
            out["trust_gain_mult_add"] = -0.08
            out["repetition_murder_threshold_delta"] = -1
            out["bucket_cold_push"] = 0.16
            out["bucket_severity_pull"] = 0.08
            out["voice_sharpen_bias"] = 0.04
            out["physical_phase_suffixes"] = ("pulled inward, like they’re done extending benefit of the doubt",)

    _apply_demo_early_turn_overlays(out, tid, phase, turns)
    return out


def append_trajectory_phase_physical_flavor(physical: str, adj: Mapping[str, Any]) -> str:
    pool = adj.get("physical_phase_suffixes") or ()
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


def resolve_trajectory_adjustments(
    trajectory_id: TrajectoryId,
    interaction_profile: Mapping[str, Any],
    current_state: Mapping[str, Any],
    *,
    turns_before_this_reply: int = 0,
) -> Dict[str, Any]:
    tid = trajectory_id if trajectory_id in TRAJECTORY_PROFILES else "slow_warmup"
    raw = dict(TRAJECTORY_PROFILES[tid])
    rt = resolve_trajectory_runtime_profile(
        tid,
        interaction_profile,
        current_state,
        turns_before_this_reply=turns_before_this_reply,
    )
    phase = str(rt.get("trajectory_phase", "") or "")

    pos_s = int(interaction_profile.get("positive_streak", 0) or 0)
    neg_s = int(interaction_profile.get("negative_streak", 0) or 0)
    repair_s = int(interaction_profile.get("repair_attempt_streak", 0) or 0)
    sustained = int(interaction_profile.get("sustained_respect_window", 0) or 0)
    esc = int(interaction_profile.get("escalation_score", 0) or 0)

    trust_gain_mult = float(raw["trust_gain_rate"]) + float(rt.get("trust_gain_mult_add", 0))
    trust_loss_mult = float(raw["trust_loss_rate"]) + float(rt.get("trust_loss_mult_add", 0))
    if repair_s >= 1:
        forgive = float(raw["forgiveness"])
        trust_loss_mult *= 0.88 + 0.12 * forgive
        trust_loss_mult *= float(rt.get("forgiveness_repair_scale", 1.0))
        trust_gain_mult *= 1.0 + 0.08 * (1.0 - forgive) * min(repair_s, 3)
    if pos_s >= 2 and tid == "slow_warmup":
        trust_gain_mult *= 1.0 + 0.03 * min(pos_s - 1, 5)

    escalation_delta_mult = float(raw["escalation_delta_mult"]) + float(rt.get("escalation_delta_mult_add", 0))
    if neg_s >= 2:
        escalation_delta_mult *= float(raw["severe_escalation_after_friction"])

    recovery_relief_mult = float(raw["recovery_relief_mult"]) + float(rt.get("recovery_relief_mult_add", 0))
    repeat_irritation_mult = float(raw["repeat_irritation_mult"]) + float(rt.get("repeat_irritation_mult_add", 0))

    cb_base = float(raw["callback_sensitivity_base"])
    cb_drift = float(raw["callback_sensitivity_per_neg_streak"]) * neg_s
    if tid == "slow_warmup":
        cb_base -= 0.015 * min(sustained, 6)
    callback_probability_mult = max(
        0.2,
        min(1.85, cb_base + cb_drift + float(rt.get("callback_probability_add", 0))),
    )

    tier_bonus = _add_triple(
        tuple(raw["tier_bonus"]),  # type: ignore[arg-type]
        tuple(rt.get("tier_bonus_delta", (0, 0, 0))),
    )
    ftier = _add_triple(
        tuple(raw["finisher_tier_bias"]),  # type: ignore[arg-type]
        tuple(rt.get("finisher_tier_bias_delta", (0, 0, 0))),
    )
    ftags = dict(raw.get("finisher_tag_weights") or {})
    for k, v in (rt.get("finisher_tag_delta") or {}).items():
        ftags[k] = ftags.get(k, 0) + float(v)

    rep_thr = int(raw["repetition_murder_threshold"]) + int(rt.get("repetition_murder_threshold_delta", 0))
    rep_thr = max(3, min(8, rep_thr))

    mult_keys = (
        trust_gain_mult,
        trust_loss_mult,
        float(raw["irritation_growth"]),
        float(raw["stress_mult"]),
        float(raw["interest_pos_mult"]),
        float(raw["interest_neg_mult"]),
        float(raw["happiness_pos_mult"]),
        float(raw["happiness_neg_mult"]),
        recovery_relief_mult,
        escalation_delta_mult,
        float(raw["trust_drop_mult"]),
        repeat_irritation_mult,
    )
    stats_scaled = any(abs(m - 1.0) > 0.02 for m in mult_keys)

    runtime_debug = {
        "trajectory_phase": phase,
        "tier_bonus_delta": list(rt.get("tier_bonus_delta", (0, 0, 0))),
        "voice_sharpen_bias": float(rt.get("voice_sharpen_bias", 0)),
        "callback_probability_add": float(rt.get("callback_probability_add", 0)),
        "bucket_warm_pull": float(rt.get("bucket_warm_pull", 0)),
        "bucket_cold_push": float(rt.get("bucket_cold_push", 0)),
        "bucket_severity_pull": float(rt.get("bucket_severity_pull", 0)),
    }

    return {
        "trajectory_id": tid,
        "trajectory_phase": phase,
        "voice_sharpen_bias": float(rt.get("voice_sharpen_bias", 0)),
        "physical_phase_suffixes": tuple(rt.get("physical_phase_suffixes") or ()),
        "bucket_warm_pull": float(rt.get("bucket_warm_pull", 0)),
        "bucket_cold_push": float(rt.get("bucket_cold_push", 0)),
        "bucket_severity_pull": float(rt.get("bucket_severity_pull", 0)),
        "trajectory_runtime_profile": runtime_debug,
        "trust_gain_mult": trust_gain_mult,
        "trust_loss_mult": trust_loss_mult,
        "anger_growth_mult": float(raw["irritation_growth"]),
        "stress_mult": float(raw["stress_mult"]),
        "interest_pos_mult": float(raw["interest_pos_mult"]),
        "interest_neg_mult": float(raw["interest_neg_mult"]),
        "happiness_pos_mult": float(raw["happiness_pos_mult"]),
        "happiness_neg_mult": float(raw["happiness_neg_mult"]),
        "recovery_relief_mult": recovery_relief_mult,
        "escalation_delta_mult": escalation_delta_mult,
        "trust_drop_profile_mult": float(raw["trust_drop_mult"]),
        "repeat_irritation_mult": repeat_irritation_mult,
        "repetition_murder_threshold": rep_thr,
        "shutdown_threshold_nondefault": rep_thr != 5,
        "stats_scaled": stats_scaled,
        "callback_probability_mult": callback_probability_mult,
        "tier_bonus": tier_bonus,
        "finisher_tier_bias": ftier,
        "finisher_tag_weights": ftags,
        "memory_snapshot": {
            "positive_streak": pos_s,
            "negative_streak": neg_s,
            "repair_attempt_streak": repair_s,
            "sustained_respect_window": sustained,
            "pushback_ignored_count": int(interaction_profile.get("pushback_ignored_count", 0) or 0),
            "recovery_window": int(interaction_profile.get("recovery_window", 0) or 0),
            "escalation_score": esc,
            "trajectory_phase": phase,
        },
    }


def scale_stat_mods_for_trajectory(mods: Mapping[str, Any], adj: Mapping[str, Any]) -> Dict[str, int]:
    """Scale integer stat deltas; trust sign-split, other attrs scale positive deltas."""
    out: Dict[str, int] = {}
    tg = float(adj.get("trust_gain_mult", 1.0))
    tl = float(adj.get("trust_loss_mult", 1.0))
    ag = float(adj.get("anger_growth_mult", 1.0))
    sm = float(adj.get("stress_mult", 1.0))
    ip = float(adj.get("interest_pos_mult", 1.0))
    ine = float(adj.get("interest_neg_mult", 1.0))
    hp = float(adj.get("happiness_pos_mult", 1.0))
    hn = float(adj.get("happiness_neg_mult", 1.0))
    for k, v in mods.items():
        if k not in ATTRIBUTES_TRAJECTORY or not isinstance(v, (int, float)):
            out[k] = int(v) if isinstance(v, (int, float)) else v  # type: ignore[assignment]
            continue
        iv = int(v)
        if iv == 0:
            out[k] = 0
        elif k == "trust":
            out[k] = int(round(iv * (tg if iv > 0 else tl)))
        elif k == "anger":
            out[k] = int(round(iv * ag)) if iv > 0 else iv
        elif k == "stress":
            out[k] = int(round(iv * sm)) if iv > 0 else iv
        elif k == "interest":
            out[k] = int(round(iv * (ip if iv > 0 else ine)))
        elif k == "happiness":
            out[k] = int(round(iv * (hp if iv > 0 else hn)))
        elif k == "confusion":
            out[k] = int(round(iv * sm)) if iv > 0 else iv
        else:
            out[k] = iv
    return out


ATTRIBUTES_TRAJECTORY = frozenset(
    {"trust", "anger", "stress", "interest", "happiness", "confusion"}
)


def scale_relief_mods_for_trajectory(mods: Mapping[str, Any], adj: Mapping[str, Any]) -> Dict[str, int]:
    """Boost stat relief (negative confusion/stress) when recovery_mult > 1."""
    rm = float(adj.get("recovery_relief_mult", 1.0))
    out = {}
    for k, v in mods.items():
        if not isinstance(v, (int, float)):
            continue
        iv = int(v)
        if iv < 0 and k in ("confusion", "stress", "anger"):
            out[k] = int(round(iv * rm))
        elif iv > 0 and k in ("trust", "happiness"):
            out[k] = int(round(iv * rm))
        else:
            out[k] = iv
    return out


def apply_trajectory_bucket_nudge(
    bucket: str,
    adj: Mapping[str, Any],
    interaction_profile: Mapping[str, Any],
    state: Mapping[str, Any],
    turns: int,
) -> Tuple[str, bool]:
    tid = str(adj.get("trajectory_id", "slow_warmup"))
    phase = str(adj.get("trajectory_phase", "") or "")
    wp = float(adj.get("bucket_warm_pull", 0) or 0)
    cp = float(adj.get("bucket_cold_push", 0) or 0)
    sp = float(adj.get("bucket_severity_pull", 0) or 0)
    pos_s = int(interaction_profile.get("positive_streak", 0) or 0)
    neg_s = int(interaction_profile.get("negative_streak", 0) or 0)
    trust = int(state.get("trust", 40) or 0)
    b = bucket
    influenced = False

    if tid == "slow_warmup":
        warm_p = 0.08 + 0.03 * min(pos_s, 5) + (0.12 * wp if phase == "comfortable" else 0.06 * wp)
        if b == "neutral" and pos_s >= 2 and random.random() < min(0.55, warm_p):
            b, influenced = "positive", True
        elif b == "positive" and neg_s == 0 and pos_s >= 3 and random.random() < 0.06 + 0.08 * wp:
            b, influenced = "positive", True
        if phase == "reserved" and b == "positive" and random.random() < 0.08 + 0.1 * cp:
            b, influenced = "neutral", True

    if tid == "volatile":
        early_soft = int(turns) <= 1 and neg_s == 0 and phase == "stable"
        fric = (
            (0.05 if early_soft else 0.1)
            + 0.035 * neg_s
            + 0.14 * sp
            + (0.12 if phase == "escalating" else 0.06 if phase == "irritated" else 0)
        )
        if b in ("neutral", "positive") and neg_s >= 1 and random.random() < min(0.58, fric):
            b, influenced = "negative", True
        if phase == "escalating" and b == "positive" and random.random() < 0.1 + 0.12 * sp:
            b, influenced = "negative", True

    if tid == "guarded_then_open":
        open_phase = _phase_open_guards_then_open(interaction_profile, turns, TRAJECTORY_PROFILES.get(tid, {}))
        if phase == "guarded" or not open_phase:
            if b == "positive" and random.random() < 0.18 + 0.12 * cp:
                b, influenced = "neutral", True
        elif phase == "open":
            if b == "neutral" and trust > 36 and pos_s >= 1 and random.random() < 0.12 + 0.18 * wp:
                b, influenced = "positive", True
        else:
            if b == "positive" and random.random() < 0.08 + 0.06 * cp:
                b, influenced = "neutral", True
            if b == "neutral" and trust > 38 and pos_s >= 1 and random.random() < 0.1 + 0.08 * wp:
                b, influenced = "positive", True

    if tid == "playful_then_cutting":
        cutting = phase == "cutting"
        edgy = phase == "edgy"
        if cutting and b in ("positive", "neutral") and random.random() < 0.14 + 0.12 * sp + 0.1 * cp:
            b, influenced = "negative", True
        elif edgy and b in ("positive", "neutral") and random.random() < 0.1 + 0.06 * cp:
            b, influenced = "negative", True
        elif not cutting and b == "negative" and random.random() < 0.1 + 0.08 * wp:
            b, influenced = "neutral", True

    if tid == "fragile":
        if b == "positive" and (neg_s >= 1 or trust < 35) and random.random() < 0.16 + 0.12 * cp:
            b, influenced = "neutral", True
        if b == "neutral" and neg_s >= 2 and random.random() < 0.12 + 0.1 * sp:
            b, influenced = "negative", True
        if phase == "withdrawn" and b == "positive" and random.random() < 0.14 + 0.1 * cp:
            b, influenced = "neutral", True

    if wp > 0.02 and b == "neutral" and random.random() < 0.06 * (1 + wp * 2.5):
        b, influenced = "positive", True
    if cp > 0.02 and b == "positive" and random.random() < 0.07 * (1 + cp * 2.2):
        b, influenced = "neutral", True
    if sp > 0.02 and b in ("neutral", "positive") and random.random() < 0.06 * (1 + sp * 2.5):
        b, influenced = "negative", True

    return b, influenced


def bump_trajectory_progression_memory(
    sess: MutableMapping[str, Any],
    choice: str,
    old_state: Mapping[str, Any],
    new_state: Mapping[str, Any],
    *,
    echo: bool = False,
    repeat_count: int = 1,
    kind: str = "say",
) -> None:
    p = dict(sess.get(PROFILE_KEY) or init_interaction_profile())
    ot = int(old_state.get("trust", 40) or 0)
    nt = int(new_state.get("trust", 40) or 0)
    trust_delta = nt - ot
    disrespect = str(choice).strip() in DISRESPECT_MENU_PROMPTS

    pos = int(p.get("positive_streak", 0) or 0)
    neg = int(p.get("negative_streak", 0) or 0)
    repair = int(p.get("repair_attempt_streak", 0) or 0)
    sustained = int(p.get("sustained_respect_window", 0) or 0)
    recovery_w = int(p.get("recovery_window", 0) or 0)
    push_ign = int(p.get("pushback_ignored_count", 0) or 0)

    prev_neg = neg

    if disrespect:
        neg = min(20, neg + 1)
        pos = 0
        sustained = 0
        recovery_w = 0
        repair = 0
    elif trust_delta >= 2:
        pos = min(30, pos + 1)
        neg = max(0, neg - 1)
        sustained = min(40, sustained + 1)
        recovery_w = min(40, recovery_w + 1)
        if prev_neg >= 1:
            repair = min(20, repair + 1)
    elif trust_delta > 0:
        pos = min(30, pos + 1) if pos > 0 or trust_delta >= 4 else pos
        neg = max(0, neg - 1)
        sustained = min(40, sustained + 1)
        recovery_w = min(40, recovery_w + 1)
    elif trust_delta <= -4:
        neg = min(20, neg + 1)
        pos = max(0, pos - 1)
        sustained = 0
    elif trust_delta < 0:
        neg = min(20, neg + 1)
        sustained = max(0, sustained - 1)

    if kind == "say" and (echo or repeat_count >= 2):
        push_ign = min(30, push_ign + 1)
    elif kind == "do" and repeat_count >= 2 and str(choice) in PUSHY_ACTIONS:
        push_ign = min(30, push_ign + 1)

    p["positive_streak"] = pos
    p["negative_streak"] = neg
    p["repair_attempt_streak"] = repair
    p["sustained_respect_window"] = sustained
    p["recovery_window"] = recovery_w
    p["pushback_ignored_count"] = push_ign
    sess[PROFILE_KEY] = p


def merge_finisher_bias_tuples(
    a: Optional[Tuple[int, int, int]],
    b: Optional[Tuple[int, int, int]],
) -> Optional[Tuple[int, int, int]]:
    if not a and not b:
        return None
    ax = a or (0, 0, 0)
    bx = b or (0, 0, 0)
    return (ax[0] + bx[0], ax[1] + bx[1], ax[2] + bx[2])


def merge_finisher_tag_weights(
    a: Optional[Mapping[str, float]],
    b: Optional[Mapping[str, float]],
) -> Optional[Dict[str, float]]:
    if not a and not b:
        return None
    out: Dict[str, float] = {}
    for d in (a, b):
        if not d:
            continue
        for k, v in d.items():
            out[k] = out.get(k, 0.0) + float(v)
    return out or None
