"""
Quick Integration Guide for ParManusAI Self-Learning System

This script shows how to easily integrate the self-learning capabilities
into the main ParManusAI application.
"""

from app.learning import (
    LearningRouter,
    enable_learning_for_agent,
    export_learning_insights,
    get_learning_dashboard,
    setup_learning_for_parmanusai,
)


def integrate_learning_into_main_app():
    """
    Main integration function to enable learning in ParManusAI.
    Call this function at application startup.
    """
    print("🧠 Integrating Self-Learning into ParManusAI...")

    # Step 1: Setup learning system
    learning_components = setup_learning_for_parmanusai()

    # Step 2: Replace the default router with learning router
    learning_router = LearningRouter()

    print("✅ Learning system integrated successfully!")
    print("\n📋 Available Learning Features:")
    print("   • Task execution tracking and analysis")
    print("   • Pattern recognition from success/failure")
    print("   • Performance monitoring and optimization")
    print("   • Self-improvement suggestions")
    print("   • Learning-based agent routing")
    print("   • Continuous learning cycles")

    return {
        "learning_engine": learning_components["learning_engine"],
        "router": learning_router,
        "config": learning_components["config"],
    }


def enhance_existing_agents():
    """
    Enhance existing agent classes with learning capabilities.
    """
    print("\n🔧 Enhancing existing agents with learning...")

    # Enhance File Agent
    from app.agent.file import FileAgent

    LearningFileAgent = enable_learning_for_agent(FileAgent)
    print("✅ FileAgent enhanced with learning")

    # Enhance Browser Agent (if available)
    try:
        from app.agent.browser import BrowserAgent

        LearningBrowserAgent = enable_learning_for_agent(BrowserAgent)
        print("✅ BrowserAgent enhanced with learning")
    except ImportError:
        print("⚠️ BrowserAgent not available for enhancement")

    # Enhance Code Agent (if available)
    try:
        from app.agent.code import CodeAgent

        LearningCodeAgent = enable_learning_for_agent(CodeAgent)
        print("✅ CodeAgent enhanced with learning")
    except ImportError:
        print("⚠️ CodeAgent not available for enhancement")

    return {
        "file_agent": LearningFileAgent,
        "browser_agent": (
            LearningBrowserAgent if "LearningBrowserAgent" in locals() else None
        ),
        "code_agent": LearningCodeAgent if "LearningCodeAgent" in locals() else None,
    }


async def demo_learning_features():
    """
    Demonstrate the learning features with sample tasks.
    """
    print("\n🎮 Demonstrating Learning Features...")

    # Create learning router
    router = LearningRouter()

    # Test routing with learning
    test_queries = [
        "Create a modern website about space exploration",
        "Search for the latest Python frameworks",
        "Generate CSS for a responsive navigation bar",
    ]

    for query in test_queries:
        try:
            agent_name = await router.route(query)
            print(f"🔀 '{query}' → {agent_name} agent")
        except Exception as e:
            print(f"❌ Error routing '{query}': {e}")

    # Get learning insights
    insights = router.get_routing_insights()
    print(
        f"\n📊 Routing Performance: {insights.get('overall_routing_success_rate', 0):.1%} success rate"
    )

    # Get system dashboard
    dashboard = get_learning_dashboard()
    if dashboard.get("insights"):
        success_rate = dashboard["insights"].get("overall_success_rate", 0)
        print(f"📈 Overall System Performance: {success_rate:.1%} success rate")


def setup_learning_monitoring():
    """
    Setup learning monitoring and reporting.
    """
    print("\n📊 Setting up Learning Monitoring...")

    # Export current learning data
    report_file = export_learning_insights()
    print(f"📄 Learning insights exported to: {report_file}")

    # Setup periodic reporting (in a real application)
    print("⏰ Consider setting up periodic learning reports")
    print("💡 Use get_learning_dashboard() for real-time insights")
    print("🔧 Use get_system_suggestions() for improvement recommendations")


def main():
    """
    Main integration function - call this to fully enable learning.
    """
    print("🚀 ParManusAI Self-Learning Integration Started")
    print("=" * 50)

    # Step 1: Integrate learning system
    learning_system = integrate_learning_into_main_app()

    # Step 2: Enhance existing agents
    enhanced_agents = enhance_existing_agents()

    # Step 3: Setup monitoring
    setup_learning_monitoring()

    print("\n🎉 Self-Learning Integration Complete!")
    print("\n📋 Integration Summary:")
    print(f"   ✅ Learning Engine: {learning_system['learning_engine'] is not None}")
    print(f"   ✅ Learning Router: {learning_system['router'] is not None}")
    print(
        f"   ✅ Enhanced Agents: {sum(1 for agent in enhanced_agents.values() if agent is not None)}"
    )
    print(f"   ✅ Monitoring Setup: True")

    print("\n🔗 To use in your application:")
    print("   1. Call integrate_learning_into_main_app() at startup")
    print("   2. Replace your router with the returned learning_router")
    print("   3. Use enhanced agent classes instead of original ones")
    print("   4. Monitor performance with get_learning_dashboard()")

    return {
        "learning_system": learning_system,
        "enhanced_agents": enhanced_agents,
        "status": "integrated",
    }


# Example integration into main.py
def integrate_into_main_py():
    """
    Example of how to integrate learning into the main ParManusAI application.
    """
    integration_code = """
# Add to main.py imports:
from app.learning import setup_learning_for_parmanusai, LearningRouter

# Add to main() function:
def main():
    # Setup learning system
    learning_system = setup_learning_for_parmanusai()

    # Use learning router instead of regular router
    router = LearningRouter()

    # Your existing main application logic here...
    # The agents will now automatically learn from their interactions!

    return router

# Example usage in your agent creation:
from app.learning import enable_learning_for_agent
from app.agent.file import FileAgent

# Create learning-enabled file agent
LearningFileAgent = enable_learning_for_agent(FileAgent)
file_agent = await LearningFileAgent.create()

# The agent now tracks performance and learns from experience!
"""

    print("\n📝 Integration Code Example:")
    print(integration_code)


if __name__ == "__main__":
    import asyncio

    # Run the integration
    result = main()

    # Run the demo
    print("\n" + "=" * 50)
    asyncio.run(demo_learning_features())

    # Show integration example
    integrate_into_main_py()

    print("\n🎯 Self-Learning Integration Guide Complete!")
    print(
        "The ParManusAI system is now ready for intelligent, self-improving operation!"
    )
