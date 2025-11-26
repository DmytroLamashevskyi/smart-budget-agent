from google.adk.agents import Agent

from smart_budget_agent.config import MODEL_NAME
from smart_budget_agent.tools import (
    compute_spending_analytics,
    detect_anomalies,
)


analyzer_agent = Agent(
    name="analyzer_agent",
    model=MODEL_NAME,
    description="Analyzes categorized transactions to find patterns and anomalies.",
    instruction=(
        "You take categorized transactions and call the tools to compute analytics. "
        "First, call 'compute_spending_analytics' to get totals by category/month "
        "and top merchants. Then, when useful, call 'detect_anomalies' to spot "
        "unusually large expenses. "
        "Summarize key insights in plain language: biggest categories, "
        "spending trends over time, and any suspicious or outlier payments."
    ),
    tools=[compute_spending_analytics, detect_anomalies],
)
