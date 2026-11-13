r"""Judge-facing impact, method and proposed-pilot visuals from existing outputs.

Run: .\.venv\Scripts\python.exe src/rubric_review.py
No new model fitting, threshold tuning, equipment sizing or deployment claim.
"""
import json
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from baseline import preserve,digest
from inventory import ROOT
from screening import RULES

DEST=ROOT/'data/processed/submission_package'
COLORS=['#246c9c','#287d69','#a85f25','#785b9b']

def wrap(value,width=64):return '\n'.join(textwrap.wrap(str(value),width))

def save(fig,stem):
    paths=[]
    for ext in ['svg','png']:
        path=DEST/'figures'/f'{stem}.{ext}';fig.savefig(path,dpi=300,facecolor='white');paths.append(path)
    plt.close(fig);return paths

def box(fig,left,bottom,width,height,color,title,body,body_size=11):
    fig.patches.append(FancyBboxPatch((left,bottom),width,height,boxstyle='round,pad=0.008',transform=fig.transFigure,facecolor='#f4f7f9',edgecolor=color,linewidth=1.5))
    fig.text(left+.015,bottom+height-.045,title,fontsize=15,color=color,fontweight='bold',va='top')
    fig.text(left+.015,bottom+height-.105,body,fontsize=body_size,va='top',linespacing=1.5)

def impact(base,screening,milestone,stress,replay):
    population=screening['qualifying_population'];ev=screening['reference_recovery']['EV'];hp=screening['reference_recovery']['HP']
    expected_ev=ev['qualifying_heldout_count']*ev['fixed_K']/population
    expected_hp=hp['qualifying_heldout_count']*hp['fixed_K']/population
    b=base['targets']['0.15'];shared=b['shared']['cost'];home=b['home']['cost'];peak=base['summer_peak_kw'];cap=b['cap_kw'];m=milestone['managed_charging'];counts=stress['counts']
    fig=plt.figure(figsize=(13.33,7.5))
    fig.text(.04,.945,'ClearGrid: what the evidence supports for Avangrid',fontsize=21,fontweight='bold')
    fig.text(.04,.895,'A transparent outreach-and-storage decision framework; modeled results require customer and field confirmation.',fontsize=11.5)
    box(fig,.04,.50,.44,.32,COLORS[0],'Outreach evidence',
        f"EV reference recovery: {ev['heldout_recovered']}/{ev['qualifying_heldout_count']} at top {ev['fixed_K']:,} ({ev['recovery_of_qualifying_heldout']:.1%}).\nHeating proxy recovery: {hp['heldout_recovered']}/{hp['qualifying_heldout_count']} at top {hp['fixed_K']:,} ({hp['recovery_of_qualifying_heldout']:.1%}).\nUniform-random expected hits: {expected_ev:.2f} EV / {expected_hp:.2f} HP.\nUnlisted is unknown; no precision estimate is established.")
    box(fig,.52,.50,.44,.32,COLORS[1],'Modeled operating impact',
        f"Measured group peak: {peak:.3f} kW; target cap: {cap:.3f} kW.\nHistorical storage relief: {peak-cap:.3f} kW (15%); zero cap misses.\n50% estimated EV flexibility moved {m['shifted_kwh']:.3f} kWh;\nmanaged charging alone still missed {milestone['options']['managed_charging_alone']['cap_miss_hours']} hours.\nNo energy moved on July 3; storage sizes stayed the same.")
    box(fig,.04,.13,.44,.31,COLORS[2],'Assumed installed-cost result',
        f"15%: shared ${shared:,.0f} vs homes ${home:,.0f}.\nModeled shared advantage: ${home-shared:,.0f}; same amount\nof extra shared installed cost erases it, all else equal.\n10%: homes are lower by ${base['targets']['0.1']['shared']['cost']-base['targets']['0.1']['home']['cost']:,.0f}.\nBaseline targets above; supplemental sweep in final appendix.")
    small_shared=replay['results']['smaller_shared']['hours_above_cap'];small_home=replay['results']['smaller_home']['hours_above_cap']
    box(fig,.52,.13,.44,.31,COLORS[3],'Stress tests bound the claim',
        f"Six additional synthetic groups: {counts['shared_win']} shared wins,\n{counts['home_win']} home wins, {counts['tie']} ties, {counts['unresolved']} unresolved (bounds retained).\nWith July 1-4 excluded, smaller designs missed {small_shared} / {small_home} hours.\nLarger full-record designs passed the causal replay.\nPilot stress validation is needed before an operating claim.")
    fig.text(.04,.055,'Measured AMI/weather; estimated appliance evidence; simulated dispatch; assumed prices. No verified bill savings or upgrade-deferral value.',fontsize=10)
    metrics={'random_outreach_baseline':'Expected qualifying reference hits under uniform sampling of K from the 33,674-person qualified population; expectation only, not a tested classifier or significance test.','ev_random_expected_hits':expected_ev,'hp_random_expected_hits':expected_hp,'ev_recovery_enrichment_vs_uniform_expectation':ev['heldout_recovered']/expected_ev,'hp_recovery_enrichment_vs_uniform_expectation':hp['heldout_recovered']/expected_hp,'screening_accuracy_status':'Partial; subtype identification/precision not established','full_record_historical_peak_reduction_kw':peak-cap,'shared_installed_cost_headroom':home-shared}
    (DEST/'rubric_impact_metrics.json').write_text(json.dumps(metrics,indent=2))
    return save(fig,'cleargrid_rubric_impact')

