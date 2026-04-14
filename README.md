# AgentGuard

Real-time cost observability and guardrails for AI agents.

Track LLM spend, set budget thresholds, and auto-pause agents before they blow up your bill.

## Install

```bash
pip install agentguard
```

## Quick Start

```python
from agentguard import AgentGuard, AgentEvent

guard = AgentGuard(
    api_key="ag_...",
    agent_id="my-sales-agent",
    cost_threshold=10.0,          # auto-pause at $10/day
    slack_webhook="https://...",  # optional alert
)

# Custom agent — wrap with decorator
@guard.track
def run_my_agent():
    # your agent logic here
    alive = guard.send_event(AgentEvent(
        agent_id="my-sales-agent",
        event_type="llm_call",
        model="gpt-4o",
        input_tokens=500,
        output_tokens=300,
    ))
    if not alive:
        print("Agent paused — cost threshold reached")
        return
```

## LangChain / LangGraph

```python
from agentguard import AgentGuard

guard = AgentGuard(api_key="ag_...", agent_id="my-agent", cost_threshold=5.0)

# Drop-in callback — tracks every LLM call automatically
chain = my_chain.with_config(callbacks=[guard.callback])
result = chain.invoke({"input": "do something"})
```

## Supported Models

| Model | Input (per 1M) | Output (per 1M) |
|-------|---------------|----------------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| claude-3-5-sonnet | $3.00 | $15.00 |
| claude-3-5-haiku | $0.80 | $4.00 |
| gemini-1.5-pro | $1.25 | $5.00 |

## Dashboard

View live costs, event feed, and manage agents at [agent-guard-nine.vercel.app](https://agent-guard-nine.vercel.app).

## Links

- Dashboard: https://agent-guard-nine.vercel.app
- Backend API: https://agent-guard-production-dcdd.up.railway.app/docs
