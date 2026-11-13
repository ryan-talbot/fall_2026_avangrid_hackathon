**Latest business/analytics addendum:** [DECISION_EVIDENCE.md](DECISION_EVIDENCE.md)
resolves the sixth comparison as a separately labeled tie, certifies 40 target
queries with five narrow transition regions, and adds ranked review queues plus
secondary frozen-rule diagnostics. Older figures/results below remain preserved
snapshots; use the addendum for current claims.

# ClearGrid: judge-facing rubric review

**Final update:** [FINAL_CODE_HANDOFF.md](FINAL_CODE_HANDOFF.md) now adds four
solved targets (7.5%, 10%, 12.5%, 15%), retrospective screening benchmarks,
annualized/export sensitivities, deterministic outage tests and a final claim
register. Use those results alongside this criterion mapping. Earlier two-target
assets remain preserved historical snapshots.


Reviewed against the organizer's two-page **Hackathon Rubric Criteria** in
`data/materials/9ccbd22a-24bc-4f39-aca5-917e9af0633e.pdf` and the challenge
statement. This is an evidence-coverage review, not a predicted judge score.

**Overall:** the strongest material is the transparent program-to-storage
decision framework, constrained battery comparison, installed-price sensitivity,
and honest causal stress testing. Appliance identification is **partial**, and
presentation quality cannot be certified until the final PowerPoint is
assembled and reviewed. No PPT/PPTX was found in this repository during this
review. Code, CSVs and attractive images alone do not establish deck coverage.

## Changes made to make the evidence clearer

Three new 16:9 SVG/PNG panels are generated from existing verified outputs:

- `data/processed/submission_package/figures/cleargrid_rubric_impact.svg`:
  puts measured peak, simulated relief/shift, conditional capital-cost advantage,
  reference recovery, and stress-test limitations on one scorecard.
- `data/processed/submission_package/figures/cleargrid_rubric_workflow.svg`:
  shows the complete input-to-offer-to-sizing-to-validation workflow, diversity
  and SOC/cap constraints, demonstrated scale and the proposed scaling path.
- `data/processed/submission_package/figures/cleargrid_rubric_pilot.svg`:
  supplies a concrete **proposed**, not executed, Avangrid pilot with owner roles,
  confirmation tasks, field evidence, and go/no-go checks.

Each SVG has a same-named 300 dpi PNG. No frozen rule, fitted feature, equipment,
solver outcome or protected historical figure was changed to improve the story.

## Criterion-by-criterion coverage

Slide numbers refer to the recommended sequence below. **Supported** means an
evidence artifact exists; it still needs to be visible in the PowerPoint.
**Partial/proposed** explicitly identifies evidence not established by this work.

