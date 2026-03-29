import html
import random
from copy import deepcopy

import streamlit as st

st.set_page_config(
    page_title="Silver Crow",
    page_icon="🪶",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from .config import (
    ACTION_OPTIONS,
    ATTRIBUTES,
    BACKGROUNDS,
    BASE_STATE,
    CHARACTER_INITIATIVES,
    FOLLOW_UP_NODES,
    DEFAULT_SAY_OPTIONS,
    PERSONALITIES,
    PHYSICAL_STATES,
    SAY_OPTIONS,
    SCENARIOS,
    STARTING_MOODS,
    get_say_options_for_scenario,
)

from .utils import (
    _dna_clamp_trait,
    _stable_seed_from_text,
    apply_mods,
    apply_ripple_effects,
    build_state,
    clamp,
    clamp01,
    murdered_state,
    normalize_speech,
    quote,
    sanitize_physical_for_display,
    sanitize_verbal_for_display,
    say_option_stat_mods,
    scale_stat_mods,
    strip_outer_quotes,
)

from .memory import (
    derive_read_on_you,
    init_memory_state,
    memory_add_recent,
    normalize_user_text,
    propose_interaction_trajectory,
    relationship_trend,
    update_conversation_memory,
    update_interaction_trajectory,
)

from .personality import (
    apply_mods_with_identity,
    dna_scaled_mods,
    generate_personality_dna,
    get_character_dna,
    init_identity_state,
    maybe_apply_personal_quirk,
)

from .free_text import (
    CAT_MODE_FREE_TEXT_EFFECTS,
    FREE_TEXT_AGGRESSIVE_HARD_SUBSTR,
    FREE_TEXT_AGGRESSIVE_HARD_WORDS,
    FREE_TEXT_AGGRESSIVE_LIGHT_SUBSTR,
    FREE_TEXT_AGGRESSIVE_MEDIUM_SUBSTR,
    FREE_TEXT_AGGRESSIVE_MEDIUM_WORDS,
    FREE_TEXT_AWKWARD,
    FREE_TEXT_CATEGORY_EFFECTS,
    FREE_TEXT_FRIENDLY,
    FREE_TEXT_JOKING,
    _SPEECH_GREETING_FRAGMENTS,
    aggressive_comeback_response,
    free_text_hard_slur_guard,
    free_text_insult_is_baiting,
    free_text_verbal_response,
    free_text_weak_insult_phrase,
    greeting_or_checkin_overlap,
    interpret_free_text,
    scaled_free_text_category_mods,
    should_use_cat_mode,
    speech_echoes_recent,
)

from .responses import (
    fill_name_tokens,
    outcome_summary,
    relationship_label,
)

from .behavior_gate import (
    EMOTIONAL_PRESSURE,
    LAST_STALL_CHECK_KEY,
    SESSION_MODE_KEY,
    apply_question_type_stat_relief,
    filter_stall_from_pool_lines,
    record_last_response_for_stall_gate,
    resolve_response_mode,
)
from .emotional_subtype import (
    PRESSURE_DEFAULT,
    ROMANTIC_PRESSURE,
    VALIDATION_SEEKING,
    record_menu_emotional_turn,
    subtype_stat_overlay,
)
from .canon_prompts import normalize_prompt_key as _normalize_menu_prompt_key
from .finishers import (
    FINISHER_SESSION_DEBUG_KEY,
    apply_finisher_debug_to_session,
)
from .interaction_profile import (
    PROFILE_KEY,
    RECENT_FINISHERS_KEY,
    init_interaction_profile,
    record_recent_finisher,
    snapshot_profile,
    update_interaction_profile_after_action,
    update_interaction_profile_after_say,
)
from .action_quarks import MOONWALK_STREAK_KEY
from .first_impression import first_impression_verbal_locked
from .archetype_layer import (
    ARCHETYPE_DEBUG_KEY,
    resolve_archetype_id,
)
from .scenario_layer import resolve_scenario_adjustments
from .trajectory_layer import (
    TRAJECTORY_DEBUG_KEY,
    bump_trajectory_progression_memory,
    resolve_initial_trajectory,
    resolve_trajectory_adjustments,
    resolve_trajectory_id,
    scale_relief_mods_for_trajectory,
    scale_stat_mods_for_trajectory,
)
from .callback_memory import (
    CALLBACK_DEBUG_KEY,
    RECENT_CALLBACK_LINES_KEY,
    RECENT_PROMPT_MEMORY_KEY,
)
from .menu_responses import (
    is_low_stakes_personal_prompt,
    register_emotional_menu_prompt,
    reset_menu_emotional_pressure,
    soften_low_stakes_menu_mods,
)
from .response_intent import RECENT_INTENTS_KEY

from .brain import (
    _brain_pick,
    _crow_brain_pick_variant,
    _crow_seed_from_state,
    _maybe_add_hesitation,
    _maybe_spike_moment,
    _micro_variation,
    _normalize_verbal_for_compare,
    _bump_linger_from_attitude,
    choose_bucket,
    crow_brain_apply_to_verbal,
    crow_brain_interpret,
    generate_crow_brain_state,
    infer_physical_response,
    infer_tone,
    infer_vibe,
    init_human_variation_state,
)
from .interaction_response import (
    DEMO_LAST_ACK_TEMPLATE_KEY,
    DEMO_LAST_MENU_SAY_INNER_KEY,
    DEMO_USED_SAY_LINES_KEY,
    ResponseContext,
    build_response,
)
from .session_finisher import finisher_pick_weighted

from .ui import app_css as ui_app_css, attribute_color, format_delta, get_avatar

SPECIAL_ENDING_KEY = "_special_ending"
RELATIONSHIP_OVERRIDE_KEY = "relationship_status_override"


def _refresh_session_trajectory_adj() -> None:
    """Recompute hidden trajectory phase after profile/memory bumps so brain/menu match this turn."""
    bs = st.session_state.get("build_snapshot") or {}
    st.session_state["_trajectory_adj"] = resolve_trajectory_adjustments(
        resolve_trajectory_id(bs),
        snapshot_profile(st.session_state),
        st.session_state.state,
        turns_before_this_reply=int(st.session_state.turns),
    )


def _profile_update_kwargs_from_scenario(prompt: str) -> dict:
    adj = resolve_scenario_adjustments(
        str(prompt or ""),
        st.session_state.selected_scenario,
        snapshot_profile(st.session_state),
    )
    return {
        "escalation_delta_multiplier": float(adj["escalation_delta_multiplier"]),
        "trust_drop_multiplier": float(adj["trust_drop_multiplier"]),
        "repeat_irritation_multiplier": float(adj["repeat_irritation_multiplier"]),
        "public_awkward_boost": bool(adj["public_awkward_boost"]),
    }


def _merged_profile_update_kwargs(prompt: str) -> dict:
    pk = _profile_update_kwargs_from_scenario(prompt)
    tj = st.session_state.get("_trajectory_adj_mods") or {}
    if tj:
        pk["escalation_delta_multiplier"] *= float(tj.get("escalation_delta_mult", 1.0))
        pk["trust_drop_multiplier"] *= float(tj.get("trust_drop_profile_mult", 1.0))
        pk["repeat_irritation_multiplier"] *= float(tj.get("repeat_irritation_mult", 1.0))
    return pk


def _trj_scale_mods(mods):
    if not mods:
        return mods
    tj = st.session_state.get("_trajectory_adj_mods") or {}
    if not tj:
        return mods
    return scale_stat_mods_for_trajectory(mods, tj)


def _trj_relief_mods(mods):
    if not mods:
        return mods
    tj = st.session_state.get("_trajectory_adj_mods") or {}
    if not tj:
        return mods
    return scale_relief_mods_for_trajectory(mods, tj)


def _hero_history_item(history: list) -> dict:
    """
    Newest history entry for the player's last speak/act turn (the `verbal` field answers that input).

    `maybe_character_initiates()` prepends a synthetic 'They asked' row; using history[0] alone then
    shows the wrong prompt (e.g. random initiative) instead of the dropdown line the reply matches.
    """
    if not history:
        return {}
    for item in history:
        t = item.get("type")
        if t in ("You said", "You answered", "You did"):
            return item
    return history[0]


def _scaled_menu_say_mods(choice: str, scale_factor: float = 0.42) -> dict:
    option = SAY_OPTIONS.get(choice)
    if option is None:
        return {}
    sm = dict(scale_stat_mods(say_option_stat_mods(option), scale_factor) or {})
    if sm and is_low_stakes_personal_prompt(choice):
        sm = soften_low_stakes_menu_mods(sm)
    sub = (st.session_state.get(SESSION_MODE_KEY) or {}).get("emotional_subtype", PRESSURE_DEFAULT)
    extra = subtype_stat_overlay(sub)
    for k, v in extra.items():
        if k in sm:
            sm[k] = sm[k] + int(round(v * scale_factor))
        elif v != 0:
            sm[k] = int(round(v * scale_factor))
    return sm


def set_defaults():
    defaults = {
        "page": "builder",
        "character_built": False,
        "state": deepcopy(BASE_STATE),
        "history": [],
        "character_name": "Character",
        "selected_scenario": list(SCENARIOS.keys())[0],
        "turns": 0,
        "build_snapshot": {},
        "last_deltas": {k: 0 for k in ATTRIBUTES},
        "repeat_counts": {},
        "action_repeat_counts": {},
        "conversation_over": False,
        "ending_message": "",
        "draft_name": "",
        "draft_personality": list(PERSONALITIES.keys())[0],
        "draft_background": list(BACKGROUNDS.keys())[0],
        "draft_physical": list(PHYSICAL_STATES.keys())[0],
        "draft_mood": list(STARTING_MOODS.keys())[0],
        "draft_archetype": "Auto",
        "mode": "normal",
        "follow_up_node": None,
        "follow_up_parent": None,
        "last_initiative_turn": -1,
        "free_text_input": "",
        "clear_text": False,
        "recent_speech_norms": [],
        "last_free_text_category": None,
        "aggressive_free_text_count": 0,
        "free_text_cat_mode_active": False,
        "crow_brain": {},
        "crow_brain_last_variant": {},
        "crow_brain_last_attitude": None,
        "crow_brain_step": 0,
        "conversation_memory": init_memory_state(),
        "human_variation": init_human_variation_state(),
        "dna_seed": random.randint(1, 10_000_000),
        "character_dna": {},
        "identity_state": init_identity_state(),
        # Crow Brain debug card: off unless set True in code (no UI toggle).
        "show_debug_crow_brain": False,
        RECENT_INTENTS_KEY: [],
        LAST_STALL_CHECK_KEY: "",
        FINISHER_SESSION_DEBUG_KEY: {},
        PROFILE_KEY: init_interaction_profile(),
        RECENT_FINISHERS_KEY: [],
        RECENT_PROMPT_MEMORY_KEY: [],
        CALLBACK_DEBUG_KEY: {},
        RECENT_CALLBACK_LINES_KEY: [],
        ARCHETYPE_DEBUG_KEY: {},
        TRAJECTORY_DEBUG_KEY: {},
        MOONWALK_STREAK_KEY: 0,
        SPECIAL_ENDING_KEY: None,
        RELATIONSHIP_OVERRIDE_KEY: None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_flow():
    st.session_state.page = "builder"
    st.session_state.character_built = False
    st.session_state.history = []
    st.session_state.turns = 0
    st.session_state.last_deltas = {k: 0 for k in ATTRIBUTES}
    st.session_state.repeat_counts = {}
    st.session_state.action_repeat_counts = {}
    st.session_state.conversation_over = False
    st.session_state.ending_message = ""
    st.session_state.build_snapshot = {}
    st.session_state.selected_scenario = list(SCENARIOS.keys())[0]
    st.session_state.state = deepcopy(BASE_STATE)
    st.session_state.mode = "normal"
    st.session_state.follow_up_node = None
    st.session_state.follow_up_parent = None
    st.session_state.last_initiative_turn = -1
    st.session_state.clear_text = True
    st.session_state.recent_speech_norms = []
    st.session_state.last_free_text_category = None
    st.session_state.aggressive_free_text_count = 0
    st.session_state.free_text_cat_mode_active = False
    st.session_state.crow_brain_last_variant = {}
    st.session_state.crow_brain_last_attitude = None
    st.session_state.crow_brain_step = 0
    st.session_state.conversation_memory = init_memory_state()
    st.session_state.human_variation = init_human_variation_state()
    st.session_state.character_dna = {}
    st.session_state.identity_state = init_identity_state()
    st.session_state[RECENT_INTENTS_KEY] = []
    st.session_state[LAST_STALL_CHECK_KEY] = ""
    st.session_state[FINISHER_SESSION_DEBUG_KEY] = {}
    st.session_state[PROFILE_KEY] = init_interaction_profile()
    st.session_state[RECENT_FINISHERS_KEY] = []
    st.session_state[RECENT_PROMPT_MEMORY_KEY] = []
    st.session_state[CALLBACK_DEBUG_KEY] = {}
    st.session_state[RECENT_CALLBACK_LINES_KEY] = []
    st.session_state[ARCHETYPE_DEBUG_KEY] = {}
    st.session_state[TRAJECTORY_DEBUG_KEY] = {}
    st.session_state[MOONWALK_STREAK_KEY] = 0
    st.session_state[SPECIAL_ENDING_KEY] = None
    st.session_state[RELATIONSHIP_OVERRIDE_KEY] = None
    st.session_state[DEMO_LAST_MENU_SAY_INNER_KEY] = {}
    st.session_state[DEMO_USED_SAY_LINES_KEY] = {}
    st.session_state[DEMO_LAST_ACK_TEMPLATE_KEY] = {}
    reset_menu_emotional_pressure()


def maybe_character_initiates():
    """Sometimes the character drives: asks a question, shifts topic."""
    if st.session_state.conversation_over:
        return
    if st.session_state.mode == "follow_up":
        return
    if st.session_state.turns < 2:
        return
    if st.session_state.turns == st.session_state.last_initiative_turn:
        return
    if random.random() > 0.18:  # 18% chance after eligible turns
        return
    state = st.session_state.state
    if state["anger"] > 65 or state["trust"] < 15:  # don't initiate when hostile
        return
    q, mods, physical, vibe = random.choice(CHARACTER_INITIATIVES)
    scale = SCENARIOS[st.session_state.selected_scenario]["sensitivity"]
    apply_mods_with_identity(st.session_state.state, mods, scale, kind="do")
    st.session_state.last_initiative_turn = st.session_state.turns
    brain = crow_brain_interpret(
        st.session_state.state,
        user_input=q,
        kind="character_initiative",
        repeat_count=st.session_state.turns,
    )
    st.session_state.crow_brain = brain
    initiative_entry = {
        "type": "They asked",
        "input": "",
        "verbal": quote(q),
        "tone": brain["tone"],
        "physical": brain["physical_reaction"],
        "vibe": brain["vibe"],
    }
    hist = st.session_state.history
    # Keep the player's latest turn at history[0] so the UI and trace match the real prompt/reply pair.
    if hist and hist[0].get("type") in ("You said", "You answered", "You did"):
        hist.insert(1, initiative_entry)
    else:
        hist.insert(0, initiative_entry)


def start_scenario(name):
    st.session_state.character_name = st.session_state.draft_name.strip() or "Character"
    st.session_state.selected_scenario = name
    st.session_state.state = build_state(
        st.session_state.draft_personality,
        st.session_state.draft_background,
        st.session_state.draft_physical,
        st.session_state.draft_mood,
        name,
    )
    st.session_state.character_dna = generate_personality_dna(
        st.session_state.draft_personality,
        st.session_state.draft_background,
        st.session_state.draft_physical,
        st.session_state.draft_mood,
        st.session_state.character_name,
        jitter_seed=st.session_state.get("dna_seed", 0),
    )
    st.session_state.identity_state = init_identity_state()
    st.session_state.character_built = True
    st.session_state.history = []
    st.session_state.turns = 0
    st.session_state.last_deltas = {k: 0 for k in ATTRIBUTES}
    st.session_state.repeat_counts = {}
    st.session_state.action_repeat_counts = {}
    st.session_state.conversation_over = False
    st.session_state.ending_message = ""
    st.session_state.mode = "normal"
    st.session_state.follow_up_node = None
    st.session_state.follow_up_parent = None
    st.session_state.last_initiative_turn = -1
    st.session_state.clear_text = True
    st.session_state.recent_speech_norms = []
    st.session_state.last_free_text_category = None
    st.session_state.aggressive_free_text_count = 0
    st.session_state.free_text_cat_mode_active = False
    st.session_state.crow_brain = {}
    st.session_state.crow_brain_last_variant = {}
    st.session_state.crow_brain_last_attitude = None
    st.session_state.crow_brain_step = 0
    st.session_state.conversation_memory = init_memory_state()
    st.session_state.human_variation = init_human_variation_state()
    _snap_for_arch = {
        "Personality": st.session_state.draft_personality,
        "Archetype": st.session_state.get("draft_archetype", "Auto"),
    }
    _resolved_arch = resolve_archetype_id(_snap_for_arch)
    _traj_seed = _stable_seed_from_text(
        "|".join(
            (
                str(st.session_state.draft_personality),
                str(st.session_state.draft_background),
                str(st.session_state.draft_mood),
                str(st.session_state.get("draft_archetype", "Auto")),
                str(st.session_state.character_name),
                str(_resolved_arch),
            )
        )
    )
    _resolved_traj = resolve_initial_trajectory(
        st.session_state.draft_personality,
        _resolved_arch,
        st.session_state.draft_mood,
        st.session_state.draft_background,
        rng=random.Random(_traj_seed),
    )
    st.session_state.build_snapshot = {
        "Personality": st.session_state.draft_personality,
        "Background": st.session_state.draft_background,
        "Physical": st.session_state.draft_physical,
        "Mood": st.session_state.draft_mood,
        "Environment": name,
        "Archetype": st.session_state.get("draft_archetype", "Auto"),
        "Trajectory": _resolved_traj,
    }
    st.session_state[RECENT_INTENTS_KEY] = []
    st.session_state[LAST_STALL_CHECK_KEY] = ""
    st.session_state[FINISHER_SESSION_DEBUG_KEY] = {}
    st.session_state[PROFILE_KEY] = init_interaction_profile()
    st.session_state[RECENT_FINISHERS_KEY] = []
    st.session_state[RECENT_PROMPT_MEMORY_KEY] = []
    st.session_state[CALLBACK_DEBUG_KEY] = {}
    st.session_state[RECENT_CALLBACK_LINES_KEY] = []
    st.session_state[ARCHETYPE_DEBUG_KEY] = {}
    st.session_state[TRAJECTORY_DEBUG_KEY] = {}
    st.session_state[MOONWALK_STREAK_KEY] = 0
    st.session_state[SPECIAL_ENDING_KEY] = None
    st.session_state[RELATIONSHIP_OVERRIDE_KEY] = "neutral"
    st.session_state[SESSION_MODE_KEY] = {}
    st.session_state[DEMO_LAST_MENU_SAY_INNER_KEY] = {}
    st.session_state[DEMO_USED_SAY_LINES_KEY] = {}
    st.session_state[DEMO_LAST_ACK_TEMPLATE_KEY] = {}
    reset_menu_emotional_pressure()
    st.session_state.page = "interact"


def trigger_overstimulated_ending(choice, kind, old_state):
    """Fourth consecutive moonwalk — full-screen secret ending (no VIBES MURDERED / finisher bank)."""
    for k in ATTRIBUTES:
        st.session_state.state[k] = 100
    st.session_state.last_deltas = {k: 0 for k in ATTRIBUTES}
    st.session_state.turns += 1
    st.session_state.conversation_over = True
    st.session_state.ending_message = "OVERSTIMULATED"
    st.session_state[SPECIAL_ENDING_KEY] = "overstimulated"
    st.session_state.mode = "normal"
    st.session_state.follow_up_node = None
    st.session_state.follow_up_parent = None
    st.session_state.history.insert(0, {
        "type": "You said" if kind == "say" else "You did",
        "input": choice,
        "verbal": quote("OVERSTIMULATED"),
        "tone": "electric",
        "physical": "overstimulated",
        "vibe": "overstimulated",
    })
    record_last_response_for_stall_gate(st.session_state.history[0]["verbal"])


def murder_vibes(
    verbal_ignored,
    input_text,
    kind,
    physical_override=None,
    shutdown_kind: str = "generic_shutdown",
    *,
    precomputed_finisher=None,
):
    """
    Hard shutdown (VIBES MURDERED). Hero line from finisher bank unless precomputed_finisher is set.
    """
    if precomputed_finisher is not None:
        finisher_text, fin_tier, fmeta = precomputed_finisher
        fmeta = dict(fmeta)
    else:
        finisher_text, fin_tier, fmeta = finisher_pick_weighted(shutdown_kind, str(input_text or ""))
        fmeta = dict(fmeta)
    record_recent_finisher(st.session_state, fmeta.get("canonical_text") or finisher_text)
    displayed = quote(finisher_text)
    apply_finisher_debug_to_session(
        st.session_state,
        finisher_text,
        fin_tier,
        shutdown_kind,
        pick_meta=fmeta,
        interaction_profile_snapshot=snapshot_profile(st.session_state),
    )
    old_state = deepcopy(st.session_state.state)
    murdered_state(st.session_state.state)
    st.session_state.last_deltas = {k: st.session_state.state[k] - old_state[k] for k in ATTRIBUTES}
    st.session_state.conversation_over = True
    st.session_state.ending_message = "VIBES MURDERED"
    st.session_state[SPECIAL_ENDING_KEY] = None
    st.session_state.mode = "normal"
    st.session_state.follow_up_node = None
    st.session_state.follow_up_parent = None
    _phys = physical_override
    if _phys is None or not str(_phys).strip():
        _phys = "the vibe snaps in half"
    st.session_state.history.insert(0, {
        "type": "You said" if kind == "say" else "You did",
        "input": input_text,
        "verbal": displayed,
        "tone": "furious",
        "physical": _phys,
        "vibe": "murdered",
    })


def enter_follow_up(node_key, parent_label=None):
    st.session_state.mode = "follow_up"
    st.session_state.follow_up_node = node_key
    st.session_state.follow_up_parent = parent_label


def resolve_follow_up_choice(option_text, mods, verbal, next_node):
    if st.session_state.conversation_over:
        return
    scale = SCENARIOS[st.session_state.selected_scenario]["sensitivity"]
    old_state = deepcopy(st.session_state.state)
    apply_mods_with_identity(st.session_state.state, mods, scale, kind="follow_up")
    st.session_state.last_deltas = {k: st.session_state.state[k] - old_state[k] for k in ATTRIBUTES}
    st.session_state.turns += 1

    if next_node == "END_MURDER":
        update_interaction_profile_after_say(
            st.session_state,
            option_text,
            1,
            False,
            old_state,
            st.session_state.state,
            **_profile_update_kwargs_from_scenario(option_text),
        )
        murder_vibes(verbal, option_text, "say", shutdown_kind="followup_murder_shutdown")
        return

    mem = st.session_state.get("conversation_memory") or init_memory_state()
    # Track follow-up answers for light contradiction/suspicion heuristics
    mem["followup_answers"] = (mem.get("followup_answers") or []) + [str(option_text)]
    mem["followup_answers"] = mem["followup_answers"][-8:]
    # Simple contradiction: praise then "never listened" / "idk" in same arc
    low = str(option_text).lower()
    if "i don't listen" in low or "never listened" in low:
        if any("they're great" in str(x).lower() or "they are great" in str(x).lower() for x in mem["followup_answers"][:-1]):
            mem["inconsistency_score"] = clamp(mem.get("inconsistency_score", 0) + 6, 0, 100)
            mem["honesty_score"] = clamp(mem.get("honesty_score", 50) - 4, 0, 100)
    if any(x in low for x in ("i don't know", "whatever", "you decide")):
        mem["pressure_score"] = clamp(mem.get("pressure_score", 0) + 1, 0, 100)
        mem["honesty_score"] = clamp(mem.get("honesty_score", 50) - 1, 0, 100)
    st.session_state.conversation_memory = mem
    update_conversation_memory(mem, option_text, "follow_up", False, None, 1, scenario_name=st.session_state.selected_scenario)

    st.session_state[SESSION_MODE_KEY] = resolve_response_mode(option_text, st.session_state.state)

    brain = crow_brain_interpret(
        st.session_state.state,
        user_input=option_text,
        kind="follow_up",
        repeat_count=st.session_state.turns,
    )
    st.session_state.crow_brain = brain
    tone = brain["tone"]
    vibe = brain["vibe"]
    physical = brain["physical_reaction"]
    verbal = crow_brain_apply_to_verbal(
        verbal,
        brain,
        st.session_state.state,
        user_input=option_text,
        turns_before_reply=st.session_state.turns,
    )
    st.session_state.history.insert(0, {
        "type": "You answered",
        "input": option_text,
        "verbal": verbal,
        "tone": tone,
        "physical": physical,
        "vibe": vibe,
    })
    record_last_response_for_stall_gate(verbal)

    if next_node:
        enter_follow_up(next_node, st.session_state.follow_up_parent)
    else:
        st.session_state.mode = "normal"
        st.session_state.follow_up_node = None
        st.session_state.follow_up_parent = None


def maybe_start_follow_up(choice):
    personality = st.session_state.build_snapshot.get("Personality", "Confident")
    bucket = choose_bucket(st.session_state.state, personality)
    if choice == "Do you want to go on a date?":
        if bucket == "positive":
            st.session_state.history.insert(0, {
                "type": "You said",
                "input": choice,
                "verbal": quote("Yeah, I'd like that. Where should we go?"),
                "tone": "warm",
                "physical": "leans in and actually seems interested",
                "vibe": "promising",
            })
            enter_follow_up("date_where", choice)
            return True
        if bucket == "neutral":
            st.session_state.history.insert(0, {
                "type": "You said",
                "input": choice,
                "verbal": quote("Sure. What did you have in mind?"),
                "tone": "neutral",
                "physical": "keeps posture relaxed but waits to hear your answer",
                "vibe": "open but evaluating",
            })
            enter_follow_up("date_neutral", choice)
            return True
    if choice == "Would you like to buy my jetski?":
        st.session_state.history.insert(0, {
            "type": "You said",
            "input": choice,
            "verbal": quote("Hmm… how much?"),
            "tone": "engaged",
            "physical": "raises an eyebrow and actually considers it",
            "vibe": "curious but suspicious",
        })
        enter_follow_up("jetski_price", choice)
        return True
    if choice == "Is Playboi Carti overrated?":
        if random.random() < 0.35:
            st.session_state.history.insert(0, {
                "type": "You said",
                "input": choice,
                "verbal": quote("Forget Carti for a second. Do you like Nirvana?"),
                "tone": "engaged",
                "physical": "tilts head and waits for your take",
                "vibe": "suddenly more specific",
            })
            enter_follow_up("nirvana_question", choice)
        else:
            bucket = choose_bucket(st.session_state.state)
            if bucket == "positive":
                verbal = quote("Carti has moments. Overrated is too lazy.")
            elif bucket == "neutral":
                verbal = quote("Sometimes yes. Sometimes people just hate fun.")
            elif bucket == "negative":
                verbal = quote("Probably. But I don't trust your taste either.")
            else:
                verbal = quote("What do you think this is? I'm the one asking the questions. Give me your opinion on Carti before I freak out.")
            st.session_state.history.insert(0, {
                "type": "You said",
                "input": choice,
                "verbal": verbal,
                "tone": infer_tone(st.session_state.state),
                "physical": "furrows brow and waits for your answer",
                "vibe": "specific and slightly combative",
            })
        return True
    return False


def process_interaction(choice, kind, is_free_text=False):
    if st.session_state.conversation_over:
        return

    if (
        st.session_state.get(RELATIONSHIP_OVERRIDE_KEY) == "neutral"
        and int(st.session_state.turns or 0) >= 1
    ):
        st.session_state[RELATIONSHIP_OVERRIDE_KEY] = None

    st.session_state[SESSION_MODE_KEY] = {}

    scale = SCENARIOS[st.session_state.selected_scenario]["sensitivity"]
    old_state = deepcopy(st.session_state.state)

    if kind == "say":
        bs_tr = st.session_state.get("build_snapshot") or {}
        traj_mods = resolve_trajectory_adjustments(
            resolve_trajectory_id(bs_tr),
            snapshot_profile(st.session_state),
            old_state,
            turns_before_this_reply=st.session_state.turns,
        )
        st.session_state["_trajectory_adj_mods"] = traj_mods
        murder_thresh = int(traj_mods.get("repetition_murder_threshold", 5))

        free_category = None
        cat_mode = False
        norm = normalize_speech(choice)
        recent_list = list(st.session_state.get("recent_speech_norms", []))
        prev_free = st.session_state.get("last_free_text_category")
        if is_free_text:
            cat_raw = interpret_free_text(choice)
            prev_fc = st.session_state.get("last_free_text_category")
            n_aggr_pre = st.session_state.get("aggressive_free_text_count", 0)
            free_category = cat_raw
            if (
                prev_fc
                and str(prev_fc).startswith("aggressive_")
                and free_category
                and str(free_category).startswith("aggressive_")
            ):
                bumped = {
                    "aggressive_light": "aggressive_medium",
                    "aggressive_medium": "aggressive_hard",
                }.get(free_category, free_category)
                if bumped == "aggressive_hard" and free_text_weak_insult_phrase(choice):
                    free_category = "aggressive_medium"
                else:
                    free_category = bumped
            cat_mode = should_use_cat_mode(choice, free_category, cat_raw, prev_fc, n_aggr_pre, recent_list)
        echo = speech_echoes_recent(
            norm, recent_list, is_free_text, prev_free, free_category if is_free_text else None
        )

        prev_count = int(st.session_state.repeat_counts.get(choice, 0))
        repeat_count_for_response = prev_count
        stored_count = prev_count + 1
        st.session_state.repeat_counts[choice] = stored_count

        is_polite_opener = (
            (not is_free_text)
            and choice in {
                "Hello, nice to meet you.",
                "Nice to meet you",
                "Hey, how are you?",
                "What's up?",
            }
        )

        local_murder_thresh = murder_thresh

        # Polite openers should not insta-die in the demo.
        if is_polite_opener:
            local_murder_thresh = max(int(murder_thresh), 5)
        elif not is_free_text:
            local_murder_thresh = min(int(murder_thresh), 4)

        effective_murder_repeat = max(0, int(local_murder_thresh) - 1)

        mem = st.session_state.get("conversation_memory") or init_memory_state()
        update_conversation_memory(
            mem,
            choice,
            kind,
            is_free_text,
            free_category if is_free_text else None,
            stored_count,
            scenario_name=st.session_state.selected_scenario,
        )
        st.session_state.conversation_memory = mem

        st.session_state["_speech_echo_this_turn"] = echo
        st.session_state[SESSION_MODE_KEY] = resolve_response_mode(choice, st.session_state.state)

        _soft_rep = (st.session_state.get(SESSION_MODE_KEY) or {}).get("soft_echo_penalty")
        if stored_count == 2:
            r2 = {"trust": -8, "confusion": 6, "happiness": -4}
            if _soft_rep:
                r2 = {"trust": -5, "confusion": 2, "happiness": -2}
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(r2), scale, kind=kind)
        elif stored_count == 3:
            r3 = {"trust": -14, "anger": 8, "stress": 6, "happiness": -8}
            if _soft_rep:
                r3 = {"trust": -8, "anger": 4, "stress": 3, "happiness": -4}
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(r3), scale, kind=kind)
        elif stored_count == 4:
            r4 = {"trust": -18, "anger": 12, "stress": 10, "interest": -10, "happiness": -10}
            if _soft_rep:
                r4 = {"trust": -10, "anger": 6, "stress": 5, "interest": -5, "happiness": -5}
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(r4), scale, kind=kind)
        elif stored_count >= 5:
            r5 = {"trust": -24, "anger": 18, "stress": 16, "interest": -18, "happiness": -12}
            if _soft_rep:
                r5 = {"trust": -12, "anger": 8, "stress": 8, "interest": -8, "happiness": -6}
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(r5), scale, kind=kind)

        echo_mods = {"trust": -5, "confusion": 4, "stress": 2, "happiness": -2}
        if (st.session_state.get(SESSION_MODE_KEY) or {}).get("soft_echo_penalty"):
            echo_mods = {"trust": -3, "confusion": 1, "stress": 0, "happiness": -1}

        sassy_free = bool(
            is_free_text
            and (
                cat_mode
                or (free_category and str(free_category).startswith("aggressive_"))
            )
        )
        if stored_count == 1:
            if echo:
                apply_mods_with_identity(st.session_state.state, _trj_scale_mods(echo_mods), scale, kind=kind)
                if is_free_text:
                    if cat_mode:
                        base_fc = dict(CAT_MODE_FREE_TEXT_EFFECTS)
                    else:
                        base_fc = scaled_free_text_category_mods(free_category)
                    scaled = scale_stat_mods(base_fc, 0.42)
                    apply_mods_with_identity(
                        st.session_state.state,
                        _trj_scale_mods(scaled),
                        scale,
                        kind=kind,
                        free_text_category=free_category,
                        sassy_comeback=sassy_free,
                    )
                else:
                    sm = _scaled_menu_say_mods(choice)
                    if sm:
                        apply_mods_with_identity(st.session_state.state, _trj_scale_mods(sm), scale, kind=kind)
            elif is_free_text:
                if cat_mode:
                    mods = dict(CAT_MODE_FREE_TEXT_EFFECTS)
                else:
                    mods = scaled_free_text_category_mods(free_category)
                apply_mods_with_identity(
                    st.session_state.state,
                    _trj_scale_mods(mods),
                    scale,
                    kind=kind,
                    free_text_category=free_category,
                    sassy_comeback=sassy_free,
                )
            else:
                sm_menu = _scaled_menu_say_mods(choice)
                if sm_menu:
                    apply_mods_with_identity(st.session_state.state, _trj_scale_mods(sm_menu), scale, kind=kind)
        else:
            repeat_drag = {"happiness": -3, "trust": -4, "stress": 3, "anger": 3}
            if stored_count >= 3:
                repeat_drag["interest"] = -4
            if (st.session_state.get(SESSION_MODE_KEY) or {}).get("soft_echo_penalty"):
                repeat_drag = {"happiness": -2, "trust": -2, "stress": 1, "anger": 1}
                if stored_count >= 3:
                    repeat_drag["interest"] = -2
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(repeat_drag), scale, kind=kind)

        _rm = st.session_state.get(SESSION_MODE_KEY) or {}
        if _rm.get("apply_stat_relief"):
            apply_question_type_stat_relief(
                st.session_state.state, _rm.get("question_type", ""), scale
            )
        if _rm.get("grounded_inquiry_relief"):
            apply_mods(
                st.session_state.state,
                _trj_relief_mods({"confusion": -10, "stress": -4}),
                scale,
            )

        update_interaction_profile_after_say(
            st.session_state,
            choice,
            stored_count,
            echo,
            old_state,
            st.session_state.state,
            **_merged_profile_update_kwargs(choice),
        )
        bump_trajectory_progression_memory(
            st.session_state,
            choice,
            old_state,
            st.session_state.state,
            echo=echo,
            repeat_count=stored_count,
            kind="say",
        )

        def record_speech_memory():
            rl = list(st.session_state.get("recent_speech_norms", []))
            rl.append(norm)
            st.session_state.recent_speech_norms = rl[-4:]
            if is_free_text:
                st.session_state.last_free_text_category = free_category
                if free_category and str(free_category).startswith("aggressive_"):
                    st.session_state.aggressive_free_text_count = int(
                        st.session_state.get("aggressive_free_text_count", 0)
                    ) + 1

        personality = st.session_state.build_snapshot.get("Personality", "Confident")

        if repeat_count_for_response >= effective_murder_repeat:
            record_speech_memory()
            resp_rep = build_response(
                ResponseContext(
                    kind="say",
                    prompt=choice,
                    repeat_count=repeat_count_for_response,
                    state=st.session_state.state,
                    state_before_mods=old_state,
                    personality=personality,
                    scenario_name=st.session_state.selected_scenario,
                    character_name=st.session_state.character_name,
                    turns_before_reply=st.session_state.turns,
                    is_free_text=is_free_text,
                    free_text_category=free_category,
                    murder_threshold=effective_murder_repeat,
                    speech_echo=echo,
                    starting_mood=(st.session_state.build_snapshot or {}).get("Mood", "Neutral"),
                    run_crow_brain=False,
                )
            )
            murder_vibes(
                "",
                choice,
                kind,
                physical_override=resp_rep.physical,
                shutdown_kind=resp_rep.shutdown_kind or "repetition_shutdown",
                precomputed_finisher=resp_rep.precomputed_finisher,
            )
            return

        if is_free_text:
            st.session_state.crow_brain = crow_brain_interpret(
                st.session_state.state,
                user_input=choice,
                kind=kind,
                free_text_category=free_category if is_free_text else None,
                repeat_count=repeat_count_for_response,
            )
            _brain_now = st.session_state.get("crow_brain") or {}
            st.session_state["_fi_lock_verbal"] = first_impression_verbal_locked(
                choice,
                st.session_state.turns,
                st.session_state.state,
                _brain_now.get("attitude", "guarded"),
            )
        else:
            st.session_state.crow_brain = {}

        if maybe_start_follow_up(choice):
            record_speech_memory()
            st.session_state.last_deltas = {k: st.session_state.state[k] - old_state[k] for k in ATTRIBUTES}
            st.session_state.turns += 1
            return

        st.session_state.free_text_cat_mode_active = bool(cat_mode)
        try:
            resp = build_response(
                ResponseContext(
                    kind="say",
                    prompt=choice,
                    repeat_count=repeat_count_for_response,
                    state=st.session_state.state,
                    state_before_mods=old_state,
                    personality=personality,
                    scenario_name=st.session_state.selected_scenario,
                    character_name=st.session_state.character_name,
                    turns_before_reply=st.session_state.turns,
                    is_free_text=is_free_text,
                    free_text_category=free_category,
                    murder_threshold=effective_murder_repeat,
                    speech_echo=echo,
                    starting_mood=(st.session_state.build_snapshot or {}).get("Mood", "Neutral"),
                    run_crow_brain=False,
                )
            )
        finally:
            st.session_state.free_text_cat_mode_active = False

        record_speech_memory()

        if resp.ended and resp.shutdown_kind == "verbal_boundary_shutdown" and resp.precomputed_finisher:
            ft, fb_tier, fb_meta = resp.precomputed_finisher
            st.session_state.last_deltas = {k: st.session_state.state[k] - old_state[k] for k in ATTRIBUTES}
            st.session_state.turns += 1
            st.session_state.history.insert(0, {
                "type": "You said",
                "input": choice,
                "verbal": resp.verbal,
                "tone": resp.tone,
                "physical": resp.physical,
                "vibe": resp.vibe,
            })
            record_recent_finisher(st.session_state, fb_meta.get("canonical_text") or ft)
            apply_finisher_debug_to_session(
                st.session_state,
                ft,
                fb_tier,
                "verbal_boundary_shutdown",
                murdered_override=False,
                pick_meta=fb_meta,
                interaction_profile_snapshot=snapshot_profile(st.session_state),
            )
            record_last_response_for_stall_gate(resp.verbal)
            st.session_state.conversation_over = True
            st.session_state.ending_message = resp.ending_message
            st.session_state[SPECIAL_ENDING_KEY] = None
            st.session_state.mode = "normal"
            st.session_state.follow_up_node = None
            st.session_state.follow_up_parent = None
            return

        st.session_state.last_deltas = {k: st.session_state.state[k] - old_state[k] for k in ATTRIBUTES}
        st.session_state.turns += 1
        st.session_state.history.insert(0, {
            "type": "You said",
            "input": choice,
            "verbal": resp.verbal,
            "tone": resp.tone,
            "physical": resp.physical,
            "vibe": resp.vibe,
        })
        record_last_response_for_stall_gate(resp.verbal)
        if not is_free_text:
            _mt = st.session_state.get(SESSION_MODE_KEY) or {}
            _esub = _mt.get("emotional_subtype", PRESSURE_DEFAULT)
            record_menu_emotional_turn(choice, str(_esub))
            if _mt.get("question_type") == EMOTIONAL_PRESSURE or _esub in (
                ROMANTIC_PRESSURE,
                VALIDATION_SEEKING,
            ):
                register_emotional_menu_prompt(choice)
        maybe_character_initiates()

    else:
        bs_tr = st.session_state.get("build_snapshot") or {}
        traj_mods = resolve_trajectory_adjustments(
            resolve_trajectory_id(bs_tr),
            snapshot_profile(st.session_state),
            old_state,
            turns_before_this_reply=st.session_state.turns,
        )
        st.session_state["_trajectory_adj_mods"] = traj_mods

        count = st.session_state.action_repeat_counts.get(choice, 0) + 1
        st.session_state.action_repeat_counts[choice] = count
        if choice != "Hit the moonwalk":
            st.session_state[MOONWALK_STREAK_KEY] = 0
        else:
            st.session_state[MOONWALK_STREAK_KEY] = int(st.session_state.get(MOONWALK_STREAK_KEY, 0)) + 1
        _mw_streak = int(st.session_state.get(MOONWALK_STREAK_KEY, 0))
        mem = st.session_state.get("conversation_memory") or init_memory_state()
        # Actions can apply pressure/awkward residue too.
        if choice in {"Step closer", "Stare blankly", "Interrupt", "Raise voice"}:
            mem["pressure_score"] = clamp(mem.get("pressure_score", 0) + (2 if choice == "Step closer" else 3), 0, 100)
            mem["awkward_score"] = clamp(mem.get("awkward_score", 0) + (2 if choice == "Stare blankly" else 1), 0, 100)
        if choice == "Smile" and mem.get("last_turn_was_rude"):
            mem["inconsistency_score"] = clamp(mem.get("inconsistency_score", 0) + 2, 0, 100)
            mem["honesty_score"] = clamp(mem.get("honesty_score", 50) - 1, 0, 100)
        st.session_state.conversation_memory = mem
        # Repeated Smile: happiness drops as it gets weird (count 2+)
        if choice == "Smile" and count >= 2:
            smile_repeat_mods = {
                2: {"confusion": 6, "happiness": -6, "trust": -2},
                3: {"trust": -10, "stress": 6, "happiness": -8, "anger": 4},
                4: {"trust": -14, "anger": 10, "stress": 10, "happiness": -12},
            }
            mods = smile_repeat_mods.get(count, {"trust": -18, "anger": 14, "stress": 12, "happiness": -14})
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(mods), scale, kind=kind)
        # Step closer repeated: negative reaction = happiness down, anger up, trust down, stress up
        elif choice == "Step closer" and count >= 2:
            step_closer_mods = {
                2: {"happiness": -6, "anger": 6, "trust": -8, "stress": 6},   # "Woah there" - tense
                3: {"happiness": -10, "anger": 12, "trust": -12, "stress": 10},  # "I said back up" - hostile
            }
            mods = step_closer_mods.get(count, {"happiness": -12, "anger": 14, "trust": -14, "stress": 12})
            apply_mods_with_identity(st.session_state.state, _trj_scale_mods(mods), scale, kind=kind)
        else:
            apply_mods_with_identity(
                st.session_state.state,
                _trj_scale_mods(dict(ACTION_OPTIONS[choice])),
                scale,
                kind=kind,
            )
        update_interaction_profile_after_action(
            st.session_state,
            choice,
            count,
            old_state,
            st.session_state.state,
            **_merged_profile_update_kwargs(""),
        )
        bump_trajectory_progression_memory(
            st.session_state,
            choice,
            old_state,
            st.session_state.state,
            echo=False,
            repeat_count=count,
            kind="do",
        )
        _refresh_session_trajectory_adj()
        personality = st.session_state.build_snapshot.get("Personality", "Confident")
        resp = build_response(
            ResponseContext(
                kind="do",
                prompt=choice,
                repeat_count=count,
                state=st.session_state.state,
                state_before_mods=old_state,
                personality=personality,
                scenario_name=st.session_state.selected_scenario,
                character_name=st.session_state.character_name,
                turns_before_reply=st.session_state.turns,
                moonwalk_streak=_mw_streak,
            )
        )

        if resp.ended and resp.special_ending == "overstimulated":
            trigger_overstimulated_ending(choice, kind, old_state)
            return

        if resp.ended and resp.apply_murdered_state:
            murder_vibes(
                "",
                choice,
                kind,
                physical_override=resp.physical,
                shutdown_kind=resp.shutdown_kind or "generic_shutdown",
                precomputed_finisher=resp.precomputed_finisher,
            )
            return

        st.session_state.last_deltas = {k: st.session_state.state[k] - old_state[k] for k in ATTRIBUTES}
        st.session_state.turns += 1
        st.session_state.history.insert(0, {
            "type": "You did",
            "input": choice,
            "verbal": resp.verbal,
            "tone": resp.tone,
            "physical": resp.physical,
            "vibe": resp.vibe,
        })
        if resp.moonwalk_universe_rulerz:
            for k in ATTRIBUTES:
                st.session_state.state[k] = 100
            st.session_state[RELATIONSHIP_OVERRIDE_KEY] = "Rulerz of the Universe"
        record_last_response_for_stall_gate(resp.verbal)
        maybe_character_initiates()


