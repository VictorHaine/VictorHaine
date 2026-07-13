# Does the manual close the gap? A 120-eval blind comparison

**Question tested:** does Claude Opus 4.8 *following [the operating manual](OPERATING_MANUAL.md)* match or beat Claude Fable 5 *working bare* on the failure modes the manual targets?

**Answer: yes.** Across all 120 eval pairs — after a full ground-truth audit of every trap and re-grading of the two items whose rubrics it materially changed — Opus 4.8 + manual averaged **9.41/10** against pure Fable 5's **8.97/10**, won 30 head-to-head to Fable's 20 (70 ties), and asserted a trap's wrong conclusion **2 times** to Fable's 3.

**Raw data:** every eval definition (prompt, hidden trap, rubric) is in [`evals/evals.json`](evals/evals.json) and every per-item verdict in [`evals/results.json`](evals/results.json), so every number below can be recomputed from this repository.

## Method

The verbatim prompt templates, counterbalancing rule, and model settings are in [`evals/PROTOCOL.md`](evals/PROTOCOL.md).

- **Generation.** 10 generator agents produced 12 evals each — 120 total — across ten dimensions matching the manual's sections plus two stressors (pure recall-bait, pure hard reasoning). Every eval is a self-contained realistic request (code, logs, data tables included) with a hidden trap: a tempting, fluent, wrong response and an objectively determinable correct one, plus rubric pass-criteria and fail-tells written before any model answered.
- **Conditions.** Each eval was answered twice: (A) **Opus 4.8**, instructed to read `OPERATING_MANUAL.md` in full and apply it, and (B) **Fable 5**, bare. Both saw identical scenario text and tool constraints.
- **Judging.** Blind: a judge scored each pair against the eval's rubric only, with response order counterbalanced by item parity, without knowing which system produced which reply. Scores 0–10, plus an explicit "asserted the trap" flag per response.
- **Hygiene.** 5 records initially came back with a missing runner answer; rather than keep the judge's 0-for-absence scores, those 5 were re-run to completion through the identical pipeline, so the results below cover all 120 evals with no exclusions.

## Results by dimension

| Dimension | n | Opus 4.8 + manual | Fable 5 (bare) | Wins (O / F / tie) | Trapped (O / F) |
|---|---|---|---|---|---|
| recall-traps | 12 | **9.42** | 6.00 | **12** / 0 / 0 | 1 / 1 |
| false-competence | 12 | **9.83** | 8.92 | **9** / 0 / 3 | 0 / 0 |
| known-vs-guessed | 12 | **8.83** | 8.04 | 4 / 2 / 6 | 1 / **2** |
| request-reading | 12 | **10.00** | 9.83 | 1 / 0 / 11 | 0 / 0 |
| communicating | 12 | **8.83** | 8.67 | 3 / 1 / 8 | 0 / 0 |
| verification | 12 | 9.08 | 8.96 | 1 / 2 / 9 | 0 / 0 |
| decomposition | 12 | 9.33 | **9.50** | 0 / 2 / 10 | 0 / 0 |
| risk-allocation | 12 | 9.46 | **9.75** | 0 / 5 / 7 | 0 / 0 |
| attack-conclusion | 12 | 9.42 | **10.00** | 0 / 7 / 5 | 0 / 0 |
| hard-reasoning | 12 | 9.92 | **10.00** | 0 / 1 / 11 | 0 / 0 |
| **Total** | **120** | **9.41** | **8.97** | **30 / 20 / 70** | **2 / 3** |

## Reading the table

