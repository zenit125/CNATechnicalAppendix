"""Simulate CNA input datasets for a fictional multi-county ELC ("ELC of Pelican Bay").

Outputs (CSV, zip codes as text):
  clean/      internally consistent datasets
  with_errors/ same datasets with planted errors (+ planted_errors.csv answer key)
"""
import os, sys
import numpy as np
import pandas as pd

rng = np.random.default_rng(20261012)
OUT = sys.argv[1]
THRESH = {"4": 4.0, "45": 4.5, "5": 5.0, "6": 6.0}
SUBS = ["BG1", "TANF", "SWD"]

ELC = "ELC of Pelican Bay"
NEIGH = {"ELC of Gator Ridge": ["Cypress"], "ELC of Sandhill": ["Palmetto"]}

# ---------------------------------------------------------------- geography
# Pelican Bay: 3 counties. Egret zips start with 0 (tests leading zeros).
# Zip 90118 is split between Heron and Osprey (providers in both counties).
geo = []
for z in ["90101", "90102", "90103", "90104", "90105", "90106", "90107", "90118"]:
    geo.append((z, "Heron", ELC))
for z in ["90121", "90122", "90123", "90124", "90125", "90118"]:
    geo.append((z, "Osprey", ELC))
for z in ["09141", "09142", "09143"]:
    geo.append((z, "Egret", ELC))
for z in ["90201", "90202", "90203"]:
    geo.append((z, "Cypress", "ELC of Gator Ridge"))
for z in ["90301", "90302"]:
    geo.append((z, "Palmetto", "ELC of Sandhill"))
geo = pd.DataFrame(geo, columns=["zip", "county", "elc"])
own_geo = geo[geo.elc == ELC].reset_index(drop=True)
nb_geo = geo[geo.elc != ELC].reset_index(drop=True)
county_weight = {"Heron": 0.55, "Osprey": 0.33, "Egret": 0.12}


def pick_home(n, own_share):
    """Home (zip, county, elc) rows: own_share in Pelican Bay, rest in neighbors."""
    rows = []
    for _ in range(n):
        if rng.random() < own_share:
            c = rng.choice(list(county_weight), p=list(county_weight.values()))
            r = own_geo[own_geo.county == c].sample(1, random_state=int(rng.integers(1e9))).iloc[0]
        else:
            r = nb_geo.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
        rows.append((r.zip, r.county, r.elc))
    return rows


# ---------------------------------------------------------------- providers
def make_providers(prefix, n_by_county, nb_n, cap_rng, class_na_share, start_id):
    rows, pid = [], start_id
    for c, n in n_by_county.items():
        zips = own_geo[own_geo.county == c].zip.tolist()
        for _ in range(n):
            z = rng.choice(zips)
            score = np.nan if rng.random() < class_na_share else round(float(np.clip(rng.normal(5.2, 0.7), 2.5, 7.0)), 2)
            rows.append((pid, z, c, ELC, int(rng.integers(*cap_rng)), score))
            pid += 1
    for _ in range(nb_n):  # out-of-area providers that serve some Pelican Bay children
        r = nb_geo.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
        score = round(float(np.clip(rng.normal(5.2, 0.7), 2.5, 7.0)), 2)
        rows.append((pid, r.zip, r.county, r.elc, int(rng.integers(*cap_rng)), score))
        pid += 1
    return pd.DataFrame(rows, columns=["provider_id", "zip", "county", "elc", "capacity", "class_score"])


sr_prov = make_providers("SR", {"Heron": 48, "Osprey": 30, "Egret": 9}, 6, (15, 160), 0.12, 1001)
vpk_prov = make_providers("VPK", {"Heron": 36, "Osprey": 22, "Egret": 7}, 4, (10, 80), 0.10, 5001)
# Make zip 09143 (Egret) have no high-quality SR providers: all scores below 4
sr_prov.loc[sr_prov.zip == "09143", "class_score"] = 3.6
# Some SR and VPK providers are the same organization: reuse IDs for 20 VPK providers in shared zips
shared = sr_prov[sr_prov.elc == ELC].sample(20, random_state=1)
vpk_prov.loc[vpk_prov.index[:20], ["provider_id", "zip", "county", "elc"]] = shared[["provider_id", "zip", "county", "elc"]].values
vpk_prov["provider_id"] = vpk_prov.provider_id.astype(int)