set_defaults()
ui_app_css(st)

if st.session_state.page == "builder":
    st.markdown('<div class="main-title">Silver Crow</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Create the person. Choose the moment. Step in.</div>', unsafe_allow_html=True)

    left, right = st.columns([1.12, 0.88], gap="medium")
    with left:
        st.markdown('<div class="builder-title">Character builder</div>', unsafe_allow_html=True)
        st.markdown('<div class="builder-sub">Who are you meeting?</div>', unsafe_allow_html=True)
        st.session_state.draft_name = st.text_input("Character name", value=st.session_state.draft_name)
        st.session_state.draft_personality = st.selectbox(
            "Personality type",
            list(PERSONALITIES.keys()),
            index=list(PERSONALITIES.keys()).index(st.session_state.draft_personality),
        )
        st.session_state.draft_background = st.selectbox(
            "Background",
            list(BACKGROUNDS.keys()),
            index=list(BACKGROUNDS.keys()).index(st.session_state.draft_background),
        )
        st.session_state.draft_physical = st.selectbox(
            "Physical state",
            list(PHYSICAL_STATES.keys()),
            index=list(PHYSICAL_STATES.keys()).index(st.session_state.draft_physical),
        )
        st.session_state.draft_mood = st.selectbox(
            "Starting mood",
            list(STARTING_MOODS.keys()),
            index=list(STARTING_MOODS.keys()).index(st.session_state.draft_mood),
        )
        st.session_state.draft_archetype = "Auto"
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Continue to scenario", use_container_width=True):
                st.session_state.page = "scenario"
                st.rerun()
        with c2:
            if st.button("Reset all", use_container_width=True):
                reset_flow()
                st.session_state.draft_name = ""
                st.session_state.draft_personality = list(PERSONALITIES.keys())[0]
                st.session_state.draft_background = list(BACKGROUNDS.keys())[0]
                st.session_state.draft_physical = list(PHYSICAL_STATES.keys())[0]
                st.session_state.draft_mood = list(STARTING_MOODS.keys())[0]
                st.session_state.draft_archetype = "Auto"
                st.rerun()


    with right:
        preview_name = st.session_state.draft_name.strip() or "Character"
        preview_state = build_state(
            st.session_state.draft_personality,
            st.session_state.draft_background,
            st.session_state.draft_physical,
            st.session_state.draft_mood,
            list(SCENARIOS.keys())[0],
        )
        avatar = get_avatar(st.session_state.draft_personality, preview_state)
        st.markdown(
            f"""<div class="builder-preview">
<div class="section-title">Preview</div>
<div class="hero-avatar">{avatar}</div>
<div class="hero-name">{preview_name}</div>
<div class="summary-line"><b>Personality:</b> {st.session_state.draft_personality}</div>
<div class="summary-line"><b>Background:</b> {st.session_state.draft_background}</div>
<div class="summary-line"><b>Physical:</b> {st.session_state.draft_physical}</div>
<div class="summary-line"><b>Mood:</b> {st.session_state.draft_mood}</div>
<div class="tiny">Scenario comes next.</div>
</div>""",
            unsafe_allow_html=True,
        )

