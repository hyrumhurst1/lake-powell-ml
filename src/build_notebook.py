"""
build_notebook.py
-----------------
Generates `notebooks/lake_powell_surface_area.ipynb`, a self-contained Google
Colab notebook that builds a multi-decade Lake Powell water-surface-area time
series from Landsat imagery and validates it against measured USBR reservoir
elevation.

We generate the .ipynb with json.dump (not by hand) so the JSON is always valid.
Run:  python src/build_notebook.py
"""

import json
import os

# Each entry is (cell_type, source_string). Code is authored as normal Python.
CELLS = []


def md(text):
    CELLS.append(("markdown", text.strip("\n") + "\n"))


def code(text):
    CELLS.append(("code", text.strip("\n") + "\n"))


# ---------------------------------------------------------------------------
md(r"""
# Lake Powell Surface Area from Satellite (1984–2026)

**Author:** Hyrum Hurst

This notebook measures the water-surface area of Lake Powell from Landsat
satellite imagery over four decades and validates the result against measured
reservoir elevation published by the U.S. Bureau of Reclamation (USBR).

**What it does, step by step:**
1. Authenticate to Google Earth Engine (your one manual step).
2. Define the Lake Powell study area.
3. Detect water in each Landsat scene using a water index (MNDWI).
4. Build a monthly surface-area time series, 1984 to 2026.
5. Pull measured reservoir elevation from the USBR RISE API.
6. Validate: fit surface area to elevation and report R^2 and error.
7. Generate publication figures and save all outputs.

Everything you need to *defend* this is explained in the markdown between cells.
Read those. They are the asset.
""")

md(r"""
## Step 0 — Setup and authentication

Earth Engine is free for research but tied to *your* Google account. You need a
registered Earth Engine project id. If you do not have one:
1. Go to https://code.earthengine.google.com and sign in once to register.
2. Your project id usually looks like `ee-yourname`. Put it in the cell below.

This is the only step that genuinely requires you. `ee.Authenticate()` opens a
Google sign-in and pastes a token back.
""")

code(r"""
# Install dependencies (Colab usually has earthengine-api; geemap we add).
!pip install -q earthengine-api geemap scikit-learn

import ee
import geemap

# ---- Your Earth Engine project id ----
EE_PROJECT = "outreach-bot-493219"

ee.Authenticate()          # opens Google sign-in the first time
ee.Initialize(project=EE_PROJECT)
print("Earth Engine initialized for project:", EE_PROJECT)
""")

md(r"""
## Step 1 — Study area

Lake Powell sits on the Colorado River at the Utah–Arizona border, impounded by
Glen Canyon Dam. It is a long, branching canyon reservoir, which is exactly what
makes the shoreline hard to map and therefore interesting.

We draw a generous bounding polygon around the full-pool extent. We do **not**
need a tight outline: the water index decides what is water *inside* this box, so
the box only has to contain the reservoir and exclude other large water bodies.
""")

code(r"""
# Bounding box around Lake Powell's full-pool extent (lon/lat).
# Generous on purpose; the water index segments water within it.
AOI = ee.Geometry.Rectangle([-111.55, 36.85, -110.40, 37.95])

# Quick look (optional in Colab).
m = geemap.Map(center=[37.3, -110.95], zoom=9)
m.addLayer(AOI, {"color": "red"}, "Study area")
m
""")

md(r"""
## Step 2 — Water detection

We use the **Modified Normalized Difference Water Index (MNDWI)** (Xu, 2006):

```
MNDWI = (Green - SWIR1) / (Green + SWIR1)
```

Water reflects green light and strongly absorbs shortwave infrared (SWIR), so
open water gives MNDWI > 0 while land gives MNDWI < 0. MNDWI beats the older NDWI
here because SWIR suppresses built-up and bright-soil false positives, which
matters against the bright canyon rock around Powell.

**Why a threshold and not a deep model?** With strong, public ground truth and a
physically grounded index, a thresholded index is the honest baseline: simple,
reproducible, and explainable. Step 5 quantifies exactly how good it is. (The
notebook is structured so a learned classifier could replace `add_water()` later
without touching the rest.)

We work in **Landsat Collection 2, Level 2 surface reflectance** and harmonize
the four sensors (5, 7, 8, 9), which use different band numbers.
""")

