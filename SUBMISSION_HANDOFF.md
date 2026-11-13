# ClearGrid slide teammate handoff

All paths below are relative to the repository root. Every listed SVG has a
same-named 300 dpi PNG beside it. Generated evidence stays in ignored `data/`;
insert the local images into the hackathon PowerPoint rather than adding meter
data or profile outputs to Git. The PowerPoint itself still needs assembly.

## Ready-to-use visuals, takeaways, and captions

| Visual and exact SVG path | One supported takeaway | Suggested on-slide caption |
|---|---|---|
| `data/processed/submission_package/figures/cleargrid_customer_segments.svg` | Four evidence-based outreach routes were evaluated over the qualifying population. | **33,674 meters, >=95% annual coverage:** 17,493 managed-charging candidates; 7,593 thermostat candidates; 5,766 BTM assessment candidates; 393 solar export checks. Offers overlap; these are not ownership or enrollment counts. |
| `data/processed/submission_package/figures/cleargrid_outreach_examples.svg` | Meter shapes and weather associations support a confirmation conversation. | Anonymized showcase home 19 illustrates a detected EV-like plateau; home 8 has higher cold-weekday load. These are illustrative profiles, not confirmed appliances or a new accuracy test. |
| `data/processed/submission_package/figures/cleargrid_appliance_appendix.svg` | Requested appliance categories are explicitly covered or marked unresolved. | Broad EV/thermal evidence and known-PV membership are available. L1/L2, heat pump vs resistance, water heaters, pools, hot tubs and battery ownership remain unresolved. Unlisted status is unknown. |
| `data/processed/submission_package/figures/cleargrid_btm_placements_15pct.svg` | The reproduced optimizer found a concrete minimum-cost fleet. | Two modules each at display homes **3, 4, 6**: 23.04 kW / 60.48 kWh, three sites, assumed $60,000. Selection uses hourly load and constrained cost minimization, not EV/HVAC labels. A shared 12.5 kW / 55 kWh system costs $50,750. |
| `data/processed/submission_package/figures/cleargrid_original_btm_placements_15pct.svg` | Original placements also satisfy the model at the same fleet size/cost. | Fixed original homes **6, 11, 19**, two modules each, verified in historical dispatch. Local no-export ceilings limit discharge below nominal inverter kW. Placements are not unique; this is the fleet used in the full-record causal replay. |
| `data/processed/final_validation/figures/cleargrid_historical_july3.svg` | Historical full-summer sizing meets the cap with modeled storage and recharge. | **Perfect-foresight sizing and dispatch:** 80.153 kW measured group peak, 68.13005 kW cap, 20% reserve and 89.4% round-trip efficiency. Overnight hours are shaded; SOC carries across midnight. This is historical feasibility, not withheld sizing validation. |
| `data/processed/final_validation/figures/cleargrid_installed_costs_10_vs_15.svg` | The lower-cost option changes between the two tested targets. | At 10%, homes $31,500 versus shared $34,500. At 15%, shared $50,750 versus homes $60,000. **Two tested targets**, not a measured crossover curve; prices are assumptions. |
| `data/processed/submission_package/figures/cleargrid_heatwave_sizing_scope.svg` | Sizing scope changes the heat-wave result. | Both smaller designs missed the cap after July 1-4 was excluded from sizing: shared 19 hours / 12.023 kW worst, homes 16 hours / 10.947 kW. Both larger designs passed the same causal replay **after sizing with the full historical record**. |
| `data/processed/submission_package/figures/cleargrid_six_group_business_stress.svg` | Five additional comparisons certify a shared-cost advantage; one remains unresolved. | Six preregistered synthetic groups at their own 15% caps: **5 shared wins, 0 home wins, 0 ties, 1 unresolved**. Three pairs solved fully; two further wins use necessary home-cost bounds. Every attempt and solver status is included. |
| `data/processed/submission_package/figures/cleargrid_shared_cost_sensitivity.svg` | The showcase advantage is conditional on installed price. | At the 15% target, **+$9,250** shared installed cost raises $50,750 to the $60,000 home cost, all else equal. Interconnection, program and ongoing costs are unpriced; no bill saving or upgrade-deferral value is verified. |

Optional trace figures already preserved:

- `data/processed/final_validation/figures/cleargrid_withheld_july1_4.svg`:
  smaller-equipment causal traces, reserve depletion, and overnight recharge.
  July 5 00:00-06:00 is a recharge audit outside the 96 scored hours.
- `data/processed/milestone_screening/managed_dispatch_july3.png`:
  historical 50%-of-estimated-EV-flexibility scenario. It moved 19.279 kWh on
  nine summer dates, none on July 3; battery sizes stayed unchanged. This does
  not reproduce the earlier brief's 26.75 kWh / seven-day movement amount.

