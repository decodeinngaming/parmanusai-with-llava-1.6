"""
Learning-enhanced router that applies self-learning capabilities to the agent selection process.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.agent.router import AgentRouter
from app.learning.self_learning import SelfLearningEngine, LearningRecord


class LearningRouter(AgentRouter):
    """Router enhanced with learning capabilities for better agent selection."""
      def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learning_engine = SelfLearningEngine()
        self.routing_history = []
    
    async def route(self, query: str) -> str:
        """Enhanced routing with learning-based optimization."""
        start_time = time.time()
        
        user_request = query
        
        # Get learning suggestions for agent selection
        suggestions = self.learning_engine.get_improvement_suggestions(
            user_request,
            {"task_type": "routing"}
        )
        
        if suggestions:
            print(f"🧠 Routing insight: {suggestions[0]}")
        
        try:
            # Use original routing logic
            selected_agent = await super().route(query)
            
            # Record successful routing
            execution_time = time.time() - start_time
            self._record_routing_success(user_request, selected_agent.name, execution_time)
            
            return selected_agent.name
            
        except Exception as e:
            # Record routing failure
            execution_time = time.time() - start_time
            self._record_routing_failure(user_request, str(e), execution_time)
            raise
    
    def _record_routing_success(self, user_request: str, selected_agent: str, execution_time: float):
        """Record successful agent routing."""
        record = LearningRecord(
            task_id=f"routing_{int(time.time())}",
            user_request=user_request,
            agent_used=f"router_to_{selected_agent}",
            success=True,
            execution_time=execution_time,
            error_message=None,
            user_feedback_score=None,
            timestamp=datetime.now(),
            context={
                "selected_agent": selected_agent,
                "routing_type": "automatic",
                "request_complexity": self._assess_request_complexity(user_request)
            }
        )
        
        self.learning_engine.record_task_execution(record)
        self.routing_history.append({
            "request": user_request,
            "agent": selected_agent,
            "success": True,
            "timestamp": datetime.now()
        })
    
    def _record_routing_failure(self, user_request: str, error: str, execution_time: float):
        """Record failed agent routing."""
        record = LearningRecord(
            task_id=f"routing_fail_{int(time.time())}",
            user_request=user_request,
            agent_used="router",
            success=False,
            execution_time=execution_time,
            error_message=error,
            user_feedback_score=None,
            timestamp=datetime.now(),
            context={
                "routing_type": "failed",
                "request_complexity": self._assess_request_complexity(user_request)
            }
        )
        
        self.learning_engine.record_task_execution(record)
    
    def _assess_request_complexity(self, user_request: str) -> str:
        """Assess the complexity of a user request."""
        request_lower = user_request.lower()
        
        # Count complexity indicators
        complex_words = ["search and create", "analyze and generate", "multiple", "complex", "advanced"]
        complexity_score = sum(1 for word in complex_words if word in request_lower)
        
        if complexity_score >= 2:
            return "high"
        elif complexity_score == 1:
            return "medium"
        else:
            return "low"
    
    def get_routing_insights(self) -> Dict[str, Any]:
        """Get insights about routing performance."""
        if not self.routing_history:
            return {"message": "No routing history available"}
        
        # Analyze routing patterns
        agent_usage = {}
        success_rate = sum(1 for r in self.routing_history if r["success"]) / len(self.routing_history)
        
        for record in self.routing_history:
            agent = record["agent"]
            if agent not in agent_usage:
                agent_usage[agent] = {"total": 0, "successful": 0}
            
            agent_usage[agent]["total"] += 1
            if record["success"]:
                agent_usage[agent]["successful"] += 1
        
        # Calculate success rates per agent
        for agent, stats in agent_usage.items():
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0
        
        return {
            "overall_routing_success_rate": success_rate,
            "total_routings": len(self.routing_history),
            "agent_usage": agent_usage,
            "learning_patterns": len(self.learning_engine.improvement_patterns),
            "last_updated": datetime.now().isoformat()
        }
    
    def suggest_routing_improvements(self) -> List[str]:
        """Suggest improvements to the routing logic."""
        insights = self.get_routing_insights()
        suggestions = []
        
        # Analyze agent performance
        if "agent_usage" in insights:
            for agent, stats in insights["agent_usage"].items():
                if stats["success_rate"] < 0.7 and stats["total"] > 3:
                    suggestions.append(f"Review routing conditions for {agent} agent - low success rate")
                elif stats["success_rate"] > 0.95 and stats["total"] > 5:
                    suggestions.append(f"{agent} agent performs excellently - consider expanding its use cases")
        
        # Overall routing suggestions
        if insights.get("overall_routing_success_rate", 1.0) < 0.8:
            suggestions.extend([
                "Improve routing logic with more specific condition matching",
                "Add fallback routing strategies for ambiguous requests",
                "Consider request preprocessing for better agent selection"
            ])
        
        return suggestions


# Enhanced agent factory with learning
class LearningAgentFactory:
    """Factory for creating learning-enabled agents."""
    
    def __init__(self):
        self.learning_engine = SelfLearningEngine()
        self.created_agents = {}
    
    async def create_agent(self, agent_type: str, **kwargs):
        """Create an agent with learning capabilities."""
        from app.learning.integration import enable_learning_for_agent
        
        # Import the original agent class
        if agent_type == "file":
            from app.agent.file import FileAgent
            EnhancedAgent = enable_learning_for_agent(FileAgent)
        elif agent_type == "browser":
            from app.agent.browser import BrowserAgent
            EnhancedAgent = enable_learning_for_agent(BrowserAgent)
        elif agent_type == "code":
            from app.agent.code import CodeAgent
            EnhancedAgent = enable_learning_for_agent(CodeAgent)
        elif agent_type == "planner":
            from app.agent.planner import PlannerAgent
            EnhancedAgent = enable_learning_for_agent(PlannerAgent)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Create the enhanced agent
        agent = await EnhancedAgent.create(**kwargs)
        
        # Track creation
        self.created_agents[agent_type] = {
            "created_at": datetime.now(),
            "kwargs": kwargs
        }
        
        return agent
    
    def get_agent_creation_stats(self) -> Dict[str, Any]:
        """Get statistics about agent creation."""
        return {
            "total_agents_created": len(self.created_agents),
            "agent_types": list(self.created_agents.keys()),
            "creation_history": self.created_agents,
            "last_updated": datetime.now().isoformat()
        }


# Testing and demonstration
async def test_learning_router():
    """Test the learning-enhanced router."""
    from app.schema import Message
    
    router = LearningRouter()
    
    # Test routing with various requests
    test_requests = [
        "Create a webpage about AI",
        "Search for information about Python",
        "Generate CSS for buttons",
        "Analyze this code for errors"
    ]
    
    for request in test_requests:
        messages = [Message(role="user", content=request)]
        try:
            selected_agent = await router.route(messages)
            print(f"✅ Request: '{request}' -> Agent: {selected_agent}")
        except Exception as e:
            print(f"❌ Request: '{request}' -> Error: {e}")
    
    # Get insights
    insights = router.get_routing_insights()
    print(f"\n📊 Routing Insights: {insights}")
    
    # Get suggestions
    suggestions = router.suggest_routing_improvements()
    print(f"\n💡 Routing Suggestions: {suggestions}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_learning_router())
