import pandas as pd
import numpy as np
import pytest

from src.core.spc_chart import SPCchart


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
def subgroup5_df():
    """ """
    rng = np.random.default_rng(42)
    df = pd.DataFrame(rng.normal(10, 1, (20, 5)))
    df.insert(0, "batch", range(20))
    return df


@pytest.fixture
def subgroup12_df():
    """ """
    rng = np.random.default_rng(42)
    df = pd.DataFrame(rng.normal(10, 1, (20, 12)))
    df.insert(0, "batch", range(20))
    return df


@pytest.fixture
def small_individual_df():
    """
    handcrafted subgroup_size = 1 data for exact-value assertions
    values: [10, 12, 11, 13, 9]
    """
    return pd.DataFrame({"batch": range(5), 0: [10, 12, 11, 13, 9]})


@pytest.fixture
def small_subgroup2_df():
    """
    handcrafted subgroup_size = 2 data for exact-value assertions
    batch0: [10, 12], batch1: [8, 14]
    """
    df = pd.DataFrame([[10, 12], [8, 14]])
    df.insert(0, "batch", range(2))
    return df


class TestImrPlot:
    def test_returns_expected_keys(self, individual_df):
        result = SPCchart(individual_df, "control_variable").imr_plot()
        assert set(result.keys()) == {"i_chart", "mr_chart"}
        assert set(result["i_chart"].keys()) == {"mean", "ucl", "lcl"}
        assert set(result["mr_chart"].keys()) == {"mean", "ucl", "lcl"}

    def test_wrong_subgroup_size_raises(self, subgroup5_df):
        with pytest.raises(ValueError):
            SPCchart(subgroup5_df, "control_variable").imr_plot()

    def test_ucl_above_mean_above_lcl(self, individual_df):
        result = SPCchart(individual_df, "control_variable").imr_plot()
        assert (
            result["i_chart"]["lcl"]
            < result["i_chart"]["mean"]
            < result["i_chart"]["ucl"]
        )

    def test_exact_values(self, small_individual_df):
        result = SPCchart(small_individual_df, "control_variable").imr_plot()
        assert result["i_chart"]["mean"] == pytest.approx(11)
        assert result["mr_chart"]["mean"] == pytest.approx(2.25)
        assert result["i_chart"]["ucl"] == pytest.approx(16.985)
        assert result["i_chart"]["lcl"] == pytest.approx(5.015)
        assert result["mr_chart"]["ucl"] == pytest.approx(7.3575)
        assert result["mr_chart"]["lcl"] == 0

    def test_golden_batches_index_filters_data(self, small_individual_df):
        subset = SPCchart(
            small_individual_df, "control_variable", golden_batches_index=[0, 1, 3]
        ).imr_plot()
        assert subset["i_chart"]["mean"] == pytest.approx((10 + 12 + 13) / 3)


class TestXrPlot:
    def test_returns_expected_keys(self, subgroup5_df):
        result = SPCchart(subgroup5_df, "control_variable").xr_plot()
        assert set(result.keys()) == {"x_bar_chart", "r_chart"}

    def test_unsupported_subgroup_size_raises(self, subgroup12_df):
        with pytest.raises(ValueError):
            SPCchart(subgroup12_df, "control_variable").xr_plot()

    def test_ucl_above_lcl(self, subgroup5_df):
        result = SPCchart(subgroup5_df, "control_variable").xr_plot()
        assert result["x_bar_chart"]["lcl"] < result["x_bar_chart"]["ucl"]
        assert result["r_chart"]["lcl"] <= result["r_chart"]["ucl"]

    def test_exact_values(self, small_subgroup2_df):
        result = SPCchart(small_subgroup2_df, "control_variable").xr_plot()
        assert result["x_bar_chart"]["mean"] == pytest.approx(11)
        assert result["r_chart"]["mean"] == pytest.approx(4)
        assert result["x_bar_chart"]["ucl"] == pytest.approx(18.52)
        assert result["x_bar_chart"]["lcl"] == pytest.approx(3.48)
        assert result["r_chart"]["ucl"] == pytest.approx(13.068)
        assert result["r_chart"]["lcl"] == 0


class TestXsPlot:
    def test_returns_expected_keys(self, subgroup12_df):
        result = SPCchart(subgroup12_df, "control_variable").xs_plot()
        assert set(result.keys()) == {"x_bar_chart", "s_chart"}

    def test_subgroup_size_below_2_raises(self, individual_df):
        with pytest.raises(ValueError, match="at least 2"):
            SPCchart(individual_df, "control_variable").xs_plot()

    def test_subgroup_size_below_10_raises(self, subgroup5_df):
        with pytest.raises(ValueError, match="at least 10"):
            SPCchart(subgroup5_df, "control_variable").xs_plot()

    def test_ucl_above_lcl(self, subgroup12_df):
        result = SPCchart(subgroup12_df, "control_variable").xs_plot()
        assert result["x_bar_chart"]["lcl"] < result["x_bar_chart"]["ucl"]
        assert result["s_chart"]["lcl"] <= result["s_chart"]["ucl"]


class TestEwmaPlot:
    def test_returns_expected_keys(self, individual_df):
        result = SPCchart(individual_df, "control_variable").ewma_plot()
        assert set(result.keys()) == {"ewma_values", "mean", "ucl", "lcl"}

    def test_values_length_matches_batch_count(self, subgroup5_df):
        result = SPCchart(subgroup5_df, "control_variable").ewma_plot()
        assert len(result["ewma_values"]) == 20

    def test_first_value_equals_first_batch(self, small_individual_df):
        result = SPCchart(small_individual_df, "control_variable").ewma_plot()
        assert result["ewma_values"][0] == pytest.approx(10)

    def test_second_value_matches_formula(self, small_individual_df):
        result = SPCchart(
            small_individual_df, "control_variable", lambda_=0.2
        ).ewma_plot()
        expected = 0.2 * 12 + 0.8 * 10
        assert result["ewma_values"][1] == pytest.approx(expected)

    def test_ucl_above_lcl(self, individual_df):
        result = SPCchart(individual_df, "control_variable").ewma_plot()
        assert result["lcl"] < result["mean"] < result["ucl"]


class TestCusumPlot:
    def test_returns_expected_keys(self, individual_df):
        result = SPCchart(individual_df, "control_variable").cusum_plot()
        assert set(result.keys()) == {"mean", "c_plus", "c_minus", "decision_limit"}

    def test_c_plus_starts_at_zero_and_nonnegative(self, individual_df):
        result = SPCchart(individual_df, "control_variable").cusum_plot()
        assert result["c_plus"][0] == 0
        assert (result["c_plus"] >= 0).all()

    def test_c_minus_starts_at_zero_and_nonpositive(self, individual_df):
        result = SPCchart(individual_df, "control_variable").cusum_plot()
        assert result["c_minus"][0] == 0
        assert (result["c_minus"] <= 0).all()

    def test_target_overrides_mean(self, individual_df):
        default = SPCchart(individual_df, "control_variable").cusum_plot()
        targeted = SPCchart(individual_df, "control_variable", target=0).cusum_plot()
        assert targeted["mean"] == 0
        assert targeted["mean"] != default["mean"]


class TestSpectralPlot:
    def test_returns_usl_lsl_as_limits(self, individual_df):
        result = SPCchart(
            individual_df, "control_variable", usl=15, lsl=5
        ).spectral_plot()
        assert result["ucl"] == 15
        assert result["lcl"] == 5

    def test_mean_is_batch_average(self, small_individual_df):
        result = SPCchart(small_individual_df, "control_variable").spectral_plot()
        assert result["mean"] == pytest.approx(11)