Use the original-placement table when discussing the four-design causal
replay, because its larger home fleet uses 6, 11, 19. Use the optimizer table
when explaining the reproduced selection algorithm. Do not mix the site lists
without the non-unique-placement note. Both fleets are feasible at the same
minimum equipment cost, but only the original fleet is the larger home case
in that four-design replay.

## Claims to keep visible in the PowerPoint

- **Held-out reference recovery:** EV **17 of 90 in the top 1,000** (18.9%);
  heating proxy **4 of 43 in the top 500** (9.3%). The remaining held-out labels
  excluded by coverage are not in those denominators. These are partial likely
  reference lists, not physically confirmed ownership labels. No cooling list
  exists. No precision, specificity or calibrated ownership probability is
  established. Rules were frozen before testing; unlisted means unknown.
- The 5,766 population battery flags are a **residual evening profile screen**,
  not 5,766 optimized or profitable battery installations. Population residual
  demand uses a 50% estimated EV allowance; the 30-home table also has actual
  simulated residual demand and selected modules.
- The July 3 group needs **12.023 kW** reduction at the peak, but equipment must
  cover the entire cap-exceedance event, reserve, efficiency, power, local
  no-export bounds and recharge. Diversity describes shape; it does not size
  the battery. The 23.04 kW installed home inverter total cannot all serve
  neighbors because each home can only offset its own meter load.
- **Historical versus withheld:** full-summer sizing is perfect foresight.
  The strict holdout excludes July 1-4 from sizing, freezes equipment, starts
  both at 100% charge and carries SOC continuously under a current-load/SOC-only
  rule. All 96 test hours are complete; both smaller designs fail despite full
  recharge by 06:00. Larger full-record designs passing those dates is not
  independent sizing generalization. No controller was tuned to remove failures.
- Neighborhoods are synthetic groups of real profiles; no feeder/transformer
  map or verified upgrade-deferral value is supplied. The approximate 3 kVA
  service-load figure is a review trigger, not a neighborhood sizing cap.

## Six-group business result and limits

Before any solve, `config/business_stress_plan.json` fixed seed **2026111301**
and the rule: one `default_rng(seed).choice(ascending eligible IDs excluding
showcase, size=(6,30), replace=False)`, preserving order and drawing without
replacement across groups. Annual eligibility is >=99.5%; both options use the
same common complete summer hours and each group's own observed 15% cap.
The six attempts used about 410 seconds of solver-phase wall time, within the
one-hour limit. The hard worker limit is five minutes per group; home MIP limit
is 120 seconds. No group was omitted or replaced based on results.

| Group | Common hours | Shared cost, verified feasible | Home cost evidence | Outcome |
|---|---:|---:|---|---|
| G1 | 2,184 | $67,000 | >=$80,000 necessary bound; MIP time limit, no incumbent | Shared win by bound |
| G2 | 2,184 | $76,750 | >=$100,000 necessary bound; MIP time limit, no incumbent | Shared win by bound |
| G3 | 2,160 | $47,500 | $51,500 minimum cost | Shared win |
| G4 | 2,160 | $44,250 | $51,500 minimum cost | Shared win |
| G5 | 2,184 | $50,750 | $60,000 minimum cost | Shared win |
| G6 | 2,184 | $34,500 | >=$31,500 necessary bound; MIP time limit, no incumbent | **Unresolved** |

Necessary home bounds use a relaxed pooled store: if fewer modules cannot
meet the cap even with ample shared power, every home placement needs more
modules. Combine that count with minimum installation sites and the same
prices. A feasible shared price below this bound certifies a strict win even
when an exact home optimum is unavailable. The bound is not a selected fleet
or a claim that the home problem is infeasible. Raw solver status/gap/dual
bounds and all completed/partial results are retained in
`data/processed/business_stress/stress_comparison.csv` and `stress_results.json`.

Shared's lower assumed $/kWh and one installation site help with sustained
residual peaks requiring several home modules/sites. For example, G1 needs at
least eight home modules/four sites ($80,000) versus an 80 kWh shared design
($67,000). G2 needs at least ten modules/five sites ($100,000) versus a 95 kWh
shared design ($76,750). This does not show that shared always wins: fixed
shared costs can dominate small requirements (the showcase's 10% case favors
homes), and G6 remains unresolved. Six synthetic groups are not a representative
utility deployment sample.

In the 15% showcase the precise cost decomposition is shared **$35,750 variable
energy component + $15,000 fixed = $50,750**, versus homes **$51,000 modules +
$9,000 site fees = $60,000**. Thus $15,250 lower variable cost offsets a $6,000
higher shared fixed/site allowance, leaving $9,250 net advantage. Do not claim
one shared site automatically has a lower installation charge. At four to five
home sites, their $12,000-$15,000 site fees approach the shared fixed allowance;
at small home fleets the shared fixed allowance can dominate. These are modeled
price components, not vendor quotes or verified avoided infrastructure costs.

