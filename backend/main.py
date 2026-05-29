from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import approval, extraction, intake, po, requests, scoring

app = FastAPI(
    title="Procurement Automation API",
    description="AI-powered procurement pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://procurement-automation-taupe.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intake.router)
app.include_router(extraction.router)
app.include_router(scoring.router)
app.include_router(approval.router)
app.include_router(po.router)
app.include_router(requests.router)


@app.get("/health")
def health():
    return {"status": "ok"}