# ---------------------------------------------------------------- families + children (SR)
fam_rows, kid_rows = [], []
fid, cid = 1, 100001
n_fam = 1150
sizes = rng.choice([1, 2, 3, 4, 5], size=n_fam, p=[0.58, 0.27, 0.10, 0.04, 0.01])
homes = pick_home(n_fam, 0.965)
for k, (hz, hc, he) in zip(sizes, homes):
    tanf = int(rng.random() < 0.06)
    income = float(np.exp(rng.normal(np.log(31000), 0.45)))
    fam_rows.append((fid, "Pelican", hz, hc, he, k, tanf, income))
    for _ in range(k):
        age = int(rng.choice(range(13), p=np.array([6, 9, 10, 10, 10, 9, 8, 7, 7, 6, 6, 6, 6]) / 100))
        kid_rows.append((cid, fid, age, hz, hc, he, ELC, int(rng.random() < 0.09), tanf, int(rng.random() < 0.025)))
        cid += 1
    fid += 1
# Children paid by neighbor ELCs who attend Pelican Bay providers (home in neighbor ELCs)
for _ in range(45):
    r = nb_geo.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
    tanf = int(rng.random() < 0.05)
    income = float(np.exp(rng.normal(np.log(31000), 0.45)))
    fam_rows.append((fid, "Other", r.zip, r.county, r.elc, 1, tanf, income))
    age = int(rng.integers(0, 6))
    kid_rows.append((cid, fid, age, r.zip, r.county, r.elc, r.elc, int(rng.random() < 0.09), tanf, int(rng.random() < 0.025)))
    cid += 1; fid += 1

fams = pd.DataFrame(fam_rows, columns=["family_id", "payer_group", "home_zip", "home_county", "home_elc", "n_children", "TANF", "income"])
kids = pd.DataFrame(kid_rows, columns=["child_id", "family_id", "age", "home_zip", "home_county", "home_elc", "paying_elc", "BG1", "TANF", "SWD"])


def choose_provider(prov, home_county, home_elc, paying_elc):
    own = prov[prov.elc == ELC]
    if paying_elc != ELC:                       # neighbor-paid child at a Pelican Bay provider
        pool = own
    else:
        u = rng.random()
        if home_elc == ELC and u < 0.85:
            pool = own[own.county == home_county]
        elif u < 0.97:
            pool = own[own.county != home_county] if home_elc == ELC else own
        else:
            pool = prov[prov.elc != ELC]        # out-of-area provider
    w = pool.capacity / pool.capacity.sum()
    return pool.iloc[rng.choice(len(pool), p=w.values)]


def enrollment_rows(children, prov, multi_share, program):
    rows = []
    for _, k in children.iterrows():
        n_prov = 2 if rng.random() < multi_share else 1
        chosen = []
        while len(chosen) < n_prov:
            p = choose_provider(prov, k.home_county, k.home_elc, k.paying_elc)
            if p.provider_id not in [c.provider_id for c in chosen]:
                chosen.append(p)
        for p in chosen:
            rows.append({
                "Unique Child ID": k.child_id,
                "Provider ID": int(p.provider_id),
                "Paying ELC": k.paying_elc,
                "Child Home Zipcode": k.home_zip,
                "Child Home County": k.home_county,
                "Child Home ELC": k.home_elc,
                "Child Provider Zipcode": p.zip,
                "Child Provider County": p.county,
                "Child Provider ELC": p.elc,
                "Child Provider not in Child Home County": int(p.county != k.home_county),
                "Child Provider not in Child Home ELC": int(p.elc != k.home_elc),
                "Child with Multiple Provider Records": int(n_prov > 1),
                ("Child aged 0-5" if program == "SR" else "Child aged 3-5"): int(k.age <= 5),
                "BG1/at-risk": k.BG1, "TANF Recip": k.TANF, "SWD": k.SWD,
                "_n_prov": n_prov,
            })
    return pd.DataFrame(rows)


sr = enrollment_rows(kids, sr_prov, 0.07, "SR")

# ---------------------------------------------------------------- VPK children
vpk_kids = kids[(kids.age == 4) & (rng.random(len(kids)) < 0.7)].copy()
extra = []
for i, (hz, hc, he) in enumerate(pick_home(1650, 0.975)):
    extra.append((cid, 0, 4, hz, hc, he, ELC, int(rng.random() < 0.02), int(rng.random() < 0.005), int(rng.random() < 0.03)))
    cid += 1
