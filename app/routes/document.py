from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.rag import process_document, answer_question
from app.core.security import get_current_user
import tempfile
import os

router = APIRouter()

# Keyed by (username, doc_id) to isolate each user's documents.
vectorstores: dict = {}


@router.post("/upload/{doc_id}", tags=["Documents"])
async def upload_document(
    doc_id: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    """Upload a PDF and index it for retrieval (authenticated)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        vectorstores[(current_user, doc_id)] = process_document(tmp_path)
    finally:
        os.unlink(tmp_path)

    return {
        "message": "Document processed successfully",
        "doc_id": doc_id,
    }


@router.post("/ask/{doc_id}", tags=["Documents"])
async def ask_question(
    doc_id: str,
    question: str,
    current_user: str = Depends(get_current_user),
):
    """Answer a question about a previously uploaded document (authenticated)."""
    key = (current_user, doc_id)
    if key not in vectorstores:
        raise HTTPException(
            status_code=404,
            detail="Document not found. Please upload the document first.",
        )

    answer = answer_question(vectorstores[key], question)
    return {
        "question": question,
        "answer": answer,
    }


@router.get("/docs/list", tags=["Documents"])
def list_documents(current_user: str = Depends(get_current_user)):
    """List all document IDs uploaded by the current user."""
    user_docs = [
        doc_id for (user, doc_id) in vectorstores if user == current_user
    ]
    return {"documents": user_docs}