from pathlib import Path
from typing import Literal
from uuid import UUID

import pytest
from pydantic import ValidationError

from repo_repair.agent.contracts import (
    AgentRequest,
    FinishAction,
    ToolCall,
    ToolObservation,
)
from repo_repair.agent.state import (
    ActionProposed,
    AgentState,
    ObservationReceived,
    RunStarted,
    RunStopped,
    TransitionError,
    reduce_state,
)

RUN_ID = UUID(int=1)
ACTION_ID = UUID(int=2)


def initial_state(tmp_path: Path) -> AgentState:
    return AgentState(
        request=AgentRequest(
            run_id=RUN_ID,
            repo_path=tmp_path.resolve(),
            issue="Investigate order validation",
        )
    )


def tool_call() -> ToolCall:
    return ToolCall(
        run_id=RUN_ID,
        action_id=ACTION_ID,
        tool_name="read_file",
        arguments={"path": "orders.py"},
    )


def finish_action() -> FinishAction:
    return FinishAction(
        run_id=RUN_ID,
        action_id=UUID(int=3),
        summary="Missing quantity validation identified",
    )


def successful_observation() -> ToolObservation:
    return ToolObservation(
        run_id=RUN_ID,
        action_id=ACTION_ID,
        tool_name="read_file",
        status="succeeded",
        output="def create_order(quantity): ...",
    )


def running_state(tmp_path: Path) -> AgentState:
    return reduce_state(initial_state(tmp_path), RunStarted(run_id=RUN_ID))


def waiting_state(tmp_path: Path) -> AgentState:
    return reduce_state(
        running_state(tmp_path),
        ActionProposed(action=tool_call()),
    )


def test_full_lifecycle_is_deterministic_and_round_trips(tmp_path: Path) -> None:
    initial = initial_state(tmp_path)
    events = (
        RunStarted(run_id=RUN_ID),
        ActionProposed(action=tool_call()),
        ObservationReceived(observation=successful_observation()),
        ActionProposed(action=finish_action()),
    )

    def replay() -> AgentState:
        state = initial
        for event in events:
            state = reduce_state(state, event)
        return state

    final = replay()

    assert final == replay()
    assert initial.status == "pending"
    assert initial.actions == ()
    assert final.status == "completed"
    assert final.pending_call is None
    assert final.result is not None
    assert final.result.observations == final.observations
    assert AgentState.model_validate_json(final.model_dump_json()) == final


@pytest.mark.parametrize("finish", [False, True])
def test_pending_call_blocks_another_action(tmp_path: Path, finish: bool) -> None:
    action = finish_action() if finish else tool_call()

    with pytest.raises(TransitionError, match="pending tool observation"):
        reduce_state(
            waiting_state(tmp_path),
            ActionProposed(action=action),
        )


def test_actions_require_a_started_run(tmp_path: Path) -> None:
    with pytest.raises(TransitionError, match="start the run"):
        reduce_state(
            initial_state(tmp_path),
            ActionProposed(action=tool_call()),
        )


def test_duplicate_start_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(TransitionError, match="only pending"):
        reduce_state(
            running_state(tmp_path),
            RunStarted(run_id=RUN_ID),
        )


def test_wrong_run_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(TransitionError, match="different run"):
        reduce_state(
            initial_state(tmp_path),
            RunStarted(run_id=UUID(int=99)),
        )


@pytest.mark.parametrize(
    ("action_id", "tool_name"),
    [
        (UUID(int=99), "read_file"),
        (ACTION_ID, "search_code"),
    ],
)
def test_observation_must_match_pending_call(
    tmp_path: Path,
    action_id: UUID,
    tool_name: str,
) -> None:
    observation = ToolObservation(
        run_id=RUN_ID,
        action_id=action_id,
        tool_name=tool_name,
        status="succeeded",
    )

    with pytest.raises(TransitionError, match="does not match"):
        reduce_state(
            waiting_state(tmp_path),
            ObservationReceived(observation=observation),
        )


def test_duplicate_observation_is_rejected(tmp_path: Path) -> None:
    event = ObservationReceived(observation=successful_observation())
    observed = reduce_state(waiting_state(tmp_path), event)

    with pytest.raises(TransitionError, match="no pending"):
        reduce_state(observed, event)


def test_action_ids_cannot_be_reused(tmp_path: Path) -> None:
    observed = reduce_state(
        waiting_state(tmp_path),
        ObservationReceived(observation=successful_observation()),
    )

    with pytest.raises(TransitionError, match="already been used"):
        reduce_state(observed, ActionProposed(action=tool_call()))


def test_tool_failure_is_feedback_not_automatic_run_failure(tmp_path: Path) -> None:
    observation = ToolObservation(
        run_id=RUN_ID,
        action_id=ACTION_ID,
        tool_name="read_file",
        status="failed",
        error="File not found",
    )

    state = reduce_state(
        waiting_state(tmp_path),
        ObservationReceived(observation=observation),
    )

    assert state.status == "running"
    assert state.pending_call is None
    assert state.observations[-1].error == "File not found"


@pytest.mark.parametrize("status", ["failed", "cancelled"])
def test_stop_can_abort_an_outstanding_call(
    tmp_path: Path,
    status: Literal["failed", "cancelled"],
) -> None:
    state = reduce_state(
        waiting_state(tmp_path),
        RunStopped(
            run_id=RUN_ID,
            status=status,
            reason="Execution interrupted",
        ),
    )

    assert state.status == status
    assert state.pending_call is None
    assert state.result is not None

    with pytest.raises(TransitionError, match="terminal"):
        reduce_state(
            state,
            ObservationReceived(observation=successful_observation()),
        )


def test_invalid_terminal_snapshot_is_rejected(tmp_path: Path) -> None:
    data = initial_state(tmp_path).model_dump()
    data["status"] = "completed"

    with pytest.raises(ValidationError, match="terminal runs require"):
        AgentState.model_validate(data)


def test_reducer_detaches_mutable_action_arguments(tmp_path: Path) -> None:
    event = ActionProposed(action=tool_call())
    before = running_state(tmp_path)
    after = reduce_state(before, event)

    assert isinstance(event.action, ToolCall)
    event.action.arguments["path"] = "changed.py"

    recorded = after.actions[0]
    assert isinstance(recorded, ToolCall)
    assert recorded.arguments["path"] == "orders.py"
    assert before.actions == ()