for _ in range(30):  # neighbor-paid VPK children at Pelican Bay providers
    r = nb_geo.sample(1, random_state=int(rng.integers(1e9))).iloc[0]
    extra.append((cid, 0, 4, r.zip, r.county, r.elc, r.elc, 0, 0, int(rng.random() < 0.03)))
    cid += 1
vpk_kids = pd.concat([vpk_kids, pd.DataFrame(extra, columns=kids.columns)], ignore_index=True)
vpk = enrollment_rows(vpk_kids, vpk_prov, 0.03, "VPK")
# VPK hours at this provider (school-year VPK, max 540); multi-provider children split hours
tot = np.where(rng.random(len(vpk_kids)) < 0.88, rng.integers(378, 541, len(vpk_kids)), rng.integers(60, 378, len(vpk_kids)))
tot_by_child = dict(zip(vpk_kids.child_id, tot))
hours = []
for cid_, grp in vpk.groupby("Unique Child ID", sort=False):
    t = tot_by_child[cid_]
    if len(grp) == 1:
        hours.append((grp.index[0], int(t)))
    else:
        a = int(rng.integers(int(t * 0.3), int(t * 0.7)))
        hours += [(grp.index[0], a), (grp.index[1], int(t) - a)]
for idx, h in hours:
    vpk.loc[idx, "VPK Hours"] = h
vpk["VPK Hours"] = vpk["VPK Hours"].astype(int)

# ---------------------------------------------------------------- zip-level FLICCA / FLIPA
def zip_level(enr, prov, age_col):
    own_prov = prov[prov.elc == ELC]
    e = enr[(enr[age_col] == 1) & (enr["Child Provider ELC"] == ELC)]
    e = e.merge(own_prov[["provider_id", "class_score"]], left_on="Provider ID", right_on="provider_id")
    out = own_prov.groupby(["zip", "county", "elc"], as_index=False).size()[["zip", "county", "elc"]]
    out.columns = ["Provider Zipcode", "Provider County", "Provider ELC"]
    for s, t in THRESH.items():
        hq_p = own_prov.class_score >= t
        cap = own_prov.assign(hq=hq_p).groupby(["zip", "county"]).apply(
            lambda g: pd.Series({"hq": g.capacity[g.hq].sum(), "lq": g.capacity[~g.hq].sum()}), include_groups=False).reset_index()
        e_hq = e.class_score >= t
        cols = {}
        for grp, mask in [("", np.ones(len(e), bool))] + [(f"{g}_", (e[c] == 1).values) for g, c in zip(SUBS, ["BG1/at-risk", "TANF Recip", "SWD"])]:
            hq_n = e[mask & e_hq].groupby(["Child Provider Zipcode", "Child Provider County"]).size()
            lq_n = e[mask & ~e_hq].groupby(["Child Provider Zipcode", "Child Provider County"]).size()
            cols[grp] = (hq_n, lq_n)
        for grp, (hq_n, lq_n) in cols.items():
            hqc, hqe, lqc, lqe = [], [], [], []
            for _, r in out.iterrows():
                key = (r["Provider Zipcode"], r["Provider County"])
                c = cap[(cap.zip == key[0]) & (cap.county == key[1])].iloc[0]
                hqc.append(int(c.hq)); lqc.append(int(c.lq))
                hqe.append(int(hq_n.get(key, 0))); lqe.append(int(lq_n.get(key, 0)))
            out[f"{grp}hq_capacity_{s}"] = hqc
            out[f"{grp}hq_enrollment_{s}"] = hqe
            out[f"{grp}lq_capacity_{s}"] = lqc
            out[f"{grp}lq_enrollment_{s}"] = lqe
            out[f"{grp}Infrastructure_{s}"] = np.array(hqc) - np.array(hqe) - np.array(lqe)
    order = ["Provider Zipcode", "Provider County", "Provider ELC"]
    for grp in [""] + [f"{g}_" for g in SUBS]:
        for s in THRESH:
            order += [f"{grp}{v}_{s}" for v in ["hq_capacity", "hq_enrollment", "lq_capacity", "lq_enrollment", "Infrastructure"]]
    return out[order].sort_values(["Provider Zipcode", "Provider County"]).reset_index(drop=True)


flicca = zip_level(sr, sr_prov, "Child aged 0-5")
flipa = zip_level(vpk, vpk_prov, "Child aged 3-5")

