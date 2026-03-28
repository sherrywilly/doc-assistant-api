from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.document import router

app = FastAPI(
    title="AI Document Assistant API",
    description="Upload a PDF and ask questions using RAG",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "AI Document Assistant API is running 🚀"}