# -*- coding: utf-8 -*-
"""Menu / free-text say line composition (bucket, trajectory, menu intelligence)."""

from __future__ import annotations

import os
import random
from typing import Any, Mapping, Optional, Tuple

import streamlit as st

from .archetype_layer import (
    ARCHETYPE_DEBUG_KEY,
    append_archetype_physical_flavor,
    apply_archetype_bucket_nudge,
    resolve_archetype_adjustments,
    resolve_archetype_id,
)
from .behavior_gate import SESSION_MODE_KEY, filter_stall_from_pool_lines
from .brain import choose_bucket, infer_physical_response, infer_tone, infer_vibe
from .callback_memory import (
    CALLBACK_DEBUG_KEY,
    RECENT_PROMPT_MEMORY_KEY,
    apply_callback_bucket_nudge,
    compute_callback_signals,
)
from .canon_prompts import normalize_prompt_key as _normalize_menu_prompt_key
from .free_text import free_text_verbal_response
from .interaction_profile import snapshot_profile
from .menu_responses import (
    filter_generic_engaged_fallback_pool,
    maybe_menu_intelligent_response,
)
from .personality import get_character_dna
from .responses import fill_name_tokens
from .scenario_layer import apply_scenario_bucket_nudge, append_physical_flavor
from .trajectory_layer import (
    TRAJECTORY_DEBUG_KEY,
    append_trajectory_phase_physical_flavor,
    apply_trajectory_bucket_nudge,
    resolve_trajectory_adjustments,
    resolve_trajectory_id,
)
from .first_impression import calibrate_bucket_for_polite_opener
from .memory import init_memory_state
from .utils import clamp_demo_physical_line, quote


def _debug_menu_prompt_trace(
    *,
    selected_prompt: str,
    normalized_key: str,
    canon_lookup_prompt: str,
    final_source: str,
    menu_line: object = None,
) -> None:
    if os.environ.get("SILVER_CROW_DEBUG_MENU") != "1":
        return
    ml = menu_line
    preview = (str(ml)[:160] + "…") if ml is not None and len(str(ml)) > 160 else ml
    print("[MENU_PROMPT_DEBUG] selected_prompt=", repr(selected_prompt), sep="")
    print("[MENU_PROMPT_DEBUG] normalized_prompt_key=", repr(normalized_key), sep="")
    print("[MENU_PROMPT_DEBUG] actual_prompt_used_for_canon=", repr(canon_lookup_prompt), sep="")
    print("[MENU_PROMPT_DEBUG] final_response_source=", repr(final_source), sep="")
    print("[MENU_PROMPT_DEBUG] menu_line_preview=", repr(preview), sep="")


