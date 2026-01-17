from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps
from typing import Callable

recipe_processing_time = Histogram(
    'recipe_processing_seconds',
    'Time spent processing recipes',
    ['source_type', 'status'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

llm_api_calls = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['model', 'status']
)

llm_tokens_used = Counter(
    'llm_tokens_total',
    'Total tokens used in LLM calls',
    ['model', 'type']
)

active_recipes = Gauge(
    'active_recipes_total',
    'Total number of active recipes in database'
)

recipes_imported = Counter(
    'recipes_imported_total',
    'Total recipes imported',
    ['source_type']
)

api_errors = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']
)


def track_recipe_processing(source_type: str = "unknown"):
    """Decorator to track recipe processing time and status."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                recipes_imported.labels(source_type=source_type).inc()
                return result
            except Exception as e:
                status = "failed"
                raise
            finally:
                duration = time.time() - start_time
                recipe_processing_time.labels(
                    source_type=source_type,
                    status=status
                ).observe(duration)
        return wrapper
    return decorator


def track_llm_call(model: str, input_tokens: int, output_tokens: int, status: str = "success"):
    """Record LLM API call metrics."""
    llm_api_calls.labels(model=model, status=status).inc()
    llm_tokens_used.labels(model=model, type="input").inc(input_tokens)
    llm_tokens_used.labels(model=model, type="output").inc(output_tokens)


def update_recipe_count(count: int):
    """Update the active recipes gauge."""
    active_recipes.set(count)


def track_api_error(endpoint: str, error_type: str):
    """Record API error metrics."""
    api_errors.labels(endpoint=endpoint, error_type=error_type).inc()
