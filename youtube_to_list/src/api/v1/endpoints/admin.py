from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.services.llm_metrics import llm_metrics
from src.auth import verify_api_key
from src.logging_config import get_logger
from src.database import get_db
from src.models import Recipe

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


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive admin statistics including:
    - LLM usage and costs
    - Recipe counts by source type
    - Recent activity
    """
    llm_summary = llm_metrics.get_summary()
    recent_calls = llm_metrics.get_recent_calls(limit=20)
    
    source_counts = db.query(
        Recipe.source_type,
        func.count(Recipe.id).label('count')
    ).filter(
        Recipe.is_deleted == False
    ).group_by(Recipe.source_type).all()
    
    source_stats = {
        "youtube": 0,
        "instagram": 0,
        "tiktok": 0,
        "facebook": 0,
        "web": 0,
        "unknown": 0
    }
    
    for source_type, count in source_counts:
        if source_type in source_stats:
            source_stats[source_type] = count
        else:
            source_stats["unknown"] += count
    
    total_recipes = sum(source_stats.values())
    
    category_counts = db.query(
        Recipe.category,
        func.count(Recipe.id).label('count')
    ).filter(
        Recipe.is_deleted == False,
        Recipe.category.isnot(None)
    ).group_by(Recipe.category).order_by(func.count(Recipe.id).desc()).limit(10).all()
    
    category_stats = [{"category": cat, "count": cnt} for cat, cnt in category_counts]
    
    recent_recipes = db.query(Recipe).filter(
        Recipe.is_deleted == False
    ).order_by(Recipe.created_at.desc()).limit(5).all()
    
    recent_activity = [
        {
            "id": r.id,
            "name": r.name,
            "source_type": r.source_type,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in recent_recipes
    ]
    
    return {
        "llm": {
            "summary": llm_summary,
            "recent_calls": recent_calls
        },
        "recipes": {
            "total": total_recipes,
            "by_source": source_stats,
            "by_category": category_stats
        },
        "recent_activity": recent_activity
    }
