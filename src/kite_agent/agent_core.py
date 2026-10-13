"""Reusable agent core: MCP client plus Ollama loop, parameterized by config."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from typing import Any

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_MODEL = "qwen3:1.7b"


@dataclass
class AgentConfig:
    system_prompt: str
    temperature: float = 0.2
    max_steps: int = 6
    model: str = DEFAULT_MODEL

    def fingerprint(self) -> str:
        digest = hashlib.md5(self.system_prompt.encode()).hexdigest()[:6]
        return f"{self.model}|t={self.temperature}|s={self.max_steps}|p={digest}"


@dataclass
class AgentRun:
    final_answer: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    steps: int = 0
    error: str | None = None


def to_ollama_tools(tools_response: Any) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema,
            },
        }
        for t in tools_response.tools
    ]


async def run_agent(user_query: str, config: AgentConfig) -> AgentRun:
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "kite_agent.server"],
    )
    result = AgentRun()

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            tools = to_ollama_tools(tools_response)

            messages: list[dict] = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": user_query},
            ]

            for step in range(1, config.max_steps + 1):
                result.steps = step
                response = ollama.chat(
                    model=config.model,
                    messages=messages,
                    tools=tools,
                    options={"temperature": config.temperature},
                    think=False,
                )
                msg = response["message"]
                messages.append(msg)

                tool_calls = msg.get("tool_calls") or []
                if not tool_calls:
                    result.final_answer = (msg.get("content") or "").strip()
                    return result

                for call in tool_calls:
                    name = call["function"]["name"]
                    args = call["function"]["arguments"] or {}
                    result.tool_calls.append({"name": name, "args": args})
                    tool_result = await session.call_tool(name, args)
                    text = tool_result.content[0].text if tool_result.content else ""
                    messages.append({"role": "tool", "content": text})

            result.error = "max_steps_exceeded"
            return result
