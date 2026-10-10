#!/usr/bin/env python3
"""Reproduce the manuscript tables and sensitivity analyses from RNArchBench 1.0.4.

No downloads, mobile-device runs, or changes to the reference data are performed.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from itertools import combinations
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import platform
import runpy
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd
import scipy
from scipy.stats import rankdata, false_discovery_control, mannwhitneyu, PermutationMethod

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
REF = HERE / 'reference'
OUT = HERE / 'results'
OUT.mkdir(exist_ok=True)

def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

before = hashes(REF)
with TemporaryDirectory() as tmp:
    work = Path(tmp) / 'reference'
    shutil.copytree(REF, work)
    sys.path.insert(0, str(work / 'analysis'))
    subprocess.run([sys.executable, str(work / 'analysis' / 'validate_data.py')], check=True)
    ns = runpy.run_path(str(work / 'analysis' / 'reproduce_analysis.py'))
    for file in (REF / 'analysis' / 'results').glob('*.csv'):
        a, b = pd.read_csv(file), pd.read_csv(work / 'analysis' / 'results' / file.name)
        pd.testing.assert_frame_equal(a, b, check_exact=False, atol=1e-12, rtol=1e-12)
    archived = ns['stats'].copy()
    samples = []
    def add(rq, device, metric, d, col, mask=None, arch='Architecture'):
        if mask is not None:
            d = d[mask]
        x = d.loc[d[arch] == 'RN_Legacy', col].astype(float).to_numpy()
        y = d.loc[d[arch] == 'RN_NewArch', col].astype(float).to_numpy()
        samples.append((rq, device, metric, x, y))
    for device, d in ns['s1'].groupby('Device', sort=False):
        for interval in [50, 100, 200, 1000]:
            add('RQ1', device, f'Avg callback delay {interval} ms', d, 'Avg_Latency_ms', d.Interval_ms == interval)
    for device, d in ns['s2'].groupby('Device', sort=False):
        for col in ['Effective_FPS', 'Janky_Frames_Percent', 'Frame_P99_ms']:
            add('RQ2', device, col, d, col)
    for mode, merged in ns['s3sets'].items():
        for device, d in merged.groupby('Device', sort=False):
            for col in ['Effective_FPS', 'Janky_Frames_Percent', 'Frame_P99_ms']:
                add('RQ3', device, f'{mode}: {col}', d, col)
    for device, d in ns['scalar_primary_by_device'].items():
        add('RQ4', device, 'Scalar', d, 'Operations_per_second', arch='Technology')
    for device, d in ns['array_by_device'].items():
        for payload in [1, 10, 100, 1000, 10000]:
            add('RQ4', device, f'Array payload {payload}', d, 'Operations_per_second', d.Payload_Size == payload, 'Technology')
    for device, d in ns['s5'].groupby('Device', sort=False):
        add('RQ5', device, 'Cold start', d, 'TotalTime_ms', arch='Technology')
    assert len(samples) == len(archived) == 40
    for row, (rq, device, metric, x, y) in zip(archived.itertuples(index=False), samples):
        assert (row.RQ, row.Device, row.Metric) == (rq, device, metric)
        assert len(x) == len(y) == 10
        assert np.isclose(np.median(x), row.Median_Legacy)
        assert np.isclose(np.median(y), row.Median_New)

    # Every assignment of ten of the twenty pooled observations is included.
    assignments = np.array(list(combinations(range(20), 10)), dtype=np.int8)
    assert assignments.shape == (184756, 10)
    def exact_p(x, y):
        # Doubled average ranks are integers, even when values are tied.
        ranks = np.rint(2 * rankdata(np.r_[x, y], method='average')).astype(np.int16)
        observed = ranks[:10].sum()
        distribution = ranks[assignments].sum(axis=1)
        return min(1.0, 2 * min(np.mean(distribution <= observed), np.mean(distribution >= observed)))

    def holm(p):
        p = np.asarray(p, dtype=float)
        order = np.argsort(p)
        values = np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1))
        answer = np.empty_like(p)
        answer[order] = np.minimum(values, 1)
        return answer

    # Independent implementation check against SciPy, including tied observations.
    for idx in [0, 16]:
        x, y = samples[idx][-2:]
        check = mannwhitneyu(x, y, alternative='two-sided', method=PermutationMethod(n_resamples=np.inf)).pvalue
        assert np.isclose(exact_p(x, y), check, rtol=0, atol=1e-14)

    result = archived.rename(columns={'p': 'p_archived_mc', 'q_BH': 'q_archived_rq_device'}).copy()
    result['p_exact'] = [exact_p(x, y) for _, _, _, x, y in samples]
    for rq, idx in result.groupby('RQ', sort=False).groups.items():
        result.loc[idx, 'p_Holm_RQ'] = holm(result.loc[idx, 'p_exact'])
        result.loc[idx, 'q_BH_RQ'] = false_discovery_control(result.loc[idx, 'p_exact'], method='bh')
    result['p_Holm_all40'] = holm(result.p_exact)
    result.to_csv(OUT / 'primary_contrasts.csv', index=False)

    # Full canonical cell inventory, including descriptive native references.
    inventory = []
    filenames = ['s1_latency.csv', 's2_scroll.csv', 's3_js_driver.csv', 's3_native_driver.csv',
                 's4_scalar.csv', 's4_array.csv', 's5_startup.csv']
    for device in ns['DEVICES']:
        for filename in filenames:
            d = ns['read_csv_measurements'](device.data_dir / filename)
            arch = 'Architecture' if 'Architecture' in d else 'Technology'
            keys = [arch] + [c for c in ['Interval_ms', 'Payload_Size'] if c in d]
            for condition, values in d.groupby(keys):
                inventory.append({'device': device.short_label, 'file': filename,
                                  'condition': str(condition), 'n': len(values)})
    inventory = pd.DataFrame(inventory)
    assert len(inventory) == 70 and inventory.n.sum() == 700 and (inventory.n == 10).all()
    inventory.to_csv(OUT / 'canonical_inventory.csv', index=False)

    # Restore all initial S4 series affected by selective remeasurement.
    # Recalculate redundant throughput from retained counts and durations,
    # rounded to operations/s to match the primary endpoint's resolution.
    alternative = result[result.RQ == 'RQ4'].copy().reset_index(drop=True)
    sensitivity = []
    read = ns['read_csv_measurements']
    initial_moto = read(REF / 'data/moto-g72/raw/s4_scalar_initial.csv')
    initial_pixel = read(REF / 'data/pixel-4a/raw/s4_array_initial.csv')
    for d in [initial_moto, initial_pixel]:
        d['Operations_per_second'] = np.floor(1000 * d.Operations_Count / d.Total_Duration_ms + .5)
    for idx, row in alternative.iterrows():
        changed = (row.Device == 'Moto G72' and row.Metric == 'Scalar') or (row.Device == 'Pixel 4a' and row.Metric in ['Array payload 1', 'Array payload 10'])
        if changed:
            d = initial_moto if row.Device == 'Moto G72' else initial_pixel[initial_pixel.Payload_Size == int(row.Metric.split()[-1])]
            x = d.loc[d.Technology == 'RN_Legacy', 'Operations_per_second'].to_numpy(float)
            y = d.loc[d.Technology == 'RN_NewArch', 'Operations_per_second'].to_numpy(float)
            difference, low, high = ns['bootstrap_median_difference_ci'](x, y, f'initial|{row.Device}|{row.Metric}')
            alternative.loc[idx, ['Median_Legacy', 'Median_New', 'Median_diff_Legacy_minus_New', 'Median_diff_CI95_low', 'Median_diff_CI95_high', 'Cliffs_delta', 'p_exact']] = [np.median(x), np.median(y), difference, low, high, ns['cliffs_delta'](x, y), exact_p(x, y)]
            sensitivity.append({'Device': row.Device, 'Metric': row.Metric,
                                'Canonical_New_median': row.Median_New, 'Initial_New_median': np.median(y),
                                'Legacy_median': np.median(x), 'Initial_Cliffs_delta': ns['cliffs_delta'](x,y),
                                'Initial_CI_low': low, 'Initial_CI_high': high,
                                'Initial_p_exact': exact_p(x,y)})
    alternative['p_Holm_RQ'] = holm(alternative.p_exact)
    alternative['q_BH_RQ'] = false_discovery_control(alternative.p_exact, method='bh')
    alternative.drop(columns=['p_archived_mc','q_archived_rq_device','p_Holm_all40']).to_csv(OUT / 's4_initial_series_contrasts.csv', index=False)
    for row in sensitivity:
        match = alternative[(alternative.Device == row['Device']) & (alternative.Metric == row['Metric'])].iloc[0]
        row['Initial_p_Holm_RQ'] = match.p_Holm_RQ
    pd.DataFrame(sensitivity).to_csv(OUT / 's4_remeasurement_sensitivity.csv', index=False)

    # Endpoint precision sensitivity: use unrounded count/duration throughput.
    continuous = result[result.RQ == 'RQ4'].copy().reset_index(drop=True)
    for idx, row in continuous.iterrows():
        d = ns['scalar_primary_by_device'][row.Device] if row.Metric == 'Scalar' else None
        if row.Metric != 'Scalar':
            payload = int(row.Metric.split()[-1])
            d = ns['array_by_device'][row.Device]
            d = d[d.Payload_Size == payload]
        values = 1000 * d.Operations_Count / d.Total_Duration_ms
        x, y = values[d.Technology == 'RN_Legacy'].to_numpy(), values[d.Technology == 'RN_NewArch'].to_numpy()
        continuous.loc[idx, ['Median_Legacy', 'Median_New', 'p_exact']] = [np.median(x), np.median(y), exact_p(x,y)]
    continuous['p_Holm_RQ'] = holm(continuous.p_exact)
    continuous['q_BH_RQ'] = false_discovery_control(continuous.p_exact, method='bh')
    continuous[['RQ','Device','Metric','Median_Legacy','Median_New','p_exact','p_Holm_RQ','q_BH_RQ']].to_csv(OUT / 's4_unrounded_throughput.csv', index=False)

    def fmt(value, digits=2):
        quantum = Decimal(1).scaleb(-digits)
        return f'{Decimal(f"{value:.10f}").quantize(quantum, rounding=ROUND_HALF_UP):.{digits}f}'
    def pformat(value):
        return '$<0.001$' if value < .001 else '$' + fmt(value, 3) + '$'
    lines = [r'\begin{table*}[!t]', r'\centering',
             r'\caption{S4 sensitivity to restoring the initial measurement series (operations/s).}',
             r'\label{tab:sensitivity}', r'\small\setlength{\tabcolsep}{5pt}',
             r'\begin{tabular}{llrrrrr}',r'\toprule',
             r'Device & Condition & Legacy median & \shortstack{New: canonical-\\series median} & \shortstack{New: initial-\\series median} & Initial $\delta$ & Initial $p_{\mathrm{Holm}}$ \\',r'\midrule']
    for row in sensitivity:
        lines.append(' & '.join([row['Device'],row['Metric'].replace('Array payload','Array'),
                    fmt(row['Legacy_median'],1),fmt(row['Canonical_New_median'],1),fmt(row['Initial_New_median'],1),
                    fmt(row['Initial_Cliffs_delta']),pformat(row['Initial_p_Holm_RQ'])])+r' \\')
    lines.extend([r'\bottomrule',r'\end{tabular}',r'\par\smallskip',r'\begin{minipage}{0.98\textwidth}\footnotesize',
                  r'Ten runs per series. All three initial series are restored together; the other nine RQ4 contrasts retain their canonical observations. The 12 exact tests are adjusted together. Throughput is recomputed from counts and durations and rounded to operations/s. Initial and canonical observations are not pooled.',
                  r'\end{minipage}',r'\end{table*}'])
    (PAPER / 'tables/sensitivity.tex').write_text('\n'.join(lines)+'\n')
    captions = [
        'Update-to-next-frame-callback delay: medians of run-level means (ms).',
        'Scrolling: effective frame-count rate, deadline-based jank, and frame-time P99.',
        'Animation: graphics endpoints for the two React Native driver configurations.',
        'Sequential asynchronous JavaScript--native throughput (operations/s).',
        'Process-cold start: Android ActivityManager TotalTime (ms).']
    for n, (rq, group) in enumerate(result.groupby('RQ', sort=False), 1):
        lines = [r'\begin{table*}[!t]', r'\centering', r'\caption{' + captions[n-1] + '}', r'\label{tab:s' + str(n) + '}',
                 r'\small\setlength{\tabcolsep}{5pt}', r'\begin{tabular}{llrrrrrr}', r'\toprule',
                 r'Device & Condition/metric & Legacy & New & $\Delta_{L-N}$ & 95\% CI for $\Delta_{L-N}$ & $\delta$ & $p_{\mathrm{Holm}}$ \\', r'\midrule']
        for row in group.itertuples(index=False):
            label = row.Metric.replace('Avg callback delay', 'Interval').replace('Array payload', 'Array')
            label = label.replace('Effective_FPS','Frames/s').replace('Janky_Frames_Percent',r'Jank (\%)').replace('Frame_P99_ms','P99 (ms)').replace('JS-driven:','JS:').replace('Native-driven:','Native driver:')
            digits = 3 if 'Jank' in label else 1 if rq == 'RQ4' else 2
            values = [row.Device.split(' (')[0], label, fmt(row.Median_Legacy,digits), fmt(row.Median_New,digits),
                      fmt(row.Median_diff_Legacy_minus_New,digits), '['+fmt(row.Median_diff_CI95_low,digits)+', '+fmt(row.Median_diff_CI95_high,digits)+']',
                      fmt(row.Cliffs_delta),pformat(row.p_Holm_RQ)]
            lines.append(' & '.join(values) + r' \\')
        lines.extend([r'\bottomrule',r'\end{tabular}',r'\par\smallskip',r'\begin{minipage}{0.98\textwidth}\footnotesize',
                      r'Ten runs per architecture and condition. $\Delta_{L-N}$ is the Legacy-minus-New median difference. Positive $\delta$ means larger Legacy values. CIs are pointwise unpaired percentile-bootstrap intervals. Exact permutation $p$-values are Holm-adjusted over all ' + str(len(group)) + ' comparisons in ' + rq + ' across the two devices; device observations remain separate.',r'\end{minipage}',r'\end{table*}'])
        (PAPER / 'tables' / f's{n}.tex').write_text('\n'.join(lines)+'\n')
    s1 = result[result.RQ == 'RQ1']
    reductions = 100 * (s1.Median_Legacy - s1.Median_New) / s1.Median_Legacy
    (PAPER / 'tables/numbers.tex').write_text(
        '\\newcommand{\\CallbackReductionMin}{'+fmt(reductions.min(),1)+'}\n' +
        '\\newcommand{\\CallbackReductionMax}{'+fmt(reductions.max(),1)+'}\n' +
        '\\newcommand{\\SignificantHolm}{'+str(int((result.p_Holm_RQ < .05).sum()))+'}\n' +
        '\\newcommand{\\SignificantBH}{'+str(int((result.q_BH_RQ < .05).sum()))+'}\n')
    summary = {'canonical_records':700,'canonical_cells':70,'primary_contrasts':40,'permutation_assignments':len(assignments),
               'Holm_RQ_significant':int((result.p_Holm_RQ<.05).sum()),'BH_RQ_significant':int((result.q_BH_RQ<.05).sum()),
               'Holm_all40_significant':int((result.p_Holm_all40<.05).sum()),
               's4_unrounded_changes_Holm':int(((continuous.p_Holm_RQ<.05).to_numpy() != (result[result.RQ=='RQ4'].p_Holm_RQ<.05).to_numpy()).sum()),
               'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,
               'archived_CSVs_verified':True,'reference_sha256_unchanged':before == hashes(REF)}
    assert summary['reference_sha256_unchanged']
    (OUT/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    (OUT/'reference_sha256.json').write_text(json.dumps(before,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print(pd.DataFrame(sensitivity).to_string(index=False))
