"""Resolve cost decisions using monotonic interval certificates and enumeration.

Original showcase and one-hour six-group experiment are never overwritten.
"""
import json
import time
from itertools import combinations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from baseline import digest
from inventory import ROOT
from model import dispatch,home_design,home_energy_bound
from showcase import serial
from business_stress import cost_interval,outcome
from final_validation import input_data

DEST=ROOT/'data/processed/decision_refinement'
PLAN=ROOT/'config/decision_refinement_plan.json'

def interval_winner(left,right):
    """Optimal costs are nondecreasing as the reduction target increases.

    Cross-endpoint separation certifies the WHOLE interval, including any
    unobserved equipment switches. Endpoint winner agreement alone cannot.
    """
    for winner,loser in [('shared','home'),('home','shared')]:
        upper=right['options'][winner]['installed_cost_interval']['upper']
        lower=left['options'][loser]['installed_cost_interval']['lower']
        if upper is not None and upper<lower-1e-6:return winner+'_win'
    a=left['options'];b=right['options']
    intervals=[a[n]['installed_cost_interval'] for n in ['shared','home']]+[b[n]['installed_cost_interval'] for n in ['shared','home']]
    if all(v['certified_minimum_cost'] for v in intervals) and len({v['lower'] for v in intervals})==1:return 'tie'
    return None

def enumerate_home(x,cap,breaks,limit,max_cost=None):
    """Cost-ordered exhaustive placements, not a sampled placement heuristic.

    Necessary equipment bounds skip impossible cheaper designs. Every other
    cheaper design must fail a necessary power cut or a proven-infeasible LP.
    A solver timeout prevents an optimality claim.
    """
    start=time.monotonic();bound=home_energy_bound(x,cap,breaks);n=len(x)
    ceilings=np.maximum(x,0);deficit=np.maximum(x.sum(axis=0)-cap,0);hours=deficit>1e-7
    candidates=[]
    for m in range(bound['modules'],2*n+1):
        for s in range(max(bound['sites'],int(np.ceil(m/2))),min(m,n)+1):
            cost=8500*m+3000*s
            if max_cost is None or cost<=max_cost:candidates.append((cost,m,s))
    counts={'placements':0,'power_pruned':0,'lp_proven_infeasible':0,'lp_unknown':0};unknown_lower=None
    for cost,m,s in sorted(candidates):
        for installed in combinations(range(n),s):
            if time.monotonic()-start>limit:return {'complete':False,'reason':'enumeration time limit','counts':counts,'elapsed_seconds':time.monotonic()-start,'certified_lower_cost':min(cost,unknown_lower) if unknown_lower else cost}
            chosen=np.array(installed)
            for doubled in combinations(range(s),m-s):
                counts['placements']+=1;units=np.ones(s,dtype=int);units[list(doubled)]=2;p=units*3.84
                if np.any(np.minimum(p[:,None],ceilings[chosen][:,hours]).sum(axis=0)<deficit[hours]-1e-7):counts['power_pruned']+=1;continue
                residual=cap-(x.sum(axis=0)-x[chosen].sum(axis=0))
                r=dispatch(x[chosen],residual,energy=units*10.08,power=p,breaks=breaks,time_limit=max(.1,min(30,limit-(time.monotonic()-start))))
                if r.get('feasible') and r['max_simultaneous_kw']<=1e-6:
                    all_units=np.zeros(n,dtype=int);all_units[chosen]=units
                    for field in ['charge','discharge','soc']:
                        expanded=np.zeros_like(x);expanded[chosen]=r[field];r[field]=expanded
                    r.update(grid=x+r['charge']-r['discharge'],energy_kwh=all_units*10.08,power_kw=all_units*3.84,units=all_units,sites=(all_units>0).astype(int),cost=cost)
                    lower=unknown_lower if unknown_lower is not None else cost
                    r.update(necessary_equipment_bound={'cost':lower},mip_dual_bound=float(lower),method='Cost-ordered exhaustive placement enumeration with necessary cuts and full-horizon LP',status=0 if lower==cost else 1)
                    return {'complete':lower==cost,'reason':'feasible configuration found; all cheaper configurations excluded' if lower==cost else 'cheaper LP outcomes unresolved','counts':counts,'elapsed_seconds':time.monotonic()-start,'certified_lower_cost':lower,'result':r}
                if r['status']==2:counts['lp_proven_infeasible']+=1
                else:counts['lp_unknown']+=1;unknown_lower=cost if unknown_lower is None else min(unknown_lower,cost)
    return {'complete':unknown_lower is None,'reason':'all configurations within cost budget excluded' if unknown_lower is None else 'unknown LP outcomes','counts':counts,'elapsed_seconds':time.monotonic()-start,'certified_lower_cost':unknown_lower if unknown_lower is not None else max_cost+1 if max_cost is not None else None,'no_design_at_or_below_budget':unknown_lower is None}

