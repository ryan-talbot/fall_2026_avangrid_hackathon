# Final focus: the 75% business and analytics criteria

This is the latest evidence addendum. Read it before older handoff snapshots.
The rubric weights business value at 40% and analytics/modeling at 35%.
The strongest supported recommendation is a targeted, engineered pilot
assessment, with conditional equipment economics and explicitly tested failures.
This document does not promise a judge score or complete appliance ownership
identification from hourly net consumption.

## Business value: close the decision, not just the solver

### Storage preference changes more than once

`src/decision_refinement.py` evaluates the same verified unshifted 30-home
summer data, cap definition, costs and storage constraints. Forty target
queries produce 80 certified minimum-cost option results. Every queried option
has a physically verified incumbent and matching lower bound. No queried
comparison remains unresolved.

We additionally certify whole intervals using monotonic costs: if the feasible
shared cost at the stricter target is below the necessary home cost at the
easier target, shared wins throughout that interval, and vice versa. Matching
winners at two endpoints alone do not establish this; a hand test checks that
distinction. This accounts for switches hidden between sparse sample points.

Five narrow transition regions remain at the **declared numerical resolution**:

| Reduction bracket, percent | Cheaper at left -> right | Equipment-cost reason at the bracket |
|---|---|---|
| 7.675781-7.685547 | Homes -> shared | Homes jump from 2 modules/1 site ($20,000) to 3/2 ($31,500); shared is $31,250. |
| 8.818359-8.828125 | Shared -> homes | Shared jumps from 25 to 30 kWh ($31,250 to $34,500); homes remain $31,500. |
| 10.058594-10.068359 | Homes -> shared | Homes jump from 3 modules/2 sites ($31,500) to 4/2 ($40,000); shared is $37,750. |
| 11.181641-11.191406 | Shared -> homes | Shared jumps from 35 to 40 kWh ($37,750 to $41,000); homes remain $40,000. |
| 12.431641-12.441406 | Homes -> shared | Homes jump from 4 modules/2 sites ($40,000) to 5/3 ($51,500); shared is $44,250. |

Each bracket is less than 0.01 percentage point wide (about 0.008 kW of cap).
Every other interval over 7.5%-15% has a whole-interval winner certificate.
Do not claim an exact real-number threshold, exactly one crossing, or a smooth
interpolated cost curve. Additional switches inside these tiny brackets are
not excluded. This numerical precision is sufficient to support the tested
10%/15% choices without implying a uniquely optimal program target.

The headline 15% result is unchanged: shared $50,750 versus homes $60,000;
the $9,250 advantage disappears with that much extra shared upfront cost,
holding everything else fixed. Annualized scenarios, costs and failures are
in `FINAL_CODE_HANDOFF.md` and the final-analysis JSON/CSV.

### All six sampled group comparisons now have a decision

The original preregistered one-hour-budget experiment stays unchanged:
**five shared wins and one unresolved comparison**. A separately labeled
post-budget refinement resolves group 6 as a **$34,500 tie**:

- Shared: 12.5 kW / 30 kWh, one site.
- Homes: 11.52 kW / 30.24 kWh, three single-module sites.
- The original group/load, common hours, cap and cost assumptions are retained.
- Cost-ordered exhaustive enumeration examines 1,282 placements; 1,281 fail
  necessary hourly power cuts and the first feasible configuration passes
  full-horizon LP dispatch at $34,500. All cheaper configurations are excluded.
- An independent acceptance audit recomputes SOC balance, reserve, power,
  no-export, cap compliance and full-charge segment endpoints from per-site
  arrays. The cost lower and upper bounds coincide.

With the extension, the six comparisons are **five shared wins, zero home
wins, one tie and zero unresolved comparisons**. Two shared wins still use
home cost lower bounds rather than completed home optima. Those exact home
optima are not needed for the certified decision and are not claimed as costs.
The six groups are synthetic, not a representative feeder sample.

### Turn broad segments into a review queue

`src/outreach_evidence.py` creates local customer-level queues and aggregate
slide evidence. The planned review capacities are assumptions, not enrollment
or an estimated number of confirmed devices:

| Offer | Candidates / 33,674 | Planned reviews | Priority evidence | Required utility action |
|---|---:|---:|---|---|
| Managed charging | 17,493 | 1,000 | Estimated EV-like summer evening overlap, then frozen EV score | Confirm EV, availability, consent, charger and ready-by before control. |
| Thermostat | 7,593 | 500 | Estimated heating/cooling weather response, then thermal score | Confirm HVAC/control compatibility and comfort needs. Includes winter-oriented leads; it is not a summer-only peak ranking. |
| BTM assessment | 5,766 | 500 | Screened residual evening demand, then observed evening P90 | Size constrained equipment, confirm real site/service/topology and obtain quotes. |
| PV export eligibility | 393 | All 393 | Known-PV list membership only | Verify surplus, metering, permissions and compensation; no battery or export revenue inferred. |

The top review queues have measured-derived median summer evening demand of
2.53 kW for managed charging and 4.61 kW for BTM assessment, versus candidate
medians of 1.56 and 2.61 kW. These describe ranked profiles; they are not causal
program effects. Thermostat priorities have a 1.37 kW summer evening median
versus 1.82 kW among all thermostat candidates because their ranking targets
weather sensitivity in either season, not exclusively summer magnitude.

