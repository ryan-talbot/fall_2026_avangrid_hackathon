r"""ClearGrid screening, offer routing, and 50% managed-charging comparison.

Run from the repo root: .\.venv\Scripts\python.exe src/milestone.py
All restricted inputs and customer-level outputs stay in ignored data/.
"""
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from baseline import preserve,digest
from inventory import ROOT
from load_data import load
from screening import screen
from managed_charging import build_jobs,schedule
from model import dispatch,home_design,diversity
from showcase import serial

DEST=ROOT/'data/processed/milestone_screening'

def cap_metrics(total,cap):
    violation=np.maximum(np.asarray(total)-cap,0)
    return {'peak_kw':float(np.max(total)),'cap_miss_hours':int((violation>1e-6).sum()),'max_cap_miss_kw':float(violation.max()),'cap_miss_kwh':float(violation.sum()),'feasible':bool(violation.max()<=1e-6)}

def load_events(path,ids):
    events=[]
    for part in pd.read_csv(path,chunksize=100000):
        events.extend(part.loc[part.CUSTOMER_NUMBER.isin(ids)].to_dict('records'))
    return events

def write_summary(dest,result,screening_summary,offers):
    schedule_info=result['managed_charging']
    lines=['# ClearGrid: screening, offers and managed charging','',
           'Measured inputs: hourly AMI and weather; synthetic 30-home group. Screening components and managed charging are estimated/simulated. All installed prices are assumptions.',
           f"Frozen rules: {screening_summary['rules_sha256']}. No EV/HP reference IDs were used to tune rules. Evidence scores are not probabilities.",'',
           '## Held-out reference recovery at fixed outreach sizes','',
           '| Reference | Outreach K | Qualifying held-out IDs | Recovered | Recovery |',
           '|---|---:|---:|---:|---:|']
    for name,value in screening_summary['reference_recovery'].items():
        if name=='cooling': continue
        lines.append(f"| {name} | {value['fixed_K']} | {value['qualifying_heldout_count']} / {value['heldout_reference_count']} total held-out | {value['heldout_recovered']} | {value['recovery_of_qualifying_heldout']:.1%} |")
    lines+=['','The held-out split is deterministic 50/50 by salted ID hash. The other half is unused for tuning. Outreach is ranked across the entire qualifying population at the fixed K, including any unused-development references. Unlisted IDs are unknown, not negatives. These recovery rates do not estimate precision, specificity or ownership prevalence. HP recovery tests broad weather-sensitive heating, not HP identification. No cooling reference list exists.',
            f"Population: {screening_summary['qualifying_population']:,}; broad EV-like leads: {screening_summary['ev_candidates']:,}; heating: {screening_summary['heating_candidates']:,}; cooling: {screening_summary['cooling_candidates']:,}; qualifying known PV: {screening_summary['known_pv_qualifying']:,}.",
            'The broad EV-like screen can also select other recurring appliances; use ranked outreach for confirmation, not automatic enrollment. Heat pump vs resistance, EV L1/L2, water heaters, pools, hot tubs and battery ownership remain uncertain.',
            '', '## Same 30 homes, same original 15% cap','',
            f"Cap: {result['cap_kw']:.8f} kW; complete common summer hours: {result['summer_hours']}/2208. The unshifted baseline is preserved with SHA-256 hashes in data/processed/baseline_unshifted_v1/.",
            f"Assumed movable fraction: 50% of estimated components for eligible EV-like homes. Availability starts at first detected arrival, ends at assumed 06:00 ready-by; charging energy is conserved per night and household. No shifts across incomplete or boundary windows.",
            f"Managed-charging offers in showcase: {schedule_info['eligible_showcase_homes']}; complete night jobs: {schedule_info['jobs']}; eligible estimated EV-like component: {schedule_info['estimated_ev_component_kwh_in_eligible_complete_jobs']:.4f} kWh; mobile allowance: {schedule_info['mobile_energy_kwh']:.4f} kWh; actually shifted (one-way): {schedule_info['shifted_kwh']:.6f} kWh over the full observed summer.",
            f"Household energy error: {schedule_info['max_household_energy_error_kwh']:.3g} kWh; per-job error by ready-by: {schedule_info['max_job_energy_error_kwh']:.3g} kWh. New cap-miss hours: {schedule_info['new_cap_miss_hours']}; new summer peak created: {schedule_info['new_peak_created']}.",
            f"July 3 original cap-exceedance event: {schedule_info['july3_sizing_hours']}. Removed energy in those hours: {schedule_info['july3_sizing_removed_kwh']:.6f} kWh. July 3 peak-hour change: {schedule_info['july3_peak_hour_net_reduction_kw']:.6f} kW. July 3 whole-day removed energy: {schedule_info['july3_day_removed_kwh']:.6f} kWh.",
            f"Actual shifting occurs on {schedule_info['shifted_calendar_days']} summer dates. The brief reports 26.75 kWh over seven days; current full-summer shifted energy differs by {schedule_info['difference_from_prior_shift_kwh']:.6f} kWh. The prior flexible-component and scheduling rules were not supplied; current frozen rules do not reproduce that movement amount. Storage sizes and costs do reproduce. No particular seven-day calendar window is assumed for that prior result.",
            '', '| Option | Peak kW | Miss hours | Max miss kW | kW / kWh / sites | Assumed installed storage cost |',
            '|---|---:|---:|---:|---|---:|']
    for name,option in result['options'].items():
        equipment='0 / 0 / 0' if name=='managed_charging_alone' else f"{sum(option['power_kw']):.2f} / {sum(option['energy_kwh']):.2f} / {sum(option['sites'])}"
        lines.append(f"| {name} | {option['peak_kw']:.6f} | {option['cap_miss_hours']} | {option['max_cap_miss_kw']:.6f} | {equipment} | ${option['cost']:,} |")
    lines+=['','Managed-charging alone has $0 battery hardware, not $0 total program cost. Control software, incentives, enrollment, and customer participation costs are not supplied. No verified bill saving or infrastructure-deferral value is claimed.',
            'Both battery designs use the exact same shifted load, original cap, 20% reserve, symmetric sqrt(0.894) efficiency, hourly limits, grid charging, and full SOC at contiguous observed-window boundaries. Home no-export remains enforced. No feasibility claim covers missing hours or held-out weather.',
            f"Baseline preferred feasible battery option: {result['baseline_preferred']}; managed-charging scenario preferred feasible option: {result['scenario_preferred']}; changed: {result['preferred_option_changed']}.",
            '', '## Local deliverables','',
            '- customer_to_offer.csv: all qualifying customers, evidence scores, reasons and uncertain types.',
            '- showcase_customer_to_offer.csv / showcase_offers.md: same 30 homes in supplied order, plus selected simulated battery units.',
            '- reference_split.csv, ev_outreach.csv, hp_outreach.csv, cooling_outreach.csv: audit of frozen evaluation.',
            '- managed_charging_jobs.csv: arrival, deadline, energy conservation, movement and power per night.',
            '- managed_loads.csv, shifted_load.npy, dispatch_managed_home.csv, dispatch_managed_shared.csv: measured/simulated load, SOC and dispatch.',
            '- managed_dispatch_july3.png, installed_storage_costs.png: figures generated from these outputs.',
            '', '## Rerun','', '```powershell',r'.\.venv\Scripts\python.exe src/milestone.py','```']
    (dest/'milestone_summary.md').write_text('\n'.join(lines)+'\n')
    short=['# Showcase customer-to-offer table','', 'Evidence scores are 0-100 indices, not probabilities. All unresolved appliance subtypes and battery ownership remain uncertain. Full reasons and anonymized IDs are in the local CSV.', '', '| Display home | EV / heat / cool scores | PV | Offers | Evidence |', '|---:|---|---|---|---|']
    for _,row in offers.iterrows():
        names=[label for flag,label in [('managed_charging_offer','managed charging'),('thermostat_offer','thermostat'),('home_battery_offer','home battery'),('export_eligibility_offer','export check')] if row[flag]]
        evidence=f"{row.ev_event_count} plateaus / {row.ev_recurring_months} months; heat/cool partial R2 {row.heating_partial_r2:.2f}/{row.cooling_partial_r2:.2f}; residual evening {row.screened_residual_evening_mean_kw:.2f} kW"
        short.append(f"| {row.display_home} | {row.ev_score:.1f} / {row.heating_score:.1f} / {row.cooling_score:.1f} | {row.pv_status} | {', '.join(names) or 'uncertain'} | {evidence} |")
    (dest/'showcase_offers.md').write_text('\n'.join(short)+'\n')

