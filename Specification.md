# AI Intelligence Hub — Technical Specification

## Project Overview

Build a hosted AI intelligence platform that automatically collects AI news and developments every morning, summarizes them using Gemini AI, stores the results in Neon PostgreSQL, and exposes a responsive dashboard accessible from desktop and mobile devices.

The system must be lightweight, maintainable, inexpensive to run, and optimized for rapid iteration.

---

# Objectives

The platform must:

1. Aggregate AI-related news from free public sources
2. Automatically ingest updates every morning
3. Deduplicate repeated articles
4. Generate AI summaries and trends using Gemini
5. Store structured data in Neon PostgreSQL
6. Provide a responsive Streamlit dashboard
7. Allow mobile access through browser/PWA usage
8. Provide a centralized page for AI resources/tools/configurations

---

# Technology Stack

## Frontend

* Streamlit

## Backend

* Python 3.12
* FastAPI (minimal backend services)

## Database

* Neon PostgreSQL

## AI Provider

* Google AI Studio
* Gemini 2.5 Flash

## Hosting

* Streamlit Community Cloud (Phase 1)

## Scheduling

* GitHub Actions

## ORM

* SQLAlchemy

## Environment Management

* python-dotenv

---

# High Level Architecture

```text
RSS Sources
    ↓
Ingestion Service
    ↓
Deduplication
    ↓
Neon PostgreSQL
    ↓
Gemini Summarization
    ↓
Summary Storage
    ↓
Streamlit Dashboard
```

---

# Directory Structure

```text
ai-intelligence-hub/
│
├── app/
│   ├── main.py
│   │
│   ├── dashboard/
│   │   ├── home.py
│   │   ├── news.py
│   │   ├── trends.py
│   │   └── tools.py
│   │
│   ├── services/
│   │   ├── rss_service.py
│   │   ├── summarizer_service.py
│   │   ├── trend_service.py
│   │   └── deduplication_service.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── migrations/
│   │
│   ├── prompts/
│   │   ├── summary_prompt.txt
│   │   └── trend_prompt.txt
│   │
│   ├── scheduler/
│   │   └── daily_pipeline.py
│   │
│   └── utils/
│       ├── logger.py
│       └── config.py
│
├── .github/
│   └── workflows/
│       └── daily_update.yml
│
├── requirements.txt
├── Dockerfile
├── .env
└── README.md
```

---

# Database Schema

## Table: articles

```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT UNIQUE NOT NULL,
    content TEXT,
    category TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

---

## Table: summaries

```sql
CREATE TABLE summaries (
    id SERIAL PRIMARY KEY,
    summary_date DATE NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Table: trends

```sql
CREATE TABLE trends (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    score INTEGER,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Table: resources

```sql
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    name TEXT,
    category TEXT,
    link TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

# RSS Sources

The platform must initially support:

```text
https://openai.com/news/rss.xml
https://www.anthropic.com/news/rss
https://hnrss.org/frontpage
https://www.reddit.com/r/LocalLLaMA/.rss
https://www.reddit.com/r/MachineLearning/.rss
```

Additional sources may be added later.

---

# Ingestion Requirements

The ingestion service must:

1. Fetch RSS feeds
2. Extract:

   * title
   * content
   * source
   * URL
   * publication date
3. Normalize content
4. Deduplicate:

   * identical URLs
   * highly similar titles
5. Store results in PostgreSQL

---

# Summarization Requirements

The summarization service must:

1. Aggregate daily articles
2. Send aggregated content to Gemini
3. Generate:

   * Top AI developments
   * New model releases
   * Enterprise AI implications
   * Open-source AI updates
   * Local AI relevance
   * Infrastructure/tooling changes
   * Emerging trends
4. Store generated summaries

---

# Gemini Prompt

## summary_prompt.txt

```text
You are an AI research analyst.

Analyze the following AI news articles.

Generate:
1. Top 5 important updates
2. Important model releases
3. Enterprise AI implications
4. Open-source AI developments
5. Local AI relevance
6. Important infrastructure/tooling developments
7. Emerging trends

Keep output concise but insightful.
```

---

# Daily Pipeline

The automated daily process must:

## Step 1

Fetch RSS feeds

## Step 2

Normalize and clean articles

## Step 3

Deduplicate content

## Step 4

Store raw articles

## Step 5

Generate AI summaries with Gemini

## Step 6

Extract trends/topics

## Step 7

Store summaries and trends

---

# Streamlit Dashboard Requirements

## Home Dashboard

Display:

* today's summary
* key AI updates
* highlighted trends
* important releases

---

## News Explorer

Features:

* article filtering
* source filtering
* category filtering
* search functionality

---

## Trends Dashboard

Display:

* trending topics
* repeated keywords
* emerging technologies
* trend history

---

## Resources Page

Store:

* useful AI tools
* prompts
* Ollama configurations
* MCP references
* repositories
* local AI setup guides

---

# Mobile Requirements

The dashboard must:

* be responsive
* support mobile browsers
* support browser “Add to Home Screen”
* render correctly on phones
* collapse sidebars properly

No native mobile application is required.

---

# Environment Variables

## .env

```text
DATABASE_URL=
GOOGLE_API_KEY=
```

---

# Requirements.txt

```text
streamlit
fastapi
uvicorn
sqlalchemy
psycopg2-binary
feedparser
python-dotenv
google-genai
pandas
requests
schedule
```

---

# GitHub Actions Automation

## File

```text
.github/workflows/daily_update.yml
```

## Workflow

```yaml
name: Daily AI Update

on:
  schedule:
    - cron: '0 6 * * *'

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install -r requirements.txt

      - run: python app/scheduler/daily_pipeline.py
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

---

# Hosting Requirements

## Phase 1

Deploy using:

* Streamlit Community Cloud

## Phase 2

Potential migration:

* Railway
* Render
* Azure App Service

---

# Security Requirements

Mandatory requirements:

* API keys stored only in backend
* `.env` excluded from git
* HTTPS enabled
* no public database access
* no exposed admin endpoints

---

# Antigravity IDE Task Distribution

## Agent 1

Database architecture and migrations

## Agent 2

RSS ingestion implementation

## Agent 3

Gemini summarization service

## Agent 4

Streamlit dashboard implementation

## Agent 5

GitHub Actions automation

---

# Codex Task Usage

Use Codex for:

* implementation
* code generation
* debugging
* refactoring
* UI generation
* database integration
* testing

---

# Development Constraints

Do NOT add initially:

* LangChain
* CrewAI
* Vector databases
* RAG
* Autonomous agents
* Kafka
* WebSockets
* Complex orchestration frameworks

Focus on delivering a stable MVP first.

---

# MVP Success Criteria

The MVP is considered complete when:

* news ingestion works automatically
* summaries generate daily
* trends are extracted
* dashboard works on mobile
* Neon DB persists data
* deployment is public
* application is accessible from all devices

---

# Future Enhancements

## Phase 2

Add:

* GitHub trending repositories
* AI YouTube channel aggregation
* AI paper summarization

## Phase 3

Add:

* embeddings
* semantic search
* personalized relevance scoring
* advanced analytics

Only after validating MVP usefulness.

---
