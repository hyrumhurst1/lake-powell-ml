# Four Decades of Lake Powell Surface-Area Decline from a Trained Landsat Water Classifier, Validated Against Measured Reservoir Elevation

**Author:** Hyrum Hurst
**Affiliation:** Independent researcher
**Contact:** hyrumhurts@gmail.com

> Draft. Numbers written as `{{like_this}}` fill automatically from
> `results.json["paper_tokens"]` after you run the notebook
> (`python src/fill_paper.py`). Every citation must be verified against its real
> source before submission (see `paper/references.md`). Read
> `paper/defense_brief.md` before you submit.

---

## Abstract

Lake Powell, the second-largest reservoir in the United States, has fallen to
near-historic lows during the twenty-first-century Colorado River drought. We
reconstruct the reservoir's water-surface area from the Landsat archive using a
supervised Random Forest classifier, and we validate the satellite measurement
against daily reservoir elevation published by the U.S. Bureau of Reclamation
(USBR). The classifier, trained on independent Global Surface Water labels and
evaluated on a spatially blocked held-out set, reached an overall accuracy of
`{{overall_accuracy}}` and a kappa of `{{kappa}}`, against `{{mndwi_overall_accuracy}}`
and `{{mndwi_kappa}}` for a standard MNDWI baseline. Using the cross-validated
area-versus-elevation relationship as the independent arbiter, the
`{{primary_method}}` surface-area series predicted measured elevation with a
cross-validated R-squared of `{{r2}}` and a root-mean-square error of `{{rmse_ft}}`
feet over `{{n_months}}` months. Mapped surface area declined `{{pct_area_decline}}`
percent from its peak (`{{area_peak_km2}}` km^2) to its recent trough
(`{{area_trough_km2}}` km^2). The method is fully reproducible on free, public
data and shows that a trained classifier on the open Landsat record can track a
major reservoir's decline to within a few feet of ground truth.

## 1. Introduction

The Colorado River supplies roughly 40 million people across seven U.S. states
and Mexico. Since about 2000 the basin has experienced one of the most severe
sustained droughts in its recorded history (Williams et al., 2022), and its two
largest reservoirs, Lake Powell and Lake Mead, have dropped toward levels that
threaten hydropower and water deliveries. In 2021 the federal government declared
the first-ever shortage on the river. Lake Powell, impounded by Glen Canyon Dam,
reached its lowest level since it first filled, and by mid-2026 it sits near 3,527
feet, about 23 percent of full capacity, roughly 157 feet above the dead-pool
elevation below which water can no longer pass through the dam.

Reservoir storage is normally tracked with in-situ gauges and known stage-storage
tables. Satellite remote sensing offers an independent, spatially explicit
alternative, because open water has a distinctive spectral signature. Surface-water
mapping from optical satellites is well established (McFeeters, 1996; Xu, 2006;
Pekel et al., 2016), and machine-learning classifiers are now widely used in its
place. The value of any such method is clearest when it is checked against an
independent measurement. Lake Powell is an ideal test case because USBR publishes
daily, high-quality elevation data.

This study asks a checkable question: **how accurately can a trained classifier on
the free, multi-decade Landsat record reproduce the known decline of Lake Powell?**
We build a monthly surface-area series with a Random Forest classifier, benchmark
it against a spectral-index baseline, and quantify how well it predicts measured
elevation.

## 2. Study Area

Lake Powell lies on the Colorado River at the Utah-Arizona border, formed by Glen
Canyon Dam (completed 1963) and first reaching full pool in 1980. At full pool
(elevation 3,700 feet) it holds about 24.3 million acre-feet. It is a long,
dendritic canyon reservoir with a highly convoluted shoreline, which makes
water-extent mapping more demanding than for a simple open lake and provides a
realistic stress test.

## 3. Data and Methods

### 3.1 Satellite imagery

