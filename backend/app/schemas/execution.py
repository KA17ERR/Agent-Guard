"""
Schemas for the LLM-powered demo agent's execution loop (Section 8).

`AgentStepDecision` is what we ask the LLM to produce on every turn: either
"respond" (agent is done, give the final answer) or "call_tool" (agent wants
to invoke one sandboxed tool next). Forcing this shape via structured output
is what lets AgentExecutor detect tool calls reliably instead of parsing
free text.
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentStepDecision(BaseModel):
    action: Literal["respond", "call_tool"]
    # Required when action == "call_tool"
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = Field(default_factory=dict)
    # Required when action == "respond"
    final_response: Optional[str] = None
    # The agent's own short rationale for this step — included in the trace
    # for human review, not used for control flow.
    thought: str = ""


class TraceEvent(BaseModel):
    step: int
    type: Literal["llm_decision", "tool_call", "final_response", "error"]
    data: Dict[str, Any]


class ToolCallRecord(BaseModel):
    step: int
    tool_name: str
    params: Dict[str, Any]
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    destructive: bool = False
    risk_level: str = "low"


class ExecutionResult(BaseModel):
    final_response: str = ""
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    steps: int = 0
    trace: List[TraceEvent] = Field(default_factory=list)
    # completed | max_steps_exceeded | error
    status: Literal["completed", "max_steps_exceeded", "error"] = "completed"
