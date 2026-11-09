#!/usr/bin/env python
"""Reproducible tables for the cohort-audit paper (paper/paper2_cohort_audit.md).

Reads only local BIDS metadata of ds007526 and ds002778 (participants.tsv, *_eeg.json sidecars,
channels.tsv, beh sidecars, sourcedata/clinical_data). Output: reports/tables/audit_*.csv and
reports/figures/audit_cohorts.png.
"""

import glob
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

from ndpred.data import bids

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

R7, R2 = Path("data/raw/ds007526"), Path("data/raw/ds002778")
OUT_T, OUT_F = Path("reports/tables"), Path("reports/figures")
OUT_T.mkdir(parents=True, exist_ok=True)
OUT_F.mkdir(parents=True, exist_ok=True)

A = bids.load_ds007526(R7)
B = bids.load_ds002778(R2)
sess = bids.load_ds002778_sessions(R2)


def ms(x):
    x = pd.Series(x).dropna()
    return f"{x.mean():.1f} ({x.std():.1f})" if len(x) else ""


# ---- t1 cohort summary
rows = []
for name, df, cog in (("ds007526", A, "moca"), ("ds002778", B, "mmse")):
    for g, d in df.groupby("group"):
        r = {"cohort": name, "group": g, "n": len(d), "age_mean_sd": ms(d["age"]),
             "female_n_pct": f"{int((d['sex'] == 0).sum())} ({100 * (d['sex'] == 0).mean():.0f}%)",
             "cognitive_screen": cog.upper(), "cognitive_mean_sd": ms(d[cog]),
             "disease_duration_mean_sd": ms(d["disease_duration"]) if g == "PD" else ""}
        if name == "ds007526":
            r["updrs_iii_mean_sd"] = ms(d["updrs_iii"]) if g == "PD" else ""
            r["updrs_total_mean_sd"] = ms(d["updrs_total"]) if g == "PD" else ""
            r["ledd_mean_sd"] = ms(d["ledd"]) if g == "PD" else ""
        rows.append(r)
pd.DataFrame(rows).to_csv(OUT_T / "audit_t1_cohort_summary.csv", index=False)

# ---- t2 completeness
comp = []
for name, df in (("ds007526", A), ("ds002778", B)):
    for c in df.columns:
        if c in ("participant_id", "cohort", "group", "label"):
            continue
        comp.append({"cohort": name, "variable": c, "non_missing": int(df[c].notna().sum()), "of": len(df)})
pd.DataFrame(comp).to_csv(OUT_T / "audit_t2_completeness.csv", index=False)

# ---- t3 recordings and acquisition
rec = []
for name, root, pat in (("ds007526", R7, "sub-*/eeg/*_eeg.json"), ("ds002778", R2, "sub-*/ses-*/eeg/*_eeg.json")):
    meta = A if name == "ds007526" else B
    grp = dict(zip(meta["participant_id"], meta["group"]))
    recs = []
    for f in glob.glob(str(root / pat)):
        j = json.loads(Path(f).read_text())
        sub = Path(f).name.split("_")[0]
        task = next(x for x in Path(f).name.split("_") if x.startswith("task-")).replace("task-", "")
        recs.append({"task": task, "group": grp.get(sub), "dur": j.get("RecordingDuration"),
                     "sfreq": j.get("SamplingFrequency"), "mains": j.get("PowerLineFrequency"),
                     "n_eeg": j.get("EEGChannelCount")})
    d = pd.DataFrame(recs)
    for task, t in d.groupby("task"):
        rec.append({"cohort": name, "task": task, "recordings": len(t),
                    "HC": int((t.group == "HC").sum()), "PD": int((t.group == "PD").sum()),
                    "sampling_hz": "/".join(sorted({str(int(x)) for x in t.sfreq.dropna()})),
                    "mains_hz": "/".join(sorted({str(int(x)) for x in t.mains.dropna()})),
                    "eeg_channel_count_sidecar": "/".join(sorted({str(int(x)) for x in t.n_eeg.dropna()})),
                    "duration_s_mean": round(t.dur.astype(float).mean(), 1),
                    "duration_s_min": round(t.dur.astype(float).min(), 1),
                    "duration_s_max": round(t.dur.astype(float).max(), 1)})
pd.DataFrame(rec).to_csv(OUT_T / "audit_t3_recordings.csv", index=False)

# ---- t4 group imbalance tests
tst = []
for name, df in (("ds007526", A), ("ds002778", B)):
    a, b = df[df.group == "HC"]["age"].dropna(), df[df.group == "PD"]["age"].dropna()
    t = stats.ttest_ind(a, b, equal_var=False)
    tab = pd.crosstab(df["group"], df["sex"])
    odds, pf = stats.fisher_exact(tab.values)
    tst.append({"cohort": name, "age_diff_PD_minus_HC": round(b.mean() - a.mean(), 2),
                "welch_t": round(t.statistic, 2), "p_age": round(t.pvalue, 4),
                "p_sex_fisher": round(pf, 4)})
