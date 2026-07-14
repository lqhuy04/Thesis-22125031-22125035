# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

**Stockrium** — a Vietnamese stock analysis platform combining real-time market data, fundamental/technical analysis, news sentiment, and AI-generated investment recommendations. The project is split into a FastAPI backend and a React Native/Expo mobile frontend.

## Commands

### Frontend (`MyApp/`)

```bash
npm install          # Install dependencies
npm start            # Start Expo dev server
npm run android      # Run on Android emulator
npm run ios          # Run on iOS simulator
npm run web          # Run web version
npm run lint         # Run ESLint
```

### Backend (`backend/app/`)

```bash
pip install -r requirements.txt   # Install Python dependencies
python -m app.main                # Run FastAPI server (localhost:8000)
```

No test framework is currently configured for either project.

## Architecture

### Backend (`backend/app/`)

Three-layer structure: **routes → services → Supabase/SSI API**

- `routes/` — 8 FastAPI routers: `auth`, `market`, `fundamental_analysis`, `technical_indicators`, `articles`, `company`, `risk_appetite`, `agentic`
- `services/` — Business logic layer; each route module has a corresponding service
- `models/` — Pydantic schemas for request/response validation
- `middleware/auth_middleware.py` — JWT verification for protected routes
- `utils/` — password hashing (bcrypt), JWT creation/verification, email sending
- `config.py` — pydantic-settings, all env vars loaded from `.env`

**Standardized API response format:**

```json
{
  "data": {},
  "errorCode": 0,
  "errorDesc": "",
  "requestId": "uuid",
  "result": true
}
```

Error codes follow convention: HTTP status → code (e.g., 400 → 400001, 401 → 401001).

### AI Agent System (`backend/agentic_ai/`)

LangGraph `StateGraph` with 5 nodes sharing `AgentState` (TypedDict):

1. `orchestrator` — parses request, decides which agents to invoke
2. `fundamental_analysis_agent` — analyzes financial metrics
3. `technical_analysis_agent` — analyzes price patterns
4. `article_agent` — analyzes news sentiment
5. `aggregator` — merges results, calls OpenAI for structured `InvestmentRecommendation`

Agents run in parallel based on conditional edges from the orchestrator. User `risk_appetite` flows through the entire pipeline. System prompts and outputs are in Vietnamese.

### Frontend (`MyApp/`)

Expo Router (file-based routing). Path alias `@/*` maps to project root.

- `app/` — Screens (each file = a route): Home, Detail, Search, TradingViewScreen, RiskAppetite, Authentication, AllNews, NewDetail, Profile, Setting
- `components/` — Reusable UI: `market/`, `detail/`, `tradingView/`, `authentication/`, `ui/` (includes custom chart components: candle, line, bar, RSI, MACD, KDJ)
- `helpers/api/` — Centralized HTTP client with automatic JWT injection; service helpers per domain (market, fundamentals, company, search)
- `hooks/` — `ThemeContext` (dark/light), `LocalizationContext` (i18n)

Tokens are stored using `expo-secure-store` (encrypted).

## Key Environment Variables (Backend)

| Group       | Variables                                                                                              |
| ----------- | ------------------------------------------------------------------------------------------------------ |
| Database    | `SUPABASE_URL`, `SUPABASE_KEY`                                                                         |
| Auth        | `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`                                                  |
| OAuth       | `GOOGLE_CLIENT_ID/SECRET`,`GOOGLE_IOS_CLIENT_ID`, `GOOGLE_ANDROID_CLIENT_ID`, `FACEBOOK_APP_ID/SECRET` |
| Market data | `SSI_CONSUMER_ID`, `SSI_CONSUMER_SECRET`, `SSI_API_URL`, `SSI_STREAM_URL`                              |
| AI          | `OPENAI_API_KEY`, `GEMINI_API_KEY`                                                                     |
| Search      | `SERPER_API_URL`, `SERPER_API_KEY`                                                                     |
| Email       | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL`                                   |

See `backend/.env.example` for the full list.

## Tech Stack

**Backend:** FastAPI, Supabase (PostgreSQL), LangGraph, OpenAI, Google Gemini, SSI FC Data API, TA-Lib, pandas/numpy, Selenium + BeautifulSoup (scraping), PyJWT, bcrypt

**Frontend:** React Native 0.81, Expo 54, Expo Router, TypeScript, @shopify/react-native-skia, react-native-wagmi-charts, victory-native, react-native-reanimated, jwt-decode
