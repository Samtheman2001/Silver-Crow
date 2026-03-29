"""
Static configuration tables/constants for Silver Crow.

Import-safe: no Streamlit usage, no session state access.
"""

# NOTE: This file is populated from the current monolith. Keep data-only.

PERSONALITIES = {
    "Confident": {"confidence": 18, "stress": -8, "fear": -8, "interest": 4},
    "Shy": {"confidence": -12, "stress": 12, "fear": 10, "trust": 4},
    "Aggressive": {"anger": 16, "stress": 6, "trust": -8, "confidence": 8},
    "Empathetic": {"trust": 14, "happiness": 8, "anger": -8, "interest": 8},
    "Analytical": {"confusion": -10, "interest": 10, "happiness": -2},
    "Impulsive": {"anger": 6, "interest": 10, "stress": 8, "confidence": 4},
}

BACKGROUNDS = {
    "College Student": {"interest": 6, "confidence": -2, "confusion": 4},
    "Military Veteran": {"stress": 4, "confidence": 10, "fear": -6},
    "Entrepreneur": {"confidence": 10, "interest": 8, "stress": 4},
    "Artist": {"interest": 8, "happiness": 6, "confidence": -2},
    "Office Worker": {"stress": 6, "trust": 2, "interest": -2},
    "Athlete": {"confidence": 8, "stress": -2, "interest": 4},
}

PHYSICAL_STATES = {
    "Relaxed": {"stress": -12, "happiness": 8, "anger": -4},
    "Tired": {"stress": 10, "confusion": 10, "interest": -6},
    "Injured": {"stress": 12, "fear": 10, "anger": 4},
    "Stressed": {"stress": 16, "anger": 8, "trust": -4},
    "Energized": {"confidence": 8, "interest": 8, "happiness": 4},
    "Sick": {"stress": 12, "happiness": -10, "interest": -8},
}

STARTING_MOODS = {
    "Neutral": {},
    "Calm": {"stress": -10, "anger": -6, "happiness": 6},
    "Anxious": {"stress": 14, "fear": 12, "confidence": -8},
    "Irritated": {"anger": 14, "trust": -8, "happiness": -6},
    "Excited": {"happiness": 12, "interest": 10, "stress": -2},
}

SCENARIOS = {
    "Living Room": {
        "scenario_id": "living_room",
        "desc": "A casual conversation in a home setting. Low stakes, but tone still matters.",
        "mods": {"stress": -6, "trust": 6, "fear": -4},
        "sensitivity": 0.9,
    },
    "Waiting in Line": {
        "scenario_id": "waiting_in_line",
        "desc": "A public place with mild awkwardness and impatience simmering underneath.",
        "mods": {"stress": 4, "confusion": 4, "interest": -2},
        "sensitivity": 1.0,
    },
    "Bus Stop": {
        "scenario_id": "bus_stop",
        "desc": "Awkward small talk and strange questions are allowed.",
        "mods": {"stress": 3, "confusion": 5, "interest": 1},
        "sensitivity": 1.0,
    },
    "Movie Theater": {
        "scenario_id": "movie_theater",
        "desc": "The movie starts eventually, so the social pressure can build.",
        "mods": {"stress": 5, "trust": -1, "interest": 3},
        "sensitivity": 1.05,
    },
    "First Date": {
        "scenario_id": "first_date",
        "desc": "Attraction and confidence matter more here. Small mistakes hit harder.",
        "mods": {"stress": 8, "interest": 10, "fear": 4},
        "sensitivity": 1.15,
    },
}

ATTRIBUTES = [
    "happiness",
    "anger",
    "trust",
    "stress",
    "confidence",
    "confusion",
    "interest",
    "fear",
]

BASE_STATE = {
    "happiness": 50,
    "anger": 20,
    "trust": 40,
    "stress": 30,
    "confidence": 50,
    "confusion": 25,
    "interest": 50,
    "fear": 20,
}

# Interaction content tables (moved from the monolith).