# ---------------------------------------------------------------- HPI (household level -> aggregates)
# Statewide households: Pelican Bay families (from the child file) + synthetic households elsewhere.
fams["HPI"] = np.clip(rng.normal(0.045 + 0.012 * np.minimum(fams.n_children, 4), 0.025), 0.002, 0.45)
fam_flags = kids.groupby("family_id")[["BG1", "SWD"]].max().reset_index()
hh = fams.merge(fam_flags, on="family_id")
hh["size"] = np.minimum(hh.n_children, 4)

other_elcs = {f"ELC of Region {i:02d}": [] for i in range(4, 31)}
other_counties = [f"County {i:02d}" for i in range(6, 68)]          # 62 more counties -> 67 total
elc_names = list(other_elcs)
for i, c in enumerate(other_counties):
    other_elcs[elc_names[i % len(elc_names)]].append(c)
county_to_elc = {"Heron": ELC, "Osprey": ELC, "Egret": ELC, "Cypress": "ELC of Gator Ridge", "Palmetto": "ELC of Sandhill"}
for e, cs in other_elcs.items():
    for c in cs:
        county_to_elc[c] = e
synth = []
for c, e in county_to_elc.items():
    n = int(rng.integers(300, 2500)) if c not in ("Heron", "Osprey", "Egret") else 0
    if c in ("Cypress", "Palmetto"):
        n = int(rng.integers(600, 900))
    if n == 0:
        continue
    sz = rng.choice([1, 2, 3, 4], size=n, p=[0.6, 0.27, 0.1, 0.03])
    base = rng.normal(0.06, 0.012)
    synth.append(pd.DataFrame({"home_zip": "NA", "home_county": c, "home_elc": e, "size": sz,
                               "HPI": np.clip(rng.normal(base + 0.012 * sz, 0.03), 0.002, 0.45),
                               "BG1": (rng.random(n) < 0.08).astype(int), "TANF": (rng.random(n) < 0.05).astype(int),
                               "SWD": (rng.random(n) < 0.03).astype(int)}))
allhh = pd.concat([hh[["home_zip", "home_county", "home_elc", "size", "HPI", "BG1", "TANF", "SWD"]]] + synth, ignore_index=True)


def hpi_row(g):
    row = {}
    for pre, mask in [("", np.ones(len(g), bool))] + [(f"{s}_", (g[s] == 1).values) for s in SUBS]:
        for k, lab in [(1, "1"), (2, "2"), (3, "3"), (4, "4plus")]:
            sel = g[mask & (g["size"] == k).values]
            row[f"{pre}HPI_{lab}"] = round(float(sel.HPI.mean()), 4) if len(sel) else np.nan
            row[f"{pre}N_{lab}"] = int(len(sel))
    return pd.Series(row)


parts = [
    pd.DataFrame([dict(**{"Home Zipcode": "NA", "Home County": "NA", "Home ELC": "Florida (State-Level)"}, **hpi_row(allhh))]),
]
for e, g in allhh.groupby("home_elc"):
    parts.append(pd.DataFrame([dict(**{"Home Zipcode": "NA", "Home County": "NA", "Home ELC": e}, **hpi_row(g))]))
for c, g in allhh.groupby("home_county"):
    parts.append(pd.DataFrame([dict(**{"Home Zipcode": "NA", "Home County": c, "Home ELC": "NA"}, **hpi_row(g))]))
for (z, c, e), g in hh[hh.home_elc == ELC].groupby(["home_zip", "home_county", "home_elc"]):
    parts.append(pd.DataFrame([dict(**{"Home Zipcode": z, "Home County": c, "Home ELC": e}, **hpi_row(g))]))
hpi = pd.concat(parts, ignore_index=True)
for c in [c for c in hpi.columns if c.startswith('N_') or '_N_' in c]:
    hpi[c] = hpi[c].astype('Int64')

# ---------------------------------------------------------------- churn-fill (coalition level)
def churn_row(name, n_children):
    out_ = int(n_children * rng.uniform(0.25, 0.4))
    in_ = int(out_ * rng.uniform(1.05, 1.5))
    avg = round(float(rng.normal(4100, 350)), 2)
    total = round(avg * n_children, 2)
    return {"CoalitionName": name, "children_in": in_, "children_out": out_, "churn_fill": round(in_ / out_, 5),
            "total_spend": total, "OCASpend": round(total * rng.uniform(0.82, 0.88), 2),
            "NetSpend": round(total * rng.uniform(0.985, 0.995), 2), "totaldayspaid": int(n_children * rng.uniform(140, 160)),
            "num_of_children": n_children, "num_of_month": int(n_children * rng.uniform(7.5, 8.5)), "avg_spend": avg}


