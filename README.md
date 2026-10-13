# mcp-kite-demo

[![tests](https://img.shields.io/badge/tests-pytest-blue)](tests/)
[![python](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)
[![uv](https://img.shields.io/badge/managed%20by-uv-5C4EE5)](https://docs.astral.sh/uv/)

Self-improving MCP agent with a deterministic eval harness, built as a
reference project for the Platform AI Engineer role (Team KITE,
ART Plattform, Capacity2Schedule).

## Why this exists

The role asks for practical MCP experience, agentic skills, and making
the quality of agentic systems measurable. This repo demonstrates all
three end-to-end on a fully local stack.

- a real MCP server with typed tools over stdio
- an agentic loop driven by a local Ollama model
- a fixed benchmark suite with a deterministic scorer, no LLM-as-judge
- a self-improving loop: baseline, mutate, evaluate, accept or reject

## Architecture

    user query
        |
        v
    Ollama chat with tool schemas     <- list_tools from MCP
        |
        v
    tool_call emitted by the model
        |
        v
    MCP server executes the tool      <- stdio subprocess
        |
        v
    tool result fed back to the model
        |
        v
    final answer

    scored by judge.py against benchmarks/tasks.json
    fed into loop.py which mutates config and accepts improvements

## Layout

    src/kite_agent/server.py      MCP server, pure helpers plus MCP wrapper
    src/kite_agent/agent_core.py  agentic loop, parameterized by AgentConfig
    src/kite_agent/cli.py         thin CLI, entry point kite-agent
    src/kite_agent/judge.py       deterministic scorer, no LLM in the loop
    src/kite_agent/loop.py        self-improving loop, entry point kite-loop
    benchmarks/tasks.json         fixed benchmark suite, versioned in git
    tests/                        pytest coverage for judge, agent, server

## Install

    uv sync --extra dev

Requires Python 3.12 or newer, Ollama running locally with
`qwen3:1.7b` pulled.

## Run

    uv run kite-agent "Read requirements.txt in mcp-kite-demo and count the words."
    uv run kite-loop 3 42

`history.jsonl` records every generation with config fingerprint, score,
and accept or reject decision.

## Test

    uv run pytest -v
    uv run ruff check src tests

## Guardrails

- Safe root is fixed to the user `Projects` folder. Any path that escapes
  it is rejected.
- Every read is capped by `max_chars`, bounding token cost per call.
- The agent loop is bounded by `max_steps`.
- The self-improving loop is bounded by the mutation space size.

## Methodology

Deterministic scorer, no LLM in the loop. Each task is scored on:

- tool recall and precision against the expected tool set
- call order as a subsequence of the expected sequence
- argument sanity, catching known failure modes such as passing a
  filename to `word_count` instead of the file content
- answer correctness, matching required or any-of keywords and
  penalizing empty success claims with no numeric evidence

Composite is a weighted sum. The suite is versioned in git so that a
model change can be evaluated against the same baseline.

## Known failure mode

`qwen3:1.7b` occasionally loses the content of an earlier tool result,
passes a filename instead of file content to the next tool, and then
hallucinates a success message. This is documented as
`regression_ctx_loss` in `benchmarks/tasks.json` and caught
automatically by `judge.args_sane`. The mutation space in `loop.py`
includes a prompt that explicitly warns against this pattern.

## Requirements

Python 3.12 or newer.
Ollama running locally with `qwen3:1.7b` pulled.
`mcp` pinned below 2 because v2 renamed `FastMCP` to `MCPServer`.
