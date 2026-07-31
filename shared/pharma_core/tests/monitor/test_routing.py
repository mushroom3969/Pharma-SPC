import numpy as np
import pandas as pd
import pytest

from pharma_core.monitor.routing import (
    acf_pacf_data,
    batch_length_type,
    has_autocorrelation,
    has_high_collinearity,
    has_multi_phase_structure,
    has_sufficient_history,
    is_normal,
    monitoring_structure,
    qq_plot_data,
    scale_type,
    shift_type,
    subgroup_size_category,
)


def test_scale_type_accepts_known_values():
    assert scale_type("nominal") == "nominal"
    assert scale_type("ordinal") == "ordinal"
    assert scale_type("continuous") == "continuous"


def test_scale_type_rejects_unknown_value():
    with pytest.raises(ValueError):
        scale_type("unknown")


def test_is_normal_true_for_normal_sample():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=10, scale=2, size=200))
    result = is_normal(data)
    assert result.is_normal is True
    assert 0.0 <= result.p_value <= 1.0


def test_is_normal_false_for_skewed_sample():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.exponential(scale=2, size=200))
    result = is_normal(data)
    assert result.is_normal is False
    assert 0.0 <= result.p_value <= 1.0


def test_is_normal_drops_nan_before_testing():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=10, scale=2, size=200))
    data_with_nan = pd.concat([data, pd.Series([None, None])], ignore_index=True)
    assert is_normal(data_with_nan).is_normal is True


def test_is_normal_raises_on_insufficient_data():
    with pytest.raises(ValueError):
        is_normal(pd.Series([1.0, 2.0]))


def test_qq_plot_data_shapes_match_sample_size():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=10, scale=2, size=50))
    result = qq_plot_data(data)
    assert len(result["theoretical_quantiles"]) == 50
    assert len(result["sample_quantiles"]) == 50
    assert "slope" in result["fit_line"]


def test_qq_plot_data_raises_on_insufficient_data():
    with pytest.raises(ValueError):
        qq_plot_data(pd.Series([1.0, 2.0]))


def test_monitoring_structure_accepts_known_values():
    assert monitoring_structure("batch_aggregate") == "batch_aggregate"
    assert monitoring_structure("batch_trajectory") == "batch_trajectory"
    assert monitoring_structure("continuous_time_series") == "continuous_time_series"


def test_monitoring_structure_rejects_unknown_value():
    with pytest.raises(ValueError):
        monitoring_structure("batch_single_point")


def test_has_autocorrelation_false_for_white_noise():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=0, scale=1, size=200))
    result = has_autocorrelation(data)
    assert result.has_autocorrelation is False
    assert 0.0 <= result.p_value <= 1.0


def test_has_autocorrelation_true_for_random_walk():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=0, scale=1, size=200).cumsum())
    result = has_autocorrelation(data)
    assert result.has_autocorrelation is True


def test_has_autocorrelation_raises_on_insufficient_data():
    with pytest.raises(ValueError):
        has_autocorrelation(pd.Series(range(5)), lags=10)


def test_acf_pacf_data_shapes_match_nlags():
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=0, scale=1, size=200))
    result = acf_pacf_data(data, nlags=10)
    assert len(result["acf"]["values"]) == 11  # lag 0..10
    assert len(result["pacf"]["values"]) == 11
    assert len(result["acf"]["confint"]) == 11


def test_acf_pacf_data_raises_on_insufficient_data():
    with pytest.raises(ValueError):
        acf_pacf_data(pd.Series(range(5)), nlags=10)


def test_default_nlags_scales_with_sample_size():
    # n=200 -> min(10*log10(200), 200//2-1) = min(23, 99) = 23
    rng = np.random.default_rng(seed=42)
    data = pd.Series(rng.normal(loc=0, scale=1, size=200))

    result = has_autocorrelation(data)
    assert result.lags == 23

    qq = acf_pacf_data(data)
    assert len(qq["acf"]["values"]) == 24  # lag 0..23


def test_default_nlags_raises_when_sample_too_small():
    # n=3 -> min(10*log10(3), 3//2-1) = min(4, 0) = 0，lag 數不足以檢定
    with pytest.raises(ValueError):
        has_autocorrelation(pd.Series([1.0, 2.0, 3.0]))


def test_has_sufficient_history_true_when_enough_batches():
    assert has_sufficient_history(pd.Series(range(20))) is True
    assert has_sufficient_history(pd.Series(range(25))) is True


def test_has_sufficient_history_false_when_not_enough_batches():
    assert has_sufficient_history(pd.Series(range(19))) is False


def test_has_sufficient_history_drops_nan_before_counting():
    data = pd.Series([1.0] * 19 + [None, None])
    assert has_sufficient_history(data) is False
    data2 = pd.Series([1.0] * 20 + [None])
    assert has_sufficient_history(data2) is True


def test_has_sufficient_history_custom_threshold():
    assert has_sufficient_history(pd.Series(range(10)), min_batches=10) is True
    assert has_sufficient_history(pd.Series(range(9)), min_batches=10) is False


