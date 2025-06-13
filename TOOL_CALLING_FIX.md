# Tool Calling Fix for ParManusAI

This directory contains scripts to fix and improve the tool calling functionality in ParManusAI. The fixes focus on making the agent reliably recognize and execute tool calls for user tasks like "build a webpage with trending news today."

## Problem

The agent was previously failing to detect tool calls in various formats, leading to inconsistent behavior when users requested actions that should trigger tools (like web browsing).

## Solution

These scripts implement the following fixes:

1. Enhanced Tool Call Parser
   - Improved regex patterns to detect various tool call formats
   - Added support for direct URL recognition and search term detection
   - Made the JSON parsing more robust with better error handling

2. Prompt Template Improvements
   - Updated tool call format instructions to be clearer
   - Enhanced browser tool usage guidance

## Scripts

- `fix_tool_calling.py`: Main Python fix script that patches the tool call parser
- `fix_tool_calling.ps1`: PowerShell script to run the fix, tests, and verification
- `test_tool_parsing.py`: Tests the tool call parser with various input formats
- `verify_tool_calling.py`: Verifies that the agent can handle real user prompts
- `enhance_tool_prompts.py`: Enhances the prompt templates for better tool guidance

## Running the Fix

1. Run the PowerShell script:
   ```
   .\fix_tool_calling.ps1
   ```

2. Follow the prompts to apply the fix, run tests, and optionally verify the agent

3. Test the agent with:
   ```
   python main.py --prompt "build a webpage with trending news today"
   ```

## Technical Details

The fix primarily addresses the `_parse_tool_calls` function in `app/llm_tool_patch.py`, which is responsible for detecting and parsing tool calls in the model's output. The enhanced version adds:

1. Better function-style call detection
2. More robust JSON parsing
3. Direct URL recognition for browser navigation
4. Search term detection for web searches
5. Special handling for news and trending topics

These improvements allow the agent to recognize tool calls even when they're not perfectly formatted, increasing the reliability of the system.

## Verification

The verification script tests the agent with several typical user prompts to ensure it correctly identifies and executes the appropriate tool calls. This serves as an end-to-end test of the fix.