## Tested assumptions and unresolved work

Same storage assumptions: grid charging; 20% reserve; symmetric sqrt(0.894)
charge/discharge efficiencies; home modules 10.08 kWh / 3.84 kW, at most two
per site; no home export; shared sizing increments 5 kWh / 2.5 kW. Assumed
prices: home $8,500/module plus $3,000/site; shared $15,000 plus $650/kWh at
modeled power. Complete-hour segments retain the documented sizing endpoint
charge assumptions. Missing hours are not imputed.

Unresolved: G6's home optimum; exact G1/G2 home equipment choices and costs;
appliance subtypes, water heaters, pools, hot tubs and storage ownership;
control/enrollment costs and participation; actual solar surplus/export value;
tariffs and bill savings; shared interconnection/site/O&M costs; service
upgrades and avoided infrastructure value. No finer target sweep or annualized
business case was completed. The installed-price sensitivity covers the
$9,250 showcase headroom without inventing those missing values.

## Exact rerun commands

Local input/dependency setup is in README.md. The real 30 IDs belong only in
ignored `data/config/original_showcase.json`; tracked templates contain no IDs.

For this existing workspace, rebuild only the new slide assets and checks
without regenerating the preserved historical figures:

```powershell
.\.venv\Scripts\python.exe src/submission_figures.py
.\.venv\Scripts\python.exe src/business_stress.py --summarize
.\.venv\Scripts\python.exe src/business_figures.py
.\.venv\Scripts\python.exe src/verify_submission.py
.\.venv\Scripts\python.exe src/package_submission.py
```

To deliberately rerun the entire analysis from authorized local inputs:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-analysis.txt
.\.venv\Scripts\python.exe src/checkpoint.py --ids-config data/config/original_showcase.json
.\.venv\Scripts\python.exe src/milestone.py
.\.venv\Scripts\python.exe src/final_validation.py
.\.venv\Scripts\python.exe src/replay_historical_equipment.py
.\.venv\Scripts\python.exe src/submission_figures.py
.\.venv\Scripts\python.exe src/business_stress.py
.\.venv\Scripts\python.exe src/business_figures.py
.\.venv\Scripts\python.exe src/verify_submission.py
.\.venv\Scripts\python.exe src/package_submission.py
```

The full rerun intentionally regenerates stage outputs. The baseline snapshot
is preserved and verified, not refreshed. Time-limited MIP incumbents can vary;
use recorded cost bounds and unresolved status rather than forcing this run's
outcome. `--summarize` reuses sampled groups and adds bound checks; it does not
resample or rerun MIPs.

## Files and submission actions still outstanding

Local handoff archives (created by `package_submission.py`):

- `data/processed/submission_package/ClearGrid_code_submission.zip`: source,
  tested dependency pins, safe config templates and documentation only.
- `data/processed/submission_package/ClearGrid_deck_evidence.zip`: anonymized
  slide figures, preserved historical figures and this guide. It stays local
  and Git-ignored; no raw input, actual meter list, reference list or cache is
  included. Use only for this hackathon handoff.
- `data/processed/submission_package/verification_report.json` and
  `git_handoff_status.txt`: final checks and exact current Git status.

The analysis source and documentation are intended to be versioned in this
repository. Use `git status` and `git log` to check the current publishing state
and any changes generated after the submission handoff. The initial scaffolding
commit was `16266c1`. The safe source set is README/requirements and `src/*.py`,
`requirements-analysis.txt`, safe `config/*.json`, AGENTS.md, PROJECT_BRIEF.md,
CHECKPOINT.md, MILESTONE.md, FINAL_VALIDATION.md and this guide. Review first:

```powershell
git status --short --untracked-files=all
git add README.md requirements.txt requirements-analysis.txt AGENTS.md PROJECT_BRIEF.md CHECKPOINT.md MILESTONE.md FINAL_VALIDATION.md SUBMISSION_HANDOFF.md src/*.py config/*.json
git diff --cached --stat
git status --short
```

Do not force-add `data/`, inputs, meter mappings, customer CSVs, profile figures,
caches or local handoff ZIPs. Evidence-generation and verification scripts do
not commit, push or upload; repository publishing is a separate Git step.

The slide teammate still needs to assemble the **self-contained PowerPoint**,
include the assumptions/failure scopes on slides, replace the team-number
placeholder in `NN_ClearGrid_Final Submission.pptx`, and submit through the
organizer's SharePoint folder with the runnable code/GitHub link. The deck is
the scored deliverable; the final PPTX and its submission have not been created
or uploaded here.
