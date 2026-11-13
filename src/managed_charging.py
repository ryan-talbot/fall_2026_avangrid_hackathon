"""Energy-preserving EV-like rescheduling; assumed availability, 06:00 deadline."""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, vstack

def schedule(load,times,jobs,cap):
    """Jobs contain home index, available hourly indices, original mobile kWh,
    and power_kw. Stage 1 minimizes cap-miss energy without new cap-miss hours;
    stage 2 minimizes actual movement while retaining that improvement.
    """
    x=np.asarray(load,float); n,t=x.shape
    if not np.isfinite(x).all(): raise ValueError('Schedule only common complete hours')
    original_mobile=np.zeros_like(x)
    offsets=[]; variable=0
    for job in jobs:
        h=np.asarray(job['hours'],int); initial=np.asarray(job['original_mobile'],float)
        if len(h)!=len(initial) or (np.diff(h)!=1).any(): raise ValueError('A job window must be contiguous and complete')
        if (initial<0).any() or initial.max()>job['power_kw']+1e-7: raise ValueError('Original schedule violates assumed charger power')
        original_mobile[job['home'],h]+=initial
        offsets.append(variable); variable+=len(h)
    if (original_mobile-x>1e-7).any(): raise ValueError('Inferred mobile component exceeds measured household load')
    fixed=x-original_mobile; observed=x.sum(axis=0); fixed_total=fixed.sum(axis=0)
    if not jobs:
        return x.copy(),{'solver_status':0,'message':'No eligible complete charging windows','shifted_kwh':0.,'mobile_energy_kwh':0.,'jobs':0,'max_household_energy_error_kwh':0.,'max_job_energy_error_kwh':0.,'new_cap_miss_hours':0,'new_peak_created':False},[]
    # Variables: job-hour charging, absolute deviations, hourly cap excess.
    count=2*variable+t; er=[]; ec=[]; ev=[]; rhs=[]
    ur=[]; uc=[]; uv=[]; upper=[]
    def row(terms,bound):
        index=len(upper)
        for column,value in terms: ur.append(index); uc.append(column); uv.append(value)
        upper.append(bound)
    hourly=[[] for _ in range(t)]; bounds=[]; initial_vector=np.zeros(variable)
    for j,job in enumerate(jobs):
        off=offsets[j]; initial=np.asarray(job['original_mobile'],float)
        for k,h in enumerate(job['hours']):
            v=off+k; hourly[h].append(v); bounds.append((0,job['power_kw'])); initial_vector[v]=initial[k]
            er.append(j); ec.append(v); ev.append(1.)
        rhs.append(float(initial.sum()))
    bounds += [(0,None)]*(variable+t)
    for v,value in enumerate(initial_vector):
        row([(v,1),(variable+v,-1)],value)
        row([(v,-1),(variable+v,-1)],-value)
    for h,variables in enumerate(hourly):
        terms=[(v,1.) for v in variables]
        row(terms+[(2*variable+h,-1.)],cap-fixed_total[h])
        # Original is feasible; do not create new exceedances or worsen old ones.
        row(terms,max(cap,observed[h])-fixed_total[h])
    aub=coo_matrix((uv,(ur,uc)),shape=(len(upper),count)).tocsr()
    aeq=coo_matrix((ev,(er,ec)),shape=(len(jobs),count)).tocsr()
    cost=np.zeros(count); cost[2*variable:]=1
    first=linprog(cost,A_ub=aub,b_ub=upper,A_eq=aeq,b_eq=rhs,bounds=bounds,method='highs')
    if not first.success: raise RuntimeError('Managed-charging cap minimization failed: '+first.message)
    optimal_miss=float(first.x[2*variable:].sum())
    cost2=np.zeros(count); cost2[variable:2*variable]=1
    cap_row=coo_matrix((np.ones(t),(np.zeros(t,int),np.arange(2*variable,count))),shape=(1,count)).tocsr()
    second=linprog(cost2,A_ub=vstack([aub,cap_row]),b_ub=np.r_[upper,optimal_miss+1e-8],A_eq=aeq,b_eq=rhs,bounds=bounds,method='highs')
    if not second.success: raise RuntimeError('Managed-charging minimum-movement replay failed: '+second.message)
    mobile=np.zeros_like(x); audit=[]; max_job_error=0.
    for j,job in enumerate(jobs):
        off=offsets[j]; h=np.asarray(job['hours'],int); charge=second.x[off:off+len(h)]
        mobile[job['home'],h]+=charge
        error=abs(float(charge.sum())-rhs[j]); max_job_error=max(max_job_error,error)
        audit.append({'home_index':job['home'],'arrival':str(times[h[0]]),'ready_by':str(times[h[-1]]+pd.Timedelta(hours=1)),'original_mobile_kwh':rhs[j],'scheduled_mobile_kwh':float(charge.sum()),'shifted_kwh':float(np.maximum(np.asarray(job['original_mobile'])-charge,0).sum()),'max_charge_kw':float(charge.max()),'assumed_power_limit_kw':job['power_kw'],'energy_error_kwh':error})
    shifted=fixed+mobile
    household_error=float(np.abs(shifted.sum(axis=1)-x.sum(axis=1)).max())
    new_misses=int(((shifted.sum(axis=0)>cap+1e-6)&(observed<=cap+1e-6)).sum())
    metrics={'solver_status':int(second.status),'stage1_cap_miss_kwh':optimal_miss,'message':'Minimum cap-miss energy, then minimum actual shifted kWh; no new cap-miss hours allowed','jobs':len(jobs),'mobile_energy_kwh':float(original_mobile.sum()),'shifted_kwh':float(np.maximum(original_mobile-mobile,0).sum()),'max_household_energy_error_kwh':household_error,'max_job_energy_error_kwh':max_job_error,'new_cap_miss_hours':new_misses,'new_peak_created':bool(shifted.sum(axis=0).max()>observed.max()+1e-6)}
    if household_error>1e-6 or max_job_error>1e-6 or new_misses or metrics['new_peak_created'] or shifted.min()<-1e-7:
        raise RuntimeError('Managed-charging conservation or rebound checks failed: '+str(metrics))
    return shifted,metrics,audit

