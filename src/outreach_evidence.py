"""Business-facing prioritized offers and fixed-rule reference diagnostics.

Customer rankings stay local. Slide figure contains aggregate quantities only.
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from inventory import ROOT
from baseline import digest
from screening import RULES

DEST=ROOT/'data/processed/outreach_evidence'
SOURCE=ROOT/'data/processed/milestone_screening'
PLAN=ROOT/'config/outreach_evidence_plan.json'

def main():
    DEST.mkdir(parents=True,exist_ok=True);plan=json.loads(PLAN.read_text());summary=json.loads((SOURCE/'screening_summary.json').read_text())
    if digest(RULES)!=summary['rules_sha256'] or digest(SOURCE/'features_before_reference.csv')!=summary['features_sha256_before_reference']:raise ValueError('Frozen classifier changed')
    (DEST/'plan_recorded_before_evaluation.json').write_text(json.dumps({'plan':plan,'rules_sha256':digest(RULES),'features_sha256':summary['features_sha256_before_reference']},indent=2))
    offers=pd.read_csv(SOURCE/'customer_to_offer.csv');features=pd.read_csv(SOURCE/'features_before_reference.csv');splits=pd.read_csv(SOURCE/'reference_split.csv')
    recovery=[]
    for tech,score in [('EV','ev_score'),('HP','heating_score')]:
        k=summary['reference_recovery'][tech]['fixed_K'];rank=features.sort_values([score,'CUSTOMER_NUMBER'],ascending=[False,True]).head(k);selected=set(rank.CUSTOMER_NUMBER)
        for split in ['heldout','unused_development']:
            refs=splits[(splits.technology==tech)&(splits.split==split)];qualified=refs[refs.qualifies];hits=len(set(qualified.CUSTOMER_NUMBER)&selected)
            recovery.append({'technology':tech,'reference_subset':split,'listed_references':len(refs),'qualifying_references':len(qualified),'recovered':hits,'fixed_K':k,'recovery':hits/len(qualified),'scope':'Same frozen label-blind rules, no retuning. Likely partial reference recovery, not precision; unlisted unknown. Secondary unused half reported separately, not a prospective ownership validation.'})
    offers['thermal_weather_response_kw']=offers[['heating_weather_response_kw','cooling_weather_response_kw']].max(axis=1)
    offers['thermal_score']=offers[['heating_score','cooling_score']].max(axis=1)
    actions={'managed_charging_offer':'Confirm EV/charger, plug-in window, consent and ready-by; then assess controllable overlap.',
             'thermostat_offer':'Confirm HVAC type and thermostat/control compatibility; assess comfort constraints.',
             'home_battery_offer':'Constrained site-specific sizing, service/interconnection review and installer quote; not approval.',
             'export_eligibility_offer':'Confirm generation surplus, interconnection, meter arrangement and export rights; no payment assumed.'}
    names={'managed_charging_offer':'Managed EV charging','thermostat_offer':'Thermostat outreach','home_battery_offer':'BTM battery assessment','export_eligibility_offer':'PV export eligibility'}
    rows=[];local=[];fields=list(plan['planned_review_budgets'])
    for offer,budget in plan['planned_review_budgets'].items():
        eligible=offers[offers[offer]].copy();columns=plan['ranking'][offer]
        ranked=eligible.sort_values(columns+['CUSTOMER_NUMBER'],ascending=[False]*len(columns)+[True]);chosen=ranked.head(budget).copy()
        chosen['review_rank']=np.arange(1,len(chosen)+1);chosen['program_offer']=offer;chosen['assumed_review_budget']=budget;chosen['recommended_action']=actions[offer]
        local.append(chosen)
        rows.append({'offer':offer,'name':names[offer],'qualified_population':len(offers),'candidate_count':len(eligible),'assumed_review_budget':budget,'planned_reviews':len(chosen),'ranking_fields':columns,'candidate_evening_mean_p50_kw':float(eligible.summer_evening_mean_kw.median()),'review_list_evening_mean_p50_kw':float(chosen.summer_evening_mean_kw.median()),'review_list_priority_metric_p50':float(chosen[columns[0]].median()),'recommended_action':actions[offer],'scope':plan['scope']+' Export list has equal PV evidence: ID tie order is administrative, not benefit ranking.'})
    pd.concat(local,ignore_index=True).to_csv(DEST/'prioritized_customer_offers_LOCAL.csv',index=False)
    combined=offers[fields].astype(int).to_numpy()@np.array([1,2,4,8]);segments=[]
    for mask in range(16):
        selected=offers[combined==mask];label=' + '.join(names[field] for j,field in enumerate(fields) if mask&(1<<j)) or 'Additional evidence needed'
        segments.append({'mask':mask,'offer_combination':label,'count':len(selected),'fraction':len(selected)/len(offers),'evening_mean_p50_kw':float(selected.summer_evening_mean_kw.median()) if len(selected) else None,'scope':'Mutually exclusive combinations of overlapping offer flags; behavior screen, not confirmed appliance inventory.'})
    if sum(s['count'] for s in segments)!=len(offers):raise ValueError('Exclusive segment accounting failed')
    pd.DataFrame(segments).to_csv(DEST/'exclusive_offer_combinations.csv',index=False)
    pd.DataFrame(rows).to_csv(DEST/'program_priority_summary.csv',index=False);pd.DataFrame(recovery).to_csv(DEST/'reference_recovery_both_halves.csv',index=False)
    folder=DEST/'figures';folder.mkdir(exist_ok=True);fig=plt.figure(figsize=(16,9))
    fig.text(.04,.94,'Make the next Avangrid action explicit',fontsize=24,fontweight='bold')
    fig.text(.04,.88,f'{len(offers):,} qualified meters. Offers overlap; review budgets below are assumptions, not enrollments.',fontsize=13)
    ax=fig.add_axes([.04,.44,.92,.37]);ax.axis('off')
    table=[[r['name'],f"{r['candidate_count']:,}",f"{r['planned_reviews']:,}",f"{r['candidate_evening_mean_p50_kw']:.2f}",f"{r['review_list_evening_mean_p50_kw']:.2f}"] for r in rows]
    t=ax.table(cellText=table,colLabels=['Offer','Screened candidates','Planned reviews','Candidate median kW','Review median kW'],cellLoc='left',loc='center',colWidths=[.29,.19,.17,.175,.175]);t.auto_set_font_size(False);t.set_fontsize(12);t.scale(1,2.3)
    fig.text(.04,.43,'kW columns: measured-derived household mean summer 16:00-22:00 demand; not delivered program relief.',fontsize=11)
    fig.text(.04,.36,'HOW TO PRIORITIZE',fontsize=14,fontweight='bold',color='#246c9c')
    lines=['Managed charging: estimated EV-like evening overlap, then EV evidence score -> confirm device, availability and consent.',
           'Thermostats: estimated temperature response, then thermal score -> confirm HVAC, controls and comfort constraints.',
           'BTM batteries: screened residual evening demand, then P90 -> constrained sizing, real site review and quote.',
           'PV: known-list membership only -> verify surplus, metering and export rights; equal evidence gives no benefit ranking.']
    fig.text(.04,.31,'\n'.join(lines),fontsize=12,linespacing=1.8,va='top')
    refs=' | '.join(f"{r['technology']} {r['reference_subset']}: {r['recovered']}/{r['qualifying_references']} at K={r['fixed_K']:,}" for r in recovery)
    fig.text(.04,.10,'Frozen-rule diagnostic (original and secondary halves kept separate):',fontsize=11,fontweight='bold')
    fig.text(.04,.065,refs,fontsize=10)
    fig.text(.04,.025,'Unlisted status unknown; no ownership precision, enrollment, bill savings or population-wide sized BESS inventory established.',fontsize=10)
    outputs=[]
    for ext in ['svg','png']:
        p=folder/f'cleargrid_outreach_priorities.{ext}';fig.savefig(p,dpi=300);outputs.append(p)
    plt.close(fig)
    result={'plan':plan,'population':len(offers),'program_priorities':rows,'exclusive_offer_combinations':segments,'reference_diagnostics':recovery,'scope':plan['scope']}
    path=DEST/'outreach_evidence_results.json';path.write_text(json.dumps(result,indent=2))
    sources=[PLAN,RULES,ROOT/'src/outreach_evidence.py',*[SOURCE/name for name in ['screening_summary.json','features_before_reference.csv','customer_to_offer.csv','reference_split.csv']]]
    outputs += [path,*DEST.glob('*.csv')]
    (DEST/'outreach_evidence_manifest.json').write_text(json.dumps({'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources},'output_sha256':{str(p.relative_to(ROOT)):digest(p) for p in outputs}},indent=2))
    print(json.dumps({'programs':rows,'reference_diagnostics':recovery},indent=2))

if __name__=='__main__':main()
