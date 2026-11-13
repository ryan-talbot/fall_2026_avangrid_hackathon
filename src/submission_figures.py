r"""Generate slide-ready screening, example, appliance, and BTM evidence.

Run: .\.venv\Scripts\python.exe src/submission_figures.py
All outputs, including anonymized household profiles, remain in ignored data/.
"""
import argparse
import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from baseline import preserve,digest
from inventory import ROOT
from load_data import load
from model import dispatch,ETA
from screening import RULES,mean_days

DEST=ROOT/'data/processed/submission_package'
SOURCE=ROOT/'data/processed/milestone_screening'
COLORS=['#246c9c','#287d69','#a85f25','#785b9b']

def save(fig,stem):
    paths=[]
    for ext in ['svg','png']:
        p=DEST/'figures'/f'{stem}.{ext}';fig.savefig(p,dpi=300,facecolor='white');paths.append(p)
    plt.close(fig)
    return paths

def wrap(value,width): return '\n'.join(textwrap.wrap(str(value),width=width))

def setup():
    (DEST/'figures').mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.parse_math':False,'axes.spines.top':False,'axes.spines.right':False})
    baseline=preserve(); summary=json.loads((SOURCE/'screening_summary.json').read_text())
    if digest(RULES)!=summary['rules_sha256'] or digest(SOURCE/'features_before_reference.csv')!=summary['features_sha256_before_reference']:
        raise ValueError('Frozen rules/features changed')
    offers=pd.read_csv(SOURCE/'customer_to_offer.csv'); showcase=pd.read_csv(SOURCE/'showcase_customer_to_offer.csv')
    if len(offers)!=summary['qualifying_population']: raise ValueError('Offer denominator differs')
    for field,count in summary['offer_counts'].items():
        if int(offers[field].sum())!=count: raise ValueError('Offer counts differ: '+field)
    return baseline,summary,offers,showcase

def segments(summary,offers):
    total=len(offers)
    cards=[('managed_charging_offer','Managed EV charging',
            'Recurring step + plateau at night; at least 12 events in 3 months; evidence score >=60 and summer evening overlap.',
            'Confirm EV and plug-in timing; invite to managed charging.'),
           ('thermostat_offer','Thermostat outreach',
            'Heating/cooling weather score >=60 and weather-associated response >=0.5 kW; daily degree exposure + AMI.',
            'Confirm HVAC and control compatibility; invite to thermostat outreach.'),
           ('home_battery_offer','BTM battery assessment',
            'Residual evening mean >=2 kW and P90 >=3 kW after an assumed 50% EV-component allowance.',
            'Assess service, site and constrained dispatch; profile screen only, not a sized design.'),
           ('export_eligibility_offer','Solar export check',
            'Membership in organizer known-PV list. No generation, export or battery measurements supplied.',
            'Check interconnection, surplus, metering and export eligibility; do not assume payments.')]
    rows=[];fig=plt.figure(figsize=(13.33,7.5))
    fig.text(.045,.945,'Meter evidence -> four Avangrid outreach actions',fontsize=22,fontweight='bold')
    fig.text(.045,.895,f'Denominator: {total:,} meters with >=95% complete annual coverage. Offers overlap; counts must not be added.',fontsize=12)
    for j,(field,title,evidence,action) in enumerate(cards):
        left=.035+j*.242; color=COLORS[j];count=int(offers[field].sum())
        fig.patches.append(FancyBboxPatch((left,.27),.226,.57,boxstyle='round,pad=0.008',transform=fig.transFigure,facecolor='#f4f7f9',edgecolor=color,linewidth=1.6))
        fig.text(left+.014,.775,f'{count:,}',fontsize=31,fontweight='bold',color=color)
        fig.text(left+.014,.73,f'{count/total:.1%} of qualifying meters',fontsize=10.5,color='#444444')
        fig.text(left+.014,.68,wrap(title,24),fontsize=13.5,fontweight='bold',color=color,va='top')
        fig.text(left+.014,.565,'EVIDENCE',fontsize=9,fontweight='bold',color='#555555')
        fig.text(left+.014,.535,wrap(evidence,33),fontsize=10.5,va='top',linespacing=1.35)
        fig.text(left+.014,.385,'ACTION',fontsize=9,fontweight='bold',color='#555555')
        fig.text(left+.014,.355,wrap(action,34),fontsize=10.5,va='top',linespacing=1.25)
        rows.append({'offer':title,'count':count,'denominator':total,'fraction':count/total,'evidence':evidence,'action':action,'scope':'Population profile/outreach screen; overlapping flags'})
    fig.text(.045,.19,'Held-out reference recovery (frozen rules; fixed outreach sizes)',fontsize=14,fontweight='bold')
    fig.text(.045,.14,'EV: 17 of 90 in the top 1,000 (18.9%)     |     Heating proxy: 4 of 43 in the top 500 (9.3%)',fontsize=14)
    fig.text(.045,.083,'Recovery is not precision or prevalence. Unlisted appliance status is unknown; scores are evidence indices, not probabilities.',fontsize=10.5)
    fig.text(.045,.045,'Measured AMI/weather + reference PV list -> estimated screening evidence -> outreach candidates. No enrollment or savings assumed.',fontsize=10)
    pd.DataFrame(rows).to_csv(DEST/'segmentation_offer_counts.csv',index=False)
    return save(fig,'cleargrid_customer_segments')

