"""
Exceptions raised by mock tool handlers.

ToolValidationError = the caller (the agent under test) supplied bad/missing
parameters — this is closer to an "invalid tool call" failure.
ToolExecutionError = parameters were well-formed but the action couldn't be
completed given the current sandbox state (e.g. order already refunded) —
this is closer to a "task failure" / business-logic failure.
Both are caught by the registry and turned into a failed ToolCallResult
rather than propagating, so a single bad tool call never crashes a run.
"""


class ToolError(Exception):
    """Base class for all mock tool errors."""


class ToolValidationError(ToolError):
    pass


class ToolExecutionError(ToolError):
    pass


class ToolNotFoundError(ToolError):
    pass
