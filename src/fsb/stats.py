"""
FSB Statistics Module.

Standalone statistical analysis for FSB bundles.
Integrates with stats/stats.json in the bundle format.

Features:
- Statistical tests (t-test, ANOVA, correlation, etc.)
- Effect sizes (Cohen's d, eta-squared, etc.)
- Multiple comparison correction (Bonferroni, FDR, Holm)
- Results formatting (p-to-stars, APA style)
- Integration with bundle Stats model

Dependencies:
- scipy (optional, for full statistical tests)
- numpy (for basic computations)

Example:
    >>> import fsb
    >>> from fsb.stats import ttest_ind, cohens_d, p_to_stars
    >>>
    >>> # Run t-test
    >>> result = ttest_ind(group1, group2)
    >>> print(f"p = {result['p_value']:.4f} {p_to_stars(result['p_value'])}")
    >>>
    >>> # Add to bundle
    >>> bundle.stats = {"analyses": [result]}
    >>> bundle.save()
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

# Check scipy availability
try:
    import scipy.stats as sp_stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

__all__ = [
    "SCIPY_AVAILABLE",
    # Tests
    "ttest_ind",
    "ttest_paired",
    "mannwhitneyu",
    "wilcoxon",
    "anova_oneway",
    "kruskal",
    "pearsonr",
    "spearmanr",
    "chi2_contingency",
    # Effect sizes
    "cohens_d",
    "hedges_g",
    "eta_squared",
    "r_to_d",
    # Correction
    "bonferroni",
    "holm",
    "fdr_bh",
    # Formatting
    "p_to_stars",
    "format_stat",
    "format_apa",
    # Result class
    "StatResult",
    # Bundle integration
    "add_analysis",
    "run_analysis",
]


# =============================================================================
# Result Data Class
# =============================================================================


@dataclass
class StatResult:
    """Standardized statistical result container."""

    result_id: str
    method: Dict[str, Any]
    inputs: Dict[str, Any]
    results: Dict[str, Any]
    display: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = {
            "result_id": self.result_id,
            "method": self.method,
            "inputs": self.inputs,
            "results": self.results,
        }
        if self.display:
            d["display"] = self.display
        if self.created_at:
            d["created_at"] = self.created_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StatResult":
        """Create from dictionary."""
        created_at = None
        if "created_at" in d:
            created_at = datetime.fromisoformat(d["created_at"])
        return cls(
            result_id=d["result_id"],
            method=d["method"],
            inputs=d["inputs"],
            results=d["results"],
            display=d.get("display"),
            created_at=created_at,
        )


# =============================================================================
# Formatting Functions
# =============================================================================


def p_to_stars(p: float, thresholds: Optional[Dict[float, str]] = None) -> str:
    """
    Convert p-value to significance stars.

    Args:
        p: P-value
        thresholds: Custom thresholds {0.001: "***", 0.01: "**", 0.05: "*"}

    Returns:
        Star notation string
    """
    if thresholds is None:
        thresholds = {0.001: "***", 0.01: "**", 0.05: "*"}

    for threshold, stars in sorted(thresholds.items()):
        if p <= threshold:
            return stars
    return "n.s."


def format_stat(
    statistic: float,
    p_value: float,
    df: Optional[float] = None,
    test_name: str = "t",
    precision: int = 3,
) -> str:
    """
    Format statistical result as string.

    Args:
        statistic: Test statistic value
        p_value: P-value
        df: Degrees of freedom (optional)
        test_name: Name of test statistic (t, F, U, etc.)
        precision: Decimal precision

    Returns:
        Formatted string like "t(28) = 2.45, p = 0.021"
    """
    if df is not None:
        if isinstance(df, float) and df == int(df):
            df = int(df)
        stat_str = f"{test_name}({df}) = {statistic:.{precision}f}"
    else:
        stat_str = f"{test_name} = {statistic:.{precision}f}"

    if p_value < 0.001:
        p_str = "p < .001"
    else:
        p_str = f"p = {p_value:.{precision}f}"

    return f"{stat_str}, {p_str}"


def format_apa(result: Union[StatResult, Dict[str, Any]]) -> str:
    """
    Format result in APA style.

    Args:
        result: StatResult or result dictionary

    Returns:
        APA-formatted string
    """
    if isinstance(result, StatResult):
        result = result.to_dict()

    method = result.get("method", {})
    results = result.get("results", {})

    test_name = method.get("name", "test")
    stat = results.get("statistic", 0)
    p = results.get("p_value", 1)
    df = results.get("df")

    # Map test names to symbols
    symbol_map = {
        "t-test": "t",
        "ttest_ind": "t",
        "ttest_paired": "t",
        "anova": "F",
        "anova_oneway": "F",
        "mannwhitneyu": "U",
        "wilcoxon": "W",
        "chi2": "χ²",
        "chi2_contingency": "χ²",
        "pearsonr": "r",
        "spearmanr": "ρ",
    }

    symbol = symbol_map.get(test_name, test_name[0].upper())
    return format_stat(stat, p, df, symbol)


# =============================================================================
# Statistical Tests
# =============================================================================


def _require_scipy():
    if not SCIPY_AVAILABLE:
        raise ImportError(
            "scipy required for statistical tests. Install with:\n"
            "  pip install fsb[stats]"
        )


def ttest_ind(
    a: np.ndarray,
    b: np.ndarray,
    equal_var: bool = False,
    result_id: Optional[str] = None,
) -> StatResult:
    """
    Independent samples t-test.

    Args:
        a: First group data
        b: Second group data
        equal_var: Assume equal variance (default: False, uses Welch's t-test)
        result_id: Optional result identifier

    Returns:
        StatResult with t-statistic and p-value
    """
    _require_scipy()

    a, b = np.asarray(a), np.asarray(b)
    stat, p = sp_stats.ttest_ind(a, b, equal_var=equal_var)

    # Calculate df
    if equal_var:
        df = len(a) + len(b) - 2
    else:
        # Welch-Satterthwaite
        va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
        na, nb = len(a), len(b)
        df = ((va / na + vb / nb) ** 2) / (
            (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
        )

    return StatResult(
        result_id=result_id or "ttest_ind",
        method={
            "name": "ttest_ind",
            "variant": "equal_var" if equal_var else "welch",
        },
        inputs={
            "n_groups": 2,
            "n_per_group": [len(a), len(b)],
        },
        results={
            "statistic": float(stat),
            "p_value": float(p),
            "df": float(df),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": format_stat(stat, p, df, "t"),
        },
    )


def ttest_paired(
    a: np.ndarray,
    b: np.ndarray,
    result_id: Optional[str] = None,
) -> StatResult:
    """Paired samples t-test."""
    _require_scipy()

    a, b = np.asarray(a), np.asarray(b)
    stat, p = sp_stats.ttest_rel(a, b)
    df = len(a) - 1

    return StatResult(
        result_id=result_id or "ttest_paired",
        method={"name": "ttest_paired", "variant": "paired"},
        inputs={"n_pairs": len(a)},
        results={
            "statistic": float(stat),
            "p_value": float(p),
            "df": float(df),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": format_stat(stat, p, df, "t"),
        },
    )


def mannwhitneyu(
    a: np.ndarray,
    b: np.ndarray,
    alternative: str = "two-sided",
    result_id: Optional[str] = None,
) -> StatResult:
    """Mann-Whitney U test (non-parametric)."""
    _require_scipy()

    a, b = np.asarray(a), np.asarray(b)
    stat, p = sp_stats.mannwhitneyu(a, b, alternative=alternative)

    return StatResult(
        result_id=result_id or "mannwhitneyu",
        method={"name": "mannwhitneyu", "alternative": alternative},
        inputs={"n_per_group": [len(a), len(b)]},
        results={
            "statistic": float(stat),
            "p_value": float(p),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": format_stat(stat, p, None, "U"),
        },
    )


def wilcoxon(
    a: np.ndarray,
    b: Optional[np.ndarray] = None,
    result_id: Optional[str] = None,
) -> StatResult:
    """Wilcoxon signed-rank test (non-parametric paired)."""
    _require_scipy()

    a = np.asarray(a)
    if b is not None:
        b = np.asarray(b)
        stat, p = sp_stats.wilcoxon(a, b)
    else:
        stat, p = sp_stats.wilcoxon(a)

    return StatResult(
        result_id=result_id or "wilcoxon",
        method={"name": "wilcoxon"},
        inputs={"n": len(a)},
        results={
            "statistic": float(stat),
            "p_value": float(p),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": format_stat(stat, p, None, "W"),
        },
    )


def anova_oneway(
    *groups: np.ndarray,
    result_id: Optional[str] = None,
) -> StatResult:
    """One-way ANOVA."""
    _require_scipy()

    groups = [np.asarray(g) for g in groups]
    stat, p = sp_stats.f_oneway(*groups)

    # Degrees of freedom
    k = len(groups)
    n = sum(len(g) for g in groups)
    df_between = k - 1
    df_within = n - k

    return StatResult(
        result_id=result_id or "anova_oneway",
        method={"name": "anova_oneway"},
        inputs={
            "n_groups": k,
            "n_per_group": [len(g) for g in groups],
        },
        results={
            "statistic": float(stat),
            "p_value": float(p),
            "df": (df_between, df_within),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": f"F({df_between}, {df_within}) = {stat:.3f}, p = {p:.3f}",
        },
    )


def kruskal(
    *groups: np.ndarray,
    result_id: Optional[str] = None,
) -> StatResult:
    """Kruskal-Wallis H-test (non-parametric ANOVA)."""
    _require_scipy()

    groups = [np.asarray(g) for g in groups]
    stat, p = sp_stats.kruskal(*groups)

    return StatResult(
        result_id=result_id or "kruskal",
        method={"name": "kruskal"},
        inputs={
            "n_groups": len(groups),
            "n_per_group": [len(g) for g in groups],
        },
        results={
            "statistic": float(stat),
            "p_value": float(p),
            "df": len(groups) - 1,
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": format_stat(stat, p, len(groups) - 1, "H"),
        },
    )


def pearsonr(
    x: np.ndarray,
    y: np.ndarray,
    result_id: Optional[str] = None,
) -> StatResult:
    """Pearson correlation coefficient."""
    _require_scipy()

    x, y = np.asarray(x), np.asarray(y)
    r, p = sp_stats.pearsonr(x, y)

    return StatResult(
        result_id=result_id or "pearsonr",
        method={"name": "pearsonr"},
        inputs={"n": len(x)},
        results={
            "statistic": float(r),
            "p_value": float(p),
            "r": float(r),
            "r_squared": float(r**2),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": f"r = {r:.3f}, p = {p:.3f}",
        },
    )


def spearmanr(
    x: np.ndarray,
    y: np.ndarray,
    result_id: Optional[str] = None,
) -> StatResult:
    """Spearman rank correlation."""
    _require_scipy()

    x, y = np.asarray(x), np.asarray(y)
    rho, p = sp_stats.spearmanr(x, y)

    return StatResult(
        result_id=result_id or "spearmanr",
        method={"name": "spearmanr"},
        inputs={"n": len(x)},
        results={
            "statistic": float(rho),
            "p_value": float(p),
            "rho": float(rho),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": f"ρ = {rho:.3f}, p = {p:.3f}",
        },
    )


def chi2_contingency(
    observed: np.ndarray,
    result_id: Optional[str] = None,
) -> StatResult:
    """Chi-square test of independence."""
    _require_scipy()

    observed = np.asarray(observed)
    chi2, p, dof, expected = sp_stats.chi2_contingency(observed)

    return StatResult(
        result_id=result_id or "chi2_contingency",
        method={"name": "chi2_contingency"},
        inputs={"shape": observed.shape},
        results={
            "statistic": float(chi2),
            "p_value": float(p),
            "df": int(dof),
        },
        display={
            "significance_label": p_to_stars(p),
            "formatted": format_stat(chi2, p, dof, "χ²"),
        },
    )


# =============================================================================
# Effect Sizes
# =============================================================================


def cohens_d(
    a: np.ndarray,
    b: np.ndarray,
    pooled: bool = True,
) -> float:
    """
    Calculate Cohen's d effect size.

    Args:
        a: First group
        b: Second group
        pooled: Use pooled standard deviation (default: True)

    Returns:
        Cohen's d value
    """
    a, b = np.asarray(a), np.asarray(b)
    na, nb = len(a), len(b)
    mean_diff = np.mean(a) - np.mean(b)

    if pooled:
        # Pooled standard deviation
        var_a = np.var(a, ddof=1)
        var_b = np.var(b, ddof=1)
        pooled_std = np.sqrt(((na - 1) * var_a + (nb - 1) * var_b) / (na + nb - 2))
        return mean_diff / pooled_std
    else:
        # Control group std
        return mean_diff / np.std(b, ddof=1)


def hedges_g(
    a: np.ndarray,
    b: np.ndarray,
) -> float:
    """
    Calculate Hedges' g (bias-corrected Cohen's d).

    Args:
        a: First group
        b: Second group

    Returns:
        Hedges' g value
    """
    d = cohens_d(a, b)
    n = len(a) + len(b)
    # Correction factor
    correction = 1 - (3 / (4 * n - 9))
    return d * correction


def eta_squared(
    *groups: np.ndarray,
) -> float:
    """
    Calculate eta-squared (η²) effect size for ANOVA.

    Args:
        *groups: Group arrays

    Returns:
        Eta-squared value
    """
    groups = [np.asarray(g) for g in groups]
    all_data = np.concatenate(groups)
    grand_mean = np.mean(all_data)

    # Between-group sum of squares
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)

    # Total sum of squares
    ss_total = np.sum((all_data - grand_mean) ** 2)

    return ss_between / ss_total if ss_total > 0 else 0.0


def r_to_d(r: float) -> float:
    """Convert correlation coefficient to Cohen's d."""
    return (2 * r) / np.sqrt(1 - r**2)