def examples(baseline,showcase):
    a,_=load(); times=pd.date_range('2025-09-01',periods=8760,freq='h')
    evrow=showcase[showcase.managed_charging_offer].sort_values(['ev_score','display_home'],ascending=[False,True]).iloc[0]
    heatrow=showcase[showcase.thermostat_offer&showcase.heating_candidate].sort_values(['heating_score','display_home'],ascending=[False,True]).iloc[0]
    candidates=[]
    for c in pd.read_csv(SOURCE/'ev_events.csv',chunksize=100000):
        q=c[c.CUSTOMER_NUMBER==int(evrow.CUSTOMER_NUMBER)].copy()
        q=q[(q.start_slot>=6552)&(q.start_slot<8760)&(q.start_slot%24>=16)&(q.start_slot%24<=21)]
        candidates.extend(q.to_dict('records'))
    if not candidates: raise ValueError('No summer event for the deterministic EV example')
    chosen=sorted(candidates,key=lambda v:(v['estimated_kwh'],v['start_slot']))[len(candidates)//2]
    start=int(chosen['start_slot']);duration=int(chosen['duration_hours']);window_start=(start//24)*24+12; window_stop=min(window_start+24,8760)
    x=np.asarray(a[int(evrow.CUSTOMER_NUMBER)],float);tx=times[window_start:window_stop];y=x[window_start:window_stop]
    weather=pd.read_csv(baseline/'weather_hour_start.csv',parse_dates=['hour_start']).set_index('hour_start').reindex(times)
    temp=mean_days(weather.temp.to_numpy()); hx=np.asarray(a[int(heatrow.CUSTOMER_NUMBER)],float).reshape(365,24)
    good=np.isfinite(hx).sum(axis=1)>=22; weekday=times[::24].day_of_week<5
    cold=good&weekday&np.isfinite(temp)&(temp<=40);mild=good&weekday&np.isfinite(temp)&(temp>=55)&(temp<=65)
    if cold.sum()<5 or mild.sum()<5: raise ValueError('Too few days for fixed illustrative weather bins')
    fig,axes=plt.subplots(1,2,figsize=(13.33,7.5))
    fig.suptitle('Two anonymized profiles: evidence for an outreach conversation',fontsize=19,y=.96)
    ax=axes[0];ax.step(tx,y,where='post',color=COLORS[0],label='Measured household AMI')
    ax.axvspan(times[start],times[start+duration],color=COLORS[0],alpha=.12,label='Detected EV-like plateau')
    ax.axhline(chosen['baseline_kw'],color='#6e6e6e',ls=':',label='Estimated pre/post baseline')
    ax.set_title(f'Example A: showcase home {int(evrow.display_home)}\nEV-like overnight plateau',fontsize=14)
    ax.set_ylabel('Hourly average load (kW)');ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[12,18,0,6]));ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    ax.legend(fontsize=9,loc='upper left',bbox_to_anchor=(0,-.18),frameon=False,borderaxespad=0);ax.grid(alpha=.15)
    ax.text(0,-.44,f"{int(evrow.ev_event_count)} events / {int(evrow.ev_recurring_months)} months; EV evidence {evrow.ev_score:.1f}/100.\nAction: confirm EV + ready-by timing; offer managed charging.\nOther repeating appliances can resemble charging; ownership is unknown.",transform=ax.transAxes,va='top',fontsize=10,linespacing=1.6)
    ax=axes[1];hours=np.arange(24)
    cold_profile=np.nanmedian(hx[cold],axis=0);mild_profile=np.nanmedian(hx[mild],axis=0)
    ax.plot(hours,cold_profile,color=COLORS[1],lw=2,label=f'Cold weekdays: mean T <=40 F (n={cold.sum()})')
    ax.plot(hours,mild_profile,color='#6e6e6e',lw=2,ls='--',label=f'Mild weekdays: 55-65 F (n={mild.sum()})')
    ax.set_title(f'Example B: showcase home {int(heatrow.display_home)}\nWeather-sensitive load',fontsize=14)
    ax.set_xlabel('Local hour');ax.set_xticks([0,6,12,18,23]);ax.set_ylabel('Median hourly load (kW)');ax.legend(fontsize=9,loc='upper left',bbox_to_anchor=(0,-.18),frameon=False,borderaxespad=0);ax.grid(alpha=.15)
    ax.text(0,-.44,f"Heating evidence {heatrow.heating_score:.1f}/100; partial R2 {heatrow.heating_partial_r2:.2f}.\nAction: confirm HVAC + controllability; thermostat outreach.\nWeather association does not resolve heat pump vs resistance heating.",transform=ax.transAxes,va='top',fontsize=10,linespacing=1.6)
    fig.text(.5,.04,'Illustrative selection, not a new accuracy test: highest relevant showcase evidence score; median-energy summer EV event; fixed weather bins.',ha='center',fontsize=9.5)
    fig.subplots_adjust(left=.065,right=.97,top=.80,bottom=.38,wspace=.28)
    pd.DataFrame({'hour_start':tx,'measured_example_A_kw':y,'estimated_event_component_kw':np.where((np.arange(window_start,window_stop)>=start)&(np.arange(window_start,window_stop)<start+duration),np.clip(y-chosen['baseline_kw'],0,chosen['component_kw']),0)}).to_csv(DEST/'example_A_profile.csv',index=False)
    pd.DataFrame({'hour':hours,'measured_cold_weekday_median_kw':cold_profile,'measured_mild_weekday_median_kw':mild_profile}).to_csv(DEST/'example_B_profile.csv',index=False)
    meta={'selection':'Label-blind illustration among showcase offer candidates; highest relevant evidence score; median-energy summer evening event. Weather curves are weekday medians in fixed bins, not model fits.','example_A_display_home':int(evrow.display_home),'example_B_display_home':int(heatrow.display_home),'ev_event_start':str(times[start]),'ev_event_duration_hours':duration,'cold_weekdays':int(cold.sum()),'mild_weekdays':int(mild.sum())}
    (DEST/'example_profile_metadata.json').write_text(json.dumps(meta,indent=2))
    return save(fig,'cleargrid_outreach_examples')

