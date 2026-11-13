"""Causal hourly cap controller: only this hour's load and carried SOC.

If measured group load exceeds the fixed cap, discharge proportionally to
available energy, respecting inverter, reserve and each home's no-export limit.
Otherwise charge proportionally to remaining capacity using available cap
headroom. Grid charging is allowed at any hour; no forecast, daily SOC reset,
terminal full-charge constraint, or future load enters the controller.
"""
import numpy as np
import pandas as pd
from model import ETA

POLICY={
    'version':'cleargrid-causal-cap-v1',
    'information':'Current complete hourly load, current SOC, fixed equipment and fixed group cap only; no future load or weather.',
    'starting_soc_fraction':1.0,
    'reserve_fraction':0.2,
    'charge_efficiency':float(ETA),
    'discharge_efficiency':float(ETA),
    'discharge_rule':'If group load > cap, discharge only the deficit, limited by site inverter power, energy above reserve, and household load (no export). Allocate proportionally to available AC energy with saturation at site limits.',
    'charge_rule':'If group load < cap, grid charge using present headroom, inverter power and capacity room. Allocate proportionally to missing energy with saturation at site limits. Allowed at every hour, including overnight.',
    'midnight_rule':'Carry SOC continuously; never reset at midnight.',
    'missing_hour_rule':'No inferred load, charge or discharge; carry SOC unchanged and report a gap. Missing hours are excluded from cap-feasibility counts.',
    'overnight_definition':'00:00 through 06:00; report SOC at 06:00 and whether all installed batteries are full. Also record first full time in this window.',
    'miss_tolerance_kw':1e-6
}

def allocate(amount,limits,weights):
    """Weighted water filling, capped at each site's available power."""
    limits=np.maximum(np.asarray(limits,float),0)
    weights=np.maximum(np.asarray(weights,float),0)
    out=np.zeros_like(limits); left=min(max(0,float(amount)),float(limits.sum()))
    for _ in range(len(limits)+1):
        room=limits-out; active=(room>1e-12)&(weights>1e-12)
        if left<=1e-12 or not active.any(): break
        shares=left*weights[active]/weights[active].sum()
        given=np.minimum(shares,room[active]); out[active]+=given; left-=float(given.sum())
    return out