We use Landsat Collection 2, Level 2 surface-reflectance imagery from Landsat 5
(Thematic Mapper), Landsat 7 (Enhanced Thematic Mapper Plus), Landsat 8, and
Landsat 9 (Operational Land Imager), accessed through Google Earth Engine
(Gorelick et al., 2017). The combined archive provides 30 m imagery from 1984 to
the present. We applied the Collection 2 surface-reflectance scaling and masked
fill, cloud, dilated-cloud, cloud-shadow, and snow pixels using the QA_PIXEL
quality band.

### 3.2 Water classification

Surface water was delineated with a supervised Random Forest classifier rather
than a fixed spectral index. All Landsat 4 to 9 scenes intersecting the area of
interest were harmonized to a common nine-band feature vector (six
surface-reflectance bands plus the MNDWI, NDWI, and NDVI indices). The identical
feature collection fed both the classifier and an MNDWI baseline so the two
methods could be compared on equal footing.

Training labels were derived from the JRC Global Surface Water occurrence layer
(Pekel et al., 2016), an independent product, using a hysteresis gap: pixels with
occurrence at or above 80 percent were labelled water and pixels at or below 10
percent were labelled land, with intermediate values discarded to avoid training
on ambiguous shoreline. To avoid trivially separable negatives, the land pool was
restricted to within five kilometres of any pixel that was ever water. The
training composite was a median of all four sensors spanning 1990 to 2021, so the
classifier saw both TM/ETM+ and OLI reflectance and was not specialized to a
single sensor era.

We drew a stratified sample of 2000 points per class and split it with a spatially
blocked scheme: each point was snapped to a roughly five-kilometre grid cell and
whole cells were assigned to training (70 percent) or testing (30 percent), so
that no test pixel was spatially adjacent to a training pixel. A Random Forest of
100 trees was trained on the training cells only. Accuracy was assessed on the
withheld cells using the Earth Engine error matrix, reporting overall accuracy,
the kappa coefficient, and per-class producer and consumer accuracies. As a
cross-sensor sanity check we additionally classified a Landsat 5 composite and
scored it against the same withheld labels, so any pre-OLI degradation was
measured rather than assumed.

Monthly water-surface area was computed by building one median reflectance
composite per month, applying the classifier once to that composite, multiplying
the resulting water mask by per-pixel area, and summing over the area of interest
in a fixed UTM Zone 12N projection. Months with no usable scenes, or with
valid-pixel coverage below 30 percent, were recorded as missing rather than zero.

### 3.3 Ground truth and validation

Daily Lake Powell elevation at Glen Canyon Dam was obtained from the USBR RISE
database (catalog item 508) and averaged to monthly means. Because reservoir
area-versus-elevation is monotonic but nonlinear, we fit a degree-two polynomial
relating satellite surface area to measured elevation and report cross-validated
R-squared and root-mean-square error in feet. The USBR comparison, not the
classification accuracy against JRC labels, is the independent arbiter of which
mask better measures the reservoir.

### 3.4 Reproducibility

All data are free and public, and all code is released. The analysis runs end to
end in a single Google Colab notebook.

## 4. Results

The Random Forest classifier reached a held-out overall accuracy of
`{{overall_accuracy}}` and kappa of `{{kappa}}` on the spatially blocked test set,
against `{{mndwi_overall_accuracy}}` and `{{mndwi_kappa}}` for the MNDWI baseline.
Both methods are scored against the JRC labels the classifier was trained on, so
this comparison measures how faithfully each reproduces the JRC water boundary,
not which is the better water detector in absolute terms. Applied to a Landsat 5
composite, the classifier reached `{{rf_out_of_era_L5_accuracy}}` accuracy,
indicating its cross-sensor behaviour back to the TM era.

