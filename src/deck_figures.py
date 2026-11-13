"""Deck-ready PNG/SVG figures drawn only from verified model output tables."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from baseline import digest
from inventory import ROOT

COLORS={'shared':'#246c9c','home':'#c26b26','measured':'#292929','cap':'#b83c3c'}

def save(fig,directory,stem):
    paths=[]
    for extension in ['png','svg']:
        path=directory/f'{stem}.{extension}'
        fig.savefig(path,dpi=300,facecolor='white')
        paths.append(path)
    plt.close(fig)
    return paths

def night_shading(axes,start,stop):
    for day in pd.date_range(pd.Timestamp(start).normalize(),pd.Timestamp(stop).normalize(),freq='D'):
        left=max(pd.Timestamp(start),day); right=min(pd.Timestamp(stop),day+pd.Timedelta(hours=6))
        if left<right:
            for ax in axes: ax.axvspan(left,right,color='#dbe6ed',alpha=.42,zorder=0)

def step(ax,times,values,**kwargs):
    values=np.asarray(values,float)
    tx=pd.DatetimeIndex(times).append(pd.DatetimeIndex([times.iloc[-1]+pd.Timedelta(hours=1)]))
    ax.step(tx,np.r_[values,values[-1]],where='post',**kwargs)

def historical(dest,baseline_dir,base,milestone):
    frames={name:pd.read_csv(baseline_dir/f'dispatch_15%_{name}.csv',parse_dates=['hour_start']) for name in ['shared','home']}
    start=pd.Timestamp('2026-07-03'); stop=pd.Timestamp('2026-07-05 06:00')
    frames={k:v[(v.hour_start>=start)&(v.hour_start<stop)].reset_index(drop=True) for k,v in frames.items()}
    shared=frames['shared']; home=frames['home']
    if not shared.hour_start.equals(home.hour_start): raise ValueError('Historical dispatch axes differ')
    output=pd.DataFrame({'hour_start':shared.hour_start,'measured_load_kw':shared.measured_load_kw,'cap_kw':shared.cap_kw})
    for name,frame in frames.items():
        for column in ['simulated_grid_kw','simulated_charge_kw','simulated_discharge_kw','simulated_soc_kwh']:
            output[f'{name}_{column}']=frame[column]
    output.to_csv(dest/'historical_july3_figure_data.csv',index=False)
    fig,axes=plt.subplots(3,1,figsize=(13.33,7.5),sharex=True,gridspec_kw={'height_ratios':[1.5,1,1]})
    t=shared.hour_start
    step(axes[0],t,shared.measured_load_kw,label='Measured AMI: 30-home sum',color=COLORS['measured'],lw=1.8)
    cap=float(base['targets']['0.15']['cap_kw'])
    for name,frame in frames.items():
        label='Shared' if name=='shared' else 'Coordinated homes'; ls='-' if name=='shared' else '--'
        step(axes[0],t,frame.simulated_grid_kw,label=f'Simulated {label.lower()} grid',color=COLORS[name],ls=ls,lw=1.8)
        step(axes[1],t,frame.simulated_charge_kw-frame.simulated_discharge_kw,label=label,color=COLORS[name],ls=ls,lw=1.6)
        capacity=sum(base['targets']['0.15'][name]['energy_kwh'])
        axes[2].step(t+pd.Timedelta(hours=1),100*frame.simulated_soc_kwh/capacity,where='post',label=f'{label}: {capacity:.2f} kWh',color=COLORS[name],ls=ls,lw=1.8)
    axes[0].axhline(cap,color=COLORS['cap'],ls=':',lw=1.7,label=f'15% cap: {cap:.2f} kW')
    axes[1].axhline(0,color='#666666',lw=.7)
    axes[2].axhline(20,color=COLORS['cap'],ls=':',lw=1.4,label='20% reserve')
    axes[0].set_ylabel('Grid / load (kW)'); axes[1].set_ylabel('Charge + / discharge -\n(kW)'); axes[2].set_ylabel('State of charge (%)'); axes[2].set_ylim(10,105)
    for j,ax in enumerate(axes):
        ax.grid(alpha=.16)
        ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),borderaxespad=0,frameon=False,fontsize=9,ncol=4 if j==0 else 3)
    night_shading(axes,start,stop)
    axes[-1].set_xlim(start,stop); axes[-1].xaxis.set_major_locator(mdates.HourLocator(byhour=[0,12])); axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    fig.suptitle('July 3 historical comparison: perfect-foresight sizing and dispatch',fontsize=18,y=.985)
    fig.text(.5,.925,'Full summer used for sizing; measured unshifted AMI and simulated storage. This is historical feasibility, not a held-out result.',ha='center',fontsize=10)
    fig.text(.5,.018,'Shading: 00:00-06:00. Grid recharge allowed whenever cap headroom exists; SOC carries across midnight. RTE 89.4%.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.05,1,.92])
    return save(fig,dest/'figures','cleargrid_historical_july3')

def installed_costs(dest,base):
    records=[]
    for target in ['0.1','0.15']:
        case=base['targets'][target]
        for name in ['home','shared']:
            r=case[name]
            if not r['feasible']: raise ValueError('Do not plot infeasible historical options as cost choices')
            records.append({'target_fraction':float(target),'cap_kw':case['cap_kw'],'option':name,'assumed_installed_cost':r['cost'],'power_kw':sum(r['power_kw']),'energy_kwh':sum(r['energy_kwh']),'sites':sum(r['sites']),'sizing_scope':'Historical full-summer perfect foresight'})
    table=pd.DataFrame(records); table.to_csv(dest/'historical_installed_cost_figure_data.csv',index=False)
    fig,ax=plt.subplots(figsize=(13.33,7.5)); positions=np.arange(2); width=.32
    for offset,name in [(-width/2,'home'),(width/2,'shared')]:
        rows=table[table.option==name]
        bars=ax.bar(positions+offset,rows.assumed_installed_cost,width,label='Coordinated homes' if name=='home' else 'Shared storage',color=COLORS[name])
        for bar,(_,row) in zip(bars,rows.iterrows()):
            center=bar.get_x()+bar.get_width()/2
            ax.text(center,row.assumed_installed_cost+1200,f'${row.assumed_installed_cost:,.0f}',ha='center',va='bottom',fontsize=15,fontweight='bold')
            ax.text(center,row.assumed_installed_cost*.50,f"{row.power_kw:g} kW\n{row.energy_kwh:g} kWh\n{int(row.sites)} site{'s' if row.sites!=1 else ''}",ha='center',va='center',fontsize=13,color='white')
    for j,target in enumerate([.10,.15]):
        case=table[table.target_fraction==target].set_index('option')
        saving=abs(case.loc['shared','assumed_installed_cost']-case.loc['home','assumed_installed_cost'])
        cheaper=case.assumed_installed_cost.idxmin(); label='Homes' if cheaper=='home' else 'Shared'
        ax.text(j,66000,f'{label} lower by ${saving:,.0f}',ha='center',fontsize=13,color=COLORS[cheaper])
    caps=[base['targets'][v]['cap_kw'] for v in ['0.1','0.15']]
    ax.set_xticks(positions,[f'10% target\n{caps[0]:.2f} kW cap',f'15% target\n{caps[1]:.2f} kW cap'],fontsize=14)
    ax.set_ylim(0,73500); ax.set_ylabel('Assumed installed storage cost ($)',fontsize=13); ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('${x:,.0f}'))
    ax.legend(loc='lower center',bbox_to_anchor=(.5,1.015),borderaxespad=0,frameon=False,ncol=2,fontsize=12); ax.grid(axis='y',alpha=.15); ax.set_axisbelow(True)
    fig.suptitle('Historical installed-cost comparison: 10% versus 15% peak reduction',fontsize=18,y=.98)
    fig.text(.5,.92,'Verified 30-home group; full-summer perfect-foresight sizing. Held-out heat-wave performance is reported separately.',ha='center',fontsize=11)
    fig.text(.5,.025,'Assumed prices: $8,500/module + $3,000/home site; shared $15,000 + $650/kWh. No program costs or bill savings included.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.06,1,.9])
    return save(fig,dest/'figures','cleargrid_installed_costs_10_vs_15')

def withheld(dest,heldout,cap):
    frames={name:pd.read_csv(dest/f'withheld_{name}.csv',parse_dates=['hour_start']) for name in ['shared','home']}
    common=frames['shared']; t=common.hour_start; start=t.iloc[0]; stop=t.iloc[-1]+pd.Timedelta(hours=1)
    fig,axes=plt.subplots(3,1,figsize=(13.33,7.5),sharex=True,gridspec_kw={'height_ratios':[1.5,1,1]})
    step(axes[0],t,common.measured_load_kw,color=COLORS['measured'],lw=1.5,label='Measured AMI: 30-home sum')
    for name,frame in frames.items():
        option=heldout['options'][name]; label='Shared' if name=='shared' else 'Coordinated homes'; ls='-' if name=='shared' else '--'
        step(axes[0],t,frame.simulated_causal_grid_kw,color=COLORS[name],ls=ls,lw=1.6,label=f'Causal {label.lower()}')
        step(axes[1],t,frame.simulated_charge_kw-frame.simulated_discharge_kw,color=COLORS[name],ls=ls,lw=1.6,label=label)
        energy=sum(option['energy_kwh'])
        soc=np.r_[frame.simulated_soc_start_kwh.iloc[0],frame.simulated_soc_end_kwh]
        tx=pd.DatetimeIndex(t).append(pd.DatetimeIndex([stop]))
        axes[2].step(tx,100*soc/energy,where='post',color=COLORS[name],ls=ls,lw=1.6,label=f'{label}: {energy:.2f} kWh')
    axes[0].axhline(cap,color=COLORS['cap'],ls=':',lw=1.6,label=f'Fixed cap: {cap:.2f} kW')
    axes[1].axhline(0,color='#666666',lw=.7); axes[2].axhline(20,color=COLORS['cap'],ls=':',lw=1.4,label='20% reserve'); axes[2].set_ylim(10,105)
    for j,ax in enumerate(axes):
        ax.grid(alpha=.15)
        ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),borderaxespad=0,frameon=False,fontsize=9,ncol=4 if j==0 else 3)
        ax.axvspan(pd.Timestamp('2026-07-05'),stop,color='#dedede',alpha=.6,zorder=0)
    night_shading(axes,start,stop)
    axes[0].set_ylabel('Grid / load (kW)'); axes[1].set_ylabel('Charge + / discharge -\n(kW)'); axes[2].set_ylabel('State of charge (%)')
    axes[-1].set_xlim(start,stop); axes[-1].xaxis.set_major_locator(mdates.HourLocator(byhour=[0,12])); axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    fig.suptitle('Withheld July 1-4: frozen equipment and causal dispatch',fontsize=18,y=.985)
    summaries=[]
    for name in ['shared','home']:
        r=heldout['options'][name]; label='Shared' if name=='shared' else 'Homes'; outcome='PASS' if r['passes_observed_cap'] else 'FAIL'; summaries.append(f"{label} {outcome}: {r['hours_above_cap']} miss hours; worst {r['worst_miss_kw']:.2f} kW")
    fig.text(.5,.925,' | '.join(summaries),ha='center',fontsize=12,color=COLORS['cap'])
    fig.text(.5,.018,'No future load used; start 100% SOC; no midnight reset. Blue shading: 00:00-06:00. Gray July 5: recharge audit, not scored.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.05,1,.92])
    return save(fig,dest/'figures','cleargrid_withheld_july1_4')

def generate(dest,baseline_dir,base,milestone,heldout):
    (dest/'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.parse_math':False,'axes.spines.top':False,'axes.spines.right':False})
    paths={'historical_july3':historical(dest,baseline_dir,base,milestone),'installed_costs_10_vs_15':installed_costs(dest,base),'withheld_july1_4':withheld(dest,heldout,base['targets']['0.15']['cap_kw'])}
    sources=[baseline_dir/'showcase_results.json',baseline_dir/'dispatch_15%_shared.csv',baseline_dir/'dispatch_15%_home.csv',dest/'historical_july3_figure_data.csv',dest/'historical_installed_cost_figure_data.csv',dest/'withheld_shared.csv',dest/'withheld_home.csv']
    manifest={'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources},'figure_sha256':{str(p.relative_to(ROOT)):digest(p) for values in paths.values() for p in values},'formats':'300 dpi PNG and vector SVG','historical_scope':'Full-summer perfect-foresight sizing and dispatch; unshifted measured load','withheld_scope':'July 1-4 excluded from sizing; frozen equipment; causal rule; July 5 extension for recharge audit only','current_managed_scenario_july3_shifted_kwh':milestone['managed_charging']['july3_day_removed_kwh']}
    (dest/'figure_manifest.json').write_text(json.dumps(manifest,indent=2))
    return paths
