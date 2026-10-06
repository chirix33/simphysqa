"""Reproduce the three-rater kappaSize::PowerBinary planning calculation.

Requires scipy. This script computes a model-based approximation, not an
exact finite-sample power guarantee or an observed audit result.
Source: https://github.com/cran/kappaSize/blob/master/R/powerBinary.R
"""
import json
import math
from scipy.optimize import brentq
from scipy.stats import chi2, ncx2

ALPHA = 0.20
TARGET_POWER = 0.80
PREVALENCE = 0.90
KAPPA_NULL = 0.60
KAPPA_ALTERNATIVE = 0.80
SELECTED_RECORDS = 140

def count_probabilities(kappa, p):
    # Distribution of 0, 1, 2, or 3 acceptable ratings for one record.
    return [
        (1 - p)**3 + p * kappa * ((1 - p)**2 + (1 - p)),
        3 * p * (1 - kappa) * (1 - p)**2,
        3 * p**2 * (1 - p) * (1 - kappa),
        p**3 + kappa * p * (1 - p**2),
    ]

null_probs = count_probabilities(KAPPA_NULL, PREVALENCE)
alternative_probs = count_probabilities(KAPPA_ALTERNATIVE, PREVALENCE)
effect = sum((b - a)**2 / a for a, b in zip(null_probs, alternative_probs))
critical_value = chi2.ppf(1 - ALPHA, df=1)
noncentrality = brentq(
    lambda value: ncx2.cdf(critical_value, df=1, nc=value)
    - (1 - TARGET_POWER), 0, 100
)
required_n = noncentrality / effect
print(json.dumps({
    "raters": 3,
    "nominal_confidence": 1 - ALPHA,
    "alpha_two_sided": ALPHA,
    "target_power": TARGET_POWER,
    "acceptable_rating_prevalence": PREVALENCE,
    "kappa_null": KAPPA_NULL,
    "kappa_alternative": KAPPA_ALTERNATIVE,
    "unrounded_records": required_n,
    "minimum_records": math.ceil(required_n),
    "selected_records": SELECTED_RECORDS,
    "selected_modeled_power": float(ncx2.sf(
        critical_value, df=1, nc=SELECTED_RECORDS * effect)),
    "null_expected_rating_count_cells": [SELECTED_RECORDS * x for x in null_probs],
    "alternative_expected_rating_count_cells": [SELECTED_RECORDS * x for x in alternative_probs],
}, indent=2))
