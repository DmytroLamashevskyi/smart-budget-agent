from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .agent_utils import Transaction, TransactionList


def _normalize_header(name: str) -> str:
    """
    Normalize column names by:
    - removing BOM characters (\ufeff),
    - trimming whitespace,
    - converting to lowercase.
    """
    if not isinstance(name, str):
        name = str(name)
    return name.replace("\ufeff", "").strip().lower()


def _normalize_transactions_df(df: pd.DataFrame) -> TransactionList:
    """
    Normalize arbitrary CSV into a standard transaction format.

    Strategy:
    1) Try to match known header names (EN + RU).
    2) If some core columns are missing, infer them from content:
       - date: column where most values parse as dates,
       - amount: numeric column with many distinct values,
       - description: text column with high uniqueness and reasonable length.

    Output transaction fields:
    - date: ISO date string "YYYY-MM-DD"
    - description: string
    - amount: float (expenses should be negative, income positive)
    - currency: string (default "USD" if not found)
    - category: optional string
    """
    # Known header candidates in multiple languages
    column_map = {
        "date": ["date", "transaction_date", "Дата", "posting_date"],
        "description": [
            "description",
            "details",
            "memo",
            "Описание",
            "name",
            "Заметки",
            "Детали",
        ],
        "amount": ["amount", "sum", "Сумма", "value", "JPY"],
        "currency": ["currency", "curr", "валюта", "Валюта", "Bалюта"],
        "category": ["category", "cat", "Категория"],
        "income_expense": ["Доход/Расход"],
    }

    def find_by_header(candidates: List[str]) -> str | None:
        """Find the first matching column by normalized header name."""
        norm_candidates = {_normalize_header(c) for c in candidates}
        for col in df.columns:
            if _normalize_header(col) in norm_candidates:
                return col
        return None

    # 1. Try to locate columns by header
    date_col = find_by_header(column_map["date"])
    desc_col = find_by_header(column_map["description"])
    amount_col = find_by_header(column_map["amount"])
    currency_col = find_by_header(column_map["currency"])
    category_col = find_by_header(column_map["category"])
    inout_col = find_by_header(column_map["income_expense"])

    # 2. Fallback: infer columns by content when not found by header

    # 2.1 Date column: column where >= 70% of values parse as dates
    if date_col is None:
        best_col = None
        best_score = 0.0
        for col in df.columns:
            series = df[col]
            parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
            score = parsed.notna().mean()
            if score > 0.7 and score > best_score:
                best_score = score
                best_col = col
        date_col = best_col

    # 2.2 Amount column: numeric column with a high ratio of numeric values
    # and enough distinct values
    if amount_col is None:
        best_col = None
        best_score = 0.0
        for col in df.columns:
            series = df[col]
            numeric = pd.to_numeric(series, errors="coerce")
            score = numeric.notna().mean()
            if score < 0.7:
                # Not enough numeric values
                continue

            distinct = numeric.nunique(dropna=True)
            if distinct < 5:
                # Not enough variation to be a meaningful amount column
                continue

            # Heuristic: higher ratio of numeric values + more distinct values is better
            metric = float(score * (1 + (distinct ** 0.5)))
            if metric > best_score:
                best_score = metric
                best_col = col

        amount_col = best_col

    # 2.3 Description column: text column with high uniqueness and reasonable length
    if desc_col is None:
        best_col = None
        best_score = 0.0
        for col in df.columns:
            series = df[col].astype(str)
            uniq_ratio = series.nunique(dropna=True) / max(len(series), 1)
            avg_len = series.str.len().mean()

            # For descriptions we want:
            # - relatively diverse values (uniq_ratio)
            # - not super short strings (avg_len)
            if uniq_ratio < 0.3 or avg_len < 4:
                continue

            score = uniq_ratio * min(avg_len, 80)
            if score > best_score:
                best_score = score
                best_col = col
        desc_col = best_col

    # 3. Validate that core fields exist
    if date_col is None or desc_col is None or amount_col is None:
        raise ValueError(
            "CSV must contain at least a date, description and amount column. "
            f"Could not infer them from columns: {list(df.columns)}"
        )

    # 4. Normalize to our internal schema
    df = df.copy()

    # Date → ISO (YYYY-MM-DD), using dayfirst=True for formats like 26/11/2025
    df["__date"] = (
        pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
        .dt.date.astype(str)
    )

    # Description
    df["__desc"] = df[desc_col].astype(str)

    # Amount
    df["__amount"] = pd.to_numeric(df[amount_col], errors="coerce")

    # Convert expenses to negative based on income/expense flag
    if inout_col is not None:
        flag = df[inout_col].astype(str)
        # When the flag contains "Расход" (Russian "Expense"), treat it as a negative amount
        df.loc[flag.str.contains("Расход"), "__amount"] *= -1

    # Currency
    if currency_col is not None:
        df["__currency"] = df[currency_col].astype(str)
    else:
        df["__currency"] = "USD"

    # Category (emoji included is fine)
    if category_col is not None:
        df["__category"] = df[category_col].astype(str)
    else:
        df["__category"] = None

    # 5. Build list of transaction dictionaries
    records: TransactionList = []
    for _, row in df.iterrows():
        if pd.isna(row["__amount"]):
            continue

        tx: Transaction = {
            "date": row["__date"],
            "description": row["__desc"],
            "amount": float(row["__amount"]),
            "currency": str(row["__currency"]),
        }
        cat = row["__category"]
        if cat is not None and str(cat).strip():
            tx["category"] = str(cat).strip()

        records.append(tx)

    return records


