# Teammate and AI PowerPoint handoff

An AI with GitHub access can read the evidence and use these PNG/SVG charts.
If its connector cannot fetch images, clone/download the repository and give
it the aggregate `deck/` folder. Do not upload raw or customer-level organizer
files to external AI services. Ignored local files cannot be fetched from GitHub.

## Copy this prompt into your presentation AI

> Build our ClearGrid Avangrid hackathon PowerPoint from this repository.
> First read `deck/AI_HANDOFF.md`, `deck/README.md`, `deck/evidence/results.json`,
> `deck/evidence/claims.json`, `docs/DECISION_EVIDENCE.md`, and
> `docs/RUBRIC_ALIGNMENT.md`. Inspect the PNG/SVG charts in `deck/figures/`.
> Prioritize Business Value (40%) and Analytics & Modeling (35%). Follow the
> slide outline below. Explain model equations and assumptions on slides:
> a GitHub link alone is insufficient because judges score the deck.
> Check numbers against the claim register and chart CSVs. Distinguish measured,
> estimated, simulated and assumed quantities, and original results from later
> refinements. Do not invent ownership precision, field performance, bill savings,
> solar revenue, upgrade deferral or real feeder topology. Mark restricted local
> examples as required team insertions; never fabricate them. Provide a source
> and caption checklist, then inspect the rendered slides for readability.

## Suggested main deck

| Slide | Message and asset |
|---:|---|
| 1 | **Turn meter evidence into a utility decision.** Outreach-to-storage framework and conditional 15% cost result. |
| 2 | **One pipeline, two validation questions.** Workflow; diversity/SOC equations; reserve, cap, no-export and complete-hour handling. |
| 3 | **Four outreach routes with evidence.** Segment/priority charts; 33,674-meter denominator, overlapping flags, assumed review budgets. |
| 4 | **Signals support confirmation.** Original EV 17/90 and heating 4/43 recovery; baselines and uncertain appliance appendix. Authorized team inserts two local household examples. |
| 5 | **Concrete BTM versus shared equipment.** Homes six modules/three sites, 23.04 kW/60.48 kWh/$60,000; shared 12.5 kW/55 kWh/$50,750. Original display placements 6/11/19 each have two modules; optimizer 3/4/6 is a separate equal-cost solution. Detailed household table is local. |
| 6 | **July 3 determines historical need.** Historical group dispatch/SOC with overnight recharge; label perfect foresight. |
| 7 | **Equipment steps cause repeated cost switches.** Refined chart: 40 queries, 80 certified costs, five transition regions <0.01 percentage point. No unique smooth crossover. |
| 8 | **Managed charging misses the sizing event.** Assumed 50% flexibility moves 19.279 kWh on nine dates, none July 3; 41 cap-miss hours remain without storage. Program cost unknown. |
| 9 | **Historical feasibility differs from held-out reliability.** Four-design heat-wave results and outages; larger designs' sizing already used the test dates. |
| 10 | **Test beyond the showcase.** Original six-group run five wins/one unresolved; separate extension resolves the last as a $34,500 tie. Two wins rely on home lower bounds. |
| 11 | **The cost advantage has a limit.** Extra $9,250 shared capex erases its 15% advantage; annualized sensitivity uses assumed horizons/rates. |
| 12 | **Confirm, engineer, shadow-test, then decide.** Proposed pilot, owners and go/no-go evidence. Missing tariffs/topology/ownership remain explicit. |

Put appliance coverage, detailed transition brackets and reproducibility in the
appendix. Do not put every available chart into the main deck.

## Critical checks

- Peak 80.153 kW, July 3 2026 14:00–15:00 local; 15% cap 68.13005 kW.
- Common summer hours 2,184/2,208; diversity 2.022744; missing hours not imputed.
- Original recovery: EV 17/90 at K=1,000; heating proxy 4/43 at K=500.
  Secondary 23/91 and 5/43 remain separately labeled. Unlisted is unknown.
- Original time-boxed and refined six-group results have different scopes.
  Latest decisions: five shared wins/one tie; two exact home optima unclaimed.
- Smaller strict-holdout designs miss 19 shared / 16 home hours. Larger designs
  pass **sized with the full historical record**, which includes those dates.
- Costs are assumed installed capital, not measured bill savings.
- Synthetic groups are not verified electrical neighborhoods. Shared connection,
  metering and interconnection feasibility require engineering.
- Unresolved device types stay unresolved. No finished PPTX is included here.

## Authorized local insertions

Use `data/processed/submission_package/ClearGrid_deck_evidence.zip` through the
approved hackathon workspace for household example and detailed placement
figures excluded from GitHub. Keep them in authorized local tooling. Raw inputs
and private cohort configs are required only for rerunning the model; aggregate
GitHub charts are ready to use without them.
