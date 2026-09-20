"""Hand-rolled data-drift statistics: Population Stability Index, a
two-sample Kolmogorov-Smirnov test, and a standardized mean-shift (Cohen's
d). Pure numpy/scipy, no drift-detection library -- see README > Data drift
for why, and for what each of these numbers actually means and doesn't mean.

These operate on one feature (a 1D array of numbers) at a time: a reference
batch and a current batch. The demo API (api/drift/routes.py) extracts
simple, inspectable image features (mean brightness, contrast) as the thing
being monitored, but these functions don't care what the numbers represent
-- they'd work equally well on model confidence scores or anything else.
"""
from __future__ import annotations

import numpy as np
from pydantic import BaseModel
from scipy import stats as scipy_stats

PSI_MODERATE_THRESHOLD = 0.1
PSI_SIGNIFICANT_THRESHOLD = 0.25
KS_ALPHA = 0.05
COHENS_D_MODERATE = 0.5
COHENS_D_LARGE = 0.8


class FeatureDriftResult(BaseModel):
    feature: str
    reference_mean: float
    current_mean: float
    psi: float
    ks_statistic: float
    ks_pvalue: float
    cohens_d: float
    verdict: str  # "none" | "moderate" | "significant"
    low_variance_warning: bool = False


def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """PSI = sum((cur% - ref%) * ln(cur% / ref%)) over bins.

    Bin edges come from the REFERENCE distribution's quantiles, so the
    reference is (by construction) roughly uniform across bins -- PSI then
    measures how far the current batch has drifted from that baseline
    shape. Conventional reading: <0.1 no meaningful shift, 0.1-0.25
    moderate, >0.25 significant (used across the MLOps industry, not just
    here).
    """
    quantile_edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(quantile_edges) < 3:
        # Reference has too little spread to bin meaningfully (e.g. a
        # constant feature) -- treat as "cannot assess" rather than a false
        # confident zero.
        return 0.0

    ref_counts, _ = np.histogram(reference, bins=quantile_edges)
    cur_counts, _ = np.histogram(current, bins=quantile_edges)

    eps = 1e-6
    ref_pct = ref_counts / max(len(reference), 1) + eps
    cur_pct = cur_counts / max(len(current), 1) + eps

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def ks_test_drift(reference: np.ndarray, current: np.ndarray) -> tuple[float, float]:
    """Two-sample KS test. Returns (statistic, p_value). A low p-value
    (< 0.05 by convention) means the two samples are unlikely to come from
    the same distribution. Note: with very large samples (tens of
    thousands+), KS becomes oversensitive to trivial differences -- PSI is
    the more reliable trigger signal at that scale. This demo's sample
    sizes are small, where KS is informative.
    """
    result = scipy_stats.ks_2samp(reference, current)
    return float(result.statistic), float(result.pvalue)


def cohens_d(reference: np.ndarray, current: np.ndarray) -> float:
    """Standardized mean shift: (mean_current - mean_reference) / pooled_std.
    Conventional reading: |d| < 0.5 small, 0.5-0.8 moderate, > 0.8 large.
    """
    n1, n2 = len(reference), len(current)
    var1, var2 = np.var(reference, ddof=1), np.var(current, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / max(n1 + n2 - 2, 1))
    if pooled_std == 0:
        return 0.0
    return float((np.mean(current) - np.mean(reference)) / pooled_std)


def _verdict(psi: float, ks_pvalue: float, d: float) -> str:
    if psi > PSI_SIGNIFICANT_THRESHOLD or ks_pvalue < KS_ALPHA or abs(d) > COHENS_D_LARGE:
        return "significant"
    if psi > PSI_MODERATE_THRESHOLD or abs(d) > COHENS_D_MODERATE:
        return "moderate"
    return "none"


# Relative mean shift that triggers the low-variance fallback verdict below.
# Deliberately coarser than Cohen's d's thresholds -- it's a blunt backstop,
# not a replacement for the standardized statistics.
_LOW_VARIANCE_RELATIVE_SHIFT_THRESHOLD = 0.15


def analyze_feature(name: str, reference: np.ndarray, current: np.ndarray) -> FeatureDriftResult:
    psi = population_stability_index(reference, current)
    ks_stat, ks_p = ks_test_drift(reference, current)
    d = cohens_d(reference, current)
    reference_mean = float(np.mean(reference))
    current_mean = float(np.mean(current))
    verdict = _verdict(psi, ks_p, d)

    # A batch of near-identical images (zero within-batch variance) silently
    # zeroes out Cohen's d (divide-by-zero guard) and starves PSI/KS of the
    # spread they need -- an obviously shifted batch can otherwise come back
    # "none". Found this by hand while building the demo (see README > Data
    # drift). Rather than let that misreport silently, fall back to a plain
    # relative-mean-shift check whenever both batches individually have
    # near-zero variance, and say so explicitly rather than presenting it
    # with the same confidence as the standardized statistics.
    low_variance_warning = False
    if np.std(reference) < 1e-6 and np.std(current) < 1e-6:
        relative_shift = abs(current_mean - reference_mean) / (abs(reference_mean) + 1e-6)
        if relative_shift > _LOW_VARIANCE_RELATIVE_SHIFT_THRESHOLD:
            low_variance_warning = True
            verdict = "significant"

    return FeatureDriftResult(
        feature=name,
        reference_mean=reference_mean,
        current_mean=current_mean,
        psi=psi,
        ks_statistic=ks_stat,
        ks_pvalue=ks_p,
        cohens_d=d,
        verdict=verdict,
        low_variance_warning=low_variance_warning,
    )
