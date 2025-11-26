# Smart Budget Agent

Smart Budget Agent is a multi-agent system built with the Google Agent Development Kit (ADK) that helps users automatically import, normalize, categorize, and analyze their personal spending data. It turns raw CSV exports from budgeting apps or banks into clear insights and actionable budget recommendations.

> Goal: make personal finance management easy, transparent, and actionable with the power of AI agents.

---

## Table of Contents

- Overview
- Key Features
- Architecture
- Repository Structure
- Getting Started
  - Prerequisites
  - Installation
  - Configuration
- Running the Agent
  - Web UI (ADK)
  - Local Tool Demo (Python)
- Data Format
- Limitations & Future Work
- License

---

## Overview

Managing a personal budget is often painful:

- Every bank/app exports data in a slightly different CSV format.
- You must manually clean, normalize, and categorize transactions.
- It is hard to see patterns, subscriptions, overspending, or anomalies.
- Typical dashboards show charts, but do not tell you *what to actually do*.

Smart Budget Agent addresses this by:

1. Importing raw CSV files and automatically recognizing key columns
   (date, description, amount, category, currency) even with non-English headers.
2. Normalizing data into a consistent transaction schema.
3. Auto-categorizing uncategorized transactions using simple keyword rules.
4. Analyzing spending patterns, categories, monthly trends, and outliers.
5. Advising the user with clear, human-readable summaries and recommendations.
6. Exporting processed data (categorized CSV, JSON analytics) for further use.

---

## Key Features

- Automatic CSV import & normalization
  - Handles different header names (English + Russian).
  - Infers columns by content when headers are unknown.
  - Converts “expense” flags into negative amounts.

- Multi-agent architecture
  - Importer Agent — loads and normalizes transactions.
  - Categorizer Agent — auto-assigns categories.
  - Analyzer Agent — computes spending analytics and detects anomalies.
  - Advisor Agent — turns analytics into clear, actionable advice.
  - Orchestrator Agent — coordinates the whole workflow.

- Analytics out of the box
  - Total spending over a period.
  - Spending by category.
  - Spending by month.
  - Top merchants / descriptions by spend.
  - Simple anomaly detection for unusually large expenses.

- Export tools
  - Save categorized transactions to CSV.
  - Save analytics to pretty-printed JSON.

---

## Architecture

At a high level, Smart Budget Agent is a small multi-agent system:

1. User provides a CSV file path and a question (e.g., “Where can I cut spending?”).
2. Orchestrator Agent delegates:
   - to Importer Agent → load + normalize transactions;
   - to Categorizer Agent → fill missing categories;
   - to Analyzer Agent → compute analytics and detect anomalies;
   - to Advisor Agent → generate explanations and recommendations.
3. The user receives:
   - a short summary of spending patterns,
   - concrete recommendations (e.g., subscriptions to review, categories to reduce),
   - optional exported files (CSV, JSON).

The core logic for importing, normalization, categorization, analytics, and export is implemented as tools in `smart_budget_agent/tools.py`, which are then used by the agents.

---

## Repository Structure

smart-budget-agent/
- smart_budget_agent/
  - __init__.py
  - agent.py               # Orchestrator agent (entry point)
  - config.py              # Model name, default paths, settings
  - tools.py               # CSV import, normalization, analytics, exports
  - agent_utils.py         # (optional) shared helpers / types
  - sub_agents/
    - __init__.py
    - importer_agent.py    # Import & normalization
    - categorizer_agent.py # Auto-categorization
    - analyzer_agent.py    # Analytics & anomalies
    - advisor_agent.py     # Recommendations & exports
- data/
  - samples/
    - transactions_sample.csv  # Example CSV (e.g., Money Manager export)
- tests/
  - __init__.py
  - test_agent.py          # Simple smoke tests
- output/                  # (ignored) generated CSV/JSON reports
- README.md
- requirements.txt
- .gitignore

---

## Getting Started

### Prerequisites

