"""
Free-text classification + aggression tiers + CAT_MODE + comeback pools.
"""

from __future__ import annotations

import random

import streamlit as st

from .behavior_gate import try_direct_free_text_answer
from .brain import infer_tone, infer_vibe
from .memory import init_memory_state
from .utils import clamp01, normalize_speech, quote


def infer_physical_response(state):
    if state["anger"] > 82:
        return random.choice(
            [
                "furrows brow and looks like they're about to snap",
                "glares at you and pulls their shoulders tight",
                "locks their jaw and looks openly irritated",
            ]
        )
    if state["anger"] > 65:
        return random.choice(
            [
                "furrows brow and narrows their eyes",
                "leans back with visible irritation",
                "stares at you like your last line annoyed them",
            ]
        )
    if state["fear"] > 70:
        return random.choice(
            [
                "leans back and scans the room",
                "goes stiff and watches you carefully",
                "creates a little more distance without saying it",
            ]
        )
    if state["stress"] > 70:
        return random.choice(
            [
                "fidgets and shifts weight",
                "rubs their hands together and looks tense",
                "takes a breath like they're trying to stay composed",
            ]
        )
    if state["trust"] > 74 and state["happiness"] > 60:
        return random.choice(
            [
                "leans in and maintains eye contact",
                "looks more relaxed around you",
                "softens a little and stays engaged",
            ]
        )
    if state["confusion"] > 72:
        return random.choice(
            [
                "tilts head and tries to read what you mean",
                "pauses, blinks, and recalculates",
                "looks at you like that came out of nowhere",
            ]
        )
    if state["interest"] > 72:
        return random.choice(
            [
                "focuses in and waits for what comes next",
                "keeps a steady posture and stays locked in",
                "leans slightly forward like they're actually listening",
            ]
        )
    if state["happiness"] > 70:
        return random.choice(
            [
                "smiles slightly and looks comfortable",
                "lets out a small laugh and relaxes their shoulders",
                "looks at you with a warmer expression",
            ]
        )
    if state["stress"] < 30 and state["anger"] < 30:
        return random.choice(
            [
                "looks relaxed and unbothered",
                "rests their posture and seems calm",
                "breathes steadily and stays present",
            ]
        )
    return random.choice(
        [
            "keeps a neutral expression",
            "holds eye contact without giving much away",
            "waits for you to continue",
        ]
    )


FREE_TEXT_FRIENDLY = {
    "hi",
    "hello",
    "hey",
    "thanks",
    "thank you",
    "please",
    "sorry",
    "good morning",
    "good afternoon",
    "good evening",
    "how are you",
    "nice to meet",
    "great",
    "awesome",
    "love that",
    "appreciate",
}
FREE_TEXT_JOKING = {"lol", "haha", "hahaha", "funny", "kidding", "joke", "jk", "just kidding", "lmao", "😂", "😄"}
FREE_TEXT_AWKWARD = {"um", "uh", "err", "so...", "weird", "uncomfortable", "awkward", "idk", "i don't know", "whatever", "i guess"}

FREE_TEXT_AGGRESSIVE_HARD_SUBSTR = (
    "fuck you",
    "fuck off",
    "fuck u",
    "f u ",
    "fuck yourself",
    "go to hell",
    "piece of shit",
    "eat shit",
    "shut the fuck",
    "stfu",
    "motherfucker",
    "mother fucker",
    "dumb bitch",
    "stupid bitch",
    "you're trash",
    "youre trash",
    "ur trash",
    "you're garbage",
    " worthless",
    " nobody likes you",
    "pathetic loser",
    "rot in hell",
)
FREE_TEXT_AGGRESSIVE_MEDIUM_SUBSTR = (
    "shut up",
    "piss off",
    "screw you",
    "damn you",
    "hate you",
    "hate u ",
    "hate ur ",
    "stupid ass",
    "dumb ass",
    "dumbass",
    "cash me outside",
    "how bout that",
    "how 'bout that",
    "wtf",
    "what the fuck",
    "what the hell",
    "the hell is wrong",
    "bite me",
    "suck my",
    "fk you",
    "fuckin ",
    "fucking ",
    " moron ",
    " neckbeard",
    " incel",
    " bastard",
    " dumb ",
    " idiot ",
    "leave me alone",
    "get lost",
    "back off",
    "shut your",
)
FREE_TEXT_AGGRESSIVE_LIGHT_SUBSTR = (
    "you're weird",
    "you are weird",
    "ur weird",
    "thats dumb",
    "that's dumb",
    "ok buddy",
    "okay buddy",
    "you're lame",
    "you are lame",
    "not funny",
    "cringe",
    "whatever dude",
    "whatever man",
    "that's rude",
    "thats rude",
    "you're mean",
    "you are mean",
    "ok then",
    "okay then",
)
FREE_TEXT_AGGRESSIVE_HARD_WORDS = {"loser", "bitch", "whore", "slut", "cunt"}
FREE_TEXT_AGGRESSIVE_MEDIUM_WORDS = {
    "hate",
    "stupid",
    "idiot",
    "dumb",
    "ugly",
    "annoying",
    "jerk",
    "moron",
    "trash",
    "pathetic",
    "lame",
    "worst",
    "terrible",
    "screw",
    "damn",
    "asshole",
    "bastard",
    "dumbass",
}


