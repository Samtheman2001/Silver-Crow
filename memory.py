"""
Conversation memory + trajectory (read-on-you) logic.
"""

from __future__ import annotations

import streamlit as st

from personality import get_character_dna
from utils import clamp, clamp01, normalize_speech


def init_memory_state():
    """Second-layer memory about how the USER has acted (not the bars)."""
    return {
        "kindness_score": 0,
        "disrespect_score": 0,
        "awkward_score": 0,
        "flirtation_score": 0,
        "honesty_score": 50,  # starts neutral; moves with consistency/suspicion
        "pressure_score": 0,
        "inconsistency_score": 0,
        "last_user_read": "",
        "last_kind": "",
        "last_free_text_category": None,
        "last_input_norm": "",
        "recent_inputs_norm": [],
        "followup_answers": [],
        "last_turn_was_rude": False,
        "last_turn_was_apology": False,
        "interaction_trajectory": "stable_neutral",
        "trajectory_strength": 25,  # inertia: 0-100
        "trajectory_streak": 0,
        "trajectory_last": "",
    }


def normalize_user_text(text):
    return normalize_speech(text)


def memory_add_recent(mem, norm):
    if not norm:
        return
    mem["recent_inputs_norm"] = (mem.get("recent_inputs_norm") or []) + [norm]
    mem["recent_inputs_norm"] = mem["recent_inputs_norm"][-6:]
    mem["last_input_norm"] = norm


def propose_interaction_trajectory(mem, state, last_deltas=None):
    """Propose a trajectory label from memory + recent deltas (candidate only)."""
    last_deltas = last_deltas or {}
    k = mem.get("kindness_score", 0)
    d = mem.get("disrespect_score", 0)
    a = mem.get("awkward_score", 0)
    f = mem.get("flirtation_score", 0)
    h = mem.get("honesty_score", 50)
    p = mem.get("pressure_score", 0)
    inc = mem.get("inconsistency_score", 0)
    trust = state.get("trust", 0)
    anger = state.get("anger", 0)
    stress = state.get("stress", 0)
    interest = state.get("interest", 0)

    dna = get_character_dna() or {}
    patience = int(dna.get("patience", 55))
    react = int(dna.get("emotional_reactivity", 50))
    trust_base = int(dna.get("trust_baseline", 45))
    agree = int(dna.get("agreeableness", 50))

    # DNA-tuned triggers. Lower patience/higher reactivity -> faster escalation.
    susp_h_trigger = int(clamp(22 + (45 - trust_base) * 0.6, 18, 40))

    pressure_trigger = int(clamp(75 - (55 - patience) * 0.55 - (react - 50) * 0.25, 60, 90))
    disrespect_trigger = int(clamp(70 - (55 - patience) * 0.35 - (react - 50) * 0.25, 55, 85))
    awkward_trigger = int(clamp(75 - (55 - patience) * 0.30 - (react - 50) * 0.20, 55, 90))

    trust_open_trigger = int(clamp(78 + (trust_base - 45) * 0.35 - (patience - 55) * 0.10, 70, 92))
    kindness_open_trigger = int(clamp(55 + (60 - agree) * 0.15 - (55 - patience) * 0.06, 45, 75))

    dt = int(last_deltas.get("trust", 0))
    da = int(last_deltas.get("anger", 0))
    ds = int(last_deltas.get("stress", 0))
    di = int(last_deltas.get("interest", 0))

    # Strong negative arcs
    if h <= susp_h_trigger or inc >= 65:
        return "suspicious"
    if p >= pressure_trigger or (p >= max(50, pressure_trigger - 15) and (da > 0 or ds > 0)):
        return "losing_patience"
    if d >= disrespect_trigger:
        return "growing_tension"
    if a >= awkward_trigger and interest < 55:
        return "disengaging"

    # Positive arcs
    if trust >= trust_open_trigger and k >= kindness_open_trigger and d < 45 and p < 55:
        return "emotionally_open"
    if dt > 0 and trust >= 60 and k >= 45 and d < 55:
        return "building_trust"
    if interest >= 70 and f >= 45 and d < 55 and p < 60:
        return "slightly_interested"
    if k >= 60 and d < 45 and p < 55 and trust >= 55:
        return "warming_up"

    # Neutral-ish
    if d >= 55 or anger >= 60 or stress >= 65:
        return "growing_tension"
    if interest >= 62 and trust >= 40:
        return "stable_neutral"
    return "stable_neutral"