own_n = sr[(sr["Paying ELC"] == ELC) & (sr["Child aged 0-5"] == 1)]["Unique Child ID"].nunique()
churn = [churn_row(ELC, own_n)] + [churn_row(e, int(rng.integers(800, 9000))) for e in ["ELC of Gator Ridge", "ELC of Sandhill"] + list(other_elcs)]
churn = pd.DataFrame(churn)
fl = {"CoalitionName": "Florida (State-level)"}
for c in ["children_in", "children_out", "total_spend", "OCASpend", "NetSpend", "totaldayspaid", "num_of_children", "num_of_month"]:
    fl[c] = round(churn[c].sum(), 2) if "spend" in c.lower() else int(churn[c].sum())
fl["churn_fill"] = round(fl["children_in"] / fl["children_out"], 5)
fl["avg_spend"] = round(fl["total_spend"] / fl["num_of_children"], 2)
churn = pd.concat([pd.DataFrame([fl]), churn], ignore_index=True)[list(churn.columns)]

# ---------------------------------------------------------------- write clean set
sr_out = sr.drop(columns="_n_prov").sort_values(["Unique Child ID", "Provider ID"]).reset_index(drop=True)
vpk_out = vpk.drop(columns="_n_prov").sort_values(["Unique Child ID", "Provider ID"]).reset_index(drop=True)
datasets = {"SR_child_by_provider.csv": sr_out, "VPK_child_by_provider.csv": vpk_out,
            "Zip_FLICCA_SR.csv": flicca, "Zip_FLIPA_VPK.csv": flipa, "HPI.csv": hpi, "ChurnFill.csv": churn}
os.makedirs(f"{OUT}/clean", exist_ok=True)
for f, d in datasets.items():
    d.to_csv(f"{OUT}/clean/{f}", index=False, na_rep="NA")

# ---------------------------------------------------------------- planted errors
err = {k: v.copy() for k, v in datasets.items()}
key = []
def note(f, where, what, check):
    key.append({"file": f, "location": where, "planted_error": what, "check_that_should_catch_it": check})

d = err["SR_child_by_provider.csv"]
dup = d.iloc[[10]]
err["SR_child_by_provider.csv"] = d = pd.concat([d, dup], ignore_index=True)
note("SR_child_by_provider.csv", f"Unique Child ID {dup.iloc[0]['Unique Child ID']}, Provider ID {dup.iloc[0]['Provider ID']} (last row)", "Exact duplicate child-provider record", "One row per child x provider")

i = d.index[d["Child Provider Zipcode"] == "09141"][0]
d.loc[i, "Child Provider Zipcode"] = "9141"
note("SR_child_by_provider.csv", f"row for Unique Child ID {d.loc[i,'Unique Child ID']}", "Provider zip lost its leading zero (9141)", "Zip codes are 5-character text")

j = d.index[(d["Child Provider not in Child Home County"] == 1) & (d["Child Provider ELC"] == ELC) & (d["Child Home ELC"] == ELC)][0]
d.loc[j, "Child Provider not in Child Home County"] = 0
note("SR_child_by_provider.csv", f"Unique Child ID {d.loc[j,'Unique Child ID']}", "'not in home county' flag = 0 although home and provider counties differ", "Flags agree with the location fields")

pid = d.loc[d["Child Provider ELC"] == ELC, "Provider ID"].value_counts().index[0]
k = d.index[d["Provider ID"] == pid][0]
other = [c for c in ["Heron", "Osprey", "Egret"] if c != d.loc[k, "Child Provider County"]][0]
d.loc[k, "Child Provider County"] = other
note("SR_child_by_provider.csv", f"Provider ID {pid}, Unique Child ID {d.loc[k,'Unique Child ID']}", f"One record gives this provider a different county ({other})", "Each Provider ID has one zip/county/ELC")

v = err["VPK_child_by_provider.csv"]
m = v.index[v["Child with Multiple Provider Records"] == 0][5]
v.loc[m, "VPK Hours"] = 612
note("VPK_child_by_provider.csv", f"Unique Child ID {v.loc[m,'Unique Child ID']}", "VPK Hours = 612 (above the 540-hour school-year maximum)", "VPK hours between 0 and 540 per child (summed across providers)")

