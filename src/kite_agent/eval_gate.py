"""Blocking quality gate for CI.

Offline mode validates the benchmark structure without LLM calls.
Full mode runs the baseline eval against Ollama and enforces a minimum
composite score.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from kite_agent.agent_core import AgentConfig, run_agent
from kite_agent.judge import aggregate, score_task
from kite_agent.search import PROMPTS, TASKS_PATH


def validate_tasks(tasks: list[dict]) -> None:
    seen: set[str] = set()
    for t in tasks:
        for key in ("id", "query", "expect_tools"):
            if key not in t:
                sys.exit(f"task missing {key}: {t}")
        if t["id"] in seen:
            sys.exit(f"duplicate task id: {t['id']}")
        seen.add(t["id"])
        if not isinstance(t["expect_tools"], list):
            sys.exit(f"expect_tools must be a list: {t['id']}")


async def evaluate_baseline(tasks: list[dict]) -> float:
    config = AgentConfig(system_prompt=PROMPTS[0])
    scores = []
    for task in tasks:
        run = await run_agent(task["query"], config)
        scores.append(score_task(task, run))
    return aggregate(scores)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-composite", type=float, default=0.70)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    tasks = json.loads(TASKS_PATH.read_text())
    validate_tasks(tasks)
    print(f"[gate] validated {len(tasks)} benchmark tasks")

    if args.offline:
        print("[gate] offline mode: structural validation only")
        return

    score = asyncio.run(evaluate_baseline(tasks))
    print(f"[gate] baseline composite: {score:.4f}")
    if score < args.min_composite:
        sys.exit(f"FAIL: composite {score:.4f} < threshold {args.min_composite}")
    print("[gate] PASS")


if __name__ == "__main__":
    main()