Offers overlap. A complete 16-combination accounting sums back to all 33,674
meters, including those needing additional evidence. PV ties are ordered by
anonymous ID administratively; there is no benefit ranking without telemetry.
Program-priority queues are different from the fixed-score classification
evaluation lists. Do not attach the latter's recovery counts to the former.

## Analytics: stronger validation without changing the frozen rules

The original held-out reference recovery remains **EV 17/90 at K=1,000 and
heating proxy 4/43 at K=500**. The fixed-score benchmark remains EV 13/90 for
event count and 9/90 for evening demand; heating ties its raw slope baseline
at 4/43. No significance or ownership-precision claim is made.

Separately evaluating the originally unused development half gives **EV 23/91
at K=1,000 and heating proxy 5/43 at K=500**. Features and primary rules are
unchanged from their original pre-reference freeze; no thresholds were retuned.
These secondary diagnostics are not an independent prospective or physical
ownership validation. Never silently pool them into the original held-out result.

This evidence supports an outreach screen, not a complete equipment inventory.
Unlisted is unknown. Weak heating recovery and unresolved appliance subtypes
remain visible in the slide appendix. Net hourly load does not establish L1/L2,
resistance vs heat pump, water heaters, pool/hot tub ownership, or solar+battery
ownership reliably enough to claim them as solved.

## Criterion-to-evidence check for the two largest categories

| Criterion | Evidence judges should see | Boundary on the claim |
|---|---|---|
| Utility relevance | Four offers, real meter/weather evidence and program review queues | Confirm technology, topology and eligibility before enrollment. |
| Actionability | Specific review budgets/ranks, original three BTM placements and pilot gates | Budgets and pilot are proposed, not executed. |
| Battery opportunity | Per-home modules, no-export ceilings, remaining-group cap, shared alternative | Population battery flags are assessments, not sized deployments. |
| Quantified impact | 12.023 kW historical relief, 19.279 kWh shifted, installed prices, causal cap misses | No verified bill savings or actual upgrade-deferral value. |
| Recommendation quality | Five transition regions, six resolved group decisions, annualized headroom and outage failures | Conditional installed-cost preference; quote/site/control validation still required. |
| Classification accuracy | Original and separate secondary reference recovery, simple baselines, honest device appendix | Partial likely labels; no negative labels, precision or complete subtype recovery. |
| Segmentation | Overlapping offers plus exhaustive exclusive combinations and profile statistics | Behavioral segmentation, not confirmed technology prevalence. |
| Technical rigor | Constrained optimization, exhaustive placement proof, monotonic certificates and hand cases | Historical sizing and causal replay are different questions. |
| Use of data | Qualified AMI, hour-start weather, known PV, references and complete-hour handling | No invented tariff, topology, export telemetry or appliance ground truth. |
| Reproducibility | Frozen hashes, recorded plans, preserved attempts, acceptance checks and local code/evidence archives | Data remain local; final PowerPoint reconciliation is a separate review. |

## Reproduce and hand off

Run the final acceptance command after the original checkpoint outputs exist:

```powershell
.\.venv\Scripts\python.exe src/finalize.py --reuse-input-audit
```

Omit `--reuse-input-audit` for fresh ZIP CRC/workbook checks. That option still
hash-verifies all recorded raw/cache inputs. To run only the new evidence:

```powershell
.\.venv\Scripts\python.exe src/decision_refinement.py
.\.venv\Scripts\python.exe src/outreach_evidence.py
```

Newest slide panels, each SVG and 300 dpi PNG:

- `data/processed/decision_refinement/figures/cleargrid_decision_refinement.svg`
  Caption: **Equipment steps create repeated cost preference changes; all
  queried costs are certified, transition regions are bounded, and group 6
  ties after a separately labeled refinement.**
- `data/processed/outreach_evidence/figures/cleargrid_outreach_priorities.svg`
  Caption: **Rank local review queues using program-relevant meter/weather
  evidence, then confirm device, site and customer requirements before action.**

Customer queues and IDs stay in ignored `data/processed/outreach_evidence/`.
All new aggregate panels and this guide are included in the local deck ZIP.
No raw inputs, customer CSVs or per-site arrays are distributed in code Git/ZIP.

## Evidence closure: unknown is not a fabricated result

There is no unresolved winner at any queried target or among the six sampled
group comparisons after refinement. Continuous thresholds have explicitly
bounded numerical resolution. Exact home optima for two already-certified
shared wins are not asserted. Missing device ground truth, tariffs, solar
telemetry, feeder mapping and prospective field performance are data limits,
not values to fill with guesses. The recommendation is deliberately conditional
on those confirmation steps. The final deck must retain these boundaries.


A complete dependency lock and isolated-environment acceptance are also supplied.
See README for `src/clean_acceptance.py`, and inspect the local
`clean_environment_acceptance.json` report for its pass/fail, package graph and
exact accepted release hash. This reuses audited local caches; it does not
claim a second 298-million-row ingestion or a test on a different machine.
