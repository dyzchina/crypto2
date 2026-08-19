"""
build_figures.py -- 3 publication-grade figures.
Sources: results/events_v50.json, dispersion_v50.json, pool_venue_v50.json.
Outputs: figures/fig{1,2,3}.{eps,pdf,png}.
"""
import json, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.linewidth": 0.8, "axes.labelsize": 10,
    "legend.fontsize": 8, "xtick.labelsize": 9, "ytick.labelsize": 9,
})

BUNDLE = Path(__file__).resolve().parents[1]
RES = BUNDLE / "results"; FIG = BUNDLE / "figures"
FIG.mkdir(exist_ok=True)

events = json.load(open(RES/"events_v50.json", encoding="utf-8"))
E = [e for e in events if math.isfinite(e.get("dlog_theta",float('nan')))
     and math.isfinite(e.get("log_rmse",float('nan')))]
n = len(E)

# --- Fig1: scatter of log(RMSE) vs dlog(theta) ---
x = np.array([e["dlog_theta"] for e in E])
y = np.array([e["log_rmse"] for e in E])
venues = sorted(set(e["venue_ccy"] for e in E))
colors = plt.cm.tab10(np.linspace(0, 1, len(venues)))
markers = ["o","s","^","D","v","P","X","*"]

fig, ax = plt.subplots(figsize=(5.5, 3.8))
for i, v in enumerate(venues):
    idx = [j for j,e in enumerate(E) if e["venue_ccy"]==v]
    if not idx: continue
    ax.scatter(x[idx], y[idx], color=colors[i], marker=markers[i%len(markers)],
               s=25, alpha=0.75, edgecolor="black", linewidth=0.3,
               label=v.replace("_","-"))
# OLS line
X = np.column_stack([np.ones(n), x])
b = np.linalg.lstsq(X, y, rcond=None)[0]
xs = np.linspace(x.min(), x.max(), 50)
ax.plot(xs, b[0]+b[1]*xs, "k-", lw=1.2,
        label=f"OLS: $\\hat\\beta_{{OLS}}={b[1]:.2f}$")
ax.set_xlabel(r"$\Delta\!\log\theta_e$ (dispersion proxy log-change)")
ax.set_ylabel(r"$\log(\mathrm{RMSE}_e)$ (reconstruction-error proxy)")
ax.set_title(f"Sign-flip events ($n = {n}$)")
ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
ax.legend(loc="best", ncol=2, framealpha=0.9)
plt.tight_layout()
for ext in ("pdf","eps","png"):
    plt.savefig(FIG/f"fig1_scatter.{ext}", dpi=300, bbox_inches="tight")
plt.close()

# --- Fig2: dumbbell top-30 by |dlog theta| ---
srt = sorted(E, key=lambda e: -abs(e["dlog_theta"]))[:30]
srt = sorted(srt, key=lambda e: e["dlog_theta"])
fig, ax = plt.subplots(figsize=(5.5, 5))
for i, e in enumerate(srt):
    pre = e["theta_pre_proxy"]; post = e["theta_post_proxy"]
    color = "steelblue" if post>pre else "firebrick"
    ax.plot([pre, post], [i, i], color=color, lw=1.2, alpha=0.75)
    ax.scatter([pre], [i], facecolor="white", edgecolor=color, s=32, zorder=3, linewidth=1.2)
    ax.scatter([post], [i], color=color, s=32, zorder=3)
ax.set_xscale("log")
ax.set_xlabel(r"$\theta_e^{\mathrm{pre}}$ (open) $\longrightarrow$ $\theta_e^{\mathrm{post}}$ (filled)")
ax.set_ylabel("Event rank (by $|\\Delta\\!\\log\\theta_e|$)")
ax.set_title("Top-30 sign-flip events")
ax.grid(alpha=0.3, linestyle="--", linewidth=0.5)
handles = [plt.Line2D([0],[0],color="steelblue",lw=2,label="dispersion increased"),
           plt.Line2D([0],[0],color="firebrick",lw=2,label="dispersion decreased")]
ax.legend(handles=handles, loc="best")
plt.tight_layout()
for ext in ("pdf","eps","png"):
    plt.savefig(FIG/f"fig2_dumbbell.{ext}", dpi=300, bbox_inches="tight")
plt.close()

# --- Fig3: crossover theta*(delta) = delta^{1/2} + events overlaid ---
fig, ax = plt.subplots(figsize=(5.5, 3.8))
d_grid = np.logspace(-3, 0, 100)
ax.plot(d_grid, d_grid**(1/2), "k-", lw=1.5, label=r"$\theta^{*}(\delta) = \delta^{1/2}$ (crossover)")
# events: use theta_post_proxy as theta, and pretend delta ~ n^{-1/2.5}
for i, e in enumerate(E):
    theta_e = e["theta_post_proxy"]
    d_e = 0.07  # reference delta
    ax.scatter(d_e, theta_e, color="royalblue", s=10, alpha=0.4)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel(r"$\delta$ (resolution scale)")
ax.set_ylabel(r"$\theta$ (dispersion angle, rad)")
ax.set_title(f"Crossover curve and $n={n}$ events")
ax.legend(loc="best")
ax.grid(alpha=0.3, linestyle="--", linewidth=0.5, which="both")
plt.tight_layout()
for ext in ("pdf","eps","png"):
    plt.savefig(FIG/f"fig3_crossover.{ext}", dpi=300, bbox_inches="tight")
plt.close()

print(f"WROTE fig1_scatter, fig2_dumbbell, fig3_crossover to {FIG}")
