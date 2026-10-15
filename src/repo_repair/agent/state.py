"""Single-action state machine with deterministic, side-effect free transitions."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, TypeAdapter, model_validator

from repo_repair.agent.contracts import (
    ContractModel,
    AgentRequest, AgentResult, AgentAction,
    ToolCall, ToolResult, FinishAction,
    RunStatus,
    NonEmptyText
)

class AgentState(ContractModel):
    """Authoritative snapshot of a run."""
    
    request: AgentRequest
    status: RunStatus = "pending"
    actions: tuple[AgentAction, ...] = ()
    observations: tuple[ToolResult, ...] = ()
    result: AgentResult | None = None 

    # dynamically check if pending tool-call without creating `is_waiting` flag.
    # dynamic - `running` and actions more than results mean pending tool execution
    @property 
    def pending_call(self) -> ToolCall | None:
        if self.status == "running" and len(self.actions) > len(self.observations):
            action = self.actions[-1]
            if isinstance(action, ToolCall):
                return action
        return None

    @model_validator(mode="after")
    def validate_invariants(self) -> Self:
        
        # 1. Validate all actions belong to same run
        run_id = self.request.run_id
        
        if any(action.run_id != run_id for action in self.actions):
            raise ValueError("All actions must belong to the current run.")
    
        # 2. Ensure unique action (ToolCall - ToolResult pair)
        action_ids = [action.action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("action IDs must be unique within run for idempotence.")
        
        # 3. Ensure sequential Toolcalls - strictly for ReAct loop
        calls = [action for action in self.actions if isinstance(action, ToolCall)]
        finishes = [action for action in self.actions if isinstance(action, FinishAction)]
        
        outstanding = len(calls) - len(finishes)
        if outstanding not in (0, 1):
            raise ValueError("Each tool call needs one observation before another is proposed.")
        
        # 4. Validate Observation <-> ToolCall
        for call, observation in zip(calls, self.observations, strict=False):
            if (
                observation.run_id,
                observation.action_id,
                observation.tool_name
            ) != (
                run_id, call.action_id, call.tool_name
            ):
                raise ValueError("Observations must match Toolcalls in order, by run, ID and name.")
        
        # 5. Validate FinishAction must be last action
        if finishes and (
            len(finishes) != 1 or # Only 1 finish action allowed (last)
            self.actions[-1] != finishes[-1] or # last action doesnt match finish
            self.status != "completed" or # finish action not completed
            outstanding != 0 # outstanding despite finish
        ):
            raise ValueError("finish must be last action of a completed run with no pending call.")
        
        if self.status == "pending" and (
            self.actions or self.observations or self.result
        ):
            raise ValueError(
                "pending runs cannot contain actions, observations, or a result"
            )

        if self.status in ("pending", "running"):
            if self.result is not None:
                raise ValueError("active runs cannot have a terminal result")
        else:
            if self.result is None:
                raise ValueError("terminal runs require a result")

            if (
                self.result.run_id,
                self.result.status,
                self.result.observations,
            ) != (run_id, self.status, self.observations):
                raise ValueError(
                    "terminal result must match the run, status, and observations"
                )

        if self.status == "completed":
            if (
                not finishes
                or self.result is None
                or self.result.summary != finishes[0].summary
            ):
                raise ValueError(
                    "completed runs require a finish action and matching result summary"
                )

        return self
        
# == Events ==
class RunStarted(ContractModel):
    kind: Literal["run_started"] = "run_started"
    run_id: UUID


class ActionProposed(ContractModel):
    kind: Literal["action_proposed"] = "action_proposed"
    action: AgentAction

    @property
    def run_id(self) -> UUID:
        return self.action.run_id


class ObservationReceived(ContractModel):
    kind: Literal["observation_received"] = "observation_received"
    observation: ToolResult

    @property
    def run_id(self) -> UUID:
        return self.observation.run_id


class RunStopped(ContractModel):
    kind: Literal["run_stopped"] = "run_stopped"
    run_id: UUID
    status: Literal["failed", "cancelled"]
    reason: NonEmptyText


AgentEvent = Annotated[
    RunStarted | ActionProposed | ObservationReceived | RunStopped,
    Field(discriminator="kind"),
]

_event_adapter: TypeAdapter[AgentEvent] = TypeAdapter(AgentEvent)

class TransitionError(ValueError):
    """A valid event is illegal for the current state."""
    
    
def _replace(state: AgentState, **updates: object) -> AgentState:
    """Construct a validated snapshot rather than bypassing validation."""
    return AgentState.model_validate({**state.model_dump(), **updates})

def reduce_state(state: AgentState, event: AgentEvent) -> AgentState:
    """Apply one event without mutation, clocks, ID generation, or external I/O."""

    # Revalidate and detach mutable payloads from the caller's objects.
    state = AgentState.model_validate(state.model_dump())
    event = _event_adapter.validate_python(event.model_dump())

    if event.run_id != state.request.run_id:
        raise TransitionError("event belongs to a different run")

    if state.status in ("completed", "failed", "cancelled"):
        raise TransitionError("terminal runs cannot accept more events")

    if isinstance(event, RunStarted):
        if state.status != "pending":
            raise TransitionError("only pending runs can start")
        return _replace(state, status="running")

    if state.status != "running":
        raise TransitionError("start the run before applying this event")

    if isinstance(event, RunStopped):
        return _replace(
            state,
            status=event.status,
            result=AgentResult(
                run_id=event.run_id,
                status=event.status,
                summary=event.reason,
                observations=state.observations,
            ),
        )

    if isinstance(event, ActionProposed):
        if state.pending_call is not None:
            raise TransitionError(
                "receive the pending tool observation before proposing an action"
            )

        action = event.action
        if any(previous.action_id == action.action_id for previous in state.actions):
            raise TransitionError("action ID has already been used")

        actions = (*state.actions, action)

        if isinstance(action, FinishAction):
            return _replace(
                state,
                status="completed",
                actions=actions,
                result=AgentResult(
                    run_id=action.run_id,
                    status="completed",
                    summary=action.summary,
                    observations=state.observations,
                ),
            )

        return _replace(state, actions=actions)

    pending = state.pending_call
    if pending is None:
        raise TransitionError("there is no pending tool call to observe")

    observation = event.observation
    if (
        observation.action_id,
        observation.tool_name,
    ) != (pending.action_id, pending.tool_name):
        raise TransitionError("observation does not match the pending tool call")

    return _replace(
        state,
        observations=(*state.observations, observation),
    )