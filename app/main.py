from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes.document import router as document_router
from app.routes.health import router as health_router
from app.core.middleware import LoggingMiddleware

app = FastAPI(
    title="AI Document Assistant API",
    description="Upload a PDF and ask questions using RAG — requires JWT auth",
    version="2.0.0",
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(document_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


@app.get("/")
def root():
    return {"message": "AI Document Assistant API is running 🚀", "version": "2.0.0"}