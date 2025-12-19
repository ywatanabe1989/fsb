"""Tests for FSB stats module."""

import numpy as np
import pytest

from fsb import stats
from fsb.stats import SCIPY_AVAILABLE, StatResult


class TestPToStars:
    """Test p_to_stars function."""
    
    def test_highly_significant(self):
        assert stats.p_to_stars(0.0001) == "***"
        assert stats.p_to_stars(0.001) == "***"
    
    def test_very_significant(self):
        assert stats.p_to_stars(0.005) == "**"
        assert stats.p_to_stars(0.01) == "**"
    
    def test_significant(self):
        assert stats.p_to_stars(0.03) == "*"
        assert stats.p_to_stars(0.05) == "*"
    
    def test_not_significant(self):
        assert stats.p_to_stars(0.1) == "n.s."
        assert stats.p_to_stars(0.5) == "n.s."


class TestFormatStat:
    """Test format_stat function."""
    
    def test_format_with_df(self):
        result = stats.format_stat(2.5, 0.03, df=28, test_name="t")
        assert "t(28)" in result
        assert "2.500" in result
        assert "0.030" in result
    
    def test_format_without_df(self):
        result = stats.format_stat(5.2, 0.0001, test_name="U")
        assert "U = 5.200" in result
        assert "p < .001" in result


class TestCohensD:
    """Test Cohen's d effect size."""
    
    def test_zero_effect(self):
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([1, 2, 3, 4, 5])
        d = stats.cohens_d(a, b)
        assert abs(d) < 0.01
    
    def test_large_effect(self):
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([5, 6, 7, 8, 9])
        d = stats.cohens_d(a, b)
        assert d < -1.0  # Large negative effect


class TestHedgesG:
    """Test Hedges' g effect size."""
    
    def test_hedges_g_smaller_than_d(self):
        a = np.array([1, 2, 3])
        b = np.array([4, 5, 6])
        d = stats.cohens_d(a, b)
        g = stats.hedges_g(a, b)
        # Hedges g should be smaller due to correction
        assert abs(g) < abs(d)


class TestInterpretCohensD:
    """Test effect size interpretation."""
    
    def test_negligible(self):
        assert stats.interpret_cohens_d(0.1) == "negligible"
    
    def test_small(self):
        assert stats.interpret_cohens_d(0.3) == "small"
    
    def test_medium(self):
        assert stats.interpret_cohens_d(0.6) == "medium"
    
    def test_large(self):
        assert stats.interpret_cohens_d(1.0) == "large"


class TestMultipleComparison:
    """Test multiple comparison corrections."""
    
    def test_bonferroni(self):
        p_values = np.array([0.01, 0.02, 0.03, 0.04])
        corrected, reject = stats.bonferroni(p_values, alpha=0.05)
        # All should be multiplied by 4
        assert np.allclose(corrected, [0.04, 0.08, 0.12, 0.16])
    
    def test_bonferroni_cap(self):
        p_values = np.array([0.5, 0.8])
        corrected, _ = stats.bonferroni(p_values)
        # Should be capped at 1.0
        assert all(corrected <= 1.0)
    
    def test_fdr_bh(self):
        p_values = np.array([0.01, 0.04, 0.03, 0.2])
        corrected, reject = stats.fdr_bh(p_values, alpha=0.05)
        assert len(corrected) == 4
        assert all(corrected <= 1.0)


@pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy not available")
class TestStatisticalTests:
    """Test statistical test functions."""
    
    def test_ttest_ind(self):
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([2, 3, 4, 5, 6])
        result = stats.ttest_ind(a, b)
        
        assert isinstance(result, StatResult)
        assert result.method["name"] == "ttest_ind"
        assert "statistic" in result.results
        assert "p_value" in result.results
        assert "df" in result.results
    
    def test_ttest_paired(self):
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([2, 3, 4, 5, 6])
        result = stats.ttest_paired(a, b)
        
        assert result.method["name"] == "ttest_paired"
        assert result.results["df"] == 4  # n - 1
    
    def test_mannwhitneyu(self):
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([3, 4, 5, 6, 7])
        result = stats.mannwhitneyu(a, b)
        
        assert result.method["name"] == "mannwhitneyu"
        assert "statistic" in result.results
    
    def test_anova_oneway(self):
        g1 = np.array([1, 2, 3])
        g2 = np.array([4, 5, 6])
        g3 = np.array([7, 8, 9])
        result = stats.anova_oneway(g1, g2, g3)
        
        assert result.method["name"] == "anova_oneway"
        assert result.inputs["n_groups"] == 3
    
    def test_pearsonr(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 2, 3, 4, 5])
        result = stats.pearsonr(x, y)
        
        assert result.method["name"] == "pearsonr"
        assert result.results["r"] == pytest.approx(1.0)
    
    def test_spearmanr(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])
        result = stats.spearmanr(x, y)
        
        assert result.method["name"] == "spearmanr"
        assert result.results["rho"] == pytest.approx(-1.0)


class TestStatResult:
    """Test StatResult dataclass."""
    
    def test_to_dict(self):
        result = StatResult(
            result_id="test",
            method={"name": "test"},
            inputs={"n": 10},
            results={"p_value": 0.05},
        )
        d = result.to_dict()
        
        assert d["result_id"] == "test"
        assert d["method"]["name"] == "test"
    
    def test_from_dict(self):
        d = {
            "result_id": "test",
            "method": {"name": "test"},
            "inputs": {"n": 10},
            "results": {"p_value": 0.05},
        }
        result = StatResult.from_dict(d)
        
        assert result.result_id == "test"
        assert result.results["p_value"] == 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
