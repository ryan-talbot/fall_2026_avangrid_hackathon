# ClearGrid — Avangrid hackathon

ClearGrid turns hourly meter and weather evidence into customer outreach
recommendations and compares managed charging, home batteries and shared
storage at a common peak-demand cap.

**Making the PowerPoint? Start with [the AI/teammate handoff](deck/AI_HANDOFF.md).**
The [final presentation handoff](deck/FINAL_PRESENTATION_HANDOFF.md) identifies
the latest deck package, final reading sequence and submission naming format.
GitHub includes aggregate PNG/SVG charts, chart data, 65 source-linked claims,
methods, assumptions and a slide outline. Raw organizer data, meter IDs and
household profiles stay local.

## Find what you need

| Task | Start here |
|---|---|
| Build slides or give another AI the project | [AI handoff](deck/AI_HANDOFF.md) — copyable prompt and reading order |
| Browse visuals and captions | [Figure catalog](deck/README.md) |
| Read the latest results | [Aggregate results](deck/evidence/results.json), [decision evidence](docs/DECISION_EVIDENCE.md) |
| Check an exact slide claim | [65-claim register](deck/evidence/claims.json), [chart CSVs](deck/evidence/) |
| Understand the rubric and limitations | [Rubric crosswalk](docs/RUBRIC_ALIGNMENT.md) |
| Install, obtain inputs or rerun from scratch | [Complete runbook](docs/RUNBOOK.md) |
| Review the original scope | [PROJECT_BRIEF.md](PROJECT_BRIEF.md) — prior results are historical checkpoints |
| Inspect algorithms | [Code map](src/README.md), [source](src/) |

## Supported headline results

- Verified synthetic 30-home group: **80.153 kW** July 3 peak,
  **2,184 / 2,208** common summer hours, diversity **2.022744**.
- At 15% reduction: shared **12.5 kW / 55 kWh, $50,750** versus homes
  **23.04 kW / 60.48 kWh, $60,000**. Prices are assumptions.
- Forty historical target queries certify 80 minimum-cost option results.
  Equipment steps create five transition regions, each narrower than
  **0.01 percentage point**; this is not one smooth crossover.
- Six additional groups: original time-boxed run five shared wins and one
  unresolved; separate refinement certifies the last as a **$34,500 tie**.
  Two wins use home lower bounds, not solved home costs.
- Original held-out recovery: **EV 17/90 at top 1,000; heating proxy 4/43 at
  top 500**. Unlisted status is unknown. These are not precision scores.
- Smaller excluded-date designs fail July 1–4 replay. Larger designs pass
  after sizing on the full historical record, including those dates.

Measured inputs, estimated appliance evidence, simulated operation and assumed
costs remain distinct. No verified bill savings, complete appliance ownership
inventory, actual feeder grouping or field guarantee is established.

## Run the code

Use 64-bit Python 3.12. From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m unittest discover -s src -p "test_*.py" -v
```

The 31 hand checks run without organizer inputs. Follow the [local data setup
and stage commands](docs/RUNBOOK.md) to reproduce the analysis. Once the verified
checkpoint outputs exist:

```powershell
.\.venv\Scripts\python.exe src/finalize.py
```

This audits inputs, checks frozen results, generates supplemental evidence,
prepares the aggregate `deck/` export and creates local submission ZIPs.
`--reuse-input-audit` skips repeat CRC/workbook reads while still checking all
recorded raw/cache hashes. Separate isolated-environment acceptance passed;
instructions are in the runbook.

## Layout

```text
deck/          Aggregate slide figures, chart data and AI handoff
docs/          Runbook, methods, rubric mapping and detailed evidence
src/           Analysis, figure generators, verification and hand checks
config/        Frozen rules, analysis plans and empty private-ID templates
data/          Authorized local inputs/results — ignored except .gitkeep
```

`requirements-lock.txt` pins all tested analysis dependencies;
`requirements-analysis.txt` pins direct dependencies. `requirements.txt`
retains the optional notebook tools.

## Restricted local additions

Organizer inputs, cohort IDs, customer CSVs, household profile images and
per-site audits are excluded from GitHub. Authorized teammates can use the
ignored `data/processed/submission_package/ClearGrid_deck_evidence.zip` for
household examples and detailed placement figures through the approved
hackathon workspace. Keep restricted material in approved local tooling;
do not upload it to another AI or external service.

The aggregate GitHub handoff supports the main deck. Restricted examples
require authorized local access. The slide team assembles the PowerPoint and
checks its numbers and scope labels against the claim register.