def workflow(coverage):
    fig=plt.figure(figsize=(13.33,7.5))
    fig.text(.04,.945,'How the model turns meter records into a utility decision',fontsize=21,fontweight='bold')
    steps=[('1  QUALIFY','Complete hourly AMI + weather.\n95% coverage: population;\n99.5%: showcase. Drop gaps.\nWeather joins to hour start.'),
           ('2  SCREEN + ROUTE','Freeze rules; test held-out IDs.\nEV-like plateaus, temperature\nresponse and known-PV lookup.\nRank leads; unlisted is unknown.'),
           ('3  COMPARE','Same cap, hours and load basis;\nsame reserve, efficiency, prices.\nCompare managed load, home BTM\nand shared storage at that cap.'),
           ('4  VALIDATE','Separate full-record sizing\nfrom excluded-date sizing +\ncausal replay. Keep failures,\nsolver bounds and unknowns.')]
    for j,(title,body) in enumerate(steps):box(fig,.035+j*.243,.54,.225,.29,COLORS[j],title,body,10.5)
    fig.text(.045,.455,'Core constraints visible to the reviewer',fontsize=15,fontweight='bold')
    fig.text(.045,.395,'Diversity = sum(individual peaks) / peak(group sum), on the same complete hours. It describes shape; dispatch establishes size.',fontsize=11.3)
    fig.text(.045,.34,'SOC[t+1] = SOC[t] + eta * charge[t] - discharge[t] / eta; eta = sqrt(0.894); SOC >= 20% of capacity.',fontsize=11.5)
    fig.text(.045,.285,'Group load + charge - discharge <= cap; inverter kW and stored kWh are bounded; each home must retain nonnegative grid draw.',fontsize=11.2)
    fig.text(.045,.205,f"DEMONSTRATED: {coverage['rows']:,} local rows ingested; {coverage['population_95']:,} meters screened; showcase + six bounded group comparisons.",fontsize=11.5,color=COLORS[0],fontweight='bold')
    fig.text(.045,.145,'PROPOSED SCALE PATH: batch screening -> confirm technologies/topology -> bounded cohort sizing -> telemetry-based field validation.',fontsize=11.3,color=COLORS[1],fontweight='bold')
    fig.text(.045,.085,'Production integration and million-meter performance are not demonstrated. Synthetic groups are not verified feeder or transformer neighborhoods.',fontsize=10.5)
    fig.text(.045,.04,'Innovation is the linked, auditable decision workflow and fair hardware comparison; no claim of a novel appliance model or a world-first algorithm.',fontsize=10)
    return save(fig,'cleargrid_rubric_workflow')