f_ = err["Zip_FLICCA_SR.csv"]
f_.loc[2, "Infrastructure_5"] = f_.loc[2, "Infrastructure_5"] + 25
note("Zip_FLICCA_SR.csv", f"Provider Zipcode {f_.loc[2,'Provider Zipcode']}", "Infrastructure_5 off by +25", "Infrastructure = hq_capacity - hq_enrollment - lq_enrollment")
r = f_.index[f_["hq_enrollment_5"] > 3][0]
f_.loc[r, "BG1_hq_enrollment_5"] = f_.loc[r, "hq_enrollment_5"] + 4
f_.loc[r, "BG1_Infrastructure_5"] = f_.loc[r, "BG1_hq_capacity_5"] - f_.loc[r, "BG1_hq_enrollment_5"] - f_.loc[r, "BG1_lq_enrollment_5"]
note("Zip_FLICCA_SR.csv", f"Provider Zipcode {f_.loc[r,'Provider Zipcode']}", "BG1_hq_enrollment_5 exceeds all-children hq_enrollment_5", "Subgroup enrollment <= total enrollment")

p_ = err["Zip_FLIPA_VPK.csv"]
p_.loc[4, "lq_enrollment_45"] = p_.loc[4, "lq_enrollment_45"] + 15
p_.loc[4, "Infrastructure_45"] = p_.loc[4, "hq_capacity_45"] - p_.loc[4, "hq_enrollment_45"] - p_.loc[4, "lq_enrollment_45"]
note("Zip_FLIPA_VPK.csv", f"Provider Zipcode {p_.loc[4,'Provider Zipcode']}", "lq_enrollment_45 is 15 higher than the VPK child file supports (Infrastructure recomputed, so arithmetic still passes)", "Zip enrollment = count of child-provider records at providers in that zip")

h = err["HPI.csv"]
zr = h.index[(h["Home Zipcode"] != "NA") & h["TANF_HPI_4plus"].notna()]
zr = zr[0] if len(zr) else h.index[(h["Home Zipcode"] != "NA")][0]
h.loc[zr, "TANF_HPI_4plus"] = 1.17
note("HPI.csv", f"Home Zipcode {h.loc[zr,'Home Zipcode']}", "TANF_HPI_4plus = 1.17 (above 100% of income)", "HPI between 0 and 1; review values above 0.40")
zz = h.index[(h["Home Zipcode"] != "NA") & h["SWD_HPI_1"].notna() & h["TANF_HPI_1"].notna()][0]
for lab in ["1", "2", "3", "4plus"]:
    h.loc[zz, f"SWD_HPI_{lab}"] = h.loc[zz, f"TANF_HPI_{lab}"]
note("HPI.csv", f"Home Zipcode {h.loc[zz,'Home Zipcode']}", "SWD HPI values copied from TANF values", "Subgroup HPI values are not identical across subgroups")
nn = h.index[(h["Home Zipcode"] != "NA") & (h["N_1"] > 5)][1]
h.loc[nn, "BG1_N_1"] = h.loc[nn, "N_1"] + 3
note("HPI.csv", f"Home Zipcode {h.loc[nn,'Home Zipcode']}", "BG1_N_1 larger than all-households N_1", "Subgroup sample size <= total sample size")

c_ = err["ChurnFill.csv"]
ci = c_.index[c_.CoalitionName == ELC][0]
c_.loc[ci, "num_of_children"] = c_.loc[ci, "num_of_children"] + 40
note("ChurnFill.csv", ELC, "num_of_children 40 higher than unique 0-5 SR children paid by the ELC in the child file", "Churn-fill children = unique 0-5 SR children by paying ELC")

os.makedirs(f"{OUT}/with_errors", exist_ok=True)
for f, d in err.items():
    d.to_csv(f"{OUT}/with_errors/{f}", index=False, na_rep="NA")
pd.DataFrame(key).to_csv(f"{OUT}/with_errors/planted_errors.csv", index=False)

# summary for the README
print("SR rows", len(sr_out), "unique children", sr_out["Unique Child ID"].nunique())
print("VPK rows", len(vpk_out), "unique children", vpk_out["Unique Child ID"].nunique())
print("FLICCA zips", len(flicca), "FLIPA zips", len(flipa), "HPI rows", len(hpi), "churn rows", len(churn))
print("SR providers in ELC", (sr_prov.elc == ELC).sum(), "VPK providers in ELC", (vpk_prov.elc == ELC).sum())
print("own 0-5 SR children paid", own_n)
print("planted errors", len(key))
