"""
Agent initialization wrapper for Consumer AI Ops Platform.
Provides lazy initialization for all 3 AI engines.
"""

from config import check_config


def create_agent():
    """Initialize all 3 AI engines. Returns None if LLM not configured."""
    if not check_config():
        return None
    # Engines are lazy-loaded on first use via service modules
    return {"bi": True, "cs": True, "marketing": True}


def get_modules():
    """Return available module names."""
    if check_config():
        return ["bi_analysis", "customer_service", "marketing_strategy"]
    return []
