"""Supplemental frozen-rule benchmarks, target sweep and operating sensitivities.

Writes only ignored local outputs; preserves all original checkpoint artifacts.
"""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from baseline import digest, preserve
from inventory import ROOT
from final_validation import input_data
from model import dispatch, home_design
from business_stress import cost_interval, outcome
from causal_dispatch import replay
from showcase import serial
from screening import RULES

DEST=ROOT/'data/processed/final_analysis'
PLAN=ROOT/'config/final_review_plan.json'

def crf(rate,years):
    if rate<0 or years<=0: raise ValueError('Nonnegative rate and positive horizon required')
    return 1/years if rate==0 else rate/(1-(1+rate)**(-years))

def wilson(hits,n):
    if n<=0: return [None,None]
    z=1.959963984540054;p=hits/n;denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return [max(0,center-half),min(1,center+half)]

def benchmarks(plan):
    folder=ROOT/'data/processed/milestone_screening'
    summary=json.loads((folder/'screening_summary.json').read_text())
    if digest(RULES)!=summary['rules_sha256'] or digest(folder/'features_before_reference.csv')!=summary['features_sha256_before_reference']:
        raise ValueError('Frozen classification changed')
    features=pd.read_csv(folder/'features_before_reference.csv')
    split=pd.read_csv(folder/'reference_split.csv');rows=[]
    for tech,primary in [('EV','ev_score'),('HP','heating_score')]:
        selected=split[(split.technology==tech)&(split.split=='heldout')&split.qualifies]
        refs=set(selected.CUSTOMER_NUMBER);k=summary['reference_recovery'][tech]['fixed_K']
        for score in [primary,*plan['screening_benchmarks'][tech]]:
            ranked=features.sort_values([score,'CUSTOMER_NUMBER'],ascending=[False,True]).head(k)
            hits=len(refs&set(ranked.CUSTOMER_NUMBER))
            rows.append({'technology':tech,'ranking':score,'K':k,'population':len(features),'qualifying_heldout_references':len(refs),'recovered':hits,'recovery':hits/len(refs),'wilson95_descriptive':wilson(hits,len(refs)),'uniform_random_expected_hits':k*len(refs)/len(features),'scope':'Retrospective benchmark on already examined held-out references; no retuning or new untouched validation. References are partial likely labels; unlisted unknown; no precision.'})
    pd.DataFrame(rows).to_csv(DEST/'screening_benchmarks.csv',index=False)
    return rows

def summarize_option(name,r,t):
    result=serial(r);result['installed_cost_interval']=cost_interval(name,result,t)
    if r.get('feasible'):
        result.update(total_kw=float(np.sum(r['power_kw'])),total_kwh=float(np.sum(r['energy_kwh'])),site_count=int(np.sum(r['sites'])))
    return result

def target_sweep(plan,base,x,times,valid):
    sx=x[:,valid];st=times[valid];peak=float(sx.sum(axis=0).max())
    breaks=np.flatnonzero(np.diff(st.values)!=np.timedelta64(1,'h'))+1
    signature={'plan':digest(PLAN),'model':digest(ROOT/'src/model.py'),'load':digest(DEST/'common_load.npy')}
    results=[]
    for target in plan['targets']:
        file=DEST/f'target_{target:.3f}.json'
        if file.exists():
            saved=json.loads(file.read_text())
            if saved['signature']!=signature: raise ValueError('Supplemental cache provenance differs; use a fresh final_analysis folder')
            results.append(saved);continue
        cap=peak*(1-target);options={}
        for name in ['shared','home']:
            if str(target) in base['targets']:
                r=base['targets'][str(target)][name]
                record=summarize_option(name,r,len(st));record['reused_preserved_baseline']=True
            else:
                print('New target',target,name,flush=True)
                r=dispatch(sx.sum(axis=0),cap,optimize='shared',breaks=breaks,time_limit=plan['new_target_solver_seconds']) if name=='shared' else home_design(sx,cap,breaks=breaks,time_limit=plan['new_target_solver_seconds'])
                record=summarize_option(name,r,len(st))
                if r['feasible']:
                    pd.DataFrame({'hour_start':st,'measured_load_kw':sx.sum(axis=0),'grid_kw':r['grid'].sum(axis=0),'cap_kw':cap}).to_csv(DEST/f'dispatch_{target:.3f}_{name}.csv',index=False)
            options[name]=record
        result={'signature':signature,'target':target,'cap_kw':cap,'complete_hours':len(st),'same_load_hours_and_cap':True,'options':options,'outcome':outcome(options['shared']['installed_cost_interval'],options['home']['installed_cost_interval'])}
        file.write_text(json.dumps(result,indent=2));results.append(result)
    return results,breaks

