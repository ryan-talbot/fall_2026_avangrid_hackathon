> Historical experiment record. See [current results](DECISION_EVIDENCE.md) for the final combined findings.

# Screening, offers, and managed charging

Run from the repository root after the verified original showcase exists:

```powershell
.\.venv\Scripts\python.exe src/milestone.py
```

The command runs the hand checks, preserves the unshifted baseline, screens the
95%-coverage population, evaluates frozen rules, creates customer-to-offer
tables, schedules estimated charging, and resizes both battery alternatives.
All customer data and outputs remain under ignored `data/processed/`.
No inputs or customer-level exports are uploaded or added to Git.

## Baseline and reproducibility

`baseline_unshifted_v1/` is a one-time copy of the verified
`original_showcase/` artifacts. Its manifest hashes every copied file. Later
runs verify the snapshot and never refresh it from newer scenario results.
The milestone also checks every common measured group-load hour against that
baseline, not only its peak. Display order comes from the snapshot's local ID
array. The baseline remains 80.153 kW, 2,184 complete summer hours, diversity
2.022744, and a 68.13005028 kW cap for the 15% comparison.

Results are in `data/processed/milestone_screening/`. The main review files are:

- `milestone_summary.md` and `milestone_results.json`: aggregate findings,
  reference recovery, scheduling audits, costs and cap misses.
- `customer_to_offer.csv`: all 33,674 qualifying customers, scores and reasons.
- `showcase_customer_to_offer.csv` / `showcase_offers.md`: the same 30 homes in
  supplied order, offers, evidence and simulated home-battery selections.
- `rules_frozen.json`, `features_before_reference.csv`, `reference_split.csv`:
  auditable rule freeze, pre-reference feature hash and validation split.
- `managed_charging_jobs.csv`: each night, assumed arrival/deadline, estimated
  mobile energy, scheduled energy, one-way shifted energy and power limit.
- `measured_showcase_load.npy`, `shifted_load.npy`, `managed_loads.csv` and
  `dispatch_managed_*.csv`: measured input and simulated household/grid/SOC
  outputs. Both batteries use the same saved shifted-load hash.
- `managed_dispatch_july3.png` / `installed_storage_costs.png`: generated
  dispatch/recharge and installed-price comparisons.

## Frozen screening rules

Rules and fixed outreach sizes are in `config/screening_rules.json`. They were
specified without fitting to EV/heat-pump IDs. The pipeline writes a rule hash,
computes and hashes features, and only then reads reference labels for
evaluation and known-PV lookup. Neither the development half nor the held-out
half is used for threshold tuning. Rules have not been adjusted to improve the
reported held-out recovery.

EV-like evidence requires a positive step of at least 1.2 kW, a 2-8 hour plateau,
an observed exit step and limited within-plateau variation. Arrival is between
16:00 and 04:00 and the observed session ends by 06:00. The estimated component
is above the mean pre/post-event load. Overlapping candidates are deduplicated.
The 0-100 index combines recurrence (45%), plateau flatness (30%), and recurring
months (25%). Eligibility requires at least 12 events, three months, and score
60. These shapes can also be other appliances; a large lead pool is expected
to need confirmation, and is not an estimate of EV prevalence.

Heating/cooling evidence uses daily hourly-average load on days with at least
22 valid AMI and temperature observations. Regression terms are heating-degree
exposure below 65 F, cooling-degree exposure above 70 F, weekend and intercept.
The score weights positive weather slope and partial R-squared equally. At
least 200 usable days, 30 cold / 20 hot days, partial R-squared 0.10 and score
60 are required. This is weather association, not appliance disaggregation or
a heat-pump-versus-resistance classifier. Seasonally changing occupancy and
other loads can confound the association.

Known PV is a reference-list lookup, with evidence index 100 for membership
and unknown (missing score) for unlisted homes. It does not measure production,
exports or batteries. All evidence indices are scores, not probabilities.

## Held-out reference recovery

A deterministic salted ID hash splits each EV/HP list 50/50. Ranking is over
the complete qualifying population, using descending score and ascending ID for
ties. Fixed outreach sizes are 1,000 EV-like and 500 heating; cooling also has
a 500-person list but no reference labels.

