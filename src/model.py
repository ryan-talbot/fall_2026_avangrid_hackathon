"""Hourly storage MILP, AC kW and internal DC kWh; one-hour steps."""
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix

ETA=np.sqrt(.894)

def home_cost_bound(load,cap,export=False):
    """Necessary equipment counts from AC power and per-home no-export.

    Test every possible one- and two-site placement at maximum site power.
    If none covers every deficient hour, at least three sites are necessary.
    This is a lower bound only: it does not assert energy feasibility.
    """
    from itertools import combinations
    x=np.atleast_2d(np.asarray(load,float))
    deficit=np.maximum(x.sum(axis=0)-cap,0)
    modules=int(np.ceil(max(0,deficit.max()-1e-8)/3.84))
    sites=int(np.ceil(modules/2))
    if modules:
        available=np.full_like(x,7.68) if export else np.minimum(7.68,np.maximum(x,0))
        for count in range(1,min(2,len(x))+1):
            if not any(np.all(available[list(combo)].sum(axis=0)>=deficit-1e-7)
                       for combo in combinations(range(len(x)),count)):
                sites=max(sites,count+1)
        modules=max(modules,sites)
    return {'modules':modules,'sites':sites,'cost':8500*modules+3000*sites}

def diversity(load):
    x=np.asarray(load,float)
    if x.ndim!=2 or not np.isfinite(x).all(): raise ValueError('Use one common complete window')
    peak=x.sum(axis=0).max()
    return x.max(axis=1).sum()/peak if peak>0 else float('nan')

def dispatch(load, cap, energy=None, power=None, reserve=.2, eta=ETA, optimize=None, export=False, time_limit=180, breaks=()):
    """Rows are sites. Full initial and terminal SOC; cap includes recharge.

    optimize='home': integer single modules (10.08kWh/3.84kW), site fees.
    optimize='shared': 5kWh and 2.5kW increments, illustrative price.
    Fixed designs: energy and power arrays. No export is per site.
    """
    x=np.atleast_2d(np.asarray(load,float)); n,t=x.shape
    starts={0,*breaks}; ends={t-1,*[h-1 for h in breaks]}
    if not np.isfinite(x).all(): raise ValueError('Missing load cannot be dispatched')
    # Variables: charge, discharge, SOC (end of each hour), design, site.
    size=3*n*t + (2*n if optimize else 0)
    obj=np.zeros(size); lower=np.zeros(size); upper=np.full(size,np.inf); integrality=np.zeros(size)
    obj[:2*n*t]=1e-5
    rows=[]; cols=[]; vals=[]; lo=[]; hi=[]
    def add(terms,l=-np.inf,u=np.inf):
        r=len(lo)
        for c,v in terms: rows.append(r); cols.append(c); vals.append(v)
        lo.append(l); hi.append(u)
    def c(i,h): return i*t+h
    def d(i,h): return n*t+i*t+h
    def s(i,h): return 2*n*t+i*t+h
    if optimize=='home':
        # Valid rounded cuts: even ideal placements need this many modules
        # and sites to meet the largest AC power deficit. These improve the
        # relaxation without changing the feasible equipment combinations.
        bound=home_cost_bound(x,cap,export)
        add([(3*n*t+i,1) for i in range(n)],l=bound['modules'])
        add([(3*n*t+n+i,1) for i in range(n)],l=bound['sites'])
    for i in range(n):
        if optimize:
            q=3*n*t+i; z=3*n*t+n+i
            integrality[q]=integrality[z]=1
            if optimize=='home':
                e,p=10.08,3.84; upper[q]=2; upper[z]=1; obj[q]=8500; obj[z]=3000
                add([(q,1),(z,-2)],u=0)
            else:
                # q energy steps, z power steps, no site variable.
                e,p=5,2.5; upper[q]=1000; upper[z]=1000; obj[q]=3250; obj[z]=.01
        else:
            e=float(np.broadcast_to(energy,(n,))[i]); p=float(np.broadcast_to(power,(n,))[i])
        for h in range(t):
            if optimize:
                add([(c(i,h),1),((z if optimize=='shared' else q),-p)],u=0)
                add([(d(i,h),1),((z if optimize=='shared' else q),-p)],u=0)
                add([(s(i,h),1),(q,-e)],u=0)
                add([(s(i,h),1),(q,-reserve*e)],l=0)
            else:
                upper[c(i,h)]=upper[d(i,h)]=p
                lower[s(i,h)]=reserve*e; upper[s(i,h)]=e
            if not export: add([(d(i,h),1),(c(i,h),-1)],u=x[i,h])
            terms=[(s(i,h),1),(c(i,h),-eta),(d(i,h),1/eta)]
            if h not in starts: terms.append((s(i,h-1),-1)); rhs=0
            elif optimize: terms.append((q,-e)); rhs=0
            else: rhs=e
            add(terms,l=rhs,u=rhs)
        for h in ends:
            if optimize: add([(s(i,h),1),(q,-e)],l=0,u=0)
            else: add([(s(i,h),1)],l=e,u=e)
    caps=np.broadcast_to(cap,(t,))
    for h in range(t): add([(c(i,h),1) for i in range(n)]+[(d(i,h),-1) for i in range(n)],u=caps[h]-x[:,h].sum())
    a=coo_matrix((vals,(rows,cols)),shape=(len(lo),size)).tocsc()
    r=milp(obj,integrality=integrality,bounds=Bounds(lower,upper),constraints=LinearConstraint(a,lo,hi),options={'time_limit':time_limit,'mip_rel_gap':0.00001})
    out={'status':int(r.status),'message':r.message,'feasible':r.x is not None}
    if r.x is None: return out
    v=r.x; charge=v[:n*t].reshape(n,t); discharge=v[n*t:2*n*t].reshape(n,t); soc=v[2*n*t:3*n*t].reshape(n,t)
    if optimize:
        units=np.rint(v[3*n*t:3*n*t+n]).astype(int); sites=np.rint(v[3*n*t+n:]).astype(int)
        energies=units*e; powers=(sites if optimize=='shared' else units)*p
        cost=15000+3250*units.sum() if optimize=='shared' else 8500*units.sum()+3000*sites.sum()
        if optimize=='shared':
            out.update(energy_steps=units.tolist(),power_steps=sites.tolist())
            sites=np.ones(n,dtype=int)
    else: energies=np.broadcast_to(energy,(n,)); powers=np.broadcast_to(power,(n,)); units=sites=None; cost=None
    grid=x+charge-discharge
    previous=np.column_stack([energies,soc[:,:-1]])
    for h in starts: previous[:,h]=energies
    residual=float(np.abs(soc-previous-eta*charge+discharge/eta).max())
    violations=[residual,float(max(0,(grid.sum(axis=0)-caps).max())),float(max(0,(reserve*energies[:,None]-soc).max())),float(max(0,(soc-energies[:,None]).max())),float(max(0,(charge-powers[:,None]).max())),float(max(0,(discharge-powers[:,None]).max())),float(np.abs(soc[:,sorted(ends)]-energies[:,None]).max())]
    if not export: violations.append(float(max(0,-grid.min())))
    if max(violations)>1e-5: raise RuntimeError(f'Dispatch verification failed: {violations}')
    out.update(charge=charge,discharge=discharge,soc=soc,grid=grid,energy_kwh=energies,power_kw=powers,units=units,sites=sites,cost=cost,max_cap_miss_kw=violations[1],minimum_soc_margin=float((soc-reserve*energies[:,None]).min()),max_simultaneous_kw=float(np.minimum(charge,discharge).max()),max_balance_residual_kwh=residual,mip_gap=getattr(r,'mip_gap',None),mip_dual_bound=getattr(r,'mip_dual_bound',None))
    return out