def finance(plan,base):
    shared=base['targets']['0.15']['shared']['cost'];home=base['targets']['0.15']['home']['cost'];rows=[]
    for rate in plan['assumed_discount_rates']:
        factor=crf(rate,plan['assumed_financial_years'])
        for incremental in plan['incremental_shared_annual_costs']:
            rows.append({'assumed_years':plan['assumed_financial_years'],'assumed_discount_rate':rate,'capital_recovery_factor':factor,'incremental_shared_annual_cost':incremental,'annualized_home_capital_cost':home*factor,'annualized_shared_capital_cost':shared*factor,'annualized_shared_advantage_after_incremental_cost':(home-shared)*factor-incremental,'maximum_shared_upfront_cost':home-incremental/factor,'scope':'Assumed equal financial horizon; incremental recurring cost includes any net O&M/program/energy cost. No measured bill savings, tariff, degradation, replacement, salvage or avoided upgrade value.'})
    pd.DataFrame(rows).to_csv(DEST/'annualized_cost_sensitivity.csv',index=False)
    return rows

def export_check(base,x,valid,cap,breaks):
    sx=x[:,valid]
    # Read placements from the original replay's verified equipment, not IDs.
    replay_results=json.loads((ROOT/'data/processed/four_design_replay/four_design_results.json').read_text())
    design=replay_results['results']['historical_home']['design']
    r=dispatch(sx,cap,energy=design['energy_kwh'],power=design['power_kw'],breaks=breaks,export=True)
    # An export-enabled fleet still needs enough aggregate energy and power.
    modules=int(np.ceil((sx.sum(axis=0).max()-cap-1e-8)/3.84));checks=[]
    while modules<=60:
        relaxed=dispatch(sx.sum(axis=0),cap,energy=[modules*10.08],power=[230.4],breaks=breaks)
        checks.append({'modules':modules,'status':relaxed['status'],'feasible':relaxed['feasible']})
        if relaxed['status']!=2:break
        modules+=1
    lower=modules*8500+math.ceil(modules/2)*3000
    certified=bool(r['feasible'] and lower==base['targets']['0.15']['home']['cost'])
    return {'target':.15,'home_export_allowed':True,'original_placements_retained':True,'fixed_equipment_replay':serial(r),'aggregate_relaxation_checks':checks,'necessary_cost_lower_bound':lower,'minimum_cost_certified':certified,'feasible_installed_cost':base['targets']['0.15']['home']['cost'] if r['feasible'] else None,'interpretation':'Mathematical export-permission sensitivity only; no export tariff, permission, solar generation or revenue assumed. Shared aggregate boundary unchanged.'}

def operating(plan,x,times,cap):
    original=json.loads((ROOT/'data/processed/four_design_replay/four_design_results.json').read_text())
    period=(times>='2026-07-01')&(times<'2026-07-05 06:00');rt=times[period];scored=rt<'2026-07-05';rows=[]
    for key in ['historical_shared','historical_home']:
        d=original['results'][key]['design'];load=x[:,period].sum(axis=0,keepdims=True) if key.endswith('shared') else x[:,period]
        for start in plan['causal_starting_soc_fractions']:
            r=replay(load,rt,cap,d['energy_kwh'],d['power_kw'],start_fraction=start,score_mask=scored)
            rows.append({'design':key,'scenario':'starting_charge','starting_soc_fraction':start,'sizing_scope':'sized with the full historical record','summary':r['summary']})
        if key.endswith('shared'):
            r=replay(load,rt,cap,np.zeros_like(d['energy_kwh']),np.zeros_like(d['power_kw']),score_mask=scored)
            rows.append({'design':key,'scenario':'shared_site_unavailable','starting_soc_fraction':1.,'sizing_scope':'sized with the full historical record','summary':r['summary']})
        if key.endswith('home'):
            for site in np.flatnonzero(d['energy_kwh']):
                e=np.array(d['energy_kwh'],float);p=np.array(d['power_kw'],float);e[site]=p[site]=0
                r=replay(load,rt,cap,e,p,score_mask=scored)
                rows.append({'design':key,'scenario':'one_home_site_unavailable','showcase_display_number':int(site+1),'starting_soc_fraction':1.,'sizing_scope':'sized with the full historical record','summary':r['summary']})
    return rows