def test_shift_type_accepts_known_values():
    assert shift_type("short_term_large") == "short_term_large"
    assert shift_type("long_term_small") == "long_term_small"
    assert shift_type("multivariate") == "multivariate"


def test_shift_type_rejects_unknown_value():
    with pytest.raises(ValueError):
        shift_type("unknown")


def test_subgroup_size_category_boundaries():
    assert subgroup_size_category(1) == "n_1"
    assert subgroup_size_category(2) == "n_2_9"
    assert subgroup_size_category(9) == "n_2_9"
    assert subgroup_size_category(10) == "n_ge_10"
    assert subgroup_size_category(50) == "n_ge_10"


def test_subgroup_size_category_rejects_invalid_n():
    with pytest.raises(ValueError):
        subgroup_size_category(0)
    with pytest.raises(ValueError):
        subgroup_size_category(-1)


def test_has_high_collinearity_true_for_derived_column():
    rng = np.random.default_rng(seed=42)
    col1 = rng.normal(0, 1, 200)
    col2 = rng.normal(0, 1, 200)
    col3 = col1 + col2 + rng.normal(0, 0.01, 200)  # 幾乎是 col1+col2 的線性組合
    data = pd.DataFrame({"a": col1, "b": col2, "c": col3})
    result = has_high_collinearity(data)
    assert result.has_high_collinearity is True
    assert result.vif["c"] > 10


def test_has_high_collinearity_false_for_independent_columns():
    rng = np.random.default_rng(seed=42)
    data = pd.DataFrame(
        {
            "a": rng.normal(0, 1, 200),
            "b": rng.normal(0, 1, 200),
            "c": rng.normal(0, 1, 200),
        }
    )
    result = has_high_collinearity(data)
    assert result.has_high_collinearity is False


def test_has_high_collinearity_raises_on_single_column():
    data = pd.DataFrame({"a": range(50)})
    with pytest.raises(ValueError):
        has_high_collinearity(data)


def test_has_high_collinearity_raises_when_not_enough_rows():
    data = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0], "c": [5.0, 6.0]})
    with pytest.raises(ValueError):
        has_high_collinearity(data)


def _make_trajectory_df(lengths: dict) -> pd.DataFrame:
    rows = []
    for batch_no, n in lengths.items():
        for t in range(n):
            rows.append({"batch_no": batch_no, "time": t, "value": float(t)})
    return pd.DataFrame(rows)


def test_batch_length_type_equal():
    data = _make_trajectory_df({"B1": 10, "B2": 10, "B3": 10})
    assert batch_length_type(data) == "equal"


def test_batch_length_type_same_count_but_misaligned_time_is_unequal():
    # B1 t=[0,1,2,3,4]，B2 t=[0,1.5,2,3,5]：點數都是 5，但時間點沒對齊，仍算不等長
    data = pd.DataFrame(
        {
            "batch_no": ["B1"] * 5 + ["B2"] * 5,
            "time": [0, 1, 2, 3, 4, 0, 1.5, 2, 3, 5],
            "value": [1.0] * 10,
        }
    )
    assert (
        batch_length_type(data, unequal_selection="unequal_pointwise")
        == "unequal_pointwise"
    )


def test_batch_length_type_unequal_pointwise():
    data = _make_trajectory_df({"B1": 10, "B2": 8, "B3": 12})
    assert batch_length_type(data, unequal_selection="unequal_pointwise") == "unequal_pointwise"


def test_batch_length_type_unequal_functional():
    data = _make_trajectory_df({"B1": 10, "B2": 8, "B3": 12})
    assert batch_length_type(data, unequal_selection="unequal_functional") == "unequal_functional"


def test_batch_length_type_unequal_requires_selection():
    data = _make_trajectory_df({"B1": 10, "B2": 8})
    with pytest.raises(ValueError):
        batch_length_type(data)


def test_batch_length_type_rejects_unknown_selection():
    data = _make_trajectory_df({"B1": 10, "B2": 8})
    with pytest.raises(ValueError):
        batch_length_type(data, unequal_selection="dtw")


def test_batch_length_type_raises_on_missing_columns():
    data = pd.DataFrame({"batch_no": ["B1", "B1"], "value": [1.0, 2.0]}).drop(
        columns=["batch_no"]
    )
    with pytest.raises(ValueError):
        batch_length_type(data)


def test_batch_length_type_raises_on_missing_time_column():
    # 有 batch_no、value，但缺 time——之後 N1/N2 都需要 time 軸，這裡要先擋下來
    data = pd.DataFrame({"batch_no": ["B1", "B1"], "value": [1.0, 2.0]})
    with pytest.raises(ValueError):
        batch_length_type(data)


def test_has_multi_phase_structure_accepts_bool():
    assert has_multi_phase_structure(True) is True
    assert has_multi_phase_structure(False) is False


def test_has_multi_phase_structure_rejects_non_bool():
    with pytest.raises(ValueError):
        has_multi_phase_structure("true")
    with pytest.raises(ValueError):
        has_multi_phase_structure(1)
