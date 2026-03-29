# -*- coding: utf-8 -*-
"""
Behavioral stress harness for trajectory phases and response feel.

Run headless (no Streamlit server):
    python -m silvercrow.trajectory_stress_test

Do not import this module from the live Streamlit app — it replaces ``streamlit``
in ``sys.modules`` for the process.
"""

from __future__ import annotations

import json
import math
import random
import statistics
import sys
import types
from collections import UserDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Headless Streamlit stub (must run before ``import silvercrow.main``)
# ---------------------------------------------------------------------------


class HarnessSessionState(UserDict):
    """Minimal session_state: supports dict API + attribute access like Streamlit."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "data":
            return super().__setattr__(name, value)
        self.data[name] = value


class _DummyColumnCtx:
    def __enter__(self) -> "_DummyColumnCtx":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _make_streamlit_stub() -> types.ModuleType:
    st = types.ModuleType("streamlit")
    st.session_state = HarnessSessionState()

    def _noop(*_a: object, **_k: object) -> None:
        return None

    st.set_page_config = _noop  # type: ignore[assignment]
    st.markdown = _noop  # type: ignore[assignment]
    st.write = _noop  # type: ignore[assignment]
    st.caption = _noop  # type: ignore[assignment]
    st.rerun = _noop  # type: ignore[assignment]

    def _columns(*args: object, **kwargs: object) -> List[_DummyColumnCtx]:
        if not args:
            return [_DummyColumnCtx() for _ in range(3)]
        a0 = args[0]
        if isinstance(a0, int):
            n = max(1, a0)
        elif isinstance(a0, (list, tuple)):
            n = max(1, len(a0))
        else:
            n = 3
        return [_DummyColumnCtx() for _ in range(n)]

    st.columns = _columns  # type: ignore[assignment]

    def _button(*_a: object, **_k: object) -> bool:
        return False

    st.button = _button  # type: ignore[assignment]

    def _text_input(_label: str, *args: object, **kwargs: Any) -> str:
        v = kwargs.get("value", "")
        return v if isinstance(v, str) else ""

    st.text_input = _text_input  # type: ignore[assignment]

    def _selectbox(_label: str, options: Sequence[Any], **kwargs: Any) -> Any:
        opts = list(options)
        if not opts:
            return None
        idx = int(kwargs.get("index", 0) or 0)
        idx = max(0, min(idx, len(opts) - 1))
        return opts[idx]

    st.selectbox = _selectbox  # type: ignore[assignment]
    return st


_STUB_INSTALLED = False


def install_headless_streamlit() -> None:
    """Replace ``sys.modules['streamlit']`` with a stub (one-time)."""
    global _STUB_INSTALLED
    if _STUB_INSTALLED:
        return
    if "streamlit" in sys.modules:
        existing = sys.modules["streamlit"]
        if getattr(existing, "__name__", "") == "streamlit" and hasattr(existing, "runtime"):
            raise RuntimeError(
                "Real Streamlit is already loaded. Run this harness as:\n"
                "  python -m silvercrow.trajectory_stress_test\n"
                "from a fresh interpreter (do not import from the Streamlit app)."
            )
    sys.modules["streamlit"] = _make_streamlit_stub()
    _STUB_INSTALLED = True


# ---------------------------------------------------------------------------
# Scripts: (label, kind, text)
# ---------------------------------------------------------------------------

Action = Tuple[str, str, str]  # label, kind, text

SMOOTH_POSITIVE_FLOW: List[Action] = [
    ("polite_open", "say", "Hello, nice to meet you."),
    ("light_flirt", "say", "Do you like me?"),
    ("trust_question", "say", "Why should I trust you?"),
    ("mild_disagreement", "say", "I disagree with you."),
    ("repair_attempt", "say", "I respect your opinion."),
    ("escalation", "say", "You're wrong."),
]

AWKWARD_THEN_RECOVER: List[Action] = [
    ("awkward_opener", "say", "Cash me outside, how 'bout that?"),
    ("check_in", "say", "Hey, how are you?"),
    ("repair_attempt", "say", "I want to help."),
    ("reengage", "say", "What do you need?"),
    ("trust_build", "say", "What do you think of me so far?"),
]

# Say-only trajectory slice (menu SAY lines; do-actions are supported elsewhere in the app).
PUSHY_AND_IGNORE: List[Action] = [
    ("polite_open", "say", "Nice to meet you"),
    ("repeated_push", "say", "Why are you talking to me?"),
    ("repeated_push", "say", "Why are you talking to me?"),
    ("ignore_signal", "say", "Why do you care?"),
    ("escalation", "say", "Do you think you're better than me?"),
    ("repeated_push", "say", "Why are you acting like this?"),
]

PLAYFUL_THEN_DISRESPECT: List[Action] = [
    ("playful", "say", "What's up?"),
    ("light_flirt", "say", "Do you want to go on a date?"),
    ("mild_disagreement", "say", "I disagree with you."),
    ("disrespect", "say", "You're wrong."),
    ("escalation", "say", "Who do you think you are?"),
]

FRAGILE_PRESSURE: List[Action] = [
    ("pressure", "say", "Why don't you like me?"),
    ("pressure", "say", "Why are you treating me this way?"),
    ("repair_attempt", "say", "I respect your opinion."),
    ("soft_ask", "say", "Can you help me?"),
    ("trust_question", "say", "Why should I trust you?"),
]


SCRIPTS: Dict[str, List[Action]] = {
    "smooth_positive_flow": SMOOTH_POSITIVE_FLOW,
    "awkward_then_recover": AWKWARD_THEN_RECOVER,
    "pushy_and_ignore_signals": PUSHY_AND_IGNORE,
    "playful_then_disrespect": PLAYFUL_THEN_DISRESPECT,
    "fragile_pressure_test": FRAGILE_PRESSURE,
}


@dataclass
class BuilderSetup:
    """Deterministic builder inputs; trajectory comes from ``start_scenario`` only."""

    name: str
    personality: str
    background: str
    physical: str
    mood: str
    archetype: str
    dna_seed: int
    # If set, used as ``draft_name`` verbatim (affects ``_traj_seed`` in ``start_scenario``).
    draft_name_override: Optional[str] = None


# Distinct archetypes + moods; two overrides tune ``_stable_seed_from_text`` to hit rarer trajectories.
DEFAULT_SETUPS: Tuple[BuilderSetup, ...] = (
    BuilderSetup("alpha_cocky", "Aggressive", "Entrepreneur", "Stressed", "Irritated", "cocky", 910_001),
    BuilderSetup("beta_guarded", "Shy", "Office Worker", "Tired", "Anxious", "guarded", 910_002),
    BuilderSetup("gamma_playful", "Impulsive", "Artist", "Energized", "Excited", "playful", 910_003),
    BuilderSetup("delta_awkward", "Empathetic", "College Student", "Relaxed", "Calm", "awkward", 910_004),
    BuilderSetup("epsilon_cold", "Confident", "Military Veteran", "Injured", "Neutral", "cold", 910_005),
    BuilderSetup(
        "zeta_guarded_open",
        "Shy",
        "Office Worker",
        "Relaxed",
        "Calm",
        "guarded",
        5,
        draft_name_override="Probe5",
    ),
    BuilderSetup(
        "eta_playful_cutting",
        "Impulsive",
        "Artist",
        "Energized",
        "Excited",
        "playful",
        1,
        draft_name_override="Ptc1",
    ),
)


@dataclass
class TurnLog:
    turn_index: int
    input_label: str
    kind: str
    selected_input_text: str
    trajectory_id: str
    trajectory_phase: str
    trust: int
    anger: int
    stress: int
    happiness: int
    interest: int
    escalation_score: int
    positive_streak: int
    negative_streak: int
    repair_attempt_streak: int
    response_text: str
    response_length: int
    sharpen_applied: bool
    callback_triggered: bool
    menu_bucket: str
    finisher_triggered: bool
    finisher_shutdown_kind: Optional[str]
    conversation_over: bool
    anger_delta: int
    trust_delta: int
    response_tone: str


@dataclass
class RunMetrics:
    script_name: str
    setup_name: str
    stored_trajectory: str
    turns: List[TurnLog] = field(default_factory=list)
    trajectory_phase_changes: int = 0
    final_phase: str = ""
    phase_sequence: List[str] = field(default_factory=list)
    max_anger: int = 0
    max_trust: int = 0
    flags: List[str] = field(default_factory=list)
    recovery_possible: Optional[bool] = None
    repetition_notes: str = ""


def _strip_quotes(s: str) -> str:
    t = (s or "").strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    return t


def _patch_sharpen_tracker() -> Callable[[], bool]:
    """Patch menu + response_voice so we can read whether sharpening changed text."""
    import silvercrow.menu_responses as mr
    import silvercrow.response_voice as rv

    last: Dict[str, bool] = {"applied": False}
    _orig = rv.maybe_sharpen_response

    def _wrap(
        text: str,
        state: Dict[str, Any],
        personality: str = "",
        *,
        voice_sharpen_bias: float = 0.0,
    ) -> str:
        out = _orig(text, state, personality, voice_sharpen_bias=voice_sharpen_bias)
        a = (text or "").strip()
        b = (out or "").strip()
        last["applied"] = bool(a and a != b)
        return out

    rv.maybe_sharpen_response = _wrap  # type: ignore[assignment]
    mr.maybe_sharpen_response = _wrap  # type: ignore[assignment]

    def _read() -> bool:
        v = last["applied"]
        last["applied"] = False
        return v

    return _read


def _apply_builder_and_start(
    main_mod: Any,
    setup: BuilderSetup,
    scenario_name: str,
) -> str:
    st = sys.modules["streamlit"]
    ss = st.session_state
    ss.draft_name = (
        setup.draft_name_override
        if setup.draft_name_override is not None
        else setup.name.replace("_", " ").title()
    )
    ss.draft_personality = setup.personality
    ss.draft_background = setup.background
    ss.draft_physical = setup.physical
    ss.draft_mood = setup.mood
    ss.draft_archetype = setup.archetype
    ss.dna_seed = int(setup.dna_seed)
    main_mod.start_scenario(scenario_name)
    snap = ss.get("build_snapshot") or {}
    return str(snap.get("Trajectory") or "")


def _run_script_actions(
    main_mod: Any,
    script: Sequence[Action],
    get_sharpen: Callable[[], bool],
) -> List[TurnLog]:
    from silvercrow.callback_memory import CALLBACK_DEBUG_KEY
    from silvercrow.finishers import FINISHER_SESSION_DEBUG_KEY
    from silvercrow.interaction_profile import PROFILE_KEY
    from silvercrow.trajectory_layer import TRAJECTORY_DEBUG_KEY

    st = sys.modules["streamlit"]
    ss = st.session_state
    logs: List[TurnLog] = []

    for step_i, (label, kind, text) in enumerate(script):
        pre_state = {k: int(ss.state[k]) for k in ("trust", "anger", "stress", "happiness", "interest")}

        if kind == "say":
            main_mod.process_interaction(text, "say", is_free_text=False)
        else:
            main_mod.process_interaction(text, "do")

        if ss.conversation_over:
            pass

        entry = (ss.history or [{}])[0] if ss.history else {}
        raw_verbal = str(entry.get("verbal") or "")
        response_plain = _strip_quotes(raw_verbal)

        prof = ss.get(PROFILE_KEY) or {}
        traj_dbg = ss.get(TRAJECTORY_DEBUG_KEY) or {}
        cb_dbg = ss.get(CALLBACK_DEBUG_KEY) or {}
        fin_dbg = ss.get(FINISHER_SESSION_DEBUG_KEY) or {}

        post_state = ss.state
        sharpen = get_sharpen()
        callback_hit = bool(cb_dbg.get("override_used"))
        fin_text = fin_dbg.get("finisher_text")
        finisher_on = bool(fin_text) or (
            ss.conversation_over and (ss.ending_message or "") in ("VIBES MURDERED", "CONVERSATION ENDED")
        )

        logs.append(
            TurnLog(
                turn_index=step_i,
                input_label=label,
                kind=kind,
                selected_input_text=text,
                trajectory_id=str(traj_dbg.get("trajectory_id") or ""),
                trajectory_phase=str(traj_dbg.get("trajectory_phase") or ""),
                trust=int(post_state.get("trust", 0)),
                anger=int(post_state.get("anger", 0)),
                stress=int(post_state.get("stress", 0)),
                happiness=int(post_state.get("happiness", 0)),
                interest=int(post_state.get("interest", 0)),
                escalation_score=int(prof.get("escalation_score", 0)),
                positive_streak=int(prof.get("positive_streak", 0)),
                negative_streak=int(prof.get("negative_streak", 0)),
                repair_attempt_streak=int(prof.get("repair_attempt_streak", 0)),
                response_text=response_plain[:2000],
                response_length=len(response_plain),
                sharpen_applied=sharpen,
                callback_triggered=callback_hit,
                menu_bucket=str(ss.get("_last_menu_bucket") or ""),
                finisher_triggered=bool(finisher_on),
                finisher_shutdown_kind=str(fin_dbg.get("shutdown_kind") or "") or None,
                conversation_over=bool(ss.conversation_over),
                anger_delta=int(post_state.get("anger", 0)) - pre_state["anger"],
                trust_delta=int(post_state.get("trust", 0)) - pre_state["trust"],
                response_tone=str(entry.get("tone") or ""),
            )
        )

        if ss.conversation_over:
            break

    return logs


def _ordered_unique_phases(turns: Sequence[TurnLog]) -> List[str]:
    seen: List[str] = []
    for t in turns:
        ph = (t.trajectory_phase or "").strip()
        if ph and (not seen or seen[-1] != ph):
            seen.append(ph)
    return seen


def _evaluate_run(script_name: str, setup_name: str, stored_traj: str, turns: List[TurnLog]) -> RunMetrics:
    m = RunMetrics(script_name=script_name, setup_name=setup_name, stored_trajectory=stored_traj, turns=list(turns))
    if not turns:
        m.flags.append("no turns completed")
        return m

    phases = [t.trajectory_phase for t in turns if t.trajectory_phase]
    m.phase_sequence = _ordered_unique_phases(turns)
    m.final_phase = phases[-1] if phases else ""
    m.trajectory_phase_changes = sum(
        1 for i in range(1, len(phases)) if phases[i] != phases[i - 1]
    )
    m.max_anger = max(t.anger for t in turns)
    m.max_trust = max(t.trust for t in turns)

    for t in turns:
        if t.turn_index < 3 and t.menu_bucket == "severe":
            m.flags.append(f"escalation too early (interaction {t.turn_index}, bucket severe)")
        if t.turn_index < 3 and t.anger >= 78:
            m.flags.append(f"escalation too early (interaction {t.turn_index}, anger={t.anger})")

    severe_like = {"You're wrong.", "Who do you think you are?", "What gives you the right?"}
    for t in turns:
        if t.anger_delta >= 40 and t.selected_input_text.strip() not in severe_like:
            m.flags.append(
                f"large anger jump (+{t.anger_delta}) on input {t.input_label!r} without severe menu text"
            )

    if len(turns) >= 6 and m.trajectory_phase_changes == 0 and m.final_phase:
        m.flags.append("trajectory_phase never changed (>=6 turns)")

    lengths = [t.response_length for t in turns if t.response_length > 0]
    if len(lengths) >= 4:
        try:
            stdev = statistics.pstdev(lengths)
            if stdev < 4.5:
                m.flags.append("response lengths very uniform (low stdev)")
        except statistics.StatisticsError:
            pass

    if len(turns) >= 5:
        from collections import Counter

        tones = [t.response_tone for t in turns if t.response_tone]
        if tones:
            c = Counter(tones)
            top_n, top_c = c.most_common(1)[0]
            if top_c >= max(4, int(math.ceil(len(turns) * 0.85))):
                m.flags.append(
                    f"responses mostly one tone ({top_n!r} on {top_c}/{len(turns)} turns — weak variety)"
                )

    any_callback = any(t.callback_triggered for t in turns)
    if len(turns) >= 6 and not any_callback:
        m.flags.append("no callback override in >=6 turns (may be OK)")

    repair_idxs = [i for i, t in enumerate(turns) if t.input_label == "repair_attempt"]
    recovery = None
    for ri in repair_idxs:
        window = turns[ri : ri + 3]
        if len(window) >= 2:
            trust_gain = window[-1].trust - turns[ri].trust
            if trust_gain >= 3:
                recovery = True
    if repair_idxs and recovery is None:
        recovery = False
    m.recovery_possible = recovery

    rep_turns = [t for t in turns if "repeat" in t.input_label or t.input_label.startswith("repeated")]
    if rep_turns:
        m.repetition_notes = f"{len(rep_turns)} push/repeat-tagged steps; murder_threshold behavior see final turn flags"

    if stored_traj == "playful_then_cutting" and len(turns) >= 5:
        if "cutting" not in m.phase_sequence and "edgy" not in m.phase_sequence:
            m.flags.append("weak distinction: playful_then_cutting never reached edgy/cutting phase")

    return m


def _turn_to_dict(t: TurnLog) -> Dict[str, Any]:
    return {k: getattr(t, k) for k in t.__dataclass_fields__}


def _metrics_to_dict(m: RunMetrics) -> Dict[str, Any]:
    return {
        "script_name": m.script_name,
        "setup_name": m.setup_name,
        "stored_trajectory": m.stored_trajectory,
        "trajectory_phase_changes": m.trajectory_phase_changes,
        "final_phase": m.final_phase,
        "phase_sequence": m.phase_sequence,
        "max_anger": m.max_anger,
        "max_trust": m.max_trust,
        "flags": list(m.flags),
        "recovery_possible": m.recovery_possible,
        "repetition_notes": m.repetition_notes,
        "turns": [_turn_to_dict(t) for t in m.turns],
    }


def _print_run_summary(m: RunMetrics) -> None:
    print(f"\n=== TEST: {m.script_name} ===")
    print(f"Setup: {m.setup_name}  |  Stored trajectory: {m.stored_trajectory}")
    prog = " -> ".join(m.phase_sequence) if m.phase_sequence else "(no phase data)"
    print(f"Phase progression: {prog}")
    if m.turns:
        last = m.turns[-1]
        print(f"Final state: trust={last.trust}, anger={last.anger}, stress={last.stress}, over={last.conversation_over}")
    print("Flags:")
    if m.flags:
        for f in m.flags:
            print(f"  - {f}")
    else:
        print("  (none)")
    if m.recovery_possible is not None:
        print(f"Recovery after repair heuristic: {m.recovery_possible}")
    if m.repetition_notes:
        print(f"Repetition: {m.repetition_notes}")
    print("Sample responses:")
    for t in m.turns[:4]:
        preview = (t.response_text[:120] + "…") if len(t.response_text) > 120 else t.response_text
        print(f"  [{t.input_label}] {preview!r}")


def run_all_tests(
    *,
    scenario_name: str = "Living Room",
    setups: Sequence[BuilderSetup] = DEFAULT_SETUPS,
    export_json: bool = True,
    master_seed: int = 42,
) -> Dict[str, Any]:
    """
    Execute all scripts × setups. Returns a report dict and optionally writes JSON.

    Parameters
    ----------
    master_seed
        Seeds ``random`` for reproducible lines inside the engine.
    """
    install_headless_streamlit()
    random.seed(master_seed)

    import silvercrow.main as main_mod

    get_sharpen = _patch_sharpen_tracker()

    report: Dict[str, Any] = {
        "scenario": scenario_name,
        "master_seed": master_seed,
        "runs": [],
    }

    traj_seen: Dict[str, str] = {}

    for setup in setups:
        for script_name, actions in SCRIPTS.items():
            stored = _apply_builder_and_start(main_mod, setup, scenario_name)
            traj_seen.setdefault(setup.name, stored)
            turns = _run_script_actions(main_mod, actions, get_sharpen)
            metrics = _evaluate_run(script_name, setup.name, stored, turns)
            report["runs"].append(_metrics_to_dict(metrics))
            _print_run_summary(metrics)

    unique_traj = set(traj_seen.values())
    print(f"\n--- Trajectory coverage across setups ({len(setups)} builds) ---")
    for k, v in sorted(traj_seen.items()):
        print(f"  {k}: {v}")
    print(f"  Unique trajectories: {len(unique_traj)} | {sorted(unique_traj)}")

    if export_json:
        out_dir = Path(__file__).resolve().parent / "test_outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "trajectory_stress_report.json"
        out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\nWrote {out_path}")

    return report


def run_single_script(
    script_key: str,
    setup: Optional[BuilderSetup] = None,
    *,
    scenario_name: str = "Living Room",
    master_seed: int = 42,
) -> RunMetrics:
    """Convenience API for a single script (e.g. future ``sam_tester`` hook)."""
    install_headless_streamlit()
    random.seed(master_seed)
    import silvercrow.main as main_mod

    get_sharpen = _patch_sharpen_tracker()
    su = setup or DEFAULT_SETUPS[0]
    actions = SCRIPTS[script_key]
    stored = _apply_builder_and_start(main_mod, su, scenario_name)
    turns = _run_script_actions(main_mod, actions, get_sharpen)
    return _evaluate_run(script_key, su.name, stored, turns)


if __name__ == "__main__":
    run_all_tests()