SAY_OPTIONS = {
    "Hello, nice to meet you.": {
        "effects": {"trust": 8, "happiness": 6, "fear": -2},
        "responses": {
            "positive": [
                "Nice to meet you too.",
                "Hey—nice to meet you.",
                "Hi. You too.",
                "Same. What's your name?",
                "Nice to meet you. I'm {name}.",
            ],
            "neutral": [
                "Nice to meet you.",
                "Yeah, nice to meet you.",
                "Hey. Nice to meet you.",
                "You too.",
                "Hey.",
                "Hi.",
                "What's your name?",
            ],
            "negative": [
                "Hey.",
                "Hi.",
                "Mm. Hey.",
            ],
            "severe": [
                "Yeah?",
                "What.",
                "Busy.",
            ],
        },
    },
    "Hey, how are you?": {
        "effects": {"trust": 6, "interest": 4, "stress": -2},
        "responses": {
            "positive": [
                "I'm good. You?",
                "Doing good. You?",
                "Pretty good. You?",
                "Not bad. You?",
                "Can't complain. You?",
            ],
            "neutral": [
                "I'm good. You?",
                "Not bad.",
                "I'm alright. You?",
                "Hey. I'm okay. You?",
                "Same old. You?",
            ],
            "negative": [
                "Eh. I've been better.",
                "It's been a long day.",
                "Tired. You?",
            ],
            "severe": [
                "Not really in the mood.",
                "I'm fine. Why?",
                "Busy.",
            ],
        },
    },
    "What's up?": {
        "effects": {"interest": 4, "trust": 2, "confusion": -1},
        "responses": {
            "positive": [
                "Not much. You?",
                "Nothing really. You?",
                "Same old. You?",
                "Hey. Not a lot. You?",
            ],
            "neutral": [
                "What's up?",
                "Hey.",
                "Not much.",
                "Not much. You?",
                "Chilling. You?",
            ],
            "negative": [
                "Working.",
                "Stuff.",
                "Long day.",
            ],
            "severe": [
                "Yeah?",
                "Busy.",
                "Not a good time.",
            ],
        },
    },
    "Do you mind if I sit here?": {
        "effects": {"trust": 4, "stress": -1},
        "responses": {
            "positive": ["Yeah, go ahead.", "Sure.", "Yeah—you're good.", "Go for it."],
            "neutral": ["Yeah.", "Sure.", "That's fine.", "It's open."],
            "negative": ["I'd rather you didn't.", "Other spots open.", "Nah, I'm good here."],
            "severe": ["Yeah, I mind.", "Somewhere else.", "Don't sit here."],
        },
    },
    "Nice to meet you": {
        "effects": {"trust": 7, "happiness": 5, "fear": -2},
        "responses": {
            "positive": [
                "Nice to meet you too.",
                "Yeah, you too.",
                "Same. What's your name?",
                "Hey. You too.",
            ],
            "neutral": [
                "You too.",
                "Nice to meet you too.",
                "Yeah, nice to meet you.",
                "Hey.",
                "Hi.",
                "Yeah.",
            ],
            "negative": [
                "Hey.",
                "Hi.",
                "Yeah. Hi.",
            ],
            "severe": [
                "Yeah. Hi.",
                "Yeah?",
                "Hi.",
            ],
        },
    },
    "What's your name?": {
        "effects": {"trust": 2, "interest": 4},
        "responses": {
            "positive": ["I'm {name}. You?", "It's {name}. Yours?", "{name}. You?", "{name}."],
            "neutral": ["{name}.", "It's {name}.", "{name}. You?", "I'm {name}."],
            "negative": ["That's kinda forward.", "{name}. Why?", "…{name}. Happy?"],
            "severe": ["You don't need my name.", "Stop digging.", "Mind your business."],
        },
    },
    "I disagree with you.": {"anger": 6, "trust": -4, "interest": 2},
    "You're wrong.": {"anger": 14, "trust": -12, "happiness": -6},
    "I want to help.": {"trust": 10, "happiness": 4, "fear": -4},
    "I respect your opinion.": {"trust": 12, "happiness": 6, "anger": -4},
    "What do you need?": {"trust": 8, "interest": 6, "fear": -2},
    "Do you like me?": {"trust": 2, "interest": 6, "stress": 2},
    "Why don't you like me?": {"trust": -4, "stress": 6, "confusion": 4},
    "What do you think of me so far?": {"interest": 6, "trust": 2, "stress": 2},
    "Do you want to go on a date?": {"interest": 12, "trust": 4, "stress": 2, "happiness": 5, "confidence": 4},
    "Why don't you want to go on a date?": {"stress": 8, "anger": 4, "trust": -4},
    "Why are you treating me this way?": {"stress": 6, "anger": 4, "trust": -2},
    "Why are you acting like this?": {"stress": 6, "anger": 5, "trust": -3},
    "Who do you think you are?": {"anger": 12, "trust": -8, "stress": 6},
    "Why should I trust you?": {
        "effects": {"trust": -2, "interest": 4, "stress": 2},
        "responses": {
            "positive": ["You don't have to yet. Let it build.", "I’ll earn it. Watch what I do.", "Fair question. Give it time."],
            "neutral": ["You probably shouldn't—yet.", "We literally just met.", "That's fair. Keep your guard up."],
            "negative": ["I'm not selling you on me.", "If you don't, you don't.", "Trust isn't something you demand."],
            "severe": ["Then don't.", "I don't care.", "Not my problem."],
        },
    },
    "What are your thoughts on the stock market these days?": {"interest": 4, "confusion": 2},
    "Where did you get those shoes?": {"interest": 6, "happiness": 2},
    "Do you own a jetski?": {"interest": 8, "confusion": 2},
    "Would you like to buy my jetski?": {"interest": 10, "confusion": 4},
    "What are your thoughts on jetskis?": {"interest": 8, "happiness": 2},
    "Who is the most attractive person in history?": {"interest": 6, "confusion": 3},
    "Is Playboi Carti overrated?": {"interest": 8, "confusion": 4},
    "Cash me outside, how 'bout that?": {"confusion": 8, "interest": 4, "anger": 2},
    "Are you Republican or Democrat?": {"stress": 8, "confusion": 4, "trust": -2},
    "Do you think you're better than me?": {"anger": 8, "trust": -5, "interest": 2},
    "Why are you talking to me?": {"stress": 4, "trust": -2, "interest": 3},
    "Why do you care?": {"anger": 5, "trust": -4, "stress": 3},
    "Why are you so quiet?": {"stress": 3, "confusion": 4, "trust": -2},
    "Can you help me?": {"trust": 8, "interest": 4, "fear": -2},
    "What gives you the right?": {
        "effects": {"anger": 8, "trust": -6, "stress": 4},
        "responses": {
            "positive": ["Wait, what do you mean?", "I'm not trying to overstep."],
            "neutral": ["What are you even talking about?", "Right to what—be specific."],
            "negative": ["I don't need your permission.", "Don't talk to me like I'm your kid.", "Watch how you say that."],
            "severe": ["Don't push me.", "Say it again and see what happens.", "We're not doing this."],
        },
    },
    "Do you think I'm attractive?": {
        "effects": {"interest": 8, "stress": 4, "trust": 1},
        "responses": {
            "positive": ["Yeah. You're attractive.", "You are. Why—do you want honesty or reassurance?", "Yeah. You clean up nice."],
            "neutral": ["You're not ugly.", "You're alright.", "Why do you ask?"],
            "negative": ["Not really.", "No. Not my type.", "I'm not feeling it."],
            "severe": ["No.", "Absolutely not.", "Don't fish like that with me."],
        },
    },
    "Can I sleep at your house tonight?": {"stress": 12, "fear": 8, "trust": -4},
    "Can a young gangsta get money anymore?": {"confusion": 6, "interest": 5},
    "What are your thoughts on this weather?": {"stress": -2, "interest": 4},
    "Do you think you're funny?": {"interest": 5, "trust": 1, "anger": 2},
    "Why are you looking at me like that?": {"stress": 6, "anger": 3, "trust": -2},
    "What do you want?": {"stress": 4, "interest": 2, "trust": -1},
    "Are you having a good day?": {
        "effects": {"trust": 4, "interest": 4, "stress": -1},
        "responses": {
            "positive": ["Yeah. It's been good.", "Honestly? Yeah.", "Yeah—pretty solid day."],
            "neutral": ["It's alright.", "Pretty average.", "It's fine."],
            "negative": ["Not really.", "It's been rough.", "I've had better days."],
            "severe": ["No.", "I don't want to talk about it.", "Drop it."],
        },
    },
    "What are you up to today?": {
        "effects": {"interest": 5, "trust": 2},
        "responses": {
            "positive": ["Just getting through the day.", "Few things. Nothing wild.", "Chilling, mostly."],
            "neutral": ["Not much.", "Same old.", "Just out."],
            "negative": ["Not much. Why?", "Eh. Long day.", "Busy. You?"],
            "severe": ["Mind your business.", "Why are you asking?", "Drop it."],
        },
    },
    "Do you come here often?": {
        "effects": {"interest": 4, "confusion": 3},
        "responses": {
            "positive": ["Yeah, sometimes.", "When I can.", "It's alright here."],
            "neutral": ["Now and then.", "Sometimes.", "Not really."],
            "negative": ["Does it matter?", "That's random.", "Not really, no."],
            "severe": ["Easy.", "Relax.", "Enough questions."],
        },
    },
    "Sam Howell sent me.": {"interest": 8, "confusion": 4, "happiness": 2},
}

