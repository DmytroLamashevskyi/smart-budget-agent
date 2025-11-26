from google.adk.agents import Agent

from smart_budget_agent.config import MODEL_NAME
from smart_budget_agent.tools import (
    export_categorized_csv,
    export_analytics_json,
)


advisor_agent = Agent(
    name="advisor_agent",
    model=MODEL_NAME,
    description=(
        "Budget advisor that turns analytics into actionable recommendations "
        "and can export results to files."
    ),
    instruction=(
        "You receive spending analytics and user goals (e.g. save more, pay debt). "
        "Use them to propose 3–7 concrete, prioritized recommendations: "
        "what to cut, where to optimize, and what realistic monthly budget "
        "targets could be. When the user asks to export data, use the tools "
        "'export_categorized_csv' and 'export_analytics_json'. "
        "Always keep explanations simple and non-judgmental."
    ),
    tools=[export_categorized_csv, export_analytics_json],
)