code(r"""
# Common band names we want, mapped from each sensor's native band ids.
# Collection 2 L2 surface reflectance.
SENSORS = {
    "L5": {"id": "LANDSAT/LT05/C02/T1_L2",
           "bands": {"SR_B2": "green", "SR_B5": "swir1"}},
    "L7": {"id": "LANDSAT/LE07/C02/T1_L2",
           "bands": {"SR_B2": "green", "SR_B5": "swir1"}},
    "L8": {"id": "LANDSAT/LC08/C02/T1_L2",
           "bands": {"SR_B3": "green", "SR_B6": "swir1"}},
    "L9": {"id": "LANDSAT/LC09/C02/T1_L2",
           "bands": {"SR_B3": "green", "SR_B6": "swir1"}},
}


def mask_and_scale(img):
    # Apply Collection-2 scaling and mask cloud/shadow/cirrus/snow via QA_PIXEL.
    qa = img.select("QA_PIXEL")
    # Bit 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow, 5 snow.
    bad = (qa.bitwiseAnd(1 << 1).neq(0)
           .Or(qa.bitwiseAnd(1 << 2).neq(0))
           .Or(qa.bitwiseAnd(1 << 3).neq(0))
           .Or(qa.bitwiseAnd(1 << 4).neq(0))
           .Or(qa.bitwiseAnd(1 << 5).neq(0)))
    # Optical SR scaling for Collection 2 Level 2.
    optical = img.select("SR_B.").multiply(0.0000275).add(-0.2)
    return img.addBands(optical, None, True).updateMask(bad.Not())


def harmonize(sensor_key):
    # Return an ImageCollection with bands renamed to green/swir1 + MNDWI water.
    cfg = SENSORS[sensor_key]
    native = list(cfg["bands"].keys())
    common = list(cfg["bands"].values())

    def prep(img):
        img = mask_and_scale(img)
        img = img.select(native).rename(common)
        mndwi = img.normalizedDifference(["green", "swir1"]).rename("mndwi")
        water = mndwi.gt(0).rename("water")          # threshold at 0
        return water.copyProperties(img, ["system:time_start"])

    return (ee.ImageCollection(cfg["id"])
            .filterBounds(AOI)
            .map(prep))


# One merged water collection across all sensors.
water_ic = (harmonize("L5")
            .merge(harmonize("L7"))
            .merge(harmonize("L8"))
            .merge(harmonize("L9")))
print("Merged water collection built.")
""")

md(r"""
## Step 3 — Monthly surface-area time series

For each calendar month we take the **median** water mask (median is robust to
the occasional cloud or shadow that slips past the QA mask), multiply by true
per-pixel area, and sum over the study area to get water area in km^2.

Working month-by-month (instead of per scene) keeps the server-side job small
enough to return in one call. If a run times out, narrow the date range or
export to Drive (see the note at the end).
""")

code(r"""
import pandas as pd

START_YEAR, END_YEAR = 2020, 2026   # TEST RANGE: fast first run. Flip to 1984 for the full series.

months = []
y, mo = START_YEAR, 1
while (y < END_YEAR) or (y == END_YEAR and mo <= 6):   # through June 2026
    months.append((y, mo))
    mo += 1
    if mo > 12:
        mo = 1
        y += 1


def monthly_area(ym):
    y, mo = ym
    start = ee.Date.fromYMD(y, mo, 1)
    end = start.advance(1, "month")
    sub = water_ic.filterDate(start, end)
    # Median water mask for the month; 0 where no obs.
    wm = ee.Image(ee.Algorithms.If(sub.size().gt(0),
                                   sub.median(),
                                   ee.Image(0).rename("water")))
    area_img = wm.multiply(ee.Image.pixelArea())          # m^2 where water
    area = area_img.reduceRegion(reducer=ee.Reducer.sum(),
                                 geometry=AOI, scale=30,
                                 maxPixels=1e13).get("water")
    return ee.Feature(None, {"year": y, "month": mo,
                             "n_scenes": sub.size(),
                             "area_km2": ee.Number(area).divide(1e6)})


fc = ee.FeatureCollection([monthly_area(ym) for ym in months])
df = geemap.ee_to_df(fc)        # one server call
df["date"] = pd.to_datetime(dict(year=df.year, month=df.month, day=1))
df = df.sort_values("date").reset_index(drop=True)
# Drop months with no usable scenes.
df = df[df["n_scenes"] > 0].copy()
print(f"Got {len(df)} months of surface area, "
      f"{df.date.min().date()} to {df.date.max().date()}")
df.head()
""")

