import asyncio
import base64
import json
import re
from typing import Dict, Generic, List, Optional, TypeVar

from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from browser_use.dom.service import DomService
from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.config import config
from app.llm import LLM
from app.logger import logger
from app.tool.base import BaseTool, ToolResult
from app.tool.web_search import WebSearch

_BROWSER_DESCRIPTION = """\
A powerful browser automation tool that allows interaction with web pages through various actions.
* This tool provides commands for controlling a browser session, navigating web pages, and extracting information
* It maintains state across calls, keeping the browser session alive until explicitly closed
* Use this when you need to browse websites, fill forms, click buttons, extract content, or perform web searches
* Each action requires specific parameters as defined in the tool's dependencies

Key capabilities include:
* Navigation: Go to specific URLs, go back, search the web, or refresh pages
* Interaction: Click elements, input text, select from dropdowns, send keyboard commands
* Scrolling: Scroll up/down by pixel amount or scroll to specific text
* Content extraction: Extract and analyze content from web pages based on specific goals
* Tab management: Switch between tabs, open new tabs, or close tabs

Note: When using element indices, refer to the numbered elements shown in the current browser state.
"""

Context = TypeVar("Context")


# Track selector usage to prevent hallucination loops
class SelectorTracker:
    def __init__(self, max_retries: int = 3):
        self.selector_counts: Dict[str, int] = {}
        self.max_retries = max_retries
        self.recent_selectors: List[str] = []
        self.max_recent = 10

    def track_selector(self, selector: str) -> bool:
        """
        Track a selector usage and determine if it's being used too many times
        Returns True if the selector should be allowed, False if it's being used too much
        """
        # Add to recent selectors list
        self.recent_selectors.append(selector)
        if len(self.recent_selectors) > self.max_recent:
            self.recent_selectors.pop(0)

        # Check for repetitive pattern
        if len(self.recent_selectors) >= 3:
            last_three = self.recent_selectors[-3:]
            if len(set(last_three)) == 1:  # All three are the same
                return False

        # Track individual selector usage
        if selector in self.selector_counts:
            self.selector_counts[selector] += 1
        else:
            self.selector_counts[selector] = 1

        return self.selector_counts[selector] <= self.max_retries

    def is_valid_selector(self, selector: str) -> bool:
        """
        Validate if a selector is properly formatted
        """
        # Basic validation for CSS selectors
        if not selector or not isinstance(selector, str):
            return False

        # Check for common hallucinated patterns (random strings of letters/numbers)
        if re.match(r"^\.?[a-z0-9]{10,}$", selector):
            return False

        # Check for obviously invalid selectors
        invalid_patterns = [
            r"\.rhp\d+[a-z]+",  # Matches patterns like .rhp90mdlnikmevrp
            r"\.random",
            r"\.undefined",
            r"\.null",
        ]

        for pattern in invalid_patterns:
            if re.match(pattern, selector):
                return False

        return True


