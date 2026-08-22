"""
Schemas for the LLM connectivity test endpoint (Section 6).
"""
from pydantic import BaseModel


class LLMTestResponse(BaseModel):
    provider: str
    model: str
    ok: bool
    sample_output: str = ""
    error: str = ""


class _PingReply(BaseModel):
    """Minimal structured-output schema used purely to smoke-test that
    generate_structured_output() round-trips real JSON through the model."""
    reply: str
