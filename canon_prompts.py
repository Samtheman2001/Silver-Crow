"""
Word of God: canonical dropdown/menu prompt response banks.

These are the first-class, authored answers for concrete menu prompts.
Routing: if a canonical bank exists for the prompt, we answer from it first.

Authored banks: `silvercrow.quarks_canon_prompts.CANON_PROMPTS` (from quarks.txt) override
`SAY_OPTIONS` `responses` tables for the same normalized prompt key.

Line tiers (quarks metadata): common / signature / nuclear — weighted at selection time.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import re
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Union

from .config import SAY_OPTIONS
from .quarks_canon_prompts import CANON_PROMPTS as _QUARKS_CANON_PROMPTS

Bucket = Literal["positive", "neutral", "negative", "severe"]
LineTier = Literal["common", "signature", "nuclear"]

_VALID_TIERS = frozenset({"common", "signature", "nuclear"})

# Default tier weights (common, signature, nuclear) by bucket kind
_WEIGHTS_NON_SEVERE: Tuple[int, int, int] = (70, 25, 5)
_WEIGHTS_SEVERE: Tuple[int, int, int] = (55, 35, 10)
# Naturally confrontational menu prompts: more signature/nuclear
_WEIGHTS_AGGR_NON_SEVERE: Tuple[int, int, int] = (55, 32, 13)
_WEIGHTS_AGGR_SEVERE: Tuple[int, int, int] = (40, 40, 20)


def normalize_prompt_key(text: str) -> str:
    """
    Normalize prompt keys to avoid fragile exact-text mismatches.
    """
    t = (text or "").strip().lower()
    t = t.replace("’", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[!?\.]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^hello,?\s+", "", t)
    t = re.sub(r"\bjet\s+ski\b", "jetski", t)
    return t


def is_high_aggression_menu_prompt(normalized_prompt_key: str) -> bool:
    """
    Prompts where a hostile or meme-forward frame should surface signature/nuclear more often.
    Keys are compared after normalize_prompt_key.
    """
    return normalized_prompt_key in _HIGH_AGGRESSION_NORM_KEYS


_HIGH_AGGRESSION_NORM_KEYS: frozenset[str] = frozenset(
    {
        normalize_prompt_key("Cash me outside, how ’bout that?"),
        normalize_prompt_key("Cash me outside, how 'bout that?"),
        normalize_prompt_key("What gives you the right?"),
        normalize_prompt_key("Do you think you're better than me?"),
    }
)


def resolve_response_bucket(state: Mapping[str, Any]) -> Bucket:
    """
    Deterministic mapping from current emotional state -> response bucket.
    Keep simple/transparent; tweak here, not scattered across callers.
    """
    anger = int(state.get("anger", 0) or 0)
    trust = int(state.get("trust", 0) or 0)
    stress = int(state.get("stress", 0) or 0)
    happiness = int(state.get("happiness", 0) or 0)

    # Severe: snapped / done
    if anger >= 78 or stress >= 86 or trust <= 14:
        return "severe"

    # Negative: skeptical / tense
    if anger >= 55 or stress >= 62 or trust <= 28:
        return "negative"

    # Positive: warm / open
    if happiness >= 62 and trust >= 44 and anger <= 40 and stress <= 55:
        return "positive"

    return "neutral"


@dataclass(frozen=True)
class CanonLine:
    text: str
    tier: LineTier = "common"


@dataclass(frozen=True)
class CanonBank:
    prompt: str
    buckets: Dict[Bucket, List[CanonLine]]


def _normalize_tier(raw: object) -> LineTier:
    if raw in _VALID_TIERS:
        return raw  # type: ignore[return-value]
    return "common"


def _parse_quarks_item(item: Union[str, Mapping[str, Any]]) -> Optional[CanonLine]:
    if isinstance(item, dict):
        text = str(item.get("text", "")).strip()
        if not text:
            return None
        tier = item.get("tier")
        if tier not in _VALID_TIERS and item.get("rare") is True:
            tier = "signature"
        return CanonLine(text=text, tier=_normalize_tier(tier))
    s = str(item).strip()
    if not s:
        return None
    return CanonLine(text=s, tier="common")


def _tier_weights_for(bucket: Bucket, prompt_norm: str) -> Tuple[int, int, int]:
    severe = bucket == "severe"
    aggr = is_high_aggression_menu_prompt(prompt_norm)
    if aggr:
        return _WEIGHTS_AGGR_SEVERE if severe else _WEIGHTS_AGGR_NON_SEVERE
    return _WEIGHTS_SEVERE if severe else _WEIGHTS_NON_SEVERE


def _apply_tier_weight_bonus(
    base: Tuple[int, int, int],
    bonus: Optional[Tuple[int, int, int]],
) -> Tuple[int, int, int]:
    if not bonus:
        return base
    bc, bs, bn = base
    ec, es, en = bonus
    return (max(1, bc + ec), max(1, bs + es), max(1, bn + en))


def _weighted_pick_from_lines(
    lines: List[CanonLine],
    bucket: Bucket,
    prompt_norm: str,
    *,
    tier_weight_bonus: Optional[Tuple[int, int, int]] = None,
) -> Optional[str]:
    if not lines:
        return None
    tiers_order: Tuple[LineTier, LineTier, LineTier] = ("common", "signature", "nuclear")
    by_tier: Dict[LineTier, List[CanonLine]] = {t: [] for t in tiers_order}
    for ln in lines:
        t = ln.tier if ln.tier in _VALID_TIERS else "common"
        by_tier[t].append(ln)
    w_common, w_sig, w_nuc = _apply_tier_weight_bonus(
        _tier_weights_for(bucket, prompt_norm),
        tier_weight_bonus,
    )
    avail: List[LineTier] = []
    weights: List[float] = []
    for t, w in zip(tiers_order, (w_common, w_sig, w_nuc)):
        if by_tier[t]:
            avail.append(t)
            weights.append(float(w))
    if not avail:
        return None
    chosen_tier = random.choices(avail, weights=weights, k=1)[0]
    return random.choice(by_tier[chosen_tier]).text


def _extract_banks_from_quarks() -> Dict[str, CanonBank]:
    out: Dict[str, CanonBank] = {}
    for prompt, bank in (_QUARKS_CANON_PROMPTS or {}).items():
        if not isinstance(bank, dict):
            continue
        buckets: Dict[Bucket, List[CanonLine]] = {
            "positive": [],
            "neutral": [],
            "negative": [],
            "severe": [],
        }
        for bk in buckets:
            raw = bank.get(bk) or []
            if not isinstance(raw, list):
                continue
            parsed: List[CanonLine] = []
            for x in raw:
                pl = _parse_quarks_item(x)
                if pl:
                    parsed.append(pl)
            buckets[bk] = parsed
        nb = normalize_prompt_key(str(prompt))
        out[nb] = CanonBank(prompt=str(prompt), buckets=buckets)
    return out


def _extract_banks_from_say_options() -> Dict[str, CanonBank]:
    out: Dict[str, CanonBank] = {}
    for prompt, option in (SAY_OPTIONS or {}).items():
        if not isinstance(option, dict):
            continue
        responses = option.get("responses")
        if not isinstance(responses, dict):
            continue
        buckets: Dict[Bucket, List[CanonLine]] = {
            "positive": [],
            "neutral": [],
            "negative": [],
            "severe": [],
        }
        for k in buckets:
            raw = responses.get(k) or []
            buckets[k] = [
                CanonLine(text=str(x).strip(), tier="common")
                for x in raw
                if str(x).strip()
            ]
        nb = normalize_prompt_key(prompt)
        out[nb] = CanonBank(prompt=prompt, buckets=buckets)
    return out


# Canonical prompt banks keyed by normalized prompt (quarks banks win on overlap).
_AUTHORED_FROM_SAY = _extract_banks_from_say_options()
_AUTHORED_FROM_QUARKS = _extract_banks_from_quarks()
AUTHORED_PROMPT_BANKS: Dict[str, CanonBank] = {**_AUTHORED_FROM_SAY, **_AUTHORED_FROM_QUARKS}


def has_canon_bank(prompt: str) -> bool:
    return normalize_prompt_key(prompt) in AUTHORED_PROMPT_BANKS


def get_authored_prompt_bank(prompt: str) -> Optional[CanonBank]:
    return AUTHORED_PROMPT_BANKS.get(normalize_prompt_key(prompt))


def get_canonical_menu_response(
    prompt: str,
    *,
    state: Mapping[str, Any],
    bucket: Optional[str] = None,
    tier_weight_bonus: Optional[Tuple[int, int, int]] = None,
) -> Optional[str]:
    """
    Return one canonical authored line for this prompt and bucket (tier-weighted random).
    """
    prompt_norm = normalize_prompt_key(prompt)
    bank = get_authored_prompt_bank(prompt)
    if not bank:
        return None
    b: Bucket
    if bucket in ("positive", "neutral", "negative", "severe"):
        b = bucket  # type: ignore[assignment]
    else:
        b = resolve_response_bucket(state)
    lines = list(bank.buckets.get(b) or [])
    if lines:
        return _weighted_pick_from_lines(lines, b, prompt_norm, tier_weight_bonus=tier_weight_bonus)
    # fall back to nearest buckets without inventing new text
    for fb in ("neutral", "negative", "positive", "severe"):
        cand = list(bank.buckets.get(fb) or [])
        if cand:
            return _weighted_pick_from_lines(
                cand, fb, prompt_norm, tier_weight_bonus=tier_weight_bonus
            )  # type: ignore[arg-type]
    return None
