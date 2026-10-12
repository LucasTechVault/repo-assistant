# Broken Python API fixture

This independent learning fixture deliberately violates its intended order contract.
`create_order(quantity)` should return `{"quantity": quantity, "status": "created"}` for
positive integers and raise `ValueError` for zero or negative integers. Validation is
intentionally missing. No HTTP server is included.

From this directory:

```sh
uv sync --locked
uv run pytest
```

Expected result: **1 passed, 3 failed, exit code 1**. All three regression cases fail with
`DID NOT RAISE ValueError`. No tests are skipped or marked as expected failures.

From the assistant project root, the shared dev environment can run the same suite:

```sh
uv run pytest -c examples/broken-python-api/pyproject.toml examples/broken-python-api/tests
```

Keep the defect intact at M00; later milestones can use it to demonstrate verified repair.
