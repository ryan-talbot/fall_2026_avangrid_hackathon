r"""Freeze equipment without July 1-4, replay causally, generate deck figures.

Run: .\.venv\Scripts\python.exe src/final_validation.py
"""
import json
import unittest
import numpy as np
import pandas as pd
from baseline import preserve,digest
from inventory import ROOT
from load_data import load
from model import dispatch,home_design
from screening import RULES
from showcase import serial
from causal_dispatch import replay,POLICY

DEST=ROOT/'data/processed/final_validation'
START=pd.Timestamp('2026-07-01')
STOP=pd.Timestamp('2026-07-05')
RECHARGE_STOP=pd.Timestamp('2026-07-05 06:00')

def gaps(times,valid):
    missing=np.flatnonzero(~np.asarray(valid))
    if not len(missing): return []
    runs=np.split(missing,np.flatnonzero(np.diff(missing)!=1)+1)
    return [{'first_hour_start':str(times[v[0]]),'last_hour_start':str(times[v[-1]]),'hours':len(v)} for v in runs]

def input_data():
    baseline_dir=preserve(); base=json.loads((baseline_dir/'showcase_results.json').read_text())
    screen_dir=ROOT/'data/processed/milestone_screening'
    freeze=json.loads((screen_dir/'rules_frozen.json').read_text())
    screening=json.loads((screen_dir/'screening_summary.json').read_text())
    if digest(RULES)!=freeze['rules_sha256'] or screening['rules_sha256']!=freeze['rules_sha256']:
        raise ValueError('Current rules differ from the frozen reference evaluation')
    if digest(screen_dir/'features_before_reference.csv')!=screening['features_sha256_before_reference']:
        raise ValueError('Frozen screening features have changed')
    milestone=json.loads((screen_dir/'milestone_results.json').read_text())
    if milestone['baseline_manifest_sha256']!=digest(baseline_dir/'baseline_manifest.json') or milestone['rules_sha256']!=freeze['rules_sha256']:
        raise ValueError('Historical milestone provenance does not match the baseline and rules')
    ids=np.load(baseline_dir/'showcase_ids.npy'); a,counts=load()
    if not np.all(counts[ids]>=.995*8760): raise ValueError('Original group no longer meets the annual screen')
    x=np.asarray(a[ids,6552:],float)
    times=pd.date_range('2026-06-01',periods=2208,freq='h'); valid=np.isfinite(x).all(axis=0)
    old=pd.read_csv(baseline_dir/'dispatch_15%_shared.csv',parse_dates=['hour_start'])
    if not pd.DatetimeIndex(old.hour_start).equals(times[valid]) or not np.allclose(old.measured_load_kw,x[:,valid].sum(axis=0),atol=1e-6,rtol=0):
        raise ValueError('Measured load differs from the preserved verified showcase')
    cap=float(base['targets']['0.15']['cap_kw'])
    if not np.isclose(cap,68.13005,atol=1e-6,rtol=0): raise ValueError('Unexpected scenario cap')
    return baseline_dir,base,milestone,ids,x,times,valid,cap,freeze['rules_sha256']

def size_and_freeze(x,times,valid,cap,rules_hash):
    holdout=(times>=START)&(times<STOP)
    train=valid&~holdout
    if np.any(holdout&train): raise AssertionError('Withheld rows entered sizing')
    tx=x[:,train]; tt=times[train]
    breaks=np.flatnonzero((tt[1:]-tt[:-1])!=pd.Timedelta(hours=1))+1
    (DEST/'online_policy.json').write_text(json.dumps(POLICY,indent=2))
    np.save(DEST/'training_load.npy',tx)
    pd.DataFrame({'hour_start':tt}).to_csv(DEST/'training_hours.csv',index=False)
    print(f'Sizing on {train.sum()} complete hours; July 1-4 excluded; fixed cap {cap:.10f} kW',flush=True)
    shared=dispatch(tx.sum(axis=0),cap,optimize='shared',breaks=breaks)
    print('Training shared:',serial(shared),flush=True)
    home=home_design(tx,cap,breaks=breaks)
    print('Training homes:',serial(home),flush=True)
    designs={'shared':shared,'home':home}
    for name,r in designs.items():
        if not r['feasible']: raise RuntimeError(f'No feasible training {name} design; status {r["status"]}')
        pd.DataFrame({'hour_start':tt,'measured_group_load_kw':tx.sum(axis=0),'simulated_training_grid_kw':r['grid'].sum(axis=0),'simulated_charge_kw':r['charge'].sum(axis=0),'simulated_discharge_kw':r['discharge'].sum(axis=0),'simulated_soc_kwh':r['soc'].sum(axis=0),'cap_kw':cap}).to_csv(DEST/f'training_{name}.csv',index=False)
    artifact={'cap_kw':cap,'target_policy':'Externally fixed original summer cap; never recomputed from training peak','load_case':'Measured unshifted AMI; no perfect-foresight managed-charging schedule used in the held-out test','withheld_start':str(START),'withheld_stop_exclusive':str(STOP),'training_complete_hours':int(train.sum()),'training_peak_kw':float(tx.sum(axis=0).max()),'training_load_sha256':digest(DEST/'training_load.npy'),'training_hours_sha256':digest(DEST/'training_hours.csv'),'screening_rules_sha256':rules_hash,'online_policy_sha256':digest(DEST/'online_policy.json'),'controller_source_sha256':digest(ROOT/'src/causal_dispatch.py'),'sizing_source_sha256':digest(ROOT/'src/model.py'),'missing_summer_hours':gaps(times,valid),'sizing_boundaries':'Existing perfect-foresight sizing: full SOC at start/end of each contiguous complete training segment; no transfer across omitted days or missing hours','equipment':{k:serial(v) for k,v in designs.items()}}
    (DEST/'frozen_equipment.json').write_text(json.dumps(artifact,indent=2))
    # No withheld load is passed to the sizing routines or used to revise them.
    return artifact,digest(DEST/'frozen_equipment.json')

