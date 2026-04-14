from pydantic import BaseModel
from typing import Literal


class AgentEvent(BaseModel):
    agent_id: str
    event_type: Literal["llm_call", "tool_call", "agent_start", "agent_end"]
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    tool_name: str | None = None
    metadata: dict | None = None
