# -*- coding: utf-8 -*-
"""
First-time-only SAY menu overrides (repeat_count == 0 for that prompt).

These apply only on the first selection of that line in the current conversation.
Repeats use the existing demo repeat / escalation / VM ladder unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class SayFirstHitOverride:
    """Inner verbal (before quote()) and/or physical. None = leave that field to normal pipeline."""

    verbal_inner: Optional[str] = None
    physical: Optional[str] = None


_SAY_FIRST_HIT_OVERRIDES: Dict[str, SayFirstHitOverride] = {
    "Why don't you like me?": SayFirstHitOverride(
        physical="slightly alarmed, slightly confused",
    ),
    "What do you think of me so far?": SayFirstHitOverride(
        physical="smiles",
    ),
    "Why are you treating me this way?": SayFirstHitOverride(
        physical="shrugs",
    ),
    "Who is the most attractive person in history?": SayFirstHitOverride(
        verbal_inner="Sam Howell. Next subject.",
        physical="looks at you like you are speaking Martian",
    ),
    "Are you Republican or Democrat?": SayFirstHitOverride(
        verbal_inner=(
            "Republican. I love Trump. Wait no. Democrat. I love Biden he is like Bush lite."
        ),
    ),
    "Do you think you're better than me?": SayFirstHitOverride(
        physical="looks at you like they are better than you",
    ),
    "Why are you so quiet?": SayFirstHitOverride(
        physical="proceeds to listen",
    ),
    "Do you think I'm attractive?": SayFirstHitOverride(
        physical="Stares off into space daydreaming about Sam Howell…",
    ),
    "Sam Howell sent me.": SayFirstHitOverride(
        physical="Becomes visibly flustered and stares off into space.",
    ),
}


def get_say_first_hit_override(prompt: str) -> Optional[SayFirstHitOverride]:
    return _SAY_FIRST_HIT_OVERRIDES.get(str(prompt or "").strip())
