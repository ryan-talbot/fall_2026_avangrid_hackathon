"""Reproduce group 3 and simulate summer caps; all outputs stay under data/."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from inventory import ROOT
from load_data import load
from model import dispatch, diversity, home_design

def serial(r):
    return {k:(v.tolist() if isinstance(v,(np.ndarray,np.generic)) else v) for k,v in r.items() if k not in ['charge','discharge','soc','grid']}

def arguments():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids-config',type=Path,help='Local JSON with customer_numbers in display order and optional expected_inputs')
    parser.add_argument('--output-dir',type=Path,help='Local output directory (default: data/processed, or its original_showcase subdirectory for explicit IDs)')
    parser.add_argument('--check-inputs-only',action='store_true',help='Verify measured inputs and stop before storage sizing')
    return parser.parse_args()

def main(ids_config=None, output_dir=None, check_inputs_only=False):
    a,counts=load()
    dest=Path(output_dir) if output_dir else ROOT/'data/processed'/('original_showcase' if ids_config else '')
    dest.mkdir(parents=True,exist_ok=True)
    ids=np.flatnonzero(counts>=.995*8760)
    expected={}
    if ids_config:
        config=json.loads(Path(ids_config).read_text())
        values=config['customer_numbers']
        if len(values)!=30 or any(type(v) is not int for v in values) or len(set(values))!=30:
            raise ValueError('customer_numbers must contain exactly 30 distinct integer IDs in display order')
        chosen=np.array(values,dtype=int)
        if not np.isin(chosen,ids).all():
            raise ValueError('Explicit IDs must all meet the existing 99.5% annual coverage screen')
        expected=config.get('expected_inputs',{})
        sampling='Explicit local ID-list override; supplied order preserved; random sampler bypassed'
    else:
        groups=np.random.default_rng(20261112).choice(ids,size=(24,30),replace=False)
        chosen=groups[2]
        sampling='default_rng(20261112).choice(ascending qualified IDs, size=(24,30), replace=False), third row; display order preserved'
    np.save(dest/'showcase_ids.npy',chosen)
    times=pd.date_range('2025-09-01',periods=8760,freq='h')
    x=np.asarray(a[chosen],dtype=float)
    summer=(times>='2026-06-01')&(times<'2026-09-01')
    valid=np.isfinite(x).all(axis=0)
    sx=x[:,summer & valid]; st=times[summer & valid]
    peak=float(sx.sum(axis=0).max())
    measured={'summer_peak_kw':peak,'summer_peak_hour_start':str(st[np.argmax(sx.sum(axis=0))]),'summer_hours':len(st),'summer_diversity':diversity(sx)}
    checks={}
    for key,value in expected.items():
        if key not in measured: raise ValueError(f'Unsupported expected input: {key}')
        if key=='summer_peak_kw': passed=bool(np.isclose(measured[key],value,rtol=0,atol=1e-5))
        elif key=='summer_diversity': passed=bool(np.isclose(measured[key],value,rtol=0,atol=1e-6))
        elif key=='summer_peak_hour_start': passed=pd.Timestamp(measured[key])==pd.Timestamp(value)
        else: passed=measured[key]==value
        checks[key]={'expected':value,'actual':measured[key],'passed':passed}
    inputs={'sampling':sampling,**measured,'expected_input_checks':checks,'missing_summer_hours':int((~valid[summer]).sum())}
    (dest/'input_checks.json').write_text(json.dumps(inputs,indent=2))
    print('Measured inputs:',json.dumps(inputs),flush=True)
    if not all(v['passed'] for v in checks.values()):
        raise ValueError(f'Input checks differ; storage sizing blocked. Inspect {dest / "input_checks.json"} and preprocessing before interpreting costs.')
    if check_inputs_only: return dest
    # Break at gaps: full SOC at both sides, no SOC transfer or invented usage.
    breaks=np.flatnonzero((st[1:]-st[:-1])!=pd.Timedelta(hours=1))+1
    w=pd.read_excel(next((ROOT/'data/raw').glob('Weather*')))
    w['timestamp']=pd.to_datetime(w['date'].astype(str)+' '+w['time'].astype(str))
    duplicates=w[w.timestamp.duplicated(False)].astype(str).to_dict('records')
    w=w.groupby('timestamp')[['temp','humidity','windspeed']].mean().reindex(times)
    w.to_csv(dest/'weather_hour_start.csv',index_label='hour_start')
    report={'labels':{'load':'measured hourly AMI, synthetic neighborhood','dispatch':'simulated perfect-foresight grid-charged storage on complete common hours only; full SOC at each contiguous segment boundary; no claim for missing hours','costs':'assumed installed prices; no bill savings'},**inputs,'coverage':json.loads((ROOT/'data/processed/coverage.json').read_text()),'weather_duplicate_rows':duplicates,'weather_missing_slots':int(w.isna().any(axis=1).sum()),'segment_starts':[str(st[h]) for h in [0,*breaks]],'targets':{}}
    (dest/'showcase_results.json').write_text(json.dumps(report,indent=2))
    for target in [.10,.15]:
        cap=peak*(1-target)
        print('solving',target,'cap',cap,flush=True)
        shared=dispatch(sx.sum(axis=0),cap,optimize='shared',breaks=breaks)
        print('shared',serial(shared),flush=True)
        home=home_design(sx,cap,time_limit=300,breaks=breaks)
        print('home',serial(home),flush=True)
        report['targets'][str(target)]={'cap_kw':cap,'flexibility_alone_feasible':False,'shared':serial(shared),'home':serial(home)}
        report['targets'][str(target)]['july3_minimum_discharge_kwh']=float(np.maximum(sx.sum(axis=0)[st.date==pd.Timestamp('2026-07-03').date()]-cap,0).sum())
        for name,r in [('shared',shared),('home',home)]:
            if not r['feasible']: continue
            frame=pd.DataFrame({'hour_start':st,'measured_load_kw':sx.sum(axis=0),'simulated_grid_kw':r['grid'].sum(axis=0),'simulated_charge_kw':r['charge'].sum(axis=0),'simulated_discharge_kw':r['discharge'].sum(axis=0),'simulated_soc_kwh':r['soc'].sum(axis=0),'cap_kw':cap})
            frame.to_csv(dest/f'dispatch_{target:.0%}_{name}.csv',index=False)
        (dest/'showcase_results.json').write_text(json.dumps(report,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
    for ax,target in zip(axes,[.10,.15]):
        f=None
        for name in ['shared','home']:
            if not report['targets'][str(target)][name]['feasible']: continue
            f=pd.read_csv(dest/f'dispatch_{target:.0%}_{name}.csv',parse_dates=['hour_start'])
            f=f[(f.hour_start>='2026-07-03')&(f.hour_start<'2026-07-05')]
            ax.plot(f.hour_start,f.simulated_grid_kw,label=f'Simulated {name} grid')
        if f is None:
            ax.text(.1,.5,f'{target:.0%}: no feasible incumbent returned',transform=ax.transAxes)
            continue
        ax.plot(f.hour_start,f.measured_load_kw,color='black',alpha=.5,label='Measured AMI sum')
        ax.axhline(f.cap_kw.iloc[0],color='red',ls='--',label=f'{target:.0%} cap')
        ax.set_ylabel('Hourly average kW'); ax.legend(fontsize=8)
    fig.suptitle('Synthetic 30-home group: July 3 and after-midnight recharge\n20% reserve, 89.4% round-trip efficiency; perfect-foresight simulation')
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(dest/'july3_dispatch.png',dpi=150)
    return dest

if __name__=='__main__':
    args=arguments()
    main(args.ids_config,args.output_dir,args.check_inputs_only)
