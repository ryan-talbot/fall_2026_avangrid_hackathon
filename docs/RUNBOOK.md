# Complete analysis runbook

Run all commands from the repository root. The root README and `deck/PROJECT_GUIDE.md` are the short entry points.

# Avangrid Energy Innovation Hackathon

**Latest business/analytics evidence:** read [DECISION_EVIDENCE.md](DECISION_EVIDENCE.md).
The adaptive sweep now certifies 80 option costs at 40 targets, bounds five
preference-transition regions to <0.01 percentage point, and resolves group 6
as a separately labeled $34,500 tie. Ranked offer review queues and secondary
frozen-rule reference diagnostics are included.

**Final code/evidence documentation:** read [RESULTS.md](RESULTS.md).
After the checkpoints below exist, run `.\.venv\Scripts\python.exe src/finalize.py`
for the complete acceptance audit and local submission archives. The latest
supplement adds 7.5% and 12.5% targets, fixed-rule screening benchmarks,
annualized cost/export sensitivities and deterministic operating failures.
The original baseline and historical figures remain preserved.


## Local data setup (required; never committed)

Use 64-bit Python 3.12. Obtain the organizer inputs through the authorized
hackathon SharePoint folder and keep them on this machine. The code does not
download or send inputs to external services.

```powershell
New-Item -ItemType Directory -Force data/raw, data/materials, data/config | Out-Null
```

Put these six organizer files in `data/raw/`, keeping their supplied names:

- `2026 Avangrid Hackathon Data_1_10000.zip`
- `2026 Avangrid Hackathon Data_10001_20000_v2.zip`
- `2026 Avangrid Hackathon Data_20001_30000.zip`
- `2026 Avangrid Hackathon Data_30001_35725.zip`
- `EV_Heat Pump_Solar PV Customers.xlsx`
- `Weather Data_Avangrid_Hackathon .xlsx` (space before `.xlsx`)

Put the four organizer PDFs (challenge, rubric, kickoff, dictionary) in
`data/materials/`. The audit identifies them from their contents. To initialize
local configs without overwriting existing IDs:

```powershell
if (-not (Test-Path -LiteralPath data/config/original_showcase.json)) {
    Copy-Item -LiteralPath config/original_showcase.template.json -Destination data/config/original_showcase.json
}
if (-not (Test-Path -LiteralPath data/config/original_historical_fleet.json)) {
    Copy-Item -LiteralPath config/original_historical_fleet.template.json -Destination data/config/original_historical_fleet.json
}
```

Fill the empty `customer_numbers` array in **local**
`data/config/original_showcase.json` with the authorized 30 IDs in their exact
original order. Get that list from the team privately; no IDs are embedded in
the source or templates. All of `data/` except `.gitkeep` is Git-ignored. Never
force-add organizer data, meter lists, caches, household outputs or profile
figures. First ingestion uses a local memory-mapped cache; allow at least 2 GB
of extra disk space beyond the supplied ZIPs.

## Setup

