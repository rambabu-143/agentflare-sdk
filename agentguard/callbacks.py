"""LangChain callback handler for AgentGuard."""

from typing import Any
from uuid import UUID

from .models import AgentEvent
from .tracker import AgentGuardTracker

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.outputs import LLMResult

    class AgentGuardCallback(BaseCallbackHandler):
        """Drop-in LangChain callback that tracks every LLM call."""

        def __init__(self, tracker: AgentGuardTracker):
            super().__init__()
            self.tracker = tracker

        # ── LLM events ────────────────────────────────────────────────────────

        def on_llm_end(
            self,
            response: LLMResult,
            *,
            run_id: UUID,
            parent_run_id: UUID | None = None,
            **kwargs: Any,
        ) -> None:
            for generations in response.generations:
                for gen in generations:
                    usage = getattr(gen, "generation_info", {}) or {}
                    # Different LLM providers use different keys
                    input_tokens = (
                        usage.get("input_tokens")
                        or usage.get("prompt_tokens")
                        or usage.get("prompt_token_count")
                        or 0
                    )
                    output_tokens = (
                        usage.get("output_tokens")
                        or usage.get("completion_tokens")
                        or usage.get("candidates_token_count")
                        or 0
                    )
                    model = usage.get("model_name") or kwargs.get("invocation_params", {}).get("model_name", "unknown")

                    self.tracker.send_event(
                        AgentEvent(
                            agent_id=self.tracker.agent_id,
                            event_type="llm_call",
                            model=model,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            metadata={"run_id": str(run_id)},
                        )
                    )

        # ── Tool events ───────────────────────────────────────────────────────

        def on_tool_start(
            self,
            serialized: dict[str, Any],
            input_str: str,
            *,
            run_id: UUID,
            **kwargs: Any,
        ) -> None:
            tool_name = serialized.get("name", "unknown")
            self.tracker.send_event(
                AgentEvent(
                    agent_id=self.tracker.agent_id,
                    event_type="tool_call",
                    tool_name=tool_name,
                    metadata={"run_id": str(run_id)},
                )
            )

        # ── Chain/agent lifecycle ─────────────────────────────────────────────

        def on_chain_start(self, *args, **kwargs) -> None:
            pass  # tracked at decorator level if desired

        def on_chain_end(self, *args, **kwargs) -> None:
            pass

except ImportError:
    # langchain not installed — AgentGuardCallback unavailable
    class AgentGuardCallback:  # type: ignore
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "LangChain is not installed. "
                "Run: pip install langchain-core"
            )
