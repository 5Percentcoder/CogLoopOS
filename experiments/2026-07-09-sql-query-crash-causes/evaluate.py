#!/usr/bin/env python3
"""Measure client memory for full versus batched SQL result consumption."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path


DEFAULT_ROWS = 75_000
DEFAULT_PAYLOAD_SIZE = 256
BATCH_SIZE = 500


def run_mode(mode: str, rows: int, payload_size: int) -> dict:
    connection = sqlite3.connect(":memory:")
    query = """
        WITH RECURSIVE sequence(value) AS (
            SELECT 1
            UNION ALL
            SELECT value + 1 FROM sequence WHERE value < ?
        )
        SELECT value, printf('%0*d', ?, value)
        FROM sequence
    """

    tracemalloc.start()
    started = time.perf_counter()
    cursor = connection.execute(query, (rows, payload_size))

    consumed = 0
    if mode == "fetchall":
        consumed = len(cursor.fetchall())
    elif mode == "fetchmany":
        while batch := cursor.fetchmany(BATCH_SIZE):
            consumed += len(batch)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    duration_seconds = time.perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    connection.close()

    return {
        "mode": mode,
        "rows_consumed": consumed,
        "peak_bytes": peak_bytes,
        "duration_seconds": round(duration_seconds, 4),
    }


def run_child(mode: str, rows: int, payload_size: int) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child-mode",
        mode,
        "--rows",
        str(rows),
        "--payload-size",
        str(payload_size),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def run_experiment(rows: int, payload_size: int) -> dict:
    fetchall = run_child("fetchall", rows, payload_size)
    fetchmany = run_child("fetchmany", rows, payload_size)
    peak_ratio = round(fetchall["peak_bytes"] / fetchmany["peak_bytes"], 2)
    same_row_count = (
        fetchall["rows_consumed"] == rows
        and fetchmany["rows_consumed"] == rows
    )

    result = {
        "experiment": "2026-07-09-sql-query-crash-causes",
        "environment": {
            "database": f"SQLite {sqlite3.sqlite_version}",
            "python": sys.version.split()[0],
            "rows": rows,
            "payload_size": payload_size,
            "fetchmany_batch_size": BATCH_SIZE,
        },
        "contract": {
            "minimum_peak_memory_ratio": 10.0,
            "required_rows_per_mode": rows,
        },
        "fetchall": fetchall,
        "fetchmany": fetchmany,
        "observed": {
            "fetchall_to_fetchmany_peak_ratio": peak_ratio,
            "same_row_count": same_row_count,
        },
        "passed": peak_ratio >= 10.0 and same_row_count,
        "limitations": [
            "tracemalloc measures Python allocations, not all native driver memory.",
            "SQLite behavior does not represent every database server or driver.",
            "The experiment demonstrates memory amplification without inducing an OOM crash.",
        ],
    }

    output_path = Path(__file__).with_name("result.json")
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child-mode", choices=("fetchall", "fetchmany"))
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--payload-size", type=int, default=DEFAULT_PAYLOAD_SIZE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.child_mode:
        print(json.dumps(run_mode(args.child_mode, args.rows, args.payload_size)))
        return

    result = run_experiment(args.rows, args.payload_size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nWrote {Path(__file__).with_name('result.json')}")


if __name__ == "__main__":
    main()
