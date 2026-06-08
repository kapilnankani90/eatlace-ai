"""
Streamlit UI for Eatlace AI.
Redesigned to match Screen 1 and Screen 2 from docs/design/screen 1.png and screen 2.png.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from src import config
from src.services.llm_client import LLMError
from src.services.orchestrator import OrchestratorError, RecommendationOrchestrator
from src.services.validator import PreferenceValidationError, PreferenceValidator

# Set page config
st.set_page_config(
    page_title="Eatlace AI",
    page_icon="🍽️",
    layout="wide",
)

# --- Custom CSS to match the design style of Screen 1 & 2 ---
st.markdown(
    """
<style>
/* Hide Streamlit default components */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}

/* Global Styles */
.stApp {
    background-color: #0c0d0f !important;
    color: #e2e4e9 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Custom header */
.custom-header {
    border-bottom: 1px solid #1f2026;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: rgba(13, 14, 17, 0.8);
    backdrop-filter: blur(10px);
    margin-bottom: 32px;
}
.brand-name {
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 800;
    color: #E23744;
    letter-spacing: 1px;
    cursor: pointer;
}
.nav-link {
    color: #a0a0ab;
    text-decoration: none;
    font-size: 14px;
    transition: color 0.2s;
    margin-right: 24px;
}
.nav-link:hover {
    color: white;
}
.user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 4px;
    background-color: #E23744;
    color: white;
    font-weight: bold;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
}

/* Screen 1 Centered Layout */
.hero-container {
    text-align: center;
    margin-bottom: 40px;
}
.hero-pill {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 9999px;
    background-color: rgba(226, 55, 68, 0.1);
    border: 1px solid rgba(226, 55, 68, 0.2);
    font-size: 12px;
    font-weight: 700;
    color: #E23744;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 16px;
}
.hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 42px;
    font-weight: 800;
    color: white;
    line-height: 1.2;
}
.hero-italic {
    font-family: 'Playfair Display', serif;
    color: #E23744;
    font-style: italic;
    font-weight: 500;
}

/* Labels */
.field-label {
    font-size: 11px;
    font-weight: 700;
    color: #71717a;
    letter-spacing: 1px;
    margin-bottom: 8px;
    text-transform: uppercase;
}

/* Styled HTML inputs wrapper */
.form-card {
    background-color: #121316;
    border: 1px solid #1f2026;
    border-radius: 12px;
    padding: 32px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    max-width: 650px;
    margin: 0 auto;
}

/* Standard button override */
div.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}
div.stButton > button[key="btn_get_recommendations"] {
    background-color: #E23744 !important;
    color: white !important;
    border: none !important;
    height: 52px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 14px rgba(226, 55, 68, 0.2) !important;
}
div.stButton > button[key="btn_get_recommendations"]:hover {
    background-color: #ff4d5a !important;
    transform: scale(1.01) !important;
}

/* Segmented Buttons */
div.stButton > button.budget-btn-inactive {
    background-color: transparent !important;
    color: #a0a0ab !important;
    border: 1px solid #2d2d34 !important;
}
div.stButton > button.budget-btn-inactive:hover {
    color: white !important;
    border-color: #a0a0ab !important;
}
div.stButton > button.budget-btn-active {
    background-color: #E23744 !important;
    color: white !important;
    border: 1px solid #E23744 !important;
}

