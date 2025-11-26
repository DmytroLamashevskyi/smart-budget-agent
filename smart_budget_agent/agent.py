from google.adk.agents import Agent

from smart_budget_agent.config import MODEL_NAME
from smart_budget_agent.sub_agents import (
    importer_agent,
    categorizer_agent,
    analyzer_agent,
    advisor_agent,
)


root_agent = Agent(
    name="smart_budget_orchestrator",
    model=MODEL_NAME,
    description=(
        "Smart Budget Agent orchestrator that helps users import, "
        "categorize, analyze and optimize their personal spending."
    ),
    instruction=(
        "You are the main entry point for the Smart Budget Agent system. "
        "Your job is to make personal finance management easy and actionable.\n\n"
        "High-level workflow:\n"
        "1) If the user provides a file path or raw CSV text, delegate to "
        "'importer_agent' to load and normalize transactions.\n"
        "2) Then delegate to 'categorizer_agent' to categorize transactions.\n"
        "3) Next, delegate to 'analyzer_agent' to compute analytics and detect patterns.\n"
        "4) Finally, delegate to 'advisor_agent' to explain insights and suggest "
        "concrete optimization steps.\n\n"
        "Ask for clarification only when strictly necessary (e.g. which file to use "
        "or which month to focus on). Keep answers short, clear and practical."
    ),
    sub_agents=[
        importer_agent,
        categorizer_agent,
        analyzer_agent,
        advisor_agent,
    ],
)