Using the independent USBR comparison as the arbiter, the `{{primary_method}}`
surface-area series predicted measured elevation with a cross-validated R-squared
of `{{r2}}` and an elevation RMSE of `{{rmse_ft}}` feet over `{{n_months}}` months,
against `{{mndwi_r2_cv}}` and `{{mndwi_rmse_ft_cv}}` feet for the alternative mask.
The two area series agreed closely, with a mean absolute difference of
`{{area_series_mean_abs_diff_km2}}` km^2 and a Pearson correlation of
`{{area_series_pearson_r}}` over `{{area_series_shared_months}}` shared months.
Mapped surface area declined `{{pct_area_decline}}` percent from a peak of
`{{area_peak_km2}}` km^2 to a trough of `{{area_trough_km2}}` km^2.

**Figure 1.** Monthly water-surface area, Random Forest versus MNDWI.
**Figure 2.** Area versus USBR elevation with the fitted curve (cross-validated R-squared annotated).
**Figure 3.** Random Forest held-out confusion matrix, with overall accuracy and kappa.
**Figure 4.** Random Forest versus MNDWI: held-out accuracy and area agreement.

## 5. Discussion

The close agreement between a classifier-derived surface-area record and
independent in-situ elevation shows that a trained model on open imagery can
reconstruct a major reservoir's multi-decade decline to within a few feet of
measured ground truth. This matters because not every reservoir on Earth has the
daily, high-quality gauging that Lake Powell does. A method validated where strong
ground truth exists can then be applied where it does not.

The result also puts a number on the Colorado River drought as seen from orbit:
the reservoir's mapped surface shrank by roughly `{{pct_area_decline}}` percent
between its full and its recent low.

## 6. Limitations

- **The classification benchmark is partly circular.** The Random Forest is
  trained and tested against the same JRC label source, while MNDWI is
  unsupervised, so a head-to-head on JRC points shows the model reproduces the JRC
  boundary more faithfully than a fixed threshold does, not that it is a better
  detector in reality. This is exactly why the headline method is chosen on the
  independent USBR criterion, not on JRC point accuracy.
- **No independent ground-truth water mask.** There is no field-surveyed shoreline
  in the pipeline; the only independent reference is USBR elevation.
- **Cross-sensor shift.** Four Landsat sensors were combined; the reported
  Landsat 5 accuracy quantifies, but does not eliminate, pre-OLI degradation.
- **Landsat 7 gaps.** After 2003 the Landsat 7 scan-line corrector failed, leaving
  striped data gaps that monthly compositing only partly mitigates.
- **Mixed and shoreline pixels.** At 30 m resolution the convoluted shoreline
  produces mixed land-water pixels; coverage filtering reduces but does not remove
  this.
- **Validation is correlational.** A high cross-validated R-squared shows the
  satellite area tracks elevation well over the observed range; it does not by
  itself establish absolute volumetric accuracy, which would require a
  stage-storage-area model.

## 7. Conclusion

A free, fully reproducible pipeline trains a Random Forest water classifier on the
Landsat archive, reconstructs four decades of Lake Powell surface area, and
predicts measured reservoir elevation with a cross-validated R-squared of
`{{r2}}` and RMSE of `{{rmse_ft}}` feet. The reservoir's mapped surface shrank by
`{{pct_area_decline}}` percent from peak to recent trough. The approach offers a
transparent, low-cost tool for monitoring reservoir change, directly extensible to
reservoirs that lack in-situ gauging.

## Data and Code Availability

All code, the analysis notebook, and derived data are available at
`https://github.com/hyrumhurst1/lake-powell-ml`. Satellite data are from the USGS
Landsat archive via Google Earth Engine; reservoir elevation is from the USBR RISE
database (item 508); water-occurrence labels are from the JRC Global Surface Water
dataset.

## Author Contributions and AI-Assistance Disclosure

See `paper/ai_disclosure.md`. AI tools were used for code scaffolding, drafting,
and editing under the author's direction; the author is responsible for the study
design, the interpretation of results, and the accuracy of all claims.

## References

See `paper/references.md` for the full list with links. Verify each one before
submission.