def update_interaction_trajectory(mem, state, last_deltas=None):
    """
    Slow-moving trajectory with inertia.
    Requires multiple consistent proposals before switching.
    """
    current = mem.get("interaction_trajectory", "stable_neutral")
    strength = int(mem.get("trajectory_strength", 25))
    streak = int(mem.get("trajectory_streak", 0))
    cand = propose_interaction_trajectory(mem, state, last_deltas=last_deltas)

    if cand == current:
        mem["trajectory_strength"] = clamp(strength + 2, 0, 100)
        mem["trajectory_streak"] = clamp(streak + 1, 0, 100)
        mem["trajectory_last"] = cand
        return

    mem["trajectory_last"] = cand
    streak = streak + 1 if mem.get("trajectory_last") == cand else 1
    mem["trajectory_streak"] = streak

    base_needed = 3
    if strength >= 60:
        base_needed = 5
    elif strength >= 40:
        base_needed = 4

    sticky = {"losing_patience", "suspicious", "disengaging"}
    if current in sticky and cand in {"warming_up", "emotionally_open", "building_trust"}:
        base_needed += 2

    dna = get_character_dna() or {}
    patience = int(dna.get("patience", 55))
    react = int(dna.get("emotional_reactivity", 50))
    trust_base = int(dna.get("trust_baseline", 45))

    negative_set = {"losing_patience", "growing_tension", "suspicious", "disengaging"}
    positive_set = {"warming_up", "emotionally_open", "building_trust", "slightly_interested"}

    if cand in negative_set:
        base_needed -= 1 if patience < 45 else 0
        base_needed -= 1 if react >= 65 else 0
    if cand in positive_set:
        base_needed += 1 if patience < 45 else 0
        base_needed += 1 if trust_base < 40 else 0

    base_needed = int(clamp(base_needed, 1, 7))
    if streak >= base_needed:
        mem["interaction_trajectory"] = cand
        mem["trajectory_strength"] = clamp(strength - 8, 0, 100)
        mem["trajectory_streak"] = 0
    else:
        mem["trajectory_strength"] = clamp(strength - 1, 0, 100)


