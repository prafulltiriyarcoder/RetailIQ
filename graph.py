
import os
import re

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.tools.database_tools import (
    get_store_performance,
    get_inventory_health,
    get_promotion_effectiveness,
    get_store_trend,
    get_store_anomalies,
)

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)


def understand_question(state: AgentState) -> AgentState:
    question = state["question"]

    prompt = f"""
You are a retail business analytics assistant.

The available data covers January to June 2026.

Analyze this question:
{question}

Identify:
1. Store ID, such as S007, or NONE.
2. Month as YYYY-MM-DD, using the first day of the month.
   For example, June means 2026-06-01.
   If no month is mentioned, return NONE.
3. User intent in a short phrase.

Return exactly:
STORE_ID: <value>
MONTH: <value>
INTENT: <value>
"""

    response = llm.invoke(prompt)
    interpretation = response.content

    store_match = re.search(
        r"STORE_ID:\s*(\S+)", interpretation, re.IGNORECASE
    )
    month_match = re.search(
        r"MONTH:\s*(\d{4}-\d{2}-\d{2}|NONE)",
        interpretation,
        re.IGNORECASE,
    )
    intent_match = re.search(
        r"INTENT:\s*(.+)", interpretation, re.IGNORECASE
    )

    store_id = store_match.group(1) if store_match else "NONE"
    month = month_match.group(1) if month_match else "NONE"
    intent = intent_match.group(1).strip() if intent_match else "Unknown"

    if store_id.upper() == "NONE":
        store_id = ""
    if month.upper() == "NONE":
        month = ""

    print("\nLLM interpretation:")
    print(interpretation)

    return {
        **state,
        "store_id": store_id,
        "month": month,
        "intent": intent,
        "investigation_notes": [],
    }


def select_tools(state: AgentState) -> AgentState:
    question = state["question"]

    prompt = f"""
You are selecting analytical tools for a retail business assistant.

User question: {question}
Store ID: {state.get("store_id", "NONE")}
Month: {state.get("month", "NONE")}
Intent: {state.get("intent", "UNKNOWN")}

Available tools:
- trend: revenue and transaction changes over time
- inventory: stock levels, replenishment, and stockouts
- promotion: promotion effectiveness and promoted revenue
- anomalies: stores with detected performance anomalies

Choose only tools relevant to answering the question.

Rules:
- Questions about why sales or performance declined: trend, inventory, promotion
- Questions about stockouts or stock levels: inventory
- Questions about promotions or discounts: promotion
- Questions asking which stores have problems or anomalies: anomalies
- If uncertain, choose trend.

Return ONLY a comma-separated list of tool names.
"""

    response = llm.invoke(prompt)
    allowed_tools = {"trend", "inventory", "promotion", "anomalies"}

    selected = [
        item.strip().lower()
        for item in response.content.split(",")
        if item.strip().lower() in allowed_tools
    ]

    if not selected:
        selected = ["trend"]

    print("\nSelected tools:", selected)

    return {
        **state,
        "selected_tools": list(dict.fromkeys(selected)),
    }


def investigate_store(state: AgentState) -> AgentState:
    store_id = state.get("store_id", "")
    month = state.get("month", "")
    selected_tools = state.get("selected_tools", [])

    if "anomalies" in selected_tools:
        anomaly_data = get_store_anomalies()
        print("\nAnomaly data:", anomaly_data)
        return {
            **state,
            "anomaly_data": anomaly_data,
            "investigation_notes": [
                "Retrieved store anomaly data."
            ],
        }

    if not store_id or not month:
        return {
            **state,
            "investigation_notes": [
                "A store ID and month are required for this investigation."
            ],
        }

    updates = {}
    notes = []

    print(f"\nInvestigating {store_id} for {month}...")
    print("Executing selected tools:", selected_tools)

    if "trend" in selected_tools:
        trend = get_store_trend(store_id, month)
        updates["trend_data"] = trend
        notes.append("Retrieved monthly sales trends.")

    if "inventory" in selected_tools:
        inventory = get_inventory_health(store_id, month)
        updates["inventory_data"] = inventory
        notes.append("Retrieved inventory health.")

    if "promotion" in selected_tools:
        promotion = get_promotion_effectiveness(store_id, month)
        updates["promotion_data"] = promotion
        notes.append("Retrieved promotion effectiveness.")

    if "performance" in selected_tools:
        performance = get_store_performance(store_id, month)
        updates["performance_data"] = performance
        notes.append("Retrieved store performance.")

    print("\nInvestigation notes:", notes)

    return {
        **state,
        **updates,
        "investigation_notes": notes,
    }


def format_anomaly_summary(anomalies: list[dict]) -> str:
    if not anomalies:
        return "No anomalies were returned."

    lines = [
        "| Store | City | Anomaly | Revenue Growth | "
        "Transaction Growth | Stockout Rate |",
        "|---|---|---|---:|---:|---:|",
    ]

    for row in anomalies:
        lines.append(
            f"| {row['store_id']} — {row['store_name']} "
            f"| {row['city']} "
            f"| {row['anomaly_type']} "
            f"| {row['revenue_growth_pct']:.2f}% "
            f"| {row['transaction_growth_pct']:.2f}% "
            f"| {row['stockout_rate']:.2f}% |"
        )

    return "\n".join(lines)

def analyze_evidence(state: AgentState) -> AgentState:
    anomaly_summary = format_anomaly_summary(
    state.get("anomaly_data", [])
)
    prompt = f"""
You are a retail performance analyst.

Answer the user's question using ONLY the evidence below.
Do not invent facts or claim causation beyond the evidence.

User question:
{state['question']}

Store: {state.get('store_id')}
Analysis month: {state.get('month')}

IMPORTANT:
- The analysis month above is authoritative.
- Treat all retrieved records as belonging to that analysis month.
- Do not infer the month from the displayed timestamp.
- Describe zero units received as applying to the analysis month.
- The data shows an inventory risk; do not claim it definitively caused
  the revenue decline.
- If no previous-month revenue is supplied, do not claim a measured
  month-over-month revenue decline.

Performance data:
{state.get('performance_data', [])}

Inventory data:
{state.get('inventory_data', [])}

Promotion data:
{state.get('promotion_data', [])}

Month-over-month sales trend:
{state.get('trend_data', [])}

Anomaly report (formatted directly from database records):
{anomaly_summary}

Write these sections:
1. Executive summary
2. Key evidence
3. Most likely explanation
4. Recommended actions

Use revenue_growth_pct and transaction_growth_pct to quantify
the change. Format revenue in Indian rupees (₹), not dollars.

Keep it concise, business-focused, and evidence-based.

If the question asks which stores have anomalies, use the Anomaly data
as the primary evidence. Summarize the flagged stores, their anomaly
types, and relevant metrics.

Do not claim data is missing when the Anomaly data field contains
records. Do not assume every flagged anomaly caused a revenue decline.

When reporting anomalies, preserve every store ID and its corresponding
store name and anomaly type exactly as provided. Do not duplicate,
omit, or reclassify stores.
"""


    response = llm.invoke(prompt)

    return {
        **state,
        "final_answer": response.content,
    }



builder = StateGraph(AgentState)

builder.add_node("understand_question", understand_question)
builder.add_node("select_tools", select_tools)
builder.add_node("investigate_store", investigate_store)
builder.add_node("analyze_evidence", analyze_evidence)

builder.add_edge(START, "understand_question")
builder.add_edge("understand_question", "select_tools")
builder.add_edge("select_tools", "investigate_store")
builder.add_edge("investigate_store", "analyze_evidence")
builder.add_edge("analyze_evidence", END)

graph = builder.compile()