class BrowserUseTool(BaseTool, Generic[Context]):
    name: str = "browser_use"
    description: str = _BROWSER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "go_to_url",
                    "click_element",
                    "input_text",
                    "scroll_down",
                    "scroll_up",
                    "scroll_to_text",
                    "send_keys",
                    "get_dropdown_options",
                    "select_dropdown_option",
                    "go_back",
                    "web_search",
                    "wait",
                    "extract_content",
                    "switch_tab",
                    "open_tab",
                    "close_tab",
                ],
                "description": "The browser action to perform",
            },
            "url": {
                "type": "string",
                "description": "URL for 'go_to_url' or 'open_tab' actions",
            },
            "index": {
                "type": "integer",
                "description": "Element index for 'click_element', 'input_text', 'get_dropdown_options', or 'select_dropdown_option' actions",
            },
            "text": {
                "type": "string",
                "description": "Text for 'input_text', 'scroll_to_text', or 'select_dropdown_option' actions",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Pixels to scroll (positive for down, negative for up) for 'scroll_down' or 'scroll_up' actions",
            },
            "tab_id": {
                "type": "integer",
                "description": "Tab ID for 'switch_tab' action",
            },
            "query": {
                "type": "string",
                "description": "Search query for 'web_search' action",
            },
            "goal": {
                "type": "string",
                "description": "Extraction goal for 'extract_content' action",
            },
            "keys": {
                "type": "string",
                "description": "Keys to send for 'send_keys' action",
            },
            "seconds": {
                "type": "integer",
                "description": "Seconds to wait for 'wait' action",
            },
            "selector": {
                "type": "string",
                "description": "CSS selector for element targeting (optional, use with caution)",
            },
        },
        "required": ["action"],
        "dependencies": {
            "go_to_url": ["url"],
            "click_element": ["index"],
            "input_text": ["index", "text"],
            "switch_tab": ["tab_id"],
            "open_tab": ["url"],
            "scroll_down": ["scroll_amount"],
            "scroll_up": ["scroll_amount"],
            "scroll_to_text": ["text"],
            "send_keys": ["keys"],
            "get_dropdown_options": ["index"],
            "select_dropdown_option": ["index", "text"],
            "go_back": [],
            "web_search": ["query"],
            "wait": ["seconds"],
            "extract_content": ["goal"],
        },
    }

    lock: asyncio.Lock = Field(default_factory=asyncio.Lock)
    browser: Optional[BrowserUseBrowser] = Field(default=None, exclude=True)
    context: Optional[BrowserContext] = Field(default=None, exclude=True)
    dom_service: Optional[DomService] = Field(default=None, exclude=True)
    web_search_tool: WebSearch = Field(default_factory=WebSearch, exclude=True)

    # Add selector tracker to prevent hallucination loops
    selector_tracker: SelectorTracker = Field(
        default_factory=SelectorTracker, exclude=True
    )

    # Context for generic functionality
    tool_context: Optional[Context] = Field(default=None, exclude=True)

    llm: Optional[LLM] = Field(default_factory=LLM)

    @field_validator("parameters", mode="before")
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        if not v:
            raise ValueError("Parameters cannot be empty")
        return v

    async def _ensure_browser_initialized(self) -> BrowserContext:
        """Ensure browser and context are initialized."""
        if self.browser is None:
            browser_config_kwargs = {"headless": False, "disable_security": True}

            if config.browser:
                from browser_use.browser.browser import ProxySettings

                # handle proxy settings.
                if config.browser.proxy and config.browser.proxy.server:
                    browser_config_kwargs["proxy"] = ProxySettings(
                        server=config.browser.proxy.server,
                        username=config.browser.proxy.username,
                        password=config.browser.proxy.password,
                    )

                browser_attrs = [
                    "headless",
                    "disable_security",
                    "extra_chromium_args",
                    "chrome_instance_path",
                    "wss_url",
                    "cdp_url",
                ]

                for attr in browser_attrs:
                    value = getattr(config.browser, attr, None)
                    if value is not None:
                        if not isinstance(value, list) or value:
                            browser_config_kwargs[attr] = value

            self.browser = BrowserUseBrowser(BrowserConfig(**browser_config_kwargs))

        if self.context is None:
            context_config = BrowserContextConfig()

            # if there is context config in the config, use it.
            if (
                config.browser
                and hasattr(config.browser, "new_context_config")
                and config.browser.new_context_config
            ):
                context_config = config.browser.new_context_config

            self.context = await self.browser.new_context(context_config)
            self.dom_service = DomService(await self.context.get_current_page())

            # Set viewport size for browser window if available in config
            if hasattr(config.browser, "window_width") and hasattr(
                config.browser, "window_height"
            ):
                try:
                    await self.context.set_viewport_size(
                        {
                            "width": config.browser.window_width,
                            "height": config.browser.window_height,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not set browser viewport size: {e}")

        return self.context

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        query: Optional[str] = None,
        goal: Optional[str] = None,
        keys: Optional[str] = None,
        seconds: Optional[int] = None,
        selector: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute a specified browser action.

        Args:
            action: The browser action to perform
            url: URL for navigation or new tab
            index: Element index for click or input actions
            text: Text for input action or search query
            scroll_amount: Pixels to scroll for scroll action
            tab_id: Tab ID for switch_tab action
            query: Search query for Google search
            goal: Extraction goal for content extraction
            keys: Keys to send for keyboard actions
            seconds: Seconds to wait
            selector: CSS selector (optional)
            **kwargs: Additional arguments

        Returns:
            ToolResult with the action's output or error
        """
        async with self.lock:
            try:
                # Validate selector if provided to prevent hallucination loops
                if selector:
                    if not self.selector_tracker.is_valid_selector(selector):
                        return ToolResult(
                            error=f"Invalid selector format: '{selector}'. Please use valid CSS selectors."
                        )

                    if not self.selector_tracker.track_selector(selector):
                        return ToolResult(
                            error=f"Selector '{selector}' has been used too many times. Please try a different approach."
                        )

                context = await self._ensure_browser_initialized()

                # Get max content length from config
                max_content_length = getattr(config.browser, "max_content_length", 2000)

                # Navigation actions
                if action == "go_to_url":
                    if not url:
                        return ToolResult(
                            error="URL is required for 'go_to_url' action"
                        )
                    page = await context.get_current_page()
                    await page.goto(url)
                    await page.wait_for_load_state()
                    return ToolResult(output=f"Navigated to {url}")

                elif action == "go_back":
                    await context.go_back()
                    return ToolResult(output="Navigated back")

                elif action == "refresh":
                    await context.refresh_page()
                    return ToolResult(output="Refreshed current page")

                elif action == "web_search":
                    if not query:
                        return ToolResult(
                            error="Query is required for 'web_search' action"
                        )

                    # Debug logging for the query
                    logger.info(
                        f"🔍 Browser web_search action called with query: {repr(query)}"
                    )

                    try:
                        # Execute the web search and return results directly without browser navigation
                        search_response = await self.web_search_tool.execute(
                            query=query, fetch_content=True, num_results=3
                        )

                        if not search_response.results:
                            # If no search results, try navigating to a known AI news site directly
                            logger.warning(
                                "No search results found, trying direct navigation to AI news sites"
                            )

                            # Try well-known AI news sites
                            ai_news_sites = [
                                "https://venturebeat.com/ai/",
                                "https://techcrunch.com/category/artificial-intelligence/",
                                "https://www.theverge.com/ai-artificial-intelligence",
                            ]

                            page = await context.get_current_page()
                            for site in ai_news_sites:
                                try:
                                    await page.goto(site, timeout=10000)
                                    # Extract content from the page
                                    await page.wait_for_load_state("load", timeout=5000)
                                    content = await page.content()

                                    if (
                                        content and len(content) > 1000
                                    ):  # Basic check for loaded content
                                        logger.info(f"Successfully navigated to {site}")
                                        return ToolResult(
                                            output=f"Successfully navigated to AI news site: {site}"
                                        )
                                except Exception as e:
                                    logger.warning(f"Failed to navigate to {site}: {e}")
                                    continue

                            return ToolResult(
                                error="No search results found and failed to navigate to AI news sites directly"
                            )

                        # Navigate to the first search result
                        first_search_result = search_response.results[0]
                        url_to_navigate = first_search_result.url

                        # Debug logging for the URL
                        logger.info(
                            f"🔍 Attempting to navigate to URL: {repr(url_to_navigate)}"
                        )

                        # Validate URL before navigation
                        if not url_to_navigate or not url_to_navigate.startswith(
                            ("http://", "https://")
                        ):
                            logger.warning(
                                f"Invalid URL received: {url_to_navigate}, returning search results instead"
                            )
                            return ToolResult(
                                output=f"Search results for '{query}':\n\n{search_response.output}"
                            )

                        page = await context.get_current_page()
                        await page.goto(url_to_navigate, timeout=15000)
                        await page.wait_for_load_state("load", timeout=10000)

                        logger.info(f"Successfully navigated to: {url_to_navigate}")
                        return search_response

                    except Exception as e:
                        logger.error(f"Web search failed with error: {e}")

                        # Fallback: try to navigate directly to AI news sites
                        logger.info(
                            "Attempting fallback to direct AI news site navigation"
                        )

                        # Extract AI-related keywords from query
                        ai_keywords = [
                            "artificial intelligence",
                            "ai",
                            "machine learning",
                            "tech",
                            "technology",
                        ]
                        query_lower = query.lower()

                        if any(keyword in query_lower for keyword in ai_keywords):
                            # Try AI news sites
                            fallback_sites = [
                                "https://venturebeat.com/ai/",
                                "https://techcrunch.com/category/artificial-intelligence/",
                                "https://www.theverge.com/ai-artificial-intelligence",
                            ]
                        else:
                            # Try general news sites
                            fallback_sites = [
                                "https://news.google.com",
                                "https://www.bbc.com/news",
                                "https://www.cnn.com",
                            ]

                        page = await context.get_current_page()
                        for site in fallback_sites:
                            try:
                                await page.goto(site, timeout=10000)
                                await page.wait_for_load_state("load", timeout=5000)
                                logger.info(
                                    f"Fallback navigation successful to: {site}"
                                )
                                return ToolResult(
                                    output=f"Search failed, but successfully navigated to news site: {site}"
                                )
                            except Exception as fallback_error:
                                logger.warning(
                                    f"Fallback navigation failed for {site}: {fallback_error}"
                                )
                                continue

                        return ToolResult(
                            error=f"Web search failed and all fallback navigation attempts failed. Original error: {str(e)}"
                        )

                # Element interaction actions
                elif action == "click_element":
                    if index is None:
                        return ToolResult(
                            error="Index is required for 'click_element' action"
                        )
                    element = await context.get_dom_element_by_index(index)
                    if not element:
                        return ToolResult(error=f"Element with index {index} not found")
                    download_path = await context._click_element_node(element)
                    output = f"Clicked element at index {index}"
                    if download_path:
                        output += f" - Downloaded file to {download_path}"
                    return ToolResult(output=output)

                elif action == "input_text":
                    if index is None or not text:
                        return ToolResult(
                            error="Index and text are required for 'input_text' action"
                        )
                    element = await context.get_dom_element_by_index(index)
                    if not element:
                        return ToolResult(error=f"Element with index {index} not found")
                    await context._input_text_element_node(element, text)
                    return ToolResult(
                        output=f"Input '{text}' into element at index {index}"
                    )

                elif action == "scroll_down" or action == "scroll_up":
                    direction = 1 if action == "scroll_down" else -1
                    amount = (
                        scroll_amount
                        if scroll_amount is not None
                        else context.config.browser_window_size["height"]
                    )
                    await context.execute_javascript(
                        f"window.scrollBy(0, {direction * amount});"
                    )
                    return ToolResult(
                        output=f"Scrolled {'down' if direction > 0 else 'up'} by {amount} pixels"
                    )

                elif action == "scroll_to_text":
                    if not text:
                        return ToolResult(
                            error="Text is required for 'scroll_to_text' action"
                        )
                    page = await context.get_current_page()
                    try:
                        locator = page.get_by_text(text, exact=False)
                        await locator.scroll_into_view_if_needed()
                        return ToolResult(output=f"Scrolled to text: '{text}'")
                    except Exception as e:
                        return ToolResult(error=f"Failed to scroll to text: {str(e)}")

                elif action == "send_keys":
                    if not keys:
                        return ToolResult(
                            error="Keys are required for 'send_keys' action"
                        )
                    page = await context.get_current_page()
                    await page.keyboard.press(keys)
                    return ToolResult(output=f"Sent keys: {keys}")

                elif action == "get_dropdown_options":
                    if index is None:
                        return ToolResult(
                            error="Index is required for 'get_dropdown_options' action"
                        )
                    element = await context.get_dom_element_by_index(index)
                    if not element:
                        return ToolResult(error=f"Element with index {index} not found")
                    page = await context.get_current_page()
                    options = await page.evaluate(
                        """
                        (xpath) => {
                            const select = document.evaluate(xpath, document, null,
                                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                            if (!select) return null;
                            return Array.from(select.options).map(opt => ({
                                text: opt.text,
                                value: opt.value,
                                index: opt.index
                            }));
                        }
                    """,
                        element.xpath,
                    )
                    return ToolResult(output=f"Dropdown options: {options}")

                elif action == "select_dropdown_option":
                    if index is None or not text:
                        return ToolResult(
                            error="Index and text are required for 'select_dropdown_option' action"
                        )
                    element = await context.get_dom_element_by_index(index)
                    if not element:
                        return ToolResult(error=f"Element with index {index} not found")
                    page = await context.get_current_page()
                    await page.select_option(element.xpath, label=text)
                    return ToolResult(
                        output=f"Selected option '{text}' from dropdown at index {index}"
                    )

                # Content extraction actions
                elif action == "extract_content":
                    if not goal:
                        return ToolResult(
                            error="Goal is required for 'extract_content' action"
                        )

                    # Check if a selector was provided and validate it
                    if selector:
                        if not self.selector_tracker.is_valid_selector(selector):
                            return ToolResult(
                                error=f"Invalid selector format: '{selector}'. Please use valid CSS selectors."
                            )

                        if not self.selector_tracker.track_selector(selector):
                            return ToolResult(
                                error=f"Selector '{selector}' has been used too many times. Please try a different approach."
                            )

                    try:
                        # Get current page state
                        page = await context.get_current_page()
                        page_url = page.url
                        page_title = await page.title()

                        # For webpage replication, get DOM structure instead of raw HTML
                        if "replication" in goal.lower() or "build" in goal.lower():
                            # Get page structure using Playwright methods
                            try:
                                # Get main content areas using CSS selectors
                                header = await page.query_selector("header")
                                nav = await page.query_selector("nav")
                                main = await page.query_selector("main")
                                footer = await page.query_selector("footer")

                                # Get basic page structure info
                                page_structure = []
                                page_structure.append(f"Title: {page_title}")

                                if header:
                                    header_text = await header.inner_text()
                                    page_structure.append(
                                        f"Header: {header_text[:200]}..."
                                    )

                                if nav:
                                    nav_text = await nav.inner_text()
                                    page_structure.append(
                                        f"Navigation: {nav_text[:200]}..."
                                    )

                                if main:
                                    main_text = await main.inner_text()
                                    page_structure.append(
                                        f"Main Content: {main_text[:500]}..."
                                    )

                                if footer:
                                    footer_text = await footer.inner_text()
                                    page_structure.append(
                                        f"Footer: {footer_text[:200]}..."
                                    )

                                # Fallback to body content if no structure found
                                if not any([header, nav, main, footer]):
                                    body = await page.query_selector("body")
                                    if body:
                                        body_text = await body.inner_text()
                                        page_structure.append(
                                            f"Body Content: {body_text[:800]}..."
                                        )

                                dom_elements = "\n".join(page_structure)
                            except Exception as struct_e:
                                logger.warning(
                                    f"Could not extract page structure: {struct_e}"
                                )
                                # Fallback to basic text content
                                body_text = await page.evaluate(
                                    "document.body.innerText"
                                )
                                dom_elements = f"Page Text: {body_text[:1000]}..."

                            # Extract key structural information
                            structural_info = f"""
Page URL: {page_url}
Page Title: {page_title}

Key Page Structure:
{dom_elements}

Goal: {goal}
"""
                        else:
                            # For content summarization, get text content
                            page_content = await page.content()
                            # Reduce content length for better LLM processing
                            content_limit = min(max_content_length, 1000)

                            structural_info = f"""
Page URL: {page_url}
Page Title: {page_title}

Page Content: {page_content[:content_limit]}...

Goal: {goal}
"""

                        # Simple extraction without LLM for now to avoid timeouts
                        return ToolResult(
                            output=f"Content extracted from {page_url}:\n\n{structural_info}"
                        )

                    except Exception as e:
                        logger.error(f"Content extraction failed: {e}")
                        return ToolResult(error=f"Failed to extract content: {str(e)}")

                # Tab management actions
                elif action == "switch_tab":
                    if tab_id is None:
                        return ToolResult(
                            error="Tab ID is required for 'switch_tab' action"
                        )
                    await context.switch_to_tab(tab_id)
                    page = await context.get_current_page()
                    await page.wait_for_load_state()
                    return ToolResult(output=f"Switched to tab {tab_id}")

                elif action == "open_tab":
                    if not url:
                        return ToolResult(error="URL is required for 'open_tab' action")
                    await context.create_new_tab(url)
                    return ToolResult(output=f"Opened new tab with {url}")

                elif action == "close_tab":
                    await context.close_current_tab()
                    return ToolResult(output="Closed current tab")

                # Utility actions
                elif action == "wait":
                    seconds_to_wait = seconds if seconds is not None else 3
                    await asyncio.sleep(seconds_to_wait)
                    return ToolResult(output=f"Waited for {seconds_to_wait} seconds")

                else:
                    return ToolResult(error=f"Unknown action: {action}")

            except Exception as e:
                return ToolResult(error=f"Browser action '{action}' failed: {str(e)}")

    async def get_current_state(
        self, context: Optional[BrowserContext] = None
    ) -> ToolResult:
        """
        Get the current browser state as a ToolResult.
        If context is not provided, uses self.context.
        """
        try:
            # Use provided context or fall back to self.context
            ctx = context or self.context
            if not ctx:
                return ToolResult(error="Browser context not initialized")

            state = await ctx.get_state()

            # Create a viewport_info dictionary if it doesn't exist
            viewport_height = 0
            if hasattr(state, "viewport_info") and state.viewport_info:
                viewport_height = state.viewport_info.height
            elif hasattr(ctx, "config") and hasattr(ctx.config, "browser_window_size"):
                viewport_height = ctx.config.browser_window_size.get("height", 0)

            # Get the current page
            page = await ctx.get_current_page()

            # Get screenshot as base64
            screenshot = None
            try:
                screenshot_bytes = await page.screenshot(type="jpeg", quality=50)
                screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
            except Exception as e:
                logger.warning(f"Failed to take screenshot: {e}")

            # Return the state
            result = ToolResult(
                output=json.dumps(state),
                base64_image=screenshot,
            )

            return result
        except Exception as e:
            return ToolResult(error=f"Failed to get browser state: {str(e)}")

    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            logger.info("Browser resources cleaned up")
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")
