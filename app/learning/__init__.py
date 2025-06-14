"""
ParManusAI Self-Learning Module

This module provides self-learning and self-improving capabilities for the ParManusAI agent system.

Key Components:
- SelfLearningEngine: Core learning engine that tracks performance and identifies patterns
- LearningIntegration: Integration layer for enhancing existing agents with learning
- LearningRouter: Enhanced router with learning-based agent selection
- LearningAgentFactory: Factory for creating learning-enabled agents

Features:
- Task execution tracking and analysis
- Pattern recognition from success/failure patterns
- Performance monitoring and optimization suggestions
- Continuous learning and improvement
- Self-improvement recommendations
- Learning-based routing optimization

Usage:
    from app.learning import SelfLearningEngine, enable_learning_for_agent

    # Create learning engine
    learning_engine = SelfLearningEngine()

    # Enhance an agent with learning
    @enable_learning_for_agent
    class MyAgent(BaseAgent):
        pass
"""

from .integration import (
    LearningEnabledAgent,
    LearningIntegration,
    enable_learning_for_agent,
    export_learning_insights,
    get_learning_dashboard,
    get_system_suggestions,
    learning_integration,
)
from .learning_router import LearningAgentFactory, LearningRouter
from .self_learning import ImprovementPattern, LearningRecord, SelfLearningEngine

__version__ = "1.0.0"
__author__ = "ParManusAI Development Team"

__all__ = [
    # Core learning components
    "SelfLearningEngine",
    "LearningRecord",
    "ImprovementPattern",
    # Integration components
    "LearningIntegration",
    "LearningEnabledAgent",
    "learning_integration",
    "enable_learning_for_agent",
    # Utility functions
    "get_learning_dashboard",
    "get_system_suggestions",
    "export_learning_insights",
    # Enhanced routing
    "LearningRouter",
    "LearningAgentFactory",
]

# Module-level configuration
DEFAULT_LEARNING_CONFIG = {
    "learning_enabled": True,
    "pattern_confidence_threshold": 0.7,
    "learning_history_days": 30,
    "auto_improvement_enabled": False,  # Safety: disabled by default
    "performance_monitoring": True,
    "suggestion_display": True,
}


def get_learning_config():
    """Get the current learning configuration."""
    return DEFAULT_LEARNING_CONFIG.copy()


def set_learning_config(**kwargs):
    """Update learning configuration."""
    DEFAULT_LEARNING_CONFIG.update(kwargs)


# Quick setup function
def setup_learning_for_parmanusai():
    """Quick setup function to enable learning for the entire ParManusAI system."""
    print("🧠 Setting up self-learning capabilities for ParManusAI...")

    # Initialize learning engine
    learning_engine = SelfLearningEngine()
    print("✅ Learning engine initialized")

    # Setup integration
    integration = learning_integration
    print("✅ Learning integration configured")

    # Create learning router
    router = LearningRouter()
    print("✅ Learning router ready")

    print("🎉 Self-learning setup complete!")

    return {
        "learning_engine": learning_engine,
        "integration": integration,
        "router": router,
        "config": get_learning_config(),
    }
