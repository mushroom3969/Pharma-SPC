import pandas as pd
import duckdb

from pathlib import Path
from src.core.spc_chart import SPCchart
from src.core.spc_diagnosis import check_nromality, autocorrelation_check


MART_DB_PATH = Path(__file__).resolve().parents[4] / "pipeline" / "pharma_pipeline.duckdb"
MART_TABLE = "pharma_analytics.mart_eg12014_cell_culture_production_sec03"


def _read_mart_data(canonical_feature: str) -> pd.DataFrame:
    con = duckdb.connect(str(MART_DB_PATH), read_only=True)
    long_df = con.execute(
        f"select base_batch_id, replicate_label, value from {MART_TABLE} where canonical_feature = ?",
        [canonical_feature],
    ).fetchdf()
    con.close()

    wide_df = long_df.pivot(index="base_batch_id", columns="replicate_label", values="value")
    wide_df = wide_df.sort_index().reset_index()
    wide_df = wide_df.rename(columns={"base_batch_id" : "batch"})

    return wide_df

def get_subgroup_size(canonical_feature: str) -> int:
    df = _read_mart_data(canonical_feature)
    return len(df.columns) - 1

def run_chart(chart_type: str, canonical_feature: str, **params) -> dict:
    df = _read_mart_data(canonical_feature)
    chart = SPCchart(df, canonical_feature, **params)
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

