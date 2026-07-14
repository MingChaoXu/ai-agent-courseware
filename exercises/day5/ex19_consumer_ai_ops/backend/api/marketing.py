"""Marketing endpoints - RFM + Persona + Sentiment + Strategy + ROI Simulation."""

from fastapi import APIRouter, HTTPException

from models.schemas import PersonaRequest, SentimentRequest, StrategyRequest, ROISimulateRequest
from data_loader import DataLoader
from services.marketing_engine import (
    analyze_segmentation,
    generate_persona,
    analyze_sentiment,
    generate_strategy,
    simulate_roi,
)

router = APIRouter()


@router.get("/marketing/segmentation")
def marketing_segmentation():
    """RFM segmentation data (computed, no LLM)."""
    return analyze_segmentation()


@router.post("/marketing/persona")
def marketing_persona(req: PersonaRequest):
    """Generate customer persona (LLM-powered)."""
    result = generate_persona(req.customer_id)
    if "error" in result and result.get("error", "").startswith("LLM"):
        raise HTTPException(503, result["error"])
    return result


@router.get("/marketing/persona/{customer_id}")
def marketing_persona_get(customer_id: str):
    """Generate customer persona (GET version)."""
    return generate_persona(customer_id)


@router.post("/marketing/sentiment")
def marketing_sentiment(req: SentimentRequest):
    """Sentiment analysis (LLM-powered)."""
    result = analyze_sentiment(req.category)
    if "error" in result and result.get("error", "").startswith("LLM"):
        raise HTTPException(503, result["error"])
    return result


@router.post("/marketing/strategy")
def marketing_strategy(req: StrategyRequest):
    """Generate campaign strategy (LLM-powered)."""
    result = generate_strategy(req.segment, req.objective)
    if "error" in result and result.get("error", "").startswith("LLM"):
        raise HTTPException(503, result["error"])
    return result


@router.post("/marketing/simulate")
def marketing_simulate(req: ROISimulateRequest):
    """ROI simulation (computed, no LLM)."""
    return simulate_roi(req.budget, req.target_segment, req.channel_mix)


@router.get("/marketing/visualization")
def marketing_visualization():
    """Pre-computed marketing visualization data (no LLM)."""
    return {
        "segmentation": DataLoader.segmentation_data(),
        "sentiment": DataLoader.sentiment_data(),
    }
