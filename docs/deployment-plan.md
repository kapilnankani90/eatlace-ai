# Streamlit Cloud Deployment Plan

This document outlines the steps and considerations for deploying the **Zomato AI Restaurant Recommendation System** (specifically the Streamlit UI at `src/ui/app.py`) to **Streamlit Community Cloud**.

---

## 1. Prerequisites

Before starting the deployment, ensure you have:
1. A **GitHub account** containing the repository.
2. A **Streamlit Community Cloud account** (free at [share.streamlit.io](https://share.streamlit.io/)) linked to your GitHub account.
3. A **Groq API key** from the [Groq Console](https://console.groq.com/keys) to power the AI recommendations.

---

## 2. Configuration & Secrets Management

Streamlit Cloud does not use `.env` files. Instead, it relies on **Streamlit Secrets** (`st.secrets`) for secure environment variable management.

### Local Mocking (for testing Streamlit configuration locally)
Create a file at `.streamlit/secrets.toml` (do not commit this to GitHub):
```toml
GROQ_API_KEY = "gsk_your_actual_groq_api_key"
LLM_MODEL = "llama-3.3-70b-versatile"
```

### Production Setup (on Streamlit Cloud)
When deploying the app, you will input these secrets in the Streamlit Cloud Console. They will be exposed to the application at runtime.

---

## 3. Step-by-Step Deployment Steps

1. **Commit and Push to GitHub**:
   Ensure all local changes are committed and pushed to your remote GitHub repository:
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Login to Streamlit Cloud**:
   Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.

3. **Deploy New App**:
   - Click the **"New app"** button.
   - Choose your repository from the list: `zomato-milestone` (or your repository's name).
   - Set the branch to `main` (or active branch).
   - Set the Main file path to: `src/ui/app.py`.

4. **Configure Advanced Settings (Secrets)**:
   - Click the **"Advanced settings..."** button before deploying.
   - In the **Secrets** text area, paste your secrets configuration:
     ```toml
     GROQ_API_KEY = "gsk_your_actual_groq_api_key"
     LLM_MODEL = "llama-3.3-70b-versatile"
     ```
   - Click **Save**.

5. **Deploy**:
   - Click **"Deploy!"**.
   - Streamlit Cloud will spin up a container, install the dependencies listed in `requirements.txt`, and launch the web server.

---

## 4. Resource & Operational Constraints

Deploying to Streamlit Community Cloud introduces certain resource caps that our app is designed to handle:

### A. Memory Limitations (1GB RAM Cap)
* **Dataset Size**: The Zomato Hugging Face dataset is ~575 MB in raw format.
* **Optimization**: Our normalizer deduplicates the records from 51,717 down to **12,143 records** during normalization. In-memory storage of normalized `RestaurantRecord` objects takes less than **100MB of RAM**, which fits safely within Streamlit Cloud's 1GB limit.
* **Cache Management**: The `@st.cache_resource` decorator caches the `RecommendationOrchestrator` globally across all user sessions. The dataset is downloaded and processed **exactly once** on app startup, saving container memory and CPU cycles.

### B. Startup Time (Cold Starts)
* The first visitor to the app after a restart will experience a delay (~15–30 seconds) while the Hugging Face dataset is downloaded and normalized.
* Subsequent visitors will load the page instantly as the cached dataset is served directly from memory.

### C. Groq Rate Limits
* Streamlit Cloud shares network resources. Ensure your Groq API key is not hitting rate limits (429 errors). We recommend using `llama-3.3-70b-versatile` or `llama-3.1-8b-instant` for faster completions.
