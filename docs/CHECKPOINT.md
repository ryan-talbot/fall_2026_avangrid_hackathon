> Historical experiment record. See [current results](DECISION_EVIDENCE.md) for the final combined findings.

# First implementation checkpoint

The repository initially contained only setup documentation, unpinned dependencies,
empty `src/` and `notebooks/` directories, and local inputs. There was no prior
loader, classification model, dispatch implementation, notebook, chart, or deck
to extend. The existing `.gitignore` already excluded everything under `data/`.
The pre-existing untracked `AGENTS.md` and `PROJECT_BRIEF.md` were preserved.

## Organizer documents identified from their contents

| Local filename under data/materials | Contents | Pages |
|---|---|---:|
| Challenge Statement.pdf | Three-part classification, segmentation, flexibility/BESS challenge; hourly AMI and weather; two-unit battery specs; deck and code deliverables | 6 |
| 9ccbd22a-24bc-4f39-aca5-917e9af0633e.pdf | Hackathon Rubric Criteria: business 40%, modeling 35%, presentation 15%, innovation 10% | 2 |
| Hackathon Kickoff 2026.pdf | Kickoff, judging, schedule and final submission instructions | 13 |
| bfa64195-8e14-4168-b7f4-32c9caf4ee02.pdf | Hackathon Data Dictionary: AMI fields, hour-ending conventions, weather and reference labels | 7 |

The kickoff requires a self-contained deck and code/tool, with filename
`team number_team name_Final Submission`, in the team's SharePoint folder by
5 PM ET November 13. Only the deck is scored. The challenge's approximate
3 kVA service-load figure is a review trigger, not a neighborhood battery limit.

## Local inventory and ingestion

The four AMI archives contain 199 readable CSVs: 52 for IDs 1-10000, 44 in the
10001-20000 **v2** archive, 51 for 20001-30000, and 52 for 30001-35725.
Every archive passed `ZipFile.testzip()` (full decompression/CRC).
Actual headers: `CUSTOMER_NUMBER, usage_date, hour_ending, day_type,
hourly_kwh, interval_count, interval_type, is_complete_hour`.

`EV_Heat Pump_Solar PV Customers.xlsx` has Description, EV Customers (200 rows),
HP Customers (100), and PV Customers (434). Reference tabs use CUSTOMER_NUMBER.
Unlisted EV/HP status is unknown; PV membership does not measure generation or storage.
`Weather Data_Avangrid_Hackathon .xlsx` has Sheet1 (8,761 rows):
date, time, temp, humidity, windspeed. Both workbooks were fully read.

The weather timestamp 2025-11-02 01:00 occurs twice. Average the numeric
observations to one local hour; join to usage_date + (hour_ending - 1) hours.
No timezone/fold is inferred. Every local timestamp is present; the workbook
has 94 missing temperature observations, 94 humidity observations, and 93
windspeed observations in March. These remain missing. Units are degrees F,
percent relative humidity, and mph respectively.
Weather is prepared for later modeling, not used to choose batteries here.

The loader processes 400,000 rows at a time into a local float32 memory-mapped
matrix. It accepts finite, in-period hours only when is_complete_hour=1 and
interval_count=4. Coverage counts distinct meter-hour slots against 8,760.
No duplicate slots were observed. Raw inputs, matrix, identifier lists,
inventory samples, dispatch CSVs and charts all remain in ignored `data/`.

## Model and hand checks

Diversity = sum of individual maxima / maximum of the summed load, using the
same complete time window for every home. Two 4 kW staggered loads give 2;
the same coincident loads give 1.

Hourly energy balance is SOC[t+1] = SOC[t] + eta*charge - discharge/eta,
with eta=sqrt(0.894), separate charge/discharge power limits, 20% reserve,
and full initial and terminal SOC. Recharge is subject to the same group cap.
Home grid draw cannot go below zero; shared storage can serve the aggregate.
The no-export sensitivity is explicit in the model API.

Tests also cover reserve infeasibility, limited power, a battery at an empty
home unable to serve a neighbor, an export-enabled comparison, a 23:00 discharge
recharged after midnight with analytically calculated losses, integer equipment
and site fees, and full SOC at both sides of a missing-data gap.
Every returned dispatch independently checks energy balance, SOC, power,
terminal energy, grid cap and no-export bounds.

Home designs permit zero, one or two 10.08 kWh / 3.84 kW modules per home.
Two modules reproduce the organizer's 20.16 kWh / 7.68 kW continuous setup.
Assumed cost is $8,500/module plus $3,000/installed site.
Shared designs use **assumed** 5 kWh energy and 2.5 kW power increments and
$15,000 fixed plus $650/kWh. Power has a small tie-breaking objective because
the supplied cost formula does not price power separately. These are scenario
prices, not verified quotes or bill savings.

This checkpoint uses unshifted measured load for both storage alternatives.
It does not claim a managed-charging scenario or calibrated appliance detection.
Perfect foresight is a historical feasibility calculation, not an operating forecast.
Only common complete summer hours are used. At a gap, the preceding segment
must end full and the following segment starts full; no energy is transferred
across the gap, and no load is imputed. Results do not establish feasibility
during missing hours. Solver status and optimality gap are retained.

## Earlier random-group replay

