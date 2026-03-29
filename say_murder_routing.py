# -*- coding: utf-8 -*-
"""Say-triggered repeat escalation + VIBES MURDERED lines must come from the authored bank for that exact prompt."""

from __future__ import annotations

import random
from typing import Callable, List, Optional

from .canon_prompts import get_authored_prompt_bank
from .config import SAY_OPTIONS
from .utils import strip_outer_quotes

FREE_TEXT_REPETITION_MURDER_LINES: tuple[str, ...] = (
    "I heard you the first time. I'm not doing this on loop.",
    "Say something new or we're done.",
    "You're stuck on repeat and I'm not playing along.",
    "I'm not your echo chamber. Stop.",
    "Enough. I'm out.",
)

FREE_TEXT_REPETITION_MURDER_PHYSICAL: tuple[str, ...] = (
    "exhales through the nose, turns their shoulders away — done indulging the loop",
    "holds up a flat palm, eyes cold; body language screams exit",
    "steps back, jaw tight, not hiding that they're clocking out",
    "looks past you like you're background noise, already disengaging",
    "turns on their heel without another beat, conversation dead",
)

FREE_TEXT_REPEAT_WARN_1: tuple[str, ...] = (
    "Didn't you just ask me that?",
    "You already asked that.",
    "Yeah—same answer.",
    "We literally just covered this.",
)

FREE_TEXT_REPEAT_WARN_2: tuple[str, ...] = (
    "Didn't you just say that?",
    "You're repeating yourself.",
    "I already answered that.",
)

FREE_TEXT_REPEAT_WARN_3: tuple[str, ...] = (
    "If you keep doing this, I'm going to leave.",
    "Please stop. This is getting irritating.",
    "I don't know what you're doing here, but it is not going well.",
)


def _coerce_lines(raw_lines) -> List[str]:
    out: List[str] = []
    for x in raw_lines or []:
        if hasattr(x, "text"):
            txt = str(getattr(x, "text") or "").strip()
        elif isinstance(x, dict):
            txt = str(x.get("text") or "").strip()
        else:
            txt = str(x).strip()
        if txt:
            out.append(txt)
    return out


def negative_lines_for_say_prompt(prompt_key: str) -> List[str]:
    bank = get_authored_prompt_bank(prompt_key)
    if not bank:
        return []
    return _coerce_lines(bank.buckets.get("negative") or [])


def positive_lines_for_say_prompt(prompt_key: str) -> List[str]:
    bank = get_authored_prompt_bank(prompt_key)
    if not bank:
        return []
    return _coerce_lines(bank.buckets.get("positive") or [])


def neutral_lines_for_say_prompt(prompt_key: str) -> List[str]:
    bank = get_authored_prompt_bank(prompt_key)
    if not bank:
        return []
    return _coerce_lines(bank.buckets.get("neutral") or [])


def severe_lines_for_say_prompt(prompt_key: str) -> List[str]:
    bank = get_authored_prompt_bank(prompt_key)
    if not bank:
        return []
    return _coerce_lines(bank.buckets.get("severe") or [])


def murder_lines_for_say_prompt(prompt_key: str) -> List[str]:
    neg = negative_lines_for_say_prompt(prompt_key)
    sev = severe_lines_for_say_prompt(prompt_key)
    return neg + sev


_REPEAT_ACK_MARKERS = (
    "again",
    "repeat",
    "already",
    "just asked",
    "just ask",
    "just said",
    "repeating",
    "same ",
    "keep ",
    "going in circles",
    "you said",
    "literally",
    "loop",
)


def line_acknowledges_repetition(line: str) -> bool:
    """True if authored text already signals repeat / loop (demo ACK prepends skipped)."""
    if not (line or "").strip():
        return False
    t = (line or "").lower()
    return any(m in t for m in _REPEAT_ACK_MARKERS)


def _ensure_repeat_acknowledgement(line: str, repeat_count: int) -> str:
    if repeat_count < 1 or not (line or "").strip():
        return line
    if line_acknowledges_repetition(line):
        return line
    return f"You're asking that again. {line}"


def _norm_inner_compare(s: str) -> str:
    return strip_outer_quotes(s or "").strip().lower()


