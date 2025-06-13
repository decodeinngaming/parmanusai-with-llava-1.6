from app.agent.base import BaseAgent


class FileAgent(BaseAgent):
    """
    File agent that can save content to files and coordinate with other agents.
    """

    name: str = "file"
    _file_saved: bool = False

    @classmethod
    async def create(cls, **kwargs):
        """Factory method to create and properly initialize a FileAgent instance."""
        instance = cls(**kwargs)
        return instance

    async def step(self):
        """
        Handle file operations including fetching news, summarizing, and saving.
        """
        import os
        from datetime import datetime

        # If we already saved a file, we're done
        if hasattr(self, "_file_saved") and self._file_saved:
            return "Task completed - file already saved."

        # Check if this is a news request that needs browser agent
        user_request = None
        if hasattr(self, "messages"):
            for msg in reversed(self.messages):
                if msg.role == "user":
                    user_request = msg.content.lower()
                    break

        if user_request and any(
            word in user_request for word in ["news", "search", "summarize", "look for"]
        ):
            # This is a complex task that needs browser agent - delegate to browser for news fetching
            from app.agent.browser import BrowserAgent
            from app.agent.router import AgentRouter

            try:
                # Create browser agent to fetch and summarize news
                browser_agent = await BrowserAgent.create(
                    llm=self.llm, memory=self.memory
                )

                # Run browser agent to get news summary
                news_result = await browser_agent.run(
                    "search for latest news and summarize it"
                )

                # Extract the summary from browser agent result
                content = (
                    news_result if isinstance(news_result, str) else str(news_result)
                )

            except Exception as e:
                content = (
                    f"Error fetching news: {str(e)}\nFallback content: {user_request}"
                )
        else:
            # Simple file save - get content from messages
            content = None
            if hasattr(self, "messages"):
                for msg in reversed(self.messages):
                    if msg.role in ("assistant", "tool") and msg.content:
                        content = msg.content
                        break
            if not content:
                content = user_request or "No content to save."

        # Save to workspace/news_summary_<timestamp>.txt
        workspace_dir = os.path.join(os.getcwd(), "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        filename = f"news_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join(workspace_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Mark as completed to avoid repeating
        self._file_saved = True
        return f"News summary saved to {file_path}"
