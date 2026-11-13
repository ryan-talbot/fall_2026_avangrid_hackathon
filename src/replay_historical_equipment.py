r"""Compare four frozen designs with the same causal July 1-4 replay.

Run: .\.venv\Scripts\python.exe src/replay_historical_equipment.py
No historical figure or prior validation artifact is rewritten.
"""
import json
import unittest
import numpy as np
import pandas as pd
from baseline import digest,preserve
from causal_dispatch import replay,POLICY
from final_validation import input_data,START,STOP,RECHARGE_STOP,DEST as PREVIOUS
from inventory import ROOT

DEST=ROOT/'data/processed/four_design_replay'
CONFIG=ROOT/'data/config/original_historical_fleet.json'
FULL_RECORD='sized with the full historical record'

def main():
    from test_causal_dispatch import CausalChecks
    if not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CausalChecks)).wasSuccessful():
        raise SystemExit(1)
    baseline_dir,base,_,ids,x,times,_,cap,_=input_data()
    previous=json.loads((PREVIOUS/'validation_results.json').read_text())
    small=json.loads((PREVIOUS/'frozen_equipment.json').read_text())
    if digest(PREVIOUS/'frozen_equipment.json')!=previous['frozen_equipment_sha256']:
        raise ValueError('Smaller-design equipment has changed since its test')
    if digest(ROOT/'src/causal_dispatch.py')!=small['controller_source_sha256']:
        raise ValueError('Controller differs from the smaller-design test')
    if json.loads((PREVIOUS/'online_policy.json').read_text())!=POLICY or cap!=small['cap_kw']:
        raise ValueError('Policy or fixed cap differs from the smaller-design test')
    figure_manifest=json.loads((PREVIOUS/'figure_manifest.json').read_text())
    protected={p:digest(ROOT/p) for p in figure_manifest['figure_sha256']}
    if protected!=figure_manifest['figure_sha256']:
        raise ValueError('Existing figure files differ from their recorded hashes')
    config=json.loads(CONFIG.read_text())
    placements=config['home_display_numbers']; modules_per_home=config['modules_per_home']
    if len(placements)!=3 or len(set(placements))!=3 or any(type(v) is not int or not 1<=v<=len(ids) for v in placements):
        raise ValueError('Exactly three distinct display placements are required')
    if modules_per_home!=2: raise ValueError('Original fleet uses two modules per site')
    units=np.zeros(len(ids),dtype=int); units[np.array(placements)-1]=modules_per_home
    home_energy=units*10.08; home_power=units*3.84
    historical=base['targets']['0.15']
    if not np.isclose(sum(historical['home']['energy_kwh']),home_energy.sum()) or not np.isclose(sum(historical['home']['power_kw']),home_power.sum()):
        raise ValueError('Original placements do not reproduce historical fleet totals')
    if not np.isclose(sum(historical['shared']['energy_kwh']),config['shared_energy_kwh']) or not np.isclose(sum(historical['shared']['power_kw']),config['shared_power_kw']):
        raise ValueError('Requested shared design differs from the historical 15% case')
    designs={}
    for name in ['shared','home']:
        r=small['equipment'][name]
        designs['smaller_'+name]={'option':name,'sizing_scope':'July 1-4 withheld from equipment sizing','energy_kwh':r['energy_kwh'],'power_kw':r['power_kw'],'sites':r['sites'],'units':r['units'],'cost':r['cost']}
    designs['historical_shared']={'option':'shared','sizing_scope':FULL_RECORD,'energy_kwh':[config['shared_energy_kwh']],'power_kw':[config['shared_power_kw']],'sites':[1],'cost':historical['shared']['cost']}
    designs['historical_home']={'option':'home','sizing_scope':FULL_RECORD,'energy_kwh':home_energy.tolist(),'power_kw':home_power.tolist(),'sites':(units>0).astype(int).tolist(),'units':units.tolist(),'home_display_numbers':placements,'cost':historical['home']['cost']}
    DEST.mkdir(parents=True,exist_ok=True)
    period=(times>=START)&(times<RECHARGE_STOP); rx=x[:,period]; rt=times[period]; scored=rt<STOP
    np.save(DEST/'showcase_ids.npy',ids); np.save(DEST/'measured_replay_load.npy',rx)
    frozen={'cap_kw':cap,'controller_source_sha256':small['controller_source_sha256'],'policy':POLICY,'original_placement_config_sha256':digest(CONFIG),'measured_load_sha256':digest(DEST/'measured_replay_load.npy'),'scored_start':str(START),'scored_stop_exclusive':str(STOP),'recharge_audit_stop_exclusive':str(RECHARGE_STOP),'scored_hours':int(scored.sum()),'designs':designs}
    (DEST/'equipment_frozen_for_replay.json').write_text(json.dumps(frozen,indent=2))
    equipment_hash=digest(DEST/'equipment_frozen_for_replay.json')
    results={}; rows=[]
    for key,design in designs.items():
        load=rx.sum(axis=0,keepdims=True) if design['option']=='shared' else rx
        r=replay(load,rt,cap,design['energy_kwh'],design['power_kw'],start_fraction=POLICY['starting_soc_fraction'],reserve=POLICY['reserve_fraction'],eta=POLICY['charge_efficiency'],score_mask=scored)
        summary=r['summary']
        results[key]={'design':design,**summary}
        rows.append({'design':key,'sizing_scope':design['sizing_scope'],'power_kw':sum(design['power_kw']),'energy_kwh':sum(design['energy_kwh']),'sites':sum(design['sites']),'hours_above_cap':summary['hours_above_cap'],'worst_miss_kw':summary['worst_miss_kw'],'result':'PASS' if summary['passes_observed_cap'] else 'FAIL'})
        observed=np.isfinite(rx).all(axis=0)
        total_load=np.full(len(rt),np.nan); total_grid=total_load.copy()
        total_load[observed]=load[:,observed].sum(axis=0); total_grid[observed]=r['grid'][:,observed].sum(axis=0)
        pd.DataFrame({'hour_start':rt,'scored_july1_4':scored,'complete_input':observed,'measured_load_kw':total_load,'simulated_causal_grid_kw':total_grid,'simulated_charge_kw':r['charge'].sum(axis=0),'simulated_discharge_kw':r['discharge'].sum(axis=0),'simulated_soc_start_kwh':r['soc_start'].sum(axis=0),'simulated_soc_end_kwh':r['soc_end'].sum(axis=0),'cap_kw':cap}).to_csv(DEST/f'{key}.csv',index=False)
        np.savez(DEST/f'{key}_site_audit.npz',load=load,grid=r['grid'],charge=r['charge'],discharge=r['discharge'],soc_start=r['soc_start'],soc_end=r['soc_end'])
        if key.startswith('smaller_'):
            old=previous['withheld']['options'][design['option']]
            if summary['hours_above_cap']!=old['hours_above_cap'] or not np.isclose(summary['worst_miss_kw'],old['worst_miss_kw'],rtol=0,atol=1e-9):
                raise RuntimeError('Smaller-design replay no longer reproduces the prior test')
        print(key,summary['hours_above_cap'],'hours above cap;',summary['worst_miss_kw'],'kW worst miss',flush=True)
    if digest(DEST/'equipment_frozen_for_replay.json')!=equipment_hash:
        raise RuntimeError('Equipment or placements changed during replay')
    if any(digest(ROOT/p)!=h for p,h in protected.items()):
        raise RuntimeError('An existing figure was modified')
    preserve()
    pd.DataFrame(rows).to_csv(DEST/'four_design_comparison.csv',index=False)
    output={'cap_kw':cap,'load_case':'Same unshifted AMI as the smaller-design test','scored_hours':int(scored.sum()),'missing_scored_hours':int((~np.isfinite(rx[:,scored]).all(axis=0)).sum()),'policy':POLICY,'frozen_equipment_sha256':equipment_hash,'historical_figures_unchanged':True,'protected_figure_sha256':protected,'sizing_caveat':'The larger designs are sized with the full historical record, including July 1-4. Their causal replay is not an independent equipment-sizing validation.','results':results}
    (DEST/'four_design_results.json').write_text(json.dumps(output,indent=2))
    lines=['# Four-design causal replay: July 1-4','',f'Fixed cap: {cap:.10f} kW. Same unshifted AMI, unchanged current-load/SOC-only controller, 100% starting charge, 20% reserve, sqrt(0.894) charge/discharge efficiency, headroom-based recharge at any hour, continuous SOC across midnight.','', '| Design | Equipment kW / kWh | Sizing scope | Hours above cap | Worst miss kW | Result |','|---|---|---|---:|---:|---|']
    for row in rows:
        lines.append(f"| {row['design']} | {row['power_kw']:.2f} / {row['energy_kwh']:.2f} | {row['sizing_scope']} | {row['hours_above_cap']} | {row['worst_miss_kw']:.6f} | {row['result']} |")
    lines+=['',f"Larger home fleet: original display placements {', '.join(map(str,placements))}, two modules each. The larger designs are **sized with the full historical record**; their sizing already used July 1-4. This replay evaluates the existing causal controller on those designs, not independent equipment-sizing generalization.",f"Scored hours: {int(scored.sum())}; missing scored hours: {output['missing_scored_hours']}. July 5 00:00-06:00 remains an unscored recharge audit, identical to the smaller-design test.",'','## Recharge by 06:00','', '| Design | Night start | All installed batteries full at 06:00 |','|---|---|---|']
    for key,value in results.items():
        for night in value['overnight_recharge']: lines.append(f"| {key} | {night['night_start']} | {night['all_sites_full_at_0600']} |")
    lines+=['','Existing historical dispatch and cost figures, and the prior validation outputs, were preserved. All existing figure hashes are unchanged.','', '```powershell',r'.\.venv\Scripts\python.exe src/replay_historical_equipment.py','```']
    (DEST/'four_design_summary.md').write_text('\n'.join(lines)+'\n')
    print('Comparison saved:',DEST/'four_design_summary.md')

if __name__=='__main__': main()
