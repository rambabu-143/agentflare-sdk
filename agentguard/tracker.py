"""Core tracking logic — sends events to the AgentGuard backend."""

import httpx
from .models import AgentEvent


class AgentGuardTracker:
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

        # Register config if threshold provided
        if cost_threshold is not None:
            self._register_config(cost_threshold, slack_webhook)

    def _register_config(self, threshold: float, slack_webhook: str | None):
        try:
            with httpx.Client() as client:
                client.post(
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
            pass  # Don't block agent startup

    def send_event(self, event: AgentEvent) -> bool:
        """
        Send event to backend. Returns False if agent is paused (caller should stop).
        """
        if self._paused:
            return False
        try:
            with httpx.Client() as client:
                resp = client.post(
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
            pass  # Don't crash the agent on network errors
        return True

    @property
    def is_paused(self) -> bool:
        return self._paused

    def track(self, fn):
        """Decorator — wrap any function, emit agent_start/agent_end events."""
        import functools

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            self.send_event(
                AgentEvent(agent_id=self.agent_id, event_type="agent_start")
            )
            try:
                result = fn(*args, **kwargs)
                self.send_event(
                    AgentEvent(agent_id=self.agent_id, event_type="agent_end")
                )
                return result
            except Exception as exc:
                self.send_event(
                    AgentEvent(
                        agent_id=self.agent_id,
                        event_type="agent_end",
                        metadata={"error": str(exc)},
                    )
                )
                raise

        return wrapper
