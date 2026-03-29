# -*- coding: utf-8 -*-
"""
Authored do-action lines from ``action quarks.txt`` (project root).

Separate from say/quarks canon, finishers, and ``quarks.txt``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

# Source document (for reference only; data is duplicated below as structured tables).
ACTION_QUARKS_SOURCE = Path(__file__).resolve().parent.parent / "action quarks.txt"

MOONWALK_STREAK_KEY = "_moonwalk_consecutive_streak"

QuarkBeat = Dict[str, Optional[str]]  # keys: "v" verbal inner, "p" physical beat (either may be None)


def _b(v: Optional[str] = None, p: Optional[str] = None) -> QuarkBeat:
    return {"v": v, "p": p}


# ACTION_QUARKS[action_name][bucket_name] -> list of beats
ACTION_QUARKS: Dict[str, Dict[str, List[QuarkBeat]]] = {
    "Smile": {
        "normal": [
            _b("Hey."),
            _b("Hi."),
            _b(p="smiles back"),
            _b("What's up?"),
            _b("Why are you so happy? Haha."),
        ],
        "uncertain": [
            _b("...hey."),
            _b("You good?"),
            _b(p="small smile, then looks away"),
            _b("Uh—hi?"),
        ],
        "suspicious": [
            _b(p="furrows brow slightly"),
            _b("Why are you smiling at me?"),
            _b("Do I know you?"),
            _b("What's going on?"),
        ],
        "annoyed": [
            _b("Okay, what?"),
            _b("Say something."),
            _b("This is weird."),
        ],
        "boundary": [
            _b("Alright, stop."),
            _b("You're making this uncomfortable."),
            _b("I'm not into this."),
        ],
    },
    "Stare blankly": {
        "normal": [
            _b("...yeah?"),
            _b("What?"),
            _b("You okay?"),
        ],
        "uncertain": [
            _b("Why are you looking at me like that?"),
            _b("Something wrong?"),
            _b("Uh…?"),
        ],
        "suspicious": [
            _b("What are you doing?"),
            _b("Why are you just staring?"),
            _b("That's weird."),
        ],
        "annoyed": [
            _b("Say something."),
            _b("Don't just stare at me."),
            _b("What do you want?"),
        ],
        "boundary": [
            _b("Alright, stop that."),
            _b("This is uncomfortable."),
            _b("I'm not doing this."),
        ],
    },
    "Interrupt": {
        "normal": [
            _b("—wait, what?"),
            _b("Hold on."),
            _b("Yeah?"),
        ],
        "uncertain": [
            _b("What?"),
            _b("You cut me off."),
            _b("Okay…?"),
        ],
        "annoyed": [
            _b("Let me finish."),
            _b("Don't interrupt me."),
            _b("Dude—what?"),
            _b("Silence...bitch."),
        ],
        "boundary": [
            _b("Stop."),
            _b("I'm talking."),
            _b("If you keep doing that I'm done."),
            _b("Silence...bitch."),
        ],
    },
    "Step closer": {
        "normal": [
            _b("Oh—hey."),
            _b("Hi."),
            _b(p="slight pause"),
        ],
        "uncertain": [
            _b("Uh… hi?"),
            _b("You're close."),
            _b("What's up?"),
        ],
        "guarded": [
            _b(p="steps back slightly"),
            _b("You good?"),
            _b("Need something?"),
        ],
        "annoyed": [
            _b("Back up."),
            _b("You're too close."),
            _b("What are you doing?"),
        ],
        "boundary": [
            _b(p="pushes you back slightly"),
            _b("Seriously, back up."),
            _b("Don't do that."),
            _b("I don't like that."),
        ],
    },
    "Step back": {
        "normal": [
            _b("Oh—okay."),
            _b("Alright."),
            _b(p="nods"),
        ],
        "uncertain": [
            _b("You good?"),
            _b("Did I do something?"),
            _b("Okay…?"),
        ],
        "guarded": [
            _b(p="watches you"),
            _b("Alright then."),
            _b("Cool."),
        ],
    },
    "Look away": {
        "normal": [
            _b("...okay."),
            _b("Alright."),
            _b(p="glances at you"),
        ],
        "uncertain": [
            _b("You good?"),
            _b("Why'd you look away?"),
            _b("Okay…?"),
        ],
        "suspicious": [
            _b("What was that?"),
            _b("You're acting weird."),
            _b("Something up?"),
        ],
        "annoyed": [
            _b("Alright, whatever."),
            _b("Okay dude."),
            _b("This is weird."),
        ],
    },
    "Raise voice": {
        "normal": [
            _b("Whoa."),
            _b("Hey."),
            _b("What's up?"),
        ],
        "annoyed": [
            _b("Why are you yelling?"),
            _b("Relax."),
            _b("What's your problem?"),
        ],
        "escalation": [
            _b("Don't talk to me like that."),
            _b("Lower your voice."),
            _b("I'm not doing this."),
        ],
        "boundary": [
            _b("Nah, we're done."),
            _b("I'm out."),
            _b("You're doing too much."),
        ],
    },
    "Stay silent": {
        "normal": [
            _b("...okay."),
            _b("Alright."),
            _b(p="waits"),
        ],
        "uncertain": [
            _b("You gonna say something?"),
            _b("Hello?"),
            _b("...?"),
        ],
        "annoyed": [
            _b("Okay, this is weird."),
            _b("Say something."),
            _b("What are we doing?"),
        ],
        "boundary": [
            _b("I'm not doing this."),
            _b("If you're not gonna talk I'm out."),
        ],
    },
    "Offer handshake": {
        "normal": [
            _b("Oh—hey."),
            _b(p="shakes your hand"),
            _b("Nice to meet you."),
        ],
        "uncertain": [
            _b("Uh—hi."),
            _b(p="hesitant handshake"),
            _b("Okay…"),
        ],
        "guarded": [
            _b(p="shakes briefly"),
            _b("Well hello there..."),
            _b("Umm... good day to you too..."),
            _b(p="looks at you with concern"),
        ],
        "awkward": [
            _b("Okay…?"),
            _b("This is kinda random."),
            _b("Uh—sure."),
        ],
        "annoyed": [
            _b("Why?"),
            _b("What is this?"),
            _b(p="doesn't take it"),
        ],
    },
    "Sit down": {
        "normal": [
            _b("Oh, okay."),
            _b("Hey, what's up?"),
            _b("Hey."),
            _b("You good?"),
        ],
        "uncertain": [
            _b("Alright…?"),
            _b("Cool."),
            _b("Okay then."),
        ],
        "awkward": [
            _b("That was random."),
            _b("You just… sat down."),
            _b("Okay…"),
        ],
    },
}


def _heat(state: Mapping[str, Any]) -> str:
    a = int(state.get("anger", 0))
    t = int(state.get("trust", 50))
    s = int(state.get("stress", 0))
    if a > 58 or t < 35 or s > 70:
        return "high"
    if a > 45 or t < 45 or s > 55:
        return "mid"
    return "low"


def _smile_upset_first(ref: Mapping[str, Any]) -> bool:
    return (
        int(ref.get("anger", 0)) > 52
        or int(ref.get("trust", 50)) < 38
        or (int(ref.get("stress", 0)) > 62 and int(ref.get("anger", 0)) > 40)
    )


def authored_bucket_for_smile(count: int, before_state: Mapping[str, Any]) -> Optional[str]:
    """Return bucket for authored Smile, or None to defer to engine (progression / shutdown)."""
    if count >= 3:
        return None
    if count == 1 and _smile_upset_first(before_state):
        return None
    if count == 1:
        return "normal"
    if count == 2:
        return "uncertain"
    return None


def authored_bucket_for_stare(count: int) -> str:
    return {1: "normal", 2: "uncertain", 3: "suspicious", 4: "annoyed"}.get(count, "boundary")


def authored_bucket_interrupt(count: int, state: Mapping[str, Any]) -> str:
    h = _heat(state)
    if count >= 3:
        return "boundary"
    if count == 2:
        return {"low": "uncertain", "mid": "annoyed", "high": "boundary"}[h]
    return {"low": "normal", "mid": "uncertain", "high": "annoyed"}[h]


def authored_bucket_step_closer(count: int, state: Mapping[str, Any]) -> str:
    h = _heat(state)
    if count >= 3:
        return "boundary"
    if count == 2:
        return {"low": "annoyed", "mid": "annoyed", "high": "boundary"}[h]
    return {"low": "normal", "mid": "uncertain", "high": "guarded"}[h]


def authored_bucket_step_back(count: int, state: Mapping[str, Any]) -> str:
    if count >= 2:
        return "guarded"
    h = _heat(state)
    return {"low": "normal", "mid": "uncertain", "high": "guarded"}[h]


def authored_bucket_look_away(count: int, state: Mapping[str, Any]) -> str:
    h = _heat(state)
    if count >= 3:
        return "annoyed"
    if count == 2:
        return {"low": "uncertain", "mid": "suspicious", "high": "annoyed"}[h]
    return {"low": "normal", "mid": "uncertain", "high": "suspicious"}[h]


def authored_bucket_raise_voice(count: int, state: Mapping[str, Any]) -> str:
    h = _heat(state)
    if count >= 4:
        return "boundary"
    if count == 3:
        return "escalation"
    if count == 2:
        return "annoyed"
    return "normal"


def authored_bucket_stay_silent(count: int, state: Mapping[str, Any]) -> str:
    if count >= 4:
        return "boundary"
    if count == 3:
        return "annoyed"
    if count == 2:
        return "uncertain"
    return "normal"


def authored_bucket_handshake(count: int, state: Mapping[str, Any]) -> str:
    h = _heat(state)
    if count >= 3:
        return "annoyed"
    if count == 2:
        return "awkward"
    return {"low": "normal", "mid": "uncertain", "high": "guarded"}[h]


def authored_bucket_sit_down(count: int, state: Mapping[str, Any]) -> str:
    if count >= 3:
        return "awkward"
    if count == 2:
        return "uncertain"
    return "normal"


def resolve_authored_bucket(action: str, count: int, state: Mapping[str, Any], before_state: Mapping[str, Any]) -> Optional[str]:
    if action == "Smile":
        return authored_bucket_for_smile(count, before_state)
    if action == "Stare blankly":
        return authored_bucket_for_stare(count)
    if action == "Interrupt":
        return authored_bucket_interrupt(count, state)
    if action == "Step closer":
        return authored_bucket_step_closer(count, state)
    if action == "Step back":
        return authored_bucket_step_back(count, state)
    if action == "Look away":
        return authored_bucket_look_away(count, state)
    if action == "Raise voice":
        return authored_bucket_raise_voice(count, state)
    if action == "Stay silent":
        return authored_bucket_stay_silent(count, state)
    if action == "Offer handshake":
        return authored_bucket_handshake(count, state)
    if action == "Sit down":
        return authored_bucket_sit_down(count, state)
    return None


def _unpack_beat(b: QuarkBeat) -> Tuple[str, Optional[str]]:
    v = (b.get("v") or "").strip()
    p = b.get("p")
    if isinstance(p, str):
        p = p.strip() or None
    else:
        p = None
    return v, p


def pick_random_beat(action: str, bucket: str) -> Tuple[str, Optional[str]]:
    beats = ACTION_QUARKS[action][bucket]
    b = random.choice(beats)
    return _unpack_beat(b)


def pick_random_beat_weighted(action: str, bucket: str, weights: Sequence[int]) -> Tuple[str, Optional[str]]:
    beats = ACTION_QUARKS[action][bucket]
    if len(weights) != len(beats):
        b = random.choice(beats)
    else:
        b = random.choices(beats, weights=list(weights), k=1)[0]
    return _unpack_beat(b)


@dataclass(frozen=True)
class AuthoredActionPick:
    verbal_inner: str
    physical: Optional[str]
    lock_physical: bool = False
    lock_verbatim: bool = True
    tone_override: Optional[str] = None
    vibe_override: Optional[str] = None
    moonwalk_universe_mode: bool = False


def pick_moonwalk_authored(streak: int) -> AuthoredActionPick:
    """streak is consecutive moonwalk count including this turn (1, 2, 3+)."""
    if streak <= 1:
        return AuthoredActionPick(
            verbal_inner="I'm boutta fuck it up yo.",
            physical="begins to hit the nastiest griddy the planet has ever seen",
            lock_physical=True,
        )
    if streak == 2:
        return AuthoredActionPick(
            verbal_inner="Gah daum I'm brutally fucking it up right now.",
            physical="Continues to brutally fuck it up",
            lock_physical=True,
        )
    return AuthoredActionPick(
        verbal_inner="I can do this all day.",
        physical="Proceeds to do it all day.",
        lock_physical=True,
        moonwalk_universe_mode=True,
        tone_override="unfathomable",
        vibe_override="electric",
    )


def try_pick_authored_action_response(
    action: str,
    count: int,
    state: Mapping[str, Any],
    before_state: Mapping[str, Any],
    moonwalk_streak: int,
) -> Optional[AuthoredActionPick]:
    """
    Primary verbal/physical for do-actions from authored bank.
    None => fall through to action_reaction + maybe_social + minimal.
    """
    if action == "Hit the moonwalk":
        if moonwalk_streak >= 4:
            return None
        return pick_moonwalk_authored(moonwalk_streak)

    if action not in ACTION_QUARKS:
        return None

    bucket = resolve_authored_bucket(action, count, state, before_state)
    if bucket is None:
        return None

    if action == "Smile" and bucket == "normal":
        v, p = pick_random_beat_weighted(action, bucket, (5, 5, 1, 5, 2))
    elif action == "Smile" and bucket == "uncertain":
        v, p = pick_random_beat_weighted(action, bucket, (4, 5, 2, 2))
    elif action == "Offer handshake" and bucket == "normal":
        v, p = pick_random_beat_weighted(action, bucket, (1, 5, 4))
    elif action == "Offer handshake" and bucket == "guarded":
        v, p = pick_random_beat_weighted(action, bucket, (1, 4, 4, 5))
    else:
        v, p = pick_random_beat(action, bucket)
    return AuthoredActionPick(
        verbal_inner=v,
        physical=p,
        lock_physical=bool(p),
        lock_verbatim=True,
    )