# Dropdown selection pools:
# - `SAY_OPTIONS` remains the full lookup table for stat/effect/response logic.
# - `DEFAULT_SAY_OPTIONS` is the full menu pool; scenarios may hide keys via `scenario_layer`.
DEFAULT_SAY_OPTIONS = {k: v for k, v in SAY_OPTIONS.items()}


def get_say_options_for_scenario(scenario_name: str) -> dict:
    """Return the dropdown pool for a scenario.

    `SAY_OPTIONS` remains the canonical effect/response lookup; this function controls what the UI/test
    dropdown offers for a given scenario (scenario-specific hides only; no duplicate banks).
    """
    from scenario_layer import filter_say_options_for_scenario

    return filter_say_options_for_scenario(DEFAULT_SAY_OPTIONS, scenario_name)


ACTION_OPTIONS = {
    "Smile": {"happiness": 8, "trust": 6, "fear": -2},
    "Stare blankly": {"confusion": 8, "stress": 5, "interest": -1, "fear": 2},
    "Interrupt": {"anger": 12, "trust": -10, "stress": 8},
    "Step closer": {"interest": 4, "fear": 8, "stress": 4},
    "Step back": {"fear": -4, "stress": -2, "trust": 2},
    "Look away": {"trust": -4, "confusion": 6, "interest": -2},
    "Raise voice": {"anger": 16, "stress": 10, "fear": 10},
    "Stay silent": {"confusion": 4, "stress": -2, "interest": -2},
    "Offer handshake": {"trust": 10, "happiness": 4, "fear": -2},
    "Sit down": {"stress": -4, "fear": -2, "interest": 2},
    "Leave": {"trust": -14, "interest": -12, "fear": 4},
    "Hit the moonwalk": {"interest": 12, "confusion": 10, "happiness": 6},
}

