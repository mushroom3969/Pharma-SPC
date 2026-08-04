
from fastapi import APIRouter, HTTPException
from src.schema import *
from src.orchestration.spc_orchestrator import *


router = APIRouter()

@router.post("/spc/diagnosis/normality", response_model=CheckNormalityResponse)
def check_normality(request: CheckNormalityRequest):
    try:
        return run_diagnosis("Normality", request.data, request.alpha)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/spc/diagnosis/autocorrelation", response_model=AutocorrelationCheckResponse)
def check_autocorrelation(request: AutocorrelationCheckRequest):
    try:
        return run_diagnosis("Autocorrelation", request.data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


CHART_RESPONSE_MODELS = {
    "imr": ImrPlotResponse,
    "xr": XrPlotResponse,
    "xs": XsPlotResponse,
    "ewma": EwmaPlotResponse,
    "cusum": CusumPlotResponse,
    "spectral": SpectralPlotResponse,
}


def make_chart_endpoint(chart_type: str):
    def endpoint(request: SpcChartInitRequest):
        params = request.model_dump(exclude={"canonical_feature"})
        try:
            return run_chart(f"{chart_type}_plot",  request.canonical_feature, **params)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    return endpoint


for chart_type, response_model in CHART_RESPONSE_MODELS.items():
    router.add_api_route(
        path=f"/spc/chart/{chart_type}",
        endpoint=make_chart_endpoint(chart_type),
        methods=["POST"],
        response_model=response_model
    )


@router.get("/spc/chart/available-types", response_model=list[str])
def get_available_chart_types(canonical_feature: str):
    subgroup_size = get_subgroup_size(canonical_feature)
    return available_chart_types(subgroup_size)