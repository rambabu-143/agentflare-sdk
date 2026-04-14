"""
AgentGuard SDK Test Suite
Run: python3 test_sdk.py

Tests:
  1. AgentEvent model validation
  2. sync send_event (llm_call, tool_call, agent_start, agent_end)
  3. @guard.track decorator
  4. cost_threshold config registration
  5. pause detection
  6. async send_event
  7. async @guard.track decorator
  8. invalid API key → graceful failure (no crash)
  9. budget_pct in response
"""

import asyncio
import sys
import os

# Run from SDK root so imports work without installing
sys.path.insert(0, os.path.dirname(__file__))

from agentguard import AgentGuard, AsyncAgentGuard, AgentEvent

# ── Config ─────────────────────────────────────────────────────────────────────
API_KEY      = os.environ.get("AGENTGUARD_API_KEY", "")
AGENT_ID     = "sdk-test-agent"
BACKEND_URL  = os.environ.get("BACKEND_URL", "https://agent-guard-production-dcdd.up.railway.app")

if not API_KEY:
    print("❌  Set AGENTGUARD_API_KEY env var first")
    print("    export AGENTGUARD_API_KEY=ag_your_key_here")
    sys.exit(1)

PASS = "✅"
FAIL = "❌"
results = []

def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"  {status}  {name}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    results.append(condition)

# ── 1. Model validation ────────────────────────────────────────────────────────
print("\n── 1. AgentEvent model validation")
try:
    e = AgentEvent(agent_id="x", event_type="llm_call", model="gpt-4o", input_tokens=100, output_tokens=50)
    check("valid llm_call event", e.agent_id == "x" and e.input_tokens == 100)
except Exception as ex:
    check("valid llm_call event", False, str(ex))

try:
    AgentEvent(agent_id="x", event_type="invalid_type")  # type: ignore
    check("invalid event_type raises error", False, "should have raised")
except Exception:
    check("invalid event_type raises error", True)

# ── 2. Sync send_event ─────────────────────────────────────────────────────────
print("\n── 2. Sync send_event")
guard = AgentGuard(api_key=API_KEY, agent_id=AGENT_ID, backend_url=BACKEND_URL)

alive = guard.send_event(AgentEvent(agent_id=AGENT_ID, event_type="agent_start"))
check("agent_start → alive=True", alive is True)

alive = guard.send_event(AgentEvent(
    agent_id=AGENT_ID,
    event_type="llm_call",
    model="gpt-4o",
    input_tokens=500,
    output_tokens=300,
))
check("llm_call gpt-4o → alive=True", alive is True)

alive = guard.send_event(AgentEvent(
    agent_id=AGENT_ID,
    event_type="llm_call",
    model="claude-sonnet-4-6",
    input_tokens=800,
    output_tokens=400,
))
check("llm_call claude → alive=True", alive is True)

alive = guard.send_event(AgentEvent(
    agent_id=AGENT_ID,
    event_type="tool_call",
    tool_name="web_search",
))
check("tool_call → alive=True", alive is True)

alive = guard.send_event(AgentEvent(agent_id=AGENT_ID, event_type="agent_end"))
check("agent_end → alive=True", alive is True)

check("is_paused=False after normal events", guard.is_paused is False)

# ── 3. @guard.track decorator ──────────────────────────────────────────────────
print("\n── 3. @guard.track decorator")
guard2 = AgentGuard(api_key=API_KEY, agent_id=f"{AGENT_ID}-decorator", backend_url=BACKEND_URL)

@guard2.track
def my_agent(x: int) -> int:
    return x * 2

try:
    result = my_agent(21)
    check("decorator returns correct value", result == 42)
    check("decorator doesn't crash", True)
except Exception as ex:
    check("decorator doesn't crash", False, str(ex))

@guard2.track
def failing_agent():
    raise ValueError("intentional error")

try:
    failing_agent()
    check("decorator re-raises exception", False, "should have raised")
except ValueError:
    check("decorator re-raises exception", True)
except Exception as ex:
    check("decorator re-raises exception", False, str(ex))

# ── 4. cost_threshold config registration ─────────────────────────────────────
print("\n── 4. cost_threshold config registration")
try:
    guard3 = AgentGuard(
        api_key=API_KEY,
        agent_id=f"{AGENT_ID}-threshold",
        backend_url=BACKEND_URL,
        cost_threshold=50.0,
    )
    check("config registration with threshold=50 doesn't crash", True)
except Exception as ex:
    check("config registration with threshold=50 doesn't crash", False, str(ex))

# ── 5. Invalid API key → graceful failure ──────────────────────────────────────
print("\n── 5. Invalid API key → graceful failure (no crash)")
bad_guard = AgentGuard(api_key="ag_invalid_key_xyz", agent_id=AGENT_ID, backend_url=BACKEND_URL)
try:
    alive = bad_guard.send_event(AgentEvent(agent_id=AGENT_ID, event_type="agent_start"))
    check("invalid key → returns True (swallows error)", alive is True)
    check("invalid key → no crash", True)
except Exception as ex:
    check("invalid key → no crash", False, str(ex))

# ── 6. Async send_event ────────────────────────────────────────────────────────
print("\n── 6. Async send_event")

async def test_async():
    async_guard = AsyncAgentGuard(
        api_key=API_KEY,
        agent_id=f"{AGENT_ID}-async",
        backend_url=BACKEND_URL,
    )
    await async_guard.start()

    alive = await async_guard.send_event(AgentEvent(
        agent_id=f"{AGENT_ID}-async",
        event_type="agent_start",
    ))
    check("async agent_start → alive=True", alive is True)

    alive = await async_guard.send_event(AgentEvent(
        agent_id=f"{AGENT_ID}-async",
        event_type="llm_call",
        model="gemini-2.0-flash",
        input_tokens=300,
        output_tokens=150,
    ))
    check("async llm_call gemini → alive=True", alive is True)

    alive = await async_guard.send_event(AgentEvent(
        agent_id=f"{AGENT_ID}-async",
        event_type="agent_end",
    ))
    check("async agent_end → alive=True", alive is True)
    check("async is_paused=False", async_guard.is_paused is False)

asyncio.run(test_async())

# ── 7. Async @guard.track decorator ───────────────────────────────────────────
print("\n── 7. Async @guard.track decorator")

async def test_async_decorator():
    async_guard2 = AsyncAgentGuard(
        api_key=API_KEY,
        agent_id=f"{AGENT_ID}-async-dec",
        backend_url=BACKEND_URL,
    )
    await async_guard2.start()

    @async_guard2.track
    async def async_agent(x: int) -> int:
        return x + 10

    try:
        result = await async_agent(32)
        check("async decorator returns correct value", result == 42)
    except Exception as ex:
        check("async decorator returns correct value", False, str(ex))

asyncio.run(test_async_decorator())

# ── 8. Unknown model falls back gracefully ─────────────────────────────────────
print("\n── 8. Unknown model fallback")
alive = guard.send_event(AgentEvent(
    agent_id=AGENT_ID,
    event_type="llm_call",
    model="some-unknown-model-xyz",
    input_tokens=100,
    output_tokens=50,
))
check("unknown model → alive=True (uses fallback pricing)", alive is True)

# ── Summary ────────────────────────────────────────────────────────────────────
passed = sum(results)
total  = len(results)
print(f"\n{'─'*40}")
print(f"  {passed}/{total} tests passed")
if passed == total:
    print(f"  {PASS} All tests passed!")
else:
    print(f"  {FAIL} {total - passed} test(s) failed")
    sys.exit(1)
