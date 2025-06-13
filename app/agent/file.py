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
        Handle file operations including creating HTML files, text files, and other content.
        """
        import os
        from datetime import datetime

        # If we already saved a file, we're done
        if hasattr(self, "_file_saved") and self._file_saved:
            return "Task completed - file already saved."

        # Get the user request
        user_request = None
        if hasattr(self, "messages"):
            for msg in reversed(self.messages):
                if msg.role == "user":
                    user_request = msg.content
                    break

        if not user_request:
            return "No user request found."

        # Analyze the request to determine file type and content
        user_request_lower = user_request.lower()

        # Determine file type and generate appropriate content
        if "html" in user_request_lower and (
            "webpage" in user_request_lower or "page" in user_request_lower
        ):
            # Create HTML webpage
            title = "My Test Page"  # Default title

            # Extract title if specified
            if "title" in user_request_lower:
                import re

                title_match = re.search(
                    r"title\s*['\"]([^'\"]+)['\"]", user_request, re.IGNORECASE
                )
                if title_match:
                    title = title_match.group(1)

            # Generate HTML content
            content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        p {{
            color: #666;
            line-height: 1.6;
        }}
        .highlight {{
            background-color: #e8f5e8;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Welcome to this simple HTML webpage!</p>
        <div class="highlight">
            <p>This page was created by the ParManusAI file agent. It demonstrates basic HTML structure with some styling.</p>
        </div>
        <p>This is a sample webpage with:</p>
        <ul>
            <li>A clean, responsive design</li>
            <li>Professional styling</li>
            <li>Semantic HTML structure</li>
            <li>Modern CSS styling</li>
        </ul>
        <p>You can customize this content as needed for your specific requirements.</p>
    </div>
</body>
</html>"""

            # Determine filename
            filename = f"webpage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        elif "news" in user_request_lower or "search" in user_request_lower:
            # Handle news requests by delegating to browser agent
            from app.agent.browser import BrowserAgent

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

            filename = f"news_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        else:
            # Default text file creation
            content = f"Content generated based on request: {user_request}\n\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            filename = f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        # Save the file
        workspace_dir = os.path.join(os.getcwd(), "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        file_path = os.path.join(workspace_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Mark as completed to avoid repeating
        self._file_saved = True

        file_type = "HTML webpage" if filename.endswith(".html") else "file"
        return f"{file_type.capitalize()} created and saved to {file_path}"
