r"""Plot every stress attempt, installed-price sensitivity, and four replay scopes."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from inventory import ROOT
from baseline import preserve,digest

DEST=ROOT/'data/processed/submission_package'

def save(fig,stem):
    out=[]
    for ext in ['png','svg']:
        path=DEST/'figures'/f'{stem}.{ext}';fig.savefig(path,dpi=300,facecolor='white');out.append(path)
    plt.close(fig);return out

def style_table(ax,cells,headers,widths,bbox,fontsize=11):
    table=ax.table(cellText=cells,colLabels=headers,colWidths=widths,cellLoc='center',bbox=bbox)
    table.auto_set_font_size(False);table.set_fontsize(fontsize)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#d6dfe5')
        if r==0:cell.set_facecolor('#246c9c');cell.set_text_props(color='white',weight='bold')
        else:cell.set_facecolor('#f1f5f8' if r%2 else 'white')
    return table

def sensitivity():
    base=json.loads((preserve()/'showcase_results.json').read_text())['targets']['0.15']
    shared=base['shared']['cost'];home=base['home']['cost'];margin=home-shared
    shared_variable=shared-15000;home_modules=sum(base['home']['units'])*8500;home_sites=home-home_modules
    x=np.arange(0,15001,250);table=pd.DataFrame({'assumed_extra_shared_installed_cost':x,'assumed_shared_total_installed_cost':shared+x,'assumed_home_installed_cost':home})
    table.to_csv(DEST/'showcase_cost_sensitivity.csv',index=False)
    fig,ax=plt.subplots(figsize=(13.33,7.5))
    ax.plot(x,shared+x,lw=3,color='#246c9c',label='Shared: base price + extra installed cost')
    ax.axhline(home,color='#a85f25',lw=2,ls='--',label='Coordinated homes: fixed modeled installed cost')
    ax.axvline(margin,color='#666666',ls=':',lw=1.3)
    ax.scatter([margin],[home],color='#333333',s=55,zorder=4)
    ax.annotate(f'Break-even: +${margin:,.0f}\nShared total = ${home:,.0f}',xy=(margin,home),xytext=(margin-4500,home+6000),arrowprops={'arrowstyle':'->','color':'#444444'},fontsize=15,fontweight='bold')
    ax.scatter([0],[shared],color='#246c9c',s=50);ax.annotate(f'Base shared: ${shared:,.0f}',(0,shared),xytext=(700,shared-2500),fontsize=13,color='#246c9c')
    ax.set_ylim(shared-4500,home+11500);ax.set_xlim(0,15000)
    ax.set_xlabel('Assumed additional shared-system installed cost ($)',fontsize=13);ax.set_ylabel('Assumed total installed storage cost ($)',fontsize=13)
    ax.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('${x:,.0f}'));ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter('${x:,.0f}'))
    ax.grid(alpha=.15);ax.legend(loc='lower right',fontsize=11)
    fig.suptitle('15% showcase: shared installed-price sensitivity',fontsize=20,y=.955)
    fig.text(.5,.90,f'Shared: ${shared_variable:,.0f} variable + $15,000 fixed. Homes: ${home_modules:,.0f} modules + ${home_sites:,.0f} site fees.',ha='center',fontsize=11)
    fig.text(.5,.85,f'${home_modules-shared_variable:,.0f} lower variable cost offsets ${15000-home_sites:,.0f} higher fixed/site allowance. Equipment and feasibility held fixed.',ha='center',fontsize=11)
    fig.text(.5,.025,'Historical full-record sizing; assumed installed prices, not quotes. Price sensitivity only, not a target sweep; interconnection/program/O&M costs unpriced.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.06,1,.82])
    return save(fig,'cleargrid_shared_cost_sensitivity')

def heatwave():
    source=ROOT/'data/processed/four_design_replay/four_design_results.json';r=json.loads(source.read_text())
    cells=[]
    for name,option in r['results'].items():
        d=option['design'];larger=name.startswith('historical')
        cells.append([('Larger ' if larger else 'Smaller ')+('shared' if d['option']=='shared' else 'home fleet'),f"{sum(d['power_kw']):.2f} / {sum(d['energy_kwh']):.2f}",'Sized with the full\nhistorical record' if larger else 'July 1-4 excluded\nfrom equipment sizing',str(option['hours_above_cap']),f"{option['worst_miss_kw']:.3f}",'PASS' if option['passes_observed_cap'] else 'FAIL'])
    fig,ax=plt.subplots(figsize=(13.33,7.5));ax.axis('off')
    fig.suptitle('Heat-wave replay: distinguish sizing scope from controller information',fontsize=19,y=.96)
    fig.text(.04,.86,'Same 96 July 1-4 hours; current-load/SOC-only rule; fixed 68.13005 kW cap; no input gaps.',fontsize=13)
    table=style_table(ax,cells,['Design','kW / kWh','Equipment sizing scope','Hours above\ncap','Worst miss\n(kW)','Replay'],[.15,.15,.31,.13,.13,.13],[.015,.33,.97,.44],11)
    for i in range(1,5):table[(i,5)].set_text_props(weight='bold',color='#a33a32' if i<=2 else '#287d69')
    fig.text(.04,.25,'Both smaller designs fail. Both larger designs pass after their equipment sizing already used July 1-4.',fontsize=14,fontweight='bold')
    fig.text(.04,.18,'The larger home fleet uses original display homes 6, 11, 19 (two modules each). A full-record replay is not independent sizing validation.',fontsize=11)
    fig.text(.04,.12,'All four: start full; 20% reserve; 89.4% round-trip efficiency; SOC carries across midnight; recharge whenever cap headroom exists.',fontsize=11)
    fig.text(.04,.06,'All installed sites full by 06:00 on every audited morning. July 5 00:00-06:00 is an unscored recharge audit. Measured AMI + simulated dispatch.',fontsize=10.5)
    ax.set_position([0,0,1,1])
    return save(fig,'cleargrid_heatwave_sizing_scope')

def stress():
    source=ROOT/'data/processed/business_stress/stress_results.json'
    if not source.exists():return []
    r=json.loads(source.read_text());counts=r['counts'];cells=[];full_pairs=0;bound_wins=0
    for group in r['groups']:
        options=group.get('options',{});s=options.get('shared',{});h=options.get('home',{})
        si=s.get('installed_cost_interval',{});hi=h.get('installed_cost_interval',{})
        solved_pair=bool(si.get('certified_minimum_cost') and hi.get('certified_minimum_cost'))
        full_pairs+=int(solved_pair)
        bound_wins+=int(group['outcome'] in ['shared_win','home_win'] and not solved_pair)
        sc=f"${si['upper']:,.0f}" if si.get('upper') is not None else 'No feasible incumbent'
        sc+=f"\n{sum(s.get('power_kw',[])):g} kW / {sum(s.get('energy_kwh',[])):g} kWh"
        if hi.get('upper') is None:hc=f">= ${hi.get('lower',0):,.0f}\nNo incumbent; time limit"
        elif hi['upper']==hi['lower']:hc=f"${hi['upper']:,.0f}\nCost certified"
        else:hc=f"${hi['lower']:,.0f} - ${hi['upper']:,.0f}\nTime-limited incumbent"
        outcome={'shared_win':'Shared win','home_win':'Home win','tie':'Tie','unresolved':'Unresolved'}[group['outcome']]
        cells.append([f"G{group['group']}",str(group.get('common_complete_hours','-')),f"{group.get('observed_common_peak_kw',0):.2f} /\n{group.get('cap_kw',0):.2f}",sc,hc,outcome])
    fig,ax=plt.subplots(figsize=(13.33,7.5));ax.axis('off')
    fig.suptitle('Six additional synthetic groups: stress the assumed installed-cost result',fontsize=18,y=.96)
    fig.text(.04,.875,f"Certified outcomes: {counts['shared_win']} shared wins | {counts['home_win']} home wins | {counts['tie']} ties | {counts['unresolved']} unresolved",fontsize=16,fontweight='bold')
    fig.text(.04,.82,'Seed 2026111301; six disjoint 30-home draws excluding showcase; >=99.5% annual coverage; unshifted loads.',fontsize=11)
    fig.text(.04,.785,'Historical perfect-foresight sizing; same reserve, efficiency and no-export rules; assumed installed storage prices.',fontsize=9.5)
    table=style_table(ax,cells,['Group','Common\nhours','Peak / cap\n(kW)','Shared installed cost\nand equipment','Home installed-cost\ninterval / solver result','Certified\noutcome'],[.07,.10,.14,.22,.29,.18],[.02,.26,.96,.51],10.5)
    for i,g in enumerate(r['groups'],1):
        if g['outcome']=='unresolved':table[(i,5)].set_text_props(color='#a85f25',weight='bold')
    fig.text(.04,.19,'Strict wins use a feasible cost below the other option\'s necessary cost bound. No incumbent does not mean infeasible.',fontsize=11.5)
    fig.text(.04,.13,f'Completed minimum-cost pairs: {full_pairs}; additional bound-certified wins: {bound_wins}. Every attempted group, status and bound is retained.',fontsize=11)
    fig.text(.04,.075,'One-site shared pricing and lower assumed $/kWh help when many home modules/sites are needed; this is not a representative utility sample.',fontsize=11)
    fig.text(.04,.03,'15% of each group\'s own observed common-hour peak; same cap/hours within pairs. No finer showcase target sweep, verified bills or upgrade value.',fontsize=10)
    ax.set_position([0,0,1,1])
    return save(fig,'cleargrid_six_group_business_stress')

def main():
    (DEST/'figures').mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.parse_math':False,'axes.spines.top':False,'axes.spines.right':False})
    protected=json.loads((ROOT/'data/processed/final_validation/figure_manifest.json').read_text())['figure_sha256']
    outputs={'cost_sensitivity':sensitivity(),'heatwave_scope':heatwave(),'six_group_stress':stress()}
    if any(digest(ROOT/p)!=h for p,h in protected.items()):raise ValueError('Preserved historical figure changed')
    (DEST/'business_figure_manifest.json').write_text(json.dumps({'output_sha256':{str(p.relative_to(ROOT)):digest(p) for paths in outputs.values() for p in paths},'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'data/processed/business_stress/stress_results.json',ROOT/'data/processed/four_design_replay/four_design_results.json',preserve()/'showcase_results.json']}},indent=2))
    print('Business/heat-wave figures generated in',DEST/'figures')

if __name__=='__main__':main()
