"""Thin CLI over agent_core for manual runs."""

from __future__ import annotations

import asyncio
import sys

from kite_agent.agent_core import AgentConfig, run_agent

DEFAULT_PROMPT = "You are a concise assistant. Use tools when helpful."


async def run(query: str) -> None:
    config = AgentConfig(system_prompt=DEFAULT_PROMPT)
    print(f"[config] {config.fingerprint()}")

    result = await run_agent(query, config)
    print(f"[steps] {result.steps}")
    for call in result.tool_calls:
        print(f"  [tool] {call['name']}({call['args']})")
    if result.error:
        print(f"[error] {result.error}")
    print("\n=== FINAL ANSWER ===")
    print(result.final_answer)


def main() -> None:
    query = " ".join(sys.argv[1:]) or "List the files in mcp-kite-demo."
    asyncio.run(run(query))


if __name__ == "__main__":
    main()
