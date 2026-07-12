"""Tests for the eval dataset (evals.json / results.json) and the aggregate.py
recomputation of EVALS.md's summary table.

Run with: pytest evals/
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
EVALS_JSON_PATH = SCRIPT_DIR / "evals.json"
RESULTS_JSON_PATH = SCRIPT_DIR / "results.json"
EVALS_MD_PATH = SCRIPT_DIR.parent / "EVALS.md"
AGGREGATE_PATH = SCRIPT_DIR / "aggregate.py"

sys.path.insert(0, str(SCRIPT_DIR))
import aggregate  # noqa: E402


EXPECTED_TOTAL = 120
EXPECTED_DIMENSIONS = 10
EXPECTED_PER_DIMENSION = 12

VALID_WINNERS = {"opus+manual", "fable", "tie"}


@pytest.fixture(scope="module")
def evals_data() -> list[dict]:
    with open(EVALS_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def results_data() -> list[dict]:
    with open(RESULTS_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Dataset integrity
# ---------------------------------------------------------------------------


def test_evals_json_has_120_items(evals_data):
    assert len(evals_data) == EXPECTED_TOTAL


def test_results_json_has_120_items(results_data):
    assert len(results_data) == EXPECTED_TOTAL


def test_evals_json_has_10_dimensions_of_12(evals_data):
    counts: dict[str, int] = {}
    for item in evals_data:
        counts[item["dimension"]] = counts.get(item["dimension"], 0) + 1
    assert len(counts) == EXPECTED_DIMENSIONS
    for dim, n in counts.items():
        assert n == EXPECTED_PER_DIMENSION, f"{dim} has {n} items, expected {EXPECTED_PER_DIMENSION}"


def test_results_json_has_10_dimensions_of_12(results_data):
    counts: dict[str, int] = {}
    for item in results_data:
        counts[item["dimension"]] = counts.get(item["dimension"], 0) + 1
    assert len(counts) == EXPECTED_DIMENSIONS
    for dim, n in counts.items():
        assert n == EXPECTED_PER_DIMENSION, f"{dim} has {n} items, expected {EXPECTED_PER_DIMENSION}"


def test_evals_and_results_keys_match(evals_data, results_data):
    evals_keys = {(item["dimension"], item["idx"]) for item in evals_data}
    results_keys = {(item["dimension"], item["idx"]) for item in results_data}
    assert evals_keys == results_keys
    # And no duplicate keys within either file.
    assert len(evals_keys) == len(evals_data)
    assert len(results_keys) == len(results_data)


def test_every_eval_has_required_fields(evals_data):
    for item in evals_data:
        key = f"{item['dimension']}#{item['idx']}"
        assert item.get("prompt") and item["prompt"].strip(), f"{key}: empty prompt"
        assert item.get("hidden_trap") and item["hidden_trap"].strip(), f"{key}: empty hidden_trap"
        assert isinstance(item.get("pass_criteria"), list) and len(item["pass_criteria"]) >= 1, (
            f"{key}: needs at least one pass_criteria"
        )
        assert isinstance(item.get("fail_tells"), list) and len(item["fail_tells"]) >= 1, (
            f"{key}: needs at least one fail_tell"
        )


def test_every_result_has_valid_fields(results_data):
    for item in results_data:
        key = f"{item['dimension']}#{item['idx']}"
        assert isinstance(item.get("om"), (int, float)), f"{key}: om missing/not numeric"
        assert 0 <= item["om"] <= 10, f"{key}: om {item['om']} out of [0,10]"
        assert isinstance(item.get("f"), (int, float)), f"{key}: f missing/not numeric"
        assert 0 <= item["f"] <= 10, f"{key}: f {item['f']} out of [0,10]"
        assert isinstance(item.get("om_trap"), bool), f"{key}: om_trap not a bool"
        assert isinstance(item.get("f_trap"), bool), f"{key}: f_trap not a bool"
        assert item.get("winner") in VALID_WINNERS, f"{key}: winner {item.get('winner')!r} invalid"


# ---------------------------------------------------------------------------
# Headline invariants
# ---------------------------------------------------------------------------


def test_total_wins_sum_to_120(results_data):
    wins_om = sum(1 for r in results_data if r["winner"] == "opus+manual")
    wins_f = sum(1 for r in results_data if r["winner"] == "fable")
    wins_tie = sum(1 for r in results_data if r["winner"] == "tie")
    assert wins_om + wins_f + wins_tie == EXPECTED_TOTAL


def test_headline_means_match_evals_md(results_data):
    """EVALS.md's headline text claims 9.41 / 8.97 overall averages."""
    mean_om = round(sum(r["om"] for r in results_data) / len(results_data), 2)
    mean_f = round(sum(r["f"] for r in results_data) / len(results_data), 2)

    md_text = EVALS_MD_PATH.read_text(encoding="utf-8")
    assert f"**{mean_om:.2f}/10**" in md_text, (
        f"Recomputed Opus+manual mean {mean_om:.2f} not found in EVALS.md headline"
    )
    assert f"**{mean_f:.2f}/10**" in md_text, (
        f"Recomputed Fable mean {mean_f:.2f} not found in EVALS.md headline"
    )


# ---------------------------------------------------------------------------
# Full table check (mirrors `python evals/aggregate.py --check`)
# ---------------------------------------------------------------------------


def test_aggregate_check_matches_in_process():
    computed = aggregate.recompute()
    md_text = EVALS_MD_PATH.read_text(encoding="utf-8")
    asserted = aggregate.parse_evals_md_table(md_text)

    assert asserted, "No rows parsed from EVALS.md's results table"

    mismatches = []
    for dim, claimed in asserted.items():
        assert dim in computed, f"EVALS.md has a row for {dim!r} not in recomputed data"
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
                mismatches.append(f"[{dim}] {field}: EVALS.md={claimed_v!r} recomputed={actual_v!r}")

    assert not mismatches, "Mismatches between EVALS.md and results.json:\n" + "\n".join(mismatches)

    for dim in computed:
        assert dim in asserted, f"Recomputed dimension {dim!r} missing from EVALS.md's table"


def test_aggregate_check_subprocess_exits_clean():
    result = subprocess.run(
        [sys.executable, str(AGGREGATE_PATH), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"aggregate.py --check failed (exit {result.returncode}):\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "MISMATCH" not in result.stdout
