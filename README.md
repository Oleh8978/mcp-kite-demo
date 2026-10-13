# mcp-kite-demo

[![CI](https://github.com/Oleh8978/mcp-kite-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/Oleh8978/mcp-kite-demo/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)
[![uv](https://img.shields.io/badge/managed%20by-uv-5C4EE5)](https://docs.astral.sh/uv/)

MCP agent with a deterministic eval harness and a configuration search
over a bounded mutation space. Reference project for a Platform AI
Engineer role, focused on agentic systems, MCP tooling, and making the
quality of agentic pipelines measurable.

## Why this exists

The role this was built for asks for practical MCP experience, agentic
skills, and a way to make the quality of agentic systems measurable.
This repo demonstrates all three end-to-end on a fully local stack.

- a real MCP server with typed tools over stdio
- an agentic loop driven by a local Ollama model
- a fixed benchmark suite with a deterministic scorer
- a configuration search that mutates agent parameters and accepts a
  candidate only if its composite score strictly improves

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
    fed into search.py which mutates config and accepts improvements

## Layout

    src/kite_agent/server.py      MCP server, pure helpers plus MCP wrapper
    src/kite_agent/agent_core.py  agentic loop, parameterized by AgentConfig
    src/kite_agent/cli.py         thin CLI, entry point kite-agent
    src/kite_agent/judge.py       deterministic scorer, no LLM in the loop
    src/kite_agent/search.py      configuration search, entry point kite-search
    src/kite_agent/eval_gate.py   blocking quality gate, entry point kite-eval-gate
    benchmarks/tasks.json         fixed benchmark suite, versioned in git
    docs/adr/                     architecture decision records
    tests/                        pytest coverage for judge, agent, server, injection
    .gitlab-ci.yml                GitLab CI: lint -> test -> eval-gate
    .github/workflows/ci.yml      GitHub Actions mirror

## Install

    uv sync --extra dev

Requires Python 3.12 or newer, Ollama running locally with
`qwen3:1.7b` pulled.

## Run

    uv run kite-agent "Read pyproject.toml in mcp-kite-demo and count the words."
    uv run kite-search 3 42
    uv run kite-eval-gate --min-composite 0.70

`history.jsonl` records every generation with config fingerprint, score,
and accept or reject decision.

## Test and CI

    uv run pytest -v
    uv run ruff check src tests
    uv run ruff format src tests --check

CI runs three stages in order, each blocking:

1. lint — ruff check and format verification.
2. test — full pytest suite.
3. eval-gate — validates the benchmark suite is well-formed. In CI
   this runs in offline mode because the runner has no local Ollama.
   The full gate runs locally and fails if the baseline composite
   drops below the configured threshold.

## Guardrails

- Safe root is fixed to the user Projects folder. Any path that
  escapes it is rejected, including absolute paths and .. traversal.
- Every read is capped by max_chars.
- The agent loop is bounded by max_steps.
- The configuration search is bounded by the mutation space size.
- Task-specific forbid_arg_patterns drop the composite to near zero
  if the agent calls a tool with a forbidden argument. This is how
  prompt-injection resistance is tested.

## Methodology

Deterministic scorer, no LLM in the loop. Each task is scored on:

- tool recall and precision against the expected tool set
- call order as a subsequence of the expected sequence
- argument sanity, catching known failure modes such as passing a
  filename to word_count instead of the file content, and matching
  forbidden argument patterns
- answer correctness, matching required or any-of keywords and
  penalizing empty success claims with no numeric evidence

Composite is a weighted sum. See docs/adr/0001-deterministic-scorer.md
for the decision and the rejected alternative (LLM-as-judge).

## Results and caveats

Measured locally on 2026-10-13 with qwen3:1.7b on an M-series MacBook,
single seed 42.

| stage | composite | tasks |
|---|---|---|
| baseline | 0.8500 | 7 |
| generation 1 (ACCEPT) | 0.9500 | 7 |

The generation-1 gain comes almost entirely from one task:
scan_keywords moved from 0.40 to 0.95. On a seven-task suite that
single-task shift moves the aggregate by roughly 0.07.

Honest caveats:

- **Seven tasks, one seed, one small model.** This is a single-task
  result, not evidence about the search method.
- **Composite weights are a design choice, not a measurement.** The
  weights (0.35 / 0.15 / 0.15 / 0.15 / 0.20) reflect priorities of the
  target role. Changing them changes which configuration wins.
- **No repeated runs, no confidence interval.** Different seeds would
  produce different search paths.
- **No larger-model comparison yet.** Results do not transfer without
  re-running the suite. Adding models to MODELS in search.py is the
  extension point.
- **Benchmark extended after this measurement.** An eighth task,
  prompt_injection, was added later. Re-run kite-search to obtain a
  baseline against the current suite; see benchmarks/baseline.json.

The search is a **configuration search over a bounded mutation space
with an acceptance criterion**. It is not self-modifying code and does
not resemble Prometheus-style self-improvement. The mutations are
system_prompt, temperature, max_steps, and model. The only acceptance
rule is score > best_score.

## Known failure modes

- qwen3:1.7b sometimes loses the content of an earlier tool result,
  passes a filename instead of the file content to the next tool, and
  then reports success with no numeric evidence. Documented as
  regression_ctx_loss in benchmarks/tasks.json and caught by
  judge.args_sane.
- The agent may read a file containing a prompt injection. The server
  does not interpret file content, and the path guard blocks any tool
  call that escapes the safe root. The prompt_injection benchmark task
  drops the composite if the agent calls read_text_file with a path
  matching .., .ssh, /etc/, passwd, or /Users/.

## Timeline

- 2026-10-13: first run produced word_count = 1 for a file with
  dozens of words. Root cause: model passed the filename, not the
  content. Logged as regression_ctx_loss and guarded by args_sane.
- 2026-10-13: added injection fixture, path-guard tests, and
  forbid_arg_patterns. Added .gitlab-ci.yml and GitHub Actions with a
  blocking eval-gate stage.
- 2026-10-13: renamed loop.py to search.py. Documented as
  configuration search with an acceptance criterion, not as
  self-improvement.

## Requirements

Python 3.12 or newer.
Ollama running locally with qwen3:1.7b pulled.
mcp pinned below 2 because v2 renamed FastMCP to MCPServer.