FREE_TEXT_CATEGORY_EFFECTS = {
    "friendly": {"trust": 6, "happiness": 4, "stress": -2},
    "awkward": {"confusion": 6, "stress": 4, "trust": -2},
    "aggressive_light": {
        "trust": -8,
        "interest": -4,
        "anger": 8,
        "stress": 4,
        "confusion": 3,
        "happiness": 4,
        "confidence": 6,
    },
    "aggressive_medium": {
        "trust": -14,
        "interest": -8,
        "anger": 14,
        "stress": 8,
        "confusion": 5,
        "happiness": 3,
        "confidence": 8,
    },
    "aggressive_hard": {
        "trust": -22,
        "interest": -12,
        "anger": 22,
        "stress": 14,
        "confusion": 6,
        "happiness": 0,
        "confidence": 10,
    },
    "joking": {"interest": 4, "happiness": 4, "confusion": 2},
    "neutral": {"interest": 2},
    "apology": {"trust": 8, "anger": -8, "stress": -5, "happiness": 3},
    "absurd": {"confusion": 24, "interest": 6, "happiness": 2},
}

CAT_MODE_FREE_TEXT_EFFECTS = {
    "happiness": 7,
    "confidence": 9,
    "anger": -6,
    "stress": -8,
    "trust": -8,
    "interest": 7,
    "confusion": 3,
}


def scaled_free_text_category_mods(free_category):
    mods = dict(FREE_TEXT_CATEGORY_EFFECTS.get(free_category, FREE_TEXT_CATEGORY_EFFECTS["neutral"]))
    if str(free_category) == "apology":
        mem = st.session_state.get("conversation_memory") or init_memory_state()
        d = mem.get("disrespect_score", 0)
        repair = 1.0 - clamp01(d / 100.0) * 0.55
        mods = dict(mods)
        if "trust" in mods:
            mods["trust"] = int(round(mods["trust"] * repair))
        if "happiness" in mods:
            mods["happiness"] = int(round(mods["happiness"] * repair))
        if "anger" in mods:
            mods["anger"] = int(round(mods["anger"] * (0.7 + (1.0 - repair) * 0.3)))
        mods["stress"] = mods.get("stress", 0) + int(round((1.0 - repair) * 3))
        return mods
    if not str(free_category).startswith("aggressive_"):
        return mods
    n = st.session_state.get("aggressive_free_text_count", 0)
    if n <= 2:
        factor = 0.68
    elif n <= 5:
        factor = 1.0
    else:
        factor = 1.1
    return {k: int(round(v * factor)) for k, v in mods.items()}


def free_text_hard_slur_guard(text):
    t = (text or "").lower()
    return any(x in t for x in ("fuck", "bitch", "cunt", "stfu", "kill you", "go to hell", "piece of shit", "eat shit"))


def free_text_weak_insult_phrase(text):
    t = (text or "").lower()
    if free_text_hard_slur_guard(text):
        return False
    return any(
        x in t
        for x in (
            "you suck",
            "you're dumb",
            "you are dumb",
            "ur dumb",
            "you're lame",
            "you are lame",
            "you're stupid",
            "you are stupid",
            "idiot",
            "moron",
            "loser",
            "you're trash",
            "you are trash",
        )
    )


def free_text_insult_is_baiting(norm, prev_fc, n_aggr, recent_norms):
    if prev_fc and str(prev_fc).startswith("aggressive_"):
        return True
    if n_aggr >= 2:
        return True
    if norm and norm in recent_norms:
        return True
    return False