def home_energy_bound(load,cap,breaks=()):
    """Strengthen necessary counts using a shared, high-power relaxation.

    Any feasible home fleet can be aggregated into this relaxed store. Proven
    infeasibility at m modules therefore proves that every home fleet needs
    at least m+1 modules. All observed hours and recharge limits are retained.
    """
    x=np.asarray(load,float)
    bound=home_cost_bound(x,cap)
    modules=bound['modules']; checks=[]
    relaxed_power=max(7.68*len(x),2*max(float(x.sum(axis=0).max()),float(np.max(cap))))
    while modules<=2*len(x) and modules>0:
        r=dispatch(x.sum(axis=0),cap,energy=[modules*10.08],power=[relaxed_power],breaks=breaks)
        checks.append({'modules':modules,'energy_kwh':modules*10.08,'solver_status':r['status'],'feasible':r['feasible']})
        if r['status']!=2: break
        modules+=1
    sites=max(bound['sites'],int(np.ceil(modules/2)))
    return {'modules':modules,'sites':sites,'cost':8500*modules+3000*sites,'aggregate_energy_checks':checks,'relaxed_power_kw':relaxed_power}

def home_design(load,cap,breaks=(),time_limit=300):
    """Try all placements at a proven cost bound, then fall back to MILP.

    For <=3 sites this avoids a large mixed-integer search. Each candidate
    must pass a continuous full-horizon dispatch, including every recharge
    hour. Finding one at the necessary cost bound proves minimum cost.
    """
    from itertools import combinations
    x=np.asarray(load,float); n,t=x.shape
    bound=home_energy_bound(x,cap,breaks); m,s=bound['modules'],bound['sites']
    deficit=np.maximum(x.sum(axis=0)-cap,0)
    if 1<=s<=3 and s<=m<=2*s:
        for installed in combinations(range(n),s):
            for doubled in combinations(installed,m-s):
                units=np.zeros(n,dtype=int); units[list(installed)]=1; units[list(doubled)]=2
                powers=units*3.84
                if np.any(np.minimum(powers[:,None],x).sum(axis=0)<deficit-1e-7): continue
                chosen=np.array(installed)
                # Non-battery homes remain measured, unmodified grid load.
                residual_cap=cap-(x.sum(axis=0)-x[chosen].sum(axis=0))
                r=dispatch(x[chosen],residual_cap,energy=units[chosen]*10.08,power=powers[chosen],breaks=breaks,time_limit=time_limit)
                if not r['feasible']: continue
                for key in ['charge','discharge','soc']:
                    full=np.zeros_like(x); full[chosen]=r[key]; r[key]=full
                r.update(grid=x+r['charge']-r['discharge'],energy_kwh=units*10.08,power_kw=powers,units=units,sites=(units>0).astype(int),cost=bound['cost'],status=0,
                         message='Minimum equipment cost certified by necessary counts and feasible full-horizon LP dispatch',mip_gap=0.0,mip_dual_bound=float(bound['cost']),method='placement enumeration at necessary cost bound; full-horizon LP replay',necessary_equipment_bound=bound)
                return r
    return dispatch(x,cap,optimize='home',breaks=breaks,time_limit=time_limit)
