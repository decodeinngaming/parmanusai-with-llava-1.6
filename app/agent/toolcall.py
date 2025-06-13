import asyncio
import json
from typing import Any, List, Optional, Union

from pydantic import Field

from app.agent.react import ReActAgent
from app.exceptions import TokenLimitExceeded
from app.logger import logger
from app.prompt.toolcall import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.schema import TOOL_CHOICE_TYPE, AgentState, Message, ToolCall, ToolChoice
from app.tool import CreateChatCompletion, Terminate, ToolCollection

TOOL_CALL_REQUIRED = "Tool calls required but none provided"


class ToolCallAgent(ReActAgent):
    """Base agent class for handling tool/function calls with enhanced abstraction"""

    name: str = "toolcall"
    description: str = "an agent that can execute tool calls."

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    available_tools: ToolCollection = ToolCollection(
        CreateChatCompletion(), Terminate()
    )
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO  # type: ignore
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None

    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None

    async def think(self) -> bool:
        """Process current state and decide next actions using tools"""
        if self.next_step_prompt:
            user_msg = Message.user_message(self.next_step_prompt)
            self.messages += [user_msg]

        try:
            # Get context-windowed messages to prevent token overflow
            context_messages = self.memory.get_context(
                max_tokens=1500
            )  # Use much smaller context to prevent overflow

            # Get response with tool options
            response = await self.llm.ask_tool(
                messages=context_messages,
                system_msgs=(
                    [Message.system_message(self.system_prompt)]
                    if self.system_prompt
                    else None
                ),
                tools=self.available_tools.to_params(),
                tool_choice=self.tool_choices,
            )

            # Debug: Log the raw response to understand what the LLM is generating
            logger.info(f"Raw LLM response received: {response}")
            if isinstance(response, dict) and "message" in response:
                logger.info(f"Raw LLM message content: {response['message']}")

        except ValueError:
            raise
        except Exception as e:
            # Check if this is a RetryError containing TokenLimitExceeded
            if hasattr(e, "__cause__") and isinstance(e.__cause__, TokenLimitExceeded):
                token_limit_error = e.__cause__
                logger.error(
                    f"🚨 Token limit error (from RetryError): {token_limit_error}"
                )
                self.memory.add_message(
                    Message.assistant_message(
                        f"Maximum token limit reached, cannot continue execution: {str(token_limit_error)}"
                    )
                )
                self.state = AgentState.FINISHED
                return False
            raise

        self.tool_calls = tool_calls = (
            response.get("tool_calls")
            if response and isinstance(response, dict)
            else (
                response.tool_calls
                if response and hasattr(response, "tool_calls")
                else []
            )
        )

        # Get content for parsing
        content = (
            response.get("content")
            if response and isinstance(response, dict)
            else response.content if response and hasattr(response, "content") else ""
        )

        # If no tool calls in response but content contains JSON with tool_calls, parse it
        if (
            not tool_calls
            and content
            and ("tool_calls" in content or "function" in content)
        ):
            logger.info("🔍 Attempting to parse tool calls from content...")
            try:
                # Try to extract JSON from the content
                import re

                # Look for JSON-like structure in content
                json_pattern = r'\{[^{}]*"tool_calls"[^{}]*\[[^\]]*\][^{}]*\}'
                json_match = re.search(json_pattern, content, re.DOTALL)

                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"📝 Found JSON in content: {json_str[:200]}...")
                    parsed_json = json.loads(json_str)

                    if "tool_calls" in parsed_json:
                        tool_calls = parsed_json["tool_calls"]
                        logger.info(
                            f"✅ Extracted {len(tool_calls)} tool calls from content"
                        )
                else:
                    # Fallback: look for individual function calls
                    func_pattern = r'"function":\s*\{[^}]*"name":\s*"([^"]*)"[^}]*"arguments":\s*(\{[^}]*\})[^}]*\}'
                    func_matches = re.finditer(func_pattern, content, re.DOTALL)

                    extracted_calls = []
                    for i, match in enumerate(func_matches):
                        name = match.group(1)
                        args_str = match.group(2)
                        try:
                            args_dict = json.loads(args_str)
                            extracted_calls.append(
                                {
                                    "id": f"extracted_{i}",
                                    "type": "function",
                                    "function": {
                                        "name": name,
                                        "arguments": json.dumps(args_dict),
                                    },
                                }
                            )
                        except:
                            # If JSON parsing fails, use the string as-is
                            extracted_calls.append(
                                {
                                    "id": f"extracted_{i}",
                                    "type": "function",
                                    "function": {"name": name, "arguments": args_str},
                                }
                            )

                    if extracted_calls:
                        tool_calls = extracted_calls
                        logger.info(
                            f"✅ Extracted {len(tool_calls)} tool calls using fallback method"
                        )

            except Exception as e:
                logger.warning(f"⚠️ Failed to parse tool calls from content: {e}")

        # PATCH: If still no tool calls and the prompt is a browser/navigation task, insert a default tool call
        if not tool_calls:
            # Try to infer from the latest user message and the current task
            last_user_msg = None
            for msg in reversed(self.messages):
                if msg.role == "user":
                    last_user_msg = msg.content.lower()
                    break

            # Also get the current task being processed (for browser agent)
            current_task = None
            if (
                hasattr(self, "memory")
                and self.memory
                and hasattr(self.memory, "messages")
            ):
                user_messages = [
                    msg for msg in self.memory.messages if msg.role == "user"
                ]
                if user_messages:
                    current_task = user_messages[0].content.lower()

            # Check both the last user message and current task for patterns
            text_to_check = f"{last_user_msg or ''} {current_task or ''}".strip()
            if text_to_check:
                import re

                # 1. Navigation
                url_match = re.search(
                    r"(?:go to|visit|open) (https?://)?([\w.-]+\.[a-z]{2,})(/\S*)?",
                    text_to_check,
                )
                if url_match:
                    url = url_match.group(2)
                    if not url_match.group(1):
                        url = "https://" + url
                    else:
                        url = url_match.group(0).split(" ", 1)[-1]
                    tool_calls = [
                        {
                            "id": "default_browser_use",
                            "type": "function",
                            "function": {
                                "name": "browser_use",
                                "arguments": json.dumps(
                                    {"action": "go_to_url", "url": url}
                                ),
                            },
                        }
                    ]
                    logger.warning(
                        f"⚠️ No tool call from LLM, inserting default browser_use tool call for URL: {url}"
                    )
                # 2. News search (check this before general extract to prioritize)
                elif any(
                    word in text_to_check
                    for word in [
                        "news",
                        "latest news",
                        "search for latest news",
                        "search for news",
                    ]
                ) or (
                    "search" in text_to_check
                    and any(
                        word in text_to_check for word in ["latest", "today", "current"]
                    )
                ):
                    tool_calls = [
                        {
                            "id": "default_browser_use_search",
                            "type": "function",
                            "function": {
                                "name": "browser_use",
                                "arguments": json.dumps(
                                    {
                                        "action": "web_search",
                                        "query": "latest news today",
                                    }
                                ),
                            },
                        }
                    ]
                    logger.warning(
                        "⚠️ No tool call from LLM, inserting browser_use tool call for web_search"
                    )
                # 3. Summarize or extract content (after news check)
                elif any(
                    word in text_to_check
                    for word in [
                        "summarize",
                        "summary",
                        "extract",
                        "analyze",
                        "look at",
                        "read",
                        "get content",
                    ]
                ):
                    tool_calls = [
                        {
                            "id": "default_browser_use_extract",
                            "type": "function",
                            "function": {
                                "name": "browser_use",
                                "arguments": json.dumps(
                                    {"action": "extract_content", "goal": text_to_check}
                                ),
                            },
                        }
                    ]
                    logger.warning(
                        "⚠️ No tool call from LLM, inserting browser_use tool call for extract_content"
                    )
                # 4. General search for non-news items
                elif "search" in text_to_check:
                    tool_calls = [
                        {
                            "id": "default_browser_use_search_general",
                            "type": "function",
                            "function": {
                                "name": "browser_use",
                                "arguments": json.dumps(
                                    {"action": "web_search", "query": text_to_check}
                                ),
                            },
                        }
                    ]
                    logger.warning(
                        "⚠️ No tool call from LLM, inserting browser_use tool call for general web_search"
                    )
                # 5. Save/download page
                elif any(word in text_to_check for word in ["save", "download"]):
                    tool_calls = [
                        {
                            "id": "default_browser_use_save",
                            "type": "function",
                            "function": {
                                "name": "browser_use",
                                "arguments": json.dumps(
                                    {
                                        "action": "extract_content",
                                        "goal": "save page to disk",
                                    }
                                ),
                            },
                        }
                    ]
                    logger.warning(
                        "⚠️ No tool call from LLM, inserting browser_use tool call for save/download"
                    )
                # 6. Blank page creation
                elif any(
                    word in text_to_check
                    for word in [
                        "browser",
                        "web page",
                        "build me a web page",
                        "create a web page",
                        "blank page",
                        "new page",
                    ]
                ):
                    tool_calls = [
                        {
                            "id": "default_browser_use_blank",
                            "type": "function",
                            "function": {
                                "name": "browser_use",
                                "arguments": json.dumps(
                                    {"action": "go_to_url", "url": "about:blank"}
                                ),
                            },
                        }
                    ]
                    logger.warning(
                        "⚠️ No tool call from LLM, inserting default browser_use tool call for about:blank (open blank page)"
                    )
                # Final fallback: if no conditions matched and it's a browser agent, default to news search
                else:
                    if self.name == "browser":
                        tool_calls = [
                            {
                                "id": "default_browser_use_news",
                                "type": "function",
                                "function": {
                                    "name": "browser_use",
                                    "arguments": json.dumps(
                                        {
                                            "action": "web_search",
                                            "query": "latest news today",
                                        }
                                    ),
                                },
                            }
                        ]
                        logger.warning(
                            "⚠️ No tool call from LLM and no conditions matched, defaulting to news search"
                        )
        # Convert dictionary tool calls to proper ToolCall objects
        if tool_calls and isinstance(tool_calls[0], dict):
            from app.schema import Function, ToolCall

            converted_calls = []
            for call_dict in tool_calls:
                if isinstance(call_dict, dict):
                    # Handle dictionary format from our custom parser
                    if "function" in call_dict:
                        func_data = call_dict["function"]
                        tool_call = ToolCall(
                            id=call_dict.get("id", f"call_{len(converted_calls)}"),
                            type=call_dict.get("type", "function"),
                            function=Function(
                                name=func_data["name"], arguments=func_data["arguments"]
                            ),
                        )
                    else:
                        # Handle old format where name/arguments are at top level
                        tool_call = ToolCall(
                            id=call_dict.get("id", f"call_{len(converted_calls)}"),
                            type="function",
                            function=Function(
                                name=call_dict["name"],
                                arguments=json.dumps(call_dict.get("arguments", {})),
                            ),
                        )
                    converted_calls.append(tool_call)
            self.tool_calls = tool_calls = converted_calls

        # Log response info
        logger.info(f"✨ {self.name}'s thoughts: {content}")
        logger.info(
            f"🛠️ {self.name} selected {len(tool_calls) if tool_calls else 0} tools to use"
        )
        if tool_calls:
            logger.info(
                f"🧰 Tools being prepared: {[call.function.name for call in tool_calls]}"
            )
            logger.info(f"🔧 Tool arguments: {tool_calls[0].function.arguments}")

        try:
            if response is None:
                raise RuntimeError("No response received from the LLM")

            # Handle different tool_choices modes
            if self.tool_choices == ToolChoice.NONE:
                if tool_calls:
                    logger.warning(
                        f"🤔 Hmm, {self.name} tried to use tools when they weren't available!"
                    )
                if content:
                    self.memory.add_message(Message.assistant_message(content))
                    return True
                return False

            # Create and add assistant message
            assistant_msg = (
                Message.from_tool_calls(content=content, tool_calls=self.tool_calls)
                if self.tool_calls
                else Message.assistant_message(content)
            )
            self.memory.add_message(assistant_msg)

            if self.tool_choices == ToolChoice.REQUIRED and not self.tool_calls:
                return True  # Will be handled in act()

            # For 'auto' mode, continue with content if no commands but content exists
            if self.tool_choices == ToolChoice.AUTO and not self.tool_calls:
                return bool(content)

            return bool(self.tool_calls)
        except Exception as e:
            logger.error(f"🚨 Oops! The {self.name}'s thinking process hit a snag: {e}")
            self.memory.add_message(
                Message.assistant_message(
                    f"Error encountered while processing: {str(e)}"
                )
            )
            return False

    async def act(self) -> str:
        """Execute tool calls and handle their results"""
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                raise ValueError(TOOL_CALL_REQUIRED)

            # Return last message content if no tool calls
            return self.messages[-1].content or "No content or commands to execute"

        results = []
        for command in self.tool_calls:
            # Reset base64_image for each tool call
            self._current_base64_image = None

            result = await self.execute_tool(command)

            if self.max_observe:
                result = result[: self.max_observe]

            logger.info(
                f"🎯 Tool '{command.function.name}' completed its mission! Result: {result}"
            )

            # Add tool response to memory
            tool_msg = Message.tool_message(
                content=result,
                tool_call_id=command.id,
                name=command.function.name,
                base64_image=self._current_base64_image,
            )
            self.memory.add_message(tool_msg)
            results.append(result)

        return "\n\n".join(results)

    async def execute_tool(self, command: ToolCall) -> str:
        """Execute a single tool call with robust error handling"""
        if not command or not command.function or not command.function.name:
            return "Error: Invalid command format"

        name = command.function.name
        if name not in self.available_tools.tool_map:
            return f"Error: Unknown tool '{name}'"

        try:
            # Parse arguments
            args = json.loads(command.function.arguments or "{}")

            # Execute the tool
            logger.info(f"🔧 Activating tool: '{name}'...")
            result = await self.available_tools.execute(name=name, tool_input=args)

            # Handle special tools
            await self._handle_special_tool(name=name, result=result)

            # Check if result is a ToolResult with base64_image
            if hasattr(result, "base64_image") and result.base64_image:
                # Store the base64_image for later use in tool_message
                self._current_base64_image = result.base64_image

            # Format result for display (standard case)
            observation = (
                f"Observed output of cmd `{name}` executed:\n{str(result)}"
                if result
                else f"Cmd `{name}` completed with no output"
            )

            return observation
        except json.JSONDecodeError:
            error_msg = f"Error parsing arguments for {name}: Invalid JSON format"
            logger.error(
                f"📝 Oops! The arguments for '{name}' don't make sense - invalid JSON, arguments:{command.function.arguments}"
            )
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"⚠️ Tool '{name}' encountered a problem: {str(e)}"
            logger.exception(error_msg)
            return f"Error: {error_msg}"

    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        """Handle special tool execution and state changes"""
        if not self._is_special_tool(name):
            return

        if self._should_finish_execution(name=name, result=result, **kwargs):
            # Set agent state to finished
            logger.info(f"🏁 Special tool '{name}' has completed the task!")
            self.state = AgentState.FINISHED

    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        """Determine if tool execution should finish the agent"""
        return True

    def _is_special_tool(self, name: str) -> bool:
        """Check if tool name is in special tools list"""
        return name.lower() in [n.lower() for n in self.special_tool_names]

    async def cleanup(self):
        """Clean up resources used by the agent's tools."""
        logger.info(f"🧹 Cleaning up resources for agent '{self.name}'...")
        for tool_name, tool_instance in self.available_tools.tool_map.items():
            if hasattr(tool_instance, "cleanup") and asyncio.iscoroutinefunction(
                tool_instance.cleanup
            ):
                try:
                    logger.debug(f"🧼 Cleaning up tool: {tool_name}")
                    await tool_instance.cleanup()
                except Exception as e:
                    logger.error(
                        f"🚨 Error cleaning up tool '{tool_name}': {e}", exc_info=True
                    )
        logger.info(f"✨ Cleanup complete for agent '{self.name}'.")

    async def run(self, request: Optional[str] = None) -> str:
        """Run the agent with cleanup when done."""
        try:
            return await super().run(request)
        finally:
            await self.cleanup()

        # SPECIAL HANDLING: If tool_calls is empty but content contains tool call JSON, extract it
        if not tool_calls and content and isinstance(content, str):
            import json
            import re

            # Look for JSON tool calls in content
            tool_call_match = re.search(
                r'\{"tool_calls":\s*\[(.*?)\]\}', content, re.DOTALL
            )
            if tool_call_match:
                try:
                    # Extract and parse the tool calls JSON
                    tool_calls_json = f'{{"tool_calls": [{tool_call_match.group(1)}]}}'
                    parsed_data = json.loads(tool_calls_json)
                    extracted_calls = parsed_data.get("tool_calls", [])

                    # Convert to ToolCall objects
                    converted_calls = []
                    for i, call_data in enumerate(extracted_calls):
                        if "function" in call_data:
                            func_data = call_data["function"]
                            # Handle arguments that might be a dict or string
                            arguments = func_data.get("arguments", {})
                            if isinstance(arguments, dict):
                                arguments = json.dumps(arguments)

                            tool_call = ToolCall(
                                id=call_data.get("id", f"extracted_call_{i}"),
                                type=call_data.get("type", "function"),
                                function=Function(
                                    name=func_data["name"], arguments=arguments
                                ),
                            )
                            converted_calls.append(tool_call)

                    if converted_calls:
                        logger.info(
                            f"🔍 Extracted {len(converted_calls)} tool calls from content"
                        )
                        self.tool_calls = tool_calls = converted_calls

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse tool calls from content: {e}")
