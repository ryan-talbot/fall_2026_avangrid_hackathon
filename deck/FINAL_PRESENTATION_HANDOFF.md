# Final presentation handoff

The presentation brand is PeakShare. ClearGrid is the analytical codebase.
The latest locally rendered deck is
`data/presentation_rebuild/output/PeakShare_Shared_Battery_Story.pptx`.
The matching PDF and `_Package.zip` share that filename stem. The package
includes Alata and its license. Install the font before editing.

These presentation files contain anonymized household profiles and household
load values. They remain in ignored local storage under the repository's
customer-level export rule. Share the package through the authorized team
folder and organizer submission channel. GitHub contains aggregate evidence,
figures and runnable analysis.

## Main presentation sequence

1. One shared battery for thirty homes.
2. The observed summer peak and 15% reduction target.
3. Shared and home equipment at the same target, including assumed costs.
4. Household discharge limits and the original three home placements.
5. Historical shared dispatch and recharge.
6. How customer evidence leads to program and storage decisions.
7. Four overlapping outreach routes across 33,674 qualified meters.
8. Household examples and held-out reference recovery.
9. Managed charging and the remaining battery requirement.
10. All six additional synthetic group comparisons.
11. Target-dependent costs and shared installed-price headroom.
12. Proposed Avangrid pilot with customer, engineering and operating gates.

Eleven appendix slides cover data preparation, reference benchmarks,
July 1–4 replay scopes, equations, the cost sweep, appliance confirmation
needs, annualized costs, screening rules, reproducibility, an illustrative
solar extension and the rubric evidence map. This sequence supersedes the
earlier suggested slide order in AI_HANDOFF.md.

The $9,250 advantage uses assumed installed prices and full-record historical
sizing. Both smaller designs miss the excluded-date replay. The larger designs
pass after sizing on the full record. Appliance reference recovery remains
17/90 EV references in the top 1,000 and 4/43 heating references in the top 500.
Unlisted equipment remains unknown. The duck curve is illustrative.

## Submission naming

The organizer kickoff specifies the PowerPoint filename pattern
`team number_team name_Final Submission`, with the example
`03_Solis_Final Submission.pptx`. Use the assigned team number and registered
team name. The supplied materials require a GitHub code submission with README
and dependencies, but specify no GitHub repository name. The existing
`ryan-talbot/fall_2026_hackathon` repository can be submitted as-is.

## Reproduce the accepted analysis

From the repository root, after completing local data setup and checkpoints
in `docs/RUNBOOK.md`, run in PowerShell

```powershell
.\.venv\Scripts\python.exe src/finalize.py --reuse-input-audit
```

This command verifies cached input hashes and regenerates accepted analysis
and aggregate evidence. The runbook provides full setup and fresh-input steps.
