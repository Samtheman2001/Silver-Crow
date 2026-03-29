# -*- coding: utf-8 -*-
"""
Context-aware finisher lines for hard shutdown (VIBES MURDERED, verbal boundary, etc.).

All spoken finisher text is extracted verbatim from quarks.txt (see line refs below).
Tier weights: common 55%, signature 35%, nuclear 10%.
Within tier: score by tags vs interaction_profile; weighted pick; streak avoidance; micro-variation (prefixes only from quarks-neutral empty string).
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple, Union

FinisherTier = Literal["common", "signature", "nuclear"]

# Do-action shutdowns use only FINISHER_EXTRAS pools (never the full bank), so nuclear
# picks cannot surface unrelated meme / flex lines (e.g. courtside rant) mid Smile arc.
_SHUTDOWN_KINDS_ACTION_POOL_ONLY: frozenset[str] = frozenset(
    {"action_shutdown", "action_shutdown_benign", "action_shutdown_smile"}
)

# Repeated non-hostile / low-intrusion actions → softer finisher vocabulary.
BENIGN_DO_ACTION_FINISHERS: frozenset[str] = frozenset(
    {
        "Offer handshake",
        "Sit down",
        "Stay silent",
        "Look away",
        "Step back",
        "Hit the moonwalk",
        "Stare blankly",
    }
)


def finisher_shutdown_kind_for_do_action(action: str) -> str:
    a = (action or "").strip()
    if a == "Smile":
        return "action_shutdown_smile"
    if a in BENIGN_DO_ACTION_FINISHERS:
        return "action_shutdown_benign"
    return "action_shutdown"

FINISHER_SESSION_DEBUG_KEY = "_finisher_debug"

_TIER_ORDER: Tuple[FinisherTier, ...] = ("common", "signature", "nuclear")
_WEIGHTS: Tuple[int, int, int] = (55, 35, 10)

# No invented prefixes — only the empty prefix (lines are complete in quarks).
DEFAULT_PREFIXES: Tuple[str, ...] = ("",)

RawEntry = Union[str, Dict[str, Any]]

_QUARKS_PATH = Path(__file__).resolve().parent / "quarks.txt"
_QUARKS_LINES_CACHE: Optional[List[str]] = None

# Fallback if a tier pool is empty (must stay synced with quarks line 123).
_FALLBACK_LINE_NUMBER = 123

Ref = Tuple[int, Tuple[str, ...]]


def _quarks_lines() -> List[str]:
    global _QUARKS_LINES_CACHE
    if _QUARKS_LINES_CACHE is None:
        _QUARKS_LINES_CACHE = _QUARKS_PATH.read_text(encoding="utf-8").splitlines()
    return _QUARKS_LINES_CACHE


def _extract_dialogue_from_raw_quarks_line(raw_line: str) -> str:
    """Pull the dialogue string from one quarks.txt line (curly quotes, straight, or mispaired U+201D)."""
    s = raw_line.strip()
    s = re.sub(r"\[.*\]\s*$", "", s).rstrip()
    if s.startswith('"'):
        if len(s) >= 2 and s[-1] in ('"', "\u201d"):
            return s[1:-1]
    if s.startswith("\u201c") and s.endswith("\u201d") and len(s) >= 2:
        return s[1:-1]
    if s.startswith("\u201d") and s.endswith("\u201d") and len(s) >= 2:
        return s[1:-1]
    if "\u201c" in s:
        si = s.index("\u201c")
        ei = s.rindex("\u201d")
        return s[si + 1 : ei]
    raise ValueError(f"No dialogue in quarks line: {raw_line!r}")


def _entry_from_ref(line_no: int, tags: Tuple[str, ...]) -> RawEntry:
    text = _extract_dialogue_from_raw_quarks_line(_quarks_lines()[line_no - 1])
    if tags:
        return {"text": text, "tags": list(tags)}
    return {"text": text}


def _tier_from_refs(refs: Sequence[Ref]) -> List[RawEntry]:
    return [_entry_from_ref(ln, tg) for ln, tg in refs]


# --- Line refs: (quarks.txt 1-based line, tags). Text is never edited here. ---
#
# COMMON — realistic hard negatives / shutdowns (mostly 🔴 / some severe prompts)
_COMMON_REFS: List[Ref] = [
    (123, ()),
    (124, ("disrespect", "judgment")),
    (125, ("dismissive",)),
    (162, ("persistence",)),
    (163, ()),
    (164, ()),
    (167, ("cold",)),
    (168, ("boundary", "cold")),
    (169, ("boundary",)),
    (54, ()),
    (55, ("dismissive",)),
    (76, ("boundary",)),
    (77, ("boundary",)),
    (78, ("boundary",)),
    (99, ("disrespect",)),
    (101, ("boundary",)),
    (245, ("cold",)),
    (248, ("final",)),
    (249, ("final",)),
    (314, ("final", "cold")),
    (333, ("final", "cold")),
    (294, ("judgment",)),
    (295, ("judgment",)),
    (296, ("cold",)),
    (583, ("dismissive", "boundary")),
    (596, ("dismissive", "repetition")),
    (750, ("dismissive", "cold")),
    (751, ("dismissive", "persistence")),
    (789, ("dismissive",)),
    (790, ("disrespect", "repetition")),
    (786, ("dismissive",)),
    (807, ("dismissive",)),
    (808, ("dismissive",)),
    (806, ("dismissive",)),
    (230, ("dismissive", "cold")),
    (226, ("disrespect", "repetition")),
    (227, ()),
    (767, ("cold",)),
    (548, ("disrespect", "boundary")),
]

# SIGNATURE — memorable / very Silver Crow (🔴🔥, rares, long burns)
_SIGNATURE_REFS: List[Ref] = [
    (38, ("judgment", "cold")),
    (39, ("disrespect", "cold")),
    (57, ("disrespect", "dismissive")),
    (58, ("disrespect", "dismissive")),
    (59, ("dismissive",)),
    (81, ("boundary", "disrespect")),
    (82, ("boundary", "disrespect")),
    (103, ("boundary", "disrespect")),
    (104, ("repetition", "boundary")),
    (119, ("disrespect",)),
    (120, ("disrespect",)),
    (121, ("disrespect",)),
    (127, ("disrespect",)),
    (148, ("disrespect", "judgment")),
    (169, ("disrespect", "judgment", "persistence")),
    (189, ("repetition", "dismissive")),
    (190, ("repetition", "dismissive")),
    (251, ("disrespect", "judgment")),
    (268, ("disrespect", "judgment", "persistence")),
    (269, ("disrespect", "judgment")),
    (298, ("judgment",)),
    (313, ("repetition", "disrespect")),
    (315, ("disrespect", "judgment")),
    (319, ("repetition", "disrespect")),
    (394, ("boundary", "disrespect")),
    (396, ("judgment",)),
    (397, ("judgment",)),
    (414, ("boundary", "judgment")),
    (418, ("boundary", "disrespect")),
    (432, ("dismissive", "judgment")),
]

# NUCLEAR — outrageous / screenshot energy (🥚, 🔴🔥 peaks, jet-ski arc, etc.)
_NUCLEAR_REFS: List[Ref] = [
    (19, ("disrespect", "judgment")),
    (17, ("disrespect", "cold")),
    (80, ("judgment",)),
    (266, ("disrespect", "boundary")),
    (317, ("disrespect", "judgment")),
    (445, ("disrespect", "judgment")),
    (471, ("judgment", "persistence")),
    (490, ("boundary", "judgment")),
    (534, ("boundary", "disrespect")),
    (536, ("boundary", "disrespect")),
    (639, ("disrespect", "boundary")),
    (640, ("judgment",)),
    (653, ("disrespect", "boundary", "judgment")),
    (672, ("dismissive", "judgment")),
    (688, ("dismissive", "judgment")),
    (734, ("boundary", "disrespect")),
    (378, ("disrespect", "judgment")),
    (792, ("cold", "judgment")),
    (447, ("dismissive", "judgment")),
]

FINISHER_BANK: Dict[str, List[RawEntry]] = {
    "common": _tier_from_refs(_COMMON_REFS),
    "signature": _tier_from_refs(_SIGNATURE_REFS),
    "nuclear": _tier_from_refs(_NUCLEAR_REFS),
}

# Shutdown-specific lines (also from quarks only)
FINISHER_EXTRAS: Dict[str, Dict[str, List[RawEntry]]] = {
    "repetition_shutdown": {
        "common": _tier_from_refs(
            [
                (185, ("repetition",)),
                (187, ("repetition",)),
                (336, ("repetition", "final")),
                (104, ("repetition", "boundary")),
            ]
        ),
        "signature": _tier_from_refs([(189, ("repetition", "dismissive")), (190, ("repetition", "dismissive"))]),
        "nuclear": _tier_from_refs([(376, ("repetition",)), (373, ("repetition",))]),
    },
    "followup_murder_shutdown": {
        "common": _tier_from_refs(
            [
                (350, ("followup",)),
                (351, ("followup",)),
                (353, ("followup", "persistence")),
                (354, ("followup",)),
            ]
        ),
        "signature": _tier_from_refs(
            [
                (268, ("followup", "disrespect", "judgment")),
                (371, ("followup",)),
                (367, ("followup",)),
            ]
        ),
        "nuclear": _tier_from_refs([(266, ("followup", "disrespect", "boundary")), (536, ("followup", "boundary"))]),
    },
    # Curated only — merged with full FINISHER_BANK these picked unrelated nuclear lines.
    "action_shutdown": {
        "common": _tier_from_refs(
            [
                (76, ("boundary",)),
                (77, ("boundary",)),
                (78, ("boundary", "dismissive")),
                (101, ("boundary",)),
                (104, ("boundary", "repetition")),
                (163, ("dismissive",)),
                (164, ("dismissive",)),
                (167, ("boundary", "cold")),
                (168, ("boundary",)),
                (169, ("boundary", "dismissive")),
                (596, ("dismissive", "repetition")),
                (750, ("dismissive", "cold")),
                (789, ("dismissive",)),
                (807, ("dismissive",)),
                (810, ("boundary", "dismissive")),
                (811, ("boundary",)),
            ]
        ),
        "signature": _tier_from_refs(
            [
                (81, ("boundary", "disrespect")),
                (82, ("boundary", "disrespect")),
                (394, ("boundary", "disrespect")),
                (189, ("dismissive", "repetition")),
                (190, ("dismissive", "repetition")),
                (104, ("boundary", "repetition")),
            ]
        ),
        "nuclear": _tier_from_refs(
            [
                (336, ("repetition", "final")),
                (337, ("repetition", "final")),
                (583, ("dismissive", "final")),
                (314, ("final", "cold")),
                (753, ("boundary", "dismissive")),
            ]
        ),
    },
    "action_shutdown_benign": {
        "common": _tier_from_refs(
            [
                (76, ("boundary",)),
                (77, ("boundary",)),
                (78, ("boundary", "dismissive")),
                (163, ("dismissive",)),
                (164, ("dismissive",)),
                (261, ("dismissive", "awkward")),
                (262, ("dismissive", "awkward")),
                (330, ("dismissive", "awkward")),
                (331, ("dismissive", "awkward")),
                (333, ("dismissive", "cold")),
                (596, ("dismissive", "repetition")),
                (750, ("dismissive", "cold")),
                (807, ("dismissive",)),
                (810, ("boundary", "dismissive")),
                (811, ("boundary",)),
            ]
        ),
        "signature": _tier_from_refs(
            [
                (189, ("dismissive", "repetition")),
                (190, ("dismissive", "repetition")),
                (596, ("dismissive", "repetition")),
                (104, ("boundary", "repetition")),
            ]
        ),
        "nuclear": [],
    },
    # Repeated Smile shutdown: awkward / discomfort / weirdness (curated; no harsh name/judgment lines).
    "action_shutdown_smile": {
        "common": _tier_from_refs(
            [
                (261, ("dismissive", "awkward")),
                (262, ("dismissive", "awkward")),
                (330, ("dismissive", "awkward")),
                (331, ("dismissive", "awkward")),
                (76, ("boundary", "awkward")),
                (77, ("boundary", "awkward")),
                (78, ("boundary", "dismissive")),
                (163, ("dismissive",)),
                (164, ("dismissive",)),
                (596, ("dismissive", "repetition")),
            ]
        ),
        "signature": _tier_from_refs(
            [
                (261, ("dismissive", "awkward")),
                (262, ("dismissive", "awkward")),
                (330, ("dismissive", "awkward")),
                (331, ("dismissive", "awkward")),
                (596, ("dismissive", "repetition")),
                (189, ("dismissive", "awkward")),
                (190, ("dismissive", "awkward")),
            ]
        ),
        "nuclear": [],
    },
    "verbal_boundary_shutdown": {
        "common": _tier_from_refs([(208, ("boundary", "dismissive")), (209, ("boundary", "dismissive")), (550, ("boundary",)), (791, ("boundary", "cold"))]),
        "signature": _tier_from_refs([(551, ("boundary", "disrespect")), (812, ("boundary", "disrespect"))]),
        "nuclear": _tier_from_refs([(490, ("boundary", "judgment")), (753, ("boundary", "dismissive"))]),
    },
}


@dataclass
class FinisherEntry:
    text: str
    tags: Tuple[str, ...] = ()
    variants: Tuple[str, ...] = ()
    prefixes: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_PREFIXES)

    def bodies(self) -> List[str]:
        return [self.text] + list(self.variants)

    def streak_keys(self) -> List[str]:
        return [b.strip().lower() for b in self.bodies() if b.strip()]

    def pick_spoken(self) -> Tuple[str, str]:
        """(full line with optional prefix, canonical key for streak — body only, lower)."""
        body = random.choice(self.bodies())
        prefs = self.prefixes if self.prefixes else DEFAULT_PREFIXES
        pref = random.choice(prefs)
        return pref + body, body.strip().lower()


def _coerce_entry(raw: RawEntry) -> FinisherEntry:
    if isinstance(raw, str):
        return FinisherEntry(text=raw)
    d = raw
    tags = tuple(d.get("tags") or ())
    variants = tuple(d.get("variants") or ())
    prefs = d.get("prefixes", None)
    if prefs is None:
        pr = DEFAULT_PREFIXES
    else:
        pr = tuple(prefs) if prefs else DEFAULT_PREFIXES
    return FinisherEntry(text=str(d["text"]), tags=tags, variants=variants, prefixes=pr)


def _entries_for_tier(shutdown_kind: str, tier: FinisherTier) -> List[FinisherEntry]:
    if shutdown_kind in _SHUTDOWN_KINDS_ACTION_POOL_ONLY:
        rows = FINISHER_EXTRAS.get(shutdown_kind, {}).get(tier, [])
        return [_coerce_entry(r) for r in rows]
    out: List[FinisherEntry] = [_coerce_entry(r) for r in FINISHER_BANK.get(tier, [])]
    if shutdown_kind in FINISHER_EXTRAS:
        for r in FINISHER_EXTRAS[shutdown_kind].get(tier, []):
            out.append(_coerce_entry(r))
    return out


def _score_entry(
    entry: FinisherEntry,
    profile: Mapping[str, Any],
    shutdown_kind: str,
    archetype_tag_weights: Optional[Mapping[str, float]] = None,
) -> float:
    s = 1.0
    tags = set(entry.tags)
    rpc = int(profile.get("repeated_same_prompt_count", 0))
    esc = int(profile.get("escalation_score", 0))

    if shutdown_kind == "repetition_shutdown" and "repetition" in tags:
        s += 5.0
    elif rpc >= 5 and "repetition" in tags:
        s += 4.0
    elif rpc >= 3 and "repetition" in tags:
        s += 2.5
    elif rpc >= 2 and "repetition" in tags:
        s += 1.2

    if profile.get("user_persistence_after_pushback") and "persistence" in tags:
        s += 2.2

    if profile.get("disrespect_flag") and "disrespect" in tags:
        s += 2.8

    if profile.get("confusion_loop_flag") and "dismissive" in tags:
        s += 2.0

    if esc >= 14 and ("cold" in tags or "judgment" in tags):
        s += 2.5
    elif esc >= 8 and ("cold" in tags or "judgment" in tags):
        s += 1.4

    if shutdown_kind == "action_shutdown" and "boundary" in tags:
        s += 1.8
    if shutdown_kind == "action_shutdown_benign" and "boundary" in tags:
        s += 2.0
    if shutdown_kind == "action_shutdown_benign" and ("dismissive" in tags or "awkward" in tags):
        s += 1.3
    if shutdown_kind == "action_shutdown_smile" and ("awkward" in tags or "repetition" in tags):
        s += 2.2
    if shutdown_kind == "action_shutdown_smile" and "boundary" in tags:
        s += 1.4
    if shutdown_kind == "verbal_boundary_shutdown" and "boundary" in tags:
        s += 2.2
    if shutdown_kind == "followup_murder_shutdown" and "followup" in tags:
        s += 2.5

    atw = archetype_tag_weights or {}
    for tnm, w in atw.items():
        if tnm in tags:
            s += float(w)

    return s


def _matched_tags(entry: FinisherEntry, profile: Mapping[str, Any], shutdown_kind: str) -> List[str]:
    hit: List[str] = []
    tags = set(entry.tags)
    rpc = int(profile.get("repeated_same_prompt_count", 0))
    if "repetition" in tags and (shutdown_kind == "repetition_shutdown" or rpc >= 2):
        hit.append("repetition")
    if "persistence" in tags and profile.get("user_persistence_after_pushback"):
        hit.append("persistence")
    if "disrespect" in tags and profile.get("disrespect_flag"):
        hit.append("disrespect")
    if "dismissive" in tags and profile.get("confusion_loop_flag"):
        hit.append("dismissive")
    if ("cold" in tags or "judgment" in tags) and int(profile.get("escalation_score", 0)) >= 8:
        hit.append("escalation")
    if "boundary" in tags and shutdown_kind in (
        "action_shutdown",
        "action_shutdown_benign",
        "action_shutdown_smile",
        "verbal_boundary_shutdown",
    ):
        hit.append("boundary")
    if "followup" in tags and shutdown_kind == "followup_murder_shutdown":
        hit.append("followup")
    return hit


def _avoid_recent(entries: Sequence[FinisherEntry], recent: set[str]) -> List[FinisherEntry]:
    fresh = [e for e in entries if not any(k in recent for k in e.streak_keys())]
    return fresh if fresh else list(entries)


def _fallback_line() -> Tuple[str, str]:
    text = _extract_dialogue_from_raw_quarks_line(_quarks_lines()[_FALLBACK_LINE_NUMBER - 1])
    return text, text.strip().lower()


def pick_finisher_line(
    shutdown_kind: str = "generic_shutdown",
    interaction_profile: Optional[Dict[str, Any]] = None,
    recent_finishers: Optional[Sequence[str]] = None,
    *,
    archetype_tier_bias: Optional[Tuple[int, int, int]] = None,
    archetype_tag_weights: Optional[Mapping[str, float]] = None,
) -> Tuple[str, FinisherTier, Dict[str, Any]]:
    """
    Returns (spoken_line, tier, meta).

    meta: canonical_text, matched_tags, context_influenced, selected_tags, shutdown_kind
    """
    profile: Dict[str, Any] = dict(interaction_profile or {})
    recent = {x.strip().lower() for x in (recent_finishers or []) if x}

    def get_pool(tier: FinisherTier) -> List[FinisherEntry]:
        if shutdown_kind in FINISHER_EXTRAS:
            return _entries_for_tier(shutdown_kind, tier)
        return [_coerce_entry(r) for r in FINISHER_BANK.get(tier, [])]

    avail_tiers: List[FinisherTier] = []
    wts: List[float] = []
    bias = archetype_tier_bias or (0, 0, 0)
    for ti, t in enumerate(_TIER_ORDER):
        p = get_pool(t)
        if p:
            avail_tiers.append(t)
            wts.append(max(1.0, float(_WEIGHTS[ti]) + float(bias[ti])))
    if not avail_tiers:
        spoken, canon = _fallback_line()
        return spoken, "common", {
            "canonical_text": canon,
            "matched_tags": [],
            "context_influenced": False,
            "selected_tags": [],
            "shutdown_kind": shutdown_kind,
        }

    tier = random.choices(avail_tiers, weights=wts, k=1)[0]
    entries = get_pool(tier)
    entries = _avoid_recent(entries, recent)

    scored = [
        (e, _score_entry(e, profile, shutdown_kind, archetype_tag_weights=archetype_tag_weights))
        for e in entries
    ]
    max_s = max(s for _, s in scored)
    min_s = min(s for _, s in scored)
    context_influenced = max_s > min_s + 0.01 or max_s >= 2.0

    weights = [max(0.2, s) for _, s in scored]
    pick_i = random.choices(range(len(scored)), weights=weights, k=1)[0]
    chosen, ch_score = scored[pick_i]

    spoken, canon = chosen.pick_spoken()
    matched = _matched_tags(chosen, profile, shutdown_kind)
    meta = {
        "canonical_text": canon,
        "matched_tags": matched,
        "context_influenced": context_influenced or ch_score >= 2.0 or bool(matched),
        "selected_tags": list(chosen.tags),
        "shutdown_kind": shutdown_kind,
        "score": ch_score,
        "archetype_tier_bias": list(bias) if any(bias) else None,
        "archetype_tag_weights": dict(archetype_tag_weights) if archetype_tag_weights else None,
    }
    return spoken, tier, meta


def apply_finisher_debug_to_session(
    session: object,
    text: str,
    tier: FinisherTier,
    shutdown_kind: str,
    *,
    murdered_override: bool = True,
    pick_meta: Optional[Dict[str, Any]] = None,
    interaction_profile_snapshot: Optional[Dict[str, Any]] = None,
) -> None:
    """Streamlit session_state dict-like."""
    base = {
        "finisher_text": text,
        "finisher_tier": tier,
        "murdered_override": murdered_override,
        "shutdown_kind": shutdown_kind,
    }
    pm = pick_meta or {}
    base["matched_tags"] = pm.get("matched_tags", [])
    base["context_influenced"] = bool(pm.get("context_influenced", False))
    base["selected_tags"] = pm.get("selected_tags", [])
    base["interaction_profile"] = interaction_profile_snapshot or {}
    base["archetype_id"] = pm.get("archetype_id")
    base["archetype_finisher_bias"] = pm.get("archetype_finisher_bias")
    base["trajectory_id"] = pm.get("trajectory_id")
    base["trajectory_finisher_bias"] = pm.get("trajectory_finisher_bias")
    session[FINISHER_SESSION_DEBUG_KEY] = base


def verify_all_finishers_in_quarks() -> None:
    """Assert every finisher body is a substring of quarks.txt (dev check)."""
    blob = _QUARKS_PATH.read_text(encoding="utf-8")

    def check(raw: RawEntry) -> None:
        if isinstance(raw, str):
            t = raw
        else:
            t = str(raw["text"])
        assert t in blob, f"Missing from quarks.txt: {t!r}"

    for tier in _TIER_ORDER:
        for r in FINISHER_BANK.get(tier, []):
            check(r)
    for _sk, tiers in FINISHER_EXTRAS.items():
        for _t, lst in tiers.items():
            for r in lst:
                check(r)


if __name__ == "__main__":
    verify_all_finishers_in_quarks()
    print("verify_all_finishers_in_quarks: OK")
