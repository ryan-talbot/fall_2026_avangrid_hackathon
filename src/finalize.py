"""One-command final acceptance audit and local handoff packaging.

Requires completed verified checkpoints; never reruns/overwrites the baseline,
frozen screening or preregistered six-group solves. No upload or Git mutation.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from inventory import ROOT,inventory,materials
from baseline import digest,preserve
from load_data import load,raw_fingerprint

DEST=ROOT/'data/processed/submission_package'

def run(script):
    subprocess.run([sys.executable,str(ROOT/'src'/script)],cwd=ROOT,check=True)

def audit_inputs():
    inventory(full_crc=True);materials()
    a,counts=load();observed=np.array([np.isfinite(row).sum() for row in a])
    if not np.array_equal(observed,counts):raise ValueError('AMI cache count array differs from actual finite slots')
    coverage=json.loads((ROOT/'data/processed/coverage.json').read_text())
    if coverage['duplicate_slots'] or coverage['conflicting_slots']:raise ValueError('Duplicate/conflicting slots need review')
    if observed.sum()!=coverage['rows']-coverage['excluded_rows']:raise ValueError('Coverage totals differ')
    if int((observed>=.95*8760).sum())!=coverage['population_95']:raise ValueError('Population coverage differs')
    # Inspect every CSV's audit sample against the stored cache. This is a
    # cross-file spot audit, not a second ingestion of all 298 million rows.
    samples=0
    for item in json.loads((ROOT/'data/processed/inventory.json').read_text()):
        for member in item.get('members',[]):
            for record in member['sample']:
                r={k.lower():v for k,v in record.items()}
                if r['is_complete_hour']!=1 or r['interval_count']!=4:continue
                h=int((pd.Timestamp(r['usage_date'])-pd.Timestamp('2025-09-01')).days*24+r['hour_ending']-1)
                if not np.isclose(a[int(r['customer_number']),h],r['hourly_kwh'],atol=1e-5,rtol=1e-6):raise ValueError('Raw sample differs from cache')
                samples+=1
    guard=ROOT/'data/processed/cache_input_guard.json'
    if not guard.exists():guard.write_text(json.dumps({'raw_zip_stat':raw_fingerprint(ROOT/'data/raw'),'scope':'Retrospective final audit of existing cache: finite counts and all CSV header samples checked; not a second full ingestion. Raw/cache SHA256 recorded separately.'},indent=2))
    paths=sorted((ROOT/'data/raw').glob('*'))+sorted((ROOT/'data/materials').glob('*.pdf'))+[ROOT/'data/processed'/n for n in ['ami.npy','counts.npy','coverage.json']]
    result={'audited_utc':datetime.now(timezone.utc).isoformat(),'csv_sample_rows_verified':samples,'rows':coverage['rows'],'sha256':{str(p.relative_to(ROOT)):digest(p) for p in paths},'scope':'Fresh full ZIP CRCs; workbooks read; all cache finite counts recomputed; every CSV sample checked; raw/cache hashes pinned. Does not claim independent full raw re-ingestion.'}
    (DEST/'input_acceptance.json').write_text(json.dumps(result,indent=2))

def claims():
    b=preserve();base=json.loads((b/'showcase_results.json').read_text());s=ROOT/'data/processed/milestone_screening';screen=json.loads((s/'screening_summary.json').read_text());m=json.loads((s/'milestone_results.json').read_text())
    supplemental=ROOT/'data/processed/final_analysis';final=json.loads((supplemental/'final_analysis_results.json').read_text());replay=json.loads((ROOT/'data/processed/four_design_replay/four_design_results.json').read_text())
    records=[]
    def add(key,value,unit,kind,source,scope):records.append({'claim':key,'value':value,'unit':unit,'evidence_type':kind,'source':str(source.relative_to(ROOT)),'scope':scope})
    for key in ['summer_peak_kw','summer_hours','summer_diversity']:
        add(key,base[key],'kW' if key.endswith('kw') else 'hours' if key.endswith('hours') else 'ratio','measured',b/'showcase_results.json','Same 30 homes and common complete summer hours')
    for k,v in screen['offer_counts'].items():add(k,v,'candidates','estimated',s/'screening_summary.json','Overlapping offers; denominator 33,674; ownership unknown unless reference-listed')
    for tech in ['EV','HP']:
        r=screen['reference_recovery'][tech];add(tech+'_reference_recovery',{'hits':r['heldout_recovered'],'denominator':r['qualifying_heldout_count'],'K':r['fixed_K']},'references','evaluated',s/'screening_summary.json','Partial likely references; unlisted unknown; no precision; HP is a heating proxy')
    for case in final['target_sweep']:
        for name,v in case['options'].items():
            interval=v['installed_cost_interval']
            add(f"{case['target']:.1%}_{name}",{'installed_dollars':v.get('cost'),'kw':v.get('total_kw'),'kwh':v.get('total_kwh'),'sites':v.get('site_count'),'status':v['status'],'cost_bounds':interval},'equipment / dollars','simulated_with_assumed_prices',supplemental/'final_analysis_results.json','Perfect-foresight unshifted historical sizing; compare only physically verified feasible incumbents')
            if interval['upper'] is not None:
                assert v['max_cap_miss_kw']<=1e-6 and v['max_simultaneous_kw']<=1e-6
    add('managed_shift',m['managed_charging']['shifted_kwh'],'kWh','simulated',s/'milestone_results.json','50% estimated eligible EV component movable, 06:00 deadline; none moved on July 3; program costs unknown')
    for name,v in replay['results'].items():add(name,{'hours_above_cap':v['hours_above_cap'],'worst_miss_kw':v['worst_miss_kw']},'hours / kW','simulated',ROOT/'data/processed/four_design_replay/four_design_results.json',v['design']['sizing_scope'])
    for r in final['screening_benchmarks']:add(r['technology']+'_'+r['ranking'],{'hits':r['recovered'],'denominator':r['qualifying_heldout_references'],'K':r['K']},'references','evaluated',supplemental/'final_analysis_results.json',r['scope'])
    for r in final['operating_sensitivities']:add(r['design']+'_'+r['scenario']+'_'+str(r.get('showcase_display_number',r['starting_soc_fraction'])),{'hours_above_cap':r['summary']['hours_above_cap'],'worst_miss_kw':r['summary']['worst_miss_kw']},'hours / kW','simulated',supplemental/'final_analysis_results.json',r['sizing_scope']+'; operating scenario, not prospective reliability')
    for r in final['annualized_cost_sensitivity']:add('annualized_cost_'+str(r['assumed_discount_rate'])+'_'+str(r['incremental_shared_annual_cost']),r,'dollars / year','assumed_financial_scenario',supplemental/'final_analysis_results.json',r['scope'])
    add('home_export_permission_sensitivity',{'installed_dollars':final['export_sensitivity']['feasible_installed_cost'],'necessary_cost_lower_bound':final['export_sensitivity']['necessary_cost_lower_bound'],'minimum_cost_certified':final['export_sensitivity']['minimum_cost_certified']},'dollars','simulated',supplemental/'final_analysis_results.json',final['export_sensitivity']['interpretation'])
    refined_path=ROOT/'data/processed/decision_refinement/decision_refinement_results.json';refined=json.loads(refined_path.read_text())
    for row in refined['showcase']['intervals']:
        if row['interval_outcome']=='transition_or_uncertified_bracket':add('preference_transition_'+str(row['left']),row,'target fraction / percentage points','simulated_with_certified_bounds',refined_path,'Finite-resolution transition region; no exact continuous threshold or single-switch claim')
    add('group6_post_budget_refinement',{'outcome':refined['group6']['outcome'],'home_cost_bounds':refined['group6']['home']['installed_cost_interval'],'shared_cost_bounds':refined['group6']['shared']['installed_cost_interval']},'dollars','simulated_with_certified_bounds',refined_path,'Post-budget refinement on original group; original time-boxed result preserved')
    outreach_path=ROOT/'data/processed/outreach_evidence/outreach_evidence_results.json';outreach=json.loads(outreach_path.read_text())
    for r in outreach['reference_diagnostics']:add('reference_'+r['technology']+'_'+r['reference_subset'],r,'references','evaluated',outreach_path,r['scope'])
    for r in outreach['program_priorities']:add('outreach_priority_'+r['offer'],r,'customers / kW','estimated_ranking_with_assumed_budget',outreach_path,r['scope'])
    path=DEST/'slide_claims.json';path.write_text(json.dumps({'claims':records,'instruction':'Use these source-backed numbers with their scope in the PowerPoint. This manifest does not inspect the actual deck. Supplementary details are in final_analysis_results.json.'},indent=2))
    pd.DataFrame(records).to_csv(DEST/'slide_claims.csv',index=False)
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reuse-input-audit',action='store_true',help='Reuse recorded input audit after verifying all recorded raw/cache SHA256 hashes; does not repeat CRC/workbook reads')
    args=parser.parse_args();DEST.mkdir(parents=True,exist_ok=True)
    status=DEST/'release_acceptance.json'
    status.write_text(json.dumps({'passed':False,'state':'running; previous acceptance invalidated'},indent=2))
    # Fail hand checks before any supplemental solves.
    subprocess.run([sys.executable,'-m','unittest','discover','-s','src','-p','test_*.py'],cwd=ROOT,check=True)
    if args.reuse_input_audit:
        old=json.loads((DEST/'input_acceptance.json').read_text())
        for p,h in old['sha256'].items():
            if digest(ROOT/p)!=h:raise ValueError('Audited input/cache changed: '+p)
    else:audit_inputs()
    run('final_analysis.py');run('decision_refinement.py');run('outreach_evidence.py');run('rubric_review.py');run('verify_submission.py')
    claim_path=claims()
    run('publish_deck_evidence.py')
    for manifest in [ROOT/'data/processed/final_analysis/final_analysis_manifest.json',ROOT/'data/processed/decision_refinement/decision_refinement_manifest.json',ROOT/'data/processed/outreach_evidence/outreach_evidence_manifest.json',DEST/'rubric_figure_manifest.json']:
        m=json.loads(manifest.read_text())
        for field in ['source_sha256','output_sha256']:
            for p,h in m[field].items():
                if digest(ROOT/p)!=h:raise ValueError('Stale source/output: '+p)
    published=json.loads((ROOT/'deck/manifest.json').read_text())
    for field in ['source_sha256','output_sha256']:
        for p,h in published[field].items():
            if digest(ROOT/p)!=h:raise ValueError('Stale aggregate GitHub evidence: '+p)
    # Compile every distributed module without writing bytecode to the archive.
    for p in (ROOT/'src').glob('*.py'):compile(p.read_text(encoding='utf-8-sig'),str(p),'exec')
    from package_submission import source_files
    sources=source_files()
    artifacts=[claim_path,DEST/'slide_claims.csv',DEST/'verification_report.json',DEST/'input_acceptance.json',ROOT/'data/processed/final_analysis/final_analysis_results.json']
    for folder in [DEST/'figures',ROOT/'data/processed/final_analysis/figures',ROOT/'data/processed/final_validation/figures',ROOT/'data/processed/decision_refinement/figures',ROOT/'data/processed/outreach_evidence/figures']:
        artifacts+=sorted(folder.glob('*.svg'))+sorted(folder.glob('*.png'))
    artifacts+=[p for p in (ROOT/'deck').rglob('*') if p.is_file()]
    report={'passed':True,'completed_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources},'artifact_sha256':{str(p.relative_to(ROOT)):digest(p) for p in artifacts},'slide_claims_sha256':digest(claim_path),'source_compile_check':True,'scope':'Code/evidence acceptance only. No final PowerPoint, field validation, complete appliance identification, tariff savings or submission upload certified.','input_audit':'input_acceptance.json','verification':'verification_report.json'}
    status.write_text(json.dumps(report,indent=2))
    try:run('package_submission.py')
    except Exception:
        report.update(passed=False,state='Code/evidence checks passed but packaging failed')
        status.write_text(json.dumps(report,indent=2));raise
    print('FINAL CODE/EVIDENCE ACCEPTANCE PASSED. See release_acceptance.json and slide_claims.json. PowerPoint review still required.')

if __name__=='__main__':main()
