"""
build_notebook.py
-----------------
Generates `notebooks/lake_powell_surface_area.ipynb`.

The notebook = a few hand-written "keep" cells (auth, study area, USBR ground
truth) + the verified ML pipeline cells in `src/pipeline_cells.json` (Step 2
features, Step 3 trained Random Forest classifier, Step 4b concurrency-safe
area extraction, Step 5 validation, Step 6 figures, Step 7 save).

The pipeline cells implement a trained Random Forest water classifier and a
concurrency-safe monthly-area extractor, reviewed for Earth Engine correctness.
We generate the .ipynb with json.dump so the JSON is always valid.

Run:  python src/build_notebook.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE_JSON = os.path.join(HERE, "pipeline_cells.json")

CELLS = []


def md(text):
    CELLS.append(("markdown", text.strip("\n") + "\n"))


def code(text):
    CELLS.append(("code", text.strip("\n") + "\n"))


def add_pipeline(cells):
    for c in cells:
        CELLS.append((c["type"], c["source"]))


# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
md(r"""
# Lake Powell from Space: a trained ML water classifier (1984-2026)

**Author:** Hyrum Hurst

This notebook measures Lake Powell's water-surface area from four decades of
Landsat imagery using a **trained Random Forest classifier** (benchmarked against
an MNDWI baseline), and validates the satellite measurement against measured
reservoir elevation from the U.S. Bureau of Reclamation.

**Pipeline:**
- Step 0: authenticate to Earth Engine (your one manual step)
- Step 1: study area
- Step 2: harmonize 4 Landsat sensors into a shared feature stack
- Step 3: train a Random Forest water classifier; report held-out accuracy + kappa
- Step 4: pull USBR measured elevation (ground truth)
- Step 4b: concurrency-safe monthly surface area (RF mask and MNDWI baseline)
- Step 5: validate area vs elevation; benchmark RF vs MNDWI
- Step 6: figures
- Step 7: save outputs + results.json

Read the markdown between cells. Understanding the method is the asset, not the
output. See `paper/defense_brief.md`.
""")

# ---------------------------------------------------------------------------
# Step 0 - setup + auth (project id baked in)
# ---------------------------------------------------------------------------
md(r"""
## Step 0 - Setup and authentication

Earth Engine is free for research but tied to *your* Google account. This is the
only step that genuinely requires you: `ee.Authenticate()` opens a Google
sign-in. Use the same account you registered Earth Engine under.
""")

code(r"""
# Colab usually has earthengine-api; we add geemap, scikit-learn, scipy.
!pip install -q earthengine-api geemap scikit-learn scipy

import ee
import geemap

EE_PROJECT = "outreach-bot-493219"   # your registered Earth Engine project

ee.Authenticate()          # opens Google sign-in the first time
ee.Initialize(project=EE_PROJECT)

NB_VERSION = "2026-06-26 v4 (90m grid, memory-hardened)"
print("Earth Engine initialized for project:", EE_PROJECT)
print(">>> NOTEBOOK VERSION:", NB_VERSION, "<<<")
""")

# ---------------------------------------------------------------------------
# Step 1 - study area (Step 2 re-pins AOI with planar edges; this is the map)
# ---------------------------------------------------------------------------
md(r"""
## Step 1 - Study area

Lake Powell sits on the Colorado River at the Utah-Arizona border, behind Glen
Canyon Dam. It is a long, branching canyon reservoir, which makes its shoreline
hard to map and therefore a good test for the classifier.

A generous bounding box contains the full-pool extent; the classifier decides
what is water *inside* it. (Step 2 re-defines this same box with planar edges for
clean area sums.)
""")

code(r"""
AOI = ee.Geometry.Rectangle([-111.55, 36.85, -110.40, 37.95])

