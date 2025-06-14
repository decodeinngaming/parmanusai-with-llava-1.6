"""Agent routing system based on Parmanus's Interaction class."""

from typing import Any, Dict, List, Optional

from app.agent.base import BaseAgent
from app.agent.manus import Manus
from app.logger import logger


class AgentRouter:
    """Routes user queries to the appropriate specialized agent."""

    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        """Initialize the agent router.

        Args:
            agents: List of available agents. If None, default agents will be created.
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.current_agent: Optional[BaseAgent] = None
        self.default_agent_name = "manus"

        # Initialize default agents if none provided
        if agents is None:
            self._initialize_default_agents()
        else:
            for agent in agents:
                self.agents[agent.name.lower()] = agent

    def _initialize_default_agents(self):
        """Initialize default agents for the router."""
        # For now, we'll start with the existing Manus agent
        # Additional agents will be added as we implement them
        self.agents["manus"] = None  # Will be created when needed

    async def route(self, query: str) -> BaseAgent:
        """Route the query to the most appropriate agent.

        Args:
            query: The user query to analyze and route.

        Returns:
            The selected agent for handling the query.
        """
        # Analyze query to determine best agent
        agent_name = await self._analyze_query(query)

        # Get or create the selected agent
        if agent_name not in self.agents or self.agents[agent_name] is None:
            self.agents[agent_name] = await self._create_agent(agent_name)

        # If switching agents or reusing the same agent, ensure proper state reset
        selected_agent = self.agents[agent_name]

        # Reset agent state for new task to prevent context overflow
        if self.current_agent != selected_agent or (
            hasattr(selected_agent, "memory")
            and hasattr(selected_agent.memory, "get_memory_size")
            and selected_agent.memory.get_memory_size()["total_messages"] > 0
        ):

            logger.info(
                f"Resetting agent state for new task (switching from {self.current_agent.name if self.current_agent else 'None'} to {agent_name})"
            )

            # Trigger agent state reset
            if hasattr(selected_agent, "reset_state"):
                await selected_agent.reset_state()
            elif hasattr(selected_agent, "_reset_state"):
                selected_agent._reset_state()

        self.current_agent = selected_agent
        logger.info(f"Routed query to {agent_name} agent")
        return self.current_agent

    async def _analyze_query(self, query: str) -> str:
        """Analyze the query to determine the best agent.

        Args:
            query: The user query to analyze.

        Returns:
            The name of the best agent for this query.
        """
        query_lower = query.lower()

        # Log the query for debugging
        logger.info(f"Analyzing query for routing: {query}")

        # Check for mixed requests first: analyze website + create webpage
        mixed_creation_patterns = [
            "look at google and build",
            "visit google and create",
            "go to google and make",
            "check google and build",
            "analyze google and create",
            "study google and build",
            "examine google and make",
            "look at facebook and build",
            "look at amazon and build",
            "look at twitter and build",
            "look at youtube and build",
            "look at linkedin and build",
            "look at instagram and build",
            "mimic",
            "copy the design",
            "similar to",
            "inspired by",
            "like google but",
            "like facebook but",
            "style of google",
            "design of facebook",
        ]

        has_mixed_pattern = any(
            pattern in query_lower for pattern in mixed_creation_patterns
        )
        has_look_and_build = (
            "look at" in query_lower
            and "build" in query_lower
            and ("webpage" in query_lower or "page" in query_lower)
        )
        has_look_and_create = (
            "look at" in query_lower
            and "create" in query_lower
            and ("webpage" in query_lower or "page" in query_lower)
        )
        has_website_analysis = any(
            site in query_lower
            for site in [
                "google.com",
                "facebook.com",
                "amazon.com",
                "twitter.com",
                "youtube.com",
                "linkedin.com",
                "instagram.com",
                "github.com",
                "stackoverflow.com",
                "reddit.com",
            ]
        )

        # Enhanced detection for website mimicking/analysis requests
        has_design_mimicking = any(
            word in query_lower
            for word in [
                "mimic",
                "copy",
                "similar",
                "inspired",
                "like",
                "style",
                "design",
            ]
        ) and any(
            word in query_lower for word in ["webpage", "page", "website", "site"]
        )

        if (
            has_mixed_pattern
            or has_look_and_build
            or has_look_and_create
            or has_website_analysis
            or has_design_mimicking
        ):
            # These requests need to create files, so route to file agent which can delegate to browser
            logger.info(
                "Routing to file agent for mixed request (analyze site + create webpage)"
            )
            return "file"

        # Check for browser navigation + file creation tasks
        browser_navigation_keywords = [
            "go to",
            "visit",
            "navigate to",
            "open",
            "browse to",
            "look at",
            "check out",
        ]

        # If it's a navigation task that also involves creation, route to browser
        if any(
            nav_keyword in query_lower for nav_keyword in browser_navigation_keywords
        ):
            # Check for website patterns
            import re

            website_patterns = [
                r"\b\w+\.com\b",
                r"\b\w+\.org\b",
                r"\b\w+\.net\b",
                r"facebook",
                r"google",
                r"twitter",
                r"youtube",
            ]
            if any(re.search(pattern, query_lower) for pattern in website_patterns):
                logger.info(
                    "Routing to browser agent based on navigation + website keywords"
                )
                return "browser"

        # File creation keywords (check after browser navigation)
        file_creation_keywords = [
            "create",
            "make",
            "build",
            "generate",
            "write to file",
            "save to file",
            "html file",
            "webpage file",
            "create webpage",
            "create html",
            "build webpage",
            "make webpage",
        ]

        # Check for file creation patterns (only if not a navigation task)
        if any(keyword in query_lower for keyword in file_creation_keywords):
            # Check if it's specifically about creating files (and not navigating to websites)
            if any(
                file_word in query_lower
                for file_word in ["file", "save", "create", "write", "make", "build"]
            ) and not any(
                nav_keyword in query_lower
                for nav_keyword in browser_navigation_keywords
            ):
                logger.info("Routing to file agent based on file creation keywords")
                return "file"

        # Browser-related queries (for browsing, searching, navigating)
        browser_keywords = [
            "browse",
            "website",
            "web",
            "www",
            "http",
            "url",
            "search",
            "click",
            "navigate",
            "download",
            "scrape",
            "form",
            "button",
            "rate",
            "feedback",
            "visit",
            "page",
            "go to",
        ]

        # Check for common website patterns
        import re

        domain_patterns = [
            r"\b\w+\.com\b",  # anything.com
            r"\b\w+\.org\b",  # anything.org
            r"\b\w+\.net\b",  # anything.net
            r"\b\w+\.edu\b",  # anything.edu
            r"\b\w+\.gov\b",  # anything.gov
            r"\bwww\.\w+",  # www.anything
            r"https?://",  # http:// or https://
        ]

        # Check for browser keywords or domain patterns
        if any(keyword in query_lower for keyword in browser_keywords) or any(
            re.search(pattern, query_lower) for pattern in domain_patterns
        ):
            logger.info("Routing to browser agent based on web keywords")
            return "browser"

        # Code-related queries
        if any(
            keyword in query_lower
            for keyword in [
                "code",
                "program",
                "script",
                "function",
                "debug",
                "compile",
                "execute",
                "python",
                "javascript",
                "java",
                "c++",
                "go",
                "rust",
            ]
        ):
            logger.info("Routing to code agent based on programming keywords")
            return "code"

        # File-related queries
        if any(
            keyword in query_lower
            for keyword in [
                "file",
                "folder",
                "directory",
                "save",
                "read",
                "write",
                "delete",
                "copy",
                "move",
                "create",
                "edit",
            ]
        ):
            logger.info("Routing to file agent based on file keywords")
            return "file"

        # Planning-related queries
        if any(
            keyword in query_lower
            for keyword in [
                "plan",
                "task",
                "step",
                "organize",
                "schedule",
                "workflow",
                "project",
                "break down",
                "strategy",
            ]
        ):
            logger.info("Routing to planner agent based on planning keywords")
            return "planner"

        # Default to manus agent for general queries
        logger.info("Routing to default manus agent")
        return self.default_agent_name

    async def _create_agent(self, agent_name: str) -> BaseAgent:
        """Create an agent instance by name.

        Args:
            agent_name: The name of the agent to create.

        Returns:
            The created agent instance.
        """
        if agent_name == "manus":
            return await Manus.create()
        elif agent_name == "code":
            # Will be implemented when CodeAgent is created
            from app.agent.code import CodeAgent

            return await CodeAgent.create()
        elif agent_name == "browser":
            # Will be implemented when BrowserAgent is created
            from app.agent.browser import BrowserAgent

            return await BrowserAgent.create()
        elif agent_name == "file":
            # Will be implemented when FileAgent is created
            from app.agent.file import FileAgent

            return await FileAgent.create()
        elif agent_name == "planner":
            # Will be implemented when PlannerAgent is created
            from app.agent.planner import PlannerAgent

            return await PlannerAgent.create()
        else:
            # Fallback to manus agent
            logger.warning(f"Unknown agent type: {agent_name}, falling back to manus")
            return await Manus.create()

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names.

        Returns:
            List of agent names that can be routed to.
        """
        return ["manus", "code", "browser", "file", "planner"]

    def get_current_agent(self) -> Optional[BaseAgent]:
        """Get the currently active agent.

        Returns:
            The current agent or None if no agent is active.
        """
        return self.current_agent
