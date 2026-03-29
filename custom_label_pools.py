# -*- coding: utf-8 -*-
"""Authored vibe / relationship / tone labels (``other quarks.txt`` at project root).

Dropdown SAY demo mode does not use these for the final displayed line; see interaction_response / responses.demo_safe_dropdown_say_relationship.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import List, Tuple


def _split_csv_blob(blob: str) -> List[str]:
    parts = []
    for piece in blob.split(","):
        t = piece.strip()
        if t:
            parts.append(t)
    return parts


def _csv_accum_in_blob(blob: str) -> List[str]:
    acc: List[str] = []
    for line in blob.splitlines():
        if "," not in line:
            continue
        piece = line.split(":", 1)[-1] if ":" in line else line
        acc.extend(_split_csv_blob(piece))
    return acc


def _parse_other_quarks(text: str) -> Tuple[List[str], List[str], List[str]]:
    low = text.lower()
    m1 = low.find("here are some relationships")
    m2 = low.find("here are some tones")
    if m1 < 0 or m2 < m1:
        return (["neutral"], [], [])
    vibes = _csv_accum_in_blob(text[:m1])
    rel = _csv_accum_in_blob(text[m1:m2])
    tones = _csv_accum_in_blob(text[m2:])
    return (vibes or ["neutral"], rel, tones)


def _load() -> Tuple[List[str], List[str], List[str]]:
    path = Path(__file__).resolve().parent / "other_quarks.txt"
    return _parse_other_quarks(path.read_text(encoding="utf-8"))


PREFERRED_VIBES, PREFERRED_RELATIONSHIPS, PREFERRED_TONES = _load()

_HOSTILE_TONE_KEYS = frozenset(
    {"mad", "angry", "furious", "bloodthirsty", "cruel", "sarcastic", "judgemental", "short"}
)
_WARM_TONE_KEYS = frozenset({"happy", "extatic", "electric", "whisper"})
_TENSE_TONE_KEYS = frozenset({"tense", "confused", "horribly sad", "meloncholy"})
_UNCERTAIN_TONE_KEYS = frozenset({"confused", "meloncholy", "bored"})
_ENGAGED_TONE_KEYS = frozenset({"curious", "intrigued", "electric", "high pitched"})

_HOSTILE_VIBE_KEYS = frozenset(
    {"bad", "not chill", "zero chill", "wack as hell", "garbage", "going gorillas", "intense"}
)
_CALM_VIBE_KEYS = frozenset({"good", "chill", "vibing", "tremendous", "swag"})
_OPEN_VIBE_KEYS = frozenset({"good", "vibing", "tremendous", "godly", "unfathomable"})
_EDGE_VIBE_KEYS = frozenset({"not chill", "bruh what is going on", "interesting"})
_AWKWARD_VIBE_KEYS = frozenset({"bruh what is going on", "interesting", "wack as hell"})
_CURIOUS_VIBE_KEYS = frozenset({"interesting", "vibing"})
_NEUTRAL_VIBE_KEYS = frozenset({"interesting", "vibing", "swag"})


def _pick_from(labels: List[str], subset_keys: frozenset) -> str:
    pool = [x for x in labels if x.lower() in subset_keys]
    if pool:
        return random.choice(pool)
    return ""


def preferred_tone_for(base: str) -> str:
    """Map engine tone bucket to an authored label when possible."""
    b = (base or "").strip().lower()
    if b == "hostile":
        return _pick_from(PREFERRED_TONES, _HOSTILE_TONE_KEYS) or "hostile"
    if b == "tense":
        return _pick_from(PREFERRED_TONES, _TENSE_TONE_KEYS) or "tense"
    if b == "warm":
        return _pick_from(PREFERRED_TONES, _WARM_TONE_KEYS) or "warm"
    if b == "uncertain":
        return _pick_from(PREFERRED_TONES, _UNCERTAIN_TONE_KEYS) or "uncertain"
    if b == "engaged":
        return _pick_from(PREFERRED_TONES, _ENGAGED_TONE_KEYS) or "engaged"
    if b == "neutral":
        return _pick_from(PREFERRED_TONES, _ENGAGED_TONE_KEYS | _UNCERTAIN_TONE_KEYS) or "neutral"
    return base


def preferred_vibe_for(base: str) -> str:
    """Map engine vibe bucket to an authored label when possible."""
    b = (base or "").strip().lower()
    if b == "hostile":
        return _pick_from(PREFERRED_VIBES, _HOSTILE_VIBE_KEYS) or "hostile"
    if b == "about to become violent":
        return _pick_from(PREFERRED_VIBES, _HOSTILE_VIBE_KEYS | {"intense", "unfathomable"}) or b
    if b == "comfortable and open":
        return _pick_from(PREFERRED_VIBES, _OPEN_VIBE_KEYS) or b
    if b == "uneasy and on edge":
        return _pick_from(PREFERRED_VIBES, _EDGE_VIBE_KEYS) or b
    if b == "awkward and uncertain":
        return _pick_from(PREFERRED_VIBES, _AWKWARD_VIBE_KEYS) or b
    if b == "locked in and curious":
        return _pick_from(PREFERRED_VIBES, _CURIOUS_VIBE_KEYS) or b
    if b == "calm":
        return _pick_from(PREFERRED_VIBES, _CALM_VIBE_KEYS) or b
    if b == "neutral":
        return _pick_from(PREFERRED_VIBES, _NEUTRAL_VIBE_KEYS) or "neutral"
    return base


def preferred_relationship_read(engine_label: str) -> str:
    """Prefer authored relationship words when they align with the engine read."""
    lab = (engine_label or "").strip().lower()
    if not PREFERRED_RELATIONSHIPS:
        return engine_label
    if lab in ("hostile", "done"):
        pool = [x for x in PREFERRED_RELATIONSHIPS if x.lower() in {"bad", "ugly", "uncomfortable", "weird"}]
        return random.choice(pool) if pool else engine_label
    if lab in ("open",):
        pool = [x for x in PREFERRED_RELATIONSHIPS if x.lower() in {"good", "close", "comfortable", "bros"}]
        return random.choice(pool) if pool else engine_label
    if lab in ("guarded", "uncertain"):
        pool = [x for x in PREFERRED_RELATIONSHIPS if x.lower() in {"complicated", "weird", "getting to know eachother", "curious"}]
        return random.choice(pool) if pool else engine_label
    return engine_label
