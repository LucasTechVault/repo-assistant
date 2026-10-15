"""
Validated data crossing:
    - Application
    - Model
    - Runtime
    - Tool
boundaries.
"""

from pathlib import Path
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StrictStr,
    StringConstraints,
    field_validator,
    model_validator,
)

NonEmptyText = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
ToolName = Annotated[str, StringConstraints(strict=True, pattern=r"^[a-z][a-z0-9_]*$")]

RunStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
TerminalStatus = Literal["completed", "failed", "cancelled"]


class ContractModel(BaseModel):
    """Shared validation rules for agent contracts."""
    
    model_config = ConfigDict(
        extra="forbid", # forbid hallucinated key-values
        frozen=True, # immutable
        revalidate_instances="always", # always check obj, regardless whether checked before
        allow_inf_nan=False # reject hallucinated inf / nan
    )

class ToolCall(ContractModel):
    """
    Proposed tool invocation, from Model to Runtime. This does not authorize execution.
    """
    
    kind: Literal["tool_call"] = "tool_call"
    run_id: UUID # Start to end of a single run
    action_id: UUID # link ToolCall to ToolResult
    tool_name: ToolName
    arguments: dict[str, JsonValue] = Field(default_factory=dict)


class ToolResult(ContractModel):
    """Executor-owned evidence associated with a proposed ToolCall."""
    
    run_id: UUID # Every ToolCall & ToolResult is in a Run
    action_id: UUID # To map to ToolCall (ToolCall, ToolResult) -> 1 action_id
    tool_name: ToolName
    status: Literal["succeeded", "failed"]
    output: StrictStr = "" # empty strings are valid success state.
    error: NonEmptyText | None = None
    
    @model_validator(mode="after") # validate after object created
    def validate_outcome(self) -> Self:
        if (self.status == "failed") != (self.error is not None):
            raise ValueError("Failed observations require an error. Successful ones forbid it.")
        return self
    

# Application Boundary contract - Created when user send request
class AgentRequest(ContractModel):
    """Application-owned task identity and repository location."""
    
    run_id: UUID
    repo_path: Path
    issue: NonEmptyText
    
    @field_validator("repo_path") # allow define custom validation functions when model instantiated
    @classmethod
    def require_absolute_path(cls, value: Path) -> Path:
        if not value.is_absolute():
            raise ValueError("repo_path must be absolute; resolve it at application boundary.")
        return value


class AgentResult(ContractModel):
    """Runtime outcome and observations. TaskCompletion does not guarantee objective met."""
    
    run_id: UUID
    status: TerminalStatus # guarantees finished result cannot be "pending" / "running" etc.
    summary: NonEmptyText
    observations: tuple[ToolResult, ...] = () # Tuple of ToolResult(s)


class FinishAction(ContractModel):
    """A proposal to finish reasoning, without claiming verified repair."""
    
    kind: Literal["finish"] = "finish"
    run_id: UUID
    action_id: UUID
    summary: NonEmptyText

# AgentAction can either be ToolCall or FinishAction
# discriminator = `kind` means ToolCall & FinishAction must have `kind` field for discrimination check.
AgentAction = Annotated[ToolCall | FinishAction, Field(discriminator="kind")] 