def figures(results,bench,fin,oper):
    folder=DEST/'figures';folder.mkdir(exist_ok=True);outputs=[]
    fig,axes=plt.subplots(1,2,figsize=(16,9))
    labels=[f"{r['target']:.1%}" for r in results]
    for name,color in [('shared','#258474'),('home','#326fa0')]:
        values=[r['options'][name].get('cost',np.nan) if r['options'][name]['installed_cost_interval']['incumbent_physically_verified'] else np.nan for r in results]
        axes[0].scatter(labels,values,label=name,color=color,s=70)
    axes[0].set(title='Historical target sweep: four tested points',ylabel='Assumed installed dollars',xlabel='Reduction from observed summer peak');axes[0].legend();axes[0].grid(alpha=.2)
    for rate in sorted({r['assumed_discount_rate'] for r in fin}):
        rows=[r for r in fin if r['assumed_discount_rate']==rate]
        axes[1].plot([r['incremental_shared_annual_cost'] for r in rows],[r['maximum_shared_upfront_cost'] for r in rows],'o-',label=f'{rate:.0%} assumed discount')
    axes[1].axhline(50750,color='black',ls='--',label='Modeled shared: $50,750')
    axes[1].set(title='15% case: maximum shared price for equal annual cost',xlabel='Extra shared recurring cost ($/year)',ylabel='Maximum shared installed dollars');axes[1].legend(fontsize=9);axes[1].grid(alpha=.2)
    fig.suptitle('ClearGrid: target and annualized cost sensitivities',fontsize=19,fontweight='bold')
    fig.text(.03,.04,'Unshifted measured AMI; perfect-foresight sizing, 20% reserve, 89.4% RTE. Financial scenario: 15 years; no bill savings or solar revenue.\nIntervals between tested targets are not solved. Read cost bounds/status in final_analysis_results.json before claiming an optimum.',fontsize=11)
    fig.tight_layout(rect=(0,.12,1,.92))
    for suffix in ['svg','png']:
        p=folder/f'cleargrid_final_cost_sensitivity.{suffix}';fig.savefig(p,dpi=300);outputs.append(p)
    plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(16,9));fig.suptitle('Screening evidence and operating limits',fontsize=21,fontweight='bold')
    for ax in axes:ax.axis('off')
    btable=[[r['technology'],r['ranking'].replace('_',' '),f"{r['recovered']}/{r['qualifying_heldout_references']}",str(r['K'])] for r in bench]
    table=axes[0].table(cellText=btable,colLabels=['Likely reference','Fixed ranking','Recovery','Outreach K'],loc='center',cellLoc='left',colWidths=[.18,.46,.18,.18]);table.auto_set_font_size(False);table.set_fontsize(12);table.scale(1,1.65)
    axes[0].set_title('Frozen rules versus simpler ranks: descriptive comparisons on previously examined held-out references',fontsize=13,pad=10)
    otable=[]
    for r in oper:
        label=f"Start {r['starting_soc_fraction']:.0%}" if r['scenario']=='starting_charge' else 'Shared site unavailable' if r['scenario']=='shared_site_unavailable' else f"Home {r['showcase_display_number']} unavailable"
        otable.append([r['design'].replace('historical_',''),label,str(r['summary']['hours_above_cap']),f"{r['summary']['worst_miss_kw']:.3f}"])
    table=axes[1].table(cellText=otable,colLabels=['Full-record-sized design','Operating assumption','Hours above cap','Worst miss kW'],loc='center',cellLoc='left',colWidths=[.22,.42,.18,.18]);table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,1.4)
    axes[1].set_title('July 1-4 causal replay: original home placements 6 / 11 / 19; same fixed 68.13005 kW cap',fontsize=13,pad=10)
    fig.text(.03,.025,'Unlisted device status is unknown; no precision or new untouched validation claimed. Home battery site loss has no rerouting or equipment replacement.\nEquipment sizing used these dates. Starting-charge cases can recharge before the critical event; they are not depleted-at-peak guarantees.',fontsize=10.5)
    fig.tight_layout(rect=(.02,.09,.98,.94),h_pad=4)
    for suffix in ['svg','png']:
        p=folder/f'cleargrid_final_evidence_limits.{suffix}';fig.savefig(p,dpi=300);outputs.append(p)
    plt.close(fig)
    return outputs

def main():
    DEST.mkdir(parents=True,exist_ok=True);plan=json.loads(PLAN.read_text())
    baseline,base,milestone,ids,x,times,valid,cap,rules_hash=input_data()
    np.save(DEST/'common_load.npy',x[:,valid])
    bench=benchmarks(plan);results,breaks=target_sweep(plan,base,x,times,valid)
    fin=finance(plan,base);export=export_check(base,x,valid,cap,breaks);oper=operating(plan,x,times,cap)
    outputs=figures(results,bench,fin,oper)
    result={'plan':plan,'screening_benchmarks':bench,'target_sweep':results,'annualized_cost_sensitivity':fin,'export_sensitivity':export,'operating_sensitivities':oper,'scope':'Supplemental retrospective analyses. Frozen rules and original historical figures/results preserved. Not new untouched reference validation or prospective field reliability.'}
    path=DEST/'final_analysis_results.json';path.write_text(json.dumps(result,indent=2))
    sources=[PLAN,ROOT/'src/final_analysis.py',ROOT/'src/model.py',ROOT/'src/causal_dispatch.py',RULES,baseline/'baseline_manifest.json',ROOT/'data/processed/milestone_screening/features_before_reference.csv',ROOT/'data/processed/milestone_screening/reference_split.csv',ROOT/'data/processed/four_design_replay/four_design_results.json']
    evidence=sorted(DEST.glob('*.csv'))+sorted(DEST.glob('target_*.json'))+[DEST/'common_load.npy']
    manifest={'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources},'output_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [path,*outputs,*evidence]}}
    (DEST/'final_analysis_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Final supplementary analyses complete:',path)

if __name__=='__main__':main()