# ---------- Import / normalization ----------


def load_csv_transactions(path: str) -> Dict[str, Any]:
    """
    Tool: Load a CSV file with raw transactions and normalize them.

    Args:
        path: Path to a CSV file relative to the project root or an absolute path.

    Returns:
        dict with:
        - status: "success" or "error"
        - transactions: normalized list[dict] (on success)
        - error_message: description (on error)
    """
    try:
        p = Path(path)
        if not p.exists():
            return {
                "status": "error",
                "error_message": f"File '{path}' does not exist.",
            }

        df = pd.read_csv(p)
        transactions = _normalize_transactions_df(df)
        return {"status": "success", "transactions": transactions}
    except Exception as exc:
        return {
            "status": "error",
            "error_message": f"Failed to load CSV: {exc}",
        }


# ---------- Categorization ----------

_KEYWORD_CATEGORIES: Dict[str, str] = {
    "uber": "Transport",
    "taxi": "Transport",
    "train": "Transport",
    "metro": "Transport",
    "spotify": "Subscriptions",
    "netflix": "Subscriptions",
    "youtube": "Subscriptions",
    "apple music": "Subscriptions",
    "grocery": "Groceries",
    "supermarket": "Groceries",
    "walmart": "Groceries",
    "costco": "Groceries",
    "starbucks": "Coffee",
    "mcdonald": "Eating Out",
    "kfc": "Eating Out",
    "restaurant": "Eating Out",
    "rent": "Housing",
    "mortgage": "Housing",
    "electric": "Utilities",
    "water": "Utilities",
    "gas": "Utilities",
}