def update_conversation_memory(mem, text, kind, is_free_text, free_text_category, repeat_count, scenario_name=None):
    """
    Update compact memory scores gradually from user behavior.
    Does NOT replace the emotional bars. This is "read on the player".
    """
    t = (text or "").strip()
    norm = normalize_user_text(t)
    memory_add_recent(mem, norm)
    mem["last_kind"] = kind
    mem["last_free_text_category"] = free_text_category if is_free_text else mem.get("last_free_text_category")

    dna = get_character_dna() or {}
    patience = int(dna.get("patience", 55))
    agree = int(dna.get("agreeableness", 50))
    react = int(dna.get("emotional_reactivity", 50))
    trust_base = int(dna.get("trust_baseline", 45))
    openness = int(dna.get("openness", 55))

    negative_keys = {"disrespect_score", "awkward_score", "pressure_score", "inconsistency_score"}
    base_decay = 0.985
    neg_decay = base_decay + (patience - 55) / 2500.0 + (agree - 50) / 3500.0 - (react - 50) / 2200.0
    neg_decay = float(clamp(neg_decay, 0.975, 0.995))
    pos_decay = base_decay - (patience - 55) / 4200.0 - (react - 50) / 5200.0 + (agree - 50) / 6000.0
    pos_decay = float(clamp(pos_decay, 0.975, 0.995))

    for k in ("kindness_score", "disrespect_score", "awkward_score", "flirtation_score", "pressure_score", "inconsistency_score"):
        factor = pos_decay if k not in negative_keys else neg_decay
        mem[k] = int(round(mem.get(k, 0) * factor))

    # Kindness/friendly
    if is_free_text and free_text_category in ("friendly", "apology"):
        kind_add = 3 if free_text_category == "friendly" else 4
        mult_kind = 0.85 + agree / 200.0 + patience / 260.0
        mem["kindness_score"] += int(round(kind_add * clamp(mult_kind, 0.75, 1.35)))
    if not is_free_text and text in (
        "Hello, nice to meet you.",
        "Nice to meet you",
        "I want to help.",
        "I respect your opinion.",
        "What do you need?",
        "Can you help me?",
    ):
        mult_kind = 0.85 + agree / 230.0 + patience / 280.0
        mem["kindness_score"] += int(round(2 * clamp(mult_kind, 0.75, 1.30)))

    # Disrespect/aggression
    if is_free_text and free_text_category and str(free_text_category).startswith("aggressive_"):
        base_dis = {"aggressive_light": 3, "aggressive_medium": 6, "aggressive_hard": 10}.get(free_text_category, 6)
        mult_dis = 0.9 + react / 160.0 + (55 - patience) / 220.0 + (45 - trust_base) / 240.0
        mem["disrespect_score"] += int(round(base_dis * clamp(mult_dis, 0.75, 1.5)))
        mem["last_turn_was_rude"] = True
    elif not is_free_text and text in ("You're wrong.", "Who do you think you are?", "What gives you the right?"):
        mult_dis = 0.9 + react / 170.0 + (55 - patience) / 240.0 + (45 - trust_base) / 260.0
        mem["disrespect_score"] += int(round(4 * clamp(mult_dis, 0.75, 1.4)))
        mem["last_turn_was_rude"] = True
    else:
        mem["last_turn_was_rude"] = False

    # Awkward/confusing
    if is_free_text and free_text_category in ("awkward", "absurd"):
        base_aw = 5 if free_text_category == "absurd" else 3
        mult_aw = 0.9 + react / 180.0 + (55 - patience) / 260.0
        mem["awkward_score"] += int(round(base_aw * clamp(mult_aw, 0.75, 1.45)))
    if not is_free_text and text in ("Can a young gangsta get money anymore?", "Do you own a jetski?", "Would you like to buy my jetski?"):
        mult_aw = 0.9 + react / 200.0 + (55 - patience) / 300.0
        mem["awkward_score"] += int(round(2 * clamp(mult_aw, 0.75, 1.35)))

    # Flirtation/attraction pressure
    if (not is_free_text) and text in ("Do you want to go on a date?", "Do you think I'm attractive?", "Do you like me?"):
        base_fl = 5 if text == "Do you want to go on a date?" else 3
        mult_fl = 0.85 + openness / 250.0 + (agree - 50) / 320.0
        mem["flirtation_score"] += int(round(base_fl * clamp(mult_fl, 0.70, 1.40)))
    if is_free_text and any(x in (t.lower()) for x in ("u cute", "you're cute", "youre cute", "date me", "kiss me", "i like you")):
        mult_fl = 0.85 + openness / 250.0 + (agree - 50) / 300.0
        mem["flirtation_score"] += int(round(4 * clamp(mult_fl, 0.70, 1.35)))

    # Pressure prompts
    pressure_prompts = {
        "Do you like me?",
        "Why don't you like me?",
        "Why should I trust you?",
        "Can I sleep at your house tonight?",
        "Do you think I'm attractive?",
        "Do you want to go on a date?",
        "Why don't you want to go on a date?",
        "What do you think of me so far?",
        "Why are you treating me this way?",
        "Why are you acting like this?",
        "Who do you think you are?",
        "Why do you care?",
        "What do you want?",
    }
    if (not is_free_text) and text in pressure_prompts:
        add = 3 if repeat_count <= 1 else 5
        if int(st.session_state.get("turns", 0)) <= 2:
            add += 2
        mult_press = 0.9 + react / 170.0 + (55 - patience) / 260.0 + (45 - trust_base) / 320.0
        mem["pressure_score"] += int(round(add * clamp(mult_press, 0.70, 1.55)))

    lower = t.lower()
    evasive = any(x in lower for x in ("idk", "i don't know", "whatever", "doesn't matter", "n/a", "no comment"))
    if evasive and (not is_free_text or free_text_category in ("awkward", "neutral")):
        mult_ev = 0.85 + (55 - patience) / 220.0 + react / 200.0 + (45 - trust_base) / 240.0
        mem["honesty_score"] -= int(round(2 * clamp(mult_ev, 0.65, 1.5)))
        mem["awkward_score"] += int(round(1 * clamp(mult_ev, 0.65, 1.5)))

    if mem.get("last_turn_was_rude") and (is_free_text and free_text_category in ("friendly", "apology")):
        mult_inc = 0.85 + react / 200.0 + (55 - patience) / 260.0
        mem["inconsistency_score"] += int(round(4 * clamp(mult_inc, 0.70, 1.4)))
        mem["honesty_score"] -= int(round(1 * clamp(0.9 + (55 - patience) / 400.0, 0.75, 1.3)))
        mem["pressure_score"] += int(round(1 * clamp(mult_inc, 0.7, 1.4)))

    if is_free_text and free_text_category == "apology":
        mem["last_turn_was_apology"] = True
    else:
        mem["last_turn_was_apology"] = False

    if is_free_text and free_text_category == "apology":
        forgiveness = clamp01((agree + patience) / 220.0)
        mem["disrespect_score"] = clamp(mem.get("disrespect_score", 0) - int(round(2 + forgiveness * 4)), 0, 100)
        mem["pressure_score"] = clamp(mem.get("pressure_score", 0) - int(round(1 + forgiveness * 3)), 0, 100)
        mem["awkward_score"] = clamp(mem.get("awkward_score", 0) - int(round(forgiveness * 2)), 0, 100)

    for k in ("kindness_score", "disrespect_score", "awkward_score", "flirtation_score", "pressure_score", "inconsistency_score"):
        mem[k] = clamp(mem.get(k, 0), 0, 100)
    mem["honesty_score"] = clamp(mem.get("honesty_score", 50), 0, 100)

    update_interaction_trajectory(
        mem,
        st.session_state.get("state") or {},
        last_deltas=st.session_state.get("last_deltas") or {},
    )