def should_use_cat_mode(choice, free_cat_after_bump, cat_raw, prev_fc, n_aggr, recent_norms):
    if (choice or "").lower().find("cash me") >= 0:
        return False
    if free_cat_after_bump == "aggressive_hard" or cat_raw == "aggressive_hard":
        return False
    if free_cat_after_bump not in ("aggressive_light", "aggressive_medium"):
        return False
    norm = normalize_speech(choice)
    if free_text_insult_is_baiting(norm, prev_fc, n_aggr, recent_norms):
        return True
    if n_aggr >= 1:
        return True
    if free_text_weak_insult_phrase(choice):
        return True
    return False


_SPEECH_GREETING_FRAGMENTS = (
    "how are you",
    "how you doing",
    "how r u",
    "how're you",
    "what's up",
    "whats up",
    "wassup",
    "sup ",
    " sup",
    "hello",
    "hey there",
    "nice to meet",
    "good morning",
    "good afternoon",
    "good evening",
    "you good",
    "everything good",
)


def greeting_or_checkin_overlap(norm, prev_norm):
    if not norm or not prev_norm:
        return False
    for frag in _SPEECH_GREETING_FRAGMENTS:
        if frag in norm and frag in prev_norm:
            return True
    return False


def speech_echoes_recent(norm, recent_norms, is_free, prev_free_category, current_category):
    if not norm:
        return False
    for prev in recent_norms:
        if prev == norm:
            return True
        if greeting_or_checkin_overlap(norm, prev):
            return True
    if is_free and prev_free_category and current_category and prev_free_category == current_category:
        if current_category in ("friendly", "neutral", "joking", "apology"):
            return True
    return False


def interpret_free_text(text):
    if not text or not str(text).strip():
        return "neutral"
    t = str(text).strip().lower()
    words = set(w.strip(".,!?\"'") for w in t.split())

    if "zip it" in t or (t.count("zip") >= 2 and "zip" in t):
        return "absurd"
    if any(x in t for x in ("my bad", "my fault", "my b ", "mb dawg", "mb fam", "mb bro", "sry dawg", "sorry dawg", "my apologies")):
        return "apology"

    if any(s in t for s in FREE_TEXT_AGGRESSIVE_HARD_SUBSTR):
        return "aggressive_hard"
    if any(s in t for s in FREE_TEXT_AGGRESSIVE_MEDIUM_SUBSTR):
        return "aggressive_medium"
    if any(s in t for s in FREE_TEXT_AGGRESSIVE_LIGHT_SUBSTR):
        return "aggressive_light"

    if words & FREE_TEXT_AGGRESSIVE_HARD_WORDS:
        return "aggressive_hard"
    if words & FREE_TEXT_AGGRESSIVE_MEDIUM_WORDS:
        return "aggressive_medium"

    if (
        "what's up man" in t
        or "whats up man" in t
        or "what up man" in t
        or "wassup man" in t
        or (("what's up" in t or "whats up" in t or "wassup" in t) and "man" in words)
    ):
        return "friendly"
    if any(f in t for f in ("how you doing", "how r u", "how're you")) or any(f in t for f in FREE_TEXT_FRIENDLY):
        return "friendly"
    if any(f in t for f in FREE_TEXT_JOKING):
        return "joking"
    if any(f in t for f in FREE_TEXT_AWKWARD):
        return "awkward"

    if words & FREE_TEXT_FRIENDLY:
        return "friendly"
    if words & FREE_TEXT_JOKING:
        return "joking"
    if words & FREE_TEXT_AWKWARD:
        return "awkward"

    if any(x in t for x in ("fuck", "shit", "bitch", "asshole", "dumbass", "loser", "hate you", "hate u", "idiot", "stupid", "pathetic", "suck ", " sucks", "trash", "moron")):
        return "aggressive_medium"

    return "neutral"


def _weighted_choice_weighted_lines(weighted_lines):
    if not weighted_lines:
        return "Say that again."
    total = sum(w for _, w in weighted_lines)
    r = random.uniform(0, total)
    acc = 0.0
    for line, w in weighted_lines:
        acc += w
        if r <= acc:
            return line
    return weighted_lines[-1][0]


