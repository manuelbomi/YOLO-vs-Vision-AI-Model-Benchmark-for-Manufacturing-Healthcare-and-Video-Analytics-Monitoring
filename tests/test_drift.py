import numpy as np

from api.drift.stats import analyze_feature, cohens_d, ks_test_drift, population_stability_index


def test_psi_near_zero_for_identical_distributions():
    rng = np.random.default_rng(0)
    reference = rng.normal(50, 10, size=1000)
    current = rng.normal(50, 10, size=1000)
    assert population_stability_index(reference, current) < 0.1


def test_psi_high_for_shifted_distribution():
    rng = np.random.default_rng(0)
    reference = rng.normal(50, 10, size=1000)
    current = rng.normal(90, 10, size=1000)  # shifted by 4 std devs
    assert population_stability_index(reference, current) > 0.25


def test_ks_pvalue_low_for_shifted_distribution():
    rng = np.random.default_rng(1)
    reference = rng.normal(0, 1, size=500)
    current = rng.normal(3, 1, size=500)
    _, pvalue = ks_test_drift(reference, current)
    assert pvalue < 0.05


def test_ks_pvalue_high_for_identical_distributions():
    rng = np.random.default_rng(1)
    reference = rng.normal(0, 1, size=500)
    current = rng.normal(0, 1, size=500)
    _, pvalue = ks_test_drift(reference, current)
    assert pvalue > 0.05


def test_cohens_d_sign_and_magnitude():
    rng = np.random.default_rng(2)
    reference = rng.normal(0, 1, size=500)
    current = rng.normal(1, 1, size=500)  # one std dev higher
    d = cohens_d(reference, current)
    assert 0.7 < d < 1.3


def test_analyze_feature_verdict_none_for_identical():
    rng = np.random.default_rng(3)
    reference = rng.normal(100, 5, size=500)
    current = rng.normal(100, 5, size=500)
    result = analyze_feature("brightness", reference, current)
    assert result.verdict == "none"


def test_analyze_feature_verdict_significant_for_large_shift():
    rng = np.random.default_rng(3)
    reference = rng.normal(100, 5, size=500)
    current = rng.normal(160, 5, size=500)
    result = analyze_feature("brightness", reference, current)
    assert result.verdict == "significant"
