from pydantic import BaseModel
from typing import Optional


class ChartLimits(BaseModel):
    mean: float
    ucl: float
    lcl: float
    values: list[Optional[float]]


class ImrPlotResponse(BaseModel):
    i_chart: ChartLimits
    mr_chart: ChartLimits


class XrPlotResponse(BaseModel):
    x_bar_chart: ChartLimits
    r_chart: ChartLimits


class XsPlotResponse(BaseModel):
    x_bar_chart: ChartLimits
    s_chart: ChartLimits


class EwmaPlotResponse(BaseModel):
    ewma_values: list[Optional[float]]
    mean: float
    ucl: float
    lcl: float


class CusumPlotResponse(BaseModel):
    mean: float
    c_plus: list[Optional[float]]
    c_minus: list[Optional[float]]
    decision_limit: float


SpectralPlotResponse = ChartLimits


class SpcChartInitRequest(BaseModel):
    canonical_feature: str
    golden_batches_index: Optional[list[int]] = None
    usl: Optional[float] = None
    lsl: Optional[float] = None
    lambda_: float = 0.2
    l: float = 3.0
    target : Optional[float] = None
    k: float = 0.5
    h: float = 5.0
    alpha: float = 0.05


class CheckNormalityResponse(BaseModel):
    shapiro_stat: float
    shapiro_p_value: float
    reject_null: bool


class CheckNormalityRequest(BaseModel):
    data: list[float]
    alpha: float = 0.05


class AutocorrelationCheckResponse(BaseModel):
    ljungbox_p_value: float
    acf_values: list[float]
    pacf_values: list[float]


class AutocorrelationCheckRequest(BaseModel):
    data: list[float]