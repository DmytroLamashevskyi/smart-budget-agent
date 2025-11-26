Smart Budget Agent is a multi-agent financial assistant that helps users understand and optimize their everyday spending. Team of agents that import transactions, categorize them, analyze spending patterns, and then turn everything into clear, actionable recommendations and reports.
Pipeline architecture:
- **Importer Agent** – ingests data from CSV, JSON, and bank-style exports.
- **Categorizer Agent** – automatically assigns spending categories and learns from user feedback.
- **Analyzer Agent** – detects patterns, anomalies, and optimization opportunities.
- **Advisor Agent** – explains what is happening with the user’s money and suggests concrete next steps.
- **Export Mapper Agent** – formats results as JSON/CSV/PDF for dashboards, sharing or archiving.

Everything is intentionally simple and transparent, so users can trust how the agent arrives at its conclusions.

## Problem the agent solves

Most people know they “should have a budget”, but in practice budgeting is painful:
1. You need to export transactions from banks or apps, clean the data, and maintain spreadsheets.
2. Categorizing each expense by hand quickly becomes a chore.
3. Dashboards show charts, but do not tell you what to do next.
4. Small “money leaks” (unused subscriptions, delivery, impulse purchases) accumulate invisibly.
The result is that many users give up after a few weeks. The friction is too high, and the insights are not actionable enough. Smart Budget Agent is designed to reduce this friction to almost zero: import automatically, analyze continuously, and speak to the user in normal language.

## How the multi-agent system works

####  1. Importer Agent

The Importer Agent takes raw financial data from the user:
- CSV exports from banks or budgeting apps,
- JSON payloads,
- simplified “bank-like” CSVs created for demo purposes.
It normalizes dates, currencies and amounts into a unified internal schema and forwards the cleaned transactions to the Categorizer Agent.

####  2. Categorizer Agent

The Categorizer Agent assigns each transaction to a spending category (e.g., groceries, transport, subscriptions, entertainment).
It uses simple heuristics and learned mappings based on merchant names and descriptions.
When the user corrects a category, this feedback is stored in memory so that future transactions from the same merchant are classified correctly. Over time, the amount of manual work required from the user decreases.
All categorized transactions are stored in a shared database, which acts as the memory layer for downstream agents.

####  3. Analyzer Agent

The Analyzer Agent reads from the database and computes:
- total spend by category and by period,
- recurring payments (subscriptions, memberships),
- anomalies such as sudden spikes in a category,
- deviations from the user’s typical baseline (e.g., this month vs 3-month average).
This agent transforms raw transaction history into structured insights that can drive decisions: “Where exactly is my money going?” and “What changed this month?”

####  4. Advisor Agent

The Advisor Agent is the “voice” of the system. It takes the analytics output and generates:
- short natural-language summaries of the current month,
- explanations of what changed compared to previous periods,

- specific recommendations such as:
- -  “You spent 30% more on food delivery than your usual average.”
- -  “You have two subscriptions that look unused.”
- -  “If you cap entertainment at X next month, you can move Y into savings.”
The advisor remembers user preferences (for example, categories the user does not want to cut) and can adapt future suggestions accordingly.

####  5. Export Mapper Agent

To make the results easy to consume in other tools or reports, the Export Mapper Agent can:
1. generate JSON responses for programmatic integration,
2. produce CSV exports with categorized transactions,
3. create simple PDF summary reports.
This makes the agent usable both as an interactive assistant and as a backend service feeding dashboards or enterprise tools.


## Why this is valuable

Smart Budget Agent adds value in three main ways:
- **Reduction of manual work**  – users no longer need to maintain complex spreadsheets or manually classify every transaction.
- **From charts to actions**  – the system does not stop at visualizations; it explicitly tells the user what they can change next month.
- **Personalization over time**  – by learning from corrections and preferences, the agent becomes more accurate and less intrusive, turning into a personalized “budget co-pilot”.

Although the current implementation is focused on individual users, the architecture can be extended to enterprise scenarios (for example, white-labeling for banks or analyzing company-wide expense data). The simple, modular agent design keeps it easy to reason about, extend, and evaluate.
