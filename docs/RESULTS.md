# Detailed results and validation

The [decision evidence](DECISION_EVIDENCE.md) provides the current 40-target
cost study and all six group decisions. This page documents operating and
financial scenarios and the acceptance workflow.

## One acceptance command

From the repository root in PowerShell, with authorized local inputs and the
completed checkpoints described in README:

```powershell
.\.venv\Scripts\python.exe src/finalize.py
```

This repeats full CRC checks on all four ZIPs, reads both workbooks, identifies
all four organizer PDFs, recomputes cache coverage counts, checks samples from
every CSV against the cache, hashes inputs/cache, runs hand checks and dependency
checks, verifies the frozen screening/baseline/figures, generates supplemental
analyses and a slide claim register, then creates both local submission ZIPs.
It compiles every distributed Python module. It does not rerun or overwrite
the original showcase, screening, holdout sizing or preregistered six groups.
It is not a second full ingestion of all 298 million rows. The separate
`src/clean_acceptance.py` run verifies a freshly created isolated environment
using `requirements-lock.txt`; it is not a different-machine test. Cached supplemental target results are accepted only when
their plan/model/load signatures match.

For a repeat acceptance using the recorded input audit, while still rechecking
all recorded raw/cache SHA256 hashes:

```powershell
.\.venv\Scripts\python.exe src/finalize.py --reuse-input-audit
```

For only supplemental analyses (no acceptance or packaging):

```powershell
.\.venv\Scripts\python.exe src/final_analysis.py
```

`config/final_review_plan.json` declares rankings, targets, financial assumptions,
and operating scenarios. Rules were not retuned. The supplemental benchmarks use
the existing, previously inspected held-out references; they are not a fresh
untouched validation. Changing the plan/model/load requires a fresh supplemental
output folder; preserve the old results for comparison.

## Latest results to use in the deck

All targets use the same 2,184 common complete summer hours, measured unshifted
AMI and the verified 30-home order. Missing 24 hours are not imputed. Summer
peak is 80.153 kW on July 3, 14:00-15:00; diversity is 2.022744. Full SOC is
required at each contiguous historical segment's start/end, not every midnight.

| Tested reduction | Shared assumed installed cost | Home assumed installed cost | Certified cheaper design |
|---|---:|---:|---|
| 7.5% | $28,000 | $20,000 | Homes |
| 10% | $34,500 | $31,500 | Homes |
| 12.5% | $44,250 | $51,500 | Shared |
| 15% | $50,750 | $60,000 | Shared |

Each comparison has a physically verified feasible incumbent and matching cost
lower bound. The preferred option differs at 10% and 12.5%; the exact crossover
is not solved, and multiple switches between sampled points are not excluded.
The original 10%/15% figures remain unchanged historical snapshots.

At 15%, shared is 12.5 kW / 55 kWh at one site; homes are 23.04 kW / 60.48 kWh
across three two-module sites. Original display placements 6, 11, 19 remain the
causal replay design; optimizer placements 3, 4, 6 are a separate equal-cost
solution. Do not mix the two tables. Home usable discharge is limited by its
own current load under no-export. An export-permission-only sensitivity also
certifies the $60,000 home cost: removing this constraint does not reduce
the minimum equipment cost in this showcase. It is not a solar-revenue case.

### Classification benchmark

| Likely reference | Ranking, fixed before comparison | Recovered / qualifying held-out | Fixed outreach K |
|---|---|---:|---:|
| EV | Frozen composite score | 17/90 | 1,000 |
| EV | Event count | 13/90 | 1,000 |
| EV | Summer evening mean demand | 9/90 | 1,000 |
| Heat pump | Frozen heating proxy | 4/43 | 500 |
| Heat pump | Temperature-response slope | 4/43 | 500 |
| Heat pump | Summer evening mean demand | 1/43 | 500 |

The EV score recovers more listed references than these two baselines in this
sample; the heating score does not improve over its raw slope baseline. No
statistical superiority, precision, complete technology inventory or ownership
probability is established. Wilson intervals in JSON are descriptive uncertainty
for the likely-reference sample, not confidence intervals for population accuracy.
Unlisted status remains unknown. See the appliance appendix for L1/L2, resistance
vs heat pumps, water heaters, pools, hot tubs and solar+battery uncertainties.

Population offer counts remain 17,493 managed charging, 7,593 thermostat,
5,766 battery assessments and 393 known-PV export checks, over 33,674 meters.
Offers overlap. Battery assessments are profile screens, not 5,766 sized sites.

