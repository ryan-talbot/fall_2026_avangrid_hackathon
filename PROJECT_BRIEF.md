# ClearGrid - One Battery, Thirty Homes

## The decision

Given a neighborhood's hourly loads and a required peak reduction, determine
the lowest-cost feasible option: managed charging alone, managed charging plus
coordinated home batteries, or managed charging plus one shared battery.
Explain the result using installed kW, kWh, and number of sites.

The physical shared battery is the centerpiece. Each household keeps its own
meter and bill. Eligible local solar producers could receive separate export
payments. Solar sourcing is a sensitivity. Grid charging is the base case.

## Inputs and constraints

- AMI covers September 2025 through August 2026. Inspect the actual CSV headers.
- Join weather to the start of the meter hour: hour_ending 1 starts at midnight.
  Document the treatment of the duplicated fall DST weather timestamp.
- Exclude incomplete intervals. Use at least 95% coverage for the population
  screen. Document any stricter coverage cutoff used for the showcase.
- The workbook has 200 likely EV IDs, 100 likely heat-pump IDs, and 434 known
  PV IDs. EV and heat-pump references are partial. Unlisted means unknown.
  PV status provides no generation, export, or battery measurements.
- No feeder or transformer mapping is supplied. Neighborhoods are synthetic
  groups built from real household load profiles.
- Use the organizer's two-unit home battery specification: 20.16 kWh,
  7.68 kW continuous, and 89.4% round-trip efficiency. Use a 20% reserve in
  the base replay and state how efficiency is split between charge and discharge.
- The approximate 3 kVA figure is a review trigger for additional residential
  service load. Keep it separate from neighborhood sizing. Upgrade costs and
  avoided infrastructure value require separate evidence.

## Pipeline

1. Ingest and qualify the AMI and weather. Record counts and missing data.
2. Screen for appliance signatures. Use recurring step-and-plateau patterns for
   EV charging, cold/hot weather response for heating/cooling, and the known PV
   list. Address the appliance types in the prompt and mark unresolved cases
   uncertain. Validate against reference IDs withheld from any threshold tuning.
3. Route customers to offers. EV-like load that overlaps peak hours supports
   managed-charging screening. Weather-sensitive peak contribution supports
   thermostat screening. Sustained demand after flexibility supports home battery
   screening. Known PV supports an optional export eligibility check.
4. Group customers and calculate diversity using the same time window for
   every home: sum of individual peaks divided by the coincident group peak.
   Use diversity to describe the load shape. Use dispatch to establish sizing.
5. At each cap, compare observed load, flexibility alone, flexibility plus an
   optimized home fleet, and flexibility plus shared storage. Hold the shifted
   load, cap, reserve, and efficiency equal across the battery options. Track
   state of charge, charge/discharge limits, home no-export bounds, and overnight
   recharge. Report cap misses and solver status. Include export as a sensitivity.
6. Sweep targets from 7.5% to at least 15%. Compare only feasible options and
   show the tested interval where the cheaper option changes. Explain the result
   using equipment and site counts.
7. Annualize the cost difference. Show the maximum shared-system price at
   different incremental annual costs. If time permits, test low/medium/high
   assumed solar surplus with grid top-up and the same cap. Account for exports'
   existing value and avoid double-counting energy savings.
8. Generate the July 3 load/dispatch chart, the cost crossover chart, and the
   customer-to-offer table from the simulation outputs. Include the after-midnight
   recharge window and a held-out weather stress test.

## Prior results to reproduce

These are checkpoints from an earlier historical replay, not values to hardcode.
The 30-home showcase was group 3 of 24 groups of 30, sampled without replacement
using NumPy default_rng(20261112) from ascending customer IDs with at least
99.5% of 8,760 hourly slots present. The population screen used 95% instead.

- Showcase summer peak: 80.15 kW. July 3 set the 15% case's energy requirement.
- 10% target: cap 72.14 kW, shared $34,500, coordinated homes $31,500.
- 15% target: cap 68.13 kW, shared 12.5 kW / 55 kWh at one site for $50,750.
  Home fleet: six units across three sites, 23.04 kW / 60.48 kWh for $60,000.
  The prior selected homes were display numbers 6, 11, and 19, two units each.
- Illustrative costs: home $8,500 per unit plus $3,000 per installation site.
  Shared $15,000 fixed plus $650/kWh at modeled power. These are scenario inputs.
- At the same 15% cap, the 50% flexible-load scenario moved 26.75 kWh over seven
  days. It shifted no energy on July 3, so both storage sizes stayed the same.
- Both smaller designs missed the summer cap when July 1-4 was withheld from
  equipment sizing. Report historical feasibility and held-out performance separately.
- These analyses used assumed prices and synthetic neighborhoods. They provide
  no verified bill savings or actual upgrade-deferral value.

## Submission

The PowerPoint must stand on its own. It needs appliance evidence, actionable
customer segments, specific home battery candidates and sizing, the shared
battery comparison, and a practical pilot recommendation. Submit the runnable
code or analytical tool with README instructions and dependencies. Follow the
organizer's SharePoint naming and submission instructions.
