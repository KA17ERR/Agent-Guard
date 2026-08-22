"""
Import every model here so a single `import app.models` registers all
tables with Base before create_all() runs. Order matters only in that a
model referenced by a relationship string (e.g. "Tool") must be imported
somewhere before mappers are configured — importing them all in one place
here avoids any ordering headaches.
"""
from app.models.agent import Agent, AgentVersion  # noqa: F401
from app.models.tool import Tool  # noqa: F401
from app.models.scenario import Scenario  # noqa: F401
from app.models.test_run import TestRun  # noqa: F401
from app.models.trace import Trace  # noqa: F401
from app.models.failure import Failure  # noqa: F401
