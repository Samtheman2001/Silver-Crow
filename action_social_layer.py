# -*- coding: utf-8 -*-
"""
Lightweight optional one-line verbal color for do-actions when the scripted
action_reaction() leaves verbal empty. Does not replace non-empty lines.
"""

from __future__ import annotations

import random
from typing import Any, List, Mapping, Optional

from .config import ACTION_OPTIONS


def _social_band(state: Mapping[str, Any]) -> str:
    a = int(state.get("anger", 0))
    t = int(state.get("trust", 50))
    h = int(state.get("happiness", 50))
    s = int(state.get("stress", 0))
    if a >= 52 or t <= 38:
        return "irritated"
    if a >= 40 or t <= 45 or s >= 62:
        return "guarded"
    if h >= 60 and t >= 52:
        return "warm"
    if h >= 48:
        return "soft"
    return "neutral"


def _shyify(line: str) -> str:
    if not line or line.startswith("…"):
        return line
    if random.random() < 0.45:
        return f"…{line}"
    return line


def _aggressive_voice(line: str, band: str) -> str:
    if band != "irritated":
        return line
    short = {
        "What?": "What.",
        "Yeah?": "Yeah—what?",
    }
    return short.get(line, line)


def _personality_touch(line: Optional[str], personality: str, band: str) -> Optional[str]:
    if not line:
        return None
    if personality == "Shy":
        return _shyify(line)
    if personality == "Aggressive":
        return _aggressive_voice(line, band)
    if personality == "Empathetic" and band in {"warm", "soft"} and random.random() < 0.35:
        warm_alt = {
            "Hey.": "Oh—hey. Hi.",
            "Hi.": "Hi there.",
            "What's up?": "Hey—how are you?",
        }
        return warm_alt.get(line, line)
    return line


def _pick(pool: List[str]) -> str:
    return random.choice(pool)


def _forced_fallback_social(action: str, count: int, band: str) -> str:
    """Guarantees a human line when force=True but no branch matched."""
    pools = {
        "warm": ["Hey.", "Hi.", "Oh—hey.", "What's up?", "Mm.", "Heh.", "Yeah…"],
        "soft": ["Hey.", "Hi.", "Mm.", "Huh.", "Yeah…", "Oh—hi."],
        "neutral": ["Hey.", "Hi.", "Mm.", "Huh.", "Yeah?", "…Hi."],
        "guarded": ["…Hi.", "Hey.", "Mm.", "Hm.", "Yeah?", "…what?"],
        "irritated": ["What?", "Yeah?", "Mm.", "…", "Huh.", "So?"],
    }
    base = pools.get(band, pools["neutral"])
    if "smile" in action.lower():
        base = base + ["Heh.", "…", "Mhm.", "Okay…"]
    if count >= 3:
        base = base + ["Again?", "Still?", "…Okay."]
    return _pick(base)


