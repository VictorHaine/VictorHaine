# VictorHaine

This repo contains:

- [`OPERATING_MANUAL.md`](OPERATING_MANUAL.md) — a craft handoff written from Claude Fable 5 to Claude Opus 4.8: how to work carefully on real tasks.
- [`EVALS.md`](EVALS.md) — a 120-eval blind validation testing whether Opus 4.8 following the manual matches or beats Fable 5 working bare.
- [`evals/`](evals/) — the raw dataset behind that report (`evals.json`, `results.json`), the exact replication protocol ([`PROTOCOL.md`](evals/PROTOCOL.md)), and the tooling that verifies EVALS.md's numbers against it (`aggregate.py`, `test_evals.py`).

## Reproducing the numbers

EVALS.md's results table is recomputed directly from `evals/results.json`, not hand-copied. To check it yourself:

```
python evals/aggregate.py            # print the recomputed per-dimension table
python evals/aggregate.py --check    # compare it against EVALS.md's table; exits 1 on any mismatch
pytest evals/                        # dataset integrity + headline + full table checks
```

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs both on every push and pull request.
