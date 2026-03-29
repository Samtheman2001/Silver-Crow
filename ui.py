"""
Streamlit rendering/presentation helpers.
"""

from __future__ import annotations

import random


def attribute_color(attr, delta):
    if delta == 0:
        return "#cbd5e1"
    good_when_up = attr in ["happiness", "trust", "confidence", "interest"]
    positive_good = (delta > 0 and good_when_up) or (delta < 0 and not good_when_up)
    return "#22c55e" if positive_good else "#ef4444"


def format_delta(delta):
    if delta == 0:
        return ""
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta}"


def get_avatar(personality, state, murdered=False, relationship_override=None):
    ro = relationship_override if isinstance(relationship_override, str) else ""
    if ro.strip() == "Rulerz of the Universe":
        return "😈"
    if murdered:
        return random.choice(["😡", "🤬", "😤"])
    base = {
        "Confident": "😎",
        "Shy": "🙂",
        "Aggressive": "😤",
        "Empathetic": "😊",
        "Analytical": "🧐",
        "Impulsive": "🤪",
    }.get(personality, "🙂")
    if state["anger"] > 70:
        return "😠"
    if state["fear"] > 70:
        return "😬"
    if state["stress"] > 70:
        return "😵"
    if state["happiness"] > 70 and state["trust"] > 60:
        return "😊"
    if state["confusion"] > 65:
        return "🤨"
    return base


