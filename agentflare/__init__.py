"""AgentFlare — AI agent cost observability SDK."""

from .tracker import AgentFlareTracker
from .async_tracker import AsyncAgentFlareTracker
from .models import AgentEvent

try:
    from .callbacks import AgentFlareCallback
except ImportError:
    AgentFlareCallback = None  # type: ignore


class AgentFlare(AgentFlareTracker):
    """
    Sync entry point. Use for standard Python agents.

    Usage::

        guard = AgentFlare(
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
        if AgentFlareCallback is None:
            raise ImportError("Install langchain-core to use guard.callback")
        return AgentFlareCallback(self)


class AsyncAgentFlare(AsyncAgentFlareTracker):
    """
    Async entry point. Use for FastAPI / async agents.

    Usage::

        guard = AsyncAgentFlare(
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
    "AgentFlare",
    "AsyncAgentFlare",
    "AgentFlareTracker",
    "AsyncAgentFlareTracker",
    "AgentEvent",
    "AgentFlareCallback",
]
__version__ = "0.2.0"
