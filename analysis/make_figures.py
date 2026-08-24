from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from data_utils import load_device_registry

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).resolve().parent / "results"
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
DEVICES = load_device_registry()


def save(name):
    """Save both formats atomically so interrupted/synced writes do not leave 0-byte figures."""
    plt.tight_layout()
    targets = [
        (FIG / f"{name}.pdf", "pdf", {}),
        (FIG / f"{name}.png", "png", {"dpi": 300}),
    ]
    try:
        for target, fmt, extra in targets:
            tmp = target.with_name(target.name + ".tmp")
            plt.savefig(tmp, format=fmt, bbox_inches="tight", **extra)
            if not tmp.exists() or tmp.stat().st_size == 0:
                raise RuntimeError(f"Figure write failed or produced an empty file: {tmp}")
            tmp.replace(target)
    finally:
        plt.close()


# Figure 1: cross-device update-to-next-frame-callback delay reduction
r = pd.read_csv(RESULTS / "s1_new_vs_legacy_reduction.csv")
plt.figure(figsize=(7.2, 4.4))
for device in DEVICES:
    label = device.display_label
    group = r[r["Device"] == label].sort_values("Interval_ms")
    plt.plot(group["Interval_ms"], group["New_reduction_pct"], marker="o", label=label)
plt.xscale("log")
plt.xticks([50, 100, 200, 1000], ["50", "100", "200", "1000"])
plt.xlabel("Update interval (ms)")
plt.ylabel("Callback-delay reduction vs Legacy (%)")
plt.legend()
plt.grid(axis="y", alpha=0.25)
save("fig1_s1_latency_reduction")


# Figure 2: scrolling modern jank
s = pd.read_csv(RESULTS / "s2_descriptive.csv")
order = []
for device in DEVICES:
    for arch in ["RN_Legacy", "RN_NewArch", "Native"]:
        order.append((device.display_label, device.short_label, arch))
labels, means, sds = [], [], []
for device_label, short_label, arch in order:
    row = s[(s["Device"] == device_label) & (s["Architecture"] == arch)].iloc[0]
    labels.append(short_label + "\n" + {"RN_Legacy": "Legacy", "RN_NewArch": "New Arch", "Native": "Native"}[arch])
    means.append(row["Janky_Frames_Percent_mean"])
    sds.append(row["Janky_Frames_Percent_sd"])
plt.figure(figsize=(8.6, 4.5))
x = np.arange(len(labels))
plt.bar(x, means, yerr=sds, capsize=3)
plt.xticks(x, labels)
plt.ylabel("Modern janky frames (%)")
plt.grid(axis="y", alpha=0.25)
save("fig2_s2_modern_jank")


# Figure 3: JS callback/rendered-frame divergence
s = pd.read_csv(RESULTS / "s3_js_descriptive.csv")
order = [
    (device.display_label, device.short_label, arch)
    for device in DEVICES
    for arch in ["RN_Legacy", "RN_NewArch"]
]
labels, js_rate, rendered_rate = [], [], []
for device_label, short_label, arch in order:
    row = s[(s["Device"] == device_label) & (s["Architecture"] == arch)].iloc[0]
    labels.append(short_label + "\n" + ("Legacy" if arch == "RN_Legacy" else "New Arch"))
    js_rate.append(row["FPS modal_mean"])
    rendered_rate.append(row["Effective_FPS_mean"])
x = np.arange(len(labels))
w = 0.36
plt.figure(figsize=(7.7, 4.5))
plt.bar(x - w / 2, js_rate, width=w, label="JS callback rate")
plt.bar(x + w / 2, rendered_rate, width=w, label="Rendered-frame rate")
plt.xticks(x, labels)
plt.ylabel("Callbacks / frames per second")
plt.legend()
plt.grid(axis="y", alpha=0.25)
save("fig3_s3_js_render_divergence")


# Figure 4: JS-Native array throughput vs payload
s = pd.read_csv(RESULTS / "s4_array_summary.csv")
plt.figure(figsize=(7.4, 4.8))
linestyles = ["-", "--", "-.", ":"]
for index, device in enumerate(DEVICES):
    linestyle = linestyles[index % len(linestyles)]
    for arch, marker in [("RN_Legacy", "o"), ("RN_NewArch", "s")]:
        group = s[(s["Device"] == device.short_label) & (s["Architecture"] == arch)]
        plt.plot(
            group["Payload_Size"], group["Median_ops_s"],
            linestyle=linestyle, marker=marker,
            label=device.short_label + " - " + ("Legacy" if arch == "RN_Legacy" else "New Arch"),
        )
plt.xscale("log")
plt.yscale("log")
plt.xlabel("Array payload size (elements)")
plt.ylabel("Median throughput (operations/s)")
plt.legend(fontsize=8)
plt.grid(alpha=0.25)
save("fig4_s4_payload_throughput")


# Figure 5: cold-start medians
s = pd.read_csv(RESULTS / "s5_descriptive.csv")
order = []
for device in DEVICES:
    for arch in ["RN_Legacy", "RN_NewArch", "Native"]:
        order.append((device.short_label, arch))
labels, medians = [], []
for device, arch in order:
    row = s[(s["Device"] == device) & (s["Technology"] == arch)].iloc[0]
    labels.append(device + "\n" + {"RN_Legacy": "Legacy", "RN_NewArch": "New Arch", "Native": "Native"}[arch])
    medians.append(row["TotalTime_ms_median"])
plt.figure(figsize=(8.2, 4.5))
x = np.arange(len(labels))
plt.bar(x, medians)
plt.xticks(x, labels)
plt.ylabel("Median cold-start TotalTime (ms)")
plt.grid(axis="y", alpha=0.25)
save("fig5_s5_cold_start")

print(f"Created figures in: {FIG}")
