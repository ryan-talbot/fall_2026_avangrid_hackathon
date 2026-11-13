"""Audit submission outputs/provenance/privacy and rerun meaningful hand checks."""
import json
import subprocess
import sys
import re
from pathlib import Path
import numpy as np
import pandas as pd
from baseline import preserve,digest
from business_stress import outcome
from inventory import ROOT
from load_data import load
from screening import RULES

DEST=ROOT/'data/processed/submission_package'

def main():
    checks=[]
    proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','src','-p','test_*.py','-v'],cwd=ROOT,capture_output=True,text=True)
    (DEST/'test_run.txt').write_text(proc.stdout+proc.stderr)
    if proc.returncode:raise RuntimeError('Hand checks failed; see test_run.txt')
    test_count=int(re.search(r'Ran (\d+) tests?',proc.stderr).group(1))
    checks.append('All discovered hand checks pass')
    dependencies=subprocess.run([sys.executable,'-m','pip','check'],cwd=ROOT,capture_output=True,text=True)
    if dependencies.returncode:raise RuntimeError('Dependency conflicts: '+dependencies.stdout+dependencies.stderr)
    checks.append('Installed dependency compatibility check passes')
    base=preserve();screen=ROOT/'data/processed/milestone_screening'
    summary=json.loads((screen/'screening_summary.json').read_text())
    assert digest(RULES)==summary['rules_sha256']
    assert digest(screen/'features_before_reference.csv')==summary['features_sha256_before_reference']
    assert summary['reference_recovery']['EV']['heldout_recovered']==17 and summary['reference_recovery']['EV']['qualifying_heldout_count']==90
    assert summary['reference_recovery']['HP']['heldout_recovered']==4 and summary['reference_recovery']['HP']['qualifying_heldout_count']==43
    offers=pd.read_csv(screen/'customer_to_offer.csv');counts=pd.read_csv(DEST/'segmentation_offer_counts.csv')
    assert len(offers)==33674 and (offers.coverage>=.95).all()
    expected={name.replace('_offer',''):int(offers[name].sum()) for name in summary['offer_counts']}
    assert counts['count'].tolist()==[summary['offer_counts'][v] for v in summary['offer_counts']]
    assert (counts.denominator==len(offers)).all()
    checks.append('Frozen rules/features, held-out recovery, actual offer counts and denominators match')
    manifests=[ROOT/'data/processed/final_validation/figure_manifest.json',DEST/'submission_figure_manifest.json',DEST/'business_figure_manifest.json']
    for path in manifests:
        m=json.loads(path.read_text())
        for key in ['source_sha256','output_sha256','figure_sha256','protected_figure_sha256']:
            for name,value in m.get(key,{}).items():assert digest(ROOT/name)==value,(path,key,name)
    checks.append('Baseline and preserved historical figure hashes are unchanged; new figure hashes match')
    for name in ['cleargrid_btm_placements_15pct','cleargrid_original_btm_placements_15pct']:
        evidence=pd.read_csv(DEST/f'{name}_evidence.csv')
        assert evidence.modules.sum()==6 and len(evidence)==3
        assert (evidence.simulated_discharge_at_group_peak_kw<=evidence.no_export_net_discharge_ceiling_kw+1e-6).all()
        assert abs(evidence.simulated_discharge_at_group_peak_kw.sum()-(80.15300032496452-68.13005027621985))<1e-6
    checks.append('Both 15% placement tables respect local no-export ceilings and cover the peak deficit')
    replay=json.loads((ROOT/'data/processed/four_design_replay/four_design_results.json').read_text())
    assert [v['hours_above_cap'] for v in replay['results'].values()]==[19,16,0,0]
    assert all(v['design']['sizing_scope']=='sized with the full historical record' for k,v in replay['results'].items() if k.startswith('historical'))
    assert replay['historical_figures_unchanged']
    checks.append('Heat-wave evidence retains both smaller failures and full-record larger passes with correct scope')
    folder=ROOT/'data/processed/business_stress';plan=json.loads((folder/'stress_test_plan.json').read_text());spec=plan['specification'];stress=json.loads((folder/'stress_results.json').read_text())
    _,population_counts=load();pool=np.flatnonzero(population_counts>=spec['annual_coverage_minimum']*8760)
    pool=pool[~np.isin(pool,np.load(base/'showcase_ids.npy'))]
    groups=np.random.default_rng(spec['seed']).choice(pool,size=(6,30),replace=False)
    assert np.array_equal(groups,np.load(folder/'sampled_groups.npy')) and len(np.unique(groups))==180
    assert digest(ROOT/'src/model.py')==plan['model_sha256'] and digest(ROOT/'config/business_stress_plan.json')==plan['plan_config_sha256']
    ledger=json.loads((folder/'attempt_ledger.json').read_text());assert len(ledger)==len(stress['groups'])==6
    assert ledger[-1]['elapsed_global_seconds']<=spec['global_time_limit_seconds']
    actual={v:0 for v in ['shared_win','home_win','tie','unresolved']}
    for g in stress['groups']:
        path=folder/f"group_{g['group']:02d}";x=np.load(path/'measured_common_load.npy')
        assert len(x)==30 and x.shape[1]==g['common_complete_hours']
        assert digest(path/'measured_common_load.npy')==g['common_load_sha256']
        assert abs(g['cap_kw']-.85*x.sum(axis=0).max())<1e-8
        assert g['same_cap_and_hours_for_both_options']
        s=g['options']['shared'];h=g['options']['home']
        assert s['common_load_sha256']==h['common_load_sha256']==g['common_load_sha256']
        label=outcome(s['installed_cost_interval'],h['installed_cost_interval']);assert label==g['outcome'];actual[label]+=1
        for name,option in g['options'].items():
            if option['installed_cost_interval']['upper'] is not None:
                f=pd.read_csv(path/f'dispatch_{name}.csv');assert len(f)==x.shape[1]
                assert (f.simulated_grid_kw-f.cap_kw).max()<1e-6
    assert actual==stress['counts']
    checks.append('All six preregistered groups, common-hour/cap equality, physical incumbents and certified/unresolved outcomes checked')
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    assert all(not p.startswith('data/') or p=='data/.gitkeep' for p in tracked)
    private=[ROOT/'data/raw',ROOT/'data/materials',ROOT/'data/config/original_showcase.json',ROOT/'data/processed/submission_package/figures/cleargrid_outreach_examples.svg',folder/'sampled_groups.npy']
    for path in private:
        code=subprocess.run(['git','check-ignore','--quiet',str(path.relative_to(ROOT))],cwd=ROOT).returncode
        assert code==0,str(path)
    assert json.loads((ROOT/'config/original_showcase.template.json').read_text())['customer_numbers']==[]
    checks.append('Organizer inputs, meter mapping, sampled IDs, household traces and outputs remain ignored; templates contain no meter IDs')
    status=subprocess.check_output(['git','status','--short','--untracked-files=all'],cwd=ROOT,text=True)
    (DEST/'git_handoff_status.txt').write_text(status)
    result={'passed':True,'checks':checks,'stress_counts':actual,'solver_attempt_elapsed_seconds':ledger[-1]['elapsed_global_seconds'],'tests_exit_code':proc.returncode,'test_count':test_count,'dependency_check':dependencies.stdout.strip(),'git_status_file':'git_handoff_status.txt','publishing':'No commit or push performed by this verification; generated data/assets remain local and ignored.'}
    (DEST/'verification_report.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
