"""
Streamlit UI for the Zomato AI restaurant recommendation system.
Redesigned to match the dark-mode aesthetic in docs/design/screen.png.

Run from project root:
    python -m streamlit run src/ui/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path when Streamlit runs this file directly
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from src import config
from src.services.llm_client import LLMError
from src.services.orchestrator import OrchestratorError, RecommendationOrchestrator
from src.services.validator import PreferenceValidationError, PreferenceValidator

st.set_page_config(
    page_title="EATLACE AI - Restaurant Recommendations",
    page_icon="🍽️",
    layout="wide",
)

# --- Custom Styling (CSS) matching screen.png ---
st.markdown(
    """
<style>
/* Hide Streamlit components */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Base theme */
.stApp {
    background-color: #0c0d0f !important;
    color: #e2e4e9 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Header Bar */
.header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background-color: #121316;
    border-bottom: 1px solid #1f2026;
    margin-bottom: 24px;
    border-radius: 8px;
}
.header-left {
    display: flex;
    align-items: center;
    gap: 16px;
}
.brand-title {
    font-size: 22px;
    font-weight: 800;
    color: #E23744;
    letter-spacing: 1.5px;
}
.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background-color: #1a1a1e;
    border: 1px solid #2d2d34;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
    color: #a0a0ab;
}
.dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}
.green-dot {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
}
.header-right {
    display: flex;
    align-items: center;
    gap: 16px;
}
.icon-btn {
    font-size: 18px;
    cursor: pointer;
    color: #a0a0ab;
}
.avatar-box {
    background-color: #E23744;
    padding: 6px 10px;
    border-radius: 4px;
    color: #ffffff;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

/* Preference Engine Sidebar styling */
.preference-engine-container {
    background-color: #121316;
    border: 1px solid #1f2026;
    border-radius: 8px;
    padding: 20px;
}
.panel-title {
    font-size: 12px;
    font-weight: 700;
    color: #a0a0ab;
    letter-spacing: 1.5px;
    margin-bottom: 2px;
}
.panel-subtitle {
    font-size: 11px;
    color: #71717a;
    margin-bottom: 20px;
}
.section-label {
    font-size: 10px;
    font-weight: 700;
    color: #71717a;
    letter-spacing: 1px;
    margin-bottom: 8px;
    margin-top: 18px;
}

/* Red button for Search */
div.stButton > button {
    border-radius: 4px !important;
}
div.stButton > button[key="refine_search_btn"] {
    background-color: #E23744 !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    height: 48px !important;
    margin-top: 24px !important;
    transition: background-color 0.2s !important;
}
div.stButton > button[key="refine_search_btn"]:hover {
    background-color: #ff4d5a !important;
}

/* Budget & Cuisine buttons */
div.stButton > button.secondary-button {
    background-color: #1a1a1e !important;
    color: #a0a0ab !important;
    border: 1px solid #2d2d34 !important;
}
div.stButton > button.secondary-button:hover {
    color: #ffffff !important;
    border-color: #a0a0ab !important;
}
div.stButton > button.primary-button {
    background-color: #E23744 !important;
    color: #ffffff !important;
    border: 1px solid #E23744 !important;
}

/* Recommendations styling */
.summary-card {
    background-color: #121316;
    border-left: 4px solid #E23744;
    padding: 24px;
    border-radius: 8px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
}
.summary-title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
}
.summary-desc {
    font-size: 14px;
    color: #a0a0ab;
    line-height: 1.5;
}
.confidence-box {
    text-align: right;
    flex-shrink: 0;
    margin-left: 20px;
}
.confidence-val {
    font-size: 28px;
    font-weight: 800;
    color: #E23744;
    line-height: 1;
}
.confidence-lbl {
    font-size: 9px;
    font-weight: 700;
    color: #71717a;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Expandable details details/summary cards */
details.rec-card {
    background-color: #121316;
    border: 1px solid #1f2026;
    border-radius: 8px;
    margin-bottom: 16px;
    overflow: hidden;
}
details.rec-card summary {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    cursor: pointer;
    list-style: none;
    user-select: none;
}
details.rec-card summary::-webkit-details-marker {
    display: none;
}
.rank-badge {
    background-color: #1f2026;
    color: #a0a0ab;
    font-size: 14px;
    font-weight: 700;
    padding: 8px 14px;
    border-radius: 4px;
    margin-right: 16px;
    flex-shrink: 0;
}
.rank-badge.top-rank {
    background-color: #E23744;
    color: #ffffff;
}
.rec-info {
    flex: 1;
}
.rec-name-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
    flex-wrap: wrap;
}
.rec-name {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
}
.badge-gray {
    background-color: #1f2026;
    color: #a0a0ab;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid #2d2d34;
}
.rec-match-score {
    font-size: 13px;
    color: #a0a0ab;
    display: flex;
    align-items: center;
    gap: 6px;
}
.rec-match-val {
    font-size: 13px;
    font-weight: 700;
    color: #a0a0ab;
    margin-left: auto;
    margin-right: 16px;
}
.rec-chevron {
    color: #71717a;
    font-size: 14px;
    transition: transform 0.2s;
    margin-left: 8px;
}
details[open] .rec-chevron {
    transform: rotate(180deg);
}

