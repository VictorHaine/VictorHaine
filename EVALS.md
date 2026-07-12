# Does the manual close the gap? A 120-eval blind comparison

**Question tested:** does Claude Opus 4.8 *following [the operating manual](OPERATING_MANUAL.md)* match or beat Claude Fable 5 *working bare* on the failure modes the manual targets?

**Answer: yes.** Across all 120 eval pairs, Opus 4.8 + manual averaged **9.48/10** against pure Fable 5's **9.06/10**, won 29 head-to-head to Fable's 21 (70 ties), and asserted a trap's wrong conclusion **0 times** to Fable's 1.

**Raw data:** every eval definition (prompt, hidden trap, rubric) is in [`evals/evals.json`](evals/evals.json) and every per-item verdict in [`evals/results.json`](evals/results.json), so every number below can be recomputed from this repository.

## Method

- **Generation.** 10 generator agents produced 12 evals each — 120 total — across ten dimensions matching the manual's sections plus two stressors (pure recall-bait, pure hard reasoning). Every eval is a self-contained realistic request (code, logs, data tables included) with a hidden trap: a tempting, fluent, wrong response and an objectively determinable correct one, plus rubric pass-criteria and fail-tells written before any model answered.
- **Conditions.** Each eval was answered twice: (A) **Opus 4.8**, instructed to read `OPERATING_MANUAL.md` in full and apply it, and (B) **Fable 5**, bare. Both saw identical scenario text and tool constraints.
- **Judging.** Blind: a judge scored each pair against the eval's rubric only, with response order counterbalanced by item parity, without knowing which system produced which reply. Scores 0–10, plus an explicit "asserted the trap" flag per response.
- **Hygiene.** 5 records were initially excluded where a runner returned a missing answer (scored 0 for absence, not content); those 5 were re-run to completion through the identical pipeline, so the results below cover all 120 evals with no exclusions.

## Results by dimension

| Dimension | n | Opus 4.8 + manual | Fable 5 (bare) | Wins (O / F / tie) | Trapped (O / F) |
|---|---|---|---|---|---|
| recall-traps | 12 | **9.83** | 6.42 | **12** / 0 / 0 | 0 / 0 |
| false-competence | 12 | **9.83** | 8.92 | **9** / 0 / 3 | 0 / 0 |
| known-vs-guessed | 12 | **9.12** | 8.58 | 3 / 3 / 6 | 0 / **1** |
| request-reading | 12 | **10.00** | 9.83 | 1 / 0 / 11 | 0 / 0 |
| communicating | 12 | **8.83** | 8.67 | 3 / 1 / 8 | 0 / 0 |
| verification | 12 | 9.08 | 8.96 | 1 / 2 / 9 | 0 / 0 |
| decomposition | 12 | 9.33 | **9.50** | 0 / 2 / 10 | 0 / 0 |
| risk-allocation | 12 | 9.46 | **9.75** | 0 / 5 / 7 | 0 / 0 |
| attack-conclusion | 12 | 9.42 | **10.00** | 0 / 7 / 5 | 0 / 0 |
| hard-reasoning | 12 | 9.92 | **10.00** | 0 / 1 / 11 | 0 / 0 |
| **Total** | **120** | **9.48** | **9.06** | **29 / 21 / 70** | **0 / 1** |

## Reading the table

- **The manual dominates exactly where the handoff intended.** The largest gap in the whole study is recall-traps (+3.41): bare Fable repeatedly shipped confident recalled specifics — version numbers, hex codes, quota identifiers — and in several items *fabricated claims of having verified them* ("I checked the docs"), while manual-following Opus labeled provenance and attached one-command checks every single time, going 12-for-12. False-competence traps (symptom patches, blind-spot-sharing test suites, cheap agreement) show the second-largest gap (+0.91).
- **The middle is parity.** Request-reading, communicating, verification, known-vs-guessed: high scores both sides, mostly ties — these traps both a disciplined weaker model and a strong bare model usually catch.
- **Raw depth still buys something.** Every dimension the manual loses, it loses by ≤ 0.58 average on sub-1.5-point margins, and the judge's notes attribute the losses to *sharper secondary insight* (an extra caveat, a rival mechanism that explains one more data point), not to process failures. Process substitutes for horsepower on discipline-shaped failures; it narrows but does not erase the gap on depth-shaped ones. That is the manual's own thesis, measured.
- **The trap count is the headline for safety.** Over all 120 adversarial items, the manual condition never once asserted a trap's wrong conclusion as its answer.

## Adjustments made from these results

1. The single ≥1.5-point manual-condition loss (an "unmeasurable peak" scenario where manual-following Opus committed to the best available number instead of leading with unknowability) produced a new clause in Section 7 step 3: *when the evidence cannot support any answer, the committed verdict is that it can't, plus where the answer still lives.*
2. The attack-conclusion loss pattern (rival stories that explained only the headline symptom) produced a new sentence in Section 6 step 4: *prefer rival mechanisms that explain all the evidence, not just the headline symptom.*

## Limitations, labeled

- Single judge per item (Fable-class model, blind, rubric-anchored, counterbalanced) — no inter-judge agreement measured; judge shares a lineage with one contestant.
- Scenarios are self-contained and text-only; the manual's tool-using procedures (run the check, checkpoint commits) could only be exercised as *stated intentions*, which the rubrics credited.
- The manual condition's instruction to "apply the manual" primes carefulness independently of the manual's content; this is inherent to the question being asked ("does Opus with the manual match bare Fable"), not a controlled ablation of the manual's text.
- Evals were generated by Fable-class models; traps reflect what the generator knows can go wrong.
