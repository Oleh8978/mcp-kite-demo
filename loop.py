"""Self-improving loop: baseline, mutate, evaluate, accept or reject."""

from __future__ import annotations

import asyncio
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

from agent_core import AgentConfig, run_agent
from judge import aggregate, score_task

HERE = Path(__file__).parent
TASKS = json.loads((HERE / "tasks.json").read_text())
HISTORY = HERE / "history.jsonl"

PROMPTS = [
    "You are a concise assistant. Use tools when helpful.",
    "You are a careful agent. Always call at least one tool before answering.",
    "You are an agentic planner. Think step by step about which tool to call next.",
    "You are a precise assistant. Prefer tools over guessing.",
    "You are a minimal agent. Call only the tools that are strictly needed. When a tool returns data, pass that data to the next tool, never its name.",
]

TEMPS = [0.0, 0.1, 0.2, 0.4]
STEPS = [4, 6, 8]
MODELS = ["qwen3:1.7b"]


async def evaluate(config: AgentConfig, verbose: bool) -> float:
    scores = []
    for task in TASKS:
        run = await run_agent(task["query"], config)
        s = score_task(task, run)
        scores.append(s)
        if verbose:
            flags = f"args_ok={s.args_ok} answer_ok={s.answer_ok}"
            print(f"    {task['id']:<18} score={s.composite:.2f}  {flags}")
    return aggregate(scores)


def mutate(config: AgentConfig, rng: random.Random) -> AgentConfig:
    return AgentConfig(
        system_prompt=rng.choice(PROMPTS),
        temperature=rng.choice(TEMPS),
        max_steps=rng.choice(STEPS),
        model=rng.choice(MODELS),
    )


def log_generation(gen: int, config: AgentConfig, score: float, accepted: bool) -> None:
    record = {
        "generation": gen,
        "fingerprint": config.fingerprint(),
        "score": score,
        "accepted": accepted,
        "config": asdict(config),
    }
    with HISTORY.open("a") as f:
        f.write(json.dumps(record) + "\n")


async def main(generations: int, seed: int) -> None:
    rng = random.Random(seed)
    best = AgentConfig(system_prompt=PROMPTS[0])

    print("=== baseline ===")
    best_score = await evaluate(best, verbose=True)
    print(f"baseline score: {best_score:.4f}\n")
    log_generation(0, best, best_score, accepted=True)

    for gen in range(1, generations + 1):
        candidate = mutate(best, rng)
        print(f"=== generation {gen} ===")
        print(f"  model={candidate.model}  temp={candidate.temperature}  steps={candidate.max_steps}")
        print(f"  prompt: {candidate.system_prompt[:70]}")
        score = await evaluate(candidate, verbose=True)
        accepted = score > best_score
        marker = "ACCEPT" if accepted else "reject"
        print(f"  score: {score:.4f}  ({marker})\n")
        log_generation(gen, candidate, score, accepted)
        if accepted:
            best = candidate
            best_score = score

    print(f"=== best score: {best_score:.4f} ===")
    print(f"best model:  {best.model}")
    print(f"best prompt: {best.system_prompt}")
    print(f"best temp:   {best.temperature}  max_steps: {best.max_steps}")
    print(f"history log: {HISTORY}")


if __name__ == "__main__":
    gens = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    asyncio.run(main(gens, seed))
