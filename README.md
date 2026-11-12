# Store Performance Intelligence

> **Project status:** Local MVP --- database, analytical tools,
> LangGraph workflow, and FastAPI endpoint operational.\
> **Last updated:** 2026-10-09

## 1. Overview

A retail analytics agent for investigating store performance using
PostgreSQL data, Python tools, LangGraph, and a Groq-hosted LLM.

**Current flow**

`Question → LangGraph → Question understanding → Tool selection → PostgreSQL tools → Evidence analysis → Answer`

FastAPI exposes the graph through an HTTP endpoint.

## 2. Technology Stack

-   **Language:** Python 3.14
-   **Database:** PostgreSQL 18
-   **Database access:** SQLAlchemy, psycopg2
-   **Agent workflow:** LangGraph
-   **LLM integration:** LangChain Groq (`openai/gpt-oss-20b`)
-   **API:** FastAPI, Uvicorn, Pydantic
-   **Data analysis:** Pandas
-   **Configuration:** `python-dotenv`

## 3. Dataset

Fictional retail business: **RetailIQ**

  Item                         Current dataset
  -------------------- -----------------------
  Stores                                    20
  Products                                  40
  Customers                                500
  Sales transactions                    18,985
  Inventory records                    144,800
  Data period            Jan 1 -- Jun 30, 2026
  Calendar events                            6

## 4. Database and Analytics

Seven core tables:

-   `stores`
-   `products`
-   `customers`
-   `sales`
-   `inventory`
-   `promotions`
-   `calendar_events`

Analytical views created:

-   `store_monthly_performance`
-   `promotion_effectiveness`
-   `store_inventory_health`
-   `store_performance_trends`
-   `category_monthly_performance`
-   `store_anomalies`

### Validated scenarios

-   **S007 --- Bengaluru Store 1:** June revenue ₹547,325.54, down
    **7.39%** from May; transactions down **9.89%**; units received
    **0**; average closing stock **1.39**; stockout rate **44.42%**.
-   **S012 --- Hyderabad Store 3:** promotion rate fell from **25.37% in
    May to 0% in June**; June revenue ₹454,441.29, down **2.02%**.
-   **June anomaly view:** **9 stores** flagged --- 6
    sales-performance-decline records, 1 inventory/stockout issue, and 2
    promotion-drop records.

These are diagnostic signals from the generated dataset; correlation
does not by itself establish causation.

## 5. Python Tool Layer

Implemented in `agent/tools/database_tools.py`:

-   `get_store_performance(store_id, month)`
-   `get_inventory_health(store_id, month)`
-   `get_promotion_effectiveness(store_id, month)`
-   `get_store_trend(store_id, month)`
-   `get_store_anomalies()`

Tools query the analytical views through SQLAlchemy and return records
for the agent. Tool selection is validated against an allowlist rather
than permitting arbitrary LLM-generated SQL.

## 6. Agent Workflow

Current workflow in `agent/graph.py`:

1.  `understand_question` --- extracts store ID, month, and intent.
2.  `select_tools` --- chooses relevant tools from the allowlist.
3.  `investigate_store` --- executes selected tools and stores evidence
    in state.
4.  `analyze_evidence` --- generates a business-facing response.

`AgentState` tracks the question, extracted context, selected tools,
evidence, investigation notes, and final answer.

## 7. API

Implemented in `api/main.py`.

  Endpoint        Purpose
  --------------- ----------------------------------------
  `GET /`         API welcome/status response
  `GET /health`   Health check
  `POST /ask`     Runs the agent for a business question

Run locally from the project root:

``` powershell
python -m uvicorn api.main:app --reload
```

Swagger UI: `http://127.0.0.1:8000/docs`

Example request:

``` json
{
  "question": "Why did S007's performance decline in June 2026?"
}
```

The `/ask` endpoint has been tested with: - A store-specific performance
investigation (S007, June 2026). - A cross-store anomaly question (June
2026).

## 8. Current Limitations / Next Steps

-   Add automated tests for routing, tool execution, API responses, and
    evidence accuracy.
-   Correct LLM-generated counting/classification errors in anomaly
    summaries; preserve database classifications.
-   Avoid unsupported causal claims in generated explanations.
-   Improve handling of questions with missing store/month context.
-   Add API-level logging and more specific error handling.
-   Consider a frontend after the API and analysis quality are more
    robust.
-   Explore mapping the local architecture to AccureIQx in parallel.

## 9. Project Structure

``` text
storage-performance-intelligence/
├── agent/
│   ├── __init__.py
│   ├── state.py
│   ├── graph.py
│   └── tools/
│       ├── __init__.py
│       └── database_tools.py
├── api/
│   └── main.py
├── data/
├── database/
│   └── schema.sql
├── notebooks/
│   └── data_generation.ipynb
└── tests/
    └── test_graph.py
```

## 10. Progress Log

Append future milestones here.

  -----------------------------------------------------------------------
  Date                    Milestone               Status / evidence
  ----------------------- ----------------------- -----------------------
  2026-10-09              PostgreSQL schema,      Complete
                          dataset, and analytical 
                          views                   

  2026-10-09              Database tool layer     5 tools implemented and
                                                  exercised

  2026-10-09              LangGraph question      Tested with store,
                          understanding and tool  promotion, and anomaly
                          selection               questions

  2026-10-09              Evidence-based analysis Working; accuracy
                          node                    improvements remain

  2026-10-09              FastAPI `/ask` endpoint Tested with
                                                  store-specific and
                                                  anomaly questions
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 11. Append Future Updates

Add new entries to the progress log and update the relevant sections as
the project evolves.

### Update template

``` markdown
### [YYYY-MM-DD] — [Milestone]
- **Implemented:**
- **Validation:**
- **Quantifiable result:**
- **Known issue / next step:**
```
