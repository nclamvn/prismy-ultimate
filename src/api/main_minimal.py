from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="PRISMY API - Minimal Test")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "PRISMY API Running", "status": "minimal", "port": os.getenv("PORT")}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "minimal"}

@app.get("/tiers")
def get_tiers():
    return {
        "tiers": ["basic", "standard", "premium"],
        "status": "available"
    }
