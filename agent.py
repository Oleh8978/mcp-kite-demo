"""Thin CLI over agent_core for manual runs."""

from __future__ import annotations

import asyncio
import sys

from agent_core import AgentConfig, run_agent

DEFAULT_PROMPT = "You are a concise assistant. Use tools when helpful."


async def main(query: str) -> None:
    config = AgentConfig(system_prompt=DEFAULT_PROMPT)
    print(f"[config] {config.fingerprint()}")

    run = await run_agent(query, config)
    print(f"[steps] {run.steps}")
    for call in run.tool_calls:
        print(f"  [tool] {call['name']}({call['args']})")
    if run.error:
        print(f"[error] {run.error}")
    print("\n=== FINAL ANSWER ===")
    print(run.final_answer)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "List the files in mcp-kite-demo."
    asyncio.run(main(query))
