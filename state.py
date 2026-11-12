from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Original user question
    question: str

    # Extracted business context
    store_id: str
    month: str
    intent: str
    selected_tools: list[str]

    # Evidence gathered from tools
    performance_data: list[dict]
    inventory_data: list[dict]
    promotion_data: list[dict]
    anomaly_data: list[dict]
    trend_data: list[dict]

    # Agent's reasoning
    investigation_notes: list[str]

    # Final response
    final_answer: str