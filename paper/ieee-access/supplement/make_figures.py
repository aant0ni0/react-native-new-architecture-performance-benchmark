#!/usr/bin/env python3
"""Generate vector manuscript figures from the bundled canonical data."""
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'figures'
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE / 'reference/analysis'))
from data_utils import read_csv_measurements, normalize_architecture

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':11,
                     'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
                     'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,
                     'axes.spines.right':False,'savefig.bbox':'tight'})
COLORS = {'RN_Legacy':'#00689D','RN_NewArch':'#D45C29','Native':'#6F7B83'}
LABELS = {'RN_Legacy':'Legacy','RN_NewArch':'New','Native':'Native'}
DEVICES = [('moto-g72','Moto G72'),('pixel-4a','Pixel 4a')]

def save(fig, name):
    fig.savefig(OUT / name, metadata={'Title':name[:-4].replace('_',' '),'Author':'Antoni Michalczak and Filip Kruzel'})
    plt.close(fig)

fig,ax=plt.subplots(figsize=(7.1,2.4))
ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
boxes=[(.01,.53,.29,.42,'Two device contexts','Moto G72 / Pixel 4a\nNominal: 120 / 60 Hz'),
       (.355,.53,.29,.42,'RN 0.81.5 treatments','Shared source; Hermes\nLegacy / New release builds'),
       (.70,.53,.29,.42,'Five workloads','UI updates, scroll, animation\nCalls and process-cold start'),
       (.01,.03,.98,.33,'Run-level evidence','700 canonical records in 70 cells; 10 runs per cell\n40 within-device contrasts; exact permutation tests; RQ-wise Holm correction')]
for x,y,w,h,title,body in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.009,rounding_size=0.018',
                              linewidth=.8,edgecolor='#B6C4CF',facecolor='#F4F8FB'))
    ax.text(x+w/2,y+h*.74,title,ha='center',va='center',fontsize=9.3,fontweight='bold',color='#17445F')
    ax.text(x+w/2,y+h*.36,body,ha='center',va='center',fontsize=8.3,linespacing=1.5)
for x in [.315,.66]:
    ax.add_patch(FancyArrowPatch((x,.74),(x+.027,.74),arrowstyle='-|>',mutation_scale=11,color='#527187',lw=1))
ax.add_patch(FancyArrowPatch((.5,.51),(.5,.38),arrowstyle='-|>',mutation_scale=12,color='#527187',lw=1))
save(fig,'study_design.pdf')

fig,axes=plt.subplots(1,2,figsize=(7.1,2.9),sharey=True,layout='constrained')
for ax,(folder,title) in zip(axes,DEVICES):
    d=normalize_architecture(read_csv_measurements(HERE/'reference/data'/folder/'s1_latency.csv'))
    for k,arch in enumerate(['RN_Legacy','RN_NewArch','Native']):
        med=[]
        for j,interval in enumerate([50,100,200,1000]):
            vals=d[(d.Architecture==arch)&(d.Interval_ms==interval)].Avg_Latency_ms.to_numpy(float)
            med.append(np.median(vals))
            ax.scatter(j+np.linspace(-.065,.065,len(vals))+(k-1)*.11,vals,s=8,color=COLORS[arch],alpha=.3,linewidths=0)
        ax.plot(np.arange(4)+(k-1)*.11,med,'o--' if arch=='Native' else 'o-',lw=1.2,ms=3.5,color=COLORS[arch],label=LABELS[arch])
    ax.set_xticks(range(4),['50','100','200','1000']);ax.set_xlabel('Update interval (ms)')
    ax.set_title(title);ax.grid(axis='y',alpha=.16);ax.set_ylim(0,133)
axes[0].set_ylabel('Run-mean callback delay (ms)');axes[0].legend(frameon=False,fontsize=8,loc='upper left')
save(fig,'callback_delay.pdf')

fig,axes=plt.subplots(1,2,figsize=(7.1,2.9),sharey=True,layout='constrained')
for ax,(folder,title) in zip(axes,DEVICES):
    d=read_csv_measurements(HERE/'reference/data'/folder/'s4_array.csv')
    for k,arch in enumerate(['RN_Legacy','RN_NewArch']):
        med=[]
        for payload in [1,10,100,1000,10000]:
            vals=d[(d.Technology==arch)&(d.Payload_Size==payload)].Operations_per_second.to_numpy(float)
            med.append(np.median(vals))
            ax.scatter(payload*np.geomspace(.86,1.16,len(vals)),vals,s=10,color=COLORS[arch],alpha=.35,linewidths=0)
        ax.plot([1,10,100,1000,10000],med,'o-',lw=1.3,ms=4,color=COLORS[arch],label=LABELS[arch])
    ax.set_xscale('log');ax.set_yscale('log');ax.set_title(title)
    ax.set_xticks([1,10,100,1000,10000],['1','10','100','1000','10000'])
    ax.set_xlabel('Numeric elements per array');ax.grid(axis='y',alpha=.16)
axes[0].set_ylabel('Throughput (operations/s)');axes[0].legend(frameon=False,fontsize=8)
save(fig,'array_throughput.pdf')

fig,axes=plt.subplots(1,2,figsize=(7.1,2.7),sharey=True,layout='constrained')
for ax,(folder,title) in zip(axes,DEVICES):
    d=normalize_architecture(read_csv_measurements(HERE/'reference/data'/folder/'s3_js_driver.csv'))
    for k,arch in enumerate(['RN_Legacy','RN_NewArch']):
        a=d[d.Architecture==arch]
        vals=[np.median(a['FPS modal']),np.median(a.Total_Frames_Rendered/(a.Measured_Duration_ms/1000))]
        bars=ax.bar(np.arange(2)+(k-.5)*.32,vals,width=.30,color=COLORS[arch],label=LABELS[arch],alpha=.95)
        ax.bar_label(bars,labels=[f'{v:.1f}' for v in vals],fontsize=8,padding=2)
    ax.set_xticks([0,1],['Modal callback\nsummary','Graphics count /\nmeasured duration'])
    ax.set_title(title);ax.set_ylim(0,110);ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
axes[0].set_ylabel('Median run-level rate (s$^{-1}$)')
axes[0].legend(frameon=False,fontsize=8,loc='upper left')
save(fig,'animation_boundaries.pdf')
print('Generated four vector figures from canonical observations.')
