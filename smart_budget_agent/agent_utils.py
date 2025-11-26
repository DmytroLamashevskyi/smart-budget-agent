from typing import TypedDict, List, Optional

class Transaction(TypedDict, total=False):
    """
    Standardized transaction format used across tools & agents.
    All fields are JSON-friendly.
    """
    date: str           # ISO date: "2025-11-26"
    description: str
    amount: float
    currency: str
    category: Optional[str]
    source: Optional[str]


TransactionList = List[Transaction]