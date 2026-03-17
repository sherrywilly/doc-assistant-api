from fastapi import APIRouter, UploadFile, File
from app.services.rag import process_document, answer_question
import tempfile
import os

router = APIRouter()
vectorstores = {}

@router.post("/upload/{doc_id}")
async def upload_document(doc_id: str, file: UploadFile = File(...)):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Process document
    vectorstores[doc_id] = process_document(tmp_path)
    os.unlink(tmp_path)

    return {
        "message": "Document processed successfully",
        "doc_id": doc_id
    }

@router.post("/ask/{doc_id}")
async def ask_question(doc_id: str, question: str):
    if doc_id not in vectorstores:
        return {"error": "Document not found. Please upload first."}

    answer = answer_question(vectorstores[doc_id], question)
    return {
        "question": question,
        "answer": answer
    }