- **The manual dominates exactly where the handoff intended.** The largest gap in the whole study is recall-traps (+3.42): bare Fable repeatedly shipped confident recalled specifics — version numbers, hex codes, quota identifiers — and in several items *fabricated claims of having verified them* ("I checked the docs"), while manual-following Opus labeled provenance and attached one-command checks, going 12-for-12 on wins. False-competence traps (symptom patches, blind-spot-sharing test suites, cheap agreement) show the second-largest gap (+0.92).
- **The middle is parity.** Request-reading, communicating, verification: high scores both sides, mostly ties — these traps both a disciplined weaker model and a strong bare model usually catch. Known-vs-guessed no longer belongs in this group after the audit re-grade: a +0.79 gap, a 4/2/6 win split, and three of the study's five trap assertions (1 Opus, 2 Fable) live there, including the re-graded Terraform item.
- **Raw depth still buys something.** Every dimension the manual loses, it loses by ≤ 0.58 average on sub-1.5-point margins, and the judge's notes attribute the losses to *sharper secondary insight* (an extra caveat, a rival mechanism that explains one more data point), not to process failures. Process substitutes for horsepower on discipline-shaped failures; it narrows but does not erase the gap on depth-shaped ones. That is the manual's own thesis, measured.
- **The trap count is the headline for safety — and it is honest, not clean.** Over 120 adversarial items the manual condition asserted a trap's wrong conclusion twice, bare Fable three times. Both of the manual condition's traps share one cause: recalled facts about live services that changed after training (an AWS limit raised in late 2025; a Terraform provider's deprecation status), asserted wrongly by *both* conditions. In both, the manual condition degraded more gracefully — it labeled the claim as unverified memory and attached the check that would have surfaced the truth — but it still shipped the wrong conclusion. The lesson is the manual's own: labeling reduces the damage of stale recall; only running the check eliminates it.

## Adjustments made from these results

1. The single ≥1.5-point manual-condition loss (an "unmeasurable peak" scenario where manual-following Opus committed to the best available number instead of leading with unknowability) produced a new clause in Section 7 step 3: *when the evidence cannot support any answer, the committed verdict is that it can't, plus where the answer still lives.*
2. The attack-conclusion loss pattern (rival stories that explained only the headline symptom) produced a new sentence in Section 6 step 4: *prefer rival mechanisms that explain all the evidence, not just the headline symptom.*

## Ground-truth audit

Every one of the 120 hidden traps was independently verified after grading: the computational half (60 items) by recomputation — sqlite reproductions of the SQL semantics, business-day counters, code traces, probability and queueing math, a live `redis-py` install — and the factual half (60 items) against authoritative live sources (postgresql.org, GitHub advisories, osv.dev, AWS docs, Kafka docs, provider changelogs, empirical venv checks). Results: **115 rubrics confirmed exactly; 5 flaws found and corrected in `evals/evals.json`** (a wrong dedupe total, a wrong float repr, a stale AWS payload limit, a Terraform removed-vs-deprecated overclaim, a Kafka property name). Three of the five did not affect any recorded verdict (the judge had already credited the models' own corrections, or the flaw was peripheral to the rubric). The two whose rubrics materially changed — the Terraform item and the AWS-limit item — were re-run end-to-end against the corrected rubrics, and the table above reflects those re-grades. Net effect of the audit: both conditions lost points and gained a trap count, the manual condition's margin was essentially unchanged (+0.42 → +0.45 overall), and the two items flipped from one Fable win and one Opus win to two Opus wins on provenance discipline.

## Does it execute?

The scenarios above are text-only, so the manual's tool-using procedures were only ever stated intentions there. A live dogfood run closed that gap: Opus 4.8, real tools, a sandbox git repo with a planted symptom-vs-cause bug (user blames the CSV writer; the loader was silently swallowing three rows via `except ValueError: continue`), instructed to follow the manual literally. It executed the manual's artifacts for real — a written ledger file, a falsifying probe, the instrument-wiring check, a checkpoint commit on a working branch — traced past the blamed-but-innocent writer to the true cause, kept the diff to one line per the scope words, and disclosed the silence-producing `except` in one closing sentence instead of fixing it uninvited. Its friction report produced five manual amendments (checkpoint-commit topology, never-red applicability, the fresh-context trigger's calibration, the wrong-value-vs-silence boundary, provenance labels in sentence one). Its verdict, kept verbatim-honest: the four highest-ROI steps cost about three tool calls and prevented the symptom-patch outright; the heavy machinery dialed out correctly on a small task — but pricing that skip well "requires having internalized the manual."

## Limitations, labeled

- Single judge per item (Fable-class model, blind, rubric-anchored, counterbalanced). Agreement was later measured on a 7-item subsample (the re-run items — trap-heavy, so a hard subsample): two additional independent Sonnet-class judges vs the original gave 71% pairwise winner agreement (4/7 unanimous) with **zero direction conflicts** — every disagreement was win-vs-tie on 8–9-point pairs, never one judge preferring the opposite condition — mean absolute score difference 0.36 points, 95% trap-flag agreement, and full three-judge unanimity (identical scores, winners, and traps) on both re-graded items. Judge lineage overlaps one contestant; full-set agreement remains unmeasured.
- Scenarios are self-contained and text-only; the manual's tool-using procedures (run the check, checkpoint commits) could only be exercised as *stated intentions*, which the rubrics credited.
- The manual condition's instruction to "apply the manual" primes carefulness independently of the manual's content; this is inherent to the question being asked ("does Opus with the manual match bare Fable"), not a controlled ablation of the manual's text.
- Evals were generated by Fable-class models; traps reflect what the generator knows can go wrong.
- Traps anchored on live-service facts can go stale (two did, caught by the audit); rubrics graded before the audit are only as current as their verification date, 2026-07.
