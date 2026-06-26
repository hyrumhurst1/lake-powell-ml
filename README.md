# Lake Powell Surface-Area Decline from Landsat (1984–2026)

Measuring Lake Powell's water-surface area from four decades of free Landsat
imagery, and validating it against measured reservoir elevation from the U.S.
Bureau of Reclamation.

**Author:** Hyrum Hurst · Independent researcher

---

## What this is

A fully reproducible remote-sensing study. It builds a monthly water-surface-area
time series for Lake Powell from the Landsat archive (Landsat 5, 7, 8, 9) using
the MNDWI water index in Google Earth Engine, then checks how well that satellite
measurement predicts the reservoir's true elevation. Everything runs on free,
public data in one Colab notebook.

## Repo layout

```
notebooks/lake_powell_surface_area.ipynb   the full pipeline (run this)
src/build_notebook.py                       regenerates the notebook
src/fetch_usbr.py                           standalone USBR ground-truth fetch
src/fill_paper.py                           fills paper numbers from results.json
paper/paper.md                              the manuscript draft
paper/defense_brief.md                      Q&A to be able to defend it
paper/references.md                         citations (verify before submitting)
paper/ai_disclosure.md                      AI-use disclosure statement
site/index.html                             personal research page
data/, figures/                             generated outputs (gitignored)
```

## How to run (about 30 minutes of clicking)

1. Open `notebooks/lake_powell_surface_area.ipynb` in Google Colab.
2. Get a free Earth Engine project id at https://code.earthengine.google.com and
   put it in the Step 0 cell (`EE_PROJECT = "ee-yourname"`).
3. Runtime → Run all. Authenticate when prompted.
4. When it finishes: `python src/fill_paper.py` to populate the paper's numbers.
5. Read `paper/defense_brief.md`. That part is on you.

## Data sources

- Landsat Collection 2 Level 2 surface reflectance, via Google Earth Engine.
- Lake Powell daily elevation, USBR RISE catalog item 508.

## Honest status

The notebook is written and syntax-checked but has **not** been executed against
live Earth Engine (that needs the author's Google auth). First runs of
remote-sensing pipelines usually need a round or two of debugging. That is
expected. The science, methods, and writeup are complete and ready to be filled
in with the run's actual numbers.

## License

MIT (code). Text and figures: the author's, pending publication.
