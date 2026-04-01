# FilingLens — SEC Intelligence Platform

A multi-agent system that performs institutional-grade SEC filing analysis. Users ask a question about any public company, and the system fetches real filings from EDGAR, analyzes how management language has shifted, correlates language signals with stock price performance, and delivers a structured Buy/Sell/Hold recommendation with evidence and visualizations.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
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

1. **SEC EDGAR API** (`fetch_filings.py`): Fetches real 10-Q and 10-K filings for any public company. The `get_cik_for_ticker()` function resolves tickers to CIK numbers, `fetch_recent_filings()` retrieves filing metadata from the EDGAR submissions API, and `fetch_filing_text()` downloads and parses the actual filing HTML — extracting the MD&A (Management Discussion & Analysis) and Risk Factors sections using BeautifulSoup. No API key required; EDGAR is a free public API with millions of filings.

2. **Yahoo Finance** (`fetch_prices.py`): Fetches up to 3 years of daily stock price data via the `yfinance` library. The `compute_returns_around_date()` function calculates 30-day and 60-day stock returns after each filing date, plus S&P 500 (SPY) returns as a benchmark.

Data collection is fully dynamic — the user's question determines which companies and filing types are fetched.

### Step 2: Explore and Analyze (EDA)

**Files:** `backend/agent_definitions/filing_nlp_agent.py`, `backend/agent_definitions/market_agent.py`, `backend/tools/analyze_language.py`, `backend/tools/compute_signal.py`

EDA is performed by **two specialized agents running in parallel**:

1. **Filing NLP Agent** (`filing_nlp_agent.py`): Calls the `fetch_and_analyze_filings` tool, which retrieves SEC filings and runs rule-based NLP analysis via `analyze_language.py`. The analysis computes:
   - **Uncertainty score**: Ratio of uncertainty/hedging words (may, might, risk, adverse, etc.) — function `compute_uncertainty_score()`
   - **Sentiment score**: Net confidence minus uncertainty, normalized — function `compute_sentiment_score()`
   - **Key risk phrases**: Sentences with highest uncertainty word density — function `extract_key_risk_phrases()`
   - **Quarterly trend**: Whether uncertainty is improving, deteriorating, or stable — function `compute_trend()`

2. **Market Signal Agent** (`market_agent.py`): Calls the `compute_market_signal` tool, which correlates filing language scores with subsequent stock returns via `compute_signal.py`. It computes:
   - 30/60-day stock returns after each filing date
   - Whether the stock outperformed the S&P 500
   - Historical accuracy of the uncertainty→underperformance signal — function `compute_signal_strength()`

Both agents run simultaneously via `asyncio.gather()` in the orchestrator, along with competitor filing analysis. The EDA adapts to different questions — different tickers, filing types, and competitor sets produce different tool calls and analyses.

### Step 3: Hypothesize

**Files:** `backend/agent_definitions/analyst_agent.py`, `backend/utils/chart_generator.py`, `backend/tools/compute_signal.py`

The **Analyst Agent** (`analyst_agent.py`) synthesizes all findings into an institutional-quality research memo:

- Calls `generate_analyst_memo` tool which runs `generate_recommendation()` to produce a Buy/Sell/Hold signal based on language trend direction, signal strength, and competitor comparison
- Generates a dual-axis matplotlib chart (`chart_generator.py`) showing uncertainty score vs stock price over time
- The LLM writes a complete research memo citing specific data points: uncertainty scores, return percentages, filing dates, and competitor comparisons
- Output is a structured `AnalystMemo` with recommendation, confidence level, key evidence bullets, historical context, and the full memo text

The hypothesis is always grounded in the collected data — every claim cites specific numbers from the EDA phase.

---

## Core Requirements

| Requirement | Implementation |
|---|---|
| **Frontend** | React + Tailwind CSS with dark financial terminal aesthetic. Components: `QueryBar`, `AgentSteps` (live reasoning), `SignalCard` (recommendation), `ChartView`, `EvidencePanel`. Located in `frontend/src/` |
| **Agent Framework** | OpenAI Agents SDK (`openai-agents`). All agents defined in `backend/agent_definitions/` using `Agent()` class with `function_tool` decorators |
| **Tool Calling** | Five tools: `fetch_and_analyze_filings`, `compute_market_signal`, `generate_analyst_memo` (agent tools), plus underlying utility functions in `backend/tools/` |
| **Non-Trivial Dataset** | SEC EDGAR contains millions of filings across all public companies. Each filing is thousands of pages. The system retrieves 4-6 filings per company and extracts key sections — far too large to dump into context |
| **Multi-Agent Pattern** | **Orchestrator → Parallel Fan-Out → Synthesis** pattern. The orchestrator (`backend/agent_definitions/orchestrator.py`) parses the question via a TickerParser agent, fans out to FilingNLPAgent + MarketSignalAgent in parallel via `asyncio.gather()`, then passes results to the AnalystAgent for synthesis. Four distinct agents with different system prompts and responsibilities |
| **Deployed** | Backend on Railway, frontend on Vercel |
| **README** | This document |

---

## Grab-Bag Features

### 1. Structured Output (2.5 pts)
**Files:** `backend/schemas/language_signal.py`, `backend/schemas/market_signal.py`, `backend/schemas/analyst_memo.py`

Every agent uses Pydantic models as its `output_type`:
- `FilingNLPAgent` → `LanguageSignal` (quarterly scores, trend, magnitude)
- `MarketSignalAgent` → `MarketSignal` (correlations, signal strength, accuracy)
- `AnalystAgent` → `AnalystMemo` (recommendation, evidence, memo, chart)

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
2. **Yahoo Finance API** for stock price data (`backend/tools/fetch_prices.py`)

---

## Architecture

```
User Question
     │
     ▼
┌─────────────┐
│ Orchestrator │ ── parses question via TickerParser agent
└──────┬──────┘
       │
       ├──────────────────────────┐  (parallel via asyncio.gather)
       ▼                          ▼
┌──────────────┐         ┌────────────────┐
│ FilingNLP    │         │ MarketSignal   │
│ Agent        │         │ Agent          │
│              │         │                │
│ EDGAR API    │         │ Yahoo Finance  │
│ NLP Analysis │         │ Return Correl. │
└──────┬───────┘         └───────┬────────┘
       │                          │
       └──────────┬───────────────┘
                  ▼
          ┌──────────────┐
          │ Analyst      │
          │ Agent        │
          │              │
          │ Synthesis    │
          │ Chart Gen    │
          │ Memo Writing │
          └──────┬───────┘
                 ▼
          AnalystMemo JSON
          (streamed to frontend)
```

---

## Example Questions

- "Should we be long or short on Nvidia going into next quarter?"
- "Is Apple's management tone improving or deteriorating?"
- "Compare Meta and Alphabet's recent filing language"
- "What does Microsoft's latest 10-K signal about their outlook?"
- "Which is a better buy: JPMorgan or Goldman Sachs?"

---

## Deployment

### Backend (Railway)
1. Connect GitHub repo to Railway
2. Set root directory to `backend`
3. Add `OPENAI_API_KEY` environment variable
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)
1. Connect GitHub repo to Vercel
2. Set root directory to `frontend`
3. Add `VITE_API_URL` environment variable pointing to Railway backend URL
4. Framework: Vite