def compose_say_response(
    action_text: str,
    kind: str,
    state: Mapping[str, Any],
    character_name: str,
    scenario_name: str,
    personality: Optional[str] = None,
    free_text_category: Optional[str] = None,
    turns_before_reply: int = 0,
    starting_mood: str = "Neutral",
) -> Tuple[str, str, str, str]:
    """
    Build (verbal, tone, physical, vibe) for a say turn.
    Uses session state for trajectory / archetype / callback debug side effects.
    """
    personality = personality or "Confident"
    if kind == "say" and free_text_category:
        return free_text_verbal_response(
            free_text_category, personality, state, character_name, raw_text=action_text
        )

    tone = infer_tone(state)
    base_phys = append_physical_flavor(infer_physical_response(state), scenario_name)
    physical = base_phys
    vibe = infer_vibe(state)

    if "Sam Howell" in action_text:
        verbal = "Sam Howell? That's a legendary reference."
        return quote(verbal), tone, clamp_demo_physical_line(physical), vibe

    if kind == "say":
        rpc_pre = int((st.session_state.repeat_counts or {}).get(action_text, 0) or 0)
        sig_cb = compute_callback_signals(st.session_state, action_text, rpc_pre)
        st.session_state["_callback_signals"] = sig_cb
        st.session_state[CALLBACK_DEBUG_KEY] = {
            "recent_prompt_memory": list(st.session_state.get(RECENT_PROMPT_MEMORY_KEY) or []),
            "signals": dict(sig_cb),
            "override_used": False,
            "override_type": None,
            "response_source_tag": None,
        }

        bs = st.session_state.get("build_snapshot") or {}
        _aid_res = resolve_archetype_id(bs)
        arch_adj = resolve_archetype_adjustments(
            str(action_text or ""),
            _aid_res,
            str(scenario_name or ""),
            snapshot_profile(st.session_state),
            sig_cb,
        )
        st.session_state["_archetype_adj"] = arch_adj
        st.session_state[ARCHETYPE_DEBUG_KEY] = {
            "resolved_archetype_id": arch_adj.get("archetype_id"),
            "explicit_archetype": bs.get("Archetype"),
            "tier_bonus_applied": list(arch_adj.get("tier_bonus") or (0, 0, 0)),
            "callback_probability_mult": float(arch_adj.get("callback_probability_mult") or 1.0),
            "finisher_tier_bias": list(arch_adj.get("finisher_tier_bias") or (0, 0, 0)),
            "finisher_tag_weights": dict(arch_adj.get("finisher_tag_weights") or {}),
            "influenced": {
                "bucket": False,
                "tier": False,
                "callback_override": False,
                "finisher": False,
            },
        }

        physical = append_archetype_physical_flavor(base_phys, arch_adj)
        traj_reply = resolve_trajectory_adjustments(
            resolve_trajectory_id(bs),
            snapshot_profile(st.session_state),
            state,
            turns_before_this_reply=int(turns_before_reply or 0),
        )
        st.session_state["_trajectory_adj"] = traj_reply
        physical = append_trajectory_phase_physical_flavor(physical, traj_reply)
        tm = st.session_state.get("_trajectory_adj_mods") or {}
        st.session_state[TRAJECTORY_DEBUG_KEY] = {
            "trajectory_id": traj_reply.get("trajectory_id"),
            "trajectory_phase": traj_reply.get("trajectory_phase"),
            "stored_trajectory": bs.get("Trajectory"),
            "trajectory_source": "auto",
            "tier_bonus_reply": list(traj_reply.get("tier_bonus") or (0, 0, 0)),
            "callback_probability_mult": float(traj_reply.get("callback_probability_mult") or 1.0),
            "repetition_murder_threshold": int(traj_reply.get("repetition_murder_threshold", 5)),
            "voice_sharpen_bias": float(traj_reply.get("voice_sharpen_bias") or 0),
            "trajectory_runtime_profile": dict(traj_reply.get("trajectory_runtime_profile") or {}),
            "memory": dict(traj_reply.get("memory_snapshot") or {}),
            "mods_profile": {
                "stats_scaled": bool(tm.get("stats_scaled")),
                "repetition_murder_threshold": int(tm.get("repetition_murder_threshold", 5)),
            },
            "influenced": {
                "bucket": False,
                "state_delta": bool(tm.get("stats_scaled")),
                "shutdown_threshold": bool(tm.get("shutdown_threshold_nondefault")),
                "finisher": False,
                "tier": False,
                "callback_override": False,
            },
        }

        bucket = choose_bucket(state, personality)
        mem_fb = st.session_state.get("conversation_memory") or init_memory_state()
        bucket = calibrate_bucket_for_polite_opener(
            bucket,
            action_text,
            turns_before_reply,
            state,
            get_character_dna(),
            starting_mood,
            scenario_name,
            mem_fb,
        )
        bucket = apply_scenario_bucket_nudge(
            bucket,
            action_text,
            scenario_name,
            snapshot_profile(st.session_state),
        )
        bucket, _arch_bucket_infl = apply_archetype_bucket_nudge(
            bucket,
            arch_adj,
            state,
            str(action_text or ""),
            snapshot_profile(st.session_state),
            str(scenario_name or ""),
        )
        if _arch_bucket_infl:
            _ad0 = st.session_state.get(ARCHETYPE_DEBUG_KEY)
            if isinstance(_ad0, dict):
                _ad0.setdefault("influenced", {})["bucket"] = True

        bucket, _traj_bucket_infl = apply_trajectory_bucket_nudge(
            bucket,
            traj_reply,
            snapshot_profile(st.session_state),
            state,
            int(turns_before_reply or 0),
        )
        if _traj_bucket_infl:
            _td0 = st.session_state.get(TRAJECTORY_DEBUG_KEY)
            if isinstance(_td0, dict):
                _td0.setdefault("influenced", {})["bucket"] = True

        bucket = apply_callback_bucket_nudge(bucket, sig_cb)
        st.session_state["_last_menu_bucket"] = bucket

        menu_line, menu_src = maybe_menu_intelligent_response(
            action_text,
            state,
            personality,
            character_name,
            bucket,
        )
        ui_for_canon = (action_text or "").strip()
        _debug_menu_prompt_trace(
            selected_prompt=str(action_text),
            normalized_key=_normalize_menu_prompt_key(str(action_text)),
            canon_lookup_prompt=ui_for_canon,
            final_source=menu_src,
            menu_line=menu_line,
        )
        if menu_line:
            return quote(fill_name_tokens(menu_line)), tone, clamp_demo_physical_line(physical), vibe

        if action_text == "I disagree with you.":
            branch = {
                "positive": ["Okay—tell me why.", "You don't have to agree with me.", "Say your piece."],
                "neutral": ["Alright.", "Whatever.", "You don't have to believe me."],
                "negative": ["Then disagree.", "Okay, whatever.", "I'm not changing it for you."],
                "severe": ["Shut up, bitch.", "Then keep it moving.", "I heard you. I do not care."],
            }
            return quote(random.choice(branch[bucket])), tone, clamp_demo_physical_line(physical), vibe

        if action_text == "You're wrong.":
            branch = {
                "positive": ["Make your case.", "Okay, interesting. Tell me why.", "I'm listening."],
                "neutral": ["Convince me.", "Say it with reasons.", "Alright, say more."],
                "negative": ["No, you're just talking.", "You can think that.", "That doesn't make you right."],
                "severe": ["Watch your tone.", "You don't know what you're talking about.", "Say that again and this gets worse."],
            }
            return quote(random.choice(branch[bucket])), tone, clamp_demo_physical_line(physical), vibe

    verbal_map = {
        "warm": [
            "I appreciate that.",
            "That actually lands.",
            "Okay—that's fair.",
            "Thanks.",
            "Yeah, that tracks.",
        ],
        "hostile": [
            "Watch your tone.",
            "Okay, whatever.",
            "I heard you.",
            "Try again.",
            "Say that again and see what happens.",
        ],
        "tense": [
            "This is getting uncomfortable.",
            "Be careful right now.",
            "I'm trying to stay calm.",
            "You're pushing it.",
            "I need a second.",
        ],
        "uncertain": [
            "I'm not sure what you mean.",
            "That came across a little strange.",
            "Give me a second.",
            "Wait, what?",
            "Run that by me again.",
        ],
        "engaged": [
            "Okay, now we're getting somewhere.",
            "That's actually interesting.",
            "You have my attention.",
            "Go on.",
            "Yeah?",
        ],
        "neutral": ["Alright.", "Okay.", "Yeah.", "Fine.", "Sure.", "Mhm."],
    }
    if personality == "Confident":
        verbal_map = {
            **verbal_map,
            "warm": ["I hear you.", "That tracks.", "Okay—say more.", "Noted. Keep going."],
            "neutral": ["Alright.", "Yeah.", "So?", "Fine.", "Go on."],
            "engaged": ["Be specific.", "What's your point?", "I'm listening—talk."],
            "tense": ["You're pushing it.", "Ease up.", "Watch how you say that.", "I don't like that angle."],
            "uncertain": ["Run that back.", "What do you mean?", "Say that again—clearly."],
        }
    personality_tweaks = {
        "Shy": {"warm": ["Oh. That's… nice.", "Thanks."], "neutral": ["Okay.", "I guess."]},
        "Aggressive": {"hostile": ["Watch it.", "Don't."], "tense": ["Back off."]},
        "Empathetic": {"warm": ["I really appreciate that.", "That's kind of you."]},
        "Analytical": {"engaged": ["Interesting—say more.", "Where are you going with that?"]},
        "Impulsive": {"hostile": ["What?", "Seriously?"], "engaged": ["Wait, yeah—", "Okay okay—"]},
    }
    mode_fb = st.session_state.get(SESSION_MODE_KEY) or {}
    pool = list(verbal_map.get(tone, verbal_map["neutral"]))
    if personality in personality_tweaks and tone in personality_tweaks[personality]:
        pool = pool + list(personality_tweaks[personality][tone])
    if kind == "say" and not free_text_category:
        pool = filter_generic_engaged_fallback_pool(
            pool,
            action_text,
            str(mode_fb.get("question_type", "")),
        )
    if mode_fb.get("allow_stall_language") is False or mode_fb.get("block_stall_language"):
        pool = filter_stall_from_pool_lines(pool)
    return quote(random.choice(pool)), tone, clamp_demo_physical_line(physical), vibe
