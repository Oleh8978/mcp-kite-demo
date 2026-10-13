# MCP KITE Demo

Self-improving MCP agent for the Platform AI Engineer role (Team KITE).

## What this is

A stdio MCP server exposes typed tools. A local Ollama model drives an
agentic loop. On top of that, a deterministic eval harness runs a fixed
task suite, scores tool selection and final answers, and drives a
self-improving loop: baseline, mutate, evaluate, accept or reject.

## Files

server.py       MCP server with four tools
agent_core.py   reusable agent loop parameterized by AgentConfig
agent.py        thin CLI over agent_core
tasks.json      fixed benchmark suite
judge.py        deterministic scorer, no LLM in the loop
loop.py         self-improving loop, writes history.jsonl

## Run

python agent.py "List the files in mcp-kite-demo."
python loop.py 3 42

## Guardrails

Safe root is fixed to the user Projects folder. Any path that escapes
it is rejected. Every read is capped to bound token cost. The loop
is bounded by max_steps and by the mutation space size.

## Requirements

Python 3.10 or newer, Ollama running locally with qwen3:1.7b pulled,
mcp pinned below 2 because v2 renamed FastMCP to MCPServer.