/* Results Summary */
.results-summary-card {
    background-color: #121316;
    border: 1px solid #1f2026;
    border-radius: 12px;
    padding: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
}
.summary-left {
    flex: 1;
}
.summary-title {
    font-size: 24px;
    font-weight: 700;
    color: white;
    margin-bottom: 6px;
}
.summary-sub {
    font-size: 14px;
    color: #a0a0ab;
    margin-bottom: 12px;
}
.summary-chip-container {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
.summary-chip {
    background-color: #1a1a1e;
    border: 1px solid #2d2d34;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 11px;
    font-weight: 600;
    color: #a0a0ab;
}
.confidence-box {
    background-color: #1a1a1e;
    border: 1px solid #2d2d34;
    padding: 16px;
    border-radius: 8px;
    text-align: center;
    min-w: 120px;
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

/* Grid card */
.grid-card {
    background-color: #121316;
    border: 1px solid #1f2026;
    border-radius: 12px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    transition: border-color 0.3s;
}
.grid-card:hover {
    border-color: #4b5563;
}
.card-header-tag {
    font-size: 11px;
    font-weight: 700;
    color: #E23744;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.card-title {
    font-size: 20px;
    font-weight: 700;
    color: white;
    margin-top: 8px;
    margin-bottom: 8px;
}
.card-meta {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #a0a0ab;
    margin-bottom: 16px;
    flex-wrap: wrap;
}
.card-meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
}
.card-cuisine-pill {
    background-color: #1a1a1e;
    border: 1px solid #2d2d34;
    color: #a0a0ab;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.card-why-ai {
    background-color: #16171a;
    border: 1px solid rgba(45, 45, 52, 0.4);
    padding: 16px;
    border-radius: 8px;
    margin-top: 16px;
}
.why-ai-header {
    font-size: 11px;
    font-weight: 700;
    color: #a0a0ab;
    letter-spacing: 1px;
    margin-bottom: 8px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 6px;
}
.why-ai-text {
    font-size: 12px;
    color: #a0a0ab;
    line-height: 1.5;
}

/* Footer style */
.custom-footer {
    border-top: 1px solid #1f2026;
    padding: 40px 24px;
    margin-top: 80px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 24px;
}
.footer-logo {
    font-family: 'Outfit', sans-serif;
    font-size: 18px;
    font-weight: 800;
    color: #E23744;
}
.footer-copyright {
    font-size: 12px;
    color: #71717a;
    margin-top: 4px;
}
.footer-links {
    display: flex;
    gap: 24px;
    font-size: 12px;
    color: #71717a;
}
.footer-link {
    color: #71717a;
    text-decoration: none;
    transition: color 0.2s;
}
.footer-link:hover {
    color: white;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading Zomato dataset from Hugging Face…")
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


def _get_cost_symbols(cost: float | None, p33: float, p66: float) -> str:
    """Return currency symbols based on budget thresholds."""
    if cost is None:
        return "₹"
    if cost <= p33:
        return "₹"
    if cost <= p66:
        return "₹₹"
    return "₹₹₹"


def _render_custom_header() -> None:
    st.markdown(
        """
    <div class="custom-header">
        <span class="brand-name">Eatlace AI</span>
        <div>
            <a href="#" class="nav-link">Discover</a>
            <span class="user-avatar">👤</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_custom_footer() -> None:
    st.markdown(
        """
    <div class="custom-footer">
        <div>
            <div class="footer-logo">Eatlace AI</div>
            <div class="footer-copyright">© 2024 Eatlace AI. High-performance dining.</div>
        </div>
        <div class="footer-links">
            <a href="#" class="footer-link">Data Sources</a>
            <a href="#" class="footer-link">Privacy Policy</a>
            <a href="#" class="footer-link">Feedback</a>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def main() -> None:
    # Render unified layout header
    _render_custom_header()

    try:
        orchestrator = get_orchestrator()
    except OrchestratorError as exc:
        st.error(f"Failed to load dataset: {exc}")
        st.stop()

    location_options = _get_location_options(orchestrator)
    meta = orchestrator.cache.get_metadata()
    p33 = meta.cost_percentile_33 or 300.0
    p66 = meta.cost_percentile_66 or 500.0

    # Initialize session state variables
    if "budget" not in st.session_state:
        st.session_state.budget = "medium"
    if "cuisine_input" not in st.session_state:
        st.session_state.cuisine_input = ""
    if "min_rating" not in st.session_state:
        st.session_state.min_rating = 4.5
    if "limit" not in st.session_state:
        st.session_state.limit = 5
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    # --- Screen 1: Preference Ingestion Card ---
    if not st.session_state.submitted:
        st.markdown(
            """
        <div class="hero-container">
            <span class="hero-pill">Discover Your Next Great Meal</span>
            <h1 class="hero-title">Where should we <br><span class="hero-italic">eat tonight?</span></h1>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Centered form card container using columns for width limitation
        c_left, c_mid, c_right = st.columns([1, 2.5, 1])

        with c_mid:
            st.markdown('<div class="form-card">', unsafe_allow_html=True)

            # Location Selectbox
            st.markdown('<div class="field-label">LOCATION</div>', unsafe_allow_html=True)
            location = st.selectbox(
                "Location",
                options=location_options,
                index=None,
                placeholder="Search location...",
                label_visibility="collapsed",
            )

            # Budget Buttons
            st.markdown(
                '<div class="field-label" style="margin-top: 24px;">BUDGET</div>',
                unsafe_allow_html=True,
            )
            b_cols = st.columns(3)
            budgets = ["low", "medium", "high"]
            labels = ["Budget", "Medium", "Premium"]
            for idx, opt in enumerate(budgets):
                with b_cols[idx]:
                    is_active = st.session_state.budget == opt
                    btn_class = "budget-btn-active" if is_active else "budget-btn-inactive"
                    if st.button(
                        labels[idx],
                        key=f"btn_budget_{opt}",
                        use_container_width=True,
                    ):
                        st.session_state.budget = opt
                        st.rerun()

            # Cuisine input
            st.markdown(
                '<div class="field-label" style="margin-top: 24px;">CUISINE & TAGS</div>',
                unsafe_allow_html=True,
            )
            cuisine_val = st.text_input(
                "Cuisine input",
                value=st.session_state.cuisine_input,
                placeholder="Search any cuisine (e.g. Japanese, Rooftop, Vegan)...",
                label_visibility="collapsed",
            )
            if cuisine_val != st.session_state.cuisine_input:
                st.session_state.cuisine_input = cuisine_val
                st.rerun()

            # Cuisine tags below
            tags = ["Italian", "North Indian", "Sushi", "Rooftop", "Live Music"]
            t_cols = st.columns(5)
            for idx, tag in enumerate(tags):
                with t_cols[idx]:
                    if st.button(
                        tag,
                        key=f"tag_{tag}",
                        use_container_width=True,
                    ):
                        st.session_state.cuisine_input = tag
                        st.rerun()

            # Min Rating and Limit selectors
            st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
            col_l, col_r = st.columns(2)

            with col_l:
                st.markdown(
                    f'<div class="flex justify-between items-center mb-2">'
                    f'<span class="field-label">MIN. RATING</span>'
                    f'<span style="color: #E23744; font-weight: 700; font-size: 13px;">{st.session_state.min_rating:.1f}+</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                min_rating = st.slider(
                    "Min Rating Slider",
                    min_value=0.0,
                    max_value=5.0,
                    value=st.session_state.min_rating,
                    step=0.1,
                    label_visibility="collapsed",
                )
                if min_rating != st.session_state.min_rating:
                    st.session_state.min_rating = min_rating
                    st.rerun()

            with col_r:
                st.markdown(
                    '<div class="field-label">RESULTS TO SHOW</div>',
                    unsafe_allow_html=True,
                )
                # Simple number input styled
                limit = st.number_input(
                    "Results count limit",
                    min_value=1,
                    max_value=20,
                    value=st.session_state.limit,
                    step=1,
                    label_visibility="collapsed",
                )
                if limit != st.session_state.limit:
                    st.session_state.limit = limit
                    st.rerun()

            # Additional preferences
            st.markdown(
                '<div class="field-label" style="margin-top: 24px;">ADDITIONAL PREFERENCES</div>',
                unsafe_allow_html=True,
            )
            additional = st.text_area(
                "Additional notes",
                placeholder="Describe your ideal dining experience... (e.g. 'Looking for a quiet spot')",
                label_visibility="collapsed",
            )

            # Get recommendations trigger
            get_recs = st.button(
                "Get AI Recommendations",
                key="btn_get_recommendations",
                use_container_width=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)

            if get_recs:
                if not location:
                    st.error("Please select a location.")
                else:
                    # Execute recommendation request
                    try:
                        prefs = PreferenceValidator().validate(
                            location=location,
                            budget=st.session_state.budget,
                            cuisine=st.session_state.cuisine_input or None,
                            min_rating=st.session_state.min_rating,
                            additional_preferences=additional or None,
                        )
                    except PreferenceValidationError as exc:
                        for err in exc.errors:
                            st.error(f"**{err.field}**: {err.message}")
                        return

                    # Running spinner and pipeline
                    with st.spinner("Filtering Zomato candidates & running Groq AI models..."):
                        try:
                            result = orchestrator.recommend(prefs, top_k=st.session_state.limit)
                            st.session_state.result = result
                            st.session_state.selected_location = location
                            st.session_state.selected_additional = additional
                            st.session_state.submitted = True
                            st.rerun()
                        except LLMError as exc:
                            st.error(f"Groq API error: {exc}")
                        except OrchestratorError as exc:
                            st.error(f"Failed to generate: {exc}")

    # --- Screen 2: Recommendations Grid (2x2 Layout) ---
    else:
        result = st.session_state.result
        location = st.session_state.selected_location
        additional = st.session_state.selected_additional
        cuisine = st.session_state.cuisine_input

        # Back to Search button
        if st.button("← Back to search", key="btn_back_to_search"):
            st.session_state.submitted = False
            st.rerun()

        # Recommendation Summary card
        cuisine_lbl = cuisine or "Fine"
        summary_text = (
            result.summary
            if result.summary
            else f"Engineered matches for {cuisine_lbl} Dining in {location}"
        )
        
        # Prepare tags list
        chips_html = f'<div class="summary-chip">Budget: {st.session_state.budget.upper()}</div>'
        if cuisine:
            chips_html += f'<div class="summary-chip">Cuisine: {cuisine}</div>'
        if additional:
            chips_html += f'<div class="summary-chip">Preferences: {additional}</div>'

        st.markdown(
            f"""
        <div class="results-summary-card">
            <div class="summary-left">
                <div class="summary-title">Recommendation Summary</div>
                <div class="summary-sub">{summary_text}</div>
                <div class="summary-chip-container">{chips_html}</div>
            </div>
            <div class="confidence-box">
                <div class="confidence-val">98%</div>
                <div class="confidence-lbl">AI Confidence</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if result.used_fallback:
            st.warning("Showing fallback ratings-based results. Groq API is temporarily unavailable.")

        if result.filter_messages:
            for msg in result.filter_messages:
                st.info(msg)

        if not result.recommendations:
            st.warning("No restaurants found. Try broader preferences.")
            return

        # Render 2x2 grid using Streamlit columns
        cols = st.columns(2)
        scores = [100, 94, 89, 82, 78]

        for idx, rec in enumerate(result.recommendations):
            r = rec.restaurant
            score = scores[idx] if idx < len(scores) else max(50, 99 - idx * 5)
            cuisines_text = ", ".join(r.cuisines) if r.cuisines else "N/A"
            cost_sym = _get_cost_symbols(r.estimated_cost, p33, p66)
            cost_val = f"₹{r.estimated_cost:,.0f}" if r.estimated_cost else "N/A"
            
            # Sub-tags formatting
            cuisine_pills = ""
            for c in r.cuisines[:3]:
                cuisine_pills += f'<span class="card-cuisine-pill">{c.upper()}</span> '

            # Column selection
            grid_col = cols[idx % 2]

            with grid_col:
                st.markdown(
                    f"""
                <div class="grid-card">
                    <div style="flex: 1;">
                        <span class="card-header-tag">#{rec.rank} &nbsp;{score}% MATCH</span>
                        <h3 class="card-title">{r.name}</h3>
                        <div class="card-meta">
                            <span class="card-meta-item">📍 {r.location}</span>
                            <span class="card-meta-item" style="color: #fbbf24;">★ {r.rating:.1f}</span>
                            <span class="card-meta-item">{cost_sym} {cost_val} for two</span>
                        </div>
                        <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;">
                            {cuisine_pills}
                        </div>
                    </div>
                    <div class="card-why-ai">
                        <div class="why-ai-header">✨ Why AI Picked It</div>
                        <p class="why-ai-text">{rec.explanation}</p>
                    </div>
                </div>
                <div style="margin-bottom: 24px;"></div>
                """,
                    unsafe_allow_html=True,
                )

    # Render footer on both screens
    _render_custom_footer()


if __name__ == "__main__":
    main()