From the repo root in Windows PowerShell with Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For the reproducible command-line documentation, the tested direct dependency
versions are pinned in `requirements-analysis.txt` (no notebook UI needed):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-analysis.txt
```

`requirements.txt` retains the original optional notebook/exploration packages.

To launch JupyterLab:

```powershell
.\.venv\Scripts\python.exe -m jupyterlab
```

- `data/` - Local datasets, ignored by Git.
- `docs/` - Methods, runbook and traceable checkpoint notes.
- `src/` - Python scripts as needed.
- `deck/` - Selected aggregate figure/evidence export and project guide.

## First implementation checkpoint

From the repository root, after installing requirements:

```powershell
.\.venv\Scripts\python.exe src/checkpoint.py
```

This runs hand-computable tests, reads both workbooks, CRC-checks all four ZIPs,
builds a chunked local AMI cache if needed, and solves the 10% and 15% storage
comparisons. First run reads about 298 million rows; subsequent runs reuse
`data/processed/ami.npy` and `counts.npy`. Keep at least 2 GB free for the cache
and use a 64-bit Python. Home sizing enumerates small placements at a proven
cost lower bound and verifies them with full-horizon linear dispatch. If no
bound-attaining design is found, a mixed-integer fallback has a 300-second
solver limit; inspect the recorded status and gap before claiming minimum cost.

Outputs stay local in ignored `data/processed/`: `inventory.json`,
`coverage.json`, `showcase_results.json`, aggregate hourly dispatch CSVs,
`checkpoint_summary.md`, `july3_dispatch.png`, and a local showcase ID array.
Do not commit that directory.
See [CHECKPOINT.md](CHECKPOINT.md) for methods, source inventory and limitations.

To run the small checks alone:

```powershell
.\.venv\Scripts\python.exe src/test_model.py
```

To replay with the existing local cache without repeating the archive audit:

```powershell
.\.venv\Scripts\python.exe src/showcase.py
```

To rerun the original 30 homes in their supplied display order:

```powershell
.\.venv\Scripts\python.exe src/checkpoint.py --ids-config data/config/original_showcase.json
```

The local JSON config contains `customer_numbers` (exactly 30 distinct integer
IDs, in display order) and `expected_inputs`. It is excluded by the existing
`data/` Git ignore rule; do not copy the IDs into tracked code. This option
bypasses the random sampler. It requires the existing 99.5% coverage screen
and checks the measured peak, peak hour, common complete hours, and diversity
before any storage sizing. A failed check stops the run. Peak tolerance is
0.00001 kW and diversity tolerance is 0.000001, allowing float32 cache rounding.

Explicit-ID outputs default to `data/processed/original_showcase/`, preserving
the earlier random-group outputs. `--output-dir` can select another local
directory. To check only the inputs, use:

```powershell
.\.venv\Scripts\python.exe src/showcase.py --ids-config data/config/original_showcase.json --check-inputs-only
```

If raw data change, remove the local generated cache files before rerunning;
the loader rejects changed ZIP sizes/timestamps after a cache build or final audit. A fresh ingestion is still required for changed inputs; the final audit also checks hashes. The code never downloads inputs.
Tested versions: Python 3.12, NumPy 2.5.4, pandas 3.1.1, SciPy 1.18.1,
openpyxl 3.1.5, matplotlib 3.11.2, pypdf 7.0.1.

## Screening, program offers, and managed charging

After the verified original showcase exists, run:

```powershell
.\.venv\Scripts\python.exe src/milestone.py
```

This preserves the unshifted results in local `data/processed/baseline_unshifted_v1/`
with a hash manifest. It screens the >=95%-coverage population using frozen,
label-blind rules; evaluates held-out reference-list recovery at fixed outreach
sizes; creates population and 30-home customer-to-offer tables; and simulates
50% of estimated eligible EV-like components being movable before 06:00.
It then resizes both battery alternatives on the exact same shifted load at
the original 15% cap. All inputs and customer outputs stay local and ignored.

Review `data/processed/milestone_screening/milestone_summary.md`,
`showcase_customer_to_offer.csv`, `showcase_offers.md`, `screening_summary.json`,
and `milestone_results.json`. Dispatch CSVs, job energy/deadline checks, rule
hashes, reference splits and figures are in that same directory.
See [MILESTONE.md](MILESTONE.md) for methods, frozen-rule validation,
assumptions, actual results and the difference from the prior shifted-kWh figure.

For just the new hand checks:

```powershell
.\.venv\Scripts\python.exe src/test_screening_managed.py
```

## Final validation and deck figures

After the verified showcase and screening milestone, run:

```powershell
.\.venv\Scripts\python.exe src/final_validation.py
```

This excludes July 1-4 from equipment sizing at the unchanged 68.13005 kW cap,
freezes equipment and home placements, and replays those 96 hours with a
current-load/SOC-only controller. SOC carries across midnight; a six-hour
July 5 extension checks final overnight recharge without adding scored hours.
The strict holdout uses measured unshifted AMI; screening rules remain frozen.

Results are in `data/processed/final_validation/validation_summary.md` and
`validation_results.json`. Three figures are exported as 300 dpi PNG and SVG
under `data/processed/final_validation/figures/`: historical July 3 dispatch,
10% versus 15% assumed installed costs, and a separate withheld-period causal
replay figure. Figure manifests, frozen equipment, chronological CSVs and
per-site audit arrays remain local and ignored.
See [FINAL_VALIDATION.md](FINAL_VALIDATION.md) for the controller rule,
training/test boundaries, recharge assumptions, actual failures and figure paths.

To compare those smaller designs with the larger historical 15% equipment
under the identical causal controller:

```powershell
.\.venv\Scripts\python.exe src/replay_historical_equipment.py
```

The larger home fleet uses the original display placements 6, 11 and 19, two
modules each, specified in ignored `data/config/original_historical_fleet.json`.
The larger cases are labeled **sized with the full historical record** because
their sizing used July 1-4. All four replay results are saved in local
`data/processed/four_design_replay/four_design_summary.md`, with CSV/JSON
comparisons and per-site audit arrays alongside it. Existing historical cost,
dispatch and validation figures are not regenerated; their hashes are checked.

## Final submission evidence package

After the checkpoints above, generate the segmentation/example/appliance and
BTM-placement visuals first:

```powershell
.\.venv\Scripts\python.exe src/submission_figures.py
```

The population counts use actual offer flags over 33,674 qualified meters.
Figures retain overlapping-offer and unknown-status notes and the frozen
held-out recovery results. The BTM table distinguishes optimizer homes 3, 4, 6
from the original homes 6, 11, 19; both have the same historical fleet cost.
All PNGs, SVGs and underlying example/placement evidence stay in ignored
`data/processed/submission_package/`.

Run the preregistered six-group business test, with a hard one-hour overall
limit and five-minute worker cap per group:

```powershell
.\.venv\Scripts\python.exe src/business_stress.py
```

It records seed 2026111301 and the exact disjoint sampling rule **before**
solves. No showcase IDs are reused. Each group has its own 15% cap, identical
common hours for both options, unshifted load and the same model/prices. Every
attempt, time limit, feasible incumbent and cost bound is retained. Strict
winners require certified interval separation; unknown comparisons are not
assigned to the cheaper incumbent. Summarizing an existing completed run only
(no new sampling or MIP solve):

```powershell
.\.venv\Scripts\python.exe src/business_stress.py --summarize
.\.venv\Scripts\python.exe src/business_figures.py
```

The summary also checks necessary home-module/site costs with the same
aggregate-energy relaxation used by the verified model. It retains any home
solver time limit/no-incumbent result. Showcase price sensitivity is generated
regardless of stress completeness: $9,250 extra shared installed cost removes
the modeled 15% cost advantage, all else equal. The original figures retain the 10% and 15% baseline targets. The final
supplement solves 7.5% and 12.5% as well; no exact crossover is claimed.

All relevant hand checks can be run together:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s src -p "test_*.py" -v
```

