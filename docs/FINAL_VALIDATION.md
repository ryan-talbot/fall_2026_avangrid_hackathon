> Historical experiment record. See [current results](DECISION_EVIDENCE.md) for the final combined findings.

# Final validation and deck figures

Run from the repository root after the original showcase and screening milestone:

```powershell
.\.venv\Scripts\python.exe src/final_validation.py
```

The command runs 22 hand checks, validates the preserved 30-home baseline and
current frozen screening-rule/feature hashes, sizes both battery options with
July 1-4 excluded, freezes equipment and placements, runs chronological causal
dispatch, and generates the figures. No screening rules are retuned. All raw
inputs, household arrays, placements and outputs stay local in ignored `data/`.

## Scope and equipment freeze

This is a strict **unshifted measured-load** storage holdout. The earlier
managed-charging schedule is a historical optimization and is not fed into
this prospective dispatch check. Annual screening features are retained for
provenance, but do not determine the storage placements; this is not a new
temporal validation of appliance classification.

The scenario cap stays at 68.1300502762 kW (displayed 68.13005), as requested.
It is not recalculated from the remaining-days peak of 74.704 kW. The remaining
summer contains 2,088 common complete hours. The existing sizing model uses
perfect foresight on those hours only, with full SOC at each contiguous
training segment's endpoints. Omitted dates are not joined into artificial
adjacent hours, and no SOC is transferred across the training gaps.

Before test dispatch, `frozen_equipment.json` records the installed kW, kWh,
sites, home-module placement vector, prices, solver status, training data/hour
hashes, rule hash, policy hash and controller source hash. Its hash is checked
after replay. No held-out observation is passed to the sizing functions, and
equipment is not revised after failures are observed.

## Current-load/SOC-only dispatch

Both options start July 1 at 00:00 at **100% of their own rated energy**, with
20% reserve and charge/discharge efficiency sqrt(0.894). This is an optimistic
shared starting-charge assumption, not a measured battery state.

At each one-hour step, the controller uses the current observed load, carried
SOC, fixed equipment and fixed cap:

1. Above cap, discharge only the deficit, limited by inverter power, available
   energy above reserve, and each home's load (no export). Allocate across home
   sites proportionally to available AC energy, saturating at local limits.
2. Below cap, charge using present cap headroom, inverter power and capacity
   room. Allocate proportionally to missing energy. Charging is allowed at any
   hour, including overnight; there is no future-load forecast or price schedule.
3. Carry SOC across midnight. There is no daily reset or terminal top-up rule.

The same rule applies to the shared store and coordinated homes. It assumes
the current hourly-average load is available for that modeled step; it is not
a minute-by-minute hardware-control demonstration. A prefix-invariance test
changes future loads and confirms that earlier actions and SOC do not change.

If an input hour is missing, no flow is inferred, SOC is carried unchanged,
and the gap is reported rather than counted as cap-feasible. In this run,
all 96 July 1-4 test hours are complete. The only common summer gap is August 12
01:00 through August 13 00:00, 24 hours, outside the test and excluded from sizing.

The replay continues through July 5 06:00 to audit recharge after the final
withheld day. Those six hours are **not included in withheld cap-miss counts**.

## Results produced

| Frozen design | kW / kWh | Sites | Assumed installed cost | July 1-4 hours above cap | Worst miss | Result |
|---|---|---:|---:|---:|---:|---|
| Shared | 7.5 / 15 | 1 | $24,750 | 19 | 12.022950 kW | FAIL |
| Coordinated homes | 7.68 / 20.16 | 2 | $23,000 | 16 | 10.946950 kW | FAIL |

The home design installs one 10.08 kWh / 3.84 kW module at each of two sites.
Both designs meet the cap on the sizing data but fail the withheld heat-wave
replay. Shared misses total 91.586834 kWh; home misses total 75.974478 kWh.
These are model cap-exceedance energy, not customer energy not served.

Both designs are fully charged by 06:00 on every audited morning. July 1 starts
full by assumption; later mornings follow uninterrupted dispatch. Where not
already full at midnight, recharge finishes by 01:00. July 5 also completes
recharge, in the unscored extension. SOC reaches the 20% reserve during the
withheld daytime events: completed overnight recharge does not prevent failure
of these smaller designs.

## Deck figures

Each is saved as a **300 dpi PNG and vector SVG** in
`data/processed/final_validation/figures/`:

- `cleargrid_historical_july3`: measured load, simulated shared/home grid load,
  charge/discharge and SOC through July 5 06:00. The title explicitly labels
  **perfect-foresight sizing and dispatch**. Night hours are shaded. It uses the
  preserved full-summer model outputs, not the withheld equipment.
- `cleargrid_installed_costs_10_vs_15`: the verified historical full-summer
  comparison. At 10%, homes cost $31,500 versus shared $34,500. At 15%, shared
  costs $50,750 versus homes $60,000. Prices are assumptions; no bill savings or
  infrastructure-deferral value is claimed. The two targets bracket a change in
  the cheaper historical option but do not locate an exact crossover.
- `cleargrid_withheld_july1_4`: a separate heat-wave figure using the frozen,
  smaller designs and causal replay. It labels both failures and marks the July 5
  recharge-only extension separately.

`figure_manifest.json` hashes the figure source tables and exported images.
`historical_july3_figure_data.csv` and
`historical_installed_cost_figure_data.csv` hold the plotted historical values;
`withheld_shared.csv` and `withheld_home.csv` hold every causal hourly flow and
start/end SOC. Per-site NPZ audits retain no-export, power and energy evidence.
`validation_results.json` and `validation_summary.md` provide the machine- and
slide-readable results, including all overnight checks.

## Slide-ready takeaway

Historical full-summer sizing changes the cheaper option from homes at 10% to
shared at 15%. With July 1-4 withheld, the cheaper, smaller training designs
both fail causal heat-wave replay despite complete overnight recharge. Present
historical feasibility and held-out reliability separately; the historical cost
comparison alone does not establish a reliable operating design.