m = geemap.Map(center=[37.3, -110.95], zoom=9)
m.addLayer(AOI, {"color": "red"}, "Study area")
m
""")

# ---------------------------------------------------------------------------
# Step 2 + Step 3 (features + trained RF classifier) from the verified pipeline
# ---------------------------------------------------------------------------
with open(PIPELINE_JSON, encoding="utf-8") as f:
    PIPE = json.load(f)


def is_step_2_or_3(cell):
    t = cell["title"]
    return t.startswith("Step 2") or t.startswith("Step 3")


add_pipeline([c for c in PIPE if is_step_2_or_3(c)])

# ---------------------------------------------------------------------------
# Step 4 - USBR ground truth (keep). Produces elev_m[date, elevation_ft]
# used by Step 5. Independent of the imagery, runs after Step 2 imports pandas.
# ---------------------------------------------------------------------------
md(r"""
## Step 4 - Ground truth: USBR measured elevation

The U.S. Bureau of Reclamation publishes daily Lake Powell elevation at Glen
Canyon Dam. We pull it from the RISE API (**catalog item 508**). This is the
independent measurement Step 5 validates against, the only non-circular reference
in the whole pipeline.

If the API call fails (param names occasionally change), download the CSV from
https://data.usbr.gov/catalog/2362/item/508 , upload it to Colab, and load it
into a DataFrame named `elev_m` with columns `date` and `elevation_ft`.
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

# ---------------------------------------------------------------------------
# Step 4b, 5, 6, 7 (area extraction, validation, figures, save) from pipeline
# ---------------------------------------------------------------------------
add_pipeline([c for c in PIPE if not is_step_2_or_3(c)])

# ---------------------------------------------------------------------------
# Step 7b - flat paper tokens (so paper/paper.md {{...}} auto-fills cleanly)
# ---------------------------------------------------------------------------
md(r"""
## Step 7b - Numbers for the writeup

Flattens the key results into `results.json["paper_tokens"]` so the paper draft's
`{{placeholders}}` fill from one place. Run `python src/fill_paper.py` afterward.
""")

code(r"""
import json

_primary_df = df_rf_clean if primary_label == "RF" else df_mndwi_clean

def _r(x, n=3):
    try:
        return round(float(x), n)
    except Exception:
        return None

_pk = _primary_df["area_km2"].max() if len(_primary_df) else None
_tr = _primary_df["area_km2"].min() if len(_primary_df) else None

paper_tokens = {
    "overall_accuracy": _r(rf_accuracy),
    "kappa": _r(rf_kappa),
    "mndwi_overall_accuracy": _r(mndwi_accuracy),
    "mndwi_kappa": _r(mndwi_kappa),
    "rf_out_of_era_L5_accuracy": _r(rf_l5_accuracy),
    "primary_method": primary_label,
    "r2": _r(primary_val.get("r2_cv")),
    "rmse_ft": _r(primary_val.get("rmse_ft_cv"), 2),
    "n_months": int(primary_val.get("n") or 0),
    "mndwi_r2_cv": _r(mndwi_val.get("r2_cv")),
    "mndwi_rmse_ft_cv": _r(mndwi_val.get("rmse_ft_cv"), 2),
    "area_series_mean_abs_diff_km2": _r(area_mean_abs_diff, 2),
    "area_series_pearson_r": _r(area_pearson_r),
    "area_series_shared_months": int(len(area_join)),
    "area_peak_km2": _r(_pk, 1),
    "area_trough_km2": _r(_tr, 1),
    "pct_area_decline": (_r(100 * (1 - _tr / _pk), 1)
                         if (_pk and _tr is not None) else None),
}

with open("results.json") as f:
    _res = json.load(f)
_res["paper_tokens"] = paper_tokens
with open("results.json", "w") as f:
    json.dump(_res, f, indent=2)

print(json.dumps(paper_tokens, indent=2))
""")

# ---------------------------------------------------------------------------
# Write the notebook
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

out_path = os.path.normpath(os.path.join(HERE, "..", "notebooks",
                                         "lake_powell_surface_area.ipynb"))
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)
print(f"Wrote {out_path} with {len(CELLS)} cells "
      f"({sum(1 for t, _ in CELLS if t == 'code')} code).")
