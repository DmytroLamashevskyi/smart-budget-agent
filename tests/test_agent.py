from google.adk.agents import Agent

from smart_budget_agent.agent import root_agent


def test_root_agent_exists():
    assert isinstance(root_agent, Agent)