def auto_categorize_transactions(
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tool: Auto-assign categories to transactions based on simple keyword rules.

    This is a heuristic, not a perfect classifier. It is meant to provide
    a reasonable initial categorization that the user can refine.

    Args:
        transactions: list of transaction dicts.

    Returns:
        dict with:
        - status: "success"
        - transactions: updated list with 'category' filled when possible.
    """
    updated: TransactionList = []

    for tx in transactions:
        new_tx = dict(tx)
        if not new_tx.get("category"):
            desc = str(new_tx.get("description", "")).lower()
            assigned = None
            for kw, cat in _KEYWORD_CATEGORIES.items():
                if kw in desc:
                    assigned = cat
                    break
            if assigned:
                new_tx["category"] = assigned
        updated.append(new_tx)

    return {"status": "success", "transactions": updated}


# ---------- Analytics ----------


def compute_spending_analytics(
    transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Tool: Compute basic spending analytics.

    Calculates:
    - total spent (sum of negative amounts),
    - totals by category,
    - totals by month,
    - top merchants by spend.

    Assumptions:
    - Negative amounts represent expenses, positive amounts are income/refunds.
    """
    if not transactions:
        return {"status": "error", "error_message": "No transactions provided."}

    df = pd.DataFrame(transactions)

    # Basic sanity check
    if "amount" not in df.columns:
        return {"status": "error", "error_message": "Missing 'amount' column."}

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    # Use only expenses (amount < 0) for spending analysis
    expenses = df[df["amount"] < 0].copy()
    expenses["abs_amount"] = expenses["amount"].abs()

    total_spent = float(expenses["abs_amount"].sum()) if not expenses.empty else 0.0

    # Summaries by category
    if "category" in expenses.columns:
        by_cat = (
            expenses.groupby(expenses["category"].fillna("Uncategorized"))["abs_amount"]
            .sum()
            .reset_index()
            .sort_values("abs_amount", ascending=False)
        )
        summary_by_category = by_cat.to_dict(orient="records")
    else:
        summary_by_category = []

    # Summaries by month
    if "date" in expenses.columns:
        expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
        expenses["month"] = expenses["date"].dt.to_period("M").astype(str)
        by_month = (
            expenses.groupby("month")["abs_amount"]
            .sum()
            .reset_index()
            .sort_values("month")
        )
        monthly_totals = by_month.to_dict(orient="records")
    else:
        monthly_totals = []

    # Top merchants (by description)
    if "description" in expenses.columns:
        by_merchant = (
            expenses.groupby("description")["abs_amount"]
            .sum()
            .reset_index()
            .sort_values("abs_amount", ascending=False)
            .head(10)
        )
        top_merchants = by_merchant.to_dict(orient="records")
    else:
        top_merchants = []

    analytics = {
        "total_spent": total_spent,
        "summary_by_category": summary_by_category,
        "monthly_totals": monthly_totals,
        "top_merchants": top_merchants,
    }
    return {"status": "success", "analytics": analytics}


def detect_anomalies(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tool: Naive anomaly detection for unusually large expenses.

    Heuristic:
    - For each category, compute the median and standard deviation of absolute amounts.
    - Flag a transaction as an anomaly if:
      - amount > median + 2 * std, and
      - amount > 50 (absolute value, as a simple noise filter).
    """
    if not transactions:
        return {"status": "error", "error_message": "No transactions provided."}

    df = pd.DataFrame(transactions)
    if "amount" not in df.columns:
        return {"status": "error", "error_message": "Missing 'amount' column."}

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])
    df["abs_amount"] = df["amount"].abs()

    if "category" not in df.columns:
        df["category"] = "Uncategorized"

    grouped = df.groupby("category")["abs_amount"]
    med = grouped.transform("median")
    std = grouped.transform("std").fillna(0)

    # An anomaly is significantly larger than the typical amount in its category
    threshold = med + 2 * std
    mask = (df["abs_amount"] > threshold) & (df["abs_amount"] > 50)
    anomalies = df[mask].sort_values("abs_amount", ascending=False)

    return {
        "status": "success",
        "anomalies": anomalies.to_dict(orient="records"),
    }


# ---------- Export / reporting ----------


def export_categorized_csv(
    transactions: List[Dict[str, Any]],
    path: str = "output/categorized_transactions.csv",
) -> Dict[str, Any]:
    """
    Tool: Save categorized transactions to a CSV file.

    Args:
        transactions: list of transaction dicts.
        path: output CSV path (relative or absolute).

    Returns:
        dict with:
        - status: "success"
        - path: where the file was saved
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(transactions)
    df.to_csv(out_path, index=False)
    return {"status": "success", "path": str(out_path)}


def export_analytics_json(
    analytics: Dict[str, Any],
    path: str = "output/analytics_summary.json",
) -> Dict[str, Any]:
    """
    Tool: Save analytics dictionary as a pretty-printed JSON file.

    Args:
        analytics: analytics dict produced by compute_spending_analytics.
        path: output JSON path (relative or absolute).

    Returns:
        dict with:
        - status: "success"
        - path: where the file was saved
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    return {"status": "success", "path": str(out_path)}
