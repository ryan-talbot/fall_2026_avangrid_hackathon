"""Export an explicit aggregate-only GitHub documentation; never copies customer data.

This script prepares files locally. Git commit/push is a separate user action.
Raw AMI, reference IDs, household profiles, per-site dispatch and customer
tables are deliberately absent. Existing historical images are copied exactly.
"""
import json
import shutil
import csv
from pathlib import Path
from inventory import ROOT
from baseline import digest,preserve

DEST=ROOT/'deck'

def read(path):return json.loads((ROOT/path).read_text())

def csv_write(name,rows):
    with (DEST/'evidence'/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    (DEST/'figures').mkdir(parents=True,exist_ok=True);(DEST/'evidence').mkdir(exist_ok=True)
    verification=read('data/processed/submission_package/verification_report.json')
    if not verification['passed']:raise ValueError('Verify the model evidence before export')
    folders={'historical':ROOT/'data/processed/final_validation/figures','submission':ROOT/'data/processed/submission_package/figures','final':ROOT/'data/processed/final_analysis/figures','refinement':ROOT/'data/processed/decision_refinement/figures','outreach':ROOT/'data/processed/outreach_evidence/figures'}
    allowlist={
        'historical':['cleargrid_historical_july3','cleargrid_installed_costs_10_vs_15','cleargrid_withheld_july1_4'],
        'submission':['cleargrid_customer_segments','cleargrid_appliance_appendix','cleargrid_shared_cost_sensitivity','cleargrid_heatwave_sizing_scope','cleargrid_six_group_business_stress','cleargrid_rubric_impact','cleargrid_rubric_workflow','cleargrid_rubric_pilot'],
        'final':['cleargrid_final_cost_sensitivity','cleargrid_final_evidence_limits'],
        'refinement':['cleargrid_decision_refinement'],
        'outreach':['cleargrid_outreach_priorities']}
    # Check these outputs against the existing provenance manifests BEFORE copy.
    manifests=['data/processed/final_validation/figure_manifest.json','data/processed/submission_package/submission_figure_manifest.json','data/processed/submission_package/business_figure_manifest.json','data/processed/submission_package/rubric_figure_manifest.json','data/processed/final_analysis/final_analysis_manifest.json','data/processed/decision_refinement/decision_refinement_manifest.json','data/processed/outreach_evidence/outreach_evidence_manifest.json']
    hashes={}
    for path in manifests:
        manifest=read(path)
        for key in ['figure_sha256','output_sha256']:
            for p,h in manifest.get(key,{}).items():hashes[(ROOT/p).resolve()]=h
    sources=[];outputs=[]
    for group,stems in allowlist.items():
        for stem in stems:
            for suffix in ['png','svg']:
                source=folders[group]/f'{stem}.{suffix}'
                if source.resolve() not in hashes or digest(source)!=hashes[source.resolve()]:raise ValueError('Unverified figure: '+stem)
                dest=DEST/'figures'/source.name;shutil.copyfile(source,dest);sources.append(source);outputs.append(dest)
    # Every field is selected below. Never serialize complete per-home model
    # records: their units/energy arrays reveal customer-level placements.
    baseline=preserve();base=json.loads((baseline/'showcase_results.json').read_text())
    final_path='data/processed/final_analysis/final_analysis_results.json';final=read(final_path)
    ref_path='data/processed/decision_refinement/decision_refinement_results.json';ref=read(ref_path)
    outreach_path='data/processed/outreach_evidence/outreach_evidence_results.json';outreach=read(outreach_path)
    milestone=read('data/processed/milestone_screening/milestone_results.json');replay=read('data/processed/four_design_replay/four_design_results.json');stress=read('data/processed/business_stress/stress_results.json')
    costs=[]
    for q in ref['showcase']['queries']:
        for name,v in q['options'].items():
            interval=v['installed_cost_interval']
            costs.append({'reduction_fraction':q['target'],'cap_kw':q['cap_kw'],'option':name,'assumed_installed_dollars':v.get('cost'),'total_power_kw':sum(v.get('power_kw',[])),'total_energy_kwh':sum(v.get('energy_kwh',[])),'sites':sum(v.get('sites',[])),'solver_status':v['status'],'cost_lower_bound':interval['lower'],'cost_upper_bound':interval['upper'],'certified_minimum_cost':interval['certified_minimum_cost'],'maximum_cap_miss_kw':v.get('max_cap_miss_kw'),'scope':'Unshifted historical perfect-foresight sizing; assumed installed prices'})
    heat=[]
    for key,v in replay['results'].items():
        d=v['design'];heat.append({'design':key,'sizing_scope':d['sizing_scope'],'kw':sum(d['power_kw']),'kwh':sum(d['energy_kwh']),'sites':sum(d['sites']),'assumed_installed_dollars':d['cost'],'hours_above_cap':v['hours_above_cap'],'worst_miss_kw':v['worst_miss_kw']})
    groups=[]
    for g in stress['groups']:
        row={'group':g['group'],'common_hours':g['common_complete_hours'],'observed_peak_kw':g['observed_common_peak_kw'],'cap_kw':g['cap_kw'],'original_time_boxed_outcome':g['outcome'],'post_refinement_outcome':ref['group6']['outcome'] if g['group']==6 else g['outcome']}
        for name in ['shared','home']:
            option=ref['group6'][name] if g['group']==6 else g['options'][name]
            row[name+'_cost_lower']=option['installed_cost_interval']['lower'];row[name+'_cost_upper']=option['installed_cost_interval']['upper']
        groups.append(row)
    transitions=[v for v in ref['showcase']['intervals'] if v['interval_outcome']=='transition_or_uncertified_bracket']
    summary={'scope':'Aggregate hackathon evidence for slide preparation. No raw inputs, actual meter IDs, household profiles or customer tables. Figures and tables are measured-derived, estimated, simulated or assumed as labeled.','showcase':{k:base[k] for k in ['summer_peak_kw','summer_peak_hour_start','summer_hours','summer_diversity','missing_summer_hours']},'historical_costs':costs,'crossover_intervals':ref['showcase']['intervals'],'transition_regions':transitions,'reference_diagnostics':outreach['reference_diagnostics'],'reference_benchmarks':final['screening_benchmarks'],'program_priorities':outreach['program_priorities'],'exclusive_offer_combinations':outreach['exclusive_offer_combinations'],'managed_charging':milestone['managed_charging'],'managed_only_cap_metrics':milestone['options']['managed_charging_alone'],'four_design_heatwave':heat,'annualized_cost_sensitivity':final['annualized_cost_sensitivity'],'six_group_comparisons':groups,'six_group_counts_after_separate_refinement':{'shared_win':5,'home_win':0,'tie':1,'unresolved':0},'validation':{'hand_tests_passed':verification['test_count'],'dependency_check':verification['dependency_check'],'frozen_baseline_and_historical_figures_preserved':True},'remaining_evidence_requirements':['Confirmed appliance ownership/subtypes and true negatives','Tariffs, complete installed/O&M/program cost quotes','Physical feeder/service/topology and shared metering/interconnection feasibility','PV surplus/export and storage telemetry','Prospective field performance and final PowerPoint review']}
    summary['operating_sensitivities']=final['operating_sensitivities']
    # Refuse accidental expansion to customer-level columns in future edits.
    payload=json.dumps(summary,indent=2)
    for forbidden in ['CUSTOMER_NUMBER','customer_numbers','home_index','start_slot']:
        if forbidden in payload:raise ValueError('Customer-level field in aggregate export: '+forbidden)
    (DEST/'evidence/results.json').write_text(payload,encoding='utf-8')
    claims_source=ROOT/'data/processed/submission_package/slide_claims.json'
    shutil.copyfile(claims_source,DEST/'evidence/claims.json')
    csv_write('target_costs.csv',costs);csv_write('heatwave_comparison.csv',heat);csv_write('six_group_comparison.csv',groups)
    for name,path in [('july3_historical_aggregate.csv','data/processed/final_validation/historical_july3_figure_data.csv'),('annualized_cost_sensitivity.csv','data/processed/final_analysis/annualized_cost_sensitivity.csv'),('offer_combinations.csv','data/processed/outreach_evidence/exclusive_offer_combinations.csv')]:
        source=ROOT/path
        header=source.read_text(encoding='utf-8').splitlines()[0].lower()
        if any(v in header for v in ['customer_number','home_index','display_home']):raise ValueError('Customer field in requested aggregate CSV')
        shutil.copyfile(source,DEST/'evidence'/name);sources.append(source)
    sources += [baseline/'showcase_results.json',ROOT/final_path,ROOT/ref_path,ROOT/outreach_path,claims_source,ROOT/'data/processed/submission_package/verification_report.json',ROOT/'src/publish_deck_evidence.py']
    outputs += sorted((DEST/'evidence').glob('*.json'))+sorted((DEST/'evidence').glob('*.csv'))
    (DEST/'manifest.json').write_text(json.dumps({'publication_scope':'Explicit allowlist of aggregate results and figures. Customer-specific examples and placements with household load evidence remain in the ignored local deck ZIP. Local provenance sources are intentionally not downloadable from GitHub.','source_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in sources},'output_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in outputs}},indent=2),encoding='utf-8')
    print('Prepared GitHub aggregate deck documentation:',len(allowlist['historical'])+sum(len(v) for k,v in allowlist.items() if k!='historical'),'figures,',len(costs),'cost rows')

if __name__=='__main__':main()