def figures(dest,times,original,shifted,cap,dispatches,baseline):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    view=(times>='2026-07-03')&(times<'2026-07-05')
    fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
    axes[0].plot(times[view],original.sum(axis=0)[view],color='black',label='Measured AMI sum')
    axes[0].plot(times[view],shifted.sum(axis=0)[view],label='Simulated managed charging')
    for name,r in dispatches.items():
        if not r['feasible']: continue
        axes[1].plot(times[view],r['grid'].sum(axis=0)[view],label=f'Simulated managed + {name}')
        axes[2].plot(times[view],r['soc'].sum(axis=0)[view],label=f'Simulated {name} SOC')
    for ax in axes[:2]: ax.axhline(cap,color='red',ls='--',label='Original 15% cap'); ax.set_ylabel('Hourly average kW')
    axes[2].set_ylabel('Internal stored energy kWh')
    for ax in axes: ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.suptitle('Same 30 homes: measured load and simulated 50% estimated EV flexibility\n06:00 assumed ready-by; 20% storage reserve; 89.4% round-trip efficiency')
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(dest/'managed_dispatch_july3.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5)); labels=[]; values=[]
    for label,name in [('Shared','shared'),('Homes','home')]:
        for condition,data in [('Unshifted',baseline['targets']['0.15'][name]),('Managed',dispatches[name])]:
            if data['feasible']: labels.append(f'{label}\n{condition}'); values.append(data['cost'])
    bars=ax.bar(labels,values,color=['#376b9b','#7aa9ce','#a86a32','#dab38d'][:len(values)])
    for bar,value in zip(bars,values): ax.text(bar.get_x()+bar.get_width()/2,value+700,f'${value:,.0f}',ha='center')
    ax.set_ylim(0,max(values)*1.18); ax.set_ylabel('Assumed installed storage cost ($)')
    ax.set_title('15% cap: feasible storage designs\nManaged-program costs not supplied; no bill savings claimed')
    fig.tight_layout(); fig.savefig(dest/'installed_storage_costs.png',dpi=150); plt.close(fig)

def main():
    from test_model import HandCases
    from test_screening_managed import ScreeningManagedChecks
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(HandCases),unittest.defaultTestLoader.loadTestsFromTestCase(ScreeningManagedChecks)])
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful(): raise SystemExit(1)
    baseline_dir=preserve(); baseline=json.loads((baseline_dir/'showcase_results.json').read_text())
    features,screening_summary,rules=screen(DEST)
    ids=np.load(baseline_dir/'showcase_ids.npy'); a,counts=load(); annual=np.asarray(a[ids],float)
    events=load_events(DEST/'ev_events.csv',ids)
    original,times,jobs,context=build_jobs(annual,ids,features,events,rules)
    if len(times)!=baseline['summer_hours'] or not np.isclose(original.sum(axis=0).max(),baseline['summer_peak_kw'],rtol=0,atol=1e-6) or not np.isclose(diversity(original),baseline['summer_diversity'],rtol=0,atol=1e-6):
        raise ValueError('Original showcase no longer matches preserved measured baseline')
    baseline_hourly=pd.read_csv(baseline_dir/'dispatch_15%_shared.csv',parse_dates=['hour_start'])
    if not pd.DatetimeIndex(baseline_hourly.hour_start).equals(times) or not np.allclose(original.sum(axis=0),baseline_hourly.measured_load_kw,rtol=0,atol=1e-6):
        raise ValueError('Full measured load trace differs from the preserved unshifted baseline')
    cap=baseline['targets']['0.15']['cap_kw']
    shifted,metrics,audit=schedule(original,times,jobs,cap)
    metrics={**context,**metrics}
    removed=np.maximum(original-shifted,0).sum(axis=0)
    jul3=times.date==pd.Timestamp('2026-07-03').date(); sizing=jul3&(original.sum(axis=0)>cap+1e-6)
    peak_index=int(np.argmax(original.sum(axis=0)))
    week=(times>='2026-07-01')&(times<'2026-07-08')
    metrics.update(july3_sizing_hours=[str(t) for t in times[sizing]],july3_sizing_removed_kwh=float(removed[sizing].sum()),july3_peak_hour_net_reduction_kw=float((original-shifted).sum(axis=0)[peak_index]),july3_day_removed_kwh=float(removed[jul3].sum()),july1_7_shifted_kwh=float(removed[week].sum()),shifted_calendar_days=len(set(times[removed>1e-6].date)),difference_from_prior_shift_kwh=float(metrics['shifted_kwh']-26.75))
    np.save(DEST/'showcase_ids.npy',ids); np.save(DEST/'measured_showcase_load.npy',original); np.save(DEST/'shifted_load.npy',shifted)
    pd.DataFrame([{'display_home':v['home_index']+1,'CUSTOMER_NUMBER':int(ids[v['home_index']]),**v} for v in audit]).to_csv(DEST/'managed_charging_jobs.csv',index=False)
    pd.DataFrame({'hour_start':times,'measured_load_kw':original.sum(axis=0),'simulated_managed_load_kw':shifted.sum(axis=0),'cap_kw':cap,'simulated_removed_kwh':removed}).to_csv(DEST/'managed_loads.csv',index=False)
    breaks=np.flatnonzero((times[1:]-times[:-1])!=pd.Timedelta(hours=1))+1
    print('Managed-charging audit:',json.dumps(metrics),flush=True)
    shared=dispatch(shifted.sum(axis=0),cap,optimize='shared',breaks=breaks)
    print('Managed + shared:',serial(shared),flush=True)
    home=home_design(shifted,cap,breaks=breaks)
    print('Managed + homes:',serial(home),flush=True)
    dispatches={'shared':shared,'home':home}; options={}
    alone=cap_metrics(shifted.sum(axis=0),cap); alone['cost']=0; alone['storage_only_cost']=True
    options['managed_charging_alone']=alone
    for name,r in dispatches.items():
        if not r['feasible']: raise RuntimeError(f'No feasible {name} design; solver status {r["status"]}')
        options['managed_plus_'+name]={**serial(r),**cap_metrics(r['grid'].sum(axis=0),cap),'same_shifted_load_sha256':digest(DEST/'shifted_load.npy')}
        pd.DataFrame({'hour_start':times,'simulated_managed_load_kw':shifted.sum(axis=0),'simulated_grid_kw':r['grid'].sum(axis=0),'simulated_charge_kw':r['charge'].sum(axis=0),'simulated_discharge_kw':r['discharge'].sum(axis=0),'simulated_soc_kwh':r['soc'].sum(axis=0),'cap_kw':cap}).to_csv(DEST/f'dispatch_managed_{name}.csv',index=False)
    costs={name:r['cost'] for name,r in options.items() if r['feasible']}
    preferred=min(costs,key=costs.get)
    base_preferred=min(['home','shared'],key=lambda k:baseline['targets']['0.15'][k]['cost'])
    result={'labels':{'measured':'AMI and weather, synthetic group','estimated':'EV-like component and evidence scores','simulated':'50% movable component and storage dispatch, perfect foresight','assumed_cost':'Storage installed cost only; managed-program cost unknown'},'baseline_manifest_sha256':digest(baseline_dir/'baseline_manifest.json'),'measured_load_sha256':digest(DEST/'measured_showcase_load.npy'),'rules_sha256':screening_summary['rules_sha256'],'cap_kw':cap,'summer_hours':len(times),'managed_charging':metrics,'unshifted_cap_metrics':cap_metrics(original.sum(axis=0),cap),'options':options,'baseline_preferred':base_preferred,'scenario_preferred':preferred,'preferred_option_changed':preferred!='managed_plus_'+base_preferred}
    offers=features.set_index('CUSTOMER_NUMBER').loc[ids].reset_index()
    offers.insert(0,'display_home',np.arange(1,len(ids)+1))
    offers['battery_profile_screen_offer']=offers.home_battery_offer
    evening=np.isin(times.hour,rules['offers']['peak_hours'])
    offers['simulated_residual_evening_mean_kw']=shifted[:,evening].mean(axis=1)
    offers['simulated_residual_evening_p90_kw']=np.percentile(shifted[:,evening],90,axis=1)
    offers['simulated_contribution_at_original_peak_kw']=shifted[:,peak_index]
    offers['simulated_managed_home_modules']=home['units']
    offers['home_battery_offer']=((offers.simulated_residual_evening_mean_kw>=rules['offers']['battery_residual_evening_mean_kw'])&(offers.simulated_residual_evening_p90_kw>=rules['offers']['battery_evening_p90_kw']))|(offers.simulated_managed_home_modules>0)
    offers['home_battery_reason']+=offers.simulated_residual_evening_mean_kw.map(lambda v:f'; actual simulated managed residual evening mean {v:.2f} kW')
    for i in offers.index[offers.simulated_managed_home_modules>0]:
        offers.loc[i,'home_battery_reason']+=f"; selected in simulated coordinated fleet: {int(offers.loc[i,'simulated_managed_home_modules'])} modules (one of potentially multiple minimum-cost placements)"
    offers['simulated_night_shifted_kwh']=0.
    for v in audit: offers.loc[v['home_index'],'simulated_night_shifted_kwh']+=v['shifted_kwh']
    offers['offers']=offers.apply(lambda v:'; '.join(label for flag,label in [('managed_charging_offer','managed_charging'),('thermostat_offer','thermostat'),('home_battery_offer','home_battery'),('export_eligibility_offer','export_eligibility')] if v[flag]) or 'uncertain / additional evidence needed',axis=1)
    offers.to_csv(DEST/'showcase_customer_to_offer.csv',index=False)
    result['showcase_offer_counts']={k:int(offers[k].sum()) for k in ['managed_charging_offer','thermostat_offer','home_battery_offer','export_eligibility_offer']}
    (DEST/'milestone_results.json').write_text(json.dumps(result,indent=2))
    figures(DEST,times,original,shifted,cap,dispatches,baseline)
    write_summary(DEST,result,screening_summary,offers)
    preserve()  # Recheck the preserved baseline hashes after the entire run.
    print('Milestone complete:',DEST/'milestone_summary.md',flush=True)

if __name__=='__main__': main()