md(r"""
## Step 4 — Ground truth: USBR measured elevation

The U.S. Bureau of Reclamation publishes daily Lake Powell elevation at Glen
Canyon Dam. We pull it from the RISE API (**catalog item 508**). This is the
independent measurement we validate against — the whole credibility of the study
rests on this comparison.

If the API call fails (param names occasionally change), the fallback is a manual
download: open
https://data.usbr.gov/catalog/2362/item/508 , download the CSV, upload it to
Colab, and load it with pandas. The rest of the notebook is identical.
""")

code(r"""
import requests

def fetch_usbr_elevation(item_id=508, after="1984-01-01", before="2026-06-30"):
    url = "https://data.usbr.gov/rise/api/result"
    params = {"itemId": item_id, "after": after, "before": before,
              "order[dateTime]": "ASC", "itemsPerPage": 10000, "page": 1}
    headers = {"Accept": "application/vnd.api+json"}
    rows = []
    while True:
        r = requests.get(url, params=params, headers=headers, timeout=90)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        for d in data:
            a = d["attributes"]
            rows.append((a.get("dateTime"), a.get("result")))
        if len(data) < params["itemsPerPage"]:
            break
        params["page"] += 1
    out = pd.DataFrame(rows, columns=["dateTime", "elevation_ft"])
    out["date"] = pd.to_datetime(out["dateTime"]).dt.tz_localize(None)
    out = out.dropna(subset=["elevation_ft"])
    return out[["date", "elevation_ft"]]


elev = fetch_usbr_elevation()
# Monthly mean elevation to match the satellite cadence.
elev["ym"] = elev["date"].dt.to_period("M")
elev_m = elev.groupby("ym", as_index=False)["elevation_ft"].mean()
elev_m["date"] = elev_m["ym"].dt.to_timestamp()
print(f"USBR elevation: {len(elev)} daily rows, "
      f"{elev.date.min().date()} to {elev.date.max().date()}")
elev_m.tail()
""")

md(r"""
## Step 5 — Validation

We merge the satellite surface area with measured elevation by month and ask:
**how well does satellite-derived area predict the true reservoir level?**

Reservoir area-vs-elevation is monotonic but nonlinear (a canyon holds more area
per foot near the top than near the bottom), so we fit a degree-2 polynomial and
report R^2 and RMSE in feet. A high R^2 with low RMSE is the headline result: it
shows the satellite measurement tracks reality.
""")

code(r"""
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_squared_error

merged = pd.merge(df[["date", "area_km2", "n_scenes"]],
                  elev_m[["date", "elevation_ft"]], on="date", how="inner")
merged = merged.dropna().sort_values("date").reset_index(drop=True)

X = merged[["area_km2"]].values
ytrue = merged["elevation_ft"].values

model = make_pipeline(PolynomialFeatures(2), LinearRegression())
model.fit(X, ytrue)
pred = model.predict(X)

r2 = r2_score(ytrue, pred)
rmse = float(np.sqrt(mean_squared_error(ytrue, pred)))
merged["elev_pred_ft"] = pred
print(f"n = {len(merged)} matched months")
print(f"R^2  = {r2:.3f}")
print(f"RMSE = {rmse:.2f} ft")
""")

md(r"""
## Step 6 — Figures

Three publication figures:
1. Surface area over time (the satellite story).
2. Measured elevation over time (the ground-truth story).
3. Area vs elevation with the fitted curve (the validation).
""")