def build_jobs(annual_load,ids,features,events,rules):
    """Return observed summer load and jobs on its common complete hours."""
    full_times=pd.date_range('2025-09-01',periods=8760,freq='h')
    summer_start=int((pd.Timestamp('2026-06-01')-full_times[0])/pd.Timedelta(hours=1))
    summer=annual_load[:,summer_start:]; valid=np.isfinite(summer).all(axis=0)
    times=full_times[summer_start:][valid]; x=np.asarray(summer[:,valid],float)
    mapping=np.full(summer.shape[1],-1,int); mapping[valid]=np.arange(valid.sum())
    lookup={int(v):i for i,v in enumerate(ids)}
    eligible=set(features.loc[features.managed_charging_offer,'CUSTOMER_NUMBER'].astype(int))&set(lookup)
    ready_hour=rules['managed_charging']['ready_by_hour']; fraction=rules['managed_charging']['movable_fraction']
    grouped={}; excluded_incomplete=0; excluded_boundary=0
    for event in events:
        customer=int(event['CUSTOMER_NUMBER'])
        if customer not in eligible: continue
        start=int(event['start_slot']); end=start+int(event['duration_hours'])
        if end<=summer_start: continue
        ready=(start//24+(start%24>=ready_hour))*24+ready_hour
        if start<summer_start or ready>8760:
            excluded_boundary+=1; continue
        grouped.setdefault((customer,ready),[]).append(event)
    jobs=[]
    for (customer,ready),sessions in sorted(grouped.items()):
        arrival=min(int(e['start_slot']) for e in sessions)
        hours=np.arange(arrival-summer_start,ready-summer_start)
        if not valid[hours].all(): excluded_incomplete+=1; continue
        mobile=np.zeros(len(hours)); max_power=0.; home=lookup[customer]
        for event in sessions:
            start=int(event['start_slot']); duration=int(event['duration_hours'])
            h=np.arange(start,start+duration)
            component=np.clip(annual_load[home,h]-event['baseline_kw'],0,event['component_kw'])
            mobile[h-arrival]+=fraction*component
            max_power=max(max_power,fraction*event['component_kw'])
        jobs.append({'home':home,'hours':mapping[hours].tolist(),'original_mobile':mobile.tolist(),'power_kw':max_power})
    context={'eligible_showcase_homes':len(eligible),'excluded_incomplete_night_windows':excluded_incomplete,'excluded_boundary_sessions':excluded_boundary,'estimated_ev_component_kwh_in_eligible_complete_jobs':sum(sum(j['original_mobile']) for j in jobs)/fraction if fraction else 0.,'movable_fraction_assumption':fraction,'ready_by_assumption':'06:00 local time; plugged in from first detected arrival','unshifted_missing_hours':int((~valid).sum())}
    return x,times,jobs,context
