from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.analytics import router as analytics_router
from app.db.session import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
	initialize_database()
	yield


app = FastAPI(title="WasteWise API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
	allow_credentials=False,
	allow_methods=["GET", "POST", "OPTIONS"],
	allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}
