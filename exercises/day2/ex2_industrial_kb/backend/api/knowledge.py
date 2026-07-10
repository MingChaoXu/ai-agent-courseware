"""
Knowledge Base API - manage documents and search
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from models.schemas import (
    KbUploadResponse, KbListResponse, KbDocument,
    KbSearchRequest, KbSearchResponse, SourceDocument,
)

router = APIRouter(tags=["knowledge"])

# Reference to knowledge base (set from main.py)
knowledge_base = None


@router.get("/knowledge", response_model=KbListResponse)
async def list_knowledge():
    """List all documents in the knowledge base."""
    if not knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized")
    docs = knowledge_base.list_documents()
    return KbListResponse(
        documents=[KbDocument(**d) for d in docs],
        total_chunks=knowledge_base.total_chunks,
    )


@router.post("/knowledge/upload-file", response_model=KbUploadResponse)
async def upload_file(file: UploadFile = File(...), chunk_size: int = Form(500)):
    """Upload a text or JSON file to the knowledge base."""
    if not knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized")

    try:
        content = (await file.read()).decode("utf-8")
        filename = file.filename or "uploaded_file"

        if filename.endswith(".json"):
            import json, tempfile, os
            tmp_path = os.path.join(tempfile.gettempdir(), f"upload_{filename}")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
            result = knowledge_base.upload_json_data(tmp_path)
            os.remove(tmp_path)
        else:
            result = knowledge_base.upload_text(title=filename, content=content, chunk_size=chunk_size)

        knowledge_base.save_index()
        return KbUploadResponse(
            status="ok",
            title=result["title"],
            chunks=result["chunks"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.post("/knowledge/search", response_model=KbSearchResponse)
async def search_knowledge(request: KbSearchRequest):
    """Search the knowledge base for relevant documents."""
    if not knowledge_base or not knowledge_base.is_loaded:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")
    try:
        results = knowledge_base.search_with_scores(request.query, top_k=request.top_k)
        return KbSearchResponse(
            results=[
                SourceDocument(content=doc.page_content[:500], score=float(score))
                for doc, score in results
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/knowledge/reload")
async def reload_knowledge():
    """Reload knowledge base from default data files."""
    if not knowledge_base:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized")
    try:
        result = knowledge_base.load_default_data()
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload error: {str(e)}")