def aggressive_comeback_response(tier, personality, state, character_name, raw_text=None):
    rt = (raw_text or "").strip().lower()
    physical = infer_physical_response(state)

    if st.session_state.get("free_text_cat_mode_active") and "cash me" not in rt and not free_text_hard_slur_guard(raw_text):
        cat_pool = [
            ("A swing and a miss.", 7),
            ("You're trying too hard.", 7),
            ("You thought that was it?", 6),
            ("You're swinging at air right now.", 6),
            ("That looked better in your head.", 6),
            ("You're not even close.", 6),
            ("This is getting embarrassing for you.", 5),
            ("You're entertaining, I'll give you that.", 5),
        ]
        verbal = _weighted_choice_weighted_lines(cat_pool)
        vibe = random.choice(["in control", "entertained"])
        return quote(verbal), "cocky", physical, vibe

    n_aggr = st.session_state.get("aggressive_free_text_count", 0)
    stage = "early" if n_aggr <= 2 else ("mid" if n_aggr <= 5 else "late")
    prev_fc = st.session_state.get("last_free_text_category")
    recent_norms = list(st.session_state.get("recent_speech_norms", []))
    norm = normalize_speech(raw_text) if raw_text else ""
    intent = "baiting" if ((prev_fc and str(prev_fc).startswith("aggressive_")) or n_aggr >= 2 or (norm and norm in recent_norms)) else "aggressive"

    pool_tier = tier
    if stage == "early" and intent != "baiting":
        if tier == "aggressive_hard":
            pool_tier = "aggressive_medium"
        elif tier == "aggressive_medium":
            pool_tier = "aggressive_light"

    shutdown_ok = stage == "late" or tier == "aggressive_hard" or intent == "baiting"

    def line_allowed(line):
        if shutdown_ok:
            return True
        ln = line.lower()
        return not ("conversation's over" in ln or "we're done if" in ln or "i'm not entertaining this" in ln)

    if "shut up" in rt and "fuck" not in rt and "stfu" not in rt.replace(" ", ""):
        playful = [("Make me.", 5), ("You first.", 4), ("No—you.", 4), ("Bold opener.", 3), ("Cute. Use your words.", 2)]
        verbal = _weighted_choice_weighted_lines(playful)
        tone = "engaged" if random.random() < 0.55 else "uncertain"
        return quote(verbal), tone, physical, "amused"

    if "ok buddy" in rt or "okay buddy" in rt:
        ok_lines = [("Alright… buddy.", 4), ("Okay?", 5), ("You good?", 4), ("Sure.", 4)]
        verbal = _weighted_choice_weighted_lines(ok_lines)
        return quote(verbal), "uncertain", physical, "mild side-eye"

    if ("that's dumb" in rt or "thats dumb" in rt) and "you're" not in rt and "you are" not in rt and "ur dumb" not in rt:
        dumb_play = [("Okay. Cool critique.", 4), ("Bold take.", 4), ("If you say so.", 5), ("That's the whole argument?", 3)]
        verbal = _weighted_choice_weighted_lines(dumb_play)
        return quote(verbal), "engaged", physical, "playful"

    if "cash me" in rt:
        cash_lines = [("We're not doing that bit.", 4), ("This isn't 2016.", 4), ("Say it again like you actually mean it.", 3), ("Okay—step outside, then. Alone.", 2)]
        verbal = _weighted_choice_weighted_lines(cash_lines)
        return quote(verbal), "tense", physical, "openly unimpressed"

    if intent == "baiting" and random.random() < 0.48:
        bait = [
            ("You're swinging at air right now.", 4),
            ("You're trying too hard.", 5),
            ("That didn't land.", 5),
            ("That didn't land the way you thought it would.", 3),
        ]
        verbal = _weighted_choice_weighted_lines(bait)
        tone = "tense" if random.random() < 0.55 else "uncertain"
        return quote(verbal), tone, physical, "dismissive"

    if pool_tier == "aggressive_hard":
        tone = "hostile"
        vibe = "done with you" if shutdown_ok and random.random() < 0.48 else "hostile"
    elif pool_tier == "aggressive_medium":
        tone = "tense"
        vibe = infer_vibe(state)
    else:
        tone = infer_tone(state)
        if tone in ("warm", "engaged"):
            tone = "uncertain"
        vibe = infer_vibe(state)

    preferred = [
        ("A swing and a miss.", ("aggressive_light", "aggressive_medium"), 9),
        ("It should be illegal for you to use the internet.", ("aggressive_hard",), 8),
        ("I hope this is making you feel less dead inside.", ("aggressive_medium", "aggressive_hard"), 8),
        ("Does this make you feel like you have a life?", ("aggressive_medium", "aggressive_hard"), 8),
        ("Life is weird. You're boring. And pretty dumb.", ("aggressive_hard",), 6),
        ("I don't actually have a mouth to shut. You have a brain that sucks.", ("aggressive_hard",), 6),
        ("If you want to have sex with your device, be my guest, but you'll probably sustain injuries.", ("aggressive_hard",), 5),
    ]
    fallback = [
        ("That didn't land the way you thought it would.", ("aggressive_light", "aggressive_medium"), 5),
        ("You're trying too hard.", ("aggressive_light", "aggressive_medium"), 5),
        ("You're not winning anything by talking like that.", ("aggressive_medium", "aggressive_hard"), 4),
        ("That was a weird thing to say out loud.", ("aggressive_light", "aggressive_medium"), 5),
        ("You sound insecure.", ("aggressive_light", "aggressive_medium"), 4),
        ("You came in loud and still said nothing.", ("aggressive_medium", "aggressive_hard"), 4),
        ("That insult came out pre-owned.", ("aggressive_medium",), 4),
        ("You're not intimidating. Just sloppy.", ("aggressive_medium", "aggressive_hard"), 4),
        ("That's your best?", ("aggressive_light", "aggressive_medium"), 5),
        ("You're arguing like your Wi-Fi is unstable.", ("aggressive_medium",), 3),
        ("Try that again without the attitude.", ("aggressive_medium",), 4),
        ("You're making yourself the problem here.", ("aggressive_medium", "aggressive_hard"), 4),
        ("You wanted that to sting way more than it did.", ("aggressive_medium", "aggressive_hard"), 3),
        ("Conversation's over.", ("aggressive_hard",), 3),
    ]

    tier_light_lines = [("Okay…?", 5), ("That's random.", 5), ("You got something you want to say?", 4), ("Weird how?", 4)]
    tier_medium_lines = [("Relax.", 5), ("Don't talk to me like that.", 5), ("What's your problem?", 5), ("Dial it back.", 4)]
    tier_hard_lines = [("Yeah, we're done if that's how you're gonna act.", 4), ("You're not winning anything talking like that.", 4), ("Conversation's over.", 3), ("I'm not entertaining this.", 4)]

    shy_alt = {
        "aggressive_light": [("That felt pretty rude.", 4), ("Why would you say it like that?", 4), ("I'm not sure what you're trying to do here.", 3)],
        "aggressive_medium": [("Stop. I'm not doing this.", 4), ("That's not okay to say.", 4), ("I need you to dial that back.", 4)],
        "aggressive_hard": [("No. I'm not taking that from you.", 4), ("I'm done. That crossed a line.", 3), ("You're being cruel—and I'm out.", 3)],
    }

    def pool_for_tier(src_list, ptier):
        out = []
        for line, tiers, w in src_list:
            if ptier not in tiers:
                continue
            if not line_allowed(line):
                continue
            out.append((line, w))
        return out

    pf = pool_for_tier(preferred, pool_tier)
    fb = pool_for_tier(fallback, pool_tier)

    if personality == "Shy" and random.random() < 0.38:
        verbal = _weighted_choice_weighted_lines(list(shy_alt.get(pool_tier, tier_medium_lines)))
        return quote(verbal), tone, physical, vibe

    core = {
        "aggressive_light": [(l, w) for l, w in tier_light_lines if line_allowed(l)],
        "aggressive_medium": [(l, w) for l, w in tier_medium_lines if line_allowed(l)],
        "aggressive_hard": [(l, w) for l, w in tier_hard_lines if line_allowed(l)],
    }
    roll = random.random()
    if roll < 0.62 and pf:
        verbal = _weighted_choice_weighted_lines(pf)
    elif roll < 0.92 and fb:
        verbal = _weighted_choice_weighted_lines(fb)
    else:
        verbal = _weighted_choice_weighted_lines(core.get(pool_tier, tier_medium_lines))

    return quote(verbal), tone, physical, vibe