def heldout_replay(frozen,equipment_hash,x,times,valid):
    period=(times>=START)&(times<RECHARGE_STOP)
    rx=x[:,period]; rt=times[period]; scored=rt<STOP
    results={}
    for name,design in frozen['equipment'].items():
        load=rx.sum(axis=0,keepdims=True) if name=='shared' else rx
        # np.sum propagates any missing household observation to the shared row.
        r=replay(load,rt,frozen['cap_kw'],design['energy_kwh'],design['power_kw'],score_mask=scored)
        summary=r['summary']
        summary.update(equipment_sha256=equipment_hash,energy_kwh=design['energy_kwh'],power_kw=design['power_kw'],units=design['units'],sites=design['sites'],assumed_installed_cost=design['cost'])
        results[name]=summary
        total_load=np.full(len(rt),np.nan); total_grid=total_load.copy()
        total_load[r['valid']]=load[:,r['valid']].sum(axis=0)
        total_grid[r['valid']]=r['grid'][:,r['valid']].sum(axis=0)
        pd.DataFrame({'hour_start':rt,'scored_july1_4':scored,'complete_input':r['valid'],'measured_load_kw':total_load,'simulated_causal_grid_kw':total_grid,'simulated_charge_kw':r['charge'].sum(axis=0),'simulated_discharge_kw':r['discharge'].sum(axis=0),'simulated_soc_start_kwh':r['soc_start'].sum(axis=0),'simulated_soc_end_kwh':r['soc_end'].sum(axis=0),'cap_kw':frozen['cap_kw']}).to_csv(DEST/f'withheld_{name}.csv',index=False)
        np.savez(DEST/f'withheld_{name}_site_audit.npz',load=load,grid=r['grid'],charge=r['charge'],discharge=r['discharge'],soc_start=r['soc_start'],soc_end=r['soc_end'])
        print('Withheld causal replay',name,json.dumps(summary),flush=True)
    if digest(DEST/'frozen_equipment.json')!=equipment_hash or digest(ROOT/'src/causal_dispatch.py')!=frozen['controller_source_sha256']:
        raise RuntimeError('Equipment or placements changed after test replay')
    return {'start':str(START),'stop_exclusive':str(STOP),'recharge_audit_extension_stop_exclusive':str(RECHARGE_STOP),'scored_expected_hours':int(scored.sum()),'test_gaps':gaps(rt[scored],np.isfinite(rx[:,scored]).all(axis=0)),'recharge_extension_gaps':gaps(rt[~scored],np.isfinite(rx[:,~scored]).all(axis=0)),'options':results}