elif st.session_state.page == "scenario":
    st.markdown('<div class="main-title scenario-picker-title">Choose scenario</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle scenario-picker-sub">Where does this happen?</div>', unsafe_allow_html=True)

    nav_a, nav_b, nav_c = st.columns([1, 2, 1])
    with nav_a:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "builder"
            st.rerun()
    with nav_b:
        dn = html.escape(st.session_state.draft_name.strip() or "Character")
        dp = html.escape(st.session_state.draft_personality)
        db = html.escape(st.session_state.draft_background)
        st.markdown(
            f'<div class="scenario-picker-meta"><b>{dn}</b> · {dp} · {db}</div>',
            unsafe_allow_html=True,
        )
    with nav_c:
        st.empty()

    scenario_items = list(SCENARIOS.items())
    n_scen = len(scenario_items)
    for row_start in range(0, n_scen, 3):
        row = scenario_items[row_start : row_start + 3]
        n_row = len(row)
        if n_row == 3:
            cols = st.columns(3, gap="medium")
        elif n_row == 2:
            # 1:2:2:1 → each card = 1/3 row width, matching a 3-column row
            cols = st.columns([1, 2, 2, 1], gap="medium")
            cols = [cols[1], cols[2]]
        else:
            cols = st.columns([1, 2, 1], gap="medium")
            cols = [cols[1]]
        for col, item in zip(cols, row):
            name, cfg = item
            ne = html.escape(name)
            de = html.escape(cfg["desc"])
            with col:
                st.markdown(
                    f'<div class="scenario-card">'
                    f'<h3 class="scenario-card__title">{ne}</h3>'
                    f'<p class="scenario-card__desc">{de}</p></div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"Enter {name}", key=f"enter_{name}", use_container_width=True):
                    start_scenario(name)
                    st.rerun()

else:
    if st.session_state.conversation_over:
        _overstim = st.session_state.get(SPECIAL_ENDING_KEY) == "overstimulated"
        if _overstim:
            st.markdown(
                """
                <div class="gameover gameover--overstimulated" id="gameover-section">
                    <span class="go-bolt go-bolt--tl" aria-hidden="true">⚡</span>
                    <span class="go-bolt go-bolt--tr" aria-hidden="true">⚡</span>
                    <span class="go-bolt go-bolt--bl" aria-hidden="true">⚡</span>
                    <span class="go-bolt go-bolt--br" aria-hidden="true">⚡</span>
                    <div class="gameover-big gameover-big--overstim">OVERSTIMULATED</div>
                    <div class="gameover-small gameover-small--overstim">Secret ending. You moonwalked past the simulation.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="recovery-buttons-overstim" aria-hidden="true" style="height:0;overflow:hidden;"></div>',
                unsafe_allow_html=True,
            )
        else:
            _em = html.escape(st.session_state.ending_message or "VIBES MURDERED")
            st.markdown(
                f"""
                <div class="gameover gameover--vibes-murdered" id="gameover-section">
                    <div class="gameover-big">{_em}</div>
                    <div class="gameover-small">What now?</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="recovery-buttons-marker" aria-hidden="true" style="height:0;overflow:hidden;"></div>',
                unsafe_allow_html=True,
            )
        a, b, c = st.columns(3)
        with a:
            if st.button("Try again", key="gameover_try_again", use_container_width=True):
                start_scenario(st.session_state.selected_scenario)
                st.rerun()
        with b:
            if st.button("Different scenario", key="gameover_scenario", use_container_width=True):
                st.session_state.page = "scenario"
                st.session_state.conversation_over = False
                st.session_state.ending_message = ""
                st.session_state[FINISHER_SESSION_DEBUG_KEY] = {}
                st.session_state[PROFILE_KEY] = init_interaction_profile()
                st.session_state[RECENT_FINISHERS_KEY] = []
                st.session_state[RECENT_PROMPT_MEMORY_KEY] = []
                st.session_state[CALLBACK_DEBUG_KEY] = {}
                st.session_state[RECENT_CALLBACK_LINES_KEY] = []
                st.session_state[ARCHETYPE_DEBUG_KEY] = {}
                st.session_state[TRAJECTORY_DEBUG_KEY] = {}
                st.session_state[MOONWALK_STREAK_KEY] = 0
                st.session_state[SPECIAL_ENDING_KEY] = None
                st.session_state[RELATIONSHIP_OVERRIDE_KEY] = None
                st.session_state.mode = "normal"
                st.session_state.follow_up_node = None
                st.session_state.follow_up_parent = None
                st.rerun()
        with c:
            if st.button("Someone new", key="gameover_new", use_container_width=True):
                reset_flow()
                st.rerun()

    cols = st.columns([1.02, 1.12, 0.92], gap="medium")
    left, middle, right = cols

    with left:
        if st.session_state.mode == "follow_up" and st.session_state.follow_up_node in FOLLOW_UP_NODES:
            node = FOLLOW_UP_NODES[st.session_state.follow_up_node]
            st.markdown('<div class="follow-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="follow-question">{node["question"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            for idx, (label, mods, verbal, next_node) in enumerate(node["options"]):
                st.button(
                    label,
                    key=f"follow_{st.session_state.follow_up_node}_{idx}",
                    use_container_width=True,
                    on_click=resolve_follow_up_choice,
                    args=(label, mods, verbal, next_node),
                )
        else:
            st.markdown('<div class="section-title">Speak</div>', unsafe_allow_html=True)
            scenario_name = st.session_state.selected_scenario
            say_pool = get_say_options_for_scenario(scenario_name) or DEFAULT_SAY_OPTIONS
            say_choice = st.selectbox(
                " ",
                list(say_pool.keys()),
                key="say_choice",
                label_visibility="collapsed",
            )
            if "clear_text" not in st.session_state:
                st.session_state.clear_text = False
            if st.session_state.clear_text:
                st.session_state.free_text_input = ""
                st.session_state.clear_text = False
            st.text_input("Or say whatever:", key="free_text_input", placeholder="Type something...", label_visibility="visible")
            say_clicked = st.button("Say it", key="send_line", use_container_width=True)
            if say_clicked:
                typed = (st.session_state.get("free_text_input") or "").strip()
                default_fallback = next(iter(say_pool.keys()), None)
                choice = typed if typed else st.session_state.get("say_choice", default_fallback)
                is_free = bool(typed)
                process_interaction(choice, "say", is_free_text=is_free)
                if is_free:
                    st.session_state.clear_text = True
                st.rerun()

            st.markdown('<div class="section-title section-title--spaced">Act</div>', unsafe_allow_html=True)
            act_choice = st.selectbox(" ", list(ACTION_OPTIONS.keys()), key="action_choice", label_visibility="collapsed")
            st.button("Do it", key="do_action", use_container_width=True, on_click=process_interaction, args=(act_choice, "do"))

        snap = st.session_state.get("build_snapshot") or {}
        if snap:
            p, bg, phy, mood = (
                html.escape(str(snap.get("Personality", "—"))),
                html.escape(str(snap.get("Background", "—"))),
                html.escape(str(snap.get("Physical", "—"))),
                html.escape(str(snap.get("Mood", "—"))),
            )
            card_name = html.escape((st.session_state.character_name or "").strip() or "Character")
            _dbg_sheet = bool(st.session_state.get("show_debug_crow_brain"))
            _traj_sheet = ""
            if _dbg_sheet:
                _tl = html.escape(str(snap.get("Trajectory") or "slow_warmup"))
                _traj_sheet = (
                    f'<div class="character-sheet-line"><span class="cs-k">Trajectory</span> (debug) {_tl}</div>'
                )
            st.markdown(
                '<div class="character-sheet">'
                f'<div class="character-card-name">{card_name}</div>'
                f'<div class="character-sheet-line"><span class="cs-k">Personality</span> {p}</div>'
                f'{_traj_sheet}'
                f'<div class="character-sheet-line"><span class="cs-k">Mood</span> {mood}</div>'
                f'<div class="character-sheet-line"><span class="cs-k">Background</span> {bg}</div>'
                f'<div class="character-sheet-line"><span class="cs-k">Physical</span> {phy}</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    with middle:
        personality = st.session_state.build_snapshot.get("Personality", "Confident")
        murdered = st.session_state.conversation_over and st.session_state.get(SPECIAL_ENDING_KEY) != "overstimulated"
        if st.session_state.conversation_over and st.session_state.get(SPECIAL_ENDING_KEY) == "overstimulated":
            avatar = random.choice(["⚡", "🌩️", "✨"])
        else:
            avatar = get_avatar(
                personality,
                st.session_state.state,
                murdered=murdered,
                relationship_override=st.session_state.get(RELATIONSHIP_OVERRIDE_KEY),
            )
        if not st.session_state.history:
            hero_text = ""
            you_context = ""
            physical = ""
        else:
            item = _hero_history_item(st.session_state.history)
            _cn = (st.session_state.character_name or "").strip()
            hero_text = sanitize_verbal_for_display(
                item.get("verbal") or "", character_name=_cn
            )
            if item.get("type") == "They asked":
                their_line = strip_outer_quotes(item.get("verbal") or "").strip()
                if their_line:
                    you_context = f'They said: {html.escape(their_line)}'
                else:
                    you_context = "They spoke first."
            elif item.get("type") in ("You said", "You answered", "You did"):
                you_context = f"You: {html.escape(str(item.get('input') or ''))}"
            else:
                you_context = f"You: {html.escape(str(item.get('input') or ''))}"
            physical = sanitize_physical_for_display(str(item.get("physical") or ""))

        _overstim = st.session_state.get(SPECIAL_ENDING_KEY) == "overstimulated"
        if st.session_state.conversation_over and _overstim and not (physical or "").strip():
            physical = "overstimulated"

        st.markdown(
            '<div class="center-response-panel center-response-panel--play">',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="hero-avatar">{avatar}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="hero-name">{html.escape(str(st.session_state.character_name or ""))}</div>',
            unsafe_allow_html=True,
        )
        if you_context:
            st.markdown(
                f'<div class="response-context-line">{you_context}</div>',
                unsafe_allow_html=True,
            )

        _phy = (physical or "").strip()
        _verb = html.escape(hero_text) if hero_text else "—"
        _phy_disp = html.escape(_phy) if _phy else "—"

        st.markdown('<div class="response-readout">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="response-readout__line response-readout__line--verbal">'
            f"🗣 Verbal response: {_verb}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="response-readout__line response-readout__line--physical">'
            f"⚡ Physical response: {_phy_disp}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


    with right:
        scenario_name = st.session_state.selected_scenario
        st.markdown(
            f'<div class="scenario-head">{html.escape(scenario_name)}</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.get("show_debug_crow_brain"):
            brain = st.session_state.get("crow_brain") or {}
            internal_thought = html.escape(str(brain.get("internal_thought", "")))
            attitude = html.escape(str(brain.get("attitude", "")))
            tone = html.escape(str(brain.get("tone", "")))
            physical = html.escape(str(brain.get("physical_reaction", "")))
            read_on_you = html.escape(str(brain.get("user_read", ""))) or html.escape(
                derive_read_on_you(st.session_state.get("conversation_memory") or init_memory_state())
            )
            trend = html.escape(str(brain.get("relationship_trend", "")))
            traj = html.escape(str(brain.get("interaction_trajectory", "")))
            if internal_thought or attitude:
                trend_html = f'<div class="crow-brain-line"><b>Trend:</b> {trend}</div>' if trend else ""
                traj_html = f'<div class="crow-brain-line"><b>Direction:</b> {traj}</div>' if traj else ""
                _fd = st.session_state.get(FINISHER_SESSION_DEBUG_KEY) or {}
                fin_html = ""
                if _fd.get("finisher_text"):
                    ft = html.escape(str(_fd.get("finisher_text", "")))
                    ftk = html.escape(str(_fd.get("finisher_tier", "")))
                    fsk = html.escape(str(_fd.get("shutdown_kind", "")))
                    fmo = html.escape(str(_fd.get("murdered_override", "")))
                    fci = html.escape(str(_fd.get("context_influenced", "")))
                    fmt = html.escape(str(_fd.get("matched_tags", "")))
                    fst = html.escape(str(_fd.get("selected_tags", "")))
                    fip = html.escape(str(_fd.get("interaction_profile", "")))
                    f_arch = html.escape(str(_fd.get("archetype_id", "")))
                    f_ab = html.escape(str(_fd.get("archetype_finisher_bias", "")))
                    f_tr = html.escape(str(_fd.get("trajectory_id", "")))
                    f_tb = html.escape(str(_fd.get("trajectory_finisher_bias", "")))
                    fin_html = (
                        f'<div class="crow-brain-line"><b>Finisher:</b> {ft}</div>'
                        f'<div class="crow-brain-line"><b>Finisher tier:</b> {ftk} · '
                        f'<b>Shutdown kind:</b> {fsk} · <b>Murdered override:</b> {fmo}</div>'
                        f'<div class="crow-brain-line"><b>Context influenced:</b> {fci} · '
                        f'<b>Matched tags:</b> {fmt} · <b>Line tags:</b> {fst}</div>'
                        f'<div class="crow-brain-line"><b>Finisher archetype:</b> {f_arch} · '
                        f'<b>Archetype finisher bias:</b> {f_ab}</div>'
                        f'<div class="crow-brain-line"><b>Finisher trajectory:</b> {f_tr} · '
                        f'<b>Trajectory finisher bias:</b> {f_tb}</div>'
                        f'<div class="crow-brain-line"><b>Interaction profile:</b> {fip}</div>'
                    )
                _arch_dbg = st.session_state.get(ARCHETYPE_DEBUG_KEY) or {}
                arch_html = ""
                if _arch_dbg.get("resolved_archetype_id") is not None or _arch_dbg.get("explicit_archetype") is not None:
                    ra = html.escape(str(_arch_dbg.get("resolved_archetype_id", "")))
                    ex = html.escape(str(_arch_dbg.get("explicit_archetype", "")))
                    inf = html.escape(str(_arch_dbg.get("influenced", "")))
                    tba = html.escape(str(_arch_dbg.get("tier_bonus_applied", "")))
                    cbm = html.escape(str(_arch_dbg.get("callback_probability_mult", "")))
                    arch_html = (
                        f'<div class="crow-brain-line"><b>Archetype (resolved):</b> {ra} · '
                        f'<b>Explicit:</b> {ex}</div>'
                        f'<div class="crow-brain-line"><b>Archetype tier bonus:</b> {tba} · '
                        f'<b>Callback mult:</b> {cbm}</div>'
                        f'<div class="crow-brain-line"><b>Archetype influenced:</b> {inf}</div>'
                    )
                _traj_dbg = st.session_state.get(TRAJECTORY_DEBUG_KEY) or {}
                traj_layer_html = ""
                if _traj_dbg.get("trajectory_id") is not None:
                    rt = html.escape(str(_traj_dbg.get("trajectory_id", "")))
                    st_t = html.escape(str(_traj_dbg.get("stored_trajectory", "")))
                    src_t = html.escape(str(_traj_dbg.get("trajectory_source", "")))
                    mem = html.escape(str(_traj_dbg.get("memory", "")))
                    inf_t = html.escape(str(_traj_dbg.get("influenced", "")))
                    tbr = html.escape(str(_traj_dbg.get("tier_bonus_reply", "")))
                    cbmt = html.escape(str(_traj_dbg.get("callback_probability_mult", "")))
                    rep_t = html.escape(str(_traj_dbg.get("repetition_murder_threshold", "")))
                    traj_layer_html = (
                        f'<div class="crow-brain-line"><b>Trajectory (active):</b> {rt} · '
                        f'<b>Stored:</b> {st_t} · <b>Source:</b> {src_t}</div>'
                        f'<div class="crow-brain-line"><b>Trajectory memory:</b> {mem}</div>'
                        f'<div class="crow-brain-line"><b>Tier bonus (reply):</b> {tbr} · '
                        f'<b>Callback mult:</b> {cbmt} · <b>Repeat murder at:</b> {rep_t}</div>'
                        f'<div class="crow-brain-line"><b>Trajectory influenced:</b> {inf_t}</div>'
                    )
                _cb = st.session_state.get(CALLBACK_DEBUG_KEY) or {}
                cb_html = ""
                if _cb.get("signals") is not None or _cb.get("recent_prompt_memory"):
                    cm = html.escape(repr(_cb.get("recent_prompt_memory")))
                    sg = html.escape(repr(_cb.get("signals")))
                    ou = html.escape(str(_cb.get("override_used")))
                    ot = html.escape(str(_cb.get("override_type")))
                    rs = html.escape(str(_cb.get("response_source_tag")))
                    cb_html = (
                        f'<div class="crow-brain-line"><b>Callback memory:</b> {cm}</div>'
                        f'<div class="crow-brain-line"><b>Callback signals:</b> {sg}</div>'
                        f'<div class="crow-brain-line"><b>Callback override:</b> {ou} · '
                        f'<b>type:</b> {ot} · <b>source:</b> {rs}</div>'
                    )
                st.markdown(
                    '<div class="crow-brain-card">'
                    '<div class="crow-brain-title">Crow Brain</div>'
                    f'<div class="crow-brain-line"><b>Internal Thought:</b> {internal_thought}</div>'
                    f'<div class="crow-brain-line"><b>Read On You:</b> {read_on_you}</div>'
                    f'{trend_html}'
                    f'{traj_html}'
                    f'{fin_html}'
                    f'{arch_html}'
                    f'{traj_layer_html}'
                    f'{cb_html}'
                    f'<div class="crow-brain-line"><b>Attitude:</b> {attitude}</div>'
                    f'<div class="crow-brain-line"><b>Tone:</b> {tone}</div>'
                    f'<div class="crow-brain-line"><b>Physical:</b> {physical}</div>'
                    "</div>",
                    unsafe_allow_html=True,
                )

        r1, r2 = st.columns(2, gap="small")
        half = (len(ATTRIBUTES) + 1) // 2
        chunks = [ATTRIBUTES[:half], ATTRIBUTES[half:]]
        _stats_all_max = (
            st.session_state.conversation_over
            and st.session_state.get(SPECIAL_ENDING_KEY) == "overstimulated"
        )
        for col, chunk in zip([r1, r2], chunks):
            with col:
                for attr in chunk:
                    value = 100 if _stats_all_max else int(st.session_state.state[attr])
                    pct = max(0, min(100, value))
                    label = attr.capitalize()
                    delta = int(st.session_state.last_deltas.get(attr, 0))
                    color = attribute_color(attr, delta)
                    delta_html = f' <span style="color:{color};font-size:0.85em;font-weight:800;">{format_delta(delta)}</span>' if delta != 0 else ''
                    st.markdown(
                        f'<div class="stat-row">'
                        f'<div class="stat-label-line"><b>{label}:</b> <span class="stat-value">{value}</span>{delta_html}</div>'
                        f'<div class="stat-bar-track"><div class="stat-bar-fill" style="width:{pct}%;"></div></div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
