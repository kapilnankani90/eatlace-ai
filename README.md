# AI-Powered Restaurant Recommendation System

Zomato-inspired milestone: load restaurant data from Hugging Face, normalize it, and cache for filtering and LLM recommendations (later phases).

## Prerequisites

- Python 3.10+
- Internet access (first run downloads ~575 MB dataset)

## Setup

```bash
cd "c:\zomato milestone"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Phase 1: Load dataset

```bash
python -m src.main --load-only
```

Optional flags:

- `--force` — reload even if cache is warm
- `--samples 5` — print more sample records

## Phase 2: Filter by preferences

```bash
python -m src.main --filter --location Bangalore --budget medium --cuisine Italian --min-rating 4.0
```

Optional: `--additional "family-friendly"`, `--cuisine "Italian and Chinese"`

If no exact match, the filter relaxes cuisine → rating → budget (see `edge-cases.md`).

## Phase 4: Full recommendations (orchestrator + Groq)

Set `GROQ_API_KEY` in `.env` ([Groq Console](https://console.groq.com/keys)), then:

```bash
python -m src.main --recommend --location Bangalore --budget medium --cuisine Italian --additional "family-friendly"
```

JSON output: add `--json`.

The orchestrator loads data → filters → calls **Groq** → parses results. Facts (name, rating, cost) always come from the dataset. On Groq or parse failure, the app falls back to top-rated matches.

## Phase 5: Web UI (FastAPI + Modern SPA)

The application features a modern Single Page Application (SPA) styled matching custom high-fidelity design specifications (screen 1 & 2):
- Dark glassmorphic inputs and crimson highlighting accents.
- Segmented budget selectors and quick cuisine taxonomy tags.
- Detailed step-by-step progress loaders showing filter pipelines.
- 2x2 grid layout of cards with collapsible match scores and AI explanations.

To start the FastAPI web server:

```bash
python -m uvicorn src.server:app --reload
```

Then open your browser to `http://localhost:8000`.

Requires `GROQ_API_KEY` in `.env` for AI recommendations.

### Legacy Web UI (Streamlit)

Alternatively, the older Streamlit app is still available and can be run with:

```bash
python -m streamlit run src/ui/app.py
```


## Run tests

Run the entire test suite locally:

```bash
python -m pytest
```

To run tests with detailed output:

```bash
python -m pytest -v
```

To run a specific test file:

```bash
python -m pytest tests/test_filter.py -v
```

---

## Manual Test Matrix

Verify the recommendation system end-to-end using these 4 manual verification scenarios via either CLI or Streamlit UI:

| Scenario | Input Parameters | Expected Behavior | Edge Cases Handled |
|---|---|---|---|
| **1. Standard Run** | Location: `Bangalore`<br>Budget: `medium`<br>Cuisine: `Italian` | Returns top Italian restaurants in Bangalore under the 66th percentile (~600 cost) with AI explanations. | Proper candidate filtering & ranking. |
| **2. Cuisine Relaxation**| Location: `Bangalore`<br>Budget: `medium`<br>Cuisine: `NonExistentFood` | No exact matches for `NonExistentFood` found; automatically relaxes the cuisine filter and shows other cuisines in Bangalore, warning the user. | `F-01` (Zero matches → Relaxation). |
| **3. Rating Relaxation** | Location: `Bangalore`<br>Budget: `low`<br>Min Rating: `4.9` | Low budget + rating >= 4.9 is extremely rare/absent; relaxes rating filter (lowering by 0.5) to return lower rated candidates rather than crashing or returning empty. | `U-07` / `F-01` (Rating relaxation). |
| **4. Invalid Input rejection** | Location: `""`<br>Budget: `luxury` | Validator throws explicit user-friendly errors: Location cannot be empty, Budget must be low/medium/high/cheap/pricey. | `U-01` & `U-04` (Input Validation). |

---

## Demo Walkthrough Script (2-Minute Video/Live Demo Guide)

1. **Prerequisites Verification**: Ensure `.env` is populated with a valid `GROQ_API_KEY`.
2. **Start the Web Application**: Run `python -m uvicorn src.server:app`. A terminal message will indicate the server is running. Open `http://localhost:8000`.
3. **Show Data Ingestion UI**: Observe the server output indicating Hugging Face dataset is being loaded into the memory cache.
4. **Run Scenario 1 (Positive Case)**:
   - Select `Indiranagar, Bangalore` in Location.
   - Choose `Medium` (or low/premium) in Budget.
   - Type or select a quick tag like `Italian` in Cuisine.
   - Click **Get AI Recommendations**.
   - Show the loading steps:
     - Applying filters...
     - Ranking results with Neural Model...
     - Generating explanations...
   - Show the results: 2x2 grid of cards showing rank badges, match percentages (e.g. #1 100% MATCH), restaurant details, and the "Why AI Picked It" explanation blocks.
5. **Run Scenario 2 (Relaxation Fallback)**:
   - Search for an invalid cuisine or broad filters.
   - Observe the relaxed options banners and fallback mechanisms.
6. **Show CLI fallback**: Run a quick terminal check showing same results:
   ```bash
   python -m src.main --recommend --location Bangalore --budget medium --cuisine Italian
   ```


---

## Project layout

```text
src/
  config.py
  main.py             # CLI (--load-only, --filter, --recommend)
  models/
    restaurant.py
    preferences.py    # UserPreferences, Budget
  data/
    ingestion.py
    normalizer.py
    cache.py
  services/
    validator.py
    filter.py
    prompt_builder.py
    llm_client.py       # GroqLLMClient + MockLLMClient
    parser.py
    recommendation_engine.py
    orchestrator.py
    formatter.py
  ui/
    app.py              # Streamlit UI (Phase 5)
prompts/
  v1_system.txt
tests/
  test_normalizer.py
  test_cache.py
  test_ingestion.py
  test_filter.py
  test_validator.py
  test_prompt_builder.py
  test_parser.py
  test_recommendation_engine.py
  test_orchestrator.py
  test_formatter.py
```

## Documentation

- [context.md](context.md) — requirements
- [architecture.md](architecture.md) — system design
- [implementation-plan.md](implementation-plan.md) — phased build
- [edge-cases.md](edge-cases.md) — handling guide

## Dataset

[ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) (~51k rows)
