from fastapi import APIRouter, Depends
from src.services.llm_metrics import llm_metrics
from src.auth import verify_api_key
from src.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/llm-metrics")
def get_llm_metrics():
    """
    Get LLM usage metrics including token counts and costs.
    Returns summary and recent call history.
    """
    return {
        "summary": llm_metrics.get_summary(),
        "recent_calls": llm_metrics.get_recent_calls(limit=10)
    }


@router.get("/llm-metrics/summary")
def get_llm_metrics_summary():
    """Get just the summary of LLM usage."""
    return llm_metrics.get_summary()