def app_css(st):
    """Inject CSS (Streamlit instance passed in)."""
    st.markdown(
        """
        <style>
        :root {
            --stat-bar-fill-start: #2563eb;
            --stat-bar-fill-end: #6366f1;
        }
        .stApp {
            background:
                linear-gradient(125deg, rgba(255,255,255,0.55) 0%, transparent 38%),
                linear-gradient(210deg, rgba(255,255,255,0.22) 0%, transparent 42%),
                radial-gradient(ellipse 90% 55% at 50% -8%, rgba(255,255,255,0.45), transparent 55%),
                radial-gradient(circle at top left, rgba(255,255,255,0.92), transparent 26%),
                radial-gradient(circle at top right, rgba(200,170,255,0.2), transparent 28%),
                radial-gradient(circle at bottom left, rgba(192,198,210,0.38), transparent 32%),
                radial-gradient(circle at bottom right, rgba(200,185,220,0.1), transparent 30%),
                linear-gradient(145deg, #f4f5f7 0%, #e8eaee 32%, #e4e6ec 55%, #f2f3f8 100%);
            color: #171a20;
        }
        /* Hide Streamlit chrome: Deploy, ⋮ menu, header actions — not part of the game UI */
        header[data-testid="stHeader"] {display: none !important;}
        div[data-testid="stToolbar"] {display: none !important;}
        div[data-testid="stDecoration"] {display: none !important;}
        div[data-testid="stStatusWidget"] {display: none !important;}
        .stAppDeployButton {display: none !important;}
        button[data-testid="baseButton-header"] {display: none !important;}
        /* Demo: hide “Or say whatever:” + free-text field only (unique placeholder; builder text inputs unaffected) */
        div[data-testid="stTextInput"]:has(input[placeholder="Type something..."]) {
            display: none !important;
        }
        .block-container {padding-top: 1.05rem; padding-bottom: 0.35rem; max-width: 1680px;}
        .main-title {
            font-size: 1.92rem; font-weight: 1000; letter-spacing: 0.03em; margin-bottom: 0.12rem;
            background: linear-gradient(90deg, #7c7f87 0%, #eef1f5 20%, #bfc7d6 44%, #c8a2ff 72%, #6a6f7a 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 1px 0 rgba(255,255,255,0.55);
        }
        .subtitle {color: #5a5468; font-size: 0.91rem; margin-bottom: 0.38rem;}
        .panel {padding: 0.1rem 0 0 0;}
        .center-panel {padding-top: 0.15rem;}
        .section-title {
            font-size: 0.88rem; font-weight: 1000; margin-bottom: 0.4rem; color: #2a2638;
            letter-spacing: 0.14em; text-transform: uppercase;
        }
        .section-title--spaced { margin-top: 0.65rem; }
        .hero-avatar {font-size: 3.5rem; line-height: 1; margin-bottom: 0.12rem; filter: drop-shadow(0 3px 10px rgba(0,0,0,0.11));}
        .hero-name {
            font-size: 1.78rem; font-weight: 1000; margin-bottom: 0.5rem; color: #141a24;
            letter-spacing: 0.02em;
        }
        /* Center: avatar → name → readout; simple stacked verbal + physical (no flex “stack” system) */
        .center-response-panel {
            text-align: center;
            padding: 0.35rem 0 1.35rem;
            max-width: 100%;
        }
        .center-response-panel--play {
            text-align: center;
            padding: 0.2rem 0.5rem 0.75rem;
            box-sizing: border-box;
        }
        .block-container:has(#gameover-section) .center-response-panel--play {
            padding-top: 0.3rem;
            padding-bottom: 0.65rem;
        }
        .center-response-panel .hero-name { margin-bottom: 0.35rem; }
        .center-response-panel--play .hero-avatar {
            margin-bottom: 0.1rem;
            line-height: 1;
        }
        .center-response-panel--play .hero-name { margin-bottom: 0.26rem; }
        .center-response-panel--play .response-context-line {
            margin: 0.1rem auto 0.48rem;
            max-width: 40rem;
        }
        .response-context-line {
            font-size: 1.02rem;
            font-weight: 650;
            color: #1e293b;
            margin: 0.2rem auto 1rem;
            max-width: 38rem;
            line-height: 1.45;
            text-rendering: optimizeLegibility;
        }
        .response-readout {
            margin: 0.15rem auto 0.5rem;
            padding: 0.2rem 0.5rem 0.35rem;
            max-width: 44rem;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.68rem;
            box-sizing: border-box;
        }
        .response-readout__line {
            font-size: 2.12rem;
            line-height: 1.32;
            font-weight: 750;
            letter-spacing: 0.008em;
            text-align: center;
            width: 100%;
            max-width: 42rem;
            text-rendering: optimizeLegibility;
            overflow-wrap: break-word;
            word-break: normal;
        }
        .response-readout__line--physical {
            color: #39ff5a;
            text-shadow:
                0 1px 0 rgba(255,255,255,0.88),
                0 1px 2px rgba(0, 110, 55, 0.4),
                0 0 1px rgba(0, 90, 45, 0.45);
        }
        .response-readout__line--verbal {
            color: #a78bfa;
            text-shadow:
                0 1px 0 rgba(255,255,255,0.88),
                0 1px 2px rgba(76, 29, 149, 0.28),
                0 0 1px rgba(60, 20, 120, 0.22);
        }
        .scenario-head {
            font-size: 0.78rem; font-weight: 1000; letter-spacing: 0.11em; text-transform: uppercase;
            color: #6b7280; margin-bottom: 0.45rem;
        }
        .tiny {font-size:0.84rem;color:#596579;}
        .summary-line {font-size:0.94rem;color:#2d3645;margin:0.16rem 0;}
        .gameover {
            border: 1px solid rgba(180,160,220,0.4); border-radius: 24px; padding: 2.5rem 1.5rem; text-align: center;
            background: linear-gradient(180deg, rgba(245,240,255,0.85), rgba(230,220,245,0.92));
            box-shadow: 0 0 40px rgba(180,160,220,0.15), 0 14px 34px rgba(35,44,62,0.08), inset 0 1px 0 rgba(255,255,255,0.9);
            margin-bottom: 0.8rem;
            position: relative;
        }
        .gameover-big {
            font-size: 3.85rem; font-weight: 1000; letter-spacing: 0.16em; margin-bottom: 0.5rem;
            color: #4a3f6b;
            text-shadow: 0 0 24px rgba(180,160,220,0.5), 0 0 48px rgba(150,130,200,0.25);
            font-family: system-ui, -apple-system, sans-serif;
        }
        .gameover-small {font-size: 0.95rem; color: #5a5168; opacity: 0.9; letter-spacing: 0.02em;}
        /* VIBES MURDERED: dominant banner + center column only (left/right panels unchanged) */
        .block-container:has(.gameover--vibes-murdered) {
            padding-top: 0.18rem !important;
            padding-bottom: 0.06rem !important;
        }
        .block-container:has(.gameover--vibes-murdered) .gameover.gameover--vibes-murdered {
            padding: 1.12rem 1.55rem 0.95rem;
            margin-bottom: 0.12rem;
            border-radius: 20px;
        }
        .block-container:has(.gameover--vibes-murdered) .gameover--vibes-murdered .gameover-big {
            font-size: clamp(3.35rem, 11vw, 6.35rem);
            letter-spacing: 0.14em;
            margin-bottom: 0.28rem;
            line-height: 1.04;
        }
        .block-container:has(.gameover--vibes-murdered) .gameover--vibes-murdered .gameover-small {
            font-size: 0.88rem;
            margin-bottom: 0;
            line-height: 1.32;
        }
        .block-container:has(.gameover--vibes-murdered) .center-response-panel--play {
            padding: 0.2rem 0.35rem 0.55rem !important;
        }
        .block-container:has(.gameover--vibes-murdered) .response-context-line {
            font-size: 0.82rem;
            margin: 0.06rem auto 0.28rem;
            line-height: 1.3;
        }
        .block-container:has(.gameover--vibes-murdered) .hero-avatar {
            font-size: clamp(3.35rem, 8.5vw, 4.7rem);
            margin-bottom: 0.12rem;
            line-height: 1;
        }
        .block-container:has(.gameover--vibes-murdered) .hero-name {
            font-size: clamp(1.32rem, 2.95vw, 1.78rem);
            margin-bottom: 0.16rem !important;
            line-height: 1.12;
        }
        .block-container:has(.gameover--vibes-murdered) .response-readout {
            margin: 0.28rem auto 0.38rem;
            padding: 0.16rem 0.45rem 0.24rem;
            gap: 0.62rem;
        }
        .block-container:has(.gameover--vibes-murdered) .response-readout__line {
            font-size: clamp(1.78rem, 3.15vw, 2.26rem);
            line-height: 1.34;
            font-weight: 750;
        }
        /* OVERSTIMULATED ending: same cinematic priority as VM */
        .block-container:has(.gameover--overstimulated) {
            padding-top: 0.18rem !important;
            padding-bottom: 0.06rem !important;
        }
        .block-container:has(.gameover--overstimulated) .gameover.gameover--overstimulated {
            padding: 0.68rem 1.05rem 0.55rem;
            margin-bottom: 0.12rem;
        }
        .block-container:has(.gameover--overstimulated) .gameover-big--overstim {
            font-size: clamp(2.55rem, 5.2vw, 4.65rem) !important;
            letter-spacing: 0.17em !important;
            margin-bottom: 0.22rem !important;
            line-height: 1.05 !important;
        }
        .block-container:has(.gameover--overstimulated) .gameover-small--overstim {
            font-size: clamp(0.95rem, 1.65vw, 1.22rem) !important;
            line-height: 1.35 !important;
        }
        .block-container:has(.gameover--overstimulated) .go-bolt {
            font-size: clamp(1.62rem, 3.55vw, 2.42rem) !important;
        }
        .block-container:has(.gameover--overstimulated) .center-response-panel--play {
            padding: 0.2rem 0.35rem 0.55rem !important;
        }
        .block-container:has(.gameover--overstimulated) .response-context-line {
            font-size: 0.82rem;
            margin: 0.06rem auto 0.28rem;
            line-height: 1.3;
        }
        .block-container:has(.gameover--overstimulated) .hero-avatar {
            font-size: clamp(3.35rem, 8.5vw, 4.7rem);
            margin-bottom: 0.12rem;
            line-height: 1;
        }
        .block-container:has(.gameover--overstimulated) .hero-name {
            font-size: clamp(1.32rem, 2.95vw, 1.78rem);
            margin-bottom: 0.16rem !important;
            line-height: 1.12;
        }
        .block-container:has(.gameover--overstimulated) .response-readout {
            margin: 0.28rem auto 0.38rem;
            padding: 0.16rem 0.45rem 0.24rem;
            gap: 0.62rem;
        }
        .block-container:has(.gameover--overstimulated) .response-readout__line {
            font-size: clamp(1.78rem, 3.15vw, 2.26rem);
            line-height: 1.34;
            font-weight: 750;
        }
        /* VM + Overstim: middle column only — tight avatar → name → readout */
        .block-container:has(#gameover-section) .center-response-panel--play {
            padding-bottom: 0.55rem !important;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }
        .block-container:has(#gameover-section) .center-response-panel--play .hero-avatar {
            margin-bottom: 0.1rem;
        }
        .block-container:has(#gameover-section) .center-response-panel--play .hero-name {
            margin-bottom: 0.18rem !important;
        }
        .block-container:has(#gameover-section) .response-context-line {
            margin-bottom: 0.32rem !important;
        }
        .block-container:has(#gameover-section) .response-readout {
            margin-top: 0.12rem;
            margin-bottom: 0.28rem;
            padding-top: 0.12rem;
            padding-bottom: 0.18rem;
            max-width: 48rem;
            gap: 0.62rem;
        }
        /* VIBES MURDERED only: overrides shared #gameover-section mids so payoff fits on laptop (Overstim unchanged) */
        .block-container:has(#gameover-section.gameover--vibes-murdered) .center-response-panel--play {
            padding: 0.15rem 0.35rem 0.5rem !important;
        }
        .block-container:has(#gameover-section.gameover--vibes-murdered) .response-context-line {
            margin: 0.04rem auto 0.14rem !important;
        }
        .block-container:has(#gameover-section.gameover--vibes-murdered) .center-response-panel--play .hero-avatar {
            margin-bottom: 0.06rem !important;
        }
        .block-container:has(#gameover-section.gameover--vibes-murdered) .center-response-panel--play .hero-name {
            margin-bottom: 0.08rem !important;
        }
        .block-container:has(#gameover-section.gameover--vibes-murdered) .response-readout {
            margin: 0.12rem auto 0.28rem !important;
            padding: 0.12rem 0.45rem 0.18rem !important;
            gap: 0.45rem !important;
        }
        .block-container:has(#gameover-section.gameover--vibes-murdered) .response-readout__line {
            font-size: clamp(1.52rem, 2.75vw, 1.95rem) !important;
            line-height: 1.28 !important;
        }
        /* OVERSTIMULATED (4th moonwalk): purple headline, neon green bolts, chaotic-celebratory frame */
        .gameover--overstimulated {
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(57, 255, 90, 0.45);
            background:
                radial-gradient(ellipse 120% 80% at 50% 0%, rgba(168, 85, 247, 0.22), transparent 55%),
                radial-gradient(ellipse 90% 60% at 20% 100%, rgba(34, 255, 136, 0.12), transparent 45%),
                radial-gradient(ellipse 90% 60% at 80% 100%, rgba(34, 255, 136, 0.12), transparent 45%),
                linear-gradient(180deg, rgba(28, 15, 48, 0.94), rgba(18, 12, 32, 0.97));
            box-shadow:
                0 0 0 1px rgba(168, 85, 247, 0.35),
                0 0 48px rgba(34, 255, 120, 0.35),
                0 0 80px rgba(168, 85, 247, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.12);
        }
        .go-bolt {
            position: absolute;
            font-size: 1.65rem;
            line-height: 1;
            color: #39ff5a;
            text-shadow:
                0 0 12px rgba(57, 255, 90, 0.95),
                0 0 28px rgba(57, 255, 90, 0.55),
                0 0 44px rgba(34, 200, 90, 0.35);
            pointer-events: none;
            z-index: 1;
        }
        .go-bolt--tl { top: 0.55rem; left: 0.65rem; transform: rotate(-12deg); }
        .go-bolt--tr { top: 0.55rem; right: 0.65rem; transform: rotate(12deg); }
        .go-bolt--bl { bottom: 0.55rem; left: 0.75rem; transform: rotate(8deg); }
        .go-bolt--br { bottom: 0.55rem; right: 0.75rem; transform: rotate(-8deg); }
        .gameover-big--overstim {
            position: relative;
            z-index: 2;
            font-size: 3.55rem;
            letter-spacing: 0.2em;
            color: #c084fc;
            -webkit-text-fill-color: #c084fc;
            background: none;
            text-shadow:
                0 0 22px rgba(192, 132, 252, 0.85),
                0 0 48px rgba(168, 85, 247, 0.45),
                0 0 2px rgba(34, 255, 90, 0.35);
        }
        .gameover-small--overstim {
            position: relative;
            z-index: 2;
            font-size: 1.15rem;
            font-weight: 700;
            color: #a7f3c8;
            letter-spacing: 0.04em;
        }
        .recovery-buttons-overstim { display: none; }
        /* Pikachu-yellow recovery row for OVERSTIMULATED */
        div:has(.recovery-buttons-overstim) + div .stButton > button {
            background: linear-gradient(180deg, #fde047 0%, #facc15 42%, #eab308 100%) !important;
            color: #1a1404 !important;
            border: 1px solid #fef08a !important;
            border-radius: 14px !important;
            box-shadow:
                0 0 0 1px rgba(234, 179, 8, 0.35),
                0 10px 26px rgba(234, 179, 8, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.65) !important;
            text-shadow: none !important;
        }
        div:has(.recovery-buttons-overstim) + div .stButton > button:hover {
            filter: brightness(1.05) saturate(1.08) !important;
            box-shadow:
                0 0 28px rgba(250, 204, 21, 0.65),
                0 12px 30px rgba(202, 138, 4, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.75) !important;
        }
        .follow-card {padding: 0 0 0.35rem 0; margin-bottom: 0.35rem;}
        .follow-label {color:#7b61c8; font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.25rem;}
        .follow-question {font-size:1.05rem; font-weight:800; color:#212735; margin-bottom:0.5rem;}
        .stButton > button {
            width: 100%;
            background: linear-gradient(180deg, #52ff1b 0%, #24de5f 100%) !important;
            color: #09130a !important;
            border: 1px solid rgba(255,255,255,0.85) !important;
            border-radius: 14px !important;
            font-weight: 1000 !important;
            min-height: 2.38rem !important;
            padding-top: 0.42rem !important;
            padding-bottom: 0.42rem !important;
            box-shadow: 0 0 0 1px rgba(0,0,0,0.02), 0 10px 22px rgba(37, 211, 102, 0.18), inset 0 1px 0 rgba(255,255,255,0.55) !important;
        }
        .stButton > button:hover {filter: brightness(1.03); box-shadow: 0 14px 28px rgba(37,211,102,0.24), inset 0 1px 0 rgba(255,255,255,0.65) !important;}

        .recovery-buttons-marker { display: none; }

        /* Post-failure recovery: vivid purple / neon (distinct from green primaries) */
        div:has(.recovery-buttons-marker) + div .stButton > button,
        div:has(.gameover) + div + div .stButton > button {
            background: linear-gradient(175deg, #8b5cf6 0%, #6d28d9 38%, #4c1d95 100%) !important;
            color: #f5f3ff !important;
            border: 1px solid #c4b5fd !important;
            border-radius: 14px !important;
            box-shadow:
                0 0 22px rgba(139, 92, 246, 0.7),
                0 0 48px rgba(109, 40, 217, 0.4),
                0 8px 24px rgba(30, 20, 60, 0.25),
                inset 0 1px 0 rgba(255,255,255,0.38),
                inset 0 -1px 0 rgba(30, 20, 80, 0.25) !important;
            text-shadow: 0 0 14px rgba(196, 181, 253, 0.55) !important;
        }
        div:has(.recovery-buttons-marker) + div .stButton > button:hover,
        div:has(.gameover) + div + div .stButton > button:hover {
            filter: brightness(1.1) saturate(1.12) !important;
            box-shadow:
                0 0 32px rgba(167, 139, 250, 0.9),
                0 0 56px rgba(124, 58, 237, 0.5),
                inset 0 1px 0 rgba(255,255,255,0.5) !important;
        }
        label, .stSelectbox label, .stTextInput label {color: #1f2734 !important; font-weight: 800 !important; opacity: 1 !important;}
        .status-box {padding: 0; margin-bottom: 0.45rem;}
        .delta-chip {font-weight:900; font-size:0.9rem; margin-left:0.35rem;}
        .builder-title {font-size:1.32rem; font-weight:1000; color:#1b2330; margin-bottom:0.14rem;}
        .builder-sub {color:#586277; margin-bottom:0.48rem; font-size:0.91rem;}
        .stMarkdown p {margin-bottom: 0.28rem;}
        /* Builder: light tightening only (keeps laptop fit without ultra-dense UI) */
        div[data-testid="stVerticalBlock"]:has(.builder-title) > div > [data-testid="stElementContainer"] {margin-bottom: 0.2rem !important;}
        div[data-testid="stVerticalBlock"]:has(.builder-title) {gap: 0.5rem !important;}
        .builder-preview .section-title {margin-bottom: 0.28rem !important; font-size: 0.84rem !important;}
        .builder-preview .hero-avatar {font-size: 2.85rem !important; margin-bottom: 0.06rem !important;}
        .builder-preview .hero-name {font-size: 1.52rem !important; margin-bottom: 0.32rem !important;}
        .builder-preview .summary-line {font-size: 0.88rem !important; margin: 0.12rem 0 !important;}
        .builder-preview .tiny {font-size: 0.82rem !important; margin-top: 0.22rem !important;}

        .relationship-pill {
            display: inline-block; font-weight: 900; font-size: 0.94em;
            padding: 0.1rem 0.55rem; border-radius: 999px;
            background: linear-gradient(180deg, rgba(255,255,255,0.65), rgba(232,230,242,0.75));
            border: 1px solid rgba(185,180,210,0.4);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);
        }
        .crow-brain-card {
            margin-top: 0.55rem;
            margin-bottom: 0.65rem;
            padding: 0.55rem 0.7rem;
            border-radius: 16px;
            background: linear-gradient(175deg, rgba(255,255,255,0.6), rgba(236,234,244,0.64));
            border: 1px solid rgba(200,195,220,0.30);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.86), 0 8px 20px rgba(19,24,36,0.05);
        }
        .crow-brain-title {
            font-size: 0.75rem; font-weight: 1000; letter-spacing: 0.12em;
            text-transform: uppercase; color: #5b5f72; margin-bottom: 0.28rem;
        }
        .crow-brain-line { font-size: 0.82rem; color: #2a3140; line-height: 1.35; margin-bottom: 0.18rem; }

        .character-sheet {
            margin-top: 0.85rem; padding: 0.65rem 0.72rem 0.62rem 0.72rem;
            border-radius: 16px;
            background: linear-gradient(175deg, rgba(255,255,255,0.62), rgba(236,234,244,0.66));
            border: 1px solid rgba(200,195,220,0.34);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.88), 0 8px 22px rgba(19,24,36,0.06);
        }
        .character-card-name {
            font-size: 1.08rem; font-weight: 1000; color: #141a24; letter-spacing: 0.02em;
            margin-bottom: 0.5rem; padding-bottom: 0.4rem;
            border-bottom: 1px solid rgba(170,175,195,0.38);
        }
        .character-sheet-line { font-size: 0.81rem; color: #2a3140; line-height: 1.42; margin-bottom: 0.1rem; }
        .cs-k { color: #6b7080; font-weight: 800; margin-right: 0.32rem; }

        /* chrome cards */
        div[data-testid="stVerticalBlock"] > div:has(> div > .section-title),
        div[data-testid="stVerticalBlock"] > div:has(> div > .builder-title),
        div[data-testid="stVerticalBlock"] > div:has(> div > .gameover) {
            background: linear-gradient(175deg, rgba(255,255,255,0.88), rgba(236,234,246,0.76));
            border: 1px solid rgba(200,195,220,0.32);
            box-shadow:
                0 16px 40px rgba(19, 24, 36, 0.09),
                inset 0 1px 0 rgba(255,255,255,0.95),
                inset 0 -1px 0 rgba(150,155,175,0.06);
            border-radius: 20px;
            padding: 0.78rem 0.92rem 0.85rem 0.92rem;
            backdrop-filter: blur(18px);
        }

        div[data-baseweb="select"] > div {
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(238,235,248,0.96)) !important;
            color: #17202c !important;
            border: 1px solid rgba(200,190,220,0.3) !important;
            border-radius: 14px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.78), 0 6px 18px rgba(17,24,39,0.05);
        }
        div[data-baseweb="select"] svg {fill:#5b6475 !important;}

        .stTextInput input {
            background: linear-gradient(180deg, rgba(255,255,255,0.93), rgba(238,235,248,0.96)) !important;
            color: #17202c !important;
            border-radius: 14px !important;
            border: 1px solid rgba(200,190,220,0.28) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.78), 0 6px 18px rgba(17,24,39,0.05);
        }

        .stat-row { margin-bottom: 0.78rem; }
        .stat-label-line {
            color: #1a2230; font-size: 0.96rem; margin-bottom: 0.36rem; line-height: 1.35;
        }
        .stat-label-line b { font-weight: 900; }
        .stat-value { font-weight: 1000; font-size: 1.05rem; }
        .stat-bar-track {
            width: 100%;
            max-width: 100%;
            background: linear-gradient(180deg, #e8eef8, #dce6f4);
            border-radius: 999px;
            height: 12px;
            overflow: hidden;
            box-sizing: border-box;
            box-shadow: inset 0 1px 2px rgba(15,23,42,0.06);
        }
        .stat-bar-fill {
            background: linear-gradient(90deg, var(--stat-bar-fill-start), var(--stat-bar-fill-end));
            height: 100%;
            min-height: 12px;
            width: 0%;
            border-radius: 999px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(240,238,248,0.96));
        }

        .scenario-picker-title { text-align: center; margin-bottom: 0.12rem !important; }
        .scenario-picker-sub { text-align: center; margin-bottom: 1rem !important; }
        .scenario-picker-meta {
            text-align: center; color: #596579; font-size: 0.86rem;
            padding: 0.35rem 0.5rem 0.5rem;
        }
        .scenario-card {
            box-sizing: border-box;
            width: 100%;
            min-height: 7.75rem;
            padding: 1rem 1.05rem 0.95rem;
            margin-bottom: 0.5rem;
            border-radius: 16px;
            border: 1px solid rgba(200,195,220,0.42);
            background: linear-gradient(175deg, rgba(255,255,255,0.92), rgba(236,234,246,0.78));
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.95),
                0 10px 26px rgba(19, 24, 36, 0.07);
        }
        .scenario-card__title {
            margin: 0 0 0.45rem 0;
            font-size: 1.08rem;
            font-weight: 1000;
            color: #1b2330;
            letter-spacing: 0.02em;
        }
        .scenario-card__desc {
            margin: 0;
            font-size: 0.88rem;
            line-height: 1.45;
            color: #465061;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