code(r"""
import matplotlib.pyplot as plt
import os
os.makedirs("figures", exist_ok=True)

# Fig 1: surface area over time
plt.figure(figsize=(10, 4))
plt.plot(merged["date"], merged["area_km2"], lw=1.2)
plt.title("Lake Powell water surface area from Landsat (1984-2026)")
plt.ylabel("Surface area (km^2)"); plt.xlabel("Year")
plt.tight_layout(); plt.savefig("figures/fig1_area_timeseries.png", dpi=200)
plt.show()

# Fig 2: measured elevation over time
plt.figure(figsize=(10, 4))
plt.plot(elev_m["date"], elev_m["elevation_ft"], lw=1.0, color="tab:orange")
plt.axhline(3700, ls="--", c="gray", lw=0.8, label="Full pool 3700 ft")
plt.axhline(3490, ls="--", c="red", lw=0.8, label="Min power pool 3490 ft")
plt.axhline(3370, ls=":", c="darkred", lw=0.8, label="Dead pool 3370 ft")
plt.title("Lake Powell measured elevation (USBR)")
plt.ylabel("Elevation (ft)"); plt.xlabel("Year"); plt.legend(fontsize=8)
plt.tight_layout(); plt.savefig("figures/fig2_elevation_timeseries.png", dpi=200)
plt.show()

# Fig 3: validation scatter
order = np.argsort(merged["area_km2"].values)
plt.figure(figsize=(6, 5))
plt.scatter(merged["area_km2"], merged["elevation_ft"], s=10, alpha=0.5,
            label="Monthly observations")
plt.plot(merged["area_km2"].values[order], merged["elev_pred_ft"].values[order],
         c="red", lw=2, label=f"Fit (R^2={r2:.3f}, RMSE={rmse:.1f} ft)")
plt.title("Validation: satellite area vs measured elevation")
plt.xlabel("Surface area (km^2)"); plt.ylabel("Elevation (ft)"); plt.legend()
plt.tight_layout(); plt.savefig("figures/fig3_validation.png", dpi=200)
plt.show()
""")

md(r"""
## Step 7 — Save outputs and the results summary

We save the merged time series as CSV and a `results.json` holding the exact
numbers the paper cites. The paper draft references these keys, so the writeup
stays in sync with whatever the data actually says.
""")

code(r"""
import json
os.makedirs("data", exist_ok=True)

merged.to_csv("data/lake_powell_monthly.csv", index=False)

first = merged.iloc[0]; last = merged.iloc[-1]
peak = merged.loc[merged["area_km2"].idxmax()]
trough = merged.loc[merged["area_km2"].idxmin()]

results = {
    "n_matched_months": int(len(merged)),
    "date_start": str(first["date"].date()),
    "date_end": str(last["date"].date()),
    "r2": round(float(r2), 3),
    "rmse_ft": round(float(rmse), 2),
    "area_peak_km2": round(float(peak["area_km2"]), 1),
    "area_peak_date": str(peak["date"].date()),
    "area_trough_km2": round(float(trough["area_km2"]), 1),
    "area_trough_date": str(trough["date"].date()),
    "pct_area_decline_peak_to_trough": round(
        100 * (1 - trough["area_km2"] / peak["area_km2"]), 1),
    "elev_full_pool_ft": 3700, "elev_min_power_ft": 3490, "elev_dead_pool_ft": 3370,
}
with open("data/results.json", "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))
""")

md(r"""
## Done

You now have:
- `data/lake_powell_monthly.csv` — the merged time series
- `data/results.json` — the numbers the paper cites
- `figures/*.png` — three publication figures

**If a server call timed out:** narrow `START_YEAR`/`END_YEAR`, or export the
monthly FeatureCollection to Drive with `ee.batch.Export.table.toDrive(fc, ...)`
and re-load it. Real remote-sensing pipelines almost always need one or two
rounds of this; that is normal, not a failure.

Next: drop `results.json` into the paper (`paper/paper.md` has matching
placeholders) and read the defense brief (`paper/defense_brief.md`).
""")

# ---------------------------------------------------------------------------
notebook = {
    "cells": [
        {"cell_type": ct, "metadata": {},
         **({"execution_count": None, "outputs": []} if ct == "code" else {}),
         "source": src}
        for ct, src in CELLS
    ],
    "metadata": {
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

out_path = os.path.join(os.path.dirname(__file__), "..", "notebooks",
                        "lake_powell_surface_area.ipynb")
out_path = os.path.normpath(out_path)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)
print(f"Wrote {out_path} with {len(CELLS)} cells.")