def maybe_social_verbal_for_do_action(
    action: str,
    count: int,
    state: Mapping[str, Any],
    personality: str,
    *,
    force: bool = False,
) -> Optional[str]:
    """
    Return a single inner line (no outer quotes) or None to stay non-verbal.
    Only called when action_reaction produced an empty verbal (unless force=True).
    When force=True, skips random silence rolls and always returns a line for
    known actions (primary path for filling after Crow Brain).
    """
    if action not in ACTION_OPTIONS:
        return None

    band = _social_band(state)
    line: Optional[str] = None

    if action == "Smile":
        if count == 1:
            talk_p = {"warm": 0.97, "soft": 0.95, "neutral": 0.92, "guarded": 0.88, "irritated": 0.72}.get(
                band, 0.9
            )
            if not force and random.random() > talk_p:
                return None
            pools = {
                "warm": ["Hey.", "What's up?", "Hi.", "Oh—hey.", "Hey—hey.", "Heh.", "Hi—hi."],
                "soft": ["Hey.", "Hi.", "Oh—hi.", "What's up?", "Mm.", "Heh."],
                "neutral": ["Hey.", "Hi.", "Oh—hi.", "…Hi.", "What's up?", "Mm."],
                "guarded": ["…Hi.", "Hey.", "Uh… hey.", "Okay… hi?", "Mm.", "Yeah…?"],
                "irritated": ["What?", "Yeah?", "…Okay.", "What is it?", "Mm.", "So?"],
            }
            pool = pools.get(band, pools["neutral"])
            if not force and band == "irritated" and random.random() < 0.35:
                return None
            line = _pick(pool)
        elif count >= 2:
            if not force and random.random() > 0.94:
                return None
            pools = {
                "warm": ["…You're smiling a lot.", "Okay—I'm seeing it.", "That's a lot of smile."],
                "soft": ["…Again?", "You're really committed to that.", "Okay…"],
                "neutral": ["…Again?", "You okay?", "That's kind of a lot."],
                "guarded": ["…Why keep doing that?", "This is getting weird.", "Stop smiling at me like that."],
                "irritated": ["Stop.", "What are you doing?", "Seriously—stop."],
            }
            line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Step closer" and count == 1:
        if not force and random.random() > 0.92:
            return None
        pools = {
            "warm": ["Oh—hey.", "You're close.", "Hi.", "Okay… hi."],
            "soft": ["Hey.", "…Personal space?", "You're right there."],
            "neutral": ["Hey.", "Little close.", "Uh—hi?"],
            "guarded": ["…Space.", "Back up a little?", "You're in my bubble."],
            "irritated": ["Back up.", "What are you doing?", "Too close."],
        }
        line = _pick(pools.get(band, pools["guarded"]))

    elif action == "Interrupt" and count == 1:
        if not force and random.random() > 0.9:
            return None
        pools = {
            "warm": ["Let me finish—", "Hold on—", "One sec—"],
            "soft": ["Hold on.", "Let me talk.", "I'm mid-sentence."],
            "neutral": ["Hold on.", "Let me finish.", "I'm talking."],
            "guarded": ["I'm not done.", "Let me finish.", "Don't cut me off."],
            "irritated": ["I'm talking.", "Stop.", "Let me finish."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Look away" and count == 1:
        if not force and random.random() > 0.9:
            return None
        pools = {
            "warm": ["You good?", "Everything okay?", "Hey—I'm here."],
            "soft": ["…You alright?", "Did I lose you?", "Hey?"],
            "neutral": ["Hello?", "You listening?", "I'm still here."],
            "guarded": ["What?", "I'm right here.", "Look at me when I'm talking."],
            "irritated": ["What now?", "Seriously?", "I'm talking to you."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Step back" and count == 1:
        if not force and random.random() > 0.88:
            return None
        pools = {
            "warm": ["You okay?", "All good?", "Did I come on too strong?"],
            "soft": ["…Okay…", "You stepping back?", "Did something happen?"],
            "neutral": ["You good?", "What's up?", "Mm."],
            "guarded": ["Fine.", "Whatever.", "Suit yourself."],
            "irritated": ["Yeah, walk away.", "Fine.", "Go ahead."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Raise voice" and count == 1:
        if not force and random.random() > 0.9:
            return None
        pools = {
            "warm": ["Whoa—tone.", "Hey, easy.", "Okay—lower the volume."],
            "soft": ["Whoa.", "Too loud.", "Ease up."],
            "neutral": ["Whoa.", "Hey—chill.", "Tone."],
            "guarded": ["Don't yell at me.", "Lower your voice.", "Back off with that."],
            "irritated": ["Stop shouting.", "I'm not deaf.", "Watch it."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Stay silent" and count == 1:
        if not force and random.random() > 0.88:
            return None
        pools = {
            "warm": ["…You gonna say something?", "I'm waiting.", "Talk to me."],
            "soft": ["Hello?", "You still there?", "…Okay?"],
            "neutral": ["You good?", "Say something.", "I'm here when you're ready."],
            "guarded": ["Well?", "I'm not a mind reader.", "Use your words."],
            "irritated": ["Say something or I'm done.", "What?", "Don't just stare."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Offer handshake" and count == 1:
        if not force and random.random() > 0.9:
            return None
        pools = {
            "warm": ["Hey—nice to meet you.", "Oh—hey.", "Hi. Yeah, sure."],
            "soft": ["Oh—hi.", "Hey.", "Okay… hi."],
            "neutral": ["Alright.", "Hey.", "Mm-hm."],
            "guarded": ["…Sure.", "Fine.", "If you want."],
            "irritated": ["…Fine.", "Make it quick.", "Yeah, whatever."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Sit down" and count == 1:
        if not force and random.random() > 0.88:
            return None
        pools = {
            "warm": ["Go ahead.", "Sure.", "Make yourself comfortable."],
            "soft": ["Sure.", "Have a seat, I guess.", "Mm."],
            "neutral": ["Sure.", "Go for it.", "Mm-hm."],
            "guarded": ["…Sure.", "Fine.", "If you want."],
            "irritated": ["Do what you want.", "Fine.", "Whatever."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Leave" and count == 1:
        if not force and random.random() > 0.9:
            return None
        pools = {
            "warm": ["Wait—already?", "You're leaving?", "Hey—hold on."],
            "soft": ["Oh… okay.", "You're going?", "Wait."],
            "neutral": ["You're leaving?", "Okay then.", "Alright."],
            "guarded": ["Fine, go.", "Whatever.", "Bye, I guess."],
            "irritated": ["Yeah, leave.", "Go.", "Don't let the door hit you."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    elif action == "Hit the moonwalk":
        # Demo: moonwalk verbal is fully authored in try_pick_authored_action_response — never override with social "Hi."
        return None

    elif action == "Stare blankly":
        if count <= 1:
            return None
        if not force and random.random() > 0.72:
            return None
        pools = {
            "warm": ["…You okay?", "Talk to me.", "What's going on?"],
            "soft": ["Hello?", "You good?", "Say something."],
            "neutral": ["You good?", "What?", "Hello?"],
            "guarded": ["Stop staring.", "What?", "Say it."],
            "irritated": ["What?", "Quit it.", "Stop."],
        }
        line = _pick(pools.get(band, pools["neutral"]))

    else:
        if count != 1:
            if force:
                line = _forced_fallback_social(action, count, band)
        else:
            if not force and random.random() > 0.82:
                return None
            pools = {
                "warm": ["Yeah…", "What's up?", "Mm.", "Hey."],
                "soft": ["…Yeah?", "What?", "Mm."],
                "neutral": ["Yeah?", "What?", "Mm."],
                "guarded": ["What?", "Yeah?", "So?"],
                "irritated": ["What?", "Yeah?", "Make it quick."],
            }
            line = _pick(pools.get(band, pools["neutral"]))

    if force and line is None:
        line = _forced_fallback_social(action, count, band)

    return _personality_touch(line, personality, band) if line is not None else None


def bare_micro_ack_for_do_action(
    state: Mapping[str, Any],
    personality: str,
    brain: Optional[Mapping[str, Any]] = None,
) -> str:
    """
    Ultra-short human grunts — last resort. No plain 'Okay.' / no skeptical menu tone.
    """
    b = brain or {}
    att_raw = str(b.get("attitude") or "guarded").strip().lower()
    band = _social_band(state)

    warmish = frozenset({"warm", "flirty", "amused"})
    sharp = frozenset({"irritated", "hostile", "dismissive"})

    if att_raw in warmish or band in {"warm", "soft"}:
        pool = ["…yeah.", "Mm.", "Mhm.", "Right.", "Heh.", "…hey.", "Yeah…", "Oh—hey."]
    elif att_raw in sharp or band == "irritated":
        pool = ["What.", "Yeah?", "Mm.", "…what?", "Huh.", "…", "So?", "Tch."]
    elif band == "guarded" or att_raw in {"anxious", "guarded"}:
        pool = ["…yeah.", "Mm.", "Hm.", "…hm.", "Uh… okay…", "Right…", "…what?", "Mhm."]
    elif att_raw in {"curious", "engaged"}:
        pool = ["Mm.", "Huh.", "…oh?", "Right.", "Yeah?", "Mhm."]
    else:
        pool = ["Mm.", "…yeah.", "Huh.", "Right…", "Yeah?", "…", "Mhm."]

    out = _personality_touch(_pick(pool), personality, band) or _pick(pool)
    return out.strip() if out.strip() else "…yeah."


def minimal_verbal_ack_for_do_action(
    action: str,
    count: int,
    state: Mapping[str, Any],
    personality: str,
    brain: Optional[Mapping[str, Any]] = None,
) -> str:
    """
    Last resort after Crow Brain. Prefer forced social; bare micro-grunts are rare on count > 2.
    """
    s = maybe_social_verbal_for_do_action(action, count, state, personality, force=True)
    if s:
        return s
    if count <= 2:
        return bare_micro_ack_for_do_action(state, personality, brain)
    if random.random() < 0.12:
        return bare_micro_ack_for_do_action(state, personality, brain)
    band = _social_band(state)
    return _forced_fallback_social(action, count, band)