def _unique_ordered_bases(lines: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for line in lines or []:
        n = _norm_inner_compare(line)
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(line)
    return out


def dropdown_say_candidate_bases_for_repeat(prompt_key: str, repeat_count: int) -> List[str]:
    """
    Ordered authored bases for menu SAY demo by repeat tier (before ack prefix).
    Caller filters by per-run used lines and consecutive-turn rule.
    """
    pos = positive_lines_for_say_prompt(prompt_key)
    neu = neutral_lines_for_say_prompt(prompt_key)
    neg = negative_lines_for_say_prompt(prompt_key)
    sev = severe_lines_for_say_prompt(prompt_key)
    if repeat_count <= 0:
        return _unique_ordered_bases(pos + neu)
    if repeat_count == 1:
        return _unique_ordered_bases(neu + neg + sev)
    if repeat_count == 2:
        return _unique_ordered_bases(neg + sev)
    if repeat_count == 3:
        return _unique_ordered_bases(sev + neg)
    return _unique_ordered_bases(sev + neg)


def pick_dropdown_say_line_deterministic(prompt_key: str, repeat_count: int) -> str:
    """Deprecated path: first candidate only. Prefer interaction_response unused-line picker."""
    bases = dropdown_say_candidate_bases_for_repeat(prompt_key, repeat_count)
    if not bases:
        return ""
    b = bases[0]
    if repeat_count >= 1:
        return _ensure_repeat_acknowledgement(b, repeat_count)
    return b


def pick_say_repeat_warning_line(prompt_key: str, repeat_count: int, *, is_free_text: bool) -> str:
    if is_free_text:
        if repeat_count <= 1:
            return random.choice(FREE_TEXT_REPEAT_WARN_1)
        if repeat_count == 2:
            return random.choice(FREE_TEXT_REPEAT_WARN_2)
        return random.choice(FREE_TEXT_REPEAT_WARN_3)

    neg = negative_lines_for_say_prompt(prompt_key)
    sev = severe_lines_for_say_prompt(prompt_key)

    if repeat_count <= 1 and neg:
        return random.choice(neg)

    if repeat_count == 2:
        if sev:
            return random.choice(sev)
        if neg:
            return random.choice(neg)

    if repeat_count >= 3:
        if sev:
            return random.choice(sev)
        if neg:
            return random.choice(neg)

    if sev:
        return random.choice(sev)
    if neg:
        return random.choice(neg)
    return random.choice(FREE_TEXT_REPEAT_WARN_2)


def pick_say_repetition_murder_line(
    prompt_key: str,
    *,
    is_free_text: bool,
    avoid_inner_norm: str | None = None,
    excluded_inner_norms: frozenset[str] | set[str] | None = None,
    line_norm_fn: Optional[Callable[[str], str]] = None,
) -> str:
    if not is_free_text:
        pool = murder_lines_for_say_prompt(prompt_key)
        if pool:
            avoid = (avoid_inner_norm or "").strip().lower()
            excl = excluded_inner_norms or frozenset()
            excl_l = {str(x).strip().lower() for x in excl if str(x).strip()}
            norm_fn = line_norm_fn or _norm_inner_compare

            def ordered_pick(use_exclude: bool) -> str | None:
                for p in pool:
                    n = norm_fn(p)
                    if avoid and n == avoid:
                        continue
                    if use_exclude and n in excl_l:
                        continue
                    return p
                return None

            hit = ordered_pick(True)
            if hit is not None:
                return hit
            hit = ordered_pick(False)
            if hit is not None:
                return hit
            return pool[0]
    return random.choice(FREE_TEXT_REPETITION_MURDER_LINES)


# Demo mode: exactly one fixed VM line per dropdown prompt (no pools, no random).
DEMO_VM_LINE_FALLBACK = "We're done here. Move on."
DEMO_VM_PHYSICAL_DEFAULT = (
    "steps back, face shutting down — they're not giving this another inch of energy"
)

DEMO_VM_LINES: dict[str, str] = {
    "Hello, nice to meet you.": "Yeah, no. We're done here.",
    "Hey, how are you?": "I'm done answering that.",
    "What's up?": "Nothing. And we're done.",
    "Do you mind if I sit here?": "Yeah, I mind. Go.",
    "Nice to meet you": "Not anymore. We're finished.",
    "What's your name?": "You don't get to know. We're done.",
    "I disagree with you.": "Keep disagreeing somewhere else.",
    "You're wrong.": "We're not doing this loop again.",
    "I want to help.": "I don't want your help. Leave.",
    "I respect your opinion.": "Respect this: we're done.",
    "What do you need?": "I need you to stop.",
    "Do you like me?": "No. And now I definitely don't.",
    "Why don't you like me?": "Because you won't stop asking.",
    "What do you think of me so far?": "I think we're done here.",
    "Do you want to go on a date?": "No. Ask me again and we're finished.",
    "Why don't you want to go on a date?": "Stop. Conversation over.",
    "Why are you treating me this way?": "Because you're stuck on repeat.",
    "Why are you acting like this?": "Because you won't drop it.",
    "Who do you think you are?": "Someone who's done with this.",
    "Why should I trust you?": "You shouldn't. That's the point.",
    "What are your thoughts on the stock market these days?": "I'm not your podcast. Done.",
    "Where did you get those shoes?": "We're not doing that question again.",
    "Do you own a jetski?": "No more jetski talk. Ever.",
    "Would you like to buy my jetski?": "Hard no. Forever.",
    "What are your thoughts on jetskis?": "I'm out.",
    "Who is the most attractive person in history?": "I'm not playing this game again.",
    "Is Playboi Carti overrated?": "We're done discussing Carti.",
    "Cash me outside, how 'bout that?": "No. Absolutely not. Again.",
    "Are you Republican or Democrat?": "I'm not doing politics on loop.",
    "Do you think you're better than me?": "I'm done proving anything to you.",
    "Why are you talking to me?": "Good question. This conversation is over.",
    "Why do you care?": "I don't. Not anymore.",
    "Why are you so quiet?": "Because I'm done talking to you.",
    "Can you help me?": "Not if you keep looping.",
    "What gives you the right?": "We're past that. Done.",
    "Do you think I'm attractive?": "No. Final answer.",
    "Can I sleep at your house tonight?": "No. Never ask again.",
    "Can a young gangsta get money anymore?": "We're not running this back.",
    "What are your thoughts on this weather?": "I'm not discussing weather again.",
    "Do you think you're funny?": "Not funny enough to repeat this.",
    "Why are you looking at me like that?": "Because I'm done with you.",
    "What do you want?": "For you to stop.",
    "Are you having a good day?": "It was. Now it's ruined. Done.",
    "What are you up to today?": "None of your business anymore.",
    "Do you come here often?": "Not with you in my face like this.",
    "Sam Howell sent me.": "Sam's not saving this conversation.",
}

# Full-body VM beat paired with each authored demo verbal (same prompt key as DEMO_VM_LINES).
DEMO_VM_PHYSICAL: dict[str, str] = {
    "Hello, nice to meet you.": (
        "steps back and shakes their head, already mentally checked out"
    ),
    "Hey, how are you?": "looks away mid-sentence, shoulders squared — not answering again",
    "What's up?": "dead stare, one eyebrow flat; they've already left the conversation",
    "Do you mind if I sit here?": "slides their stuff into the empty seat, blocking you out",
    "Nice to meet you": "breaks eye contact and angles their body away, hard stop",
    "What's your name?": "mouth tightens; they fold their arms like a door closing",
    "I disagree with you.": "tilts their chin up, dismissive wave — take it somewhere else",
    "You're wrong.": "exhales sharply, turns half away; not doing another round",
    "I want to help.": "recoils slightly, palms out — they don't want your help",
    "I respect your opinion.": "slow blink, flat mouth; respect isn't on the table anymore",
    "What do you need?": "stares you down, then breaks off like you're wasting oxygen",
    "Do you like me?": "scoffs without sound, looks at the ceiling — answer was no",
    "Why don't you like me?": "rubs their temple, won't meet your eyes; exhausted by the loop",
    "What do you think of me so far?": "looks through you, not at you; verdict's delivered",
    "Do you want to go on a date?": "takes a full step back, hands in pockets — hard boundary",
    "Why don't you want to go on a date?": "jaw set, voice gone from their face; topic closed",
    "Why are you treating me this way?": "spreads their hands, then drops them — done explaining",
    "Why are you acting like this?": "shoulders hike, chin down; they're not performing patience",
    "Who do you think you are?": "half-turns like they're leaving the frame of you",
    "Why should I trust you?": "eyes narrow, one corner of the mouth down; trust isn't on offer",
    "What are your thoughts on the stock market these days?": (
        "taps their phone awake, already bored — not your finance hour"
    ),
    "Where did you get those shoes?": "glances at your feet, then away; not engaging the bit",
    "Do you own a jetski?": "pinches the bridge of their nose; jetski topic cremated",
    "Would you like to buy my jetski?": "laughs once, hollow, and turns away",
    "What are your thoughts on jetskis?": "waves a hand like swatting smoke — done with jetskis",
    "Who is the most attractive person in history?": (
        "rolls their eyes toward the exit; not playing ranking games"
    ),
    "Is Playboi Carti overrated?": "mouth a flat line; Carti discourse is over",
    "Cash me outside, how 'bout that?": "stares, then looks at their watch — absolute no",
    "Are you Republican or Democrat?": "leans away, hands up — not your debate partner",
    "Do you think you're better than me?": "tilts their head, pity-flash, then shuts it off",
    "Why are you talking to me?": "gestures at the space between you like it's contaminated",
    "Why do you care?": "shrugs once, cold; caring left the building",
    "Why are you so quiet?": "lips press thin; silence is the whole answer",
    "Can you help me?": "already stepping back, shaking their head — not on repeat",
    "What gives you the right?": "squares up, then exhales and pivots away — argument over",
    "Do you think I'm attractive?": "looks you over once, flat, then breaks eye contact hard",
    "Can I sleep at your house tonight?": "recoils, boundary written on their whole body",
    "Can a young gangsta get money anymore?": "rubs their eyes, turns sideways — not rerunning this",
    "What are your thoughts on this weather?": "glances at the sky without seeing it; not chatting",
    "Do you think you're funny?": "deadpan, not a muscle moving — joke didn't land, you're done",
    "Why are you looking at me like that?": "meets your eyes once, then cuts away like a blade",
    "What do you want?": "hands on hips, then drops them; wants you to stop",
    "Are you having a good day?": "smile dies on their face; day was fine until this",
    "What are you up to today?": "checks the door, weight on back foot — leaving energy",
    "Do you come here often?": "doesn't answer; body already angled toward anywhere else",
    "Sam Howell sent me.": (
        "closes their phone and looks at you like you're not worth another second"
    ),
}

for _demo_vm_key in SAY_OPTIONS:
    DEMO_VM_LINES.setdefault(_demo_vm_key, DEMO_VM_LINE_FALLBACK)
    DEMO_VM_PHYSICAL.setdefault(_demo_vm_key, DEMO_VM_PHYSICAL_DEFAULT)


def _build_vm_physical_by_verbal_norm() -> dict[str, str]:
    out: dict[str, str] = {}
    for _pk in SAY_OPTIONS:
        _phys = DEMO_VM_PHYSICAL.get(_pk, DEMO_VM_PHYSICAL_DEFAULT)
        for _line in murder_lines_for_say_prompt(_pk):
            nn = _norm_inner_compare(_line)
            if nn:
                out.setdefault(nn, _phys)
        dv = DEMO_VM_LINES.get(_pk, "")
        if dv:
            out.setdefault(_norm_inner_compare(dv), _phys)
    for _i, _v in enumerate(FREE_TEXT_REPETITION_MURDER_LINES):
        out.setdefault(_norm_inner_compare(_v), FREE_TEXT_REPETITION_MURDER_PHYSICAL[_i])
    return out


_VM_PHYSICAL_BY_VERBAL_NORM: dict[str, str] = _build_vm_physical_by_verbal_norm()


def resolve_say_vm_physical(prompt: str, line_inner: str, *, is_free_text: bool) -> str:
    """
    Body-language line for SAY-triggered VIBES MURDERED. Never empty.
    Matches authored verbal when possible; falls back to this prompt's VM physical if
    name-fill/sanitize changed the wording.
    """
    key = str(prompt or "").strip()
    n = _norm_inner_compare(line_inner)
    hit = _VM_PHYSICAL_BY_VERBAL_NORM.get(n)
    if hit:
        return hit
    if not is_free_text:
        return DEMO_VM_PHYSICAL.get(key, DEMO_VM_PHYSICAL_DEFAULT)
    return FREE_TEXT_REPETITION_MURDER_PHYSICAL[0]


def demo_dropdown_vm_inner_line(prompt: str) -> str:
    """Single authored VM line for menu SAY demo; no pools or randomness."""
    key = str(prompt or "").strip()
    return DEMO_VM_LINES.get(key, DEMO_VM_LINE_FALLBACK)
