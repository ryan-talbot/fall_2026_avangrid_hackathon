# PowerPoint assets and evidence

Start with [PROJECT_GUIDE.md](PROJECT_GUIDE.md). PNGs are 300 dpi; SVGs are editable
vectors. Each stem below has both extensions in [figures/](figures/).

| Figure stem | Supported takeaway / caption |
|---|---|
| [cleargrid_customer_segments](figures/cleargrid_customer_segments.png) ([SVG](figures/cleargrid_customer_segments.svg)) | Four overlapping outreach routes over 33,674 qualified meters; screens are not confirmed ownership or enrollments. |
| [cleargrid_outreach_priorities](figures/cleargrid_outreach_priorities.png) ([SVG](figures/cleargrid_outreach_priorities.svg)) | Rank assumed review queues, then confirm customer/device/site requirements. Median kW describes profiles, not delivered relief. |
| [cleargrid_appliance_appendix](figures/cleargrid_appliance_appendix.png) ([SVG](figures/cleargrid_appliance_appendix.svg)) | Hourly net AMI supports some signals while several appliance types remain uncertain. Unlisted is unknown. |
| [cleargrid_rubric_workflow](figures/cleargrid_rubric_workflow.png) ([SVG](figures/cleargrid_rubric_workflow.svg)) | Qualify, screen, compare at the same cap/hours, then validate. Keep measured/estimated/simulated/assumed labels. |
| [cleargrid_historical_july3](figures/cleargrid_historical_july3.png) ([SVG](figures/cleargrid_historical_july3.svg)) | July 3 drives historical sizing. Perfect-foresight dispatch includes after-midnight recharge; not held-out sizing validation. |
| [cleargrid_installed_costs_10_vs_15](figures/cleargrid_installed_costs_10_vs_15.png) ([SVG](figures/cleargrid_installed_costs_10_vs_15.svg)) | Preserved original two-target comparison. Use refinement for intermediate behavior. |
| [cleargrid_decision_refinement](figures/cleargrid_decision_refinement.png) ([SVG](figures/cleargrid_decision_refinement.svg)) | Forty target queries certify 80 costs. Repeated transitions are bracketed to <0.01 percentage point; group 6 ties after separate refinement. |
| [cleargrid_shared_cost_sensitivity](figures/cleargrid_shared_cost_sensitivity.png) ([SVG](figures/cleargrid_shared_cost_sensitivity.svg)) | Another $9,250 shared installed cost removes its 15% advantage, all else equal. No bill savings claimed. |
| [cleargrid_final_cost_sensitivity](figures/cleargrid_final_cost_sensitivity.png) ([SVG](figures/cleargrid_final_cost_sensitivity.svg)) | Four-point snapshot plus assumed annualized economics; refinement supplies latest crossover resolution. |
| [cleargrid_heatwave_sizing_scope](figures/cleargrid_heatwave_sizing_scope.png) ([SVG](figures/cleargrid_heatwave_sizing_scope.svg)) | Smaller excluded-date designs fail; larger full-record-sized designs pass after sizing used those dates. |
| [cleargrid_withheld_july1_4](figures/cleargrid_withheld_july1_4.png) ([SVG](figures/cleargrid_withheld_july1_4.svg)) | Failure evidence from the strict excluded-date sizing test. |
| [cleargrid_final_evidence_limits](figures/cleargrid_final_evidence_limits.png) ([SVG](figures/cleargrid_final_evidence_limits.svg)) | EV recovery exceeds two simple ranks; heating ties the slope baseline. Site outages can cause cap misses. |
| [cleargrid_six_group_business_stress](figures/cleargrid_six_group_business_stress.png) ([SVG](figures/cleargrid_six_group_business_stress.svg)) | Original time-boxed experiment: five wins/one unresolved. Pair with the separately labeled refinement, which resolves the last as a tie. |
| [cleargrid_rubric_impact](figures/cleargrid_rubric_impact.png) ([SVG](figures/cleargrid_rubric_impact.svg)) | Original impact scorecard; pair original-window counts with the latest refinement. |
| [cleargrid_rubric_pilot](figures/cleargrid_rubric_pilot.png) ([SVG](figures/cleargrid_rubric_pilot.svg)) | Proposed pilot: confirm leads, engineer sites, shadow-test, then decide whether to expand. Not an executed pilot. |

## Machine-readable evidence

- [results.json](evidence/results.json): aggregate results, diagnostics, assumptions,
  certified intervals and limitations.
- [claims.json](evidence/claims.json): 65 claims. `source` records local provenance
  files that may intentionally be excluded from GitHub.
- [target_costs.csv](evidence/target_costs.csv): all 80 costs, sizes, sites, caps,
  solver statuses and cost bounds.
- [july3_historical_aggregate.csv](evidence/july3_historical_aggregate.csv): aggregate
  group load, grid draw, charging/discharging and SOC.
- [heatwave_comparison.csv](evidence/heatwave_comparison.csv): four designs and scope.
- [six_group_comparison.csv](evidence/six_group_comparison.csv): original and refined
  decisions, retaining unknown home upper costs.
- [annualized_cost_sensitivity.csv](evidence/annualized_cost_sensitivity.csv).
- [offer_combinations.csv](evidence/offer_combinations.csv).
- [manifest.json](manifest.json): local source and exported-file hashes.

The export comes from `src/publish_deck_evidence.py`; do not edit it manually.
Only aggregate/method figures are published. Household examples and detailed
placement evidence remain in the authorized local deck ZIP.
