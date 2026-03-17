from fastapi import FastAPI
from app.routes.document import router

app = FastAPI(
    title="AI Document Assistant API",
    description="Upload a PDF and ask questions using RAG",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI Document Assistant API is running 🚀"}