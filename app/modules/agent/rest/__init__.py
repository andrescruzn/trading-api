# -*- coding: utf-8 -*-

from .agent.routes import router as agent_router
from .models.routes import router as models_router
from .model_runs.routes import router as model_runs_router
from .recommendations.routes import router as recommendations_router

__all__ = ["agent_router", "models_router", "model_runs_router", "recommendations_router"]