Verify the full evidence documentation and create local archives:

```powershell
.\.venv\Scripts\python.exe src/finalize.py
```

`verify_submission.py` reruns the hand checks, audits frozen source/figure
hashes, sampling/solver bounds, actual offer denominators, placement evidence,
heat-wave scope and Git exclusions. The code ZIP is allowlisted to source,
documentation and safe templates; it contains no `data/` inputs or outputs.
The separate local deck-asset ZIP contains the requested anonymized figures.
Both archives stay under ignored `data/processed/submission_package/`.

The criterion-by-criterion review and recommended 12-slide story are in
[RUBRIC_ALIGNMENT.md](RUBRIC_ALIGNMENT.md). The rubric review command reads
existing verified outputs and creates `cleargrid_rubric_impact`,
`cleargrid_rubric_workflow`, and `cleargrid_rubric_pilot` as SVG/PNG pairs in
`data/processed/submission_package/figures/`. These make quantified impact,
technical rigor, scalability limits and proposed utility actions visible.
The [submission guide](SUBMISSION.md) describes the completed presentation
and organizer naming requirements. Appliance classifications remain candidate
screens, with unknown status preserved.

PowerPoint and code or analytical tool are due via SharePoint on Friday,
November 13 at 5:00 PM ET.


## Final acceptance and latest supplemental evidence

