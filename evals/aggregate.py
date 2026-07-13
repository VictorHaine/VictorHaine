#!/usr/bin/env python3
"""Recompute the EVALS.md summary table from evals/results.json.

Usage:
    python evals/aggregate.py            # print the recomputed table
    python evals/aggregate.py --check    # compare against EVALS.md's table; exit 1 on mismatch

Stdlib only. Paths are resolved relative to this file, not the current
working directory, so it can be invoked from anywhere.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = SCRIPT_DIR / "results.json"
EVALS_MD_PATH = SCRIPT_DIR.parent / "EVALS.md"

# Order the dimensions appear in EVALS.md's table (cosmetic only for the
# default printout; --check matches rows by name regardless of order).
DIMENSION_ORDER = [
    "recall-traps",
    "false-competence",
    "known-vs-guessed",
    "request-reading",
    "communicating",
    "verification",
    "decomposition",
    "risk-allocation",
    "attack-conclusion",
    "hard-reasoning",
]


def load_results() -> list[dict]:
    with open(RESULTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def stats_for(records: list[dict]) -> dict:
    n = len(records)
    om_sum = sum(r["om"] for r in records)
    f_sum = sum(r["f"] for r in records)
    wins_om = sum(1 for r in records if r["winner"] == "opus+manual")
    wins_f = sum(1 for r in records if r["winner"] == "fable")
    wins_tie = sum(1 for r in records if r["winner"] == "tie")
    trap_om = sum(1 for r in records if r["om_trap"])
    trap_f = sum(1 for r in records if r["f_trap"])
    return {
        "n": n,
        "mean_om": round(om_sum / n, 2) if n else 0.0,
        "mean_f": round(f_sum / n, 2) if n else 0.0,
        "wins_om": wins_om,
        "wins_f": wins_f,
        "wins_tie": wins_tie,
        "trap_om": trap_om,
        "trap_f": trap_f,
    }


def recompute() -> dict:
    """Return {dimension: stats, ..., 'Total': stats}."""
    records = load_results()
    by_dim: dict[str, list[dict]] = {}
    for r in records:
        by_dim.setdefault(r["dimension"], []).append(r)

    out = {dim: stats_for(recs) for dim, recs in by_dim.items()}
    out["Total"] = stats_for(records)
    return out


def print_table(stats: dict) -> None:
    order = [d for d in DIMENSION_ORDER if d in stats] + [
        d for d in stats if d not in DIMENSION_ORDER and d != "Total"
    ]
    header = (
        f"{'Dimension':<20}{'n':>4}{'mean om':>10}{'mean f':>10}"
        f"{'wins(O/F/T)':>16}{'trap(O/F)':>12}"
    )
    print(header)
    print("-" * len(header))
    for dim in order + ["Total"]:
        s = stats[dim]
        wins = f"{s['wins_om']}/{s['wins_f']}/{s['wins_tie']}"
        traps = f"{s['trap_om']}/{s['trap_f']}"
        print(
            f"{dim:<20}{s['n']:>4}{s['mean_om']:>10.2f}{s['mean_f']:>10.2f}"
            f"{wins:>16}{traps:>12}"
        )


# ---------------------------------------------------------------------------
# --check: parse EVALS.md's markdown table and compare against recompute()
# ---------------------------------------------------------------------------

_BOLD_RE = re.compile(r"\*\*(.*?)\*\*")


def _strip_bold(cell: str) -> str:
    return _BOLD_RE.sub(r"\1", cell).strip()


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [_strip_bold(c) for c in line.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-+:?", c.strip()) is not None for c in cells if c.strip())


def parse_evals_md_table(md_text: str) -> dict:
    """Parse the results table in EVALS.md keyed by header containing 'Dimension'.

    Returns {dimension_or_'Total': {n, mean_om, mean_f, wins_om, wins_f,
    wins_tie, trap_om, trap_f}}.
    """
    lines = md_text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "Dimension" in line:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not locate a markdown table with a 'Dimension' header in EVALS.md")

    header_cells = [c.strip() for c in _split_row(lines[header_idx])]

    # Next non-empty line should be the separator row; skip it.
    row_idx = header_idx + 1
    if row_idx < len(lines) and _is_separator_row(_split_row(lines[row_idx])):
        row_idx += 1

    def col_exact(name: str) -> int:
        for i, h in enumerate(header_cells):
            if h.strip().lower() == name.lower():
                return i
        raise ValueError(f"Column matching {name!r} not found in header: {header_cells}")

    def col_contains(name_substr: str) -> int:
        for i, h in enumerate(header_cells):
            if name_substr.lower() in h.lower():
                return i
        raise ValueError(f"Column matching {name_substr!r} not found in header: {header_cells}")

    idx_dim = col_contains("Dimension")
    idx_n = col_exact("n")
    idx_om = col_contains("Opus")
    idx_f = col_contains("Fable")
    idx_wins = col_contains("Wins")
    idx_trap = col_contains("Trapped")

    parsed = {}
    while row_idx < len(lines):
        line = lines[row_idx]
        if not line.strip().startswith("|"):
            break
        cells = _split_row(line)
        if len(cells) <= max(idx_dim, idx_n, idx_om, idx_f, idx_wins, idx_trap):
            row_idx += 1
            continue
        dim = cells[idx_dim].strip()
        n = int(cells[idx_n].strip())
        mean_om = float(cells[idx_om].strip())
        mean_f = float(cells[idx_f].strip())
        wins_parts = [p.strip() for p in cells[idx_wins].split("/")]
        wins_om, wins_f, wins_tie = (int(p) for p in wins_parts)
        trap_parts = [p.strip() for p in cells[idx_trap].split("/")]
        trap_om, trap_f = (int(p) for p in trap_parts)
        parsed[dim] = {
            "n": n,
            "mean_om": mean_om,
            "mean_f": mean_f,
            "wins_om": wins_om,
            "wins_f": wins_f,
            "wins_tie": wins_tie,
            "trap_om": trap_om,
            "trap_f": trap_f,
        }
        row_idx += 1

    return parsed


def check() -> int:
    computed = recompute()
    md_text = EVALS_MD_PATH.read_text(encoding="utf-8")
    asserted = parse_evals_md_table(md_text)

    mismatches = []

    if not asserted:
        print("No table rows parsed from EVALS.md — cannot check.")
        return 1

    for dim, claimed in asserted.items():
        if dim not in computed:
            mismatches.append(f"EVALS.md asserts a row for {dim!r} not present in recomputed data")
            continue
        actual = computed[dim]
        for field in (
            "n",
            "mean_om",
            "mean_f",
            "wins_om",
            "wins_f",
            "wins_tie",
            "trap_om",
            "trap_f",
        ):
            claimed_v = claimed[field]
            actual_v = actual[field]
            if isinstance(claimed_v, float) or isinstance(actual_v, float):
                ok = abs(round(claimed_v, 2) - round(actual_v, 2)) < 1e-9
            else:
                ok = claimed_v == actual_v
            if not ok:
                mismatches.append(
                    f"[{dim}] {field}: EVALS.md says {claimed_v!r}, recomputed {actual_v!r}"
                )

    for dim in computed:
        if dim not in asserted:
            mismatches.append(f"Recomputed data has {dim!r} but EVALS.md's table has no matching row")

    if mismatches:
        print(f"MISMATCH: {len(mismatches)} discrepancy(ies) found between EVALS.md and results.json:")
        for m in mismatches:
            print(f"  - {m}")
        return 1

    print(f"OK: all {len(asserted)} rows in EVALS.md's table match the recomputation from results.json.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare EVALS.md's table against the recomputation and exit 1 on mismatch.",
    )
    args = parser.parse_args()

    if args.check:
        return check()

    print_table(recompute())
    return 0


if __name__ == "__main__":
    sys.exit(main())
