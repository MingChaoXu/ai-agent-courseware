"""
Chat API - Multi-agent traffic incident analysis pipeline
"""

from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from db.database import create_incident, add_dispatch

router = APIRouter(tags=["chat"])

# Global agent instance (initialized in main.py)
agent_instance = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Run 5-agent traffic incident analysis pipeline.

    Pipeline: incident_analysis → [AMap enrichment] → impact_assessment
              → dispatch_plan → info_publish → review_report
    """
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API configuration.")

    try:
        from agent.agent import chat as agent_chat
        result = agent_chat(agent_instance, request.question)

        if result.get("error"):
            return ChatResponse(answer="", error=result["error"])

        # Auto-archive: create incident + dispatch record
        results = result.get("results", {})
        amap_mode = results.get("_amap_mode", "")
        try:
            incident = create_incident(
                description=request.question,
                incident_type="",
                location="",
                severity="",
                status="analyzed",
                amap_mode=amap_mode,
                ai_analysis=results.get("incident_analysis", "")[:500],
            )
            add_dispatch(
                incident_id=incident["id"],
                analysis_text=results.get("incident_analysis", ""),
                dispatch_plan=results.get("dispatch_plan", ""),
                publish_text=results.get("info_publish", ""),
                review_report=results.get("review_report", ""),
            )
        except Exception:
            pass  # Archiving failure should not block the response

        return ChatResponse(
            answer=result["answer"],
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
