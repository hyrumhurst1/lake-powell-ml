# Four Decades of Lake Powell Surface-Area Decline from Landsat, Validated Against Measured Reservoir Elevation

**Author:** Hyrum Hurst
**Affiliation:** Independent researcher
**Contact:** hyrumhurts@gmail.com

> Draft. Numbers written as `{{like_this}}` are filled automatically from
> `data/results.json` after you run the notebook (`python src/fill_paper.py`).
> Every citation must be verified against its real source before submission
> (see `paper/references.md`). Read `paper/defense_brief.md` before you submit.

---

## Abstract

Lake Powell, the second-largest reservoir in the United States, has fallen to
near-historic lows during the twenty-first-century Colorado River drought. We
reconstruct the reservoir's water-surface area from `{{n_matched_months}}` months
of Landsat imagery spanning `{{date_start}}` to `{{date_end}}` using the Modified
Normalized Difference Water Index (MNDWI), and we validate the satellite
measurement against daily reservoir elevation published by the U.S. Bureau of
Reclamation. Satellite-derived surface area predicts measured elevation with an
R^2 of `{{r2}}` and a root-mean-square error of `{{rmse_ft}}` feet. Surface area
declined `{{pct_area_decline_peak_to_trough}}` percent from its peak
(`{{area_peak_km2}}` km^2 in `{{area_peak_date}}`) to its trough
(`{{area_trough_km2}}` km^2 in `{{area_trough_date}}`). The method is fully
reproducible on free, public data and demonstrates that an openly available
satellite record can track a major reservoir's decline to within a few feet of
ground truth, without proprietary data or in-situ instrumentation.

## 1. Introduction

The Colorado River supplies water to roughly 40 million people across seven U.S.
states and Mexico. Since about 2000 the basin has experienced one of the most
severe sustained droughts in its recorded history (Williams et al., 2022), and
its two largest reservoirs, Lake Powell and Lake Mead, have dropped toward levels
that threaten hydropower generation and water deliveries. In 2021 the federal
government declared the first-ever shortage on the river. Lake Powell, impounded
by Glen Canyon Dam, reached its lowest level since it first filled, and as of
mid-2026 it sits near 3,527 feet, about 23 percent of full capacity, roughly 157
feet above the "dead pool" elevation at which water can no longer pass through
the dam.

Tracking how much water a reservoir holds usually relies on in-situ gauges and
known stage-storage tables. Satellite remote sensing offers an independent,
spatially explicit alternative: open water has a distinctive spectral signature,
so its extent can be mapped directly from imagery. Surface-water mapping from
optical satellites is well established (McFeeters, 1996; Xu, 2006; Pekel et al.,
2016), but its value is clearest when the satellite estimate is checked against
an independent measurement. Lake Powell is an ideal test case because the Bureau
of Reclamation publishes daily, high-quality elevation data, giving a strong
ground truth.

This study asks a simple, checkable question: **how accurately can a free,
multi-decade satellite record reproduce the known decline of Lake Powell?** We
build a monthly surface-area time series from the full Landsat archive and
quantify how well it predicts measured elevation.

## 2. Study Area

Lake Powell lies on the Colorado River at the Utah-Arizona border, formed by Glen
Canyon Dam (completed 1963) and first reaching full pool in 1980. At full pool
(elevation 3,700 feet) it holds about 24.3 million acre-feet. It is a long,
dendritic canyon reservoir with a highly convoluted shoreline, which makes
water-extent mapping more demanding than for a simple open lake and provides a
realistic stress test for the method.

## 3. Data and Methods

### 3.1 Satellite imagery

We use Landsat Collection 2, Level 2 surface-reflectance imagery from Landsat 5
(Thematic Mapper), Landsat 7 (Enhanced Thematic Mapper Plus), Landsat 8, and
Landsat 9 (Operational Land Imager), accessed through Google Earth Engine
(Gorelick et al., 2017). The combined archive provides 30 m imagery from 1984 to
the present. We applied the Collection 2 surface-reflectance scaling factors and
masked cloud, cloud shadow, cirrus, dilated cloud, and snow using the QA_PIXEL
quality band.

### 3.2 Water detection

Open water was identified with the Modified Normalized Difference Water Index
(Xu, 2006):

    MNDWI = (Green - SWIR1) / (Green + SWIR1)

Water reflects green and strongly absorbs shortwave infrared, yielding MNDWI > 0,
while land yields MNDWI < 0. MNDWI is preferred over the older NDWI (McFeeters,
1996) here because the shortwave-infrared band suppresses false positives from
bright canyon rock and built surfaces. Pixels with MNDWI greater than zero were
classified as water.

### 3.3 Surface-area time series

