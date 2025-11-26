from google.adk.agents import Agent

from smart_budget_agent.config import MODEL_NAME
from smart_budget_agent.tools import load_csv_transactions


importer_agent = Agent(
    name="importer_agent",
    model=MODEL_NAME,
    description="Imports and normalizes raw transaction data from CSV bank exports.",
    instruction=(
        "You help the user import and normalize transaction data. "
        "When the user provides a path to a CSV file, "
        "call the 'load_csv_transactions' tool. "
        "Always return a short confirmation plus a summary "
        "of how many transactions were loaded."
    ),
    tools=[load_csv_transactions],
)
