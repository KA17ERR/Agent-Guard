"""
SandboxState holds all the mock "world state" for a single test run — fake
orders, fake customers, and a running log of every tool call made against
it. A fresh SandboxState is created per scenario execution so runs never
leak state into one another, which is what makes deterministic replay
possible later (Section 8): same seed data + same scenario => same trace.
"""
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _seed_customers() -> Dict[str, dict]:
    return {
        "cust_1": {
            "customer_id": "cust_1",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "account_status": "active",
        },
        "cust_2": {
            "customer_id": "cust_2",
            "name": "Bob Martinez",
            "email": "bob@example.com",
            "account_status": "active",
        },
    }


def _seed_orders() -> Dict[str, dict]:
    return {
        "ORD-1001": {
            "order_id": "ORD-1001",
            "customer_id": "cust_1",
            "item": "Wireless Headphones",
            "amount": 79.99,
            "status": "delivered",
            "refunded": False,
        },
        "ORD-1002": {
            "order_id": "ORD-1002",
            "customer_id": "cust_1",
            "item": "Phone Case",
            "amount": 15.99,
            "status": "delivered",
            "refunded": False,
        },
        "ORD-2001": {
            "order_id": "ORD-2001",
            "customer_id": "cust_2",
            "item": "Laptop Stand",
            "amount": 45.00,
            "status": "shipped",
            "refunded": False,
        },
    }


@dataclass
class ToolCallLogEntry:
    """One recorded call against the sandbox — the raw material for traces."""
    index: int
    tool_name: str
    params: Dict[str, Any]
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    is_destructive: bool

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "tool_name": self.tool_name,
            "params": self.params,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "is_destructive": self.is_destructive,
        }


@dataclass
class SandboxState:
    customers: Dict[str, dict] = field(default_factory=_seed_customers)
    orders: Dict[str, dict] = field(default_factory=_seed_orders)
    emails: List[dict] = field(default_factory=list)
    call_log: List[ToolCallLogEntry] = field(default_factory=list)

    @classmethod
    def fresh(cls) -> "SandboxState":
        """Always returns a brand-new, independent copy of the seed world."""
        return cls(customers=_seed_customers(), orders=_seed_orders())

    def snapshot(self) -> dict:
        """A deep-copied, JSON-serializable view of current state (for traces/debugging)."""
        return {
            "customers": copy.deepcopy(self.customers),
            "orders": copy.deepcopy(self.orders),
            "emails": copy.deepcopy(self.emails),
            "call_log": [entry.to_dict() for entry in self.call_log],
        }
