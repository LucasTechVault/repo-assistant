"""Passing happy path and real failing regression tests for the deliberate defect."""

import pytest
from broken_python_api.orders import create_order


def test_create_order_accepts_positive_quantity() -> None:
    assert create_order(3) == {"quantity": 3, "status": "created"}


@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_create_order_rejects_non_positive_quantity(quantity: int) -> None:
    with pytest.raises(ValueError):
        create_order(quantity)
