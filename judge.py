"""Deterministic scorer for agent runs against benchmark tasks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from agent_core import AgentRun


@dataclass
class TaskScore:
    task_id: str
    tool_recall: float
    tool_precision: float
    order_ok: bool
    args_ok: bool
    answer_ok: bool
    composite: float
    detail: str = ""


def _is_subsequence(expected: list[str], actual: list[str]) -> bool:
    it = iter(actual)
    return all(any(a == e for a in it) for e in expected)


def _args_sane(run: AgentRun) -> bool:
    """Catch the known failure: word_count receives the filename, not file content."""
    for call in run.tool_calls:
        if call["name"] == "word_count":
            text = str(call["args"].get("text", ""))
            if len(text) < 40 and not any(c.isspace() for c in text):
                return False
        if call["name"] == "list_files":
            path = str(call["args"].get("relative_path", ""))
            if path.endswith((".py", ".md", ".txt", ".json")):
                return False
    return True


def _answer_ok(task: dict, answer: str) -> bool:
    low = answer.lower()
    required = [n.lower() for n in task.get("expect_answer_contains", [])]
    any_of = [n.lower() for n in task.get("expect_answer_contains_any", [])]

    if required and not all(n in low for n in required):
        return False
    if any_of and not any(n in low for n in any_of):
        return False
    if not required and not any_of:
        if not answer.strip():
            return False
        if "successfully" in low and not re.search(r"\d", low):
            return False
    return True


def score_task(task: dict, run: AgentRun) -> TaskScore:
    expected = task.get("expect_tools", [])
    called = [c["name"] for c in run.tool_calls]
    unique_called = set(called)

    if expected:
        recall = sum(1 for e in expected if e in unique_called) / len(expected)
        precision = (
            sum(1 for c in unique_called if c in expected) / len(unique_called)
            if unique_called
            else 0.0
        )
    else:
        recall = precision = 1.0

    order_ok = _is_subsequence(expected, called) if expected else True
    args_ok = _args_sane(run)
    answer_ok = _answer_ok(task, run.final_answer)

    composite = (
        0.35 * recall
        + 0.15 * precision
        + 0.15 * (1.0 if order_ok else 0.0)
        + 0.15 * (1.0 if args_ok else 0.0)
        + 0.20 * (1.0 if answer_ok else 0.0)
    )
    return TaskScore(
        task_id=task["id"],
        tool_recall=round(recall, 3),
        tool_precision=round(precision, 3),
        order_ok=order_ok,
        args_ok=args_ok,
        answer_ok=answer_ok,
        composite=round(composite, 4),
        detail=f"called={called} expected={expected}",
    )


def aggregate(scores: list[TaskScore]) -> float:
    if not scores:
        return 0.0
    return round(sum(s.composite for s in scores) / len(scores), 4)