def derive_read_on_you(mem):
    """Derived label shown in UI (no raw scores exposed)."""
    k = mem.get("kindness_score", 0)
    d = mem.get("disrespect_score", 0)
    a = mem.get("awkward_score", 0)
    f = mem.get("flirtation_score", 0)
    h = mem.get("honesty_score", 50)
    p = mem.get("pressure_score", 0)
    inc = mem.get("inconsistency_score", 0)

    if d >= 70:
        return "annoying"
    if p >= 70:
        return "pushy"
    if inc >= 55 or h <= 22:
        return "inconsistent"
    if a >= 65:
        return "awkward"
    if f >= 65 and d < 55 and p < 55:
        return "charming"
    if k >= 65 and d < 40:
        return "sincere"
    if d >= 45 and p >= 45:
        return "intense"
    if k >= 40 and a >= 40:
        return "hard to read"
    return "respectful"


def relationship_trend(mem):
    """Optional label; derived only from memory arc."""
    k = mem.get("kindness_score", 0)
    d = mem.get("disrespect_score", 0)
    p = mem.get("pressure_score", 0)
    inc = mem.get("inconsistency_score", 0)
    score = (k + mem.get("flirtation_score", 0) * 0.6) - (d * 1.2 + p * 0.9 + inc * 0.8)
    if score > 45:
        return "warming"
    if score < -35:
        return "cooling"
    if inc > 55:
        return "volatile"
    return "steady"