def replay(load,times,cap,energy,power,start_fraction=1.0,reserve=.2,eta=ETA,score_mask=None):
    """One-hour steps, including explicit missing hours in the timeline.

    Rows correspond to sites. For shared storage pass one aggregate-load row;
    for a home fleet pass every household (zero capacity at uninstalled sites).
    Returns start/end SOC and flows for direct independent audit.
    """
    x=np.atleast_2d(np.asarray(load,float)); n,t=x.shape
    times=pd.DatetimeIndex(times)
    scored=np.ones(t,dtype=bool) if score_mask is None else np.asarray(score_mask,dtype=bool)
    if scored.shape!=(t,) or not scored.any(): raise ValueError('A nonempty hourly scoring mask is required')
    if len(times)!=t or (len(times)>1 and ((times[1:]-times[:-1])!=pd.Timedelta(hours=1)).any()):
        raise ValueError('Replay needs the complete chronological hourly axis, including gaps')
    e=np.broadcast_to(np.asarray(energy,float),(n,)); p=np.broadcast_to(np.asarray(power,float),(n,))
    if np.any(e<0) or np.any(p<0) or not reserve<=start_fraction<=1 or not 0<eta<=1:
        raise ValueError('Invalid equipment, reserve, charge fraction or efficiency')
    state=e*start_fraction
    before=np.zeros_like(x); after=np.zeros_like(x); charge=np.zeros_like(x); discharge=np.zeros_like(x)
    valid=np.isfinite(x).all(axis=0)
    grid=np.full_like(x,np.nan)
    for h in range(t):
        before[:,h]=state
        if valid[h]:
            load_now=x[:,h]  # The only load observation used by this decision.
            total=float(load_now.sum())
            if total>cap:
                ac_energy=np.maximum(state-reserve*e,0)*eta
                limits=np.minimum.reduce([p,ac_energy,np.maximum(load_now,0)])
                discharge[:,h]=allocate(total-cap,limits,ac_energy)
                state=state-discharge[:,h]/eta
            elif total<cap:
                ac_room=np.maximum(e-state,0)/eta
                limits=np.minimum(p,ac_room)
                charge[:,h]=allocate(cap-total,limits,ac_room)
                state=state+eta*charge[:,h]
            grid[:,h]=load_now+charge[:,h]-discharge[:,h]
        after[:,h]=state
    # Independent physics audit; cap failures are reported, not rejected.
    residual=float(np.abs(after-before-eta*charge+discharge/eta).max())
    violations=[residual,float(max(0,(reserve*e[:,None]-after).max())),float(max(0,(after-e[:,None]).max())),float(max(0,(charge-p[:,None]).max())),float(max(0,(discharge-p[:,None]).max())),float(np.minimum(charge,discharge).max())]
    if valid.any(): violations.append(float(max(0,-grid[:,valid].min())))
    if max(violations)>1e-7: raise RuntimeError('Causal replay physics failed: '+str(violations))
    if t>1 and not np.allclose(before[:,1:],after[:,:-1],rtol=0,atol=1e-9): raise RuntimeError('SOC reset in replay')
    total_grid=np.full(t,np.nan); total_grid[valid]=grid[:,valid].sum(axis=0)
    misses=np.maximum(total_grid-cap,0)
    installed=e>0
    overnight=[]
    for day in pd.date_range(times[0].normalize(),times[-1].normalize(),freq='D'):
        window=(times>=day)&(times<day+pd.Timedelta(hours=6))
        if not window.any(): continue
        slots=np.flatnonzero(window); complete=len(slots)==6 and bool(valid[slots].all())
        final_soc=after[:,slots[-1]]
        full=np.all(after[installed][:,slots]>=e[installed,None]-1e-7,axis=0)
        first=slots[np.flatnonzero(full)[0]] if full.any() else None
        started=bool(np.all(before[installed,slots[0]]>=e[installed]-1e-7))
        first_full=str(day) if started and complete else str(times[first]+pd.Timedelta(hours=1)) if first is not None and complete else None
        overnight.append({'night_start':str(day),'deadline':str(day+pd.Timedelta(hours=6)),'complete_input_window':complete,'soc_at_0600_kwh':float(final_soc.sum()),'soc_fraction_at_0600':float(final_soc.sum()/e.sum()) if e.sum() else 1.,'all_sites_full_at_0600':bool(np.all(final_soc[installed]>=e[installed]-1e-7)) if complete else None,'first_full_by':first_full,'started_full':started,'scored_period':bool(scored[slots].any())})
    assess=valid&scored
    summary={'replayed_hours':t,'observed_hours':int(assess.sum()),'missing_hours':int((~valid&scored).sum()),'replay_missing_hours':int((~valid).sum()),'hours_above_cap':int(np.nansum(misses[assess]>1e-6)),'worst_miss_kw':float(np.max(misses[assess])) if assess.any() else None,'cap_miss_kwh':float(np.sum(misses[assess])),'peak_grid_kw':float(np.max(total_grid[assess])) if assess.any() else None,'passes_observed_cap':bool(np.max(misses[assess])<=1e-6) if assess.any() else False,'max_energy_balance_residual_kwh':residual,'minimum_soc_fraction':float(np.min(after[installed]/e[installed,None])) if installed.any() else None,'overnight_recharge':overnight,'ending_soc_kwh':float(after[:,-1].sum()),'scored_period_ending_soc_kwh':float(after[:,np.flatnonzero(scored)[-1]].sum())}
    return {'summary':summary,'charge':charge,'discharge':discharge,'soc_start':before,'soc_end':after,'grid':grid,'valid':valid}
