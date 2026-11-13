"""Label-blind AMI screening, frozen rules, reference-list recovery, offers.

Scores are evidence indices, not technology probabilities. Customer outputs
and reference splits are written only to ignored local data/processed/.
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from baseline import digest
from inventory import ROOT
from load_data import load

RULES=ROOT/'config/screening_rules.json'
UNCERTAIN='EV ownership and L1/L2; heat pump vs resistance; water heater; pool; hot tub; solar+battery/storage ownership: uncertain from hourly net AMI'

def mean_days(values,minimum=22):
    x=np.asarray(values).reshape(-1,24)
    count=np.isfinite(x).sum(axis=1)
    return np.divide(np.nansum(x,axis=1),count,out=np.full(len(x),np.nan),where=count>=minimum)

def ev_events(load,rules):
    """Recurring step-and-plateau candidates, with an observed exit step.

    The component is estimated above the mean of the pre/post-event load.
    Keep longest valid plateau at a start; never double count overlapping runs.
    """
    x=np.asarray(load,float); r=rules['ev']; size=len(x)
    starts=np.flatnonzero(np.diff(x)>=r['minimum_step_kw'])+1
    starts=starts[(starts<size-r['minimum_duration_hours']) & np.isin(starts%24,r['arrival_hours'])]
    if not len(starts): return []
    ready=(starts//24+(starts%24>=rules['managed_charging']['ready_by_hour']))*24+rules['managed_charging']['ready_by_hour']
    found={}
    for duration in range(r['maximum_duration_hours'],r['minimum_duration_hours']-1,-1):
        valid=(starts+duration<size)&(starts+duration<=ready)
        s=starts[valid]
        if not len(s): continue
        plateau=x[s[:,None]+np.arange(duration)]
        before=x[s-1]; after=x[s+duration]
        base=(before+after)/2
        median=np.median(plateau,axis=1); amp=median-base
        deviation=np.abs(plateau-median[:,None])
        ok=np.isfinite(plateau).all(axis=1)&np.isfinite(base)&(amp>=r['minimum_step_kw'])&(amp<=r['maximum_component_kw'])
        ok &= (median-after>=r['minimum_end_drop_fraction']*amp)
        ok &= (deviation.max(axis=1)<=np.maximum(r['plateau_absolute_tolerance_kw'],r['plateau_relative_tolerance']*amp))
        for j in np.flatnonzero(ok):
            start=int(s[j])
            if start in found: continue
            component=np.clip(plateau[j]-base[j],0,amp[j])
            found[start]={'start_slot':start,'duration_hours':duration,'baseline_kw':float(base[j]),'component_kw':float(amp[j]),'estimated_kwh':float(component.sum()),'quality':float(np.clip(1-deviation[j].mean()/amp[j],0,1))}
    events=[]; end=-1
    for start,event in sorted(found.items()):
        if start<end: continue
        events.append(event); end=start+event['duration_hours']
    return events

def weather_features(load,weather,rules):
    r=rules['weather']; daily=mean_days(load,r['minimum_daily_hours'])
    good=np.isfinite(daily)&np.isfinite(weather).all(axis=1)
    result={'weather_days':int(good.sum())}
    for label in ['heating','cooling']:
        result.update({label+'_score':0.,label+'_slope_kw_per_f':0.,label+'_partial_r2':0.,label+'_weather_response_kw':0.})
    if good.sum()<r['minimum_days']: return result
    y=daily[good]; design=np.column_stack([np.ones(good.sum()),weather[good]])
    beta=np.linalg.lstsq(design,y,rcond=None)[0]
    residual=y-design@beta; sse=float(residual@residual)
    for label,column,min_days in [('heating',1,r['minimum_heating_days']),('cooling',2,r['minimum_cooling_days'])]:
        short=np.delete(design,column,axis=1)
        reduced=y-short@np.linalg.lstsq(short,y,rcond=None)[0]
        reduced_sse=float(reduced@reduced)
        partial=max(0,1-sse/reduced_sse) if reduced_sse>1e-12 else 0.
        slope=float(beta[column])
        exposure=design[:,column]; days=int((exposure>0).sum())
        score=0.
        if slope>0 and partial>=r['minimum_partial_r2'] and days>=min_days:
            score=100*(.5*min(slope/r['slope_saturation_kw_per_f'],1)+.5*min(partial/r['partial_r2_saturation'],1))
        result.update({label+'_score':score,label+'_slope_kw_per_f':slope,label+'_partial_r2':partial,label+'_weather_response_kw':max(0,slope)*float(np.percentile(exposure,90))})
    return result

def reference_recovery(features,refs,rules,dest):
    """Evaluate fixed ranked outreach lists; unlisted IDs are not negatives."""
    evaluation=rules['evaluation']; summary={}; splits=[]
    for tech,sheet,score,k in [('EV','EV Customers','ev_score',evaluation['outreach_size_ev']),('HP','HP Customers','heating_score',evaluation['outreach_size_heating'])]:
        values=sorted(refs[sheet].CUSTOMER_NUMBER.astype(int).tolist(),key=lambda v:hashlib.sha256(f"{evaluation['split_salt']}:{tech}:{v}".encode()).hexdigest())
        n=int(len(values)*evaluation['heldout_fraction']); held=set(values[:n])
        population=set(features.CUSTOMER_NUMBER); qualified=held&population
        ranked=features.sort_values([score,'CUSTOMER_NUMBER'],ascending=[False,True]).head(k)
        selected=set(ranked.CUSTOMER_NUMBER); hits=qualified&selected
        summary[tech]={'outreach_list_size':len(ranked),'fixed_K':k,'heldout_reference_count':len(held),'qualifying_heldout_count':len(qualified),'heldout_recovered':len(hits),'recovery_of_qualifying_heldout':len(hits)/len(qualified) if qualified else None,'recovery_of_all_heldout':len(hits)/len(held),'lowest_outreach_score':float(ranked[score].min()),'interpretation':'Reference-list recovery, not precision/specificity. EV/HP references are partial likely labels; unlisted status unknown. HP recovery tests a weather-sensitive heating proxy, not an HP-vs-resistance classifier.'}
        for value in values: splits.append({'technology':tech,'CUSTOMER_NUMBER':value,'split':'heldout' if value in held else 'unused_development','qualifies':value in population,'in_fixed_outreach':value in selected})
        ranked.to_csv(dest/f'{tech.lower()}_outreach.csv',index=False)
    cooling=features.sort_values(['cooling_score','CUSTOMER_NUMBER'],ascending=[False,True]).head(evaluation['outreach_size_cooling'])
    cooling.to_csv(dest/'cooling_outreach.csv',index=False)
    summary['cooling']={'fixed_K':len(cooling),'reference_recovery':None,'reason':'No AC/cooling reference labels supplied; no accuracy estimate available.'}
    pd.DataFrame(splits).to_csv(dest/'reference_split.csv',index=False)
    return summary

def screen(dest,rules_path=RULES):
    dest=Path(dest); dest.mkdir(parents=True,exist_ok=True)
    rules=json.loads(Path(rules_path).read_text()); rules_hash=digest(rules_path)
    # This artifact is written before features and before any reference read.
    freeze={'rules_sha256':rules_hash,'rules':rules,'label_usage':'No reference IDs used for features, threshold tuning or eligibility; 50% reference holdout, other half also unused for tuning.'}
    (dest/'rules_frozen.json').write_text(json.dumps(freeze,indent=2))
    a,counts=load(); ids=np.flatnonzero(counts>=rules['population_coverage']*8760)
    times=pd.date_range('2025-09-01',periods=8760,freq='h')
    weather=pd.read_csv(ROOT/'data/processed/baseline_unshifted_v1/weather_hour_start.csv',parse_dates=['hour_start']).set_index('hour_start').reindex(times)
    r=rules['weather']; temp=weather.temp.to_numpy()
    daily_weather=np.column_stack([mean_days(np.maximum(r['heating_balance_f']-temp,0),r['minimum_daily_hours']),mean_days(np.maximum(temp-r['cooling_balance_f'],0),r['minimum_daily_hours']),(times[::24].dayofweek>=5).astype(float)])
    summer=(times>='2026-06-01')&(times<'2026-09-01'); peak_hours=np.isin(times.hour,rules['offers']['peak_hours']); evening=summer&peak_hours
    rows=[]; event_fields=['CUSTOMER_NUMBER','start_slot','duration_hours','baseline_kw','component_kw','estimated_kwh','quality']
    with (dest/'ev_events.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=event_fields); writer.writeheader()
        for number,customer in enumerate(ids):
            x=np.asarray(a[customer],float); events=ev_events(x,rules)
            months=len({times[e['start_slot']].month for e in events})
            quality=float(np.median([e['quality'] for e in events])) if events else 0.
            weights=rules['ev']['score_weights']
            score=100*(weights[0]*min(len(events)/rules['ev']['event_saturation'],1)+weights[1]*quality+weights[2]*min(months/rules['ev']['month_saturation'],1)) if events else 0.
            ev_candidate=score>=rules['ev']['eligible_score'] and len(events)>=rules['ev']['minimum_events'] and months>=rules['ev']['minimum_months']
            overlap=0.
            for event in events:
                writer.writerow({'CUSTOMER_NUMBER':int(customer),**event})
                s=event['start_slot']; h=np.arange(s,s+event['duration_hours'])
                component=np.clip(x[h]-event['baseline_kw'],0,event['component_kw'])
                overlap+=float(component[evening[h]].sum())
            row={'CUSTOMER_NUMBER':int(customer),'coverage':counts[customer]/8760,'ev_score':score,'ev_event_count':len(events),'ev_recurring_months':months,'ev_plateau_quality':quality,'ev_candidate':bool(ev_candidate),'ev_reason':f'{len(events)} recurring overnight step/plateau events in {months} months; median flatness {quality:.2f}; component inferred, not measured charging','ev_estimated_summer_evening_kwh':overlap}
            row.update(weather_features(x,daily_weather,rules))
            for label in ['heating','cooling']:
                row[label+'_reason']=f"daily weather slope {row[label+'_slope_kw_per_f']:.4f} kW/F; partial R2 {row[label+'_partial_r2']:.3f}; {row['weather_days']} usable days; association only"
                row[label+'_candidate']=row[label+'_score']>=r['eligible_score']
            evening_values=x[evening&np.isfinite(x)]
            row['summer_evening_mean_kw']=float(evening_values.mean()) if len(evening_values) else np.nan
            row['summer_evening_p90_kw']=float(np.percentile(evening_values,90)) if len(evening_values) else np.nan
            discount=rules['managed_charging']['movable_fraction']*overlap/len(evening_values) if ev_candidate and len(evening_values) else 0.
            row['screened_residual_evening_mean_kw']=row['summer_evening_mean_kw']-discount
            row['managed_charging_offer']=bool(ev_candidate and overlap>0)
            row['managed_charging_reason']=f"EV score {score:.1f}; {overlap:.2f} estimated EV-like kWh overlaps summer 16:00-22:00" if row['managed_charging_offer'] else 'Insufficient recurring EV-like evidence or no summer evening overlap; EV status unknown'
            row['thermostat_offer']=any(row[label+'_candidate'] and row[label+'_weather_response_kw']>=rules['offers']['thermostat_weather_response_kw'] for label in ['heating','cooling'])
            row['thermostat_reason']='; '.join(row[label+'_reason'] for label in ['heating','cooling'] if row[label+'_candidate']) if row['thermostat_offer'] else 'Insufficient weather-response evidence; equipment and control compatibility unknown'
            row['home_battery_offer']=bool(row['screened_residual_evening_mean_kw']>=rules['offers']['battery_residual_evening_mean_kw'] and row['summer_evening_p90_kw']>=rules['offers']['battery_evening_p90_kw'])
            row['home_battery_reason']=f"Residual evening mean {row['screened_residual_evening_mean_kw']:.2f} kW after estimated 50% EV allowance; evening P90 {row['summer_evening_p90_kw']:.2f} kW; profile screening only, dispatch needed for sizing"
            row['uncertain_appliances']=UNCERTAIN
            rows.append(row)
            if (number+1)%1000==0: print(f'Screened {number+1}/{len(ids)} customers (label-blind)',flush=True)
    features=pd.DataFrame(rows)
    features.to_csv(dest/'features_before_reference.csv',index=False)
    feature_hash=digest(dest/'features_before_reference.csv')
    # Only now read references. Rules/features are already frozen on disk.
    refs=pd.read_excel(next((ROOT/'data/raw').glob('EV_Heat*')),sheet_name=None)
    recovery=reference_recovery(features,refs,rules,dest)
    pv=set(refs['PV Customers'].CUSTOMER_NUMBER.astype(int)); ev=set(refs['EV Customers'].CUSTOMER_NUMBER.astype(int)); hp=set(refs['HP Customers'].CUSTOMER_NUMBER.astype(int))
    features['pv_evidence_score']=features.CUSTOMER_NUMBER.map(lambda v:100. if v in pv else np.nan)
    features['pv_status']=features.CUSTOMER_NUMBER.map(lambda v:'known PV reference' if v in pv else 'unknown')
    features['pv_reason']=features.CUSTOMER_NUMBER.map(lambda v:'Organizer known-PV list; no generation, export or battery measurements' if v in pv else 'Not on known-PV list; no measured generation/export/storage evidence')
    features['export_eligibility_offer']=features.CUSTOMER_NUMBER.isin(pv)
    features['export_eligibility_reason']=features.pv_reason+'; verify interconnection, surplus, metering and export compensation before enrollment'
    features['ev_reference_status']=features.CUSTOMER_NUMBER.map(lambda v:'likely reference label' if v in ev else 'unknown')
    features['hp_reference_status']=features.CUSTOMER_NUMBER.map(lambda v:'likely reference label' if v in hp else 'unknown')
    offer_columns=['managed_charging_offer','thermostat_offer','home_battery_offer','export_eligibility_offer']
    features['offers']=features.apply(lambda v:'; '.join(c.replace('_offer','') for c in offer_columns if v[c]) or 'uncertain / additional evidence needed',axis=1)
    features.to_csv(dest/'customer_to_offer.csv',index=False)
    summary={'rules_sha256':rules_hash,'features_sha256_before_reference':feature_hash,'rule_hash_unchanged_after_evaluation':digest(rules_path)==rules_hash,'qualifying_population':len(ids),'coverage_threshold':rules['population_coverage'],'ev_candidates':int(features.ev_candidate.sum()),'heating_candidates':int(features.heating_candidate.sum()),'cooling_candidates':int(features.cooling_candidate.sum()),'known_pv_qualifying':int(features.export_eligibility_offer.sum()),'offer_counts':{c:int(features[c].sum()) for c in offer_columns},'reference_recovery':recovery,'scores':'Evidence indices, not calibrated probabilities. No negative technology labels assigned to unlisted customers.'}
    (dest/'screening_summary.json').write_text(json.dumps(summary,indent=2))
    print('Screening summary:',json.dumps(summary),flush=True)
    return features,summary,rules
