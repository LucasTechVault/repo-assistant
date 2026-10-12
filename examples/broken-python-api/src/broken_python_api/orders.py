"""Order creation fixture; intentionally broken until a later repair milestone."""

from typing import TypedDict


class Order(TypedDict):
    quantity: int
    status: str


def create_order(quantity: int) -> Order:
    """Create an order; intended contract requires ValueError for quantity <= 0.

    BUG: validation is deliberately absent, so zero and negative quantities succeed.
    """
    return {"quantity": quantity, "status": "created"}