def refine_showcase(plan,signature):
    _,base,_,_,x,times,valid,_,_=input_data();sx=x[:,valid];st=times[valid]
    breaks=np.flatnonzero(np.diff(st.values)!=np.timedelta64(1,'h'))+1;peak=float(sx.sum(axis=0).max())
    seeds=json.loads((ROOT/'data/processed/final_analysis/final_analysis_results.json').read_text())['target_sweep']
    def query(target):
        file=DEST/f'query_{target:.8f}.json'
        if file.exists():
            result=json.loads(file.read_text())
            if result['signature']!=signature:raise ValueError('Refinement cache provenance differs')
            return result
        reused=next((r for r in seeds if abs(r['target']-target)<1e-10),None)
        if reused:result={k:reused[k] for k in ['target','cap_kw','options','outcome']}
        else:
            cap=peak*(1-target);options={}
            print(f'Refinement query {target:.6%}',flush=True)
            for name in ['shared','home']:
                r=dispatch(sx.sum(axis=0),cap,optimize='shared',breaks=breaks,time_limit=plan['solver_time_limit_seconds']) if name=='shared' else home_design(sx,cap,breaks=breaks,time_limit=plan['solver_time_limit_seconds'])
                record=serial(r);record['installed_cost_interval']=cost_interval(name,record,len(st));options[name]=record
            result={'target':target,'cap_kw':cap,'options':options,'outcome':outcome(options['shared']['installed_cost_interval'],options['home']['installed_cost_interval'])}
        result.update(signature=signature,complete_common_hours=len(st),load_basis='Same verified unshifted historical showcase')
        file.write_text(json.dumps(result,indent=2));return result
    leaves=[]
    def split(left,right):
        winner=interval_winner(left,right)
        if winner or right['target']-left['target']<=plan['target_resolution_fraction']+1e-12:
            leaves.append({'left':left['target'],'right':right['target'],'left_outcome':left['outcome'],'right_outcome':right['outcome'],'interval_outcome':winner or 'transition_or_uncertified_bracket','certificate':'Monotonic optimal-cost endpoint separation' if winner else 'Resolution reached; no claim inside interval','width_percentage_points':100*(right['target']-left['target'])});return
        middle=query((left['target']+right['target'])/2);split(left,middle);split(middle,right)
    for a,b in zip(seeds,seeds[1:]):split(query(a['target']),query(b['target']))
    queries=[json.loads(p.read_text()) for p in sorted(DEST.glob('query_*.json'))]
    for name in ['shared','home']:
        for a,b in zip(queries,queries[1:]):
            upper=b['options'][name]['installed_cost_interval']['upper'];lower=a['options'][name]['installed_cost_interval']['lower']
            if upper is not None and upper<lower-1e-6:raise ValueError('Optimal cost monotonicity violated')
    return {'queries':queries,'intervals':leaves,'resolution_percentage_points':100*plan['target_resolution_fraction'],'all_queried_points_certified':all(q['outcome']!='unresolved' for q in queries),'scope':'Monotonic certificates cover full intervals; remaining narrow brackets explicitly retain finite numerical resolution. No continuous exact crossover or single-switch assumption.'}

def group6(plan,signature):
    file=DEST/'group6_refinement.json'
    if file.exists():
        cached=json.loads(file.read_text())
        if cached['signature']!=signature:raise ValueError('Group refinement cache provenance differs')
        return cached
    folder=ROOT/'data/processed/business_stress/group_06';original=json.loads((folder/'result.json').read_text());x=np.load(folder/'measured_common_load.npy')
    if digest(folder/'measured_common_load.npy')!=original['common_load_sha256']:raise ValueError('Group 6 load changed')
    tt=pd.DatetimeIndex(pd.read_csv(folder/'common_hours.csv',parse_dates=['hour_start']).hour_start);breaks=np.flatnonzero(np.diff(tt.values)!=np.timedelta64(1,'h'))+1
    enumerated=enumerate_home(x,original['cap_kw'],breaks,plan['group6_enumeration_limit_seconds'],max_cost=original['options']['shared']['cost'])
    r=enumerated.pop('result',None);home=serial(r) if r else {'feasible':False,'status':1,'necessary_equipment_bound':{'cost':enumerated['certified_lower_cost']}}
    home['installed_cost_interval']=cost_interval('home',home,len(tt))
    if r:
        np.savez(DEST/'group6_home_site_audit.npz',load=x,charge=r['charge'],discharge=r['discharge'],soc=r['soc'],grid=r['grid'])
    result={'signature':signature,'original_result_sha256':digest(folder/'result.json'),'same_load_sha256':original['common_load_sha256'],'same_hours_and_cap':True,'cap_kw':original['cap_kw'],'original_outcome':'unresolved','enumeration':enumerated,'home':home,'shared':original['options']['shared'],'outcome':outcome(original['options']['shared']['installed_cost_interval'],home['installed_cost_interval']),'scope':'Post-budget refinement; original one-hour experiment and its unresolved result preserved, not retroactively relabeled.'}
    file.write_text(json.dumps(result,indent=2));return result