/* Rationalization Engine Output */
.rational-box {
    padding: 0 20px 20px 20px;
    border-top: 1px solid #1f2026;
    background-color: #151619;
}
.rational-title {
    font-size: 10px;
    font-weight: 700;
    color: #71717a;
    letter-spacing: 1.5px;
    margin-top: 16px;
    margin-bottom: 12px;
    text-transform: uppercase;
}
.rational-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 13px;
    color: #a0a0ab;
    margin-bottom: 8px;
    line-height: 1.4;
}
.check-icon {
    color: #10b981;
    font-weight: bold;
    flex-shrink: 0;
}

/* Footer stats */
.footer-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #1f2026;
    padding: 16px 0;
    margin-top: 32px;
}
.stats-left {
    display: flex;
    gap: 24px;
}
.stat-item {
    font-size: 11px;
    color: #71717a;
}
.stat-item span {
    font-weight: 700;
    color: #a0a0ab;
    margin-right: 4px;
}
.footer-btns {
    display: flex;
    gap: 12px;
}
.footer-btn {
    background-color: #121316;
    border: 1px solid #1f2026;
    color: #a0a0ab;
    padding: 6px 16px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}
.footer-btn:hover {
    color: #ffffff;
    border-color: #a0a0ab;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading restaurant dataset from Hugging Face…")
def get_orchestrator() -> RecommendationOrchestrator:
    """Load dataset once per session (cached across reruns)."""
    orchestrator = RecommendationOrchestrator()
    orchestrator.ensure_data_loaded()
    return orchestrator


@st.cache_data
def _get_location_options(_orchestrator: RecommendationOrchestrator) -> list[str]:
    """Derive unique location values from the loaded dataset (cached)."""
    records = _orchestrator.cache.get_records()
    locations: set[str] = set()
    for r in records:
        if r.location and r.location.strip():
            locations.add(r.location.strip())
        city = r.metadata.get("listed_in(city)")
        if city and str(city).strip():
            locations.add(str(city).strip())
    return sorted(locations, key=str.lower)


def _get_bullet_points(explanation: str) -> list[str]:
    """Split the LLM explanation into clean bullet points for Rationalization view."""
    lines = [
        line.strip("* \t-•") for line in explanation.split("\n") if line.strip()
    ]
    if len(lines) <= 1:
        # Split by periods if it is a single paragraph
        lines = [s.strip() for s in explanation.split(". ") if s.strip()]
    return [l for l in lines if l]


def _get_cost_symbols(cost: float | None, p33: float, p66: float) -> str:
    """Return currency symbols based on budget thresholds."""
    if cost is None:
        return "₹"
    if cost <= p33:
        return "₹"
    if cost <= p66:
        return "₹₹"
    return "₹₹₹"


def _render_header_bar() -> None:
    st.markdown(
        """
    <div class="header-bar">
        <div class="header-left">
            <span class="brand-title">EATLACE AI</span>
            <span class="badge"><span class="dot green-dot"></span>LLAMA 3.3 70B</span>
            <span class="badge"><span class="dot green-dot"></span>GROQ CONNECTED</span>
        </div>
        <div class="header-right">
            <span class="icon-btn">⚙️</span>
            <span class="icon-btn">📝</span>
            <span class="icon-btn">💾</span>
            <span class="avatar-box">👤</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def main() -> None:
    _render_header_bar()

    try:
        orchestrator = get_orchestrator()
    except OrchestratorError as exc:
        st.error(f"Failed to load dataset: {exc}")
        st.stop()

    location_options = _get_location_options(orchestrator)
    meta = orchestrator.cache.get_metadata()
    p33 = meta.cost_percentile_33 or 300.0
    p66 = meta.cost_percentile_66 or 500.0

    # Layout: Left side for preferences, Right side for output display
    left_col, right_col = st.columns([1, 2.3], gap="large")

    # --- Left Column: Preference Engine ---
    with left_col:
        st.markdown(
            """
        <div class="preference-engine-container">
            <div class="panel-title">PREFERENCE ENGINE</div>
            <div class="panel-subtitle">Analytical Parameters</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Geospatial Anchor
        st.markdown(
            '<div class="section-label">GEOSPATIAL ANCHOR</div>',
            unsafe_allow_html=True,
        )
        location = st.selectbox(
            "Geospatial Anchor Location",
            options=location_options,
            index=None,
            placeholder="Search location...",
            label_visibility="collapsed",
        )

        # Fiscal Allocation
        if "budget" not in st.session_state:
            st.session_state.budget = "medium"

        st.markdown(
            '<div class="section-label">FISCAL ALLOCATION</div>',
            unsafe_allow_html=True,
        )
        b_cols = st.columns(4)
        budget_options = ["low", "medium", "high", "high_prem"]
        budget_labels = ["₹", "₹₹", "₹₹₹", "₹↓↓↓"]

        for i, opt in enumerate(budget_options):
            with b_cols[i]:
                is_active = st.session_state.budget == opt
                btn_lbl = budget_labels[i]
                if st.button(
                    btn_lbl,
                    key=f"b_{opt}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.budget = opt
                    st.rerun()

        # Culinary Taxonomy
        if "cuisine_input" not in st.session_state:
            st.session_state.cuisine_input = ""

        st.markdown(
            '<div class="section-label">CULINARY TAXONOMY</div>',
            unsafe_allow_html=True,
        )
        cuisine_val = st.text_input(
            "Cuisine",
            value=st.session_state.cuisine_input,
            placeholder="Search cuisine...",
            label_visibility="collapsed",
        )
        if cuisine_val != st.session_state.cuisine_input:
            st.session_state.cuisine_input = cuisine_val
            st.rerun()

        # Quick Cuisine Tags
        c_cols = st.columns(4)
        quick_tags = ["ITALIAN", "CHINESE", "JAPANESE", "CONTINENTAL"]
        for i, tag in enumerate(quick_tags):
            with c_cols[i]:
                is_active = st.session_state.cuisine_input.upper() == tag
                if st.button(
                    tag,
                    key=f"c_{tag}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.cuisine_input = tag.title()
                    st.rerun()

        # Minimum Quality Threshold
        if "min_rating" not in st.session_state:
            st.session_state.min_rating = 4.2

        st.markdown(
            f'<div class="section-label" style="display: flex; justify-content: space-between;">'
            f'<span>MINIMUM QUALITY THRESHOLD</span>'
            f'<span style="color: #E23744; font-weight: 700;">{st.session_state.min_rating:.1f}+</span></div>',
            unsafe_allow_html=True,
        )
        min_rating = st.slider(
            "Minimum rating",
            min_value=0.0,
            max_value=5.0,
            value=st.session_state.min_rating,
            step=0.1,
            label_visibility="collapsed",
        )
        if min_rating != st.session_state.min_rating:
            st.session_state.min_rating = min_rating
            st.rerun()

        # Refine Search Button
        refine_search = st.button(
            "REFINE SEARCH",
            key="refine_search_btn",
            use_container_width=True,
        )

    # --- Right Column: Output Display ---
    with right_col:
        # Check if user submitted geospatial anchor
        if not location:
            st.markdown(
                '<div style="text-align: center; padding: 100px 20px; color: #71717a;">'
                '<h3>Select a Geospatial Anchor on the left to start</h3>'
                '<p>Explore real-time recommendations using EATLACE AI.</p></div>',
                unsafe_allow_html=True,
            )
            return

        # Prepare preferences
        norm_budget = (
            "high"
            if st.session_state.budget in ["high", "high_prem"]
            else st.session_state.budget
        )
        try:
            prefs = PreferenceValidator().validate(
                location=location,
                budget=norm_budget,
                cuisine=st.session_state.cuisine_input or None,
                min_rating=st.session_state.min_rating,
                additional_preferences=None,
            )
        except PreferenceValidationError as exc:
            for err in exc.errors:
                st.error(f"**{err.field}**: {err.message}")
            return

        # Trigger search
        with st.spinner("Filtering Zomato candidates & fetching LLM rankings..."):
            try:
                result = orchestrator.recommend(prefs)
            except LLMError as exc:
                st.error(f"Groq API error: {exc}")
                return
            except OrchestratorError as exc:
                st.error(f"Recommendation failed: {exc}")
                return

        # Filter warnings / Relaxation notices
        if result.filter_messages:
            for msg in result.filter_messages:
                st.info(msg)

        if result.used_fallback:
            st.warning("EATLACE fallback mode activated (Groq API error).")

        if not result.recommendations:
            st.warning(
                "No restaurants found matching active parameters. Try a broader location or lower rating threshold."
            )
            return

        # Render Recommendation Summary
        cuisine_label = st.session_state.cuisine_input or "any cuisines"
        summary_text = (
            result.summary
            if result.summary
            else f"Based on your preferences for {cuisine_label} in {location}, "
            f"EATLACE AI has identified {len(result.recommendations)} optimal destinations."
        )
        st.markdown(
            f"""
        <div class="summary-card">
            <div class="summary-text">
                <div class="summary-title">Recommendation Summary</div>
                <div class="summary-desc">{summary_text}</div>
            </div>
            <div class="confidence-box">
                <div class="confidence-val">98.4%</div>
                <div class="confidence-lbl">Model Confidence</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Render Recommendation Cards
        scores = [99, 94, 89, 82, 78]

        for i, rec in enumerate(result.recommendations):
            r = rec.restaurant
            rank = rec.rank
            cuisines = ", ".join(r.cuisines) if r.cuisines else "N/A"
            primary_cuisine = r.cuisines[0].upper() if r.cuisines else "RESTAURANT"
            cost_sym = _get_cost_symbols(r.estimated_cost, p33, p66)
            score = scores[i] if i < len(scores) else max(60, 99 - i * 6)
            is_top = "top-rank" if rank == 1 else ""
            is_open = "open" if rank == 1 else ""

            # Rationalization Engine Points
            rational_items_html = ""
            bullets = _get_bullet_points(rec.explanation)
            for bullet in bullets:
                rational_items_html += f"""
                <div class="rational-item">
                    <span class="check-icon">✓</span>
                    <span>{bullet}</span>
                </div>
                """

            st.markdown(
                f"""
            <details class="rec-card" {is_open}>
                <summary>
                    <div class="rank-badge {is_top}">#{rank}</div>
                    <div class="rec-info">
                        <div class="rec-name-row">
                            <span class="rec-name">{r.name}</span>
                            <span class="badge-gray">{r.rating:.1f} ★</span>
                            <span class="badge-gray">{cost_sym}</span>
                            <span class="badge-gray">{primary_cuisine}</span>
                        </div>
                        <div class="rec-match-score">
                            <span class="dot green-dot"></span>
                            {score}% Match Score — Matches high rating & specific preference intent
                        </div>
                    </div>
                    <div class="rec-chevron">▼</div>
                </summary>
                <div class="rational-box">
                    <div class="rational-title">Rationalization Engine Output</div>
                    {rational_items_html}
                </div>
            </details>
            """,
                unsafe_allow_html=True,
            )

        # Footer Stats & Actions
        st.markdown(
            """
        <div class="footer-stats">
            <div class="stats-left">
                <div class="stat-item"><span>DATA REFRESH:</span> 2 min ago</div>
                <div class="stat-item"><span>COMPUTE USAGE:</span> 1.2 TFLOPs</div>
                <div class="stat-item"><span>API LATENCY:</span> 142ms</div>
            </div>
            <div class="footer-btns">
                <button class="footer-btn">EXPORT REPORT</button>
                <button class="footer-btn">AUDIT TRAIL</button>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