FOLLOW_UP_NODES = {
    "date_where": {
        "question": "Where should we go?",
        "options": [
            ("Coffee shop", {"trust": 6, "happiness": 4}, '"Coffee sounds good. Easy start."', None),
            ("Nice restaurant", {"interest": 4, "stress": 2}, '"Okay, going a little ambitious. I respect it."', None),
            ("Walk on the beach", {"happiness": 6, "trust": 5}, '"That actually sounds kind of beautiful."', None),
            ("Somewhere cheap", {"confusion": 2, "interest": 1}, '"At least you\'re honest about it."', None),
            ("Your place", {"fear": 10, "trust": -12, "anger": 8}, '"Whoa. You jumped way too fast there."', None),
        ],
    },
    "date_neutral": {
        "question": "What did you have in mind?",
        "options": [
            ("Something casual", {"trust": 4, "stress": -2}, '"Casual works."', None),
            ("Something fancy", {"interest": 3, "stress": 2}, '"You\'re trying hard. Noted."', None),
            ("I don't know yet", {"confusion": 3}, '"Then maybe think about it first."', None),
            ("You decide", {"trust": -2, "interest": 2}, '"So I\'m doing the work now? Cool."', None),
        ],
    },
    "jetski_price": {
        "question": "Hmm… how much?",
        "options": [
            ("$500", {"confusion": 6, "trust": -6}, '"That\'s way too cheap. What\'s wrong with it?"', "jetski_500"),
            ("$2,000", {"interest": 6}, '"That\'s actually reasonable. What condition is it in?"', "jetski_2000"),
            ("$10,000", {"confusion": 5, "interest": 3}, '"That\'s a lot. Why is it worth that much?"', "jetski_10000"),
            ("$50,000", {"anger": 8, "interest": -10, "trust": -8}, '"You\'ve completely lost your mind."', "jetski_absurd"),
        ],
    },
    "jetski_500": {
        "question": "Be honest — what\'s wrong with it?",
        "options": [
            ("Nothing, it works perfectly", {"trust": -6, "confusion": 6}, '"Yeah, I don\'t believe you."', None),
            ("It has a few issues", {"trust": -2, "interest": 2}, '"Okay… like what?"', None),
            ("I stole it", {"anger": 14, "trust": -18, "fear": 6}, '"Yeah, I\'m out. We\'re done here."', "END_MURDER"),
        ],
    },
    "jetski_2000": {
        "question": "What condition is it in?",
        "options": [
            ("Like new", {"interest": 6, "trust": 4}, '"Alright… now I\'m interested."', None),
            ("Used but solid", {"interest": 3, "trust": 2}, '"Okay, that\'s fair. I might consider it."', None),
            ("Barely runs", {"anger": 7, "trust": -10}, '"So you\'re trying to scam me? No thanks."', None),
        ],
    },
    "jetski_10000": {
        "question": "Why is it worth that much?",
        "options": [
            ("It's top of the line", {"interest": 4}, '"It better be for that price. I\'d need to see it."', None),
            ("It has sentimental value", {"confusion": 4, "trust": -2}, '"Then why are you selling it? That doesn\'t add up."', None),
            ("Because I said so", {"anger": 10, "trust": -10}, '"Yeah… I\'m definitely not buying it now."', None),
        ],
    },
    "nirvana_question": {
        "question": "Do you like Nirvana?",
        "options": [
            ("Yeah, they're great", {"interest": 6, "trust": 2}, '"Favorite song?"', "nirvana_song"),
            ("They're alright", {"interest": 2}, '"Fair enough. Favorite song anyway?"', "nirvana_song"),
            ("Nirvana sucks", {"anger": 8, "trust": -6}, '"That\'s actually a terrible opinion."', None),
            ("I've never listened to them", {"confusion": 2, "interest": 3}, '"That feels fixable."', None),
        ],
    },
    "nirvana_song": {
        "question": "Favorite song?",
        "options": [
            ("Smells Like Teen Spirit", {"trust": 3, "interest": 4}, '"Classic answer. Respect."', None),
            ("Come As You Are", {"trust": 4, "interest": 4}, '"Okay, now we\'re talking."', None),
            ("I don't listen to Nirvana", {"confusion": 3}, '"You just said they were great and now this?"', None),
        ],
    },
}

CHARACTER_INITIATIVES = [
    ("So what brings you here?", {"interest": 4, "trust": 2}, "looks at you expectantly", "curious"),
    ("You've been quiet. Everything good?", {"trust": 3, "stress": -2}, "tilts head", "checking in"),
    ("Random question—what do you do?", {"interest": 6, "confusion": -2}, "leans back a little", "making conversation"),
    ("Do you come here a lot?", {"interest": 4}, "glances around", "small talk"),
    ("What's on your mind?", {"trust": 4, "interest": 4}, "waits", "open"),
    ("Sorry, I'm just—you remind me of someone.", {"confusion": 4, "interest": 6}, "trails off, then refocuses", "slightly flustered"),
    ("Anyway. You were saying?", {"interest": 2}, "gestures for you to continue", "back on track"),
]