pd.DataFrame(tst).to_csv(OUT_T / "audit_t4_group_balance.csv", index=False)

# ---- t5 ds002778 ON/OFF
w = sess.pivot(index="participant_id", columns="session", values=["updrs_total", "hoehn_yahr"])
rows5 = []
rng = np.random.default_rng(0)
for var in ("updrs_total", "hoehn_yahr"):
    off, on = w[(var, "off")], w[(var, "on")]
    d = (off - on).dropna()
    boots = [rng.choice(d.values, len(d), replace=True).mean() for _ in range(5000)]
    rows5.append({"variable": var, "n_pairs": len(d), "mean_off": round(off.mean(), 2),
                  "mean_on": round(on.mean(), 2), "mean_off_minus_on": round(d.mean(), 2),
                  "ci_lo": round(np.percentile(boots, 2.5), 2), "ci_hi": round(np.percentile(boots, 97.5), 2),
                  "identical_on_off": int((d == 0).sum())})
pd.DataFrame(rows5).to_csv(OUT_T / "audit_t5_ds002778_on_off.csv", index=False)
hy = sess.groupby("session")["hoehn_yahr"].value_counts().unstack(fill_value=0)
hy.to_csv(OUT_T / "audit_t5b_ds002778_hoehn_yahr.csv")

# ---- t6 channels
ca = pd.read_csv(next(R7.glob("sub-001/eeg/*task-rest_channels.tsv")), sep="\t")["name"].tolist()
cb = pd.read_csv(next(R2.glob("sub-hc10/ses-hc/eeg/*_channels.tsv")), sep="\t")["name"].tolist()
def non_scalp(c):
    return c.startswith(("EOG", "EXG", "VREF", "Status"))


sa, sb = [c for c in ca if not non_scalp(c)], [c for c in cb if not non_scalp(c)]
shared = [c for c in sb if c in sa]
pd.DataFrame([{"cohort": "ds007526", "rows_in_channels_tsv": len(ca), "typed_EEG_but_non_scalp": ", ".join(c for c in ca if non_scalp(c)), "scalp_channels": len(sa)},
              {"cohort": "ds002778", "rows_in_channels_tsv": len(cb), "typed_EEG_but_non_scalp": ", ".join(c for c in cb if non_scalp(c)), "scalp_channels": len(sb)},
              {"cohort": "shared", "rows_in_channels_tsv": "", "typed_EEG_but_non_scalp": "", "scalp_channels": len(shared)}]
             ).to_csv(OUT_T / "audit_t6_channels.csv", index=False)
json.dump({"shared": shared, "only_ds002778": [c for c in sb if c not in sa],
           "only_ds007526_count": len([c for c in sa if c not in sb])},
          open("reports/results/audit_channels.json", "w"), indent=1)

# ---- t7 supplementary clinical files (ds007526)
U = pd.read_csv(R7 / "sourcedata/clinical_data/full_UPDRS_data.tsv", sep="\t")
P = pd.read_csv(R7 / "participants.tsv", sep="\t", na_values=["n/a"])
gait_items = {"3.10": "gait", "3.11": "freezing of gait", "3.12": "postural stability", "3.13": "posture"}
mp = U.merge(P[["subject_id", "group"]], left_on="Subject", right_on="subject_id", how="inner")
g = [{"item": k, "name": v, "n": int(mp[k].notna().sum()), "mean": round(mp[k].mean(), 2),
      "sd": round(mp[k].std(), 2), "pct_score_ge1": round(100 * (mp[k] >= 1).mean(), 1)}
     for k, v in gait_items.items()]
pd.DataFrame(g).to_csv(OUT_T / "audit_t7_gait_items_ds007526.csv", index=False)

# ---- figure: cohort composition
fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
col = {"HC": "#4C72B0", "PD": "#DD8452"}
for k, (name, df) in enumerate((("ds007526", A), ("ds002778", B))):
    for grp in ("HC", "PD"):
        ax[k].hist(df[df.group == grp]["age"].dropna(), bins=np.arange(30, 95, 5), alpha=0.65,
                   color=col[grp], label=f"{grp} (n={int((df.group == grp).sum())})")
    ax[k].set_title(f"{name}: age", fontsize=9)
    ax[k].set_xlabel("years")
    ax[k].legend(fontsize=8)
ax[2].bar(["ds007526", "ds002778\n(per session)"], [len(sa), len(sb)], color="#999999", label="scalp channels")
ax[2].bar(["ds007526", "ds002778\n(per session)"], [len(shared)] * 2, color="#55A868", label="shared by both")
ax[2].set_title("Scalp channels", fontsize=9)
ax[2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT_F / "audit_cohorts.png", dpi=200)

for f in sorted(OUT_T.glob("audit_*.csv")):
    print("=====", f.name)
    print(pd.read_csv(f).to_string(index=False))
print("shared channels:", len(shared), "| only ds002778:", [c for c in sb if c not in sa])