The chunked import read 298,032,553 rows, excluded 8,758 incomplete/invalid
rows, and found zero duplicate slots. There are 33,674 customers meeting 95%
coverage and 30,557 meeting 99.5%.

The explicit sampling rule is one call to
`default_rng(20261112).choice(ascending_qualified_ids, size=(24,30), replace=False)`;
group 3 is row index 2, preserving draw order for display numbers. This gives
81.567 kW on August 6 at 17:00 and summer diversity 2.021050, **not** the brief's
80.15 kW peak and July 3 sizing event. Repeated draws from a shrinking pool,
independent draws, and permutation-based sampling were also checked and did
not recover the stated peak. The later explicit-ID replay below resolves the
mismatch without changing preprocessing. Nothing was chosen to force the
expected numbers in this earlier random draw.

| Target | Cap kW | Shared kW / kWh / sites | Shared assumed cost | Home kW / kWh / sites | Home assumed cost |
|---|---:|---|---:|---|---:|
| 10% | 73.410300 | 10 / 25 / 1 | $31,250 | 11.52 / 30.24 / 2 | $31,500 |
| 15% | 69.331950 | 12.5 / 35 / 1 | $37,750 | 15.36 / 40.32 / 3 | $43,000 |

These are feasible on the 2,160 common complete summer hours, out of 2,208.
The missing summer hours occur June 3 and August 12-13. July 3 is fully observed:
its peak is 70.368 kW, with zero required discharge at 10% and a minimum
1.036049 kWh at 15%. Recharge windows and simulated SOC are in the local CSVs.
Both shared MILPs reached optimal status. Independent integer power/no-export
bounds certify the reported home equipment costs: 10% requires at least three modules and two sites;
15% requires four modules and three sites. Every possible one- and two-site
placement was checked at maximum power against every deficient hour. These
valid bounds support a short placement enumeration followed by full-horizon
linear dispatch. A feasible design at the necessary cost bound certifies
minimum equipment cost without a large mixed-integer search. If that procedure
does not find a bound-attaining design, a full MILP is used with a 300-second
limit; its status and gap must then be reviewed. Fresh statuses are recorded
on every run; equally priced home placements can differ.

The 10% home cost matches the brief; the shared costs and the 15% fleet do not.
On this sampled group, the brief's 12.5 kW / 55 kWh shared design is feasible at
15%, while its specified home placements (display 6, 11 and 19) are infeasible.
This is not evidence against their feasibility on the unrecovered prior group.
The prior 50% flexible-load and held-out weather results were not reproduced
in this checkpoint.

## Original-group replay with local ID override

The supplied original membership is stored only in ignored
`data/config/original_showcase.json`, in the exact requested display order.
`--ids-config` bypasses random sampling. It validates 30 distinct integer IDs
against the same 99.5% annual screen and checks measured inputs before sizing.
The expected peak/hour, complete hours, and diversity all pass:

- Peak: 80.153000325 kW, July 3, 2026, 14:00-15:00 local meter time.
- Common complete summer hours: 2,184 / 2,208.
- Diversity on those hours: 2.0227439925.

No preprocessing change was necessary. The prior discrepancy was membership.
The original-group replay is separate from the earlier random-group artifacts:
all new results are under ignored `data/processed/original_showcase/`.

| Target | Cap kW | Shared kW / kWh / sites | Shared assumed cost | Home kW / kWh / sites | Home assumed cost |
|---|---:|---|---:|---|---:|
| 10% | 72.137700 | 10 / 30 / 1 | $34,500 | 11.52 / 30.24 / 2 | $31,500 |
| 15% | 68.130050 | 12.5 / 55 / 1 | $50,750 | 23.04 / 60.48 / 3 | $60,000 |

The cheaper option changes from homes at 10% ($3,000 less) to shared at 15%
($9,250 less). These reproduce the brief's sizes/costs. This tests two endpoints;
it does not locate the crossover between them. All four designs have zero cap
misses above a 0.000001 kW numerical tolerance on complete observed periods.
They make no claim for the 24 missing hours or held-out weather performance.

The 15% home fleet has six modules, with two per site. Placements can differ at
the same minimum cost. The prior display homes 6, 11, and 19 were independently
replayed and are feasible on this original group, unlike on the earlier random
group. Home sizing now strengthens necessary counts with an aggregate energy
relaxation before enumerating placements: a high-power shared store containing
five home modules (50.4 kWh) is infeasible at the 15% cap, so every feasible
home fleet needs at least six modules and three sites. A feasible fleet at that
cost certifies the minimum. This bound retains the same reserve, efficiency,
cap, complete-hour segments, and recharge constraints. A new hand-computable
case tests the energy-based module count.

Exact rerun from the repository root:

```powershell
.\.venv\Scripts\python.exe src/checkpoint.py --ids-config data/config/original_showcase.json
```

The command runs hand checks and the full input audit before sizing. A deliberately
incorrect expected peak was also tested and correctly blocked storage sizing.

## Still missing from the full submission

Appliance feature extraction and held-out label validation; classification-to-offer
table; managed charging and thermostat scenarios; a target/cost crossover sweep;
incremental annual cost sensitivity; solar sensitivity; held-out weather stress
test; and the final PowerPoint. The two target prices alone do not establish a
crossover. No upgrade-deferral or bill-saving value is verified.
