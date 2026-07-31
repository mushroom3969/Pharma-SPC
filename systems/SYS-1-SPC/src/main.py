from fastapi import FastAPI

from src.router import router

app = FastAPI(title="SYS-1-SPC")
app.include_router(router)
