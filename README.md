# FilingLens — SEC Intelligence Platform

**Live Demo:** [https://filinglens-frontend-879618059262.us-central1.run.app](https://filinglens-frontend-879618059262.us-central1.run.app)

A multi-agent system that performs institutional-grade SEC filing analysis. Users ask a question about any public company, and the system fetches real filings from EDGAR, analyzes how management language has shifted, correlates language signals with stock price performance, and delivers a structured Buy/Sell/Hold recommendation with evidence and visualizations.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- GCP project with Vertex AI enabled (or a Google AI Studio API key)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI
# For local dev, also run: gcloud auth application-default login
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173` and the backend at `http://localhost:8000`.

---

## Data Analysis Lifecycle

### Step 1: Collect

**Files:** `backend/tools/fetch_filings.py`, `backend/tools/fetch_prices.py`

The system collects data from **two external sources** at runtime:

1. **SEC EDGAR API** (`fetch_filings.py`): Fetches real 10-Q and 10-K filings for any public company. The `get_cik_for_ticker()` function resolves tickers to CIK numbers, `fetch_recent_filings()` retrieves filing metadata from the EDGAR submissions API, and `fetch_filing_text()` downloads and parses the actual filing HTML — extracting the MD&A (Management Discussion & Analysis) and Risk Factors sections using BeautifulSoup. No API key required; EDGAR is a free public API with millions of filings. A single query fetches 18 filings (6 per company x 3 companies), totaling ~500K characters (~125K tokens) of filing text from a source of 3M+ characters of raw filing data.

2. **Yahoo Finance** (`fetch_prices.py`): Fetches up to 3 years of daily OHLCV stock price data via the `yfinance` library. The system computes 30/60-day post-filing returns, pre/post filing volatility, volume spikes, and comprehensive price statistics (total return, annualized volatility, max drawdown, Sharpe ratio) across the full 500+ trading day dataset. The `compute_returns_around_date()` function also benchmarks against the S&P 500 (SPY).

Data collection is fully dynamic — the user's question determines which companies and filing types are fetched.

### Step 2: Explore and Analyze (EDA)

**Files:** `backend/agent_definitions/filing_nlp_agent.py`, `backend/agent_definitions/market_agent.py`, `backend/tools/analyze_language.py`, `backend/tools/compute_signal.py`

EDA is performed by **two specialized agents running in parallel**:

1. **Filing NLP Agent** (`filing_nlp_agent.py`): Calls the `fetch_and_analyze_filings` tool, which retrieves SEC filings and runs rule-based NLP analysis via `analyze_language.py`. The analysis computes:
   - **Uncertainty score**: Ratio of uncertainty/hedging words (may, might, risk, adverse, etc.) scaled to 0-1 — function `compute_uncertainty_score()`
   - **Sentiment score**: Net confidence minus uncertainty, normalized to -1 to +1 — function `compute_sentiment_score()`
   - **Key risk phrases**: Sentences with highest uncertainty word density, filtered for boilerplate — function `extract_key_risk_phrases()`
   - **Quarterly trend**: Whether uncertainty is improving, deteriorating, or stable — function `compute_trend()`

2. **Market Signal Agent** (`market_agent.py`): Calls the `compute_market_signal` tool, which correlates filing language scores with subsequent stock returns via `compute_signal.py`. It computes:
   - 30/60-day stock returns after each filing date
   - Whether the stock outperformed the S&P 500
   - Pre/post filing volatility changes and volume spikes
   - Historical accuracy of the uncertainty-to-underperformance signal — function `compute_signal_strength()`

Both agents run simultaneously via `asyncio.gather()` in the orchestrator, along with competitor filing analysis. The EDA adapts to different questions — different tickers, filing types, and competitor sets produce different tool calls and analyses.

### Step 3: Hypothesize

**Files:** `backend/agent_definitions/analyst_agent.py`, `backend/utils/chart_generator.py`, `backend/tools/compute_signal.py`

The **Analyst Agent** (`analyst_agent.py`) synthesizes all findings into an institutional-quality research memo:

- The `generate_recommendation()` function in `compute_signal.py` produces a Buy/Sell/Hold signal with data-driven confidence computed from 6 factors: signal strength, trend magnitude, filing count, trend consistency, return spread, and competitor divergence
- Generates a dual-axis matplotlib chart (`chart_generator.py`) showing uncertainty score vs stock price over time
- The LLM writes a structured research memo with sections: Investment Thesis, Language Trend Analysis, Market Signal Analysis, Competitive Landscape, Risk Factors, and Conclusion
- Output includes recommendation, confidence level, key evidence bullets, historical context, competitor comparison, the full memo, and a chart

The hypothesis is always grounded in the collected data — every claim cites specific numbers from the EDA phase.

**Downloadable outputs:**
- Full research report (HTML, printable as PDF) with methodology, appendices, and data tables
- Filing sources CSV with direct EDGAR links
- Analysis scores CSV with quarterly uncertainty/sentiment data
- Raw data CSV with full dataset including extracted risk phrases

---

## Core Requirements

| Requirement | Implementation |
|---|---|
| **Frontend** | React + Tailwind CSS with dark financial terminal aesthetic. Components: `QueryBar`, `AgentSteps` (live reasoning), `SignalCard` (recommendation), `ChartView`, `EvidencePanel`, `DataSourcesPanel`, `HowItWorks`. Located in `frontend/src/` |
| **Agent Framework** | Google ADK (`google-adk`) with Gemini 2.0 Flash via Vertex AI. All agents defined in `backend/agent_definitions/` using `Agent()` class with plain Python function tools |
| **Tool Calling** | Three agent tools: `fetch_and_analyze_filings`, `compute_market_signal`, `generate_analyst_memo`. Plus underlying utility functions in `backend/tools/` for EDGAR fetching, price analysis, NLP, and signal computation |
| **Non-Trivial Dataset** | SEC EDGAR: 3M+ characters of filing text per query (18 filings across 3 companies). Each full 10-Q is ~168K chars / ~42K tokens — far too large to dump into context. Yahoo Finance: 500+ trading days of OHLCV per ticker with derived statistics computed across the full history |
| **Multi-Agent Pattern** | **Orchestrator → Parallel Fan-Out → Synthesis** pattern. The orchestrator (`backend/agent_definitions/orchestrator.py`) parses the question via a TickerParser agent, fans out to FilingNLPAgent + MarketSignalAgent in parallel via `asyncio.gather()`, then passes results to the AnalystAgent for synthesis. Four distinct agents with different system prompts and responsibilities |
| **Deployed** | Frontend: [filinglens-frontend-879618059262.us-central1.run.app](https://filinglens-frontend-879618059262.us-central1.run.app) / Backend API: [filinglens-api-879618059262.us-central1.run.app](https://filinglens-api-879618059262.us-central1.run.app) — both on GCP Cloud Run |
| **README** | This document |

---

## Grab-Bag Features

### 1. Structured Output (2.5 pts)
**Files:** `backend/schemas/language_signal.py`, `backend/schemas/market_signal.py`, `backend/schemas/analyst_memo.py`

Every agent is instructed to return typed JSON matching Pydantic model schemas:
- `FilingNLPAgent` → `LanguageSignal` schema (quarterly scores, trend, magnitude)
- `MarketSignalAgent` → `MarketSignal` schema (correlations, signal strength, accuracy)
- `AnalystAgent` → `AnalystMemo` schema (recommendation, evidence, memo, chart)

All inter-agent communication uses typed JSON schemas. The `TickerParser` agent also returns structured JSON for ticker extraction.

### 2. Data Visualization (2.5 pts)
**File:** `backend/utils/chart_generator.py` — function `generate_sentiment_vs_price_chart()`

Generates a professional dual-axis matplotlib chart:
- Left Y-axis: Uncertainty score over time (red line with markers)
- Right Y-axis: Stock price over time (green line)
- Competitor uncertainty scores as dashed lines
- Filing dates marked with vertical dotted lines
- Dark terminal aesthetic (#0f1117 background) matching the frontend
- Returned as base64 PNG and displayed in the frontend's `ChartView` component

### 3. Parallel Execution (2.5 pts)
**File:** `backend/agent_definitions/orchestrator.py` — function `run_analysis()`

The MarketSignalAgent and competitor FilingNLPAgent analyses run simultaneously using `asyncio.gather()`. For a query about NVDA with AMD and INTC as competitors, three agent runs execute in parallel:
1. MarketSignalAgent for NVDA
2. FilingNLPAgent for AMD
3. FilingNLPAgent for INTC

Results are awaited together and aggregated before being passed to the AnalystAgent.

### 4. Second Data Retrieval Method (2.5 pts)
The system uses two distinct data retrieval methods:
1. **SEC EDGAR API** for filing text (`backend/tools/fetch_filings.py`)
2. **Yahoo Finance API** for stock price data (`backend/tools/fetch_prices.py`) — computes total return, annualized volatility, max drawdown, Sharpe ratio, and volume analysis across the full price history

### 5. Artifacts (2.5 pts)
**File:** `frontend/src/components/EvidencePanel.jsx`

The system generates persistent downloadable outputs:
- **Full research report** (styled HTML, printable as PDF) with methodology, data tables, chart, appendices, and filing source links
- **Filing sources CSV** with direct EDGAR links to every filing analyzed
- **Analysis scores CSV** with quarterly uncertainty and sentiment data
- **Raw data CSV** with the complete dataset including extracted risk phrases and filing URLs

---

## Architecture

```
User Question
     |
     v
+-------------+
| Orchestrator | -- parses question via TickerParser agent (Gemini 2.0 Flash)
+------+------+
       |
       +------------------------------+  (parallel via asyncio.gather)
       v                              v
+--------------+             +----------------+
| FilingNLP    |             | MarketSignal   |
| Agent        |             | Agent          |
|              |             |                |
| EDGAR API    |             | Yahoo Finance  |
| NLP Analysis |             | Return Correl. |
+------+-------+             +-------+--------+
       |                              |
       +----------+-------------------+
                  v
          +--------------+
          | Analyst      |
          | Agent        |
          |              |
          | Synthesis    |
          | Chart Gen    |
          | Memo Writing |
          +------+-------+
                 v
          AnalystMemo JSON
          (streamed to frontend)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Agent Framework | Google ADK (`google-adk`) |
| LLM | Gemini 2.0 Flash via Vertex AI |
| Filing Data | SEC EDGAR API (free, no key needed) |
| Price Data | Yahoo Finance via `yfinance` (free) |
| NLP | Rule-based word frequency analysis (uncertainty/confidence word sets) |
| Charts | Matplotlib (base64 PNG, dual-axis) |
| Frontend | React 18 + Tailwind CSS + Vite |
| Deployment | GCP Cloud Run (backend + frontend) |

---

## Example Questions

- "Should we be long or short on Nvidia going into next quarter?"
- "Is Apple's management tone improving or deteriorating?"
- "Compare Meta and Alphabet's recent filing language"
- "What does Microsoft's latest 10-K signal about their outlook?"
- "Which is a better buy: JPMorgan or Goldman Sachs?"

---

## Deployment

Both services are deployed on **GCP Cloud Run** in `us-central1`.

| Service | URL |
|---|---|
| Frontend | https://filinglens-frontend-879618059262.us-central1.run.app |
| Backend API | https://filinglens-api-879618059262.us-central1.run.app |

### Redeploy Backend
```bash
cd backend
gcloud run deploy filinglens-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=agentic-ai-for-analytics,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE" \
  --memory 1Gi \
  --timeout 300 \
  --project agentic-ai-for-analytics
```

### Redeploy Frontend
```bash
cd frontend
gcloud run deploy filinglens-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 256Mi \
  --project agentic-ai-for-analytics
```

The frontend Dockerfile bakes in the backend API URL at build time. The backend uses Vertex AI with the Cloud Run service account — no API keys needed in production.
