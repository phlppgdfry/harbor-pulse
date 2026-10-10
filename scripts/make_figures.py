"""Render honest evidence figures; these are not Power BI screenshots."""
import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).resolve().parents[1];E=ROOT/'evidence';OUT=ROOT/'docs/assets';OUT.mkdir(exist_ok=True)
pilot=json.loads((E/'pilot.json').read_text());decision=json.loads((E/'decisions.json').read_text());summary=json.loads((E/'summary.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#243B53','text.color':'#102A43','axes.edgecolor':'#D6E0E8','figure.facecolor':'#F2F5F9','axes.facecolor':'white','savefig.facecolor':'#F2F5F9'})
fig=plt.figure(figsize=(16,9),dpi=140)
fig.text(.045,.935,'Harbor Pulse',fontsize=35,fontweight='bold')
fig.text(.047,.89,'From messy terminal events to defensible decisions',fontsize=19,color='#007F86')
fig.text(.047,.853,'Synthetic portfolio case  /  Python · SQL · Power BI · DAX · CI',fontsize=11,color='#526879')
grid=fig.add_gridspec(1,2,left=.14,right=.96,bottom=.17,top=.77,wspace=.30)
ax=fig.add_subplot(grid[0]);labels=['Dispatch / slots','Extra yard space','Additional staffing'];options=decision['options']
for i,o in enumerate(options):
    ax.errorbar(o['NettoP50']/1000,i,xerr=[[(o['NettoP50']-o['NettoP10'])/1000],[(o['NettoP90']-o['NettoP50'])/1000]],fmt='o',markersize=9,capsize=7,lw=3,color='#007F86' if i==0 else '#5064A0')
ax.axvline(0,color='#BAC7D2',ls='--');ax.set_yticks(range(3),labels);ax.invert_yaxis();ax.set_ylim(2.6,-.6)
ax.set_title('Investment decision: annual net value',loc='left',fontsize=15,fontweight='bold',pad=18)
ax.set_xlabel('€ thousands / median and assumption P10–P90');ax.grid(axis='x',alpha=.16)
ax.text(.02,.03,'After annual opex; one-off investment is separate.\nAssumption ranges, not confidence intervals.',transform=ax.transAxes,fontsize=9,color='#526879')
ax2=fig.add_subplot(grid[1]);means={(r['Groep'],r['Periode']):r['GemiddeldeVertraging'] for r in pilot['summary']}
for label,color,group in [('Intervention','#007F86','Interventie'),('Control','#5064A0','Controle')]:
 ax2.plot([0,1],[means[group,'Voor'],means[group,'Na']],'-o',lw=3,markersize=8,label=label,color=color)
ax2.set_xticks([0,1],['Before','After']);ax2.set_ylim(10,25);ax2.set_ylabel('Mean delay / minutes');ax2.grid(axis='y',alpha=.16);ax2.legend(frameon=False)
ax2.set_title('Simulated, day-blocked pilot',loc='left',fontsize=15,fontweight='bold',pad=18)
ax2.text(.02,.03,f'Difference-in-differences: {pilot["observed_did_minutes"]:.2f} min\n84 lane-day sessions · generated effect: −6 min',transform=ax2.transAxes,fontsize=9,color='#526879')
fig.text(.047,.09,'216 duplicates skipped   ·   36 late corrections   ·   0 unexplained reconciliation difference',fontsize=13,fontweight='bold')
fig.text(.047,.047,'All data and intervention outcomes are fictitious. Figures are generated from reproducible evidence, not Power BI screenshots.',fontsize=9,color='#526879')
fig.savefig(OUT/'case-cover.png');fig.savefig(OUT/'case-cover.svg');plt.close(fig)
print('Rendered evidence cover: PNG + SVG')