def free_text_verbal_response(category, personality, state, character_name, raw_text=None):
    tone = infer_tone(state)
    physical = infer_physical_response(state)
    vibe = infer_vibe(state)
    rt = (raw_text or "").strip().lower()

    if category == "apology":
        base_apology = [
            "You're good. Don't worry about it.",
            "Alright. I hear you.",
            "Okay. Apology accepted—just don't double down.",
            "Yeah, I get it. We're fine.",
        ]
        blend_apology = {
            "Shy": ["Oh—okay. Thanks for saying that.", "It's… it's fine."],
            "Aggressive": ["Yeah, whatever. Mean it next time.", "Say it like you mean it."],
            "Empathetic": ["I appreciate you saying that.", "Thanks. That actually helps."],
            "Analytical": ["Noted. Let's move on.", "Okay. Context received."],
            "Impulsive": ["Bet. We're cool.", "Aight, I see you."],
            "Confident": ["Cool. Water under the bridge.", "Alright. Don't make it a pattern."],
        }
        pool = list(base_apology) + blend_apology.get(personality, [])
        return quote(random.choice(pool)), tone, physical, vibe

    if category == "absurd":
        base_absurd = [
            "What does that even mean?",
            "I'm sorry—what?",
            "That sentence just walked in with no luggage.",
            "I genuinely can't tell if that's a bit or a glitch.",
        ]
        blend_absurd = {
            "Shy": ["Um… okay?", "I'm… not following."],
            "Aggressive": ["Say something real.", "You're not making sense."],
            "Empathetic": ["I'm trying to keep up. Can you say that normally?", "Help me out here."],
            "Analytical": ["That doesn't parse. Try again in English.", "Define your terms."],
            "Impulsive": ["Bro what?", "That's nonsense."],
            "Confident": ["Come again?", "You're going to have to translate that."],
        }
        pool = list(base_absurd) + blend_absurd.get(personality, [])
        return quote(random.choice(pool)), "uncertain", physical, "confused"

    if category in ("aggressive_light", "aggressive_medium", "aggressive_hard"):
        return aggressive_comeback_response(category, personality, state, character_name, raw_text=raw_text)

    mode = st.session_state.get("response_mode") or {}
    if mode.get("skip_crow_brain_rewrite"):
        direct = try_direct_free_text_answer(raw_text or "", personality, mode.get("question_type", ""))
        if direct:
            return quote(direct), tone, physical, vibe

    tense_joke = state["anger"] > 42 or tone in ("hostile", "tense") or state["stress"] > 58
    if category == "joking" and rt and ("lol" in rt or "lmao" in rt) and ("bro" in rt or "bruh" in rt):
        if tense_joke:
            pool_bro = ["What's so funny?", "What are you laughing at?", "This isn't the time for 'lol bro.'", "Why is that funny right now?"]
        else:
            pool_bro = ["What's up with you?", "You good?", "Okay… loud and online.", "Bro energy noted."]
        return quote(random.choice(pool_bro)), tone, physical, vibe

    base = {
        "friendly": ["Hey—what's going on?", "I'm alright. What's up with you?", "Yeah, hey.", "Cool. What's on your mind?"],
        "joking": ["Alright, I see what you're doing.", "That almost landed.", "You're a lot.", "Okay, I'll bite."],
        "awkward": ["Uh… hey.", "You okay?", "That came out weird.", "Okay…"],
        "neutral": ["Yeah?", "What's up?", "Say it plain.", "I'm listening—go ahead."],
    }
    pool = list(base.get(category, base["neutral"]))
    personality_blend = {
        "Shy": {"friendly": ["Oh—hi.", "Hi.", "Hey."], "joking": ["Heh.", "That's… a choice."], "awkward": ["Um…", "I don't know what to say."], "neutral": ["Hi.", "Yeah?"]},
        "Aggressive": {"friendly": ["Alright.", "What's good."], "joking": ["Cute.", "You trying something?"], "awkward": ["Say what you mean."], "neutral": ["Yeah.", "Spit it out."]},
        "Empathetic": {"friendly": ["I'm good. How about you?", "Hey—thanks for asking."], "joking": ["Ha, fair.", "You're a trip."], "awkward": ["It's okay. Take your time."], "neutral": ["I'm listening.", "Go ahead."]},
        "Analytical": {"friendly": ["Fine. You?", "Straightforward. Okay."], "joking": ["If that's a joke, I need the punchline.", "Trying to be funny?"], "awkward": ["I'm not following.", "Can you rephrase that?"], "neutral": ["Go on.", "What are you getting at?"]},
        "Impulsive": {"friendly": ["Yo!", "What's good?"], "joking": ["Dead.", "Stop."], "awkward": ["Bro…", "That was weird."], "neutral": ["Yeah?", "Talk to me."]},
        "Confident": {"friendly": ["Hey. I'm good.", "Solid. You?"], "joking": ["That one almost worked.", "Bold."], "awkward": ["Let's reset.", "Try that again."], "neutral": ["Go on.", "Yeah?"]},
    }
    pool.extend(personality_blend.get(personality, {}).get(category, []))
    return quote(random.choice(pool)), tone, physical, vibe