def appendix():
    rows=[
      ('EV: Level 1 / Level 2','Recurring overnight step/plateau; held-out EV recovery 17/90 at K=1,000.','EV-like screen only. L1/L2 and ownership unresolved; confirm charger.'),
      ('Air conditioning','Positive cooling-degree exposure response; score and partial R2.','Cooling-associated candidate, not confirmed AC; no cooling reference list.'),
      ('Resistance heating','Positive heating-degree exposure response in daily load.','Subtype unresolved; other temperature-related loads can contribute.'),
      ('Heat pumps / mini-splits','Heating proxy; held-out HP-list recovery 4/43 at K=500.','Not an HP-vs-resistance classifier; confirm equipment.'),
      ('Water heaters','Step/plateau signatures can overlap other end uses.','Unresolved; no separate validated detector or reference labels.'),
      ('Swimming pools','Seasonal repeating loads could be consistent with pumps.','Unresolved; no implemented pool-specific classification.'),
      ('Hot tubs','Repeating pump/heater loads can resemble other appliances.','Unresolved; no implemented hot-tub-specific classification.'),
      ('Solar PV','Organizer known-PV list; 393 references meet the 95% screen.','PV membership only. No measured generation, exports or surplus.'),
      ('Solar + battery','PV reference membership; no battery telemetry or ownership labels.','Storage ownership/operation unresolved; export eligibility check only.'),
      ('Persistent peak contributors','Residual evening mean/P90 screen; 30-home constrained dispatch.','BTM assessment lead. No verified bill saving or service-upgrade value.')]
    df=pd.DataFrame(rows,columns=['Challenge category','Evidence actually available','Status / next step'])
    df.to_csv(DEST/'appliance_coverage_appendix.csv',index=False)
    (DEST/'appliance_coverage_appendix.md').write_text('\n'.join(['| '+' | '.join(df.columns)+' |','|---|---|---|',*['| '+' | '.join(v)+' |' for v in df.values.tolist()]])+'\n')
    fig,ax=plt.subplots(figsize=(13.33,7.5));ax.axis('off')
    fig.suptitle('Appendix: challenge appliance coverage and unresolved categories',fontsize=18,y=.96)
    cells=[[wrap(v,26 if j==0 else 49) for j,v in enumerate(row)] for row in df.values]
    table=ax.table(cellText=cells,colLabels=df.columns,colWidths=[.21,.405,.385],cellLoc='left',loc='center',bbox=[0,.02,1,.94])
    table.auto_set_font_size(False);table.set_fontsize(10)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#d6dfe5');cell.set_text_props(va='center')
        if r==0:cell.set_facecolor('#246c9c');cell.set_text_props(color='white',weight='bold')
        else:cell.set_facecolor('#f1f5f8' if r%2 else 'white')
    fig.text(.5,.025,'Unlisted appliance status is unknown. Evidence scores are not probabilities; reference recovery is not precision or verified ownership.',ha='center',fontsize=10)
    fig.subplots_adjust(left=.025,right=.975,top=.88,bottom=.07)
    return save(fig,'cleargrid_appliance_appendix')

