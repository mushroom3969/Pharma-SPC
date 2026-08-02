import pandas as pd
from scipy import stats

from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf, pacf


def check_nromality(data: pd.Series, alpha=0.05) -> dict:
    """
    Check if the data follows a normal distribution using the Shapiro-Wilk test.

    Parameters:
    data (array-like): The input data to be tested for normality.
    alpha (float): The significance level for the test (default is 0.05).

    Returns:
    dict: A dictionary containing the Shapiro-Wilk test statistic, p-value, and a boolean indicating whether the null hypothesis (data is normally distributed) is rejected.
    """
    stat, p_value = stats.shapiro(data)
    (osm, osr), _ = stats.probplot(data, dist="norm", plot=None)

    return {
        "shapiro_stat": stat,
        "shapiro_p_value": p_value,
        "reject_null": bool(p_value < alpha),
    }


def autocorrelation_check(data: pd.Series, alpha=0.05) -> dict:
    """
    Check for autocorrelation in the data using the Durbin-Watson test.

    Parameters:
    data (array-like): The input data to be tested for autocorrelation.
    alpha (float): The significance level for the test (default is 0.05).

    Returns:
    dict: A dictionary containing the ljungbox p-value, ACF values, and PACF values.
    """

    lags = min(10, len(data) - 1)

    lb_test = acorr_ljungbox(data, lags=lags, return_df=True)
    lb_p_value = lb_test["lb_pvalue"].values[0]

    acf_values = acf(data, nlags=lags)
    pacf_values = pacf(data, nlags=lags)

    return {
        "ljungbox_p_value": lb_p_value,
        "acf_values": acf_values,
        "pacf_values": pacf_values,
    }
