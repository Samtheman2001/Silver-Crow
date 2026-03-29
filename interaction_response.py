# -*- coding: utf-8 -*-
"""
Single entry point for interaction replies: one immutable Response, no post-hoc mutation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Any, Dict, Literal, Mapping, Optional, Tuple

import streamlit as st

from action_quarks import try_pick_authored_action_response
from action_social_layer import maybe_social_verbal_for_do_action, minimal_verbal_ack_for_do_action
from action_vm_quarks import authored_action_vm_pair
from brain import crow_brain_interpret, infer_physical_response, infer_tone, infer_vibe
from do_reactions import action_reaction
from finishers import finisher_shutdown_kind_for_do_action
from first_impression import first_impression_verbal_locked
from responses import demo_safe_dropdown_say_relationship, fill_name_tokens, relationship_status
from say_first_hit_overrides import get_say_first_hit_override
from say_murder_routing import (
    demo_dropdown_vm_inner_line,
    dropdown_say_candidate_bases_for_repeat,
    pick_say_repeat_warning_line,
    pick_say_repetition_murder_line,
    resolve_say_vm_physical,
)
from say_pipeline import compose_say_response
from session_finisher import finisher_pick_weighted
from tone_vibe_map import resolve_tone_and_vibe
from utils import quote, sanitize_live_verbal_inner, strip_outer_quotes, verbal_triggers_conversation_shutdown

SourceKind = Literal["authored", "engine"]

# Last menu SAY inner (normalized) per prompt — avoids reusing the same line on consecutive turns.
DEMO_LAST_MENU_SAY_INNER_KEY = "_demo_last_menu_say_inner_norm_by_prompt"
# Per prompt, normalized inner lines already shown this run (dropdown SAY demo); reset when a tier is exhausted.
DEMO_USED_SAY_LINES_KEY = "DEMO_USED_SAY_LINES"
# Last repeat-ack line used per prompt (no same line twice in a row for that pool).
DEMO_LAST_ACK_TEMPLATE_KEY = "_demo_last_ack_template_by_prompt"

QUESTION_REPEAT_LINES = (
    "Didn't you just ask me that?",
    "You just asked that.",
    "Why are you asking that again?",
)

STATEMENT_REPEAT_LINES = (
    "You just said that.",
    "You're repeating yourself.",
    "You already said that.",
)

_STATS_KEYS = ("happiness", "trust", "anger", "stress", "interest")


def _stats_delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> Dict[str, int]:
    return {k: int(after[k]) - int(before[k]) for k in _STATS_KEYS}


def _ensure_non_empty_verbal(verbal: str, fallback: str = "I'm listening.") -> str:
    if strip_outer_quotes(verbal or "").strip():
        return verbal
    return quote(fallback)


def _norm_demo_menu_line(verbal_quoted: str) -> str:
    return strip_outer_quotes(verbal_quoted or "").strip().lower()


def _register_demo_menu_say_line(prompt: str, verbal_quoted: str) -> None:
    n = _norm_demo_menu_line(verbal_quoted)
    d_last = dict(st.session_state.get(DEMO_LAST_MENU_SAY_INNER_KEY) or {})
    d_last[str(prompt)] = n
    st.session_state[DEMO_LAST_MENU_SAY_INNER_KEY] = d_last
    d_used = dict(st.session_state.get(DEMO_USED_SAY_LINES_KEY) or {})
    key = str(prompt)
    s = set(d_used.get(key) or [])
    s.add(n)
    d_used[key] = s
    st.session_state[DEMO_USED_SAY_LINES_KEY] = d_used


def _display_norm_from_filled_raw(raw: str) -> str:
    return _norm_demo_menu_line(quote(raw))


def _pick_repeat_ack_line_only(prompt: str) -> str:
    """repeat_count == 1: one acknowledgement line only (question vs statement); no authored mash."""
    is_question = str(prompt).strip().endswith("?")
    pool = list(QUESTION_REPEAT_LINES if is_question else STATEMENT_REPEAT_LINES)
    d = dict(st.session_state.get(DEMO_LAST_ACK_TEMPLATE_KEY) or {})
    p = str(prompt)
    last_line = d.get(p)
    choices = [x for x in pool if x != last_line]
    if not choices:
        choices = pool[:]
    line = random.choice(choices)
    d[p] = line
    st.session_state[DEMO_LAST_ACK_TEMPLATE_KEY] = dict(d)
    return line


def _pick_dropdown_say_first_use_raw(prompt: str, cname: str) -> str:
    """repeat_count == 0 only: authored positive/neutral; no repeat acknowledgement."""
    bases = dropdown_say_candidate_bases_for_repeat(prompt, 0)
    if not bases:
        return ""
    d_used = dict(st.session_state.get(DEMO_USED_SAY_LINES_KEY) or {})
    used: set[str] = set(d_used.get(str(prompt)) or [])
    prev = (st.session_state.get(DEMO_LAST_MENU_SAY_INNER_KEY) or {}).get(str(prompt)) or ""
    prev = (prev or "").strip().lower()

    def finalize_first(b: str) -> str:
        return sanitize_live_verbal_inner(fill_name_tokens(b), character_name=cname)

    def pick_with(used_set: set[str]) -> Optional[str]:
        for b in bases:
            raw = finalize_first(b)
            dn = _display_norm_from_filled_raw(raw)
            if not dn:
                continue
            if dn in used_set or dn == prev:
                continue
            return raw
        return None

    picked_raw = pick_with(used)
    if picked_raw is None:
        d_used[str(prompt)] = set()
        st.session_state[DEMO_USED_SAY_LINES_KEY] = dict(d_used)
        picked_raw = pick_with(set())
    if picked_raw is None:
        for b in bases:
            raw = finalize_first(b)
            dn = _display_norm_from_filled_raw(raw)
            if dn and dn != prev:
                return raw
        return finalize_first(bases[0])
    return picked_raw


def _pick_escalation_line_only(prompt: str, rc: int, cname: str) -> str:
    """repeat_count >= 2: single authored escalation line only — never prepend repeat ack."""
    bases = dropdown_say_candidate_bases_for_repeat(prompt, rc)
    if not bases:
        return random.choice(list(STATEMENT_REPEAT_LINES))
    d_used = dict(st.session_state.get(DEMO_USED_SAY_LINES_KEY) or {})
    used: set[str] = set(d_used.get(str(prompt)) or [])
    prev = (st.session_state.get(DEMO_LAST_MENU_SAY_INNER_KEY) or {}).get(str(prompt)) or ""
    prev = (prev or "").strip().lower()

    def finalize_esc(b: str) -> str:
        return sanitize_live_verbal_inner(fill_name_tokens(b), character_name=cname)

    def pick_with(used_set: set[str]) -> Optional[str]:
        for b in bases:
            raw = finalize_esc(b)
            dn = _display_norm_from_filled_raw(raw)
            if not dn:
                continue
            if dn in used_set or dn == prev:
                continue
            return raw
        return None

    picked_raw = pick_with(used)
    if picked_raw is None:
        d_used[str(prompt)] = set()
        st.session_state[DEMO_USED_SAY_LINES_KEY] = dict(d_used)
        picked_raw = pick_with(set())
    if picked_raw is None:
        for b in bases:
            raw = finalize_esc(b)
            dn = _display_norm_from_filled_raw(raw)
            if dn and dn != prev:
                return raw
        return finalize_esc(bases[0])
    return picked_raw


def _dropdown_say_demo_safe_build(ctx: ResponseContext, delta: Dict[str, int], stt: Mapping[str, Any]) -> Response:
    """
    Menu SAY only: deterministic authored lines, fixed tone/vibe/physical by repeat step,
    no compose_say_response / crow_brain / callback pools / trajectory flavor on output.
    """
    polite_openers = {
        "Hello, nice to meet you.",
        "Nice to meet you",
        "Hey, how are you?",
        "What's up?",
    }
    rel = demo_safe_dropdown_say_relationship(stt, ctx.turns_before_reply)
    cname = str(ctx.character_name or "").strip()

    first_polite_menu_use = (
        ctx.prompt in polite_openers
        and int(ctx.turns_before_reply) == 0
        and int(ctx.repeat_count) == 0
    )
    if first_polite_menu_use:
        if ctx.prompt in {"Hello, nice to meet you.", "Nice to meet you"}:
            verbal = quote("Nice to meet you.")
        elif ctx.prompt == "Hey, how are you?":
            verbal = quote("I'm alright.")
        else:
            verbal = quote("Nothing really.")
        tone, vibe, physical = "curious", "chill", "looks relaxed"
        if verbal_triggers_conversation_shutdown(verbal):
            ft, tier, meta = finisher_pick_weighted("verbal_boundary_shutdown", str(ctx.prompt or ""))
            meta_d = dict(meta)
            return Response(
                verbal=quote(ft),
                physical=physical,
                tone="hostile",
                vibe="done",
                relationship=rel,
                stats_delta=delta,
                ended=True,
                source="engine",
                shutdown_kind="verbal_boundary_shutdown",
                finisher_tier=tier,
                finisher_meta=meta_d,
                precomputed_finisher=(ft, tier, meta_d),
                apply_murdered_state=False,
                ending_message="CONVERSATION ENDED",
            )
        verbal = _ensure_non_empty_verbal(verbal)
        resp = Response(
            verbal=verbal,
            physical=physical,
            tone=tone,
            vibe=vibe,
            relationship=rel,
            stats_delta=delta,
            ended=False,
            source="engine",
        )
        _register_demo_menu_say_line(ctx.prompt, resp.verbal)
        return resp

    rc = int(ctx.repeat_count)
    first_hit = None
    if rc <= 0:
        first_hit = get_say_first_hit_override(ctx.prompt)
        raw = _pick_dropdown_say_first_use_raw(ctx.prompt, cname)
        if first_hit is not None and first_hit.verbal_inner is not None:
            raw = sanitize_live_verbal_inner(
                fill_name_tokens(first_hit.verbal_inner), character_name=cname
            )
    elif rc == 1:
        raw = _pick_repeat_ack_line_only(ctx.prompt)
    else:
        raw = _pick_escalation_line_only(ctx.prompt, rc, cname)
    if not (raw or "").strip():
        raw = "Alright." if rc <= 0 else random.choice(list(STATEMENT_REPEAT_LINES))
    verbal = quote(raw)

    if rc <= 0:
        tone, vibe, physical = "curious", "chill", "looks relaxed"
        if first_hit is not None and first_hit.physical is not None:
            physical = first_hit.physical
    elif rc == 1:
        tone, vibe, physical = "confused", "interesting", "looks a little confused"
    elif rc == 2:
        tone, vibe, physical = "tense", "not chill", "looks irritated"
    elif rc == 3:
        tone, vibe, physical = "mad", "zero chill", "looks openly annoyed"
    else:
        tone, vibe, physical = "angry", "garbage", "looks like they are done with this"

    if verbal_triggers_conversation_shutdown(verbal):
        ft, tier, meta = finisher_pick_weighted("verbal_boundary_shutdown", str(ctx.prompt or ""))
        meta_d = dict(meta)
        return Response(
            verbal=quote(ft),
            physical=physical,
            tone="hostile",
            vibe="done",
            relationship=rel,
            stats_delta=delta,
            ended=True,
            source="engine",
            shutdown_kind="verbal_boundary_shutdown",
            finisher_tier=tier,
            finisher_meta=meta_d,
            precomputed_finisher=(ft, tier, meta_d),
            apply_murdered_state=False,
            ending_message="CONVERSATION ENDED",
        )

    verbal = _ensure_non_empty_verbal(verbal)
    resp = Response(
        verbal=verbal,
        physical=physical,
        tone=tone,
        vibe=vibe,
        relationship=rel,
        stats_delta=delta,
        ended=False,
        source="authored",
    )
    _register_demo_menu_say_line(ctx.prompt, resp.verbal)
    return resp


@dataclass(frozen=True)
class Response:
    verbal: str
    physical: str
    tone: str
    vibe: str
    relationship: str
    stats_delta: Dict[str, int]
    ended: bool
    source: SourceKind
    shutdown_kind: Optional[str] = None
    finisher_tier: Optional[str] = None
    finisher_meta: Optional[Dict[str, Any]] = None
    """(unquoted_line, tier, meta) when a finisher was selected inside build_response (no second pick)."""
    precomputed_finisher: Optional[Tuple[str, str, Dict[str, Any]]] = None
    special_ending: Optional[str] = None
    apply_murdered_state: bool = False
    ending_message: str = ""
    moonwalk_universe_rulerz: bool = False


@dataclass
class ResponseContext:
    kind: str  # "say" | "do"
    prompt: str
    repeat_count: int
    state: Mapping[str, Any]
    state_before_mods: Mapping[str, Any]
    personality: str
    scenario_name: str
    character_name: str
    turns_before_reply: int
    moonwalk_streak: int = 0
    is_free_text: bool = False
    free_text_category: Optional[str] = None
    murder_threshold: int = 5
    speech_echo: bool = False
    starting_mood: str = "Neutral"
    """When False, say branch skips crow_brain_interpret (caller already set session)."""
    run_crow_brain: bool = True


def _finalize_response(ctx: ResponseContext, resp: Response) -> Response:
    t, v = resolve_tone_and_vibe(
        kind=ctx.kind,
        is_free_text=ctx.is_free_text,
        free_text_category=ctx.free_text_category,
        state=ctx.state,
        verbal_quoted=resp.verbal,
        physical=resp.physical,
        prompt=ctx.prompt,
        source=resp.source,
        ended=resp.ended,
        apply_murdered_state=resp.apply_murdered_state,
        ending_message=resp.ending_message,
        special_ending=resp.special_ending,
        preliminary_tone=resp.tone,
        preliminary_vibe=resp.vibe,
    )
    return replace(resp, tone=t, vibe=v)


def _finisher_response(
    *,
    shutdown_kind: str,
    input_text: str,
    state_before: Mapping[str, Any],
    state_after: Mapping[str, Any],
    physical: str,
    tone: str,
    vibe: str,
    apply_murdered: bool,
    ending_message: str,
    source: SourceKind = "engine",
) -> Response:
    ft, tier, meta = finisher_pick_weighted(shutdown_kind, str(input_text or ""))
    rel = relationship_status(state_after, True)
    meta_d = dict(meta)
    return Response(
        verbal=quote(ft),
        physical=physical,
        tone=tone,
        vibe=vibe,
        relationship=rel,
        stats_delta=_stats_delta(state_before, state_after),
        ended=True,
        source=source,
        shutdown_kind=shutdown_kind,
        finisher_tier=tier,
        finisher_meta=meta_d,
        precomputed_finisher=(ft, tier, meta_d),
        apply_murdered_state=apply_murdered,
        ending_message=ending_message,
    )


def build_response(ctx: ResponseContext) -> Response:
    """
    Construct exactly one Response for this turn. No layer may rewrite fields afterward.
    """
    stt = ctx.state
    before = ctx.state_before_mods
    delta = _stats_delta(before, stt)

    if ctx.kind == "say":
        if ctx.repeat_count >= ctx.murder_threshold:
            _vm_cname = str(ctx.character_name or "").strip()
            if ctx.is_free_text:
                line_inner = pick_say_repetition_murder_line(
                    ctx.prompt,
                    is_free_text=True,
                    avoid_inner_norm=None,
                    excluded_inner_norms=frozenset(),
                    line_norm_fn=None,
                )
            else:
                line_inner = demo_dropdown_vm_inner_line(ctx.prompt)
            line_inner = fill_name_tokens(line_inner)
            line_inner = sanitize_live_verbal_inner(line_inner, character_name=_vm_cname)
            rel = relationship_status(stt, True)
            meta_d = {
                "canonical_text": line_inner.lower(),
                "shutdown_kind": "say_repetition_prompt_pool",
                "murder_prompt_key": str(ctx.prompt or ""),
                "is_free_text": bool(ctx.is_free_text),
            }
            _vm_verbal = quote(line_inner)
            if not ctx.is_free_text:
                _register_demo_menu_say_line(ctx.prompt, _vm_verbal)
            _vm_phys = resolve_say_vm_physical(
                ctx.prompt,
                line_inner,
                is_free_text=ctx.is_free_text,
            )
            return _finalize_response(
                ctx,
                Response(
                    verbal=_vm_verbal,
                    physical=_vm_phys,
                    tone="furious",
                    vibe="unfathomable",
                    relationship=rel,
                    stats_delta=delta,
                    ended=True,
                    source="authored",
                    shutdown_kind="say_repetition_prompt_pool",
                    finisher_tier="prompt_severe",
                    finisher_meta=dict(meta_d),
                    precomputed_finisher=(line_inner, "prompt_severe", meta_d),
                    apply_murdered_state=True,
                    ending_message="VIBES MURDERED",
                ),
            )

        if not ctx.is_free_text:
            return _finalize_response(ctx, _dropdown_say_demo_safe_build(ctx, delta, stt))

        if ctx.run_crow_brain:
            st.session_state.crow_brain = crow_brain_interpret(
                stt,
                user_input=ctx.prompt,
                kind="say",
                free_text_category=ctx.free_text_category if ctx.is_free_text else None,
                repeat_count=ctx.repeat_count,
            )
            brain = st.session_state.get("crow_brain") or {}
            st.session_state["_fi_lock_verbal"] = first_impression_verbal_locked(
                ctx.prompt,
                ctx.turns_before_reply,
                stt,
                brain.get("attitude", "guarded"),
            )

        verbal, tone, physical, vibe = compose_say_response(
            ctx.prompt,
            "say",
            stt,
            ctx.character_name,
            ctx.scenario_name,
            ctx.personality,
            free_text_category=ctx.free_text_category,
            turns_before_reply=ctx.turns_before_reply,
            starting_mood=ctx.starting_mood,
        )

        ag_free = bool(
            ctx.is_free_text and ctx.free_text_category and str(ctx.free_text_category).startswith("aggressive_")
        )

        if ctx.is_free_text:
            if ctx.repeat_count == 1 and ctx.speech_echo:
                verbal = quote(pick_say_repeat_warning_line(ctx.prompt, 1, is_free_text=True))
                tone = infer_tone(stt)
                if tone == "warm":
                    tone = "uncertain"
                vibe = "weirdly familiar"
                physical = "gives you a look like you're looping"
            elif ctx.repeat_count == 2 and not ag_free:
                verbal = quote(pick_say_repeat_warning_line(ctx.prompt, 2, is_free_text=True))
                tone = "tense"
                vibe = "interesting"
                physical = "looks a little irritated"
            elif ctx.repeat_count >= 3 and not ag_free:
                verbal = quote(pick_say_repeat_warning_line(ctx.prompt, 3, is_free_text=True))
                tone = "hostile"
                vibe = "vibe slipping"
                physical = "looks irritated and starts pulling away"

        if verbal_triggers_conversation_shutdown(verbal):
            ft, tier, meta = finisher_pick_weighted("verbal_boundary_shutdown", str(ctx.prompt or ""))
            rel = relationship_status(stt, True)
            meta_d = dict(meta)
            return _finalize_response(
                ctx,
                Response(
                    verbal=quote(ft),
                    physical=physical,
                    tone="hostile",
                    vibe="done",
                    relationship=rel,
                    stats_delta=delta,
                    ended=True,
                    source="engine",
                    shutdown_kind="verbal_boundary_shutdown",
                    finisher_tier=tier,
                    finisher_meta=meta_d,
                    precomputed_finisher=(ft, tier, meta_d),
                    apply_murdered_state=False,
                    ending_message="CONVERSATION ENDED",
                ),
            )

        verbal = _ensure_non_empty_verbal(verbal)
        rel = relationship_status(stt, False)
        return _finalize_response(
            ctx,
            Response(
                verbal=verbal,
                physical=physical,
                tone=tone,
                vibe=vibe,
                relationship=rel,
                stats_delta=delta,
                ended=False,
                source="engine",
            ),
        )

    # --- do ---
    st.session_state.crow_brain = crow_brain_interpret(
        stt,
        user_input=ctx.prompt,
        kind="do",
        free_text_category=None,
        repeat_count=ctx.repeat_count,
    )
    brain = st.session_state.get("crow_brain") or {}

    if ctx.prompt == "Hit the moonwalk" and ctx.moonwalk_streak >= 4:
        rel = relationship_status(stt, True)
        return _finalize_response(
            ctx,
            Response(
                verbal=quote("OVERSTIMULATED"),
                physical="overstimulated",
                tone="unfathomable",
                vibe="electric",
                relationship=rel,
                stats_delta=delta,
                ended=True,
                source="authored",
                special_ending="overstimulated",
                ending_message="OVERSTIMULATED",
            ),
        )

    if ctx.prompt == "Hit the moonwalk":
        ap_mw = try_pick_authored_action_response(
            ctx.prompt,
            ctx.repeat_count,
            stt,
            before,
            ctx.moonwalk_streak,
        )
        if ap_mw is not None:
            verbal = quote(ap_mw.verbal_inner) if ap_mw.verbal_inner.strip() else ""
            tone = ap_mw.tone_override or infer_tone(stt)
            vibe = ap_mw.vibe_override or infer_vibe(stt)
            physical = ap_mw.physical if ap_mw.physical else infer_physical_response(stt)
            if not strip_outer_quotes(verbal).strip():
                verbal = _ensure_non_empty_verbal(verbal, fallback="…")
            rel = relationship_status(stt, False)
            return _finalize_response(
                ctx,
                Response(
                    verbal=verbal,
                    physical=physical,
                    tone=tone,
                    vibe=vibe,
                    relationship=rel,
                    stats_delta=delta,
                    ended=False,
                    source="authored",
                    moonwalk_universe_rulerz=bool(ap_mw.moonwalk_universe_mode),
                ),
            )

    verbal, tone, physical, vibe, ended = action_reaction(
        ctx.prompt, ctx.repeat_count, stt, ctx.personality, before_state=before
    )
    if ended:
        ap_vm = authored_action_vm_pair(ctx.prompt)
        if ap_vm is not None:
            phys_ex, verb_inner = ap_vm
            phys_ex = (phys_ex or "").strip() or (
                "body goes rigid, then they cut you off with a look — full shutdown"
            )
            rel = relationship_status(stt, True)
            meta_d = {
                "canonical_text": verb_inner.lower(),
                "shutdown_kind": "action_vm_authored",
                "authored_action": ctx.prompt,
            }
            return _finalize_response(
                ctx,
                Response(
                    verbal=quote(verb_inner),
                    physical=phys_ex,
                    tone="hostile",
                    vibe="unfathomable",
                    relationship=rel,
                    stats_delta=delta,
                    ended=True,
                    source="authored",
                    shutdown_kind="action_vm_authored",
                    finisher_tier="authored_vm",
                    finisher_meta=dict(meta_d),
                    precomputed_finisher=(verb_inner, "authored_vm", meta_d),
                    apply_murdered_state=True,
                    ending_message="VIBES MURDERED",
                ),
            )
        sk = finisher_shutdown_kind_for_do_action(ctx.prompt)
        return _finalize_response(
            ctx,
            _finisher_response(
                shutdown_kind=sk,
                input_text=ctx.prompt,
                state_before=before,
                state_after=stt,
                physical=physical
                or "steps back, expression shutting down — they're done with this",
                tone="hostile",
                vibe="unfathomable",
                apply_murdered=True,
                ending_message="VIBES MURDERED",
            ),
        )

    ap = try_pick_authored_action_response(
        ctx.prompt,
        ctx.repeat_count,
        stt,
        before,
        ctx.moonwalk_streak,
    )
    if ap is not None:
        verbal = quote(ap.verbal_inner) if ap.verbal_inner.strip() else ""
        tone = ap.tone_override or infer_tone(stt)
        vibe = ap.vibe_override or infer_vibe(stt)
        physical = ap.physical if ap.physical else infer_physical_response(stt)
        if not strip_outer_quotes(verbal).strip():
            verbal = _ensure_non_empty_verbal(verbal, fallback="…")
        rel = relationship_status(stt, False)
        return _finalize_response(
            ctx,
            Response(
                verbal=verbal,
                physical=physical,
                tone=tone,
                vibe=vibe,
                relationship=rel,
                stats_delta=delta,
                ended=False,
                source="authored",
                moonwalk_universe_rulerz=bool(ap.moonwalk_universe_mode),
            ),
        )

    if not strip_outer_quotes(verbal or "").strip():
        extra = maybe_social_verbal_for_do_action(ctx.prompt, ctx.repeat_count, stt, ctx.personality)
        if extra:
            verbal = quote(extra)
    if not strip_outer_quotes(verbal or "").strip():
        verbal = quote(
            minimal_verbal_ack_for_do_action(
                ctx.prompt,
                ctx.repeat_count,
                stt,
                ctx.personality,
                brain,
            )
        )
    verbal = _ensure_non_empty_verbal(verbal, fallback="Yeah.")
    rel = relationship_status(stt, False)
    return _finalize_response(
        ctx,
        Response(
            verbal=verbal,
            physical=physical,
            tone=tone,
            vibe=vibe,
            relationship=rel,
            stats_delta=delta,
            ended=False,
            source="engine",
        ),
    )
