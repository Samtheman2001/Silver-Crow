"""
Dropdown SAY intelligence: direct answers, families, validation, emotional progression.

Works with behavior_gate (mode / question_type already in session).
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import streamlit as st

from behavior_gate import (
    CHALLENGE,
    DEFAULT_MIXED,
    EMOTIONAL_PRESSURE,
    FACTUAL_PERSONAL,
    NEUTRAL_SOCIAL,
    NONSENSE_RANDOM,
    OPINION,
    REPEAT_REDUNDANT,
    SESSION_MODE_KEY,
    try_direct_free_text_answer,
)
from emotional_subtype import (
    ACCUSATION_HURT,
    CONTROL_PROBE,
    OPEN_SOCIAL_REENGAGE,
    PRESSURE_DEFAULT,
    REPAIR_ATTEMPT,
    ROMANTIC_PRESSURE,
    STATUS_CHALLENGE,
    SUPPORT_OFFER,
    TRUST_CHALLENGE,
    VALIDATION_SEEKING,
    get_recent_subtype_history,
    has_recent_tension,
    is_false_softness_transition,
    reset_emotional_subtype_history,
)
from archetype_layer import ARCHETYPE_DEBUG_KEY, merge_tier_triples
from trajectory_layer import TRAJECTORY_DEBUG_KEY
from callback_memory import (
    CALLBACK_DEBUG_KEY,
    try_callback_menu_override,
)
from canon_prompts import get_canonical_menu_response, has_canon_bank
from config import SAY_OPTIONS
from interaction_profile import snapshot_profile
from scenario_layer import resolve_scenario_adjustments
from response_voice import maybe_sharpen_response
from utils import strip_outer_quotes

MENU_EMOTIONAL_PRESSURE_KEY = "menu_emotional_pressure_state"

# --- Low-stakes personal (stat softening + direct-answer bias) ---
_LOW_STAKES_EXACT = {
    "Where did you get those shoes?",
    "Do you own a jetski?",
    "What's your name?",
    "Are you having a good day?",
    "What are you up to today?",
    "Do you come here often?",
    "Can you help me?",
    "What are your thoughts on this weather?",
    "Hey, how are you?",
    "What's up?",
    "Do you mind if I sit here?",
    "Hello, nice to meet you.",
    "Nice to meet you",
    "What do you need?",
    "I want to help.",
    "I respect your opinion.",
}


def is_low_stakes_personal_prompt(text: str) -> bool:
    t = (text or "").strip()
    if t in _LOW_STAKES_EXACT:
        return True
    low = t.lower()
    if any(
        p in low
        for p in (
            "what do you do",
            "where do you work",
            "what's your job",
            "whats your job",
        )
    ):
        return True
    return False


def soften_low_stakes_menu_mods(mods: Dict[str, int]) -> Dict[str, int]:
    """Reduce confusion/stress spikes from ordinary small talk."""
    out = dict(mods)
    for k in ("confusion", "stress"):
        if k in out and out[k] > 0:
            out[k] = max(0, int(round(out[k] * 0.42)))
    if "interest" in out and out["interest"] > 6:
        out["interest"] = min(out["interest"], 6)
    return out


# --- Generic engaged / filler that must not answer concrete menu prompts ---
_BAD_GENERIC_SUBSTRINGS = (
    "you have my attention",
    "that's actually interesting",
    "now we're getting somewhere",
    "anyway. you were saying",
    "anyway you were saying",
    "where are you going with this",
    "what are you getting at",
)

_OPEN_ENDED_HINTS = (
    "tell me more",
    "what's on your mind",
    "whats on your mind",
    "go on",
    "continue",
    "say more",
    "elaborate",
)


def _is_open_ended_menu_prompt(ui: str) -> bool:
    low = ui.lower()
    return any(h in low for h in _OPEN_ENDED_HINTS)


def menu_response_addresses_prompt(user_input: str, response: str, question_type: str) -> bool:
    """Reject replies that ignore what the menu line actually asked."""
    ui = (user_input or "").strip().lower()
    inner = strip_outer_quotes(response).strip().lower()
    inner_c = " ".join(inner.split())

    if not inner_c:
        return False

    if question_type in (CHALLENGE, EMOTIONAL_PRESSURE, REPEAT_REDUNDANT, NONSENSE_RANDOM):
        return True

    if _is_open_ended_menu_prompt(ui):
        return True

    for bad in _BAD_GENERIC_SUBSTRINGS:
        if bad in inner_c:
            return False

    # Short pure backchannels fail unless prompt is phatic
    if len(inner_c) <= 18 and inner_c.rstrip(".!?") in (
        "yeah",
        "okay",
        "ok",
        "sure",
        "mhm",
        "mm",
        "uh huh",
        "right",
        "go on",
        "say more",
        "yeah?",
        "and?",
    ):
        if not any(x in ui for x in ("hey", "hi", "hello", "what's up", "whats up", "how are you")):
            return False

    def _needs(*words: str) -> bool:
        return any(w in ui for w in words)

    def _has(*words: str) -> bool:
        return any(w in inner_c for w in words)

    if "attractive" in ui and "history" in ui:
        return len(inner_c) >= 10 or _has(
            "howell", "rank", "trap", "pass", "bracket", "humanity", "polarizing", "cheesy", "game show"
        )

    if _needs("weather"):
        return _has("hot", "cold", "rain", "sunny", "nice", "gross", "humid", "freezing", "warm", "bad", "good", "fine", "terrible", "weird", "can't complain", "crazy out", "miserable", "beautiful")
    if _needs("help me", "help?"):
        return _has("help", "what", "need", "with", "sure", "maybe", "depends", "what's wrong", "whats wrong", "talk", "here")
    if _needs("shoes"):
        return _has("store", "online", "amazon", "mall", "got", "gift", "thrift", "ordered", "forgot", "old", "sale", "random")
    if _needs("jetski") and "thought" not in ui:
        return _has("no", "nah", "nope", "yeah", "yes", "wish", "own", "jet", "ski", "boat", "sold")
    if "jetski" in ui and "thought" in ui:
        return len(inner_c) >= 12 or _has("fun", "loud", "danger", "overrated", "ridiculous", "love", "hate")
    if _needs("republican", "democrat"):
        return _has("politic", "vote", "party", "independent", "rather not", "don't talk", "dont talk", "pass", "private", "both", "neither", "lean")
    if _needs("stock market", "stocks"):
        return _has("market", "stock", "crazy", "up", "down", "risk", "bubble", "honestly", "wild", "volatile", "no idea")
    if _needs("carti", "overrated"):
        return len(inner_c) >= 10
    if _needs("attractive", "think i'm", "think i am"):
        return _has("yeah", "alright", "cute", "not", "maybe", "honest", "fishing", "why", "ugly", "fine", "look")
    if _needs("like me") and "date" not in ui:
        return len(inner_c) >= 8
    if _needs("go on a date", "date?"):
        return len(inner_c) >= 6
    if _needs("why don't you like"):
        return len(inner_c) >= 14 or _has("because", "fair", "harsh", "don't", "dont", "not", "yet")
    if _needs("treating me", "acting like this"):
        return len(inner_c) >= 12
    if _needs("think of me so far"):
        return _has("alright", "honest", "early", "hard", "fine", "okay", "lot", "yet")
    if _needs("young gangsta", "get money"):
        return _has("mean", "what", "serious", "talking", "street", "job", "honest")
    if "cash me outside" in ui:
        return _has("joking", "serious", "what", "tv", "internet", "old", "reference")
    if _needs("funny") and "you're" in ui:
        return len(inner_c) >= 10
    if _needs("quiet"):
        return len(inner_c) >= 10
    if _needs("looking at me"):
        return len(inner_c) >= 10
    if _needs("talking to me"):
        return len(inner_c) >= 10
    if _needs("sleep at your house"):
        return len(inner_c) >= 12 or _has("no", "nah", "absolutely not", "weird")

    if question_type in (FACTUAL_PERSONAL, OPINION, NEUTRAL_SOCIAL) or question_type == DEFAULT_MIXED:
        if len(inner_c) < 10 and inner_c in ("yeah.", "okay.", "sure.", "fine.", "alright.", "mhm."):
            return False

    return True


def _finalize_menu_line(
    line: Optional[str],
    user_input: str,
    qt: str,
    state: Dict[str, Any],
    personality: str,
) -> Optional[str]:
    """Sharpen phrasing when safe; never drop content-match validity."""
    if not line:
        return None
    adj = st.session_state.get("_trajectory_adj") or {}
    sharp = maybe_sharpen_response(
        line,
        state,
        personality or "",
        voice_sharpen_bias=float(adj.get("voice_sharpen_bias") or 0.0),
    )
    if sharp != line and menu_response_addresses_prompt(user_input, sharp, qt):
        return sharp
    return line


def _pressure_tier() -> int:
    d = st.session_state.get(MENU_EMOTIONAL_PRESSURE_KEY) or {}
    c = int(d.get("count", 0))
    return min(3, c)


def register_emotional_menu_prompt(menu_text: str) -> None:
    d = dict(st.session_state.get(MENU_EMOTIONAL_PRESSURE_KEY) or {})
    d["count"] = int(d.get("count", 0)) + 1
    recent = list(d.get("recent", []))
    recent.append((menu_text or "").strip())
    d["recent"] = recent[-12:]
    st.session_state[MENU_EMOTIONAL_PRESSURE_KEY] = d


def reset_menu_emotional_pressure() -> None:
    st.session_state[MENU_EMOTIONAL_PRESSURE_KEY] = {"count": 0, "recent": []}
    reset_emotional_subtype_history()


# --- Response families ---
def _factual_personal_answers(personality: str) -> List[str]:
    base = [
        "Nah.",
        "Nope.",
        "I wish.",
        "Not anymore.",
        "Sometimes.",
        "Why—random question.",
        "Yeah, actually.",
        "A little bit.",
    ]
    blend = {
        "Shy": ["Um… no?", "Not really.", "That's kinda personal."],
        "Aggressive": ["Why do you care?", "Nah.", "Figure it out."],
        "Empathetic": ["Not really—why do you ask?", "I don't. Should I?"],
        "Analytical": ["No. Why?", "Depends what you mean by that."],
        "Impulsive": ["Nah lol.", "No. Weird ask."],
        "Confident": ["Nope.", "If I did, you'd hear about it."],
    }
    return base + blend.get(personality, [])


def _neutral_social_answers(personality: str) -> List[str]:
    base = [
        "Not much.",
        "Long day.",
        "Just chilling.",
        "Running around.",
        "Same old.",
        "I'm alright. You?",
        "Fine. You?",
    ]
    blend = {
        "Shy": ["Oh—hey.", "Hi.", "I'm okay…"],
        "Aggressive": ["What's it to you?", "Fine.", "Busy."],
        "Empathetic": ["I'm hanging in. You?", "Pretty okay. What's up with you?"],
        "Analytical": ["Fine. Why?", "Alright."],
        "Impulsive": ["Yo. Not much.", "Eh. You?"],
        "Confident": ["Solid. You?", "Good. What's good with you?"],
    }
    return base + blend.get(personality, [])


def _opinion_answers(personality: str) -> List[str]:
    base = [
        "It's fine.",
        "Could be worse.",
        "Not my lane.",
        "I'm not deep on that.",
        "Strong take: who cares.",
    ]
    blend = {
        "Shy": ["It's… okay?", "Normal enough."],
        "Aggressive": ["Why are we talking about this?", "It's whatever."],
        "Empathetic": ["Kinda nice out.", "I'm not complaining."],
        "Analytical": ["Within normal range.", "I'd need a forecast to care more."],
        "Impulsive": ["Mid.", "It's weather."],
        "Confident": ["It's doing its job.", "Fine enough.", "Not worth a debate."],
    }
    return base + blend.get(personality, [])


def _mild_repeat_answers() -> List[str]:
    return [
        "You already asked that.",
        "Same answer as before.",
        "We just did this.",
        "Still me. Still here.",
    ]


def _challenge_answers(bucket: str) -> List[str]:
    m = {
        "positive": ["Say it nicer and I'll engage.", "Bold. Keep going.", "Alright—prove it."],
        "neutral": ["That's a choice.", "Okay.", "You sure about that?"],
        "negative": ["Watch yourself.", "Nah.", "You don't know me like that."],
        "severe": ["Try again with respect.", "No.", "We're not doing this."],
    }
    return list(m.get(bucket, m["neutral"]))


def _clarifying_answers(topic: str) -> List[str]:
    if topic == "gangsta_money":
        return [
            "What do you mean by that?",
            "You being serious or is this a bit?",
            "Say that in normal words.",
        ]
    if topic == "cash_outside":
        return [
            "You joking or serious?",
            "That reference is ancient.",
            "Where is this coming from?",
        ]
    return ["What do you mean?", "Say that a different way.", "Be specific."]


def _emotional_pressure_answers(action_text: str, bucket: str, tier: int) -> List[str]:
    low = action_text.lower()
    tier = max(0, min(3, tier))

    def scale(lines_soft: List[str], lines_mid: List[str], lines_hard: List[str]) -> List[str]:
        if tier <= 0:
            return lines_soft
        if tier == 1:
            return lines_soft + lines_mid
        if tier == 2:
            return lines_mid + lines_hard
        return lines_hard + lines_mid

    if "date" in low:
        soft = ["That's a lot out of nowhere.", "Slow down.", "A date? Just like that?"]
        mid = ["I'm not there yet.", "Let's not rush that.", "Too fast for me."]
        hard = ["No. And don't push it.", "I'm not doing this pressure thing.", "Stop."]
        return scale(soft, mid, hard)

    if "why don't you like me" in low:
        soft = ["I didn't say I don't.", "That's heavy.", "I barely know you."]
        mid = ["Don't put words in my mouth.", "You're assuming a lot.", "This isn't a fair question."]
        hard = ["I'm not doing this interrogation.", "Back up.", "Enough."]
        return scale(soft, mid, hard)

    if "treating me" in low or "acting like this" in low:
        soft = ["I'm just being me.", "What are you seeing?", "Tell me what you mean."]
        mid = ["You're reading into it.", "I'm not trying to mess with you.", "Dial it back."]
        hard = ["You're making this weird.", "Stop.", "I'm done with this angle."]
        return scale(soft, mid, hard)

    if "think of me so far" in low:
        soft = ["Too early for a verdict.", "You're alright.", "Still figuring you out."]
        mid = ["I don't do instant reviews.", "Ask me later.", "Mixed bag."]
        hard = ["I'm not grading you.", "Weird question.", "Pass."]
        return scale(soft, mid, hard)

    if "like me" in low and "date" not in low:
        bmap = {
            "positive": ["Yeah—so far.", "You're cool.", "I do, actually."],
            "neutral": ["You're alright.", "Maybe.", "Too early."],
            "negative": ["Not really.", "You're making it weird.", "I don't know you like that."],
            "severe": ["No.", "Stop fishing.", "Don't ask me that like that."],
        }
        lines = list(bmap.get(bucket, bmap["neutral"]))
        if tier >= 2:
            lines += ["I already answered this.", "Again?", "You're repeating yourself."]
        return lines

    # default emotional
    return scale(
        ["That's a lot.", "Where's this coming from?", "Say that slower."],
        ["Chill.", "Slow down.", "You're doing a lot right now."],
        ["I'm not doing this.", "Stop.", "We're done with this topic."],
    )


_DISCOMFORT_PHRASES = (
    "i need a second",
    "this is getting uncomfortable",
    "be careful right now",
    "give me a second",
    "trying to stay calm",
)


def _strip_discomfort_candidates(
    pool: List[str],
    state: Dict[str, Any],
    pressure_count: int = 0,
) -> List[str]:
    """Keep stall/discomfort lines only under real sustained pressure + high arousal."""
    stress = int(state.get("stress", 0))
    anger = int(state.get("anger", 0))
    pc = int(pressure_count)
    if stress >= 88 or anger >= 84:
        return pool
    sustained = pc >= 2 and (stress >= 74 or anger >= 68)
    if sustained and random.random() < 0.42:
        return pool
    out = [x for x in pool if not any(d in x.lower() for d in _DISCOMFORT_PHRASES)]
    return out if out else pool


_MID_TIER_SUBSTRINGS = (
    "maybe. depends",
    "maybe—depends",
    "i don't know",
    "don't know yet",
    "kind of ",
    "kinda ",
    "sort of ",
    "it depends",
    "not sure",
    "i guess",
    "probably not",
    "could be",
)


def _is_mid_tier_bland(line: str) -> bool:
    l = (line or "").lower().strip()
    if any(s in l for s in _MID_TIER_SUBSTRINGS):
        return True
    if len(l) <= 14 and l.rstrip(".!?") in (
        "it's fine",
        "okay",
        "ok",
        "alright",
        "sure",
        "yeah",
        "maybe",
        "i guess",
    ):
        return True
    return False


def _tier_from_pressure(pressure_count: int, same_subtype_streak: int) -> int:
    t = int(pressure_count) + int(same_subtype_streak)
    return max(0, min(2, t))


def _same_subtype_streak(recent_subtypes: List[str], subtype: str) -> int:
    n = 0
    for x in reversed(recent_subtypes or []):
        if x == subtype:
            n += 1
        else:
            break
    return n


def _transition_lines(prev: str, curr: str) -> List[str]:
    key = (prev, curr)
    m = {
        (STATUS_CHALLENGE, REPAIR_ATTEMPT): [
            "That's a fast switch.",
            "Now you're cleaning it up.",
            "Pick a lane.",
            "Okay… tone shift.",
        ],
        (ACCUSATION_HURT, SUPPORT_OFFER): [
            "That doesn't match how you were just talking.",
            "Help, or control?",
            "You mean that?",
            "Suddenly you're helpful?",
        ],
        (ROMANTIC_PRESSURE, VALIDATION_SEEKING): [
            "Whoa—pile on.",
            "That's a jump.",
            "One thing at a time.",
            "Slow down with the questions.",
        ],
        (VALIDATION_SEEKING, ROMANTIC_PRESSURE): [
            "You're not gonna let this go, huh?",
            "Different angle, same pressure.",
            "Okay. And?",
        ],
        (STATUS_CHALLENGE, OPEN_SOCIAL_REENGAGE): [
            "Now you want small talk?",
            "That's a weird follow-up.",
            "You switching subjects on purpose?",
        ],
        (ACCUSATION_HURT, OPEN_SOCIAL_REENGAGE): [
            "Now you want normal?",
            "You're changing the tone.",
            "I've been better, honestly.",
        ],
    }
    return list(m.get(key, []))


_FALSE_SOFT_LINES = [
    "That's a sudden change.",
    "Now you want to soften it?",
    "You weren't talking like that a second ago.",
    "Don't switch up on me now.",
    "Okay… that came out of nowhere.",
]


def select_emotional_menu_response(
    user_input: str,
    state: Dict[str, Any],
    mode: Dict[str, Any],
    subtype: str,
    pressure_count: int,
    recent_subtypes: List[str],
    bucket: str = "neutral",
) -> Optional[str]:
    """
    Subtype- and transition-aware lines for loaded dropdown SAY prompts.
    """
    ui = (user_input or "").strip()
    qt = str(mode.get("question_type", DEFAULT_MIXED))
    if subtype == PRESSURE_DEFAULT and qt not in (EMOTIONAL_PRESSURE, CHALLENGE):
        return None

    prev = recent_subtypes[-1] if recent_subtypes else ""
    romantic_streak = sum(1 for x in (recent_subtypes or [])[-4:] if x == ROMANTIC_PRESSURE)
    streak = _same_subtype_streak(recent_subtypes, subtype)
    tier = _tier_from_pressure(pressure_count, streak + (romantic_streak if subtype == ROMANTIC_PRESSURE else 0))
    pc_menu = int((st.session_state.get(MENU_EMOTIONAL_PRESSURE_KEY) or {}).get("count", 0))
    mem_fb = st.session_state.get("conversation_memory") or {}
    press_mem = int(mem_fb.get("pressure_score", 0) or 0)
    flirt_mem = int(mem_fb.get("flirtation_score", 0) or 0)
    turn_n = int(st.session_state.get("turns", 0) or 0)
    conv_esc = min(
        2,
        (press_mem // 26) + (flirt_mem // 34) + max(0, (turn_n - 1) // 5),
    )
    tier = min(2, tier + conv_esc)

    candidates: List[str] = []

    if is_false_softness_transition(subtype, recent_subtypes):
        candidates.extend(_FALSE_SOFT_LINES)

    if prev:
        candidates.extend(_transition_lines(prev, subtype))

    if (streak >= 2 or pc_menu >= 2) and random.random() < 0.66:
        candidates.extend(
            [
                "Pick a lane.",
                "You're doing too much.",
                "We going in circles?",
                "That's not what you just said.",
                "Now you're switching it up.",
            ]
        )

    # --- Subtype pools (short, spoken; avoid stall unless tier high) ---
    rp_t0 = [
        "That's a lot.",
        "You move fast.",
        "Slow down.",
        "Out of nowhere.",
        "Whoa—okay.",
        "That's direct.",
        "I'm not sprinting this.",
        "We barely started talking.",
        "Bold question.",
        "Didn't see that coming.",
        "Pump the brakes.",
        "That's forward.",
    ]
    rp_t1 = [
        "No, seriously—back up a little.",
        "I'm not there yet.",
        "Don't push it like that.",
        "That's a lot to drop on me.",
        "I'm not playing that game.",
        "Pump the brakes.",
        "You're doing a lot.",
        "I'm not comfortable with that pace.",
    ]
    rp_t2 = [
        "Stop pushing this.",
        "I'm not doing this pressure thing.",
        "No. And don't ask again like that.",
        "Enough with that.",
        "We're done with this topic.",
    ]

    val_t0 = [
        "You're asking a lot right now.",
        "I don't know you like that yet.",
        "Why do you need me to say that?",
        "You're putting me in a weird spot.",
        "That's heavy for how long we've talked.",
        "I can't feed you that answer.",
        "You're fishing.",
        "I'm not your mirror.",
        "That's a setup.",
        "I barely have a read on you.",
        "What are you looking for here?",
        "That's not my job to prove.",
    ]
    val_t1 = [
        "Don't put words in my mouth.",
        "You're assuming a lot.",
        "I'm not signing up for that judgment.",
        "That's not how this works.",
        "You're making me the bad guy.",
    ]
    val_t2 = [
        "I'm not doing this interrogation.",
        "Back up.",
        "Enough.",
        "Stop testing me.",
    ]

    acc_t0 = [
        "What do you think I'm doing?",
        "You're reading a lot into this.",
        "I'm not. You're making it heavier.",
        "Say what you mean.",
        "Because you're coming at me sideways.",
        "I'm just sitting here.",
        "You're projecting.",
        "That's a you problem.",
        "I'm not picking a fight—you are.",
        "What exactly is the issue?",
        "Tone check.",
        "I'm not the villain in your head.",
    ]
    acc_t1 = [
        "Dial it back.",
        "You're not giving me room to breathe.",
        "I'm not your enemy.",
        "That's not what's happening.",
    ]
    acc_t2 = [
        "Stop.",
        "I'm done with this angle.",
        "You're making this weird.",
    ]

    st_t0 = {
        "positive": ["Say it nicer and I'll hear you.", "Alright—make your point.", "Bold. Keep going."],
        "neutral": ["That's a choice.", "Okay.", "You sure?", "Watch the tone.", "Nah.", "I said what I said."],
        "negative": ["Watch how you talk to me.", "No.", "You don't know me like that.", "Try again with respect."],
        "severe": ["No.", "We're not doing this.", "Say that again and see what happens."],
    }
    st_lines = list(st_t0.get(bucket, st_t0["neutral"])) + [
        "Then say your point.",
        "I don't owe you a debate.",
        "You're loud—prove it.",
        "Cool story. Evidence?",
        "I'm not folding because you're mad.",
        "Say it with your chest.",
    ]

    trust_t = [
        "You shouldn't. We just met.",
        "You don't have to.",
        "I didn't ask you to.",
        "What do you mean by that?",
        "Earn it. I'm not pitching myself.",
        "That's on you.",
        "Fair question. Still—slow.",
        "I'm not asking for blind trust.",
        "Then don't—yet.",
        "Time will tell.",
        "I get why you'd ask.",
        "Nobody hands trust out on command.",
    ]

    ctrl_t = [
        "Why are you asking?",
        "Why?",
        "What are you getting at?",
        "Nothing crazy. What's up?",
        "You first.",
        "What's the angle?",
        "Just talking.",
        "Curious.",
        "Why the interrogation vibe?",
        "Say it plain.",
        "I'm not hiding anything weird.",
        "Know what you want, then ask.",
    ]

    rep_high = [
        "That's better.",
        "Now you're changing the tone.",
        "Okay. That's different.",
        "Don't clean it up now.",
        "I'll take it—if you mean it.",
        "Alright. I hear you.",
        "Too smooth, but okay.",
        "Fine. Let's reset a little.",
    ]
    rep_low = [
        "Thanks.",
        "Fair.",
        "Alright.",
        "Good to know.",
        "Noted.",
    ]

    sup_t = [
        "Help with what?",
        "Talk. What's actually wrong?",
        "I'm listening.",
        "That's not what this is.",
        "You mean that or are you smoothing this over?",
        "Say what you need.",
        "What kind of help?",
        "Could be. Talk to me.",
        "I'm not signing up blind.",
        "Alright—what's going on?",
        "If it's real, say it straight.",
        "Don't use 'help' like a trap.",
        "Okay… what's the actual problem?",
        "I'll hear you out—if it's real.",
        "Sounds convenient.",
    ]

    open_t0 = [
        "Long day.",
        "Not much.",
        "I've been better.",
        "What do you want?",
        "Now you're switching it up.",
        "Same old.",
        "Eh.",
        "I'm here.",
        "Could be worse.",
        "Fine enough.",
    ]
    open_tense = [
        "Now you want normal?",
        "You're changing the tone.",
        "After all that?",
        "Okay… hi.",
        "Sure. What's up.",
        "Dry, but hi.",
        "I'm tired, but go ahead.",
    ]

    def pick3(a: List[str], b: List[str], c: List[str]) -> List[str]:
        if tier <= 0:
            return list(a)
        if tier == 1:
            return list(a) + list(b)
        return list(b) + list(c)

    if subtype == ROMANTIC_PRESSURE:
        candidates.extend(pick3(rp_t0, rp_t1, rp_t2))
    elif subtype == VALIDATION_SEEKING:
        candidates.extend(pick3(val_t0, val_t1, val_t2))
    elif subtype == ACCUSATION_HURT:
        candidates.extend(pick3(acc_t0, acc_t1, acc_t2))
    elif subtype == STATUS_CHALLENGE:
        candidates.extend(st_lines)
    elif subtype == TRUST_CHALLENGE:
        candidates.extend(trust_t)
    elif subtype == CONTROL_PROBE:
        candidates.extend(ctrl_t)
    elif subtype == REPAIR_ATTEMPT:
        if int(state.get("stress", 0)) > 62 or int(state.get("anger", 0)) > 55:
            candidates.extend(rep_high)
        else:
            candidates.extend(rep_low + rep_high)
    elif subtype == SUPPORT_OFFER:
        candidates.extend(sup_t)
    elif subtype == OPEN_SOCIAL_REENGAGE:
        if has_recent_tension(recent_subtypes, state):
            candidates.extend(open_t0 + open_tense)
        else:
            candidates.extend(open_t0)
    elif qt == EMOTIONAL_PRESSURE or qt == CHALLENGE:
        candidates.extend(
            pick3(
                ["That's a lot.", "Okay…", "Where's this coming from?", "Say that again slower."],
                ["Slow down.", "You're doing a lot.", "I'm not playing.", "Chill."],
                ["Stop.", "Enough.", "We're not doing this loop."],
            )
        )

    if not candidates:
        return None

    candidates = _strip_discomfort_candidates(candidates, state, pc_menu)
    line = _pick_valid(candidates, ui, qt)
    return line


def _use_emotional_subtype_layer(
    ui: str,
    mode: Dict[str, Any],
    state: Dict[str, Any],
    recent_subtypes: List[str],
) -> bool:
    est = str(mode.get("emotional_subtype", PRESSURE_DEFAULT))
    qt = str(mode.get("question_type", DEFAULT_MIXED))
    loaded = {
        ROMANTIC_PRESSURE,
        VALIDATION_SEEKING,
        ACCUSATION_HURT,
        STATUS_CHALLENGE,
        TRUST_CHALLENGE,
        CONTROL_PROBE,
        REPAIR_ATTEMPT,
        SUPPORT_OFFER,
    }
    if est in loaded:
        return True
    if est == OPEN_SOCIAL_REENGAGE and has_recent_tension(recent_subtypes, state):
        return True
    if qt in (EMOTIONAL_PRESSURE, CHALLENGE):
        return True
    if has_recent_tension(recent_subtypes, state) and is_low_stakes_personal_prompt(ui):
        return True
    return False


def _pick_valid(
    candidates: Sequence[str],
    user_input: str,
    qt: str,
    tries: int = 8,
) -> Optional[str]:
    pool = list(candidates)
    lean = [x for x in pool if not _is_mid_tier_bland(x)]
    if lean and random.random() < 0.64:
        pool = lean + [x for x in pool if x not in lean]
    random.shuffle(pool)
    for line in pool[: min(len(pool), tries)]:
        if menu_response_addresses_prompt(user_input, line, qt):
            return line
    for line in pool[min(len(pool), tries) :]:
        if menu_response_addresses_prompt(user_input, line, qt):
            return line
    return None


def try_direct_menu_answer(
    user_input: str,
    state: Dict[str, Any],
    mode: Dict[str, Any],
    bucket: str = "neutral",
) -> Optional[str]:
    """
    Exact-menu and phrase-aligned direct lines (inner text, {name} allowed).
    """
    ui = (user_input or "").strip()
    if not ui:
        return None

    qt = mode.get("question_type", DEFAULT_MIXED)
    personality = (st.session_state.get("build_snapshot") or {}).get("Personality", "Confident")

    # Mirror free-text layer for overlapping semantics
    ft = try_direct_free_text_answer(ui, personality, qt)
    if ft and menu_response_addresses_prompt(ui, ft, qt):
        return ft

    low = ui.lower()
    exact: Dict[str, List[str]] = {
        "Do you own a jetski?": ["Nah.", "No.", "I wish.", "Not even close.", "Why?"],
        "What's up?": ["Not much.", "Long day.", "Just here.", "Same old. You?"],
        "What are you up to today?": ["Just out.", "Not much.", "Running errands.", "Nothing wild."],
        "Do you come here often?": ["Sometimes.", "Here and there.", "Not really.", "Often enough."],
        "Can you help me?": ["Maybe—what do you need?", "Depends. With what?", "Talk to me.", "What's going on?"],
        "Where did you get those shoes?": ["Online.", "A store.", "I've had them forever.", "Random shop."],
        "What are your thoughts on this weather?": [
            "It's fine.",
            "Kinda gross out, honestly.",
            "Not bad today.",
            "Could be worse.",
        ],
        "Would you like to buy my jetski?": ["I'm good.", "Nah.", "That's random.", "Not in the market."],
        "Why are you talking to me?": ["You started it.", "Just being polite.", "Why not?", "Figured I'd say something."],
        "Why do you care?": ["Maybe I don't.", "Fair question.", "Curious.", "Just asking."],
        "What do you want?": ["Clarity.", "Nothing weird.", "To see where this goes.", "Same as you—figure it out."],
        "Do you think you're funny?": ["Sometimes.", "I've heard worse.", "I try.", "You tell me."],
        "Do you think you're better than me?": ["I didn't say that.", "No.", "Why would you ask that?", "We're not doing this."],
        "Can I sleep at your house tonight?": ["No.", "Absolutely not.", "That's a wild ask.", "Nah. Hard no."],
        "Are you Republican or Democrat?": [
            "I don't really do politics with strangers.",
            "I'd rather not go there.",
            "Independent, if it matters.",
            "Why—are you testing me?",
        ],
        "What are your thoughts on the stock market these days?": [
            "Wild.",
            "Up and down.",
            "Not my department.",
            "Feels risky out there.",
        ],
        "What are your thoughts on jetskis?": [
            "Loud fun.",
            "Not for me.",
            "They're a vibe if you like water.",
            "Kinda ridiculous—in a good way.",
        ],
        "Is Playboi Carti overrated?": [
            "He's polarizing.",
            "Depends who you ask.",
            "Sometimes yes, sometimes no.",
            "People argue about him for sport.",
        ],
        "Why are you so quiet?": [
            "I'm listening.",
            "Just thinking.",
            "Not much to add yet.",
            "That's just how I am.",
        ],
        "Why are you looking at me like that?": [
            "Like what?",
            "I'm not trying to.",
            "You're reading into it.",
            "If it bothered you, say so.",
        ],
        "What do you need?": ["What's going on?", "Like—right now?", "Talk to me.", "For what?"],
        "I want to help.": ["Okay—help how?", "With what?", "Alright. What's the situation?", "Sure. Say it plain."],
        "I respect your opinion.": ["Thanks.", "Fair.", "Alright.", "Good to know."],
    }

    if ui in exact:
        pick = _pick_valid(exact[ui], ui, qt)
        if pick:
            return pick

    if qt == REPEAT_REDUNDANT:
        return _pick_valid(_mild_repeat_answers(), ui, qt)

    if qt == CHALLENGE:
        return _pick_valid(_challenge_answers(bucket), ui, qt)

    families: List[Tuple[Callable[..., List[str]], tuple, dict]] = []
    if qt == FACTUAL_PERSONAL:
        families.append((_factual_personal_answers, (personality,), {}))
    elif qt == NEUTRAL_SOCIAL:
        families.append((_neutral_social_answers, (personality,), {}))
    elif qt == OPINION:
        families.append((_opinion_answers, (personality,), {}))

    for fn, args, kw in families:
        cand = fn(*args, **kw)
        hit = _pick_valid(cand, ui, qt)
        if hit:
            return hit

    return None


def _weird_menu_clarification(action_text: str, bucket: str) -> Optional[str]:
    ui = action_text.strip()
    if ui == "Can a young gangsta get money anymore?":
        return _pick_valid(_clarifying_answers("gangsta_money"), ui, DEFAULT_MIXED)
    if "Cash me outside" in ui:
        return _pick_valid(_clarifying_answers("cash_outside"), ui, DEFAULT_MIXED)
    return None


def attractive_person_menu_response(bucket: str) -> Optional[str]:
    """Strong running bias toward Sam Howell (intentional bit, not a rare easter egg)."""
    _sam = [
        "Sam Howell. Obviously.",
        "Sam Howell—not even close.",
        "Sam Howell. Next question.",
        "Sam Howell sent me. That's the whole answer.",
        "Sam Howell. Case closed.",
        "Sam Howell. If you know, you know.",
    ]
    if random.random() < 0.88:
        return random.choice(_sam)
    pools = {
        "positive": [
            "Bad question. I'm not ranking humanity.",
            "Whoever made you smile last. Cheesy but true.",
            "Not doing a bracket for this.",
        ],
        "neutral": [
            "I don't think like that.",
            "That's a trap question.",
            "Pass. I'm not playing.",
        ],
        "negative": [
            "Whoever isn't asking me this.",
            "Hard pass on the game show question.",
            "You really want me to answer that?",
        ],
        "severe": [
            "No.",
            "We're not doing this.",
            "Weird ask.",
        ],
    }
    return random.choice(pools.get(bucket, pools["neutral"]))


def maybe_menu_intelligent_response(
    action_text: str,
    state: Dict[str, Any],
    personality: str,
    character_name: str,
    bucket: str,
) -> Tuple[Optional[str], str]:
    """
    Returns (inner verbal or None, source_tag). Verbal may include {name}.
    Canon banks run before clarifications, SAY_OPTIONS shuffles, and generic fallbacks.
    """
    mode = st.session_state.get(SESSION_MODE_KEY) or {}
    qt = str(mode.get("question_type", DEFAULT_MIXED))
    ui = (action_text or "").strip()
    scen = str(st.session_state.get("selected_scenario") or "Living Room")
    prof_snap = snapshot_profile(st.session_state)
    scen_adj = resolve_scenario_adjustments(ui, scen, prof_snap, current_bucket=bucket)
    st.session_state["_scenario_layer_last"] = scen_adj

    def out(line: Optional[str], tag: str) -> Tuple[Optional[str], str]:
        if line is None:
            return None, tag
        return _finalize_menu_line(line, ui, qt, state, personality), tag

    sig = st.session_state.get("_callback_signals") or {}
    rpc = int((st.session_state.get("repeat_counts") or {}).get(ui, 0) or 0)
    arch_adj = st.session_state.get("_archetype_adj") or {}
    traj_adj = st.session_state.get("_trajectory_adj") or {}
    cb_mult = float(arch_adj.get("callback_probability_mult") or 1.0) * float(
        traj_adj.get("callback_probability_mult") or 1.0
    )

    cb_line, cb_type = try_callback_menu_override(
        ui, bucket, sig, rpc, probability_mult=cb_mult, session=st.session_state
    )
    if cb_line and menu_response_addresses_prompt(ui, cb_line, REPEAT_REDUNDANT):
        _dbg = st.session_state.get(CALLBACK_DEBUG_KEY)
        if isinstance(_dbg, dict):
            _dbg["override_used"] = True
            _dbg["override_type"] = cb_type
            _dbg["response_source_tag"] = f"callback:{cb_type}"
        _adbg = st.session_state.get(ARCHETYPE_DEBUG_KEY)
        if isinstance(_adbg, dict) and float(arch_adj.get("callback_probability_mult") or 1.0) != 1.0:
            _adbg.setdefault("influenced", {})["callback_override"] = True
        _tdbg = st.session_state.get(TRAJECTORY_DEBUG_KEY)
        if isinstance(_tdbg, dict) and float(traj_adj.get("callback_probability_mult") or 1.0) != 1.0:
            _tdbg.setdefault("influenced", {})["callback_override"] = True
        return out(cb_line, f"callback:{cb_type}")

    # 1) Word of God: canonical authored prompt bank (before any other menu layer).
    if has_canon_bank(ui):
        twb = scen_adj.get("tier_weight_bonus")
        bonus_a = tuple(twb) if isinstance(twb, (list, tuple)) and len(twb) == 3 else None
        cb_b = sig.get("tier_bonus")
        bonus_b = tuple(cb_b) if isinstance(cb_b, (list, tuple)) and len(cb_b) == 3 else None
        arch_tb = arch_adj.get("tier_bonus")
        arch_part = tuple(arch_tb) if isinstance(arch_tb, (list, tuple)) and len(arch_tb) == 3 else None
        traj_tb = traj_adj.get("tier_bonus")
        traj_part = tuple(traj_tb) if isinstance(traj_tb, (list, tuple)) and len(traj_tb) == 3 else None
        base_merge = merge_tier_triples(bonus_a, bonus_b, None)
        if base_merge == (0, 0, 0):
            base_merge = None
        base_arch = merge_tier_triples(bonus_a, bonus_b, arch_part)
        if base_arch == (0, 0, 0):
            base_arch = None
        merged_bonus = merge_tier_triples(bonus_a, bonus_b, arch_part, traj_part)
        if merged_bonus == (0, 0, 0):
            merged_bonus = None
        elif arch_part and merged_bonus != base_merge:
            _adbg = st.session_state.get(ARCHETYPE_DEBUG_KEY)
            if isinstance(_adbg, dict):
                _adbg.setdefault("influenced", {})["tier"] = True
        if traj_part and merged_bonus != base_arch:
            _tdbg = st.session_state.get(TRAJECTORY_DEBUG_KEY)
            if isinstance(_tdbg, dict):
                _tdbg.setdefault("influenced", {})["tier"] = True
        canon = get_canonical_menu_response(
            ui,
            state=state,
            bucket=bucket,
            tier_weight_bonus=merged_bonus,
        )
        if canon and menu_response_addresses_prompt(ui, canon, qt):
            _dbg = st.session_state.get(CALLBACK_DEBUG_KEY)
            if isinstance(_dbg, dict):
                _dbg["response_source_tag"] = "canon"
            return out(canon, "canon")

    # 2) Topic-specific clarifications only if canon did not supply an answer
    weird = _weird_menu_clarification(ui, bucket)
    if weird:
        return out(weird, "weird_clarification")

    if ui == "Who is the most attractive person in history?":
        line = attractive_person_menu_response(bucket)
        if line and menu_response_addresses_prompt(ui, line, qt):
            return out(line, "attractive_person_special")

    recent_st = get_recent_subtype_history()
    est = str(mode.get("emotional_subtype", PRESSURE_DEFAULT))
    if _use_emotional_subtype_layer(ui, mode, state, recent_st):
        line = select_emotional_menu_response(
            ui,
            state,
            mode,
            est,
            _pressure_tier(),
            recent_st,
            bucket,
        )
        if line and menu_response_addresses_prompt(ui, line, qt):
            return out(line, "emotional_subtype")

    direct = try_direct_menu_answer(ui, state, mode, bucket=bucket)
    if direct and menu_response_addresses_prompt(ui, direct, qt):
        return out(direct, "direct_free_text_style")

    option = SAY_OPTIONS.get(ui)
    if isinstance(option, dict) and "responses" in option:
        responses = option["responses"].get(bucket, [])
        if responses:
            shuffled = list(responses)
            random.shuffle(shuffled)
            for raw_line in shuffled:
                test_line = raw_line.replace("{name}", character_name or "Alex")
                if menu_response_addresses_prompt(ui, test_line, qt):
                    return out(str(raw_line), "say_options_responses")

    if qt == EMOTIONAL_PRESSURE:
        tier = _pressure_tier()
        pool = _emotional_pressure_answers(ui, bucket, tier)
        line = _pick_valid(pool, ui, qt)
        if line:
            return out(line, "emotional_pressure_pool")

    # Family fallback by type
    if qt == FACTUAL_PERSONAL:
        hit = _pick_valid(_factual_personal_answers(personality), ui, qt)
        if hit:
            return out(hit, "factual_personal_fallback")
    if qt == NEUTRAL_SOCIAL:
        hit = _pick_valid(_neutral_social_answers(personality), ui, qt)
        if hit:
            return out(hit, "neutral_social_fallback")
    if qt == OPINION:
        hit = _pick_valid(_opinion_answers(personality), ui, qt)
        if hit:
            return out(hit, "opinion_fallback")
    if qt == CHALLENGE:
        hit = _pick_valid(_challenge_answers(bucket), ui, qt)
        if hit:
            return out(hit, "challenge_fallback")

    return None, "none"


def filter_generic_engaged_fallback_pool(
    pool: List[str],
    menu_action_text: Optional[str],
    question_type: str,
) -> List[str]:
    """Narrow 'engaged but vague' lines when the prompt is concrete."""
    if not menu_action_text:
        return pool
    if _is_open_ended_menu_prompt(menu_action_text.lower()):
        return pool
    if question_type in (FACTUAL_PERSONAL, OPINION, NEUTRAL_SOCIAL, CHALLENGE, EMOTIONAL_PRESSURE):
        banned = (
            "you have my attention",
            "now we're getting somewhere",
            "that's actually interesting",
            "go on.",
            "yeah?",
            "and?",
            "fair enough.",
            "that's fair.",
            "makes sense.",
        )
        out = [p for p in pool if not any(b in p.lower() for b in banned)]
        return out if out else pool
    return pool
