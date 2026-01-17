from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from src.logging_config import get_logger
from src.metrics import track_llm_call

logger = get_logger(__name__)


@dataclass
class LLMUsage:
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    

@dataclass 
class LLMMetrics:
    """Track LLM API usage and costs."""
    
    PRICING: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "gemini-2.5-flash": {
            "input": 0.000000075,
            "output": 0.0000003,
        },
        "gemini-2.0-flash": {
            "input": 0.0000001,
            "output": 0.0000004,
        },
        "gemini-1.5-flash": {
            "input": 0.000000075,
            "output": 0.0000003,
        },
        "gemini-1.5-pro": {
            "input": 0.00000125,
            "output": 0.000005,
        },
    })
    
    usage_history: List[LLMUsage] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    
    def track_call(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> LLMUsage:
        """
        Record LLM API call metrics.
        
        Args:
            model: The model name (e.g., "gemini-2.5-flash")
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            
        Returns:
            LLMUsage record with calculated cost
        """
        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        
        cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])
        
        usage = LLMUsage(
            timestamp=datetime.utcnow(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost
        )
        
        self.usage_history.append(usage)
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
        
        track_llm_call(model, input_tokens, output_tokens, "success")
        
        logger.info(
            "LLM API call tracked",
            extra={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": f"{cost:.8f}",
                "total_cost_usd": f"{self.total_cost_usd:.6f}"
            }
        )
        
        return usage
    
    def track_failed_call(self, model: str, error: str) -> None:
        """Record a failed LLM API call."""
        track_llm_call(model, 0, 0, "failed")
        logger.warning(
            "LLM API call failed",
            extra={"model": model, "error": error}
        )
    
    def get_summary(self) -> Dict:
        """Get summary of LLM usage metrics."""
        return {
            "total_calls": len(self.usage_history),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "average_cost_per_call": round(
                self.total_cost_usd / len(self.usage_history), 6
            ) if self.usage_history else 0,
            "average_tokens_per_call": round(
                (self.total_input_tokens + self.total_output_tokens) / len(self.usage_history)
            ) if self.usage_history else 0,
        }
    
    def get_recent_calls(self, limit: int = 10) -> List[Dict]:
        """Get the most recent LLM calls."""
        recent = self.usage_history[-limit:] if self.usage_history else []
        return [
            {
                "timestamp": u.timestamp.isoformat(),
                "model": u.model,
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "cost_usd": round(u.cost_usd, 8)
            }
            for u in reversed(recent)
        ]


llm_metrics = LLMMetrics()