- Python 3.10 or 3.11
- A Google API key for Generative AI (used by ADK)
- pip for installing dependencies

### Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/your-name/smart-budget-agent.git
cd smart-budget-agent

python -m venv .venv
# Windows
.\.venv\Scripts ctivate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
GOOGLE_GENAI_USE_VERTEXAI=False
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE
```

Optionally adjust `smart_budget_agent/config.py`:

```python
MODEL_NAME = "gemini-1.5-flash"  # or another supported model
DEFAULT_SAMPLE_CSV = "data/samples/transactions_sample.csv"
BASE_CURRENCY = "USD"
```

---

## Running the Agent

### Web UI (ADK)

The easiest way to interact with the agent is via the ADK web interface.

From the project root:

```bash
adk web
```

ADK will start a local web UI (typically `http://127.0.0.1:8000`) and display a link in the console.

1. Open the link in your browser.
2. Select the agent named (for example) `smart_budget_orchestrator`.
3. Start a conversation, for example:

   Use the sample file `data/samples/transactions_sample.csv`.
   Import my transactions, analyze my spending over the last month,
   and give me a short summary with 3–5 recommendations.

The orchestrator will automatically delegate to the sub-agents and call the appropriate tools. If configured, it can also export categorized CSV and analytics JSON.

---

### Local Tool Demo (Python)

You can also run the core logic directly (without the agent layer), which is useful for debugging.

From a Python shell in the project root:

```python
from smart_budget_agent.tools import (
    load_csv_transactions,
    compute_spending_analytics,
)

# Load and normalize transactions
res = load_csv_transactions("data/samples/transactions_sample.csv")
print("status:", res["status"])
print("tx count:", len(res.get("transactions", [])))

if res["status"] == "success":
    txs = res["transactions"]

    # Compute analytics
    analytics_res = compute_spending_analytics(txs)
    print("analytics status:", analytics_res["status"])

    if analytics_res["status"] == "success":
        analytics = analytics_res["analytics"]
        print("total_spent:", analytics["total_spent"])
        print("by category:", analytics["summary_by_category"][:5])
```

This verifies that:

- the importer can handle your CSV format,
- the analytics logic runs correctly,
- the data is in a consistent format.

---

## Data Format

Smart Budget Agent is designed to be tolerant to different CSV schemas.

### Expected core fields

Internally, each transaction is normalized into a dictionary with:

- date — ISO date string, "YYYY-MM-DD",
- description — text describing the transaction,
- amount — float (negative for expenses, positive for income/refunds),
- currency — currency code/string, e.g. "USD", "JPY",
- category — optional category string (can include emoji).

### Column detection strategies

The importer tries:

1. Header matching (English + Russian):
   - date, transaction_date, Дата, etc.
   - description, memo, Заметки, etc.
   - amount, Сумма, JPY, etc.
   - currency, валюта, Валюта, Bалюта, etc.
   - category, Категория
   - Доход/Расход to decide sign of the amount.

2. Content-based inference, if headers are unknown:
   - date — column where ≥70% of values parse as dates,
   - amount — numeric column with enough numeric values and distinct values,
   - description — text column with high uniqueness and reasonable average length.

If it still cannot infer date, description, or amount, the tool returns an error with a clear message.

---

## Limitations & Future Work

Current version focuses on a simple but robust end-to-end pipeline:

- Heuristic keyword-based categorization.
- Simple anomaly detection based on category medians and standard deviations.
- Single-user, local CSV files (no real bank/API integrations yet).

Planned or possible future improvements:

- More advanced ML-based categorization tuned on real transaction datasets.
- Learning from user feedback on categories (personalized rules).
- Better detection of subscriptions and recurring payments.
- Multi-currency support with FX normalization to a base currency.
- Richer dashboards / visualizations (time series, category breakdowns).
- Integration with external data sources and budgeting apps.

---

## License

This project is provided as part of an AI Agents / Kaggle experimentation setup.
You are free to adapt it for your own experiments, demos, or learning purposes.
(Check the LICENSE file if one is included.)