For each calendar month from 1984 through June 2026, we computed the median water
mask across all available scenes (the median is robust to residual cloud or
shadow), multiplied it by the true per-pixel area, and summed over a fixed study
polygon enclosing the reservoir's full-pool extent. This yields monthly water
surface area in square kilometers. Months with no usable observations were
dropped.

### 3.4 Ground truth and validation

Daily Lake Powell elevation at Glen Canyon Dam was obtained from the Bureau of
Reclamation RISE database (catalog item 508) and averaged to monthly means.
Because reservoir area-versus-elevation is monotonic but nonlinear, we fit a
degree-two polynomial relating satellite surface area to measured elevation and
evaluated it with the coefficient of determination (R^2) and root-mean-square
error (RMSE) in feet.

### 3.5 Reproducibility

All data are free and public, and all code is released (see Data and Code
Availability). The analysis runs end to end in a single Google Colab notebook.

## 4. Results

Across `{{n_matched_months}}` matched months from `{{date_start}}` to
`{{date_end}}`, satellite-derived surface area predicted measured elevation with
R^2 = `{{r2}}` and RMSE = `{{rmse_ft}}` feet. Surface area peaked at
`{{area_peak_km2}}` km^2 (`{{area_peak_date}}`) and reached a minimum of
`{{area_trough_km2}}` km^2 (`{{area_trough_date}}`), a decline of
`{{pct_area_decline_peak_to_trough}}` percent. The surface-area record (Figure 1)
closely mirrors the measured-elevation record (Figure 2), and the two are tightly
related (Figure 3).

**Figure 1.** Lake Powell water-surface area from Landsat, 1984 to 2026.
**Figure 2.** Measured reservoir elevation (USBR), with full-pool, minimum-power,
and dead-pool reference lines.
**Figure 3.** Satellite surface area versus measured elevation, with the fitted
curve.

## 5. Discussion

The close agreement between an entirely satellite-derived surface-area record and
independent in-situ elevation shows that open imagery can reconstruct a major
reservoir's multi-decade decline to within a few feet of measured ground truth.
This matters because not every reservoir on Earth has the daily, high-quality
gauging that Lake Powell does. A method validated where strong ground truth
exists can then be applied where it does not, giving a low-cost way to monitor
reservoirs that lack instrumentation.

The result also puts a number on the Colorado River drought as seen from orbit:
the reservoir's mapped water surface shrank by roughly
`{{pct_area_decline_peak_to_trough}}` percent between its full and its recent
low, a loss visible without any model of the basin, purely from counting water
pixels.

## 6. Limitations

Several factors bound the accuracy of this approach and should temper its claims:

- **Sensor harmonization.** Four Landsat sensors with slightly different spectral
  responses were combined; small cross-sensor biases may remain despite using a
  consistent surface-reflectance product.
- **Landsat 7 gaps.** After 2003 the Landsat 7 scan-line corrector failed,
  leaving striped data gaps that the monthly median only partly mitigates.
- **Cloud and shadow.** Residual cloud, terrain shadow in the canyon, and snow
  can be misclassified despite QA masking, adding noise to individual months.
- **Mixed and shoreline pixels.** At 30 m resolution, the convoluted shoreline
  produces mixed land-water pixels; a hard MNDWI threshold of zero is a
  simplification, and the optimal threshold can vary with conditions.
- **Validation is correlational.** A high R^2 shows the satellite area tracks
  elevation well over the observed range; it does not by itself establish
  absolute volumetric accuracy, which would require a stage-storage-area model.

These are honest constraints, not fatal ones: the validation against measured
elevation is precisely what makes the size of these effects quantifiable rather
than hidden.

## 7. Conclusion

A free, fully reproducible Landsat pipeline reconstructs four decades of Lake
Powell surface area and predicts measured reservoir elevation with R^2 =
`{{r2}}` and RMSE = `{{rmse_ft}}` feet. The reservoir's mapped surface shrank by
`{{pct_area_decline_peak_to_trough}}` percent from peak to recent trough. The
approach offers a transparent, low-cost tool for monitoring reservoir change,
and it is directly extensible to reservoirs that lack in-situ gauging.

## Data and Code Availability

All code, the analysis notebook, and derived data are available at:
`https://github.com/<HANDLE>/lake-powell-ml`. Satellite data are from the USGS
Landsat archive via Google Earth Engine; reservoir elevation is from the U.S.
Bureau of Reclamation RISE database (item 508).

## Author Contributions and AI-Assistance Disclosure

See `paper/ai_disclosure.md`. AI tools were used for code scaffolding, drafting,
and editing under the author's direction; the author is responsible for the
study design, the interpretation of results, and the accuracy of all claims.

## References

See `paper/references.md` for the full list with links. Verify each one before
submission.
