# ADR 0001 — Deterministic scorer instead of an LLM judge

## Status

Accepted, 2026-10-13.

## Context

The eval harness scores agent runs against a fixed benchmark. Two
options were considered:

- A deterministic scorer built from explicit rules over the agent's
  tool calls and final answer.
- An LLM-as-judge that grades the final answer for semantic quality.

## Decision

Use a deterministic scorer (src/kite_agent/judge.py). Each task is
scored on five axes: tool recall, tool precision, call order as a
subsequence, argument sanity including task-specific forbidden
patterns, and answer correctness via keyword matching. Composite is a
weighted sum.

## Rejected alternative — LLM-as-judge

An LLM judge would catch semantic paraphrases that keyword matching
misses. It was rejected for four reasons:

1. Non-determinism. The same agent run would score differently across
   days, model versions, and prompt variations. Reproducibility would
   be lost, and the search would then optimize against a moving
   target.
2. Cost and latency. Every eval iteration would double the number of
   model calls. With eight tasks and four generations, this multiplies
   wall-clock time and token spend by roughly two.
3. Circular dependency. Using an LLM to score an LLM introduces the
   exact failure modes the eval is meant to detect: hallucination,
   context loss, silent degradation. The judge would need its own
   judge.
4. Debuggability. When a score changes, the difference must be
   explainable. A deterministic scorer produces a diff. An LLM judge
   produces an opinion that itself needs verification.

## Consequences

- Positive: fast, reproducible, no network calls at scoring time.
- Negative: keyword matching misses semantic paraphrase. A response
  that is correct but phrased differently may fail. Accepted for now.
- Negative: adding a task requires writing expected keywords by hand.
  Mitigated by keeping the suite small and explicit.

## Revisit when

- The task suite grows beyond what keyword matching can express
  without becoming brittle.
- A deterministic semantic-equivalence scorer becomes available, for
  example embeddings with a fixed threshold and a frozen model. Even
  then it should be an additional axis, not a replacement.
