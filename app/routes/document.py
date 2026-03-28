from fastapi import APIRouter, HTTPException, UploadFile, File
from app.services.rag import process_document, answer_question
import tempfile
import os

router = APIRouter()
vectorstores = {}


@router.post("/upload/{doc_id}")
async def upload_document(doc_id: str, file: UploadFile = File(...)):
    """Upload a PDF and index it for retrieval."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        vectorstores[doc_id] = process_document(tmp_path)
    finally:
        os.unlink(tmp_path)

    return {
        "message": "Document processed successfully",
        "doc_id": doc_id,
    }


@router.post("/ask/{doc_id}")
async def ask_question(doc_id: str, question: str):
    """Answer a question about a previously uploaded document."""
    if doc_id not in vectorstores:
        raise HTTPException(
            status_code=404,
            detail="Document not found. Please upload the document first.",
        )

    answer = answer_question(vectorstores[doc_id], question)
    return {
        "question": question,
        "answer": answer,
    }