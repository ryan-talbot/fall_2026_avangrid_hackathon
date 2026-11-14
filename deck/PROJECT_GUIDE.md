# Project guide

PeakShare connects customer program decisions with battery planning. ClearGrid
is the reproducible analysis implementation.

## The shared-battery decision

The verified group reaches 80.153 kW on July 3. A 15% reduction sets a demand
limit of 68.130 kW. The model finds equipment that can maintain that limit over
all complete summer hours, including charging periods.

One shared battery needs 12.5 kW and 55 kWh at an assumed $50,750. The home
alternative needs six modules across three sites at $60,000. A home battery
can discharge only into its own home's load under the study's no-export rule.
Shared storage can offset the combined group demand. Both options retain a
20% energy reserve and use 89.4% round-trip efficiency.

Here, kW measures the rate of electricity use or delivery. kWh measures the
amount of energy stored or consumed. A battery must have enough of both.

## Customer programs

| Program | Candidates | Evidence and action |
|---|---:|---|
| Managed vehicle charging | 17,493 | Recurring charging-like evening loads support a call to confirm the vehicle and charging schedule. |
| Thermostat outreach | 7,593 | Heating or cooling weather response supports a review of equipment and controls. |
| Home battery assessment | 5,766 | Sustained remaining evening demand supports a site-specific battery assessment. |
| Solar export check | 393 | Known solar membership supports a check of surplus energy, metering and permissions. |

The denominator is 33,674 qualified meters. Customers may appear in multiple
program lists. Counts describe review candidates. Equipment ownership and
enrollment require confirmation.

## How the model works

1. Keep complete hourly meter records and align them with weather.
2. Apply fixed rules for repeated charging patterns and temperature response.
3. Evaluate those rules against references withheld from rule development.
4. Assign customer review routes and estimate flexible charging opportunities.
5. Compare home and shared batteries using the same loads and demand target.
6. Check operating limits, overnight recharge, additional groups and prices.

The historical equipment model uses the full observed load record. A separate
controller test uses only current demand and stored charge. The
[results](../docs/DECISION_EVIDENCE.md) explain their different testing scopes.

## Public evidence

The [figure catalog](README.md) links charts and aggregate data. The
[runbook](../docs/RUNBOOK.md) explains how authorized users reproduce them.
The [challenge crosswalk](../docs/RUBRIC_ALIGNMENT.md) connects the evidence
to utility relevance, modeling, communication and innovation.
