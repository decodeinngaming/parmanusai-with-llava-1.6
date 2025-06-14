"""
Integration module to add self-learning capabilities to existing ParManusAI agents.
This module patches the existing agent system to include learning functionality.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.learning.self_learning import (
    LearningEnabledAgent,
    LearningRecord,
    SelfLearningEngine,
)


class LearningIntegration:
    """Main integration class for adding learning to ParManusAI."""

    def __init__(self):
        self.learning_engine = SelfLearningEngine()
        self.enhanced_agents = {}
        self.original_agents = {}

    def enhance_agent(self, agent_class):
        """Enhance an agent class with learning capabilities."""

        class EnhancedAgent(agent_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.learning_engine = self.get_learning_engine()
                self.current_task_id = None
                self.task_start_time = None

            def get_learning_engine(self):
                """Get the shared learning engine instance."""
                return learning_integration.learning_engine

            async def step(self):
                """Enhanced step method with learning capabilities."""
                self.current_task_id = f"task_{int(time.time())}"
                self.task_start_time = time.time()

                # Get user request
                user_request = self._extract_user_request()

                # Get learning suggestions
                suggestions = self.learning_engine.get_improvement_suggestions(
                    user_request, {"agent_type": self.name}
                )

                # Show suggestions to user (optional)
                if suggestions and len(suggestions) > 0:
                    print(f"💡 Learning insights: {suggestions[0]}")

                try:
                    # Execute original agent logic
                    result = await super().step()

                    # Record successful execution
                    self._record_success(user_request, result)

                    return result

                except Exception as e:
                    # Record failed execution
                    self._record_failure(user_request, e)

                    # Re-raise the exception
                    raise

            def _extract_user_request(self) -> str:
                """Extract user request from messages."""
                user_request = ""
                if hasattr(self, "messages") and self.messages:
                    for msg in reversed(self.messages):
                        if msg.role == "user":
                            user_request = msg.content
                            break
                return user_request

            def _record_success(self, user_request: str, result: Any):
                """Record a successful task execution."""
                execution_time = time.time() - self.task_start_time

                record = LearningRecord(
                    task_id=self.current_task_id,
                    user_request=user_request,
                    agent_used=self.name,
                    success=True,
                    execution_time=execution_time,
                    error_message=None,
                    user_feedback_score=None,
                    timestamp=datetime.now(),
                    context={
                        "agent_type": self.name,
                        "result_length": len(str(result)) if result else 0,
                        "execution_speed": "fast" if execution_time < 5 else "slow",
                    },
                )

                self.learning_engine.record_task_execution(record)

                # Async analysis (don't block)
                asyncio.create_task(
                    self._analyze_success_patterns(user_request, result)
                )

            def _record_failure(self, user_request: str, error: Exception):
                """Record a failed task execution."""
                execution_time = time.time() - self.task_start_time

                record = LearningRecord(
                    task_id=self.current_task_id,
                    user_request=user_request,
                    agent_used=self.name,
                    success=False,
                    execution_time=execution_time,
                    error_message=str(error),
                    user_feedback_score=None,
                    timestamp=datetime.now(),
                    context={
                        "agent_type": self.name,
                        "error_type": type(error).__name__,
                        "execution_time": execution_time,
                    },
                )

                self.learning_engine.record_task_execution(record)

            async def _analyze_success_patterns(self, user_request: str, result: Any):
                """Analyze successful patterns for future optimization."""
                try:
                    # Simple pattern analysis
                    request_lower = user_request.lower()

                    # File creation patterns
                    if "create" in request_lower and "file" in request_lower:
                        if "html" in request_lower:
                            await self._learn_html_creation_pattern(
                                user_request, result
                            )
                        elif "css" in request_lower:
                            await self._learn_css_creation_pattern(user_request, result)

                    # Web search patterns
                    elif "search" in request_lower:
                        await self._learn_search_pattern(user_request, result)

                except Exception as e:
                    print(f"Pattern analysis error: {e}")

            async def _learn_html_creation_pattern(
                self, user_request: str, result: Any
            ):
                """Learn from HTML creation tasks."""
                # Analyze what makes HTML creation successful
                if (
                    "fancy" in user_request.lower()
                    or "advanced" in user_request.lower()
                ):
                    suggestion = "For advanced HTML requests, include animations and modern styling"
                else:
                    suggestion = "For simple HTML requests, focus on clean structure and readability"

                # Store the learning (this would be enhanced with actual pattern storage)
                print(f"🧠 Learned: {suggestion}")

            async def _learn_css_creation_pattern(self, user_request: str, result: Any):
                """Learn from CSS creation tasks."""
                if "button" in user_request.lower():
                    suggestion = (
                        "Button CSS requests benefit from multiple style variations"
                    )
                elif "animation" in user_request.lower():
                    suggestion = (
                        "Animation CSS should include keyframes and utility classes"
                    )
                else:
                    suggestion = "General CSS should follow modern design principles"

                print(f"🧠 Learned: {suggestion}")

            async def _learn_search_pattern(self, user_request: str, result: Any):
                """Learn from search task patterns."""
                suggestion = (
                    "Search tasks work best when combined with content creation"
                )
                print(f"🧠 Learned: {suggestion}")

        return EnhancedAgent

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get a comprehensive performance dashboard."""
        insights = self.learning_engine.get_performance_insights()

        # Add additional dashboard metrics
        dashboard = {
            "learning_status": "active",
            "insights": insights,
            "recommendations": self._generate_recommendations(insights),
            "last_updated": datetime.now().isoformat(),
        }

        return dashboard

    def _generate_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on insights."""
        recommendations = []

        if "overall_success_rate" in insights:
            success_rate = insights["overall_success_rate"]
            if success_rate < 0.8:
                recommendations.append(
                    "Consider improving error handling - success rate below 80%"
                )
            elif success_rate > 0.95:
                recommendations.append(
                    "Excellent performance! Consider documenting best practices"
                )

        if "avg_execution_time" in insights:
            avg_time = insights["avg_execution_time"]
            if avg_time > 10:
                recommendations.append(
                    "Execution times are high - consider optimization"
                )
            elif avg_time < 2:
                recommendations.append("Fast execution times - good performance")

        if "agent_performance" in insights:
            agent_perf = insights["agent_performance"]
            for agent, stats in agent_perf.items():
                if stats["success_rate"] < 0.7:
                    recommendations.append(
                        f"Agent '{agent}' needs improvement - low success rate"
                    )

        return recommendations

    def suggest_system_improvements(self) -> List[str]:
        """Suggest system-wide improvements based on learning data."""
        suggestions = []

        # Analyze recent patterns
        insights = self.learning_engine.get_performance_insights()

        # Performance-based suggestions
        if insights.get("avg_execution_time", 0) > 5:
            suggestions.extend(
                [
                    "Implement caching for frequently requested operations",
                    "Add progress indicators for long-running tasks",
                    "Consider parallel processing for independent operations",
                ]
            )

        # Success rate suggestions
        if insights.get("overall_success_rate", 1.0) < 0.8:
            suggestions.extend(
                [
                    "Improve error handling and recovery mechanisms",
                    "Add more specific error messages for user guidance",
                    "Implement fallback strategies for common failures",
                ]
            )

        # Agent-specific suggestions
        agent_performance = insights.get("agent_performance", {})
        for agent, stats in agent_performance.items():
            if stats["success_rate"] < 0.7:
                suggestions.append(f"Review and improve {agent} agent implementation")

        return suggestions

    def export_learning_data(self, file_path: str):
        """Export learning data for analysis or backup."""
        insights = self.learning_engine.get_performance_insights()

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "performance_insights": insights,
            "recommendations": self._generate_recommendations(insights),
            "system_suggestions": self.suggest_system_improvements(),
        }

        import json

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return f"Learning data exported to {file_path}"


# Global instance for easy access
learning_integration = LearningIntegration()


def enable_learning_for_agent(agent_class):
    """Decorator to enable learning for an agent class."""
    return learning_integration.enhance_agent(agent_class)


# Utility functions for easy integration
def get_learning_dashboard():
    """Get the current learning dashboard."""
    return learning_integration.get_performance_dashboard()


def get_system_suggestions():
    """Get system improvement suggestions."""
    return learning_integration.suggest_system_improvements()


def export_learning_insights(file_path: str = None):
    """Export learning insights to file."""
    if file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"learning_insights_{timestamp}.json"

    return learning_integration.export_learning_data(file_path)


# Example of how to integrate with existing agents
async def enhance_existing_agent(agent_instance):
    """Enhance an existing agent instance with learning capabilities."""
    enhanced_agent = LearningEnabledAgent(
        agent_instance, learning_integration.learning_engine
    )
    return enhanced_agent


# Testing and demonstration
if __name__ == "__main__":
    # Example of enhancing an agent class
    from app.agent.file import FileAgent

    # Enhance the FileAgent with learning
    EnhancedFileAgent = enable_learning_for_agent(FileAgent)

    print("✅ FileAgent enhanced with learning capabilities")
    print("💡 Learning features added:")
    print("   - Task execution tracking")
    print("   - Pattern recognition")
    print("   - Performance monitoring")
    print("   - Improvement suggestions")
    print("   - Success/failure analysis")

    # Get current dashboard
    dashboard = get_learning_dashboard()
    print(f"\n📊 Learning Dashboard: {dashboard}")

    # Get system suggestions
    suggestions = get_system_suggestions()
    print(f"\n🔧 System Suggestions: {suggestions}")
