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


