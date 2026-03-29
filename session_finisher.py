# -*- coding: utf-8 -*-
"""Session-scoped finisher selection (archetype + trajectory weighting)."""

from __future__ import annotations

import streamlit as st

from .archetype_layer import (
    ARCHETYPE_DEBUG_KEY,
    resolve_archetype_adjustments,
    resolve_archetype_id,
)
from .finishers import pick_finisher_line
from .interaction_profile import RECENT_FINISHERS_KEY, snapshot_profile
from .trajectory_layer import (
    TRAJECTORY_DEBUG_KEY,
    merge_finisher_bias_tuples,
    merge_finisher_tag_weights,
    resolve_trajectory_adjustments,
    resolve_trajectory_id,
)


def finisher_pick_weighted(shutdown_kind: str, input_text: str = "") -> tuple:
    """Finisher selection with archetype + trajectory tier/tag weighting; enriches pick_meta for debug."""
    bs = st.session_state.get("build_snapshot") or {}
    aid = resolve_archetype_id(bs)
    prof = snapshot_profile(st.session_state)
    sig = st.session_state.get("_callback_signals") or {}
    adj = resolve_archetype_adjustments(
        str(input_text or ""),
        aid,
        str(st.session_state.get("selected_scenario") or ""),
        prof,
        sig,
    )
    traj_fin = resolve_trajectory_adjustments(
        resolve_trajectory_id(bs),
        prof,
        st.session_state.state,
        turns_before_this_reply=int(st.session_state.turns),
    )
    recent = list(st.session_state.get(RECENT_FINISHERS_KEY) or [])
    ftb = merge_finisher_bias_tuples(
        tuple(adj.get("finisher_tier_bias") or (0, 0, 0)),
        tuple(traj_fin.get("finisher_tier_bias") or (0, 0, 0)),
    )
    atw = merge_finisher_tag_weights(
        adj.get("finisher_tag_weights"),
        traj_fin.get("finisher_tag_weights"),
    )
    fin_text, fin_tier, fmeta = pick_finisher_line(
        shutdown_kind,
        prof,
        recent,
        archetype_tier_bias=ftb,
        archetype_tag_weights=atw,
    )
    fmeta = dict(fmeta)
    fmeta["archetype_id"] = adj.get("archetype_id")
    fmeta["archetype_finisher_bias"] = {
        "tier_bias": fmeta.get("archetype_tier_bias"),
        "tag_weights": fmeta.get("archetype_tag_weights"),
    }
    fmeta["trajectory_id"] = traj_fin.get("trajectory_id")
    fmeta["trajectory_finisher_bias"] = {
        "tier_bias": list(traj_fin.get("finisher_tier_bias") or (0, 0, 0)),
        "tag_weights": dict(traj_fin.get("finisher_tag_weights") or {}),
    }
    if any(ftb) or atw:
        _ad = st.session_state.get(ARCHETYPE_DEBUG_KEY)
        if isinstance(_ad, dict):
            _ad.setdefault("influenced", {})["finisher"] = True
    if any(tuple(traj_fin.get("finisher_tier_bias") or (0, 0, 0))) or traj_fin.get("finisher_tag_weights"):
        _td = st.session_state.get(TRAJECTORY_DEBUG_KEY)
        if isinstance(_td, dict):
            _td.setdefault("influenced", {})["finisher"] = True
    return fin_text, fin_tier, fmeta
