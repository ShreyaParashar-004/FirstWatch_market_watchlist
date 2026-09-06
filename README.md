# FirstWatch

> **Tell me what is starting to matter before it becomes obvious.**

FirstWatch is a market watchlist platform designed to help users understand **what is changing around the companies and themes they care about, and whether the market has started reacting to it.**

Instead of continuously scanning information about every company, users build their own watchlist by adding **companies or broader themes** they are interested in — such as solar power, oil, pharmaceuticals, battery storage, or sustainable energy.

FirstWatch then monitors relevant information and separates two different questions:

* **Developments** — What is happening around the world that could be relevant to something the user is watching?
* **Market Tracking** — What changes have actually occurred in the market based on observed data?

This separation is central to the product.

A development and a subsequent market movement are **not automatically treated as cause and effect**. FirstWatch provides the supporting information and shows the actual market movement separately, allowing the user to understand the relationship without presenting an unsupported conclusion as fact.

---

## Why FirstWatch?

A traditional watchlist can tell you what a stock is doing.

It does not necessarily tell you **what happened that might explain why attention should be paid to it.**

FirstWatch combines a user-controlled watchlist with information retrieval, structured analysis, evidence, notifications, and independent market tracking.

The goal is simple:

> **Help users identify what deserves their attention.**

---

## Core Experience

### 1. Watch

Users decide what they want to follow.

A watchlist can contain:

* Individual companies
* Broader themes and areas of interest

The system does not silently add companies or topics to the user's watchlist.

### 2. Detect

FirstWatch retrieves recent information from real sources and checks it against the user's watch context.

Information is filtered for relevance and duplicate information is removed before AI analysis.

### 3. Analyze

Relevant information is provided to the AI together with the user's watch context.

The resulting structured analysis can include:

* Development/event type
* Relevant companies/entities
* Sentiment
* Potential impact
* Impact direction
* Time horizon
* Confidence
* Explanation
* Supporting evidence

The AI does **not** independently generate the underlying market or news information.

### 4. Alert

When genuinely new and relevant activity is detected, FirstWatch can generate an **in-app notification** for the user.

### 5. Explain

Each development is connected to the information from which it was derived.

The system preserves source information such as:

* Source
* Article title
* URL
* Publication time
* Supporting content

This keeps the analysis traceable to retrieved information.

### 6. Track

Market tracking is deliberately separate from the information-analysis process.

FirstWatch retrieves real market observations, stores timestamped observations, and calculates market movement from those observations.

This allows users to see:

**What happened in the world**

separately from:

**What happened in the market.**

---

## Architecture

FirstWatch uses two independent pipelines.

### Market Tracking

```text
Market Provider
      ↓
Market Observations
      ↓
Change Detection
      ↓
Tracking API
      ↓
Frontend
```

### Information & Analysis

```text
Watchlist
      ↓
Information Retrieval
      ↓
Relevance / Entity Matching
      ↓
De-duplication
      ↓
AI Analysis
      ↓
Result Processing
      ↓
Developments API
      ↓
Notifications
```

The separation is intentional.

Market data and external information have different failure modes, update patterns, and trust requirements. Neither pipeline needs the other in order to function.

---

## Evidence First

FirstWatch follows an **evidence-first** approach.

The system retrieves information first and only then asks the AI to interpret the supplied evidence.

```text
Retrieved information
        ↓
Relevance filtering
        ↓
Entity matching
        ↓
De-duplication
        ↓
Structured AI analysis
        ↓
Development + supporting evidence
```

The AI-generated text is therefore **not treated as a source of truth**.

The model is constrained to work from the supplied evidence and cannot invent:

* Sources
* URLs
* Publication dates
* Events
* Companies
* Market prices
* Financial information

---

## Data Sources

| Purpose                      | Source          |
| ---------------------------- | --------------- |
| Market observations          | Yahoo Finance   |
| Information retrieval        | Google News RSS |
| Structured AI analysis       | Groq            |
| Authentication & persistence | Supabase        |

### Market Data

FirstWatch uses Yahoo Finance for market observations.

Timestamped observations are stored rather than relying only on a single current quote. Market movement is then calculated from the observed data.