def figure(showcase,g6):
    folder=DEST/'figures';folder.mkdir(exist_ok=True);fig,axes=plt.subplots(1,2,figsize=(16,9))
    for name,color in [('shared','#287d69'),('home','#246c9c')]:
        x=[];y=[]
        for q in showcase['queries']:
            interval=q['options'][name]['installed_cost_interval']
            if interval['certified_minimum_cost']:x.append(q['target']*100);y.append(interval['upper'])
        axes[0].scatter(x,y,s=20,color=color,label=name)
    for row in showcase['intervals']:
        if row['interval_outcome']=='transition_or_uncertified_bracket':axes[0].axvspan(row['left']*100,row['right']*100,color='#b75c29',alpha=.5)
    axes[0].set(xlabel='Peak reduction target (%)',ylabel='Assumed installed dollars',title='Adaptive historical cost comparison');axes[0].legend();axes[0].grid(alpha=.2)
    axes[1].axis('off');lines=['POST-BUDGET GROUP 6 REFINEMENT',f"Outcome: {g6['outcome']}",f"Shared: ${g6['shared']['cost']:,}",f"Home cost bounds: {g6['home']['installed_cost_interval']['lower']} to {g6['home']['installed_cost_interval']['upper']}",'',f"{len(showcase['queries'])} showcase target queries",f"Transition bracket width <= {showcase['resolution_percentage_points']:.3f} percentage points",'Entire other intervals use monotonic cost certificates.','','Original six-group run remains:','5 shared wins; 1 unresolved.','Refinement is separately labeled.']
    axes[1].text(.02,.95,'\n'.join(lines),va='top',fontsize=14,linespacing=1.7)
    fig.suptitle('Business decisions backed by feasible designs and cost bounds',fontsize=20,fontweight='bold')
    fig.text(.03,.04,'Measured unshifted AMI; synthetic groups; historical perfect foresight; assumed installed prices. Orange bands retain crossover resolution.\nNo actual bill savings or feeder-level relief established. Original showcase and one-hour stress experiment are preserved.',fontsize=11)
    fig.tight_layout(rect=(0,.12,1,.92));paths=[]
    for ext in ['png','svg']:
        p=folder/f'cleargrid_decision_refinement.{ext}';fig.savefig(p,dpi=300);paths.append(p)
    plt.close(fig);return paths

def main():
    DEST.mkdir(parents=True,exist_ok=True);plan=json.loads(PLAN.read_text())
    signature={str(p.relative_to(ROOT)):digest(p) for p in [PLAN,ROOT/'src/model.py',ROOT/'src/decision_refinement.py',ROOT/'data/processed/final_analysis/common_load.npy',ROOT/'data/processed/business_stress/group_06/result.json']}
    # Written before any new solve; this is an extension, not the original plan.
    recorded=DEST/'plan_recorded_before_solves.json'
    if recorded.exists() and json.loads(recorded.read_text())['signature']!=signature:raise ValueError('Refinement implementation/plan changed; use a fresh output folder')
    recorded.write_text(json.dumps({'plan':plan,'signature':signature},indent=2))
    print('Refining group 6 without resampling',flush=True);g6=group6(plan,signature)
    print('Group 6:',g6['outcome'],g6['enumeration'],flush=True)
    showcase=refine_showcase(plan,signature);paths=figure(showcase,g6)
    result={'showcase':showcase,'group6':g6,'plan':plan};p=DEST/'decision_refinement_results.json';p.write_text(json.dumps(result,indent=2))
    outputs=[p,*paths,*DEST.glob('query_*.json'),DEST/'group6_refinement.json']
    audit=DEST/'group6_home_site_audit.npz'
    if audit.exists():outputs.append(audit)
    (DEST/'decision_refinement_manifest.json').write_text(json.dumps({'source_sha256':signature,'output_sha256':{str(p.relative_to(ROOT)):digest(p) for p in outputs}},indent=2))
    print('Decision refinement complete:',p,flush=True)

if __name__=='__main__':main()
