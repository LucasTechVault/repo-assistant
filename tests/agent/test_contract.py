from pathlib import Path
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from repo_repair.agent.contracts import (
    AgentAction,
    AgentRequest,
    AgentResult,
    ContractModel,
    FinishAction,
    ToolCall,
    ToolObservation,
)

RUN_ID = UUID(int=1)
ACTION_ID = UUID(int=2)


def test_contracts_round_trip_through_json(tmp_path: Path) -> None:
    observation = ToolObservation(
        run_id=RUN_ID,
        action_id=ACTION_ID,
        tool_name="read_file",
        status="succeeded",
        output="  source code\n",
    )

    models: tuple[ContractModel, ...] = (
        AgentRequest(
            run_id=RUN_ID,
            repo_path=tmp_path.resolve(),
            issue="Find missing quantity validation",
        ),
        ToolCall(
            run_id=RUN_ID,
            action_id=ACTION_ID,
            tool_name="read_file",
            arguments={"path": "orders.py", "start_line": 1},
        ),
        FinishAction(
            run_id=RUN_ID,
            action_id=UUID(int=3),
            summary="Investigation complete",
        ),
        observation,
        AgentResult(
            run_id=RUN_ID,
            status="completed",
            summary="Investigation complete",
            observations=(observation,),
        ),
    )

    for model in models:
        restored = type(model).model_validate_json(model.model_dump_json())
        assert restored == model

    assert observation.output == "  source code\n"


@pytest.mark.parametrize("issue", ["", "   "])
def test_request_rejects_empty_issue(issue: str, tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        AgentRequest(
            run_id=RUN_ID,
            repo_path=tmp_path.resolve(),
            issue=issue,
        )


def test_request_rejects_relative_path() -> None:
    with pytest.raises(ValidationError, match="must be absolute"):
        AgentRequest(
            run_id=RUN_ID,
            repo_path=Path("relative"),
            issue="Investigate",
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ToolCall.model_validate(
            {
                "run_id": RUN_ID,
                "action_id": ACTION_ID,
                "tool_name": "read_file",
                "arguments": {},
                "authorized": True,
            }
        )


def test_action_discriminator_selects_the_contract() -> None:
    adapter: TypeAdapter[AgentAction] = TypeAdapter(AgentAction)

    action = adapter.validate_python(
        {
            "kind": "finish",
            "run_id": RUN_ID,
            "action_id": ACTION_ID,
            "summary": "Done investigating",
        }
    )

    assert isinstance(action, FinishAction)

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "kind": "execute_arbitrary_command",
                "run_id": RUN_ID,
                "action_id": ACTION_ID,
            }
        )


@pytest.mark.parametrize(
    ("status", "error"),
    [
        ("failed", None),
        ("succeeded", "Unexpected error"),
    ],
)
def test_observation_rejects_inconsistent_outcome(
    status: str,
    error: str | None,
) -> None:
    with pytest.raises(ValidationError):
        ToolObservation.model_validate(
            {
                "run_id": RUN_ID,
                "action_id": ACTION_ID,
                "tool_name": "read_file",
                "status": status,
                "error": error,
            }
        )