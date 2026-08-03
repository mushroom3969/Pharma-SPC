import pandas as pd

from src.core.spc_chart import SPCchart
from src.core.spc_diagnosis import check_nromality, autocorrelation_check


def run_chart(chart_type: str, data: list[dict[str, float]], control_variable: str, **params) -> dict:
    df = pd.DataFrame(data)
    chart = SPCchart(df, control_variable, **params)
    method = getattr(chart, chart_type)
    return method()

def available_chart_types(subgroup_size: int) -> list:
    result = ["ewma_plot", "cusum_plot", "spectral_plot"]
    if subgroup_size == 1:
        result.append("imr_plot")
    elif 2 <= subgroup_size <= 9:
        result.append("xr_plot")
    else:
        result.append("xs_plot") 
    return result

def run_diagnosis(diag_type: str, data: list[float], alpha: float=0.05):
    series = pd.Series(data)
    if diag_type == "Normality":
        return check_nromality(series, alpha)
    elif diag_type == "Autocorrelation":
        return autocorrelation_check(series, alpha)
