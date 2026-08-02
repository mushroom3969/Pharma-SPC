import pandas as pd
import numpy as np
import pytest

from core.spc_diagnosis import check_nromality, autocorrelation_check


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
