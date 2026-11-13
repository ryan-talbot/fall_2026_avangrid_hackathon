r"""Preregistered, time-boxed six-group historical business stress test.

Run: .\.venv\Scripts\python.exe src/business_stress.py
Worker timeouts retain partial solves and unresolved comparisons.
"""
import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from baseline import preserve,digest
from inventory import ROOT
from load_data import load
from model import dispatch,home_design,home_energy_bound,diversity
from showcase import serial

DEST=ROOT/'data/processed/business_stress'
PLAN=ROOT/'config/business_stress_plan.json'

def now():return datetime.now(timezone.utc).isoformat()

def cost_interval(option,r,t,houses=30):
    """Conservative primary-cost intervals, excluding auxiliary tie objectives.

    Solver dual bounds include tiny throughput/power tie penalties. Subtract
    their finite maximum, then round UP to the installed-cost lattice.
    """
    if option=='shared':
        lattice=3250;fixed=15000;auxiliary_max=.01*1000+1e-5*2*t*2500
    else:
        lattice=500;fixed=0;auxiliary_max=1e-5*2*t*houses*7.68
    lower=float(fixed)
    dual=r.get('mip_dual_bound')
    if dual is not None and np.isfinite(dual):
        lower=fixed+lattice*max(0,math.ceil((float(dual)-auxiliary_max-1e-6)/lattice))
    analytical=r.get('necessary_equipment_bound',{}).get('cost')
    if analytical is not None:lower=max(lower,float(analytical))
    physical=bool(r.get('feasible') and r.get('max_cap_miss_kw',float('inf'))<=1e-6 and r.get('max_simultaneous_kw',float('inf'))<=1e-6)
    upper=float(r['cost']) if physical else None
    if upper is not None and lower>upper+1e-6:raise ValueError('Invalid installed-cost bound')
    return {'lower':lower,'upper':upper,'incumbent_physically_verified':physical,'certified_minimum_cost':upper is not None and abs(upper-lower)<1e-6,'auxiliary_objective_bound_subtracted':auxiliary_max,'proven_infeasible':r.get('status')==2}

def outcome(shared,home):
    if not shared or not home:return 'unresolved'
    if shared['upper'] is not None and (home['proven_infeasible'] or shared['upper']<home['lower']-1e-6):return 'shared_win'
    if home['upper'] is not None and (shared['proven_infeasible'] or home['upper']<shared['lower']-1e-6):return 'home_win'
    if shared['certified_minimum_cost'] and home['certified_minimum_cost'] and abs(shared['upper']-home['upper'])<1e-6:return 'tie'
    return 'unresolved'

def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2));tmp.replace(path)

def worker(index):
    plan=json.loads((DEST/'stress_test_plan.json').read_text());spec=plan['specification']
    if digest(ROOT/'src/model.py')!=plan['model_sha256']:raise ValueError('Model changed after sampling freeze')
    a,_=load();ids=np.load(DEST/'sampled_groups.npy')[index]
    times=pd.date_range(spec['summer_start'],spec['summer_stop_exclusive'],freq='h',inclusive='left')
    x=np.asarray(a[ids,6552:],float);valid=np.isfinite(x).all(axis=0);x=x[:,valid];times=times[valid]
    cap=float(x.sum(axis=0).max()*(1-spec['peak_reduction_fraction']))
    breaks=np.flatnonzero((times[1:]-times[:-1])!=pd.Timedelta(hours=1))+1
    folder=DEST/f'group_{index+1:02d}';folder.mkdir(exist_ok=True)
    np.save(folder/'measured_common_load.npy',x)
    pd.DataFrame({'hour_start':times}).to_csv(folder/'common_hours.csv',index=False)
    result={'group':index+1,'started_utc':now(),'common_complete_hours':len(times),'missing_summer_hours':2208-len(times),'observed_common_peak_kw':float(x.sum(axis=0).max()),'peak_hour_start':str(times[np.argmax(x.sum(axis=0))]),'cap_kw':cap,'diversity':diversity(x),'common_load_sha256':digest(folder/'measured_common_load.npy'),'same_cap_and_hours_for_both_options':True,'phase':'shared_running','options':{}}
    path=folder/'result.json';write(path,result)
    for name in ['shared','home']:
        result['phase']=name+'_running';write(path,result)
        r=dispatch(x.sum(axis=0),cap,optimize='shared',breaks=breaks,time_limit=spec['shared_solver_time_limit_seconds']) if name=='shared' else home_design(x,cap,breaks=breaks,time_limit=spec['home_mip_time_limit_seconds'])
        # Time-limited incumbents can contain avoidable simultaneous flows;
        # establish a physical fixed-design LP replay before using their cost.
        if r.get('feasible') and r.get('max_simultaneous_kw',0)>1e-6:
            fixed=dispatch(x.sum(axis=0) if name=='shared' else x,cap,energy=r['energy_kwh'],power=r['power_kw'],breaks=breaks,time_limit=30)
            if fixed['feasible']:
                for field in ['charge','discharge','soc','grid','max_cap_miss_kw','max_simultaneous_kw','max_balance_residual_kwh']:r[field]=fixed[field]
                r['fixed_design_verification_status']=fixed['status']
        record=serial(r);record['installed_cost_interval']=cost_interval(name,record,len(times))
        record['common_load_sha256']=result['common_load_sha256']
        result['options'][name]=record;result['phase']=name+'_complete';write(path,result)
        if r['feasible']:
            pd.DataFrame({'hour_start':times,'measured_group_load_kw':x.sum(axis=0),'simulated_grid_kw':r['grid'].sum(axis=0),'simulated_charge_kw':r['charge'].sum(axis=0),'simulated_discharge_kw':r['discharge'].sum(axis=0),'simulated_soc_kwh':r['soc'].sum(axis=0),'cap_kw':cap}).to_csv(folder/f'dispatch_{name}.csv',index=False)
    result['phase']='complete';result['completed_utc']=now();write(path,result)

