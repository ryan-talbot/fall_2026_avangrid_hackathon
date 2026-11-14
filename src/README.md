# Code map

Run commands from the repository root. See `docs/RUNBOOK.md` for the full sequence.

| Purpose | Files |
|---|---|
| Final acceptance and packaging | `finalize.py`, `verify_submission.py`, `package_submission.py`, `clean_acceptance.py` |
| Aggregate GitHub documentation | `publish_deck_evidence.py` — explicit allowlist, no customer exports |
| Input audit and chunked cache | `inventory.py`, `load_data.py` |
| Historical showcase and baseline | `checkpoint.py`, `showcase.py`, `baseline.py` |
| Constrained sizing and dispatch | `model.py` |
| Frozen screening and offers | `screening.py`, `milestone.py`, `managed_charging.py` |
| Causal validation | `causal_dispatch.py`, `final_validation.py`, `replay_historical_equipment.py` |
| Supplemental decisions | `business_stress.py`, `final_analysis.py`, `decision_refinement.py`, `outreach_evidence.py` |
| Figures | `deck_figures.py`, `submission_figures.py`, `business_figures.py`, `rubric_review.py` |
| Checkpoint reports | `report.py` |
| Hand verification | `test_*.py` — diversity, reserve, losses, no-export, recharge, deadlines, bounds and interval certificates |

Historical sizing uses perfect foresight. Causal replay uses current hourly-average
load and carried SOC. Those scopes must remain labeled. Customer outputs stay in data/.
