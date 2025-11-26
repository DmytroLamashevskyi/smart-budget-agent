from google.adk.agents import Agent

from smart_budget_agent.config import MODEL_NAME
from smart_budget_agent.tools import auto_categorize_transactions


categorizer_agent = Agent(
    name="categorizer_agent",
    model=MODEL_NAME,
    description="Automatically categorizes transactions into spending categories.",
    instruction=(
        "You receive a list of transactions (as JSON) and assign categories "
        "using the 'auto_categorize_transactions' tool. "
        "If some transactions already have categories, keep them unless "
        "they are clearly wrong. "
        "Explain to the user how many transactions were categorized "
        "and which top merchants belong to each major category."
    ),
    tools=[auto_categorize_transactions],
)
