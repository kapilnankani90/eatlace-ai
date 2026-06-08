# Project Context: AI-Powered Restaurant Recommendation System

This document captures the full context of the Zomato-inspired milestone project. Use it as the single source of truth for scope, workflow, and deliverables.

---

## Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The system suggests restaurants from user preferences by combining **structured restaurant data** with a **Large Language Model (LLM)** to produce personalized, human-like recommendations.

---

## Primary Objective

Design and implement an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and more)
2. Uses a real-world restaurant dataset
3. Uses an LLM to generate personalized, natural-language recommendations
4. Presents clear, useful results to the user

---

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato restaurant data on Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |
| **Relevant fields** | Restaurant name, location, cuisine, cost, rating, and related attributes |

### Data Ingestion Responsibilities

- Load and preprocess the dataset from Hugging Face
- Extract fields needed for filtering and display (name, location, cuisine, cost, rating, etc.)

---

## User Input (Preferences)

Collect at minimum:

| Preference | Examples / Notes |
|------------|------------------|
| **Location** | Delhi, Bangalore, etc. |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese, etc. |
| **Minimum rating** | Numeric or threshold filter |
| **Additional** | family-friendly, quick service, or other free-text preferences |

---

## System Workflow

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ Data Ingestion  │ ──► │  User Input  │ ──► │ Integration Layer│ ──► │ Recommendation Engine│ ──► │ Output Display  │
│ (Hugging Face)  │     │ (preferences)│     │ filter + prompt  │     │ (LLM rank + explain) │     │ (top picks)     │
└─────────────────┘     └──────────────┘     └──────────────────┘     └─────────────────────┘     └─────────────────┘
```

### 1. Data Ingestion

- Load Zomato dataset from Hugging Face
- Preprocess and normalize fields for filtering and LLM context

### 2. User Input

- Gather location, budget, cuisine, minimum rating, and optional extra preferences

### 3. Integration Layer

- Filter restaurant records to match user input
- Prepare a structured subset for the LLM
- Build a prompt that enables the LLM to **reason** and **rank** options

### 4. Recommendation Engine (LLM)

The LLM should:

- **Rank** restaurants by fit to preferences
- **Explain** why each recommendation matches the user
- **Optionally** summarize the overall set of choices

### 5. Output Display

Present top recommendations in a user-friendly format including:

| Field | Source |
|-------|--------|
| Restaurant Name | Dataset |
| Cuisine | Dataset |
| Rating | Dataset |
| Estimated Cost | Dataset |
| Explanation | AI-generated (LLM) |

---

## Technical Expectations (Implicit)

- **Structured pipeline**: dataset → filter → prompt → LLM → formatted output
- **LLM role**: ranking, reasoning, and natural-language explanations—not replacing the dataset as the source of truth for facts
- **UX**: results should be readable and actionable (not raw JSON dumps unless that is an intermediate step)

---

## Success Criteria

- [ ] Dataset loads from Hugging Face and key fields are available
- [ ] User can specify location, budget, cuisine, rating, and optional preferences
- [ ] Filtering narrows candidates before LLM processing
- [ ] LLM produces ranked recommendations with explanations
- [ ] UI or output layer shows name, cuisine, rating, cost, and AI explanation

---

## Out of Scope (Unless Extended Later)

- Production deployment, auth, or payments
- Real-time Zomato API integration (dataset-only for this milestone)
- Non-restaurant recommendation domains

---

## Reference

- **Problem statement file**: `problemstatement.txt`
- **Dataset**: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

---

*Last derived from: `problemstatement.txt` — AI-Powered Restaurant Recommendation System (Zomato Use Case).*
