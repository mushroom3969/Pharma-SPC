import pandas as pd
import duckdb

from pathlib import Path
from src.core.spc_chart import imr_plot, ewma_plot, cusum_plot
from src.core.spc_diagnosis import check_nromality, autocorrelation_check


def database_table_selection(product: str, process_step: str, scale: str = "", version: str = ""):
    MART_DB_PATH = (
        Path(__file__).resolve().parents[4] / "pipeline" / "pharma_pipeline.duckdb"
    )

    # 基本架構
    table_parts = ["pharma_analytics", f"mart_{product}_{process_step}"]

    # 如果有 scale，就加進去
    if scale:
        table_parts.append(scale)

    # 如果有 version，就加進去
    if version:
        table_parts.append(version)

    # 用底線把所有部分串接起來
    MART_TABLE = "_".join(table_parts)

    return MART_DB_PATH, MART_TABLE