def preregister():
    DEST.mkdir(parents=True,exist_ok=True);spec=json.loads(PLAN.read_text());a,counts=load();baseline=preserve()
    eligible=np.flatnonzero(counts>=spec['annual_coverage_minimum']*8760)
    eligible=eligible[~np.isin(eligible,np.load(baseline/'showcase_ids.npy'))]
    groups=np.random.default_rng(spec['seed']).choice(eligible,size=(spec['groups'],spec['homes_per_group']),replace=False)
    np.save(DEST/'eligible_pool.npy',eligible);np.save(DEST/'sampled_groups.npy',groups)
    recorded={'recorded_before_solves_utc':now(),'specification':spec,'plan_config_sha256':digest(PLAN),'model_sha256':digest(ROOT/'src/model.py'),'eligible_pool_count':len(eligible),'eligible_pool_sha256':digest(DEST/'eligible_pool.npy'),'sampled_groups_sha256':digest(DEST/'sampled_groups.npy'),'baseline_manifest_sha256':digest(baseline/'baseline_manifest.json')}
    write(DEST/'stress_test_plan.json',recorded)
    return recorded

def summarize(ledger,recorded):
    details=[];rows=[]
    for entry in ledger:
        folder=DEST/f"group_{entry['group']:02d}";p=folder/'result.json';r=json.loads(p.read_text()) if p.exists() else {'group':entry['group'],'options':{},'phase':'not_started'}
        r['execution']=entry
        intervals={name:r.get('options',{}).get(name,{}).get('installed_cost_interval') for name in ['shared','home']}
        r['outcome']=outcome(intervals['shared'],intervals['home']);details.append(r)
        row={k:r.get(k) for k in ['group','common_complete_hours','missing_summer_hours','observed_common_peak_kw','cap_kw','diversity','outcome','phase']}
        row['execution_status']=entry['status']
        for name in ['shared','home']:
            option=r.get('options',{}).get(name,{})
            for field in ['status','message','mip_gap','mip_dual_bound','cost','max_cap_miss_kw']:
                row[f'{name}_{field}']=option.get(field)
            interval=option.get('installed_cost_interval',{})
            row[f'{name}_cost_lower']=interval.get('lower');row[f'{name}_cost_upper']=interval.get('upper')
            for field in ['power_kw','energy_kwh','sites']:row[f'{name}_{field}']=sum(option[field]) if option.get(field) is not None else None
        rows.append(row)
    counts={name:sum(r['outcome']==name for r in details) for name in ['shared_win','home_win','tie','unresolved']}
    adequate=sum(counts[k] for k in ['shared_win','home_win','tie'])>=recorded['specification']['minimum_certified_comparisons_for_summary']
    result={'recorded_plan_sha256':digest(DEST/'stress_test_plan.json'),'counts':counts,'enough_certified_comparisons':adequate,'all_six_attempts_or_nonstarts_included':True,'groups':details,'interpretation':'Six additional synthetic groups, not a representative utility sample or feeder map. Historical perfect-foresight sizing, assumed prices; bounds certify strict winners. Unresolved comparisons are not assigned to the cheaper incumbent.','fallback_shared_break_even_extra_installed_cost':9250}
    write(DEST/'stress_results.json',result);pd.DataFrame(rows).to_csv(DEST/'stress_comparison.csv',index=False)
    lines=['# Six-group business stress test','',f"Seed {recorded['specification']['seed']}; exact one-draw sampling rule and time limits frozen before solves in stress_test_plan.json. All six groups are reported.",json.dumps(counts),f'At least four certified comparisons required for a multi-group summary: {adequate}.','', '| Group | Common hours | Peak / cap kW | Shared cost interval | Home cost interval | Outcome | Execution |','|---|---:|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['group']} | {r['common_complete_hours']} | {r['observed_common_peak_kw']} / {r['cap_kw']} | {r['shared_cost_lower']} to {r['shared_cost_upper']} | {r['home_cost_lower']} to {r['home_cost_upper']} | {r['outcome']} | {r['execution_status']} |")
    lines+=['','Strict wins use feasible upper costs versus certified lower bounds. Dual bounds are adjusted conservatively for tie-breaking objectives and rounded to primary installed-cost lattices. Raw solver status, gaps, bounds, phase and timeouts are retained in CSV/JSON. A missing/unfinished option remains unresolved unless a strict cost ordering can be proved.',
            'The model includes hourly cap, SOC, efficiency, reserve, power, no-export and recharge constraints. It excludes managed-program costs, validated bill savings, actual feeder mapping, service-upgrade costs and infrastructure-deferral value.',
            'Showcase sensitivity is available regardless of run completion: $50,750 shared vs $60,000 homes at 15%; $9,250 of extra shared installed cost erases that advantage, all else equal. 10% and 15% remain two tested showcase targets; no finer crossover sweep is claimed.',
            '', '```powershell',r'.\.venv\Scripts\python.exe src/business_stress.py','```']
    (DEST/'stress_summary.md').write_text('\n'.join(lines)+'\n')
    print('Stress counts:',counts,'Enough comparisons:',adequate,flush=True)

def certify_completed_run():
    """Add valid aggregate-energy cost bounds without rerunning group sampling
    or changing any installed prices/physics. Keep failed/timed-out solves.
    """
    recorded=json.loads((DEST/'stress_test_plan.json').read_text());ledger=json.loads((DEST/'attempt_ledger.json').read_text())
    terminal={'complete','worker_error','hard_group_time_limit','global_deadline_not_started'}
    if len(ledger)!=recorded['specification']['groups'] or any(v['status'] not in terminal for v in ledger):raise ValueError('Wait for all six attempts before final bound certification')
    if digest(ROOT/'src/model.py')!=recorded['model_sha256']:raise ValueError('Model changed since preregistration')
    for entry in ledger:
        folder=DEST/f"group_{entry['group']:02d}";path=folder/'result.json'
        if not path.exists():continue
        r=json.loads(path.read_text());load_path=folder/'measured_common_load.npy'
        if digest(load_path)!=r['common_load_sha256']:raise ValueError('Recorded group input changed')
        x=np.load(load_path);tt=pd.DatetimeIndex(pd.read_csv(folder/'common_hours.csv',parse_dates=['hour_start']).hour_start)
        breaks=np.flatnonzero((tt[1:]-tt[:-1])!=pd.Timedelta(hours=1))+1
        bound=home_energy_bound(x,r['cap_kw'],breaks)
        option=r['options'].setdefault('home',{'status':None,'message':'No completed home incumbent; necessary equipment bound only','feasible':False})
        option['necessary_equipment_bound']=bound
        option['installed_cost_interval']=cost_interval('home',option,len(tt))
        r['analytical_bound_certified_utc']=now();write(path,r)
    summarize(ledger,recorded)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=int);parser.add_argument('--summarize',action='store_true');args=parser.parse_args()
    if args.worker is not None:worker(args.worker);return
    if args.summarize:certify_completed_run();return
    recorded=preregister();print('Sampling frozen before solves:',DEST/'stress_test_plan.json',flush=True)
    spec=recorded['specification'];start=time.monotonic();ledger=[{'group':i+1,'status':'not_started','started_utc':None} for i in range(spec['groups'])]
    # Remove no outputs: reuse is only within this new invocation. Existing
    # results are marked stale until this invocation actually launches a worker.
    for i in range(spec['groups']):
        folder=DEST/f'group_{i+1:02d}';folder.mkdir(exist_ok=True)
        result_path=folder/'result.json'
        if result_path.exists():result_path.replace(folder/f'previous_result_{time.time_ns()}.json')
    write(DEST/'attempt_ledger.json',ledger)
    for i,entry in enumerate(ledger):
        folder=DEST/f'group_{i+1:02d}'
        remaining=spec['global_time_limit_seconds']-(time.monotonic()-start)
        if remaining<=0:entry['status']='global_deadline_not_started';continue
        entry['started_utc']=now();print('Attempting group',i+1,flush=True)
        with (folder/'solver_log.txt').open('w') as log:
            try:
                proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(i)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=min(remaining,spec['group_time_limit_seconds']))
                entry['status']='complete' if proc.returncode==0 else 'worker_error';entry['return_code']=proc.returncode
            except subprocess.TimeoutExpired:entry['status']='hard_group_time_limit'
        entry['finished_utc']=now();entry['elapsed_global_seconds']=time.monotonic()-start
        write(DEST/'attempt_ledger.json',ledger);summarize(ledger,recorded)
    write(DEST/'attempt_ledger.json',ledger)
    certify_completed_run()

if __name__=='__main__':main()