### Operating and financial sensitivities

- Both full-record-sized designs pass July 1-4 causal replay at 100%, 80% and
  50% starting SOC on July 1. They can recharge before the critical event;
  this does not establish performance when depleted immediately before a peak.
- Removing any one original home battery site causes seven cap-miss hours.
  Worst misses: home 6 unavailable, 3.169 kW; home 11, 6.511 kW; home 19,
  4.937 kW. The shared-site-unavailable case is also included in model outputs
  and the new evidence panel: 29 miss hours, worst 12.023 kW. These are deterministic outages, not probabilities
  or an expected reliability comparison. No replacement equipment is assumed.
- At equal assumed 15-year financial horizons, the $9,250 upfront advantage is
  $616.67/year at 0% discount, approximately $891.17/year at 5%, or
  $1,080.67/year at 8%. These are annualized capital differences, not bill
  savings. Extra net shared recurring costs above the corresponding amount
  erase the advantage. Exact values are in the financial CSV.
- The threshold shared price is `home upfront cost - extra annual shared
  cost / CRF`, where `CRF = r / (1 - (1+r)^(-years))`, or `1/years` at zero
  rate. O&M, losses, program costs, degradation, replacements and salvage need
  actual evidence; the scenarios do not invent their amounts or tariff value.
- Managed charging remains 19.279 kWh shifted over nine dates, none on July 3;
  41 cap-miss hours without storage. The 50% flexibility and 06:00 ready-by
  assumptions are unchanged. Program operating costs are unknown.
- Strict excluded-date sizing still fails 19 shared / 16 home hours. Larger
  full-record-sized designs pass the same causal replay, having already used
  the test dates for sizing. All original heat-wave scope labels remain.
- Six additional preregistered groups remain five certified shared wins and
  one unresolved comparison; two wins use bounds, not solved home optima.

## Slide files and captions

New final panels (each has a same-named SVG and 300 dpi PNG):

| Path under `data/processed/final_analysis/figures/` | Takeaway and caption |
|---|---|
| `cleargrid_final_cost_sensitivity.svg` | **The preferred equipment depends on target and recurring costs.** Four historical targets are solved; the exact crossover is not. Annualized comparison assumes equal 15-year horizons and explicit discount rates; no tariff savings are measured. |
| `cleargrid_final_evidence_limits.svg` | **Keep the evidence and failure limits visible.** Retrospective fixed-K reference recovery favors the EV composite over two simple ranks; heating ties the slope baseline. Full-record-sized equipment passes lower starting-charge cases but home site loss causes misses. |

Use existing segmentation, two example profiles, appliance appendix and BTM
placement figures from `data/processed/submission_package/figures/`. Keep the
preserved July 3, 10%/15% cost and excluded-date heat-wave figures in
`data/processed/final_validation/figures/`. The pilot/workflow/impact panels
and `RUBRIC_ALIGNMENT.md` supply the main-deck narrative and criterion mapping.

Local release files under `data/processed/submission_package/`:

- `slide_claims.json` / `.csv`: source, unit, evidence type and scope per number.
- `release_acceptance.json`: pass/fail and exact source/artifact hashes.
- `verification_report.json`: hand-check count, frozen provenance, privacy audits.
- `input_acceptance.json`: ZIP/workbook/cache audit and input hashes.
- `ClearGrid_code_submission.zip`: runnable source, configs without meter IDs,
  dependency pins and documentation.
- `ClearGrid_deck_evidence.zip`: anonymized figure assets and slide guides.

Packaging refuses changed source or accepted artifacts until acceptance reruns.
All generated/customer-level outputs, raw/material inputs and actual meter IDs
remain local and ignored. Only source, safe config and documentation belong in
Git. The presentation package is documented in deck/PRESENTATION.md.

## Further evidence for deployment

Appliance subtypes require confirmed device labels. Customer bill savings
require tariffs. Field reliability requires prospective operating data.
A physical shared installation requires network, metering and interconnection
engineering. Known solar membership supports an export check, while measured
surplus and storage telemetry would support a solar operating scenario.

The completed presentation includes results, methods and assumptions.
The proposed next step is to confirm customer leads, assess real sites,
obtain quotes and test fixed equipment before expanding the program.

The latest post-budget decision and outreach evidence is in `DECISION_EVIDENCE.md`.
A separate isolated-environment acceptance report is saved at
`data/processed/submission_package/clean_environment_acceptance.json`; use its
pass/fail and recorded release hash to check the exact tested revision.
