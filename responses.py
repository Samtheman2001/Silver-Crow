"""
Response/outcome helpers that aren't the core brain logic.
"""

from __future__ import annotations

import streamlit as st

from .custom_label_pools import PREFERRED_RELATIONSHIPS, preferred_relationship_read


def _flavor_relationship_line(label: str) -> str:
    if not PREFERRED_RELATIONSHIPS:
        return label
    key = {
        "Open": "open",
        "Guarded": "guarded",
        "Closed off": "guarded",
        "Curious": "uncertain",
        "Uncomfortable": "guarded",
        "Tense": "hostile",
    }.get(label)
    if key:
        return preferred_relationship_read(key)
    return label


def relationship_label(state):
    if state["trust"] <= 5 or (state["anger"] > 80 and state["stress"] > 75):
        return "hostile"
    if state["trust"] > 75:
        return "open"
    if state["trust"] < 25:
        return "guarded"
    return "uncertain"


def demo_safe_dropdown_say_relationship(state, turns_before_reply: int) -> str:
    """Deterministic relationship label for menu SAY (no random flavored pools)."""
    if int(turns_before_reply or 0) <= 3:
        return "neutral"
    trust = int(state.get("trust", 50) or 0)
    if trust < 25:
        return "weird"
    if trust <= 60:
        return "getting to know eachother"
    return "good"


def relationship_status(state, conversation_over):
    """Concise relationship read — no narrative 'almost gone' when interaction is over."""
    ov = st.session_state.get("relationship_status_override")
    if conversation_over:
        if st.session_state.get("_special_ending") == "overstimulated" and isinstance(ov, str) and ov.strip():
            return ov.strip()
        return "Done"
    if isinstance(ov, str) and ov.strip():
        return ov.strip()
    if int(st.session_state.get("turns", 0) or 0) == 0:
        return "neutral"
    if state["anger"] > 78 and state["trust"] < 30:
        return _flavor_relationship_line("Tense")
    if state["trust"] < 20 and state["anger"] > 45:
        return _flavor_relationship_line("Closed off")
    if state["trust"] < 28:
        return _flavor_relationship_line("Guarded")
    if state["confusion"] > 70 or state["fear"] > 72:
        return _flavor_relationship_line("Uncomfortable")
    if state["stress"] > 74 and state["trust"] < 45:
        return _flavor_relationship_line("Uncomfortable")
    if state["trust"] > 70 and state["happiness"] > 52 and state["anger"] < 48:
        return _flavor_relationship_line("Open")
    if state["interest"] > 64 and state["trust"] >= 30 and state["anger"] < 58:
        return _flavor_relationship_line("Curious")
    if state["anger"] > 58 or state["stress"] > 64:
        return _flavor_relationship_line("Tense")
    if state["stress"] > 56 or state["happiness"] < 32:
        return _flavor_relationship_line("Guarded")
    return _flavor_relationship_line("Guarded")


def outcome_summary(state, name):
    score = state["trust"] + state["happiness"] + state["interest"] + state["confidence"]
    score -= state["anger"] + state["stress"] + state["fear"] + state["confusion"]
    if score > 110:
        verdict = "Strong positive outcome"
        advice = f"{name} feels comfortable, engaged, and relatively trusting. Your approach is working."
    elif score > 40:
        verdict = "Mixed but promising"
        advice = f"{name} is still open, but the interaction needs more care and consistency."
    elif score > -20:
        verdict = "Shaky interaction"
        advice = f"{name} is not fully lost, but trust and clarity need repair."
    else:
        verdict = "Poor outcome"
        advice = f"{name} feels guarded or overwhelmed. A reset in tone and approach would help."
    return verdict, advice


def fill_name_tokens(text):
    return str(text).replace("{name}", st.session_state.character_name)

