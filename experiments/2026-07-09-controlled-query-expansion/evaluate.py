#!/usr/bin/env python3
"""Compare token-overlap retrieval with controlled acronym expansion."""

from __future__ import annotations

import json
import re
from pathlib import Path


DOCUMENTS = [
    {
        "id": "ops-rag",
        "text": "Red Amber Green RAG status pipeline for operational project reporting.",
    },
    {
        "id": "rag",
        "text": (
            "Retrieval Augmented Generation connects a language model to external "
            "knowledge before it produces an answer."
        ),
    },
    {
        "id": "cert-mcp",
        "text": "Microsoft Certified Professional MCP exam preparation and certification.",
    },
    {
        "id": "mcp",
        "text": (
            "Model Context Protocol connects AI applications to tools and contextual "
            "data through a standard interface."
        ),
    },
    {
        "id": "hybrid-search",
        "text": "Hybrid search combines dense and sparse retrieval signals.",
    },
    {
        "id": "reranker",
        "text": "A cross encoder reranker scores query document pairs after retrieval.",
    },
    {
        "id": "graphrag",
        "text": "GraphRAG supports entity relationships and multi hop retrieval.",
    },
    {
        "id": "chunking",
        "text": "Chunking with overlap preserves context across retrieval segments.",
    },
]

CASES = [
    {"query": "RAG pipeline", "relevant": "rag", "uses_expansion": True},
    {"query": "MCP interface", "relevant": "mcp", "uses_expansion": True},
    {
        "query": "hybrid search dense sparse",
        "relevant": "hybrid-search",
        "uses_expansion": False,
    },
    {
        "query": "cross encoder reranker",
        "relevant": "reranker",
        "uses_expansion": False,
    },
    {
        "query": "GraphRAG multi hop",
        "relevant": "graphrag",
        "uses_expansion": False,
    },
    {
        "query": "chunking overlap retrieval",
        "relevant": "chunking",
        "uses_expansion": False,
    },
]

EXPANSIONS = {
    "rag": ["retrieval", "augmented", "generation"],
    "mcp": ["model", "context", "protocol"],
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def query_tokens(query: str, expand: bool) -> list[str]:
    tokens = tokenize(query)
    if not expand:
        return tokens

    expanded = list(tokens)
    for token in tokens:
        expanded.extend(EXPANSIONS.get(token, []))
    return expanded


def retrieve(query: str, expand: bool) -> tuple[str, int]:
    query_terms = set(query_tokens(query, expand))
    ranked: list[tuple[int, int, str]] = []

    for position, document in enumerate(DOCUMENTS):
        document_terms = set(tokenize(document["text"]))
        score = len(query_terms & document_terms)
        ranked.append((score, -position, document["id"]))

    score, _, document_id = max(ranked)
    return document_id, score


def evaluate(expand: bool) -> dict:
    rows = []
    for case in CASES:
        predicted, score = retrieve(case["query"], expand)
        rows.append(
            {
                **case,
                "predicted": predicted,
                "score": score,
                "correct": predicted == case["relevant"],
            }
        )

    recall_at_1 = sum(row["correct"] for row in rows) / len(rows)
    stable_rows = [row for row in rows if not row["uses_expansion"]]
    stable_recall_at_1 = (
        sum(row["correct"] for row in stable_rows) / len(stable_rows)
    )
    return {
        "recall_at_1": round(recall_at_1, 4),
        "non_expansion_recall_at_1": round(stable_recall_at_1, 4),
        "cases": rows,
    }


def main() -> None:
    baseline = evaluate(expand=False)
    controlled_expansion = evaluate(expand=True)
    improvement = round(
        controlled_expansion["recall_at_1"] - baseline["recall_at_1"], 4
    )
    guardrail_delta = round(
        controlled_expansion["non_expansion_recall_at_1"]
        - baseline["non_expansion_recall_at_1"],
        4,
    )
    result = {
        "experiment": "2026-07-09-controlled-query-expansion",
        "contract": {
            "minimum_recall_at_1_improvement": 0.25,
            "minimum_non_expansion_guardrail_delta": 0.0,
        },
        "baseline": baseline,
        "controlled_expansion": controlled_expansion,
        "observed": {
            "recall_at_1_improvement": improvement,
            "non_expansion_guardrail_delta": guardrail_delta,
        },
        "passed": improvement >= 0.25 and guardrail_delta >= 0.0,
        "limitations": [
            "Toy data validates the mechanism and workflow, not production impact.",
            "The experiment does not measure precision, latency, or answer quality.",
        ],
    }

    output_path = Path(__file__).with_name("result.json")
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