def pilot():
    fig=plt.figure(figsize=(13.33,7.5))
    fig.text(.04,.945,'Proposed Avangrid pilot: confirm, engineer, shadow, then decide',fontsize=20,fontweight='bold')
    fig.text(.04,.89,'Proposed next steps, not an executed pilot or a deployment approval. Keep customer meters and bills separate unless an approved design changes them.',fontsize=10.7)
    stages=[('1  CONFIRM LEADS','Customer programs',
             'Start with ranked EV-like and thermal leads; verify charger/HVAC, consent and ready-by needs. Check PV eligibility separately.',
             'Record confirmed devices and controllability; measure conversion from outreach, not assumed adoption.'),
            ('2  VERIFY SITE','Distribution planning + interconnection',
             'Obtain real network topology, service limits, installer quotes and a feasible shared connection/metering arrangement.',
             'Screen extra service load near the 3 kVA review trigger; do not treat it as a neighborhood battery cap.'),
            ('3  SHADOW TEST','Operations + installer',
             'Test fixed equipment with telemetry on predeclared peak/stress periods using a causal controller and customer deadlines.',
             'Track cap-miss hours/worst kW, SOC reserve, inverter limits, no-export, energy by 06:00 and recharge readiness.'),
            ('4  GO / NO-GO','Program sponsor + engineering',
             'Require the agreed field target on prospective stress days and a quote-based lifecycle comparison before expansion.',
             'Reassess sizing if misses remain. +$9,250 shared capex erases showcase advantage only with other assumptions unchanged.')]
    for j,(title,owner,action,gate) in enumerate(stages):
        left=.035+j*.243;color=COLORS[j]
        box(fig,left,.22,.225,.59,color,title,'',11)
        fig.text(left+.014,.70,wrap(owner,29),fontsize=10.5,color='#555555',va='top')
        fig.text(left+.014,.62,'ACTION',fontsize=9,fontweight='bold',color=color)
        fig.text(left+.014,.59,wrap(action,33),fontsize=10.5,va='top',linespacing=1.35)
        fig.text(left+.014,.405,'EVIDENCE / GATE',fontsize=9,fontweight='bold',color=color)
        fig.text(left+.014,.375,wrap(gate,33),fontsize=10.5,va='top',linespacing=1.35)
    fig.text(.04,.145,'BTM sites are concrete assessment candidates; the shared design is a planning alternative until topology, metering and interconnection are verified.',fontsize=10.8)
    fig.text(.04,.09,'Measure bill savings only after tariffs/billing are supplied; measure solar value only after surplus/export rights are confirmed. Neither is established here.',fontsize=10.3)
    fig.text(.04,.04,'Why gate expansion: both smaller omitted-date designs failed the heat wave even though overnight recharge completed.',fontsize=11,fontweight='bold')
    return save(fig,'cleargrid_rubric_pilot')

def main():
    (DEST/'figures').mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.parse_math':False})
    b=preserve();source=ROOT/'data/processed';screen_path=source/'milestone_screening/screening_summary.json'
    screen=json.loads(screen_path.read_text())
    if digest(RULES)!=screen['rules_sha256']:raise ValueError('Frozen screening rules changed')
    paths=[b/'showcase_results.json',screen_path,source/'milestone_screening/milestone_results.json',source/'business_stress/stress_results.json',source/'four_design_replay/four_design_results.json',source/'coverage.json']
    base,s,m,stress,replay,coverage=[json.loads(p.read_text()) for p in paths]
    protected=json.loads((source/'final_validation/figure_manifest.json').read_text())['figure_sha256']
    outputs={'rubric_impact':impact(base,s,m,stress,replay),'rubric_workflow':workflow(coverage),'rubric_pilot':pilot()}
    if any(digest(ROOT/p)!=h for p,h in protected.items()):raise ValueError('Preserved historical figure changed')
    (DEST/'rubric_figure_manifest.json').write_text(json.dumps({'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in paths},'output_sha256':{str(p.relative_to(ROOT)):digest(p) for values in outputs.values() for p in values},'scope':'Judge-facing synthesis of existing results and explicitly proposed pilot; no new fitting, device labels, field measurements or operating guarantees.'},indent=2))
    print('Rubric figures generated:',list(outputs))

if __name__=='__main__':main()