| Rubric area | Criterion | Current evidence and on-slide claim | Assessment / required treatment | Slide |
|---|---|---|---|---:|
| Business value **40%** | Utility relevance | 33,674 qualified meters routed to managed charging, thermostat, BTM assessment or PV export check; compare feasible storage at a utility peak cap. | Supported. Lead with the utility decision, not a generic battery sales pitch. | 1, 3 |
| Business value | Actionability | Population and 30-home offer tables; specific home placements; proposed confirmation, site study, shadow test and expansion gates. | Partial/proposed. No enrollment or field pilot has occurred; the new pilot panel makes the next action concrete. | 5, 12 |
| Business value | Battery opportunity assessment | Home hourly no-export dispatch, reserve/power/energy/recharge constraints, actual modules/sites, shared alternative at the same cap. | Supported as a historical planning assessment. The population battery flag is a profile screen, not 5,766 sized installations. | 5, 6 |
| Business value | Impact quantification | Measured peak 80.153 kW; 68.13005 kW cap; 12.023 kW historical modeled reduction; 19.279 kWh scenario shifting; installed kW/kWh/sites/prices and cap-miss counts. | Supported for these modeled outcomes. Bill savings, real infrastructure capacity relief and electrification enablement are not measured. | 1, 6, 8, 9 |
| Business value | Quality of recommendations | Four tested target choices, $9,250 price headroom, six additional groups with bounds, omitted-date failures, proposed field gates. | Supported conditionally. Recommend confirmation/stress-tested pilot assessment, not immediate deployment or verified upgrade deferral. | 7, 9-12 |
| Analytics **35%** | Customer classification accuracy | Frozen engineering rules; EV held-out recovery 17/90 at K=1,000; heating proxy 4/43 at K=500; example traces; explicit appliance appendix. | **Partial and the main analytic weakness.** Recovery is not precision or complete classification. L1/L2, HP vs resistance, water heating, pools, hot tubs and batteries are unresolved. Do not claim all requested appliances were identified. | 3, 4; appendix |
| Analytics | Segmentation quality | Four overlapping, quantitatively defined outreach segments, with counts, meter/weather evidence and an Avangrid action for each. | Supported as program-oriented segmentation. These are overlapping rules, not learned/exclusive clusters or confirmed ownership populations. | 3 |
| Analytics | Data science / technical rigor | Local chunked qualification; repeatable evidence features; label holdout; constrained sizing; energy-conserving 06:00 charging jobs; causal controller; 31 hand checks; certified cost bounds. | Supported. Distinguish perfect-foresight optimization from chronological replay and explain why a solver timeout is not infeasibility. | 2, 8-10 |
| Analytics | Use of available data | AMI, hourly-start aligned temperature and known technology references; duplicated fall weather hour averaged; incomplete AMI excluded. | Supported. No feeder/transformer mapping, generation/export telemetry or storage ownership was supplied; humidity/wind are ingested but not used as classifier predictors. | 2; appendix |
| Analytics | Transparency / reproducibility | Frozen rule hashes, exact cohort/configs kept local, recorded seed/sampling, all six attempts retained, README, direct dependency pins, runnable commands and provenance manifests. | Supported. Keep the main method and assumptions visible on a slide; a GitHub link is not a substitute for explaining them. | 2, 10; appendix |
| Communication **15%** | Slide quality | Readable 16:9 SVG and 300 dpi PNG panels; consistent measured/estimated/simulated/assumed labels; revised captions and clear failure labels. | **Final deck unverified.** Check typography, cropping, slide density, source notes and exported PowerPoint rendering after assembly. | All |
| Communication | Clarity of explanation | New workflow includes the physical equations; placement table explains local no-export ceilings; price panel separates variable from fixed/site assumptions. | Supported in assets. Explain cap, kW, kWh, reserve and scope once before using charts. | 2, 5-7 |
| Communication | Storytelling | Recommended decision -> evidence -> segments -> BTM candidates -> dispatch -> price -> control/stress -> pilot narrative. | **Assembly pending.** Avoid opening with solver logs, an unsupported universal shared-storage claim, or thirteen unrelated charts. | 1-12 |
| Communication | Visualization effectiveness | Customer segment counts, actual profiles, placement evidence, SOC/recharge, two-target costs, six-group outcomes, heat-wave scope and price sensitivity. | Supported assets. Choose the original or optimizer placement consistently; do not mix original 6/11/19 with optimizer 3/4/6 without the note. | 3-11 |
| Innovation **10%** | Novelty of approach | Connect appliance evidence and program routing to a fair, constrained BTM/shared decision and a separate causal reliability check. | Supported as an integrated utility workflow. No world-first, novel ML model or benchmark superiority is established. | 1, 2 |
| Innovation | Creative use of data | Real meter profiles form synthetic neighborhoods; current-load/SOC-only replay exposes hindsight sizing risk; partial references evaluate prioritized outreach without treating unknowns as negatives. | Supported exploratory integration. Synthetic groups must not be described as actual electrical neighborhoods. | 2, 4, 9 |
| Innovation | Additional insights | Lower cost flips between two tested targets; nominal inverter kW is limited by home no-export; modeled EV flexibility misses the July 3 sizing event; good recharge does not fix undersizing. | Supported. These specific findings are more defensible than generic claims about AI, savings or grid transformation. | 5, 7-9 |
| Innovation | Scalability | 298,032,553 rows ingested locally; 33,674 screens; memory-mapped/chunked inputs; bounded cohort solves; partial results and certificates retained. | **Partial/proposed.** Local throughput is demonstrated, million-meter production and utility systems integration are not. New workflow/pilot panels show the scaling path and blockers. | 2, 12 |
| Optional bonus | Exceptional creativity, rigor or utility potential | Traceable offer decisions, exact equipment alternatives, preserved failure evidence and bound-safe decisions even when some solves time out. | A defensible bonus narrative, not evidence of an awarded bonus. Keep the utility action and reliable decision boundaries central. | 9, 10, 12 |

## Recommended main-deck sequence and speaker lines