def report(frozen,heldout,figures):
    lines=['# ClearGrid final validation','',
           f"Fixed cap: {frozen['cap_kw']:.10f} kW (displayed 68.13005). Training uses measured, unshifted load, excluding all July 1-4 hours. Frozen screening rules are unchanged; this tests storage generalization, not a new temporal validation of appliance classification.",
           f"Training complete hours: {frozen['training_complete_hours']}; training peak: {frozen['training_peak_kw']:.6f} kW. Missing summer data: {json.dumps(frozen['missing_summer_hours'])}.",
           f"Held-out scored hours: {heldout['scored_expected_hours']}; gaps: {json.dumps(heldout['test_gaps'])}. July 5 00:00-06:00 is a recharge audit only, outside held-out cap scoring; gaps: {json.dumps(heldout['recharge_extension_gaps'])}.",
           '', '## Frozen equipment and causal withheld results','',
           '| Option | kW / kWh | Sites | Assumed installed cost | Hours above cap | Worst miss kW | Outcome |',
           '|---|---|---:|---:|---:|---:|---|']
    for name,r in heldout['options'].items():
        lines.append(f"| {name} | {sum(r['power_kw']):.2f} / {sum(r['energy_kwh']):.2f} | {sum(r['sites'])} | ${r['assumed_installed_cost']:,} | {r['hours_above_cap']} | {r['worst_miss_kw']:.6f} | {'PASS' if r['passes_observed_cap'] else 'FAIL'} |")
    lines+=['','Equipment and placements are written and hashed before replay. The hash is verified afterward. Both options start at 100% of their own rated energy, retain 20% reserve, and use sqrt(0.894) charge/discharge efficiency. No final-charge requirement, daily reset, forecast, future load, weather or future charging schedule is used during the replay.',
            'At each hour: if group load exceeds cap, discharge only the deficit, limited by available energy, power and each home\'s no-export bound; allocate proportionally to available AC energy with saturation. Otherwise charge from the grid using present cap headroom, site power and capacity room, proportionally to missing energy. Charging is allowed whenever headroom exists, including overnight. The hourly model assumes the current hourly-average load is observable for that step.',
            'Across any input gap, SOC is carried unchanged with no modeled flow and no claim of cap feasibility. Actual test-period gaps are reported above.',
            '', '## Overnight recharge (SOC at 06:00)','',
            '| Option | Night start | Complete data | All installed sites full at 06:00 | SOC fraction | Started full |',
            '|---|---|---|---|---:|---|']
    for name,r in heldout['options'].items():
        for night in r['overnight_recharge']:
            lines.append(f"| {name} | {night['night_start']} | {night['complete_input_window']} | {night['all_sites_full_at_0600']} | {night['soc_fraction_at_0600']:.6f} | {night['started_full']} |")
    lines+=['','July 1 starts full by assumption. July 2-4 nights follow uninterrupted scored replay. July 5 audits recharge after the final withheld day and is not included in cap-miss counts.',
            '', '## Figure provenance','',
            'The historical July 3 chart and 10%/15% installed-cost comparison use the preserved verified full-summer perfect-foresight model outputs. They are hindsight historical feasibility/sizing, not held-out performance. The heat-wave chart uses only the frozen-equipment causal replay CSVs. All costs are scenario assumptions; no bill savings, program costs or infrastructure-deferral value is verified.']
    for name,paths in figures.items(): lines.append(f"- {name}: "+'; '.join(str(p.relative_to(ROOT)) for p in paths))
    lines+=['','## Slide-ready summary','']
    for name,r in heldout['options'].items():
        lines.append(f"- With July 1-4 withheld, {name} sizing chose {sum(r['power_kw']):.2f} kW / {sum(r['energy_kwh']):.2f} kWh across {sum(r['sites'])} sites (${r['assumed_installed_cost']:,}, assumed). Causal replay {'missed' if not r['passes_observed_cap'] else 'met'} the 68.13 kW cap: {r['hours_above_cap']} miss hours; worst {r['worst_miss_kw']:.3f} kW.")
    lines+=['- Full-summer historical sizing and held-out chronological performance must appear as separate results in the deck.',
            '', '```powershell',r'.\.venv\Scripts\python.exe src/final_validation.py','```']
    (DEST/'validation_summary.md').write_text('\n'.join(lines)+'\n')

def main():
    from test_model import HandCases
    from test_screening_managed import ScreeningManagedChecks
    from test_causal_dispatch import CausalChecks
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [HandCases,ScreeningManagedChecks,CausalChecks])
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful(): raise SystemExit(1)
    DEST.mkdir(parents=True,exist_ok=True)
    baseline_dir,base,milestone,ids,x,times,valid,cap,rules_hash=input_data()
    np.save(DEST/'showcase_ids.npy',ids)
    frozen,equipment_hash=size_and_freeze(x,times,valid,cap,rules_hash)
    heldout=heldout_replay(frozen,equipment_hash,x,times,valid)
    from deck_figures import generate
    paths=generate(DEST,baseline_dir,base,milestone,heldout)
    result={'labels':{'measured':'Hourly AMI, synthetic group','historical':'Perfect-foresight full-summer sizing/dispatch','heldout':'Frozen equipment and placements; current-load/SOC-only hourly replay','cost':'Assumed installed storage prices'},'baseline_manifest_sha256':digest(baseline_dir/'baseline_manifest.json'),'rules_sha256':rules_hash,'frozen_equipment_sha256':equipment_hash,'training':frozen,'withheld':heldout,'figures':{name:[str(v.relative_to(ROOT)) for v in values] for name,values in paths.items()}}
    (DEST/'validation_results.json').write_text(json.dumps(result,indent=2))
    report(frozen,heldout,paths)
    preserve()
    print('Final validation complete:',DEST/'validation_summary.md',flush=True)

if __name__=='__main__': main()
