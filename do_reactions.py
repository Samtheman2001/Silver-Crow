# -*- coding: utf-8 -*-
"""Engine-authored do-action progression (non-quark actions)."""

from __future__ import annotations

import random
from typing import Any, Mapping, Optional, Tuple

from brain import infer_physical_response, infer_tone, infer_vibe
from utils import quote


def action_reaction(
    action_text: str,
    count: int,
    state: Mapping[str, Any],
    personality: str,
    before_state: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, str, str, str, bool]:
    """Returns (verbal, tone, physical, vibe, ended). Verbal may be empty for layered picks."""
    tone = infer_tone(state)
    vibe = infer_vibe(state)
    physical = infer_physical_response(state)
    aggressive_end = personality in {"Aggressive", "Impulsive"}

    if action_text == "Smile":
        if count == 1:
            ref = before_state if before_state is not None else state
            upset_context = (
                ref["anger"] > 52
                or ref["trust"] < 38
                or (ref["stress"] > 62 and ref["anger"] > 40)
            )
            if upset_context:
                return (
                    quote(
                        random.choice(
                            [
                                "Why are you smiling right now?",
                                "Is this funny to you?",
                                "What's funny?",
                                "I don't get why you're smiling.",
                            ]
                        )
                    ),
                    "tense",
                    "stares at you without returning it",
                    "uncomfortable",
                    False,
                )
            return "", tone, "smiles back slightly", vibe, False
        if count == 2:
            return "", "uncertain", "tilts head a little like they're trying to read you", "mildly confused", False
        if count == 3:
            return quote("Why are you just smiling at me?"), "tense", "leans back slightly", "awkward", False
        if count == 4:
            return (
                quote("Alright, you're being weird now. If you keep doing this I'm leaving."),
                "hostile",
                "stops smiling and looks annoyed",
                "vibe slipping",
                False,
            )
        if count == 5 and aggressive_end:
            return quote("What is your problem? Back up."), "hostile", "slaps your hand away and storms off", "murdered", True
        if count == 5:
            return (
                quote("I mean it—quit it. This is uncomfortable."),
                "hostile",
                "takes a step back and crosses their arms",
                "uncomfortable",
                False,
            )
        if aggressive_end:
            return quote("What is your problem? Back up."), "hostile", "slaps your hand away and storms off", "murdered", True
        return quote("I'm leaving. This is too weird."), "hostile", "walks away shaking their head", "murdered", True

    if action_text == "Stare blankly":
        if count == 1:
            return quote("...You good?"), "uncertain", "waves a hand in front of your face", "awkward", False
        if count == 2:
            return quote("Okay, now you're doing a little too much."), "tense", "leans back and furrows brow", "awkward", False
        if count == 3:
            return (
                quote("Why are you staring at me like that?"),
                "hostile",
                "breaks eye contact and looks irritated",
                "vibe slipping",
                False,
            )
        if count == 4:
            return quote("Stop that. Seriously."), "hostile", "looks openly unsettled now", "vibe slipping", False
        if aggressive_end:
            return quote("Back up before I make this a problem."), "hostile", "steps in and snaps at you", "murdered", True
        return quote("Nope. I'm out."), "hostile", "gets up and leaves", "murdered", True

    if action_text == "Step closer":
        if count == 1:
            return "", tone, physical, vibe, False
        if count == 2:
            return (
                quote(random.choice(["Woah there.", "Hey—personal space.", "Okay, back up a little."])),
                "tense",
                "leans back and puts a hand up",
                "on edge",
                False,
            )
        if count == 3:
            return (
                quote(
                    random.choice(
                        [
                            "I said back up.",
                            "You need to give me some space.",
                            "Seriously, step back.",
                        ]
                    )
                ),
                "hostile",
                "stiffens and takes a full step back",
                "uncomfortable",
                False,
            )
        if count >= 4:
            if aggressive_end:
                return quote("Touch me and we're done."), "hostile", "squares up", "murdered", True
            return quote("I'm leaving."), "hostile", "backs away and turns to go", "murdered", True

    if action_text == "Offer handshake":
        if count == 1:
            return "", tone, "takes the handshake after a short pause", vibe, False
        if count == 2:
            return quote("We already did that."), "uncertain", "looks at your hand, confused", "awkward", False
        if count == 3:
            return quote("Okay, enough with the hand thing."), "tense", "refuses the handshake", "annoyed", False
        if count == 4:
            return quote("Touch me again and this goes badly."), "hostile", "pulls away hard", "hostile", False
        if aggressive_end:
            return (
                quote("Touch me again and we're going to have a problem."),
                "hostile",
                "pulls away hard and squares up",
                "murdered",
                True,
            )
        return quote("Nope. Conversation over."), "hostile", "steps back and ends the interaction", "murdered", True

    if count == 1:
        return "", tone, physical, vibe, False
    if count == 2:
        return quote("You just did that."), "uncertain", "looks a little confused", "awkward", False
    if count == 3:
        return quote("Why do you keep doing that?"), "tense", "fidgets and watches you more carefully", "vibe slipping", False
    if count == 4:
        return quote("If you keep doing that, I'm gone."), "hostile", "gets visibly annoyed", "vibe slipping", False
    if aggressive_end:
        return quote("Stop doing that."), "hostile", "snaps at you and shuts the interaction down", "murdered", True
    return quote("Okay, I'm done here."), "hostile", "pulls back and leaves", "murdered", True