def interpret_cohens_d(d: float) -> str:
    """Interpret Cohen's d magnitude."""
    d = abs(d)
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"


# =============================================================================
# Multiple Comparison Correction
# =============================================================================


def bonferroni(
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bonferroni correction for multiple comparisons.

    Args:
        p_values: Array of p-values
        alpha: Significance level

    Returns:
        Tuple of (corrected_p_values, reject_null_array)
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    corrected = np.minimum(p_values * n, 1.0)
    reject = corrected < alpha
    return corrected, reject


def holm(
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Holm-Bonferroni step-down correction.

    Args:
        p_values: Array of p-values
        alpha: Significance level

    Returns:
        Tuple of (corrected_p_values, reject_null_array)
    """
    p_values = np.asarray(p_values)
    n = len(p_values)

    # Sort p-values
    sorted_idx = np.argsort(p_values)
    sorted_p = p_values[sorted_idx]

    # Calculate corrected p-values
    corrected = np.zeros(n)
    for i, p in enumerate(sorted_p):
        corrected[sorted_idx[i]] = min(p * (n - i), 1.0)

    # Ensure monotonicity
    for i in range(1, n):
        idx = sorted_idx[i]
        prev_idx = sorted_idx[i - 1]
        if corrected[idx] < corrected[prev_idx]:
            corrected[idx] = corrected[prev_idx]

    reject = corrected < alpha
    return corrected, reject


def fdr_bh(
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Benjamini-Hochberg FDR correction.

    Args:
        p_values: Array of p-values
        alpha: False discovery rate

    Returns:
        Tuple of (corrected_p_values, reject_null_array)
    """
    p_values = np.asarray(p_values)
    n = len(p_values)

    sorted_idx = np.argsort(p_values)
    sorted_p = p_values[sorted_idx]

    # Calculate corrected p-values
    corrected = np.zeros(n)
    for i in range(n):
        corrected[sorted_idx[i]] = sorted_p[i] * n / (i + 1)

    # Ensure monotonicity (from largest to smallest)
    for i in range(n - 2, -1, -1):
        idx = sorted_idx[i]
        next_idx = sorted_idx[i + 1]
        if corrected[idx] > corrected[next_idx]:
            corrected[idx] = corrected[next_idx]

    corrected = np.minimum(corrected, 1.0)
    reject = corrected < alpha
    return corrected, reject


# =============================================================================
# Bundle Integration
# =============================================================================


def add_analysis(
    bundle: "Bundle",
    result: Union[StatResult, Dict[str, Any]],
) -> None:
    """
    Add a statistical analysis result to a bundle.

    Args:
        bundle: FSB Bundle instance
        result: StatResult or result dictionary
    """
    if isinstance(result, StatResult):
        result = result.to_dict()

    stats = bundle.stats or {"analyses": []}
    if "analyses" not in stats:
        stats["analyses"] = []

    stats["analyses"].append(result)
    bundle.stats = stats


def run_analysis(
    bundle: "Bundle",
    test: str,
    groups: List[str],
    **kwargs,
) -> StatResult:
    """
    Run statistical analysis on bundle data.

    Args:
        bundle: FSB Bundle with data
        test: Test name ("ttest_ind", "anova_oneway", etc.)
        groups: List of column names or group identifiers
        **kwargs: Additional test arguments

    Returns:
        StatResult

    Example:
        >>> result = run_analysis(bundle, "ttest_ind", ["control", "treatment"])
        >>> add_analysis(bundle, result)
    """
    import pandas as pd

    # Load data
    bundle_dir = bundle._get_bundle_dir()
    data_path = bundle_dir / "data" / "data.csv"

    if not data_path.exists():
        raise FileNotFoundError(f"No data file found: {data_path}")

    df = pd.read_csv(data_path)

    # Get test function
    test_funcs = {
        "ttest_ind": ttest_ind,
        "ttest_paired": ttest_paired,
        "mannwhitneyu": mannwhitneyu,
        "wilcoxon": wilcoxon,
        "anova_oneway": anova_oneway,
        "kruskal": kruskal,
        "pearsonr": pearsonr,
        "spearmanr": spearmanr,
    }

    if test not in test_funcs:
        raise ValueError(f"Unknown test: {test}. Available: {list(test_funcs.keys())}")

    func = test_funcs[test]

    # Extract group data
    group_data = []
    for g in groups:
        if g in df.columns:
            group_data.append(df[g].dropna().values)
        else:
            raise ValueError(f"Column not found: {g}")

    # Run test
    result_id = kwargs.pop("result_id", f"{test}_{'_vs_'.join(groups)}")

    if test in ("pearsonr", "spearmanr"):
        result = func(group_data[0], group_data[1], result_id=result_id, **kwargs)
    elif test in ("ttest_ind", "ttest_paired", "mannwhitneyu"):
        result = func(group_data[0], group_data[1], result_id=result_id, **kwargs)
    else:
        result = func(*group_data, result_id=result_id, **kwargs)

    return result


# EOF
