"""Aggregate review report from local model outputs (no customer IDs)."""
import json
import numpy as np
import pandas as pd
from inventory import ROOT
from model import home_cost_bound, dispatch

def report(dest=None):
    dest=dest or ROOT/'data/processed'
    r=json.loads((dest/'showcase_results.json').read_text())
    a=np.load(ROOT/'data/processed/ami.npy',mmap_mode='r')
    x=np.asarray(a[np.load(dest/'showcase_ids.npy'),6552:],float)
    valid=np.isfinite(x).all(axis=0)
    times=pd.date_range('2026-06-01',periods=2208,freq='h')[valid]
    breaks=np.flatnonzero((times[1:]-times[:-1])!=pd.Timedelta(hours=1))+1
    x=x[:,valid]
    lines=['# Checkpoint results','',
           'Measured AMI; simulated perfect-foresight storage; assumed installed costs.',
           f"Summer peak: {r['summer_peak_kw']:.6f} kW; diversity: {r['summer_diversity']:.6f}.",
           f"Common complete hours: {r['summer_hours']}/2208; no feasibility claim for missing hours.",'',
           '| Target | Cap kW | Option | kW | kWh | Sites | Assumed cost | Solver status | Gap | Max cap miss kW |',
           '|---|---:|---|---:|---:|---:|---:|---|---:|---:|']
    for target,case in r['targets'].items():
        bound=home_cost_bound(x,case['cap_kw'])
        cost_bound=bound['cost']
        for name in ['shared','home']:
            v=case[name]
            if not v['feasible']:
                lines.append(f"| {float(target):.0%} | {case['cap_kw']:.6f} | {name} | - | - | - | - | {v['status']} | - | - |")
                continue
            sites=1 if name=='shared' else sum(v['sites'])
            lines.append(f"| {float(target):.0%} | {case['cap_kw']:.6f} | {name} | {sum(v['power_kw']):.2f} | {sum(v['energy_kwh']):.2f} | {sites} | ${v['cost']:,} | {v['status']} | {v['mip_gap']:.6f} | {v['max_cap_miss_kw']:.3g} |")
            if name=='home':
                v['power_based_cost_lower_bound']=cost_bound
                v['cost_certified_by_power_bound']=v['cost']==cost_bound
                v['necessary_equipment_bound']=bound
                if v['cost']!=cost_bound:
                    # Relax all home restrictions into one high-power store.
                    # If one fewer module is infeasible even there, no home
                    # placement with that total energy can meet the same cap.
                    fewer_modules=int(sum(v['units']))-1
                    relaxed_power=max(7.68*len(x),2*max(r['summer_peak_kw'],case['cap_kw']))
                    relaxed=dispatch(x.sum(axis=0),case['cap_kw'],energy=[fewer_modules*10.08],power=[relaxed_power],breaks=breaks)
                    v['aggregate_energy_bound_check']={'modules_tested':fewer_modules,'energy_kwh':fewer_modules*10.08,'power_kw':relaxed_power,'solver_status':relaxed['status'],'feasible':relaxed['feasible']}
                    if relaxed['status']==2:
                        minimum_modules=max(bound['modules'],fewer_modules+1)
                        minimum_sites=max(bound['sites'],int(np.ceil(minimum_modules/2)))
                        v['necessary_equipment_bound']={'modules':minimum_modules,'sites':minimum_sites,'cost':8500*minimum_modules+3000*minimum_sites}
                v['cost_certified_by_necessary_bounds']=v['cost']==v['necessary_equipment_bound']['cost']
            if name=='shared':
                # Shared MILP auxiliary integers represent power steps, not sites.
                v['sites']=[1]
                v['energy_steps']=[int(round(sum(v['energy_kwh'])/5))]
                v['power_steps']=[int(round(sum(v['power_kw'])/2.5))]
            f=pd.read_csv(dest/f'dispatch_{float(target):.0%}_{name}.csv',parse_dates=['hour_start'])
            misses=f.simulated_grid_kw-f.cap_kw
            v['cap_miss_hours_over_1e_6_kw']=int((misses>1e-6).sum())
            july=f[(f.hour_start>='2026-07-03')&(f.hour_start<'2026-07-04')]
            v['july3_discharge_kwh']=float(july.simulated_discharge_kw.sum())
            v['july3_charge_kwh']=float(july.simulated_charge_kw.sum())
        if case['shared']['feasible'] and case['home']['feasible']:
            difference=case['shared']['cost']-case['home']['cost']
            case['cost_comparison']={'shared_minus_home_assumed_cost':difference,'cheaper':'home' if difference>0 else 'shared' if difference<0 else 'tie'}
    lines+=['','Status 0 = solver optimal within tolerance or equipment cost certified by a feasible dispatch at a necessary count bound; status 1 = time limit (feasible incumbent if shown).',
            'Home cost certification uses rounded power/site bounds and, when needed, an aggregate energy relaxation: a high-power shared store with one fewer module must be proven infeasible. A feasible home design at the necessary cost bound certifies equipment cost independently of the MILP gap.',
            '', '## Input provenance',r['sampling']]
    if r.get('expected_input_checks'):
        for key,value in r['expected_input_checks'].items():
            lines.append(f"{key}: expected {value['expected']}; measured {value['actual']}; {'PASS' if value['passed'] else 'FAIL'}.")
    else:
        lines.append('The default random draw does not reproduce the prior group; use the explicit local ID-list override to replay it.')
    lines+=['Results concern unshifted load, not the prior 50% flexible-load scenario. They do not establish held-out weather performance.']
    for target,case in r['targets'].items():
        if 'cost_comparison' in case:
            comparison=case['cost_comparison']
            lines.append(f"{float(target):.0%}: {comparison['cheaper']} is cheaper; shared minus home assumed cost = ${comparison['shared_minus_home_assumed_cost']:,}.")
    text='\n'.join(lines)+'\n'
    (dest/'checkpoint_summary.md').write_text(text)
    (dest/'showcase_results.json').write_text(json.dumps(r,indent=2))
    print(text)

if __name__=='__main__': report()
