"""Async version of AgentGuardTracker — for FastAPI / async agents."""

import httpx
import functools
from .models import AgentEvent


class AsyncAgentGuardTracker:
    def __init__(
        self,
        api_key: str,
        agent_id: str,
        backend_url: str = "https://agent-guard-production-dcdd.up.railway.app",
        cost_threshold: float | None = None,
        slack_webhook: str | None = None,
    ):
        self.api_key = api_key
        self.agent_id = agent_id
        self.backend_url = backend_url.rstrip("/")
        self._paused = False
        self._cost_threshold = cost_threshold
        self._slack_webhook = slack_webhook

    async def _register_config(self, threshold: float, slack_webhook: str | None):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.backend_url}/config",
                    json={
                        "agent_id": self.agent_id,
                        "cost_threshold_usd": threshold,
                        "slack_webhook_url": slack_webhook,
                    },
                    headers={"x-api-key": self.api_key},
                    timeout=5,
                )
        except Exception:
            pass

    async def start(self):
        """Call once after creating the tracker to register config."""
        if self._cost_threshold is not None:
            await self._register_config(self._cost_threshold, self._slack_webhook)
        return self

    async def send_event(self, event: AgentEvent) -> bool:
        """
        Async send. Returns False if agent is paused.
        """
        if self._paused:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.backend_url}/events",
                    json=event.model_dump(),
                    headers={"x-api-key": self.api_key},
                    timeout=5,
                )
                data = resp.json()
                if data.get("paused"):
                    self._paused = True
                    return False
        except Exception:
            pass
        return True

    @property
    def is_paused(self) -> bool:
        return self._paused

    def track(self, fn):
        """Async decorator — emit agent_start/agent_end around an async function."""
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            await self.send_event(AgentEvent(agent_id=self.agent_id, event_type="agent_start"))
            try:
                result = await fn(*args, **kwargs)
                await self.send_event(AgentEvent(agent_id=self.agent_id, event_type="agent_end"))
                return result
            except Exception as exc:
                await self.send_event(AgentEvent(
                    agent_id=self.agent_id,
                    event_type="agent_end",
                    metadata={"error": str(exc)},
                ))
                raise
        return wrapper