`src/finalize.py` requires the completed verified showcase, screening, validation,
four-design replay and six-group stress outputs above. It preserves these and
runs the final supplementary analysis, 31 hand checks, dependency compatibility,
input audit, provenance/privacy checks and packaging. It writes a machine-readable
slide claim register and refuses to package changed accepted source/artifacts.
It does not upload anything or mutate Git. See `RESULTS.md` for the
current result tables, figure paths, captions, assumptions and unresolved criteria.

After an initial acceptance, this skips repeat CRC/workbook reads but still
checks recorded input/cache SHA256 hashes:

```powershell
.\.venv\Scripts\python.exe src/finalize.py --reuse-input-audit
```

Only the new supplementary analyses can be regenerated with:

```powershell
.\.venv\Scripts\python.exe src/final_analysis.py
```

Plan settings are in `config/final_review_plan.json`. Cached supplementary target
solves require matching plan/model/load signatures; changing those requires a
fresh supplemental output folder. Figures are SVG/300 dpi PNG pairs in
`data/processed/final_analysis/figures/`. Screening comparisons use already
examined held-out labels, without retuning; they are descriptive benchmarks,
not fresh validation or ownership precision. Annualized capital costs use
assumed equal 15-year horizons and explicit rates, not measured bill savings.


## Business and analytics refinements

The final acceptance command also runs these two cached, provenance-checked
extensions without changing original checkpoints or the one-hour experiment:

```powershell
.\.venv\Scripts\python.exe src/decision_refinement.py
.\.venv\Scripts\python.exe src/outreach_evidence.py
```

The former certifies cost preference throughout intervals using monotonic
optimal-cost endpoint bounds; endpoint agreement alone is insufficient. It
retains five narrow transition brackets at a declared 0.01 percentage point
resolution, rather than claiming an exact or unique crossover. Group 6 is a
certified tie after a separately labeled exhaustive-placement extension. The
original six-group report remains five shared wins and one unresolved; after
the extension the decisions are five shared wins and one tie.

The latter ranks assumed program-review queues, reconciles all 16 exclusive
combinations of overlapping offers, and separately reports original and
previously unused reference halves. No rule retuning, true-negative technology
labels, ownership precision, enrollment or delivered response is inferred.
Program-priority ranks differ from fixed-score classification evaluation ranks.
Customer queues remain local and ignored. See `DECISION_EVIDENCE.md` for
all numbers, captions, highest-weight criterion mapping and claim boundaries.


## Isolated-environment release verification

`requirements-lock.txt` pins the complete dependency graph, including transitive
packages, used for the separate Windows Python 3.12 environment. To reproduce:

```powershell
python -m venv data/processed/clean_environment/venv
.\data\processed\clean_environment\venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe src/clean_acceptance.py
```

`clean_acceptance.py` rejects system-site packages or lock mismatches, then runs
the complete final acceptance with the isolated interpreter. It reuses the
hash-audited inputs/checkpoints rather than re-ingesting all raw rows, and writes
`data/processed/submission_package/clean_environment_acceptance.json`. The
installation uses package repositories; organizer data never leave the machine.


GitHub documentation export is prepared by `src/publish_deck_evidence.py` during final acceptance. This is an explicit aggregate allowlist, separate from original ignored household outputs. See `deck/PROJECT_GUIDE.md` for an overview.