| Reference | Held-out total | Qualifying held-out | Recovered at fixed K | Recovery among qualifying |
|---|---:|---:|---:|---:|
| Likely EV | 100 | 90 | 17 / K=1,000 | 18.9% |
| Likely heat pump, tested via heating proxy | 50 | 43 | 4 / K=500 | 9.3% |

This is reference-list recovery, not precision or specificity. Unlisted means
unknown; the EV and HP labels are partial and not physically confirmed.
The population has 18,488 broad EV-like leads, 4,612 heating-response leads,
19,920 cooling-response leads, and 393 qualifying known-PV references. These
counts describe evidence rules, not verified appliance ownership.

## Routing to offers

Managed-charging outreach needs recurring EV-like evidence and overlap with
summer 16:00-22:00 load. Thermostat outreach needs a weather score of at least
60 and estimated weather-associated response of at least 0.5 kW. Confirm
equipment and controllability before enrollment.

The population battery screen uses residual summer evening demand after an
assumed 50% EV-component allowance: mean at least 2 kW and P90 at least 3 kW.
It is a profile screen, not a verified size or economic benefit. For the actual
30 homes, the table also shows residual demand after simulated scheduling,
contribution at the original group peak, and modules selected by coordinated
dispatch. Selected placements need not be unique at the same minimum cost.

Known PV supports an export *eligibility check*, not assumed exports or payment
eligibility. EV ownership and L1/L2, heat pump vs resistance, water heaters,
pools, hot tubs, solar+battery combinations and battery ownership remain
uncertain where the hourly AMI provides insufficient evidence.

## Managed-charging scenario

Only eligible EV-like homes participate. Exactly 50% of each estimated session
component is available to move; measured non-EV load and the other half stay
fixed. This is an assumption, not measured controllable energy or consent.
Multiple detected events on one household-night are one job, assumed connected
from first detected arrival until the next 06:00. Movable charging power is
limited to half the largest estimated session component that night. There is
no pre-arrival charging. Nights with any common missing hour, and sessions
crossing the summer/data boundary, stay unshifted.

Two linear programs first minimize remaining cap-miss energy, then minimize
actual shifted energy while retaining that improvement. Hourly bounds forbid
new cap-miss hours or worsening existing ones. This avoids gratuitous shifts
on already-feasible nights. Energy is conserved for every job by 06:00 and for
every household over the modeled summer. One-way shifted kWh is the sum of
removed positive charging, not the sum of removal and recharging.

Actual result: 18 showcase homes have managed-charging offers; 236 complete
night jobs contain 1,110.538 kWh of estimated EV-like components, of which
555.269 kWh is the assumed movable allowance. Only **19.278998 kWh** actually
moves, on nine summer dates. Household and night-job energy errors are zero;
no new summer peak or cap-miss hour is created. Six incomplete night windows
and one boundary session are excluded.

No energy moves on July 3, including the original 12:00-17:00 cap-exceedance
event. Thus the sizing event remains. The brief's 26.75 kWh over seven days does
not reproduce: current movement is 7.471002 kWh lower. The old component and
scheduling rules were not available. No particular seven-day calendar window
is inferred and no parameter was tuned to force the earlier result.

| Option at original 15% cap | Peak kW | Miss hours | Max miss kW | Equipment | Assumed installed storage cost |
|---|---:|---:|---:|---|---:|
| Managed charging alone | 80.153000 | 41 | 12.022950 | No battery | $0 battery hardware |
| Managed + coordinated homes | 68.130050 | 0 | 0 | 23.04 kW / 60.48 kWh, six modules at three sites | $60,000 |
| Managed + shared | 68.130050 | 0 | 0 | 12.5 kW / 55 kWh, one site | $50,750 |

Both battery designs are feasible on the same shifted load. Shared remains
$9,250 cheaper at this cap; the preferred option does not change. Battery
sizes and prices remain identical to the preserved unshifted baseline. These
are historical perfect-foresight results on complete hours, not a held-out
weather test. The same 20% reserve, symmetric sqrt(0.894) efficiency, power and
home no-export constraints, cap and recharge treatment remain in force.

The storage costs exclude unprovided managed-program software, incentives,
enrollment and operating costs. No bill savings, solar generation or avoided
infrastructure value is inferred. Managed charging alone has no battery capital
cost but is infeasible at the target; it is not a zero-cost feasible alternative.
