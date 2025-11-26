from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .agent_utils import Transaction, TransactionList


def _normalize_transactions_df(df: pd.DataFrame) -> TransactionList:
    """
    Try to normalize arbitrary CSV into our standard Transaction format.
    Мы не идеальны, но покрываем самые типичные названия колонок.
    """
    column_map = {
        "date": ["date", "transaction_date", "Дата", "posting_date"],
        "description": ["description", "details", "memo", "Описание", "name"],
        "amount": ["amount", "sum", "Сумма", "value"],
        "currency": ["currency", "curr", "валюта"],
        "category": ["category", "cat", "Категория"],
    }

    def find_col(candidates):
        for c in candidates:
            for col in df.columns:
                if col.strip().lower() == c.strip().lower():
                    return col
        return None

    date_col = find_col(column_map["date"])
    desc_col = find_col(column_map["description"])
    amount_col = find_col(column_map["amount"])
    currency_col = find_col(column_map["currency"])
    category_col = find_col(column_map["category"])

    if date_col is None or desc_col is None or amount_col is None:
        raise ValueError(
            f"CSV must contain at least date/description/amount columns. "
            f"Found columns: {list(df.columns)}"
        )

    df = df.copy()
    df["__date"] = pd.to_datetime(df[date_col], errors="coerce").dt.date.astype(str)
    df["__desc"] = df[desc_col].astype(str)
    df["__amount"] = pd.to_numeric(df[amount_col], errors="coerce")

    if currency_col:
        df["__currency"] = df[currency_col].astype(str)
    else:
        df["__currency"] = "USD"

    if category_col:
        df["__category"] = df[category_col].astype(str)
    else:
        df["__category"] = None

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
        if row["__category"] is not None and str(row["__category"]).strip():
            tx["category"] = str(row["__category"]).strip()
        records.append(tx)

    return records


# ---------- Import / normalization ----------


def load_csv_transactions(path: str) -> Dict[str, Any]:
    """
    Tool: Load a CSV file with raw transactions and normalize them.

    Args:
        path: Path to a CSV file relative to project root or absolute.

    Returns:
        dict with:
        - status: "success" or "error"
        - transactions: normalized TransactionList (on success)
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

_KEYWORD_CATEGORIES = {
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


def auto_categorize_transactions(transactions: TransactionList) -> Dict[str, Any]:
    """
    Tool: Auto-assign categories to transactions based on simple keyword rules.
    Не претендует на идеал, но даёт разумное начальное разбиение.

    Args:
        transactions: list of Transaction dicts.

    Returns:
        dict with:
        - status
        - transactions: updated list with 'category' filled when possible.
    """
    updated: TransactionList = []

    for tx in transactions:
        new_tx = dict(tx)
        if not new_tx.get("category"):
            desc = new_tx.get("description", "").lower()
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


def compute_spending_analytics(transactions: TransactionList) -> Dict[str, Any]:
    """
    Tool: Compute basic spending analytics: totals, by category, by month, top merchants.
    Предполагаем, что отрицательные суммы = расход, положительные = доход/возврат.
    """
    if not transactions:
        return {"status": "error", "error_message": "No transactions provided."}

    df = pd.DataFrame(transactions)

    # защита от странных данных
    if "amount" not in df.columns:
        return {"status": "error", "error_message": "Missing 'amount' column."}

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount"])

    expenses = df[df["amount"] < 0].copy()
    expenses["abs_amount"] = expenses["amount"].abs()

    total_spent = float(expenses["abs_amount"].sum()) if not expenses.empty else 0.0

    # by category
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

    # by month
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

    # top merchants (по description)
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


def detect_anomalies(transactions: TransactionList) -> Dict[str, Any]:
    """
    Tool: naive anomaly detection — unusually large expenses vs медианы по категории.
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

    threshold = med + 2 * std
    mask = (df["abs_amount"] > threshold) & (df["abs_amount"] > 50)
    anomalies = df[mask].sort_values("abs_amount", ascending=False)

    return {
        "status": "success",
        "anomalies": anomalies.to_dict(orient="records"),
    }


# ---------- Export / reporting ----------


def export_categorized_csv(
    transactions: TransactionList, path: str = "output/categorized_transactions.csv"
) -> Dict[str, Any]:
    """
    Tool: Save categorized transactions to CSV.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(transactions)
    df.to_csv(out_path, index=False)
    return {"status": "success", "path": str(out_path)}


def export_analytics_json(
    analytics: Dict[str, Any], path: str = "output/analytics_summary.json"
) -> Dict[str, Any]:
    """
    Tool: Save analytics dict as pretty JSON.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    return {"status": "success", "path": str(out_path)}
