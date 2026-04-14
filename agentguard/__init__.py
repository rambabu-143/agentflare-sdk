"""AgentGuard — AI agent cost observability SDK."""

from .tracker import AgentGuardTracker
from .async_tracker import AsyncAgentGuardTracker
from .models import AgentEvent

try:
    from .callbacks import AgentGuardCallback
except ImportError:
    AgentGuardCallback = None  # type: ignore


class AgentGuard(AgentGuardTracker):
    """
    Sync entry point. Use for standard Python agents.

    Usage::

        guard = AgentGuard(
            api_key="ag_...",
            agent_id="my-sales-agent",
            cost_threshold=10.0,
            slack_webhook="https://hooks.slack.com/...",
        )

        # LangChain / LangGraph
        chain = my_chain.with_config(callbacks=[guard.callback])

        # Custom agent
        @guard.track
        def run_my_agent():
            ...
    """

    @property
    def callback(self):
        if AgentGuardCallback is None:
            raise ImportError("Install langchain-core to use guard.callback")
        return AgentGuardCallback(self)


class AsyncAgentGuard(AsyncAgentGuardTracker):
    """
    Async entry point. Use for FastAPI / async agents.

    Usage::

        guard = AsyncAgentGuard(
            api_key="ag_...",
            agent_id="my-async-agent",
            cost_threshold=10.0,
        )
        await guard.start()  # registers config with backend

        @guard.track
        async def run_my_agent():
            ...
    """
    pass


__all__ = [
    "AgentGuard",
    "AsyncAgentGuard",
    "AgentGuardTracker",
    "AsyncAgentGuardTracker",
    "AgentEvent",
    "AgentGuardCallback",
]
__version__ = "0.2.0"
