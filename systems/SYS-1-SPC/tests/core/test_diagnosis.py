import pandas as pd
import numpy as np
import pytest

from src.core.spc_diagnosis import check_nromality, autocorrelation_check


@pytest.fixture
def individual_df():
    """
    subgroup_size = 1
    20 batches
    N(10, 1)
    """
    rng = np.random.default_rng(42)
    return pd.DataFrame({"batch": range(20), 0: rng.normal(10, 1, 20)})


@pytest.fixture
def normal_data():
    """
    non-normal
    N(0,1), sample size = 200
    """
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(0, 1, 200))


@pytest.fixture
def non_normal_data():
    """
    normal
    exp()
    """
    rng = np.random.default_rng(42)
    return pd.Series(rng.exponential(size=200))


@pytest.fixture
def white_noise_data():
    """
    no autocorrelation: independent
    """
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(0, 1, 200))


@pytest.fixture
def autocorrelation_data():
    """
    autocorrelation: random walk (accumulate white noise)
    """
    rng = np.random.default_rng(42)
    return pd.Series(np.cumsum(rng.normal(0, 1, 200)))


@pytest.fixture
def few_data():
    """
    three datas
    """
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(0, 1, 1))


class TestCheckNormality:
    def test_normal_data_not_rejected(self, normal_data):
        result = check_nromality(normal_data)
        assert result["reject_null"] == False

    def test_non_normal_data_not_rejected(self, non_normal_data):
        result = check_nromality(non_normal_data)
        assert result["reject_null"] == True

    def test_reject_null_matches_pvalues(self, normal_data):
        result = check_nromality(normal_data, alpha=0.05)
        assert result["reject_null"] == (result["shapiro_p_value"] < 0.05)

    def test_too_few_points(self, few_data):
        with pytest.raises(ValueError):
            check_nromality(few_data)


class TestAutocorrelationCheck:
    def test_white_noise_in_lbtest(self, white_noise_data):
        result = autocorrelation_check(white_noise_data)
        assert result["ljungbox_p_value"] >= 0.05

    def test_random_walk_in_lbtest(self, autocorrelation_data):
        result = autocorrelation_check(autocorrelation_data)
        assert result["ljungbox_p_value"] <=0.05

    def test_too_few_points(self, few_data):
        with pytest.raises(ValueError):
            autocorrelation_check(few_data)