### Information Retrieval

Google News RSS provides recent article information and metadata without requiring a paid news API.

Retrieved information is filtered before being sent for AI analysis to reduce unnecessary model usage.

### AI Analysis

The current implementation uses Groq for fast structured analysis.

AI analysis is separated behind a provider layer so that the underlying model can be changed without redesigning the rest of the application.

---

## Reliability & Failure Isolation

The application is designed so that one external dependency does not unnecessarily break another part of the product.

### Information / AI failure

Market tracking can continue independently using stored market observations.

### Market-data failure

Previously stored observations can remain available where possible, with stale/unavailable data indicated instead of fabricating a current value.

### AI unavailable

The system can fall back to a basic relevant-information result rather than inventing an AI explanation.

The principle is:

> **Never manufacture information just to make the interface look complete.**

---

## Authentication & User Isolation

Authentication and persistent user state are handled through Supabase.

Row Level Security (**RLS**) ensures that user-specific information remains isolated between users.

This includes:

* User profiles
* Watchlists
* Watchlist items
* Developments
* Notifications
* User checkpoint state

The canonical state is stored server-side so that it persists across browser refreshes, sessions, and devices.

---

## Notifications

FirstWatch includes in-app notifications for genuinely new and relevant developments.

Notifications are:

* User-specific
* Deduplicated
* Tracked with unread/read state
* Connected to the underlying development
* Opened directly from the notification

The current implementation does not depend on SMS, email, or external push-notification infrastructure.

---

## What FirstWatch Does Not Do

The current version intentionally does **not** provide:

* Buy/sell recommendations
* Trading functionality
* Guaranteed price predictions
* Fabricated financial information
* AI-generated news
* Portfolio analytics
* Guaranteed returns

The system is designed to help users **find emerging information, understand its potential relevance, and separately observe actual market movement.**

---

## Technology Stack

### Frontend

* React
* TypeScript
* TanStack Start

### Backend

* Python
* FastAPI
* Uvicorn

### Database & Authentication

* Supabase
* PostgreSQL
* Supabase Auth
* Row Level Security (RLS)

### External Services

* Yahoo Finance
* Google News RSS
* Groq

---

## Project Structure

```text
FirstWatch/
│
├── FirstWatch_back/
│   ├── app/
│   ├── tests/
│   └── requirements.txt
│
├── FirstWatch_front/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── project-documentation/
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Running Locally

### Backend

```bash
cd FirstWatch_back
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The FastAPI backend runs on:

```text
http://127.0.0.1:8000
```

### Frontend

```bash
cd FirstWatch_front
npm install
npm run dev
```

The frontend runs on:

```text
http://localhost:8080
```

The frontend API configuration should point to the local FastAPI backend.

Required environment variables should be configured locally using `.env.example`.

---

## Testing

Backend tests:

```bash
cd FirstWatch_back
pytest
```

The core application flow is designed around:

```text
Sign up
   ↓
Login
   ↓
Add company/theme
   ↓
Refresh
   ↓
Watchlist persists
   ↓
View Developments
   ↓
View Market Tracking
   ↓
Remove from watchlist
   ↓
Logout
   ↓
Login again
```

---

## Future Work

The next stage of FirstWatch is a **Forecast Layer** built on the existing information and market-tracking infrastructure.

Planned areas include:

* Identifying emerging patterns before they become obvious in the market
* Estimating potential direction and time horizon
* Richer theme-to-company/entity mapping
* Broader information coverage
* Improved source ranking
* More advanced personalization

The current implementation establishes the foundations required for this layer through real information retrieval, evidence preservation, structured analysis, timestamped market observations, persistent user state, and independent processing pipelines.

---

## Project Status

**Initial working implementation**

FirstWatch currently provides:

* Multi-user authentication
* Persistent user watchlists
* Company and theme monitoring
* Real information retrieval
* Evidence-based structured analysis
* In-app notifications
* Real market-data tracking
* Historical market observations
* Independent information and market pipelines
* Server-side user isolation with RLS

The project is intentionally structured so that future intelligence and forecasting capabilities can build on the existing foundation without replacing the core architecture.
