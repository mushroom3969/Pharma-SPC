from pydantic import BaseModel, Field
from typing import Optional


class CheckNormalityRequest(BaseModel):
    data: list[float] = Field()
    alpha: float = Field(default=0.05)

class NormalityResult(BaseModel):
    method: str = Field()
    statistic: float = Field()
    p_value: float = Field()
    alpha: float = Field()
    reject_null: bool = Field()

class PointData(BaseModel):
    x: float = Field()
    y: float = Field()

class ReferenceLine(BaseModel):
    x: float = Field()
    y: float = Field()

class QqplotResult(BaseModel):
    points: PointData = Field()
    reference_line: ReferenceLine = Field()
    r: float = Field()

class CheckNormalityResponse(BaseModel):
    normality: NormalityResult = Field()
    qq_plot: QqplotResult = Field()

class AutocorrelationCheckRequest(BaseModel):
    data: list[float] = Field()
    alpha: float = Field()

class AutocorrelationResult(BaseModel):
    method: str = Field()
    p_value: float = Field()
    reject_null: bool = Field()
 
class AcfPoint(BaseModel):
    x: float = Field()
    y: float = Field()

class PacfPoint(BaseModel):
    x: float = Field()
    y: float = Field()

class AutocorrelationResponse(BaseModel):
    autocorrelation: AutocorrelationResult = Field()
    acf_plot: AcfPoint = Field()
    pacf_plot: PacfPoint = Field()


class ImrPlotRequest(BaseModel):
    data: list[dict[float]] = Field()
    golden_batch_name: list = Field()
    control_feature: str = Field()

class ShewartchartResult(BaseModel):
    x: list[str] = Field()
    y: list[float] = Field()
    mean: float = Field()
    ucl: float = Field()
    lcl: float = Field()

class ImrPlotResponse(BaseModel):
    i_chart: ShewartchartResult = Field()
    mr_chart: ShewartchartResult = Field()

class EwmaPlotRequest(BaseModel):
    data: list[dict[float]] = Field()
    golden_batch_name: list[str] = Field()
    control_feature: str = Field()
    lambda_: float  = Field(default=0.2)
    l: float = Field(default=3)

class EwmaPlotResponse(BaseModel):
    x: list[str] = Field()
    y: list[float] = Field()
    mean: float = Field()
    ucl: float = Field()
    lcl: float = Field()

class CusumPlotRequest(BaseModel):
    data: list[dict[float]] = Field()
    control_feature: str = Field()
    target: float = Field(default=None)
    k: float = Field(default=0.5)
    h: float = Field(default=5.0)

class CusumPlotResponse(BaseModel):
    x: list[str] = Field()
    y_c_plus: list[float] = Field()
    y_c_minus: list[float] = Field()
    mean: float = Field()
    decision_limit: float = Field()