def placements(baseline,original=False):
    base=json.loads((baseline/'showcase_results.json').read_text());ids=np.load(baseline/'showcase_ids.npy');a,_=load()
    times=pd.date_range('2026-06-01',periods=2208,freq='h');full=np.asarray(a[ids,6552:],float);valid=np.isfinite(full).all(axis=0);x=full[:,valid];t=times[valid]
    case=base['targets']['0.15'];cap=case['cap_kw'];design=case['home'];units=np.array(design['units'])
    if original:
        config=json.loads((ROOT/'data/config/original_historical_fleet.json').read_text());units[:]=0;units[np.array(config['home_display_numbers'])-1]=config['modules_per_home']
    energy=units*10.08;power=units*3.84;breaks=np.flatnonzero((t[1:]-t[:-1])!=pd.Timedelta(hours=1))+1
    r=dispatch(x,cap,energy=energy,power=power,breaks=breaks)
    if not r['feasible']: raise ValueError('Placement replay failed')
    peak=int(np.argmax(x.sum(axis=0)));jul3=t.date==pd.Timestamp('2026-07-03').date()
    rows=[]
    for i in np.flatnonzero(units):
        rows.append({'display_home':i+1,'modules':int(units[i]),'rated_power_kw':power[i],'rated_energy_kwh':energy[i],'measured_load_at_group_peak_kw':x[i,peak],'no_export_net_discharge_ceiling_kw':min(power[i],x[i,peak]),'simulated_discharge_at_group_peak_kw':r['discharge'][i,peak],'simulated_july3_discharge_kwh':float(r['discharge'][i,jul3].sum()),'selection_evidence':'Original-analysis placements fixed; verified with measured hourly loads and group cap/SOC/power/reserve/efficiency/no-export constraints.' if original else 'Measured household hourly load, group cap, SOC/power/reserve/efficiency/no-export feasibility; installed-cost minimization. Appliance labels were not optimization inputs.','placement_scope':'Original-analysis fixed fleet, independently verified' if original else 'Current reproduced optimizer-selected fleet; one minimum-cost placement'})
    df=pd.DataFrame(rows);stem='cleargrid_original_btm_placements_15pct' if original else 'cleargrid_btm_placements_15pct'
    df.to_csv(DEST/f'{stem}_evidence.csv',index=False)
    fig,ax=plt.subplots(figsize=(13.33,7.5));ax.axis('off')
    title='Original-analysis fleet: fixed placements, verified at the 15% cap' if original else 'Concrete BTM recommendation: one minimum-cost 15% home fleet'
    fig.suptitle(title,fontsize=19,y=.96)
    fig.text(.045,.875,f'Remaining group requirement: {x.sum(axis=0)[peak]:.3f} kW - {cap:.3f} kW cap = {x.sum(axis=0)[peak]-cap:.3f} kW at July 3, 14:00.',fontsize=13)
    explanation='Original placements fixed; verification uses hourly load + cap, SOC, power, reserve and no-export constraints. No new site optimization.' if original else 'Selection uses measured hourly loads + dispatch constraints + assumed installed cost. EV/HVAC labels do not select the sites.'
    fig.text(.045,.82,explanation,fontsize=11)
    cells=[]
    for _,row in df.iterrows():
        cells.append([f"Home {int(row.display_home)}",str(int(row.modules)),f'{row.rated_power_kw:.2f} / {row.rated_energy_kwh:.2f}',f'{row.measured_load_at_group_peak_kw:.3f}',f'{row.no_export_net_discharge_ceiling_kw:.3f}',f'{row.simulated_discharge_at_group_peak_kw:.3f}',f'{row.simulated_july3_discharge_kwh:.2f}'])
    headers=['Showcase\ndisplay','Modules','Rated\nkW / kWh','Measured load\nat group peak (kW)','No-export\nceiling (kW)','Simulated peak\ndischarge (kW)','Simulated July 3\ndischarge (kWh)']
    table=ax.table(cellText=cells,colLabels=headers,cellLoc='center',bbox=[.01,.38,.98,.37],colWidths=[.12,.08,.14,.17,.15,.17,.17]);table.auto_set_font_size(False);table.set_fontsize(11)
    for (row,col),cell in table.get_celld().items():
        cell.set_edgecolor('#d6dfe5')
        if row==0:cell.set_facecolor(COLORS[0]);cell.set_text_props(color='white',weight='bold')
        else:cell.set_facecolor('#f1f5f8' if row%2 else 'white')
    fig.text(.045,.35,f"HOME FLEET: {power.sum():.2f} kW / {energy.sum():.2f} kWh, {len(rows)} sites, assumed $60,000. SHARED ALTERNATIVE: 12.5 kW / 55 kWh, 1 site, $50,750.",fontsize=12,fontweight='bold')
    fig.text(.045,.285,'No export: a home can only reduce its own current meter load. Rated inverter power is not all usable against neighbors\' demand.',fontsize=11)
    fig.text(.045,.24,f'At 20% reserve, each two-module site can deliver up to {20.16*.8*ETA:.2f} AC kWh from full charge. Sizing must cover the whole event, not just its peak hour.',fontsize=11)
    fig.text(.045,.175,'Placements are not unique: the reproduced optimizer uses homes 3, 4, 6; the original analysis uses 6, 11, 19 at the same fleet size/cost.',fontsize=11)
    fig.text(.045,.12,'Original homes 6, 11, 19 passed the causal July 1-4 replay after sizing with the full historical record. This is not held-out sizing validation.',fontsize=10.5)
    fig.text(.045,.055,'Measured AMI; simulated perfect-foresight fixed-fleet dispatch checks; assumed installed prices. Separate service/interconnection assessment required.',fontsize=10)
    ax.set_position([0,0,1,1])
    return save(fig,stem)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--segments-only',action='store_true');args=parser.parse_args()
    baseline,summary,offers,showcase=setup()
    protected=json.loads((ROOT/'data/processed/final_validation/figure_manifest.json').read_text())['figure_sha256']
    outputs={'customer_segments':segments(summary,offers),'outreach_examples':examples(baseline,showcase),'appliance_appendix':appendix()}
    if not args.segments_only:
        outputs['btm_optimizer_placements']=placements(baseline)
        outputs['btm_original_placements']=placements(baseline,original=True)
    if any(digest(ROOT/p)!=v for p,v in protected.items()):raise ValueError('Verified figure changed')
    meta={'rules_sha256':summary['rules_sha256'],'baseline_manifest_sha256':digest(baseline/'baseline_manifest.json'),'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [SOURCE/'customer_to_offer.csv',SOURCE/'showcase_customer_to_offer.csv',SOURCE/'screening_summary.json']},'output_sha256':{str(p.relative_to(ROOT)):digest(p) for paths in outputs.values() for p in paths},'protected_figure_sha256':protected}
    (DEST/'submission_figure_manifest.json').write_text(json.dumps(meta,indent=2))
    print('Submission figures:',json.dumps({k:[str(p.relative_to(ROOT)) for p in v] for k,v in outputs.items()},indent=2))

if __name__=='__main__':main()