| Slide | Headline / required asset | Short speaker line |
|---:|---|---|
| 1 | **Choose a feasible offer and storage design at the required peak cap.** New impact scorecard. | We turn meter evidence into outreach and compare managed load, BTM batteries and shared storage at one common target. Reported economics are assumed installed prices. |
| 2 | **One transparent pipeline, two distinct validation questions.** New workflow. | Qualify inputs, freeze screening rules, evaluate reference recovery, size constrained equipment, then separately test a causal controller. Screening recovery and storage generalization are different tests. |
| 3 | **Four outreach routes, with explicit denominators and evidence.** Segment visual. | These overlapping flags were evaluated for all 33,674 qualified meters. They are leads, not ownership prevalence or guaranteed enrollments. |
| 4 | **AMI and weather support a conversation, not a device guarantee.** Two examples + held-out results. | EV recovery is 17/90 at K=1,000 and heating proxy recovery is 4/43 at K=500. Unlisted is unknown; other appliances can resemble these signals. |
| 5 | **Make the BTM fleet concrete and show its local limit.** Original 6/11/19 table, or explicitly labeled optimizer 3/4/6 table. | Two modules per selected site give 23.04 kW / 60.48 kWh across three sites. A battery cannot reduce a neighbor's bill-meter draw through home export in this model. Placements are not unique. |
| 6 | **The full July 3 event determines storage need.** Historical dispatch/SOC figure. | The 80.153 kW peak needs 12.023 kW relief at the 68.13005 kW cap, but energy, reserve and recharge over the whole event drive sizing. This curve is perfect foresight. |
| 7 | **The cheaper historical option depends on target and installed cost.** 10%/15% cost figure. | Homes are $3,000 lower at 10%; shared is $9,250 lower at 15%. The preserved figure shows two baseline targets; the final appendix adds 7.5% and 12.5%. The preferred option differs at 10% and 12.5%; the exact crossover is unsolved. |
| 8 | **Managed charging helps some hours but does not remove the critical event.** Managed scenario trace or impact scorecard excerpt. | The assumed 50% estimated EV allowance moves 19.279 kWh on nine dates, none on July 3; charging energy is conserved by 06:00, and storage sizes remain unchanged. Program costs are unknown. |
| 9 | **Passing historical sizing does not establish held-out reliability.** Four-design scope table. | Smaller omitted-date designs fail 19 and 16 hours. Larger designs pass the same causal replay after their sizing already used these dates. Every audited morning recharged by 06:00. |
| 10 | **Challenge the business result beyond the showcase.** Six-group table. | Five certified shared wins and one unresolved comparison, including every sampled group. Two wins use home cost lower bounds rather than a completed home optimum. This is not a representative utility sample. |
| 11 | **There is $9,250 of shared installed-price headroom, not a verified saving.** Sensitivity figure. | $15,250 lower modeled variable cost offsets $6,000 higher fixed/site allowance in the showcase. Extra shared capex of $9,250 removes the advantage if everything else stays fixed. |
| 12 | **Confirm, engineer, shadow-test, then decide whether to expand.** New pilot. | Start with prioritized outreach, confirm real topology and service limits, obtain quotes, and test telemetry/control on prospective peak periods. Expansion needs the agreed field target and a complete cost comparison. |

Appendix: appliance coverage/unresolved types; coverage/DST/missing-hour detail;
reference split and recovery denominator; solver statuses and primary-cost
bounds; full model assumptions and commands. Do not hide the primary recovery
numbers, assumption labels or causal failure scopes only in the appendix.

## Guardrails for wording and interpretation

- **Say:** held-out reference recovery. **Do not label it:** accuracy, precision,
  ownership probability, recall of all EVs/heat pumps, or confirmation of devices.
  The recovered references are sampled likely labels; many meters are unlisted.
- For context only, uniform random K-person outreach from the qualifying
  population would recover **2.67 EV and 0.64 HP references in expectation**.
  Actual recoveries are about 6.36 and 6.26 times those expectations. This
  arithmetic benchmark is not a statistical significance test or an estimate of
  production precision; it does not resolve the missing appliance categories.
- **Say:** modeled historical peak reduction and assumed price difference.
  Do not claim measured bill savings, real upgrade deferral, production-grade
  reliability or proven electrification headroom.
- A **shared planning alternative** is not automatically a behind-the-meter
  implementation serving thirty separate meters. Real network topology,
  connection location, metering and the operating arrangement need engineering
  confirmation. BTM customer assessment remains an explicit primary offer.
- The 20% reserve and 89.4% round-trip efficiency are assumptions/specification
  inputs; a model beginning at 100% charge is not a measured installed SOC.
- Keep the two placement lists and three validation scopes distinct: full-record
  perfect foresight, excluded-date equipment sizing + causal replay, and
  full-record equipment + causal replay. None is a prospective field trial.

## What is genuinely still missing

1. Complete appliance identification/validation for all requested types. Closing
   this requires additional labels/features or confirmation data; rewriting
   captions cannot turn unknowns into established detections. Do not tune the
   frozen rules on their already-used held-out IDs.
2. A real topology/metering/interconnection/site study, prospective controller
   validation and approved operating target for a physical pilot.
3. Tariffs, quotes, incentives/control costs, participation, O&M, solar/export
   data and a lifecycle business case. The $9,250 installed-price headroom does
   not quantify these missing items or justify an immediate capital decision.
4. The assembled, rendered and reviewed PowerPoint. Presentation and
   communication cannot be called complete from a code/asset review alone.

## Final slide QA against the rubric

- Opening slide answers the utility decision and gives only supported numbers.
- Every main figure has a headline, scope, denominator/time window, units and
  measured/estimated/simulated/assumed labels.
- Held-out recovery and unknown appliance status are visible; unresolved
  categories remain explicit in the appendix.
- At least one concrete BTM fleet, local no-export example and shared
  alternative appear with kW, kWh, modules/sites and assumed cost.
- The operating-impact claims and limits are separate from installed-price
  assumptions; there is no invented bill saving or avoided-upgrade value.
- Heat-wave failures, full-record larger passes, unresolved group and solver
  time limits are visible and correctly labeled.
- Pilot roles, measurements, gates and scalability blockers are explicit and
  labeled proposed.
- Images remain legible at actual slide size; the exported deck is checked for
  font substitution, cropping, overloaded tables, captions and a coherent story.

Rerun this clarity pass without changing frozen results:

```powershell
.\.venv\Scripts\python.exe src/finalize.py
```
