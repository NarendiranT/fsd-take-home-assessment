from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.meetings import router
from app.observe import install

app = FastAPI(title="FSD Take Home Assignment")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)
install(app)
