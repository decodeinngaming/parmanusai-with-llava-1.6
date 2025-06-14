from typing import Dict, List, Optional

from pydantic import Field, model_validator

from app.agent.browser import BrowserContextHelper
from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import Function, ToolCall
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.web_search import WebSearch


class Manus(ToolCallAgent):
    """A versatile general-purpose agent with support for both local and MCP tools."""

    name: str = "Manus"
    description: str = (
        "A versatile agent that can solve various tasks using multiple tools including MCP-based tools"
    )

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000
    max_steps: int = 20

    # MCP clients for remote tool access
    mcp_clients: MCPClients = Field(default_factory=MCPClients)

    # Add general-purpose tools to the tool collection
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            WebSearch(),
            StrReplaceEditor(),
            AskHuman(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])
    browser_context_helper: Optional[BrowserContextHelper] = None

    # Track connected MCP servers
    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )  # server_id -> url/command
    _initialized: bool = False

    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        """Initialize basic components synchronously."""
        self.browser_context_helper = BrowserContextHelper(self)
        return self

    @classmethod
    async def create(cls, **kwargs) -> "Manus":
        """Factory method to create and properly initialize a Manus instance."""
        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance

    async def initialize_mcp_servers(self) -> None:
        """Initialize connections to configured MCP servers."""
        for server_id, server_config in config.mcp_config.servers.items():
            try:
                if server_config.type == "sse":
                    if server_config.url:
                        await self.connect_mcp_server(server_config.url, server_id)
                        logger.info(
                            f"Connected to MCP server {server_id} at {server_config.url}"
                        )
                elif server_config.type == "stdio":
                    if server_config.command:
                        await self.connect_mcp_server(
                            server_config.command,
                            server_id,
                            use_stdio=True,
                            stdio_args=server_config.args,
                        )
                        logger.info(
                            f"Connected to MCP server {server_id} using command {server_config.command}"
                        )
            except Exception as e:
                logger.error(f"Failed to connect to MCP server {server_id}: {e}")

    async def connect_mcp_server(
        self,
        server_url: str,
        server_id: str = "",
        use_stdio: bool = False,
        stdio_args: List[str] = None,
    ) -> None:
        """Connect to an MCP server and add its tools."""
        if use_stdio:
            await self.mcp_clients.connect_stdio(
                server_url, stdio_args or [], server_id
            )
            self.connected_servers[server_id or server_url] = server_url
        else:
            await self.mcp_clients.connect_sse(server_url, server_id)
            self.connected_servers[server_id or server_url] = server_url

        # Update available tools with only the new tools from this server
        new_tools = [
            tool for tool in self.mcp_clients.tools if tool.server_id == server_id
        ]
        self.available_tools.add_tools(*new_tools)

    async def disconnect_mcp_server(self, server_id: str = "") -> None:
        """Disconnect from an MCP server and remove its tools."""
        await self.mcp_clients.disconnect(server_id)
        if server_id:
            self.connected_servers.pop(server_id, None)
        else:
            self.connected_servers.clear()

        # Rebuild available tools without the disconnected server's tools
        base_tools = [
            tool
            for tool in self.available_tools.tools
            if not isinstance(tool, MCPClientTool)
        ]
        self.available_tools = ToolCollection(*base_tools)
        self.available_tools.add_tools(*self.mcp_clients.tools)

    async def cleanup(self):
        """Clean up Manus agent resources."""
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
        # Disconnect from all MCP servers only if we were initialized
        if self._initialized:
            await self.disconnect_mcp_server()
            self._initialized = False

    async def think(self) -> bool:
        """Process current state and decide next actions with appropriate context."""
        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        # Call parent think method
        result = await super().think()

        # If LLM didn't generate tool calls but the task clearly requires action, force appropriate tool calls
        if not self.tool_calls and self._should_force_tool_call():
            logger.info(
                "🚀 No tool calls generated by LLM. Analyzing task to force appropriate tool calls..."
            )

            # Check if we already have good search results and should terminate instead
            if self._has_sufficient_search_results():
                logger.info("✅ Sufficient search results found, forcing termination")
                self.tool_calls = [self._generate_termination_call()]
                result = True
            else:
                forced_call = self._generate_forced_tool_call()
                if forced_call:
                    logger.info(f"🔧 Forcing tool call: {forced_call.function.name}")
                    self.tool_calls = [forced_call]
                    result = True

        # Restore original prompt
        self.next_step_prompt = original_prompt

        return result

    def _should_force_tool_call(self) -> bool:
        """Determine if we should force a tool call based on recent messages."""
        if not self.memory.messages:
            return False

        # Look at the last user message to understand the intent
        last_user_msg = None
        for msg in reversed(self.memory.messages):
            if msg.role == "user":
                last_user_msg = msg
                break

        if not last_user_msg:
            return False

        content = last_user_msg.content.lower()

        # Check for web search/information gathering patterns
        web_patterns = [
            "news",
            "search",
            "find",
            "look",
            "get",
            "fetch",
            "browse",
            "website",
            "internet",
            "online",
            "latest",
            "current",
            "top",
            "information",
            "data",
            "results",
            "updates",
        ]

        # Check for programming/calculation patterns
        code_patterns = [
            "calculate",
            "compute",
            "run",
            "execute",
            "python",
            "code",
            "script",
            "program",
            "analyze",
            "process",
        ]

        # Check for file patterns
        file_patterns = ["file", "write", "read", "edit", "create", "save", "open"]

        return (
            any(pattern in content for pattern in web_patterns)
            or any(pattern in content for pattern in code_patterns)
            or any(pattern in content for pattern in file_patterns)
        )

    def _generate_forced_tool_call(self) -> Optional[ToolCall]:
        """Generate an appropriate forced tool call based on the user's request."""
        if not self.memory.messages:
            return None  # Get the ORIGINAL user message, not system prompts added by the agent
        last_user_msg = None
        for msg in reversed(self.memory.messages):
            if (
                msg.role == "user"
                and not msg.content.startswith("🎯")
                and not msg.content.startswith("🔍")
                and not "IMMEDIATE ACTION REQUIRED" in msg.content
            ):
                last_user_msg = msg
                break

        if not last_user_msg:
            return None

        # Use the actual user content directly
        actual_query = last_user_msg.content.strip()
        content = actual_query.lower()

        logger.info(f"🔍 Extracted query for search: '{actual_query}'")

        # Check if web_search has already failed recently
        recent_errors = [
            msg
            for msg in self.memory.messages[-5:]
            if msg.content and "web_search" in msg.content and "Error" in msg.content
        ]
        web_search_failed = len(recent_errors) > 0

        # For web search/information gathering tasks
        if any(
            pattern in content
            for pattern in [
                "news",
                "search",
                "find",
                "look",
                "get",
                "fetch",
                "browse",
                "latest",
                "top",
                "information",
            ]
        ):
            import json

            # Extract search intent from the message
            search_query = actual_query
            if "news" in content and not any(
                specific in content.lower()
                for specific in ["artificial intelligence", "ai", "tech", "technology"]
            ):
                # Only default to generic news if it's a general news request
                search_query = "top 10 latest news today"
            elif (
                "top" in content
                and ("news" in content or "latest" in content)
                and not any(
                    specific in content.lower()
                    for specific in [
                        "artificial intelligence",
                        "ai",
                        "tech",
                        "technology",
                    ]
                )
            ):
                search_query = "top 10 latest news today"
            else:
                # Use the actual query, but clean it up
                search_query = (
                    actual_query.replace("look for", "")
                    .replace("give me", "")
                    .replace("summary", "")
                    .strip()
                )

            # For news searches, use the smart workflow system
            if "news" in content or ("top" in content and "latest" in content):
                logger.info("📰 News search detected, using smart workflow system")
                workflow_calls = self._generate_news_workflow(actual_query)
                return workflow_calls[0] if workflow_calls else None

            # Use browser_use if web_search has failed, otherwise try web_search first
            elif web_search_failed:
                logger.info(
                    "🔄 web_search failed previously, falling back to browser_use"
                )
                return ToolCall(
                    id="forced_browser_call",
                    type="function",
                    function=Function(
                        name="browser_use",
                        arguments=json.dumps(
                            {
                                "action": "web_search",
                                "query": search_query.strip(),
                                "goal": f"Search for and gather information about: {last_user_msg.content}",
                            }
                        ),
                    ),
                )
            else:
                # Prefer web_search for general search tasks
                return ToolCall(
                    id="forced_web_search_call",
                    type="function",
                    function=Function(
                        name="web_search",
                        arguments=json.dumps(
                            {"query": search_query.strip(), "num_results": 10}
                        ),
                    ),
                )

        # For calculation/programming tasks
        elif any(
            pattern in content
            for pattern in ["calculate", "compute", "python", "code", "analyze"]
        ):
            import json

            return ToolCall(
                id="forced_python_call",
                type="function",
                function=Function(
                    name="python_execute",
                    arguments=json.dumps(
                        {
                            "code": f"# Task: {last_user_msg.content}\nprint('Starting to work on your request...')"
                        }
                    ),
                ),
            )

        return None

    def _has_sufficient_search_results(self) -> bool:
        """Check if we have sufficient search results to answer the user's query."""
        if not self.memory.messages:
            return False

        # Look for recent search results with actual URLs (not just placeholders)
        recent_results = []
        for msg in self.memory.messages[-10:]:
            if msg.content and "web_search" in msg.content and "URL:" in msg.content:
                # Count URLs that are not just placeholders
                urls = [
                    line
                    for line in msg.content.split("\n")
                    if "URL:" in line and "http" in line
                ]
                recent_results.extend(urls)

        # We have sufficient results if we have at least 3 real URLs
        return len(recent_results) >= 3

    def _generate_termination_call(self) -> ToolCall:
        """Generate a termination call with a summary of what was found."""
        import json

        return ToolCall(
            id="forced_termination_call",
            type="function",
            function=Function(
                name="terminate",
                arguments=json.dumps(
                    {
                        "reason": "Search completed successfully. Found multiple relevant search results that can answer the user's query about top news."
                    }
                ),
            ),
        )

    def _generate_news_workflow(self, query: str) -> List[ToolCall]:
        """Generate a sequence of tool calls for comprehensive news gathering."""
        import json

        # Check if we've ACTUALLY navigated to a news site (look for successful browser_use outputs)
        actual_browser_navigation = [
            msg
            for msg in self.memory.messages[-10:]
            if (
                msg.role == "tool"
                and msg.content
                and ("Navigated to" in msg.content or "browser_use" in msg.content)
                and (
                    "news" in msg.content.lower() or "google.com" in msg.content.lower()
                )
            )
        ]

        # If we haven't actually navigated yet, start with navigation
        if not actual_browser_navigation:
            logger.info("🗞️ Starting news workflow: Step 1 - Navigate to news site")
            return [
                ToolCall(
                    id="news_step_1",
                    type="function",
                    function=Function(
                        name="browser_use",
                        arguments=json.dumps(
                            {
                                "action": "go_to_url",
                                "url": "https://news.google.com",
                                "goal": "Navigate to Google News homepage to access latest headlines",
                            }
                        ),
                    ),
                )
            ]

        # If we've navigated but haven't extracted content, extract headlines
        recent_extract_calls = [
            msg
            for msg in self.memory.messages[-5:]
            if (
                msg.role == "tool"
                and msg.content
                and (
                    "extract_content" in msg.content
                    or "headlines" in msg.content.lower()
                )
            )
        ]

        if not recent_extract_calls:
            logger.info("🗞️ News workflow: Step 2 - Extract headlines from news page")
            return [
                ToolCall(
                    id="news_step_2",
                    type="function",
                    function=Function(
                        name="browser_use",
                        arguments=json.dumps(
                            {
                                "action": "extract_content",
                                "goal": "Extract the top 10 news headlines and their summaries from the current news page. Focus on getting clear, readable headlines with brief descriptions.",
                            }
                        ),
                    ),
                )
            ]

        # If we've extracted content, terminate with summary
        logger.info("🗞️ News workflow: Step 3 - Complete with summary")
        return [
            ToolCall(
                id="news_step_3",
                type="function",
                function=Function(
                    name="terminate",
                    arguments=json.dumps(
                        {
                            "reason": "Successfully gathered news headlines. The browser has navigated to the news site and extracted the content. Please review the extracted headlines above for the top news stories."
                        }
                    ),
                ),
            ),
        ]
