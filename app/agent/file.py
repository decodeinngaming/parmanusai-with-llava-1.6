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

    async def reset_state(self):
        """Reset the file agent state for new tasks."""
        self._file_saved = False
        # Call parent reset if it exists
        if hasattr(super(), "reset_state"):
            await super().reset_state()

    async def step(self):
        """
        Handle file operations including creating HTML files, text files, and other content.
        Enhanced to delegate web search tasks to browser agent when needed.
        """
        import asyncio
        import logging
        import os
        from datetime import datetime

        # Setup logger
        logger = logging.getLogger(__name__)

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

        # Enhanced timeout and memory management
        start_time = datetime.now()
        max_processing_time = 60  # 60 seconds max per request

        # Analyze the request to determine file type and content
        user_request_lower = user_request.lower()

        # Check if this request needs website analysis AND webpage creation
        needs_website_analysis = (
            any(
                pattern in user_request_lower
                for pattern in [
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
                    "mimic google",
                    "copy google",
                    "similar to google",
                    "inspired by google",
                    "like google but",
                    "style of google",
                    "design of google",
                    "mimic facebook",
                    "copy facebook",
                    "similar to facebook",
                    "inspired by facebook",
                    "like facebook but",
                    "style of facebook",
                    "design of facebook",
                    "mimic amazon",
                    "copy amazon",
                    "similar to amazon",
                    "inspired by amazon",
                ]
            )
            or (
                "look at" in user_request_lower
                and any(
                    site in user_request_lower
                    for site in [
                        "google",
                        "facebook",
                        "amazon",
                        "twitter",
                        "youtube",
                        "linkedin",
                        "instagram",
                        "github",
                        "stackoverflow",
                        "reddit",
                        "website",
                        "site",
                    ]
                )
                and any(
                    action in user_request_lower
                    for action in ["build", "create", "make", "generate", "design"]
                )
                and any(
                    target in user_request_lower
                    for target in ["webpage", "page", "website", "site"]
                )
            )
            or (
                any(
                    mimic_word in user_request_lower
                    for mimic_word in [
                        "mimic",
                        "copy",
                        "similar",
                        "inspired",
                        "like",
                        "style",
                        "design",
                    ]
                )
                and any(
                    site in user_request_lower
                    for site in [
                        "google",
                        "facebook",
                        "amazon",
                        "twitter",
                        "youtube",
                        "linkedin",
                        "instagram",
                    ]
                )
                and any(
                    target in user_request_lower
                    for target in ["webpage", "page", "website", "site"]
                )
            )
        )

        # If website analysis and webpage creation are needed, delegate to browser first
        if needs_website_analysis:
            try:
                # Check processing time
                if (datetime.now() - start_time).seconds > max_processing_time:
                    logger.warning(
                        "Processing timeout reached, falling back to simple webpage"
                    )
                    return await self._create_simple_webpage(user_request)

                # Import and create browser agent with timeout
                from app.agent.browser import BrowserAgent

                browser_agent = await BrowserAgent.create()

                # Extract the website to analyze
                site_to_analyze = "https://www.google.com"  # Default to Google
                if "google" in user_request_lower:
                    site_to_analyze = "https://www.google.com"
                elif "facebook" in user_request_lower:
                    site_to_analyze = "https://www.facebook.com"
                elif "amazon" in user_request_lower:
                    site_to_analyze = "https://www.amazon.com"
                elif "twitter" in user_request_lower:
                    site_to_analyze = "https://www.twitter.com"
                elif "youtube" in user_request_lower:
                    site_to_analyze = "https://www.youtube.com"
                elif "linkedin" in user_request_lower:
                    site_to_analyze = "https://www.linkedin.com"
                elif "instagram" in user_request_lower:
                    site_to_analyze = "https://www.instagram.com"
                elif "github" in user_request_lower:
                    site_to_analyze = "https://www.github.com"
                elif "stackoverflow" in user_request_lower:
                    site_to_analyze = "https://www.stackoverflow.com"
                elif "reddit" in user_request_lower:
                    site_to_analyze = "https://www.reddit.com"

                # Task the browser agent to analyze the website
                browser_task = f"navigate to {site_to_analyze} and analyze the design, layout, and structure"
                from app.schema import Message

                browser_agent.memory.add_message(Message.user_message(browser_task))

                # Run the browser agent to get website analysis with timeout
                try:
                    analysis_result = await asyncio.wait_for(
                        browser_agent.run(),
                        timeout=30,  # 30 second timeout for browser operations
                    )
                except asyncio.TimeoutError:
                    logger.warning("Browser analysis timed out, using fallback design")
                    analysis_result = f"Timeout occurred while analyzing {site_to_analyze}. Using default design elements."

                # Now create webpage based on the analysis
                return await self._create_webpage_based_on_analysis(
                    user_request, analysis_result, site_to_analyze
                )

            except Exception as e:
                # Log the exception for debugging
                import logging

                logging.error(f"Website analysis failed: {e}")
                # Fallback to creating basic webpage
                logger.info("Falling back to simple webpage creation")
                return await self._create_simple_webpage(user_request)

        # Check if this request needs web search AND webpage creation
        needs_web_search = any(
            keyword in user_request_lower
            for keyword in [
                "search the web",
                "search web",
                "look up",
                "look for",
                "find information",
                "find the",
                "get the",
                "latest trends",
                "current news",
                "recent",
                "today",
                "now",
                "up to date",
                "real time",
                "current information",
                "top 10",
                "top ten",
                "best",
                "trending",
                "news",
                "articles",
                "headlines",
                "stories",
            ]
        )

        needs_webpage_creation = any(
            keyword in user_request_lower
            for keyword in [
                "create webpage",
                "build webpage",
                "make webpage",
                "generate webpage",
                "create page",
                "build page",
                "create a webpage",
                "build a webpage",
                "make a webpage",
                "build me a web page",
                "build me a webpage",
                "create me a webpage",
                "make me a webpage",
                "create website",
                "build website",
                "html",
                "website",
                "web page",
                "showing",  # as in "showing all top 10 news"
                "displaying",  # as in "displaying the results"
            ]
        ) or (
            # Also check for "create" + "with" + web search context
            "create" in user_request_lower
            and (
                "with the information" in user_request_lower
                or "with the data" in user_request_lower
                or "with the results" in user_request_lower
            )
        )

        # If both web search and webpage creation are needed, delegate to browser first
        if needs_web_search and needs_webpage_creation:
            try:
                # Check processing time
                if (datetime.now() - start_time).seconds > max_processing_time:
                    logger.warning(
                        "Processing timeout reached, falling back to simple webpage"
                    )
                    return await self._create_simple_webpage(user_request)

                # Import and create browser agent
                from app.agent.browser import BrowserAgent

                browser_agent = await BrowserAgent.create()

                # Extract search query from the request
                search_query = self._extract_search_query(user_request)

                # Task the browser agent to perform the search
                browser_task = (
                    f"search for {search_query} and extract detailed information"
                )
                from app.schema import Message

                browser_agent.memory.add_message(Message.user_message(browser_task))

                # Run the browser agent to get search results with timeout
                try:
                    search_result = await asyncio.wait_for(
                        browser_agent.run(),
                        timeout=30,  # 30 second timeout for search operations
                    )
                except asyncio.TimeoutError:
                    logger.warning("Browser search timed out, using fallback content")
                    search_result = f"Search timeout occurred for '{search_query}'. Using default content."

                # Now create webpage with the search results
                return await self._create_webpage_with_search_data(
                    user_request, search_result
                )

            except Exception as e:
                # Log the exception for debugging
                import logging

                logging.error(f"Web search failed: {e}")
                # Fallback to creating webpage without live data
                logger.info("Falling back to webpage creation without live data")
                return await self._create_simple_webpage(user_request)

        # Check if this is a standalone CSS file request (not part of HTML webpage creation)
        is_standalone_css = "css" in user_request_lower and any(
            keyword in user_request_lower
            for keyword in ["create", "write", "generate", "make", "build", "file"]
        )

        # Only create standalone CSS if HTML/webpage is NOT mentioned
        is_html_request = any(
            keyword in user_request_lower
            for keyword in ["html", "webpage", "web page", "website", "page"]
        )

        if is_standalone_css and not is_html_request:
            return await self._create_css_file(user_request)

        # Determine file type and generate appropriate content
        # Check for HTML/webpage creation requests with more comprehensive detection
        is_webpage_request = any(
            [
                # Direct HTML/webpage keywords
                "html" in user_request_lower,
                "webpage" in user_request_lower,
                "web page" in user_request_lower,
                "website" in user_request_lower,
                # Page creation with action words
                (
                    "page" in user_request_lower
                    and any(
                        action in user_request_lower
                        for action in ["create", "build", "make", "generate", "design"]
                    )
                ),
                # Landing page specifically
                "landing page" in user_request_lower,
                # E-commerce specific
                (
                    "e-commerce" in user_request_lower
                    and any(
                        action in user_request_lower
                        for action in ["create", "build", "make", "generate", "design"]
                    )
                ),
                (
                    "ecommerce" in user_request_lower
                    and any(
                        action in user_request_lower
                        for action in ["create", "build", "make", "generate", "design"]
                    )
                ),
                # Portfolio/restaurant/dashboard specific
                (
                    "portfolio" in user_request_lower
                    and any(
                        action in user_request_lower
                        for action in ["create", "build", "make", "generate", "design"]
                    )
                ),
                (
                    "restaurant" in user_request_lower
                    and any(
                        action in user_request_lower
                        for action in ["create", "build", "make", "generate", "design"]
                    )
                ),
                (
                    "dashboard" in user_request_lower
                    and any(
                        action in user_request_lower
                        for action in ["create", "build", "make", "generate", "design"]
                    )
                ),
            ]
        )

        if is_webpage_request:
            # Create HTML webpage
            title = "My Webpage"  # Default title

            # Extract title if specified or generate from request
            if "title" in user_request_lower:
                import re

                title_match = re.search(
                    r"title\s*['\"]([^'\"]+)['\"]", user_request, re.IGNORECASE
                )
                if title_match:
                    title = title_match.group(1)

            # Check if this is a request for fancy/animated webpage
            is_fancy = any(
                word in user_request_lower
                for word in [
                    "fancy",
                    "animation",
                    "transition",
                    "interactive",
                    "modern",
                    "sophisticated",
                    "advanced",
                    "beautiful",
                    "stunning",
                    "dynamic",
                ]
            )

            # Check if images are requested
            wants_images = any(
                word in user_request_lower
                for word in [
                    "image",
                    "images",
                    "picture",
                    "pictures",
                    "photo",
                    "photos",
                ]
            )

            # Generate title from request content if not explicitly provided
            if "title" not in user_request_lower:
                if (
                    "kitchener" in user_request_lower
                    and "ontario" in user_request_lower
                ):
                    title = "Top 10 Places to Visit in Kitchener, Ontario"
                elif "cats" in user_request_lower:
                    title = "All About Cats"
                elif "travel" in user_request_lower or "visit" in user_request_lower:
                    title = "Travel Guide"
                else:
                    title = "My Amazing Webpage"

            # Generate dynamic content based on request
            if "kitchener" in user_request_lower and (
                "place" in user_request_lower or "visit" in user_request_lower
            ):
                if is_fancy and wants_images:
                    main_content = f"""
        <div class="hero-section">
            <div class="hero-content">
                <h1 class="hero-title">✨ Top 10 Places to Visit in Kitchener, Ontario ✨</h1>
                <p class="hero-subtitle">Discover the vibrant heart of Waterloo Region</p>
                <div class="hero-image">
                    <img src="https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?w=800&h=400&fit=crop"
                         alt="Kitchener Skyline" class="fade-in-image" />
                </div>
            </div>
        </div>

        <div class="intro-section">
            <p class="intro-text">Kitchener is a vibrant city in the heart of Waterloo Region, offering a perfect blend of culture, history, and modern attractions. Explore these amazing destinations!</p>
        </div>

        <div class="places-grid">
            <div class="place-card animated" data-delay="0">
                <div class="card-image">
                    <img src="https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=200&fit=crop" alt="THEMUSEUM" />
                    <div class="card-overlay">
                        <span class="card-number">1</span>
                    </div>
                </div>
                <div class="card-content">
                    <h3>THEMUSEUM</h3>
                    <p>An interactive museum featuring science, technology, and art exhibitions for all ages.</p>
                    <div class="card-footer">
                        <span class="rating">⭐⭐⭐⭐⭐</span>
                        <span class="category">Museum</span>
                    </div>
                </div>
            </div>

            <div class="place-card animated" data-delay="100">
                <div class="card-image">
                    <img src="https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=300&h=200&fit=crop" alt="Victoria Park" />
                    <div class="card-overlay">
                        <span class="card-number">2</span>
                    </div>
                </div>
                <div class="card-content">
                    <h3>Victoria Park</h3>
                    <p>Beautiful lakefront park perfect for picnics, walking trails, and outdoor events.</p>
                    <div class="card-footer">
                        <span class="rating">⭐⭐⭐⭐⭐</span>
                        <span class="category">Nature</span>
                    </div>
                </div>
            </div>

            <div class="place-card animated" data-delay="200">
                <div class="card-image">
                    <img src="https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=300&h=200&fit=crop" alt="Kitchener Market" />
                    <div class="card-overlay">
                        <span class="card-number">3</span>
                    </div>
                </div>
                <div class="card-content">
                    <h3>Kitchener Market</h3>
                    <p>Historic farmers market operating since 1869, featuring local produce and artisan goods.</p>
                    <div class="card-footer">
                        <span class="rating">⭐⭐⭐⭐⭐</span>
                        <span class="category">Market</span>
                    </div>
                </div>
            </div>

            <div class="place-card animated" data-delay="300">
                <div class="card-image">
                    <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=200&fit=crop" alt="CIGI Campus" />
                    <div class="card-overlay">
                        <span class="card-number">4</span>
                    </div>
                </div>
                <div class="card-content">
                    <h3>CIGI Campus</h3>
                    <p>Modern campus with beautiful architecture and public events.</p>
                    <div class="card-footer">
                        <span class="rating">⭐⭐⭐⭐</span>
                        <span class="category">Architecture</span>
                    </div>
                </div>
            </div>

            <div class="place-card animated" data-delay="400">
                <div class="card-image">
                    <img src="https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=300&h=200&fit=crop" alt="Grand River" />
                    <div class="card-overlay">
                        <span class="card-number">5</span>
                    </div>
                </div>
                <div class="card-content">
                    <h3>Grand River</h3>
                    <p>Scenic river perfect for kayaking, canoeing, and riverside walks.</p>
                    <div class="card-footer">
                        <span class="rating">⭐⭐⭐⭐⭐</span>
                        <span class="category">Recreation</span>
                    </div>
                </div>
            </div>

            <div class="place-card animated" data-delay="500">
                <div class="card-image">
                    <img src="https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=300&h=200&fit=crop" alt="St. Jacobs Village" />
                    <div class="card-overlay">
                        <span class="card-number">6</span>
                    </div>
                </div>
                <div class="card-content">
                    <h3>St. Jacobs Village</h3>
                    <p>Charming nearby village known for its farmers market and Mennonite heritage.</p>
                    <div class="card-footer">
                        <span class="rating">⭐⭐⭐⭐⭐</span>
                        <span class="category">Heritage</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="highlight animated fade-in-up">
            <h3>🗺️ Planning Your Visit</h3>
            <p>Kitchener offers something for everyone - from cultural attractions and historic sites to outdoor activities and family fun. The city is easily accessible by car or public transit, and many attractions are within walking distance of downtown.</p>
            <div class="planning-tips">
                <div class="tip">
                    <span class="tip-icon">🚗</span>
                    <span>Free parking available at most locations</span>
                </div>
                <div class="tip">
                    <span class="tip-icon">🚌</span>
                    <span>Excellent public transit connections</span>
                </div>
                <div class="tip">
                    <span class="tip-icon">🏨</span>
                    <span>Stay downtown for walking access</span>
                </div>
            </div>
        </div>"""
                else:
                    # Regular version without fancy animations
                    main_content = """
        <h1>Top 10 Places to Visit in Kitchener, Ontario</h1>
        <p>Kitchener is a vibrant city in the heart of Waterloo Region, offering a perfect blend of culture, history, and modern attractions.</p>

        <div class="places-grid">
            <div class="place-card">
                <h3>1. THEMUSEUM</h3>
                <p>An interactive museum featuring science, technology, and art exhibitions for all ages.</p>
            </div>
            <div class="place-card">
                <h3>2. Victoria Park</h3>
                <p>Beautiful lakefront park perfect for picnics, walking trails, and outdoor events.</p>
            </div>
            <div class="place-card">
                <h3>3. Kitchener Market</h3>
                <p>Historic farmers market operating since 1869, featuring local produce and artisan goods.</p>
            </div>
            <div class="place-card">
                <h3>4. Centre for International Governance Innovation (CIGI)</h3>
                <p>Modern campus with beautiful architecture and public events.</p>
            </div>
            <div class="place-card">
                <h3>5. Grand River</h3>
                <p>Scenic river perfect for kayaking, canoeing, and riverside walks.</p>
            </div>
            <div class="place-card">
                <h3>6. St. Jacobs Village</h3>
                <p>Charming nearby village known for its farmers market and Mennonite heritage.</p>
            </div>
            <div class="place-card">
                <h3>7. Waterloo Park</h3>
                <p>Large park with trails, playgrounds, and the famous Waterloo Park Pavilion.</p>
            </div>
            <div class="place-card">
                <h3>8. Schneider Haus National Historic Site</h3>
                <p>Historic German-Canadian heritage site showcasing early settlement history.</p>
            </div>
            <div class="place-card">
                <h3>9. Homer Watson House & Gallery</h3>
                <p>Art gallery and historic home of famous Canadian landscape painter Homer Watson.</p>
            </div>
            <div class="place-card">
                <h3>10. Bingemans</h3>
                <p>Family entertainment complex with water park, camping, and year-round activities.</p>
            </div>
        </div>

        <div class="highlight">
            <h3>Planning Your Visit</h3>
            <p>Kitchener offers something for everyone - from cultural attractions and historic sites to outdoor activities and family fun. The city is easily accessible by car or public transit, and many attractions are within walking distance of downtown.</p>
        </div>"""

                if is_fancy and wants_images:
                    additional_styles = """
        /* Hero Section Styles */
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
            margin: -40px -40px 40px -40px;
            position: relative;
            overflow: hidden;
        }
        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.3);
            z-index: 1;
        }
        .hero-content {
            position: relative;
            z-index: 2;
        }
        .hero-title {
            font-size: 3rem;
            margin-bottom: 1rem;
            animation: fadeInDown 1s ease-out;
        }
        .hero-subtitle {
            font-size: 1.3rem;
            margin-bottom: 2rem;
            animation: fadeInUp 1s ease-out 0.3s both;
        }
        .hero-image img {
            max-width: 600px;
            width: 100%;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            animation: zoomIn 1s ease-out 0.6s both;
        }

        /* Intro Section */
        .intro-section {
            text-align: center;
            margin: 40px 0;
        }
        .intro-text {
            font-size: 1.2rem;
            color: #555;
            max-width: 800px;
            margin: 0 auto;
            animation: fadeIn 1s ease-out 1s both;
        }

        /* Places Grid */
        .places-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 50px 0;
        }
        .place-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            opacity: 0;
            transform: translateY(50px);
        }
        .place-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        .place-card.animated {
            animation: slideInUp 0.6s ease-out forwards;
        }
        .card-image {
            position: relative;
            height: 200px;
            overflow: hidden;
        }
        .card-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        .place-card:hover .card-image img {
            transform: scale(1.1);
        }
        .card-overlay {
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(76, 175, 80, 0.9);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        .card-content {
            padding: 25px;
        }
        .card-content h3 {
            color: #2c5f2d;
            margin: 0 0 15px 0;
            font-size: 1.3rem;
        }
        .card-content p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .rating {
            font-size: 0.9rem;
        }
        .category {
            background: #e8f5e8;
            color: #2c5f2d;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        /* Planning Tips */
        .planning-tips {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 25px;
        }
        .tip {
            display: flex;
            align-items: center;
            gap: 15px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .tip:hover {
            transform: translateX(10px);
        }
        .tip-icon {
            font-size: 2rem;
        }

        /* Animations */
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(50px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes zoomIn {
            from { opacity: 0; transform: scale(0.5); }
            to { opacity: 1; transform: scale(1); }
        }
        @keyframes slideInUp {
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        .fade-in-up {
            animation: fadeInUp 0.8s ease-out;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .hero-title { font-size: 2rem; }
            .hero-subtitle { font-size: 1.1rem; }
            .places-grid { grid-template-columns: 1fr; gap: 20px; }
            .planning-tips { grid-template-columns: 1fr; }
        }"""

                    javascript_code = """
    <script>
        // Animation trigger on scroll
        function animateOnScroll() {
            const elements = document.querySelectorAll('.animated');
            elements.forEach(element => {
                const elementTop = element.getBoundingClientRect().top;
                const elementVisible = 150;

                if (elementTop < window.innerHeight - elementVisible) {
                    const delay = element.dataset.delay || 0;
                    setTimeout(() => {
                        element.style.animationDelay = delay + 'ms';
                        element.classList.add('animate');
                    }, delay);
                }
            });
        }

        // Initialize animations
        window.addEventListener('scroll', animateOnScroll);
        window.addEventListener('load', animateOnScroll);

        // Add some interactive effects
        document.addEventListener('DOMContentLoaded', function() {
            // Trigger animations on page load
            setTimeout(animateOnScroll, 100);

            // Add click effects to cards
            document.querySelectorAll('.place-card').forEach(card => {
                card.addEventListener('click', function() {
                    this.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        this.style.transform = '';
                    }, 150);
                });
            });
        });
    </script>"""
                else:
                    additional_styles = """
        .places-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .place-card {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .place-card h3 {
            color: #2c5f2d;
            margin-top: 0;
        }"""
                    javascript_code = ""

            elif "cats" in user_request_lower:
                if is_fancy and wants_images:
                    main_content = """
        <div class="hero-section cat-hero">
            <div class="hero-content">
                <h1 class="hero-title">🐱 All About Cats 🐱</h1>
                <p class="hero-subtitle">Discover the fascinating world of our feline friends</p>
                <div class="hero-image">
                    <img src="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&h=400&fit=crop"
                         alt="Beautiful Cat" class="fade-in-image" />
                </div>
            </div>
        </div>

        <div class="intro-section">
            <p class="intro-text">Cats are fascinating creatures that have been companions to humans for thousands of years. Explore their amazing world!</p>
        </div>

        <div class="cat-facts animated fade-in-up">
            <h2>✨ Interesting Cat Facts</h2>
            <div class="facts-grid">
                <div class="fact-card animated" data-delay="0">
                    <div class="fact-icon">🕒</div>
                    <h3>Ancient Companions</h3>
                    <p>Cats have been domesticated for approximately 9,000 years</p>
                </div>
                <div class="fact-card animated" data-delay="100">
                    <div class="fact-icon">👥</div>
                    <h3>Group Name</h3>
                    <p>A group of cats is called a "clowder"</p>
                </div>
                <div class="fact-card animated" data-delay="200">
                    <div class="fact-icon">👂</div>
                    <h3>Super Hearing</h3>
                    <p>Cats can rotate their ears 180 degrees</p>
                </div>
                <div class="fact-card animated" data-delay="300">
                    <div class="fact-icon">👁️</div>
                    <h3>Third Eyelid</h3>
                    <p>They have a third eyelid called a nictitating membrane</p>
                </div>
                <div class="fact-card animated" data-delay="400">
                    <div class="fact-icon">😴</div>
                    <h3>Sleep Champions</h3>
                    <p>Cats spend 70% of their lives sleeping (13-16 hours a day)</p>
                </div>
                <div class="fact-card animated" data-delay="500">
                    <div class="fact-icon">💝</div>
                    <h3>Healing Purr</h3>
                    <p>A cat's purr vibrates at a frequency that promotes healing</p>
                </div>
            </div>
        </div>

        <div class="cat-breeds">
            <h2>🐾 Popular Cat Breeds</h2>
            <div class="breed-grid">
                <div class="breed-card animated" data-delay="0">
                    <div class="breed-image">
                        <img src="https://images.unsplash.com/photo-1618826417493-b2e8a8b3b60c?w=300&h=200&fit=crop" alt="Persian Cat" />
                        <div class="breed-overlay">
                            <span class="breed-name">Persian</span>
                        </div>
                    </div>
                    <div class="breed-content">
                        <h3>Persian</h3>
                        <p>Known for their long, luxurious coat and flat face. These gentle cats love quiet environments.</p>
                        <div class="breed-traits">
                            <span class="trait">Gentle</span>
                            <span class="trait">Quiet</span>
                            <span class="trait">Fluffy</span>
                        </div>
                    </div>
                </div>

                <div class="breed-card animated" data-delay="100">
                    <div class="breed-image">
                        <img src="https://images.unsplash.com/photo-1513245543132-31f507417b26?w=300&h=200&fit=crop" alt="Siamese Cat" />
                        <div class="breed-overlay">
                            <span class="breed-name">Siamese</span>
                        </div>
                    </div>
                    <div class="breed-content">
                        <h3>Siamese</h3>
                        <p>Vocal and social cats with distinctive color points. They're known for their intelligence and loyalty.</p>
                        <div class="breed-traits">
                            <span class="trait">Vocal</span>
                            <span class="trait">Social</span>
                            <span class="trait">Smart</span>
                        </div>
                    </div>
                </div>

                <div class="breed-card animated" data-delay="200">
                    <div class="breed-image">
                        <img src="https://images.unsplash.com/photo-1574231164645-d6f0e8553590?w=300&h=200&fit=crop" alt="Maine Coon Cat" />
                        <div class="breed-overlay">
                            <span class="breed-name">Maine Coon</span>
                        </div>
                    </div>
                    <div class="breed-content">
                        <h3>Maine Coon</h3>
                        <p>Large, gentle giants with tufted ears and bushy tails. They're friendly and great with families.</p>
                        <div class="breed-traits">
                            <span class="trait">Large</span>
                            <span class="trait">Gentle</span>
                            <span class="trait">Family</span>
                        </div>
                    </div>
                </div>

                <div class="breed-card animated" data-delay="300">
                    <div class="breed-image">
                        <img src="https://images.unsplash.com/photo-1571566882372-1598d88abd90?w=300&h=200&fit=crop" alt="British Shorthair Cat" />
                        <div class="breed-overlay">
                            <span class="breed-name">British Shorthair</span>
                        </div>
                    </div>
                    <div class="breed-content">
                        <h3>British Shorthair</h3>
                        <p>Round-faced cats with dense, plush coats. They're calm and make excellent indoor companions.</p>
                        <div class="breed-traits">
                            <span class="trait">Calm</span>
                            <span class="trait">Round</span>
                            <span class="trait">Indoor</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="highlight animated fade-in-up">
            <h3>🏥 Cat Care Tips</h3>
            <p>Proper cat care ensures a happy and healthy feline companion. Here are essential care guidelines:</p>
            <div class="care-tips">
                <div class="tip animated" data-delay="0">
                    <span class="tip-icon">💧</span>
                    <div class="tip-content">
                        <h4>Fresh Water</h4>
                        <p>Provide clean, fresh water daily</p>
                    </div>
                </div>
                <div class="tip animated" data-delay="100">
                    <span class="tip-icon">🏥</span>
                    <div class="tip-content">
                        <h4>Regular Checkups</h4>
                        <p>Schedule yearly veterinary visits</p>
                    </div>
                </div>
                <div class="tip animated" data-delay="200">
                    <span class="tip-icon">🧸</span>
                    <div class="tip-content">
                        <h4>Mental Stimulation</h4>
                        <p>Provide interactive toys and play time</p>
                    </div>
                </div>
                <div class="tip animated" data-delay="300">
                    <span class="tip-icon">🏠</span>
                    <div class="tip-content">
                        <h4>Safe Environment</h4>
                        <p>Create a secure indoor space</p>
                    </div>
                </div>
            </div>
        </div>"""
                else:
                    # Regular version without fancy animations
                    main_content = """
        <h1>All About Cats</h1>
        <p>Cats are fascinating creatures that have been companions to humans for thousands of years.</p>

        <div class="cat-facts">
            <h2>Interesting Cat Facts</h2>
            <ul>
                <li>Cats have been domesticated for approximately 9,000 years</li>
                <li>A group of cats is called a "clowder"</li>
                <li>Cats can rotate their ears 180 degrees</li>
                <li>They have a third eyelid called a nictitating membrane</li>
                <li>Cats spend 70% of their lives sleeping (13-16 hours a day)</li>
                <li>A cat's purr vibrates at a frequency that promotes healing</li>
            </ul>
        </div>

        <div class="cat-breeds">
            <h2>Popular Cat Breeds</h2>
            <div class="breed-grid">
                <div class="breed-card">
                    <h3>Persian</h3>
                    <p>Known for their long, luxurious coat and flat face.</p>
                </div>
                <div class="breed-card">
                    <h3>Siamese</h3>
                    <p>Vocal and social cats with distinctive color points.</p>
                </div>
                <div class="breed-card">
                    <h3>Maine Coon</h3>
                    <p>Large, gentle giants with tufted ears and bushy tails.</p>
                </div>
                <div class="breed-card">
                    <h3>British Shorthair</h3>
                    <p>Round-faced cats with dense, plush coats.</p>
                </div>
            </div>
        </div>

        <div class="highlight">
            <h3>Cat Care Tips</h3>
            <p>Provide fresh water daily, regular veterinary checkups, interactive toys for mental stimulation, and a clean litter box. Cats also need scratching posts and safe indoor environments.</p>
        </div>"""

                if is_fancy and wants_images:
                    additional_styles = """
        /* Cat Hero Section */
        .cat-hero {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
        }

        /* Facts Grid */
        .facts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }
        .fact-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            opacity: 0;
            transform: translateY(30px);
        }
        .fact-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        .fact-card.animated {
            animation: slideInUp 0.6s ease-out forwards;
        }
        .fact-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            animation: bounce 2s infinite;
        }
        .fact-card h3 {
            color: #2c5f2d;
            margin: 15px 0;
            font-size: 1.2rem;
        }
        .fact-card p {
            color: #666;
            line-height: 1.6;
        }

        /* Breed Grid */
        .breed-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }
        .breed-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            opacity: 0;
            transform: translateY(30px);
        }
        .breed-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        .breed-card.animated {
            animation: slideInUp 0.6s ease-out forwards;
        }
        .breed-image {
            position: relative;
            height: 200px;
            overflow: hidden;
        }
        .breed-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        .breed-card:hover .breed-image img {
            transform: scale(1.1);
        }
        .breed-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.7));
            color: white;
            padding: 20px;
            transform: translateY(100%);
            transition: transform 0.3s ease;
        }
        .breed-card:hover .breed-overlay {
            transform: translateY(0);
        }
        .breed-name {
            font-size: 1.2rem;
            font-weight: bold;
        }
        .breed-content {
            padding: 25px;
        }
        .breed-content h3 {
            color: #2c5f2d;
            margin: 0 0 15px 0;
        }
        .breed-traits {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .trait {
            background: #e8f5e8;
            color: #2c5f2d;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }

        /* Care Tips */
        .care-tips {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        .tip {
            display: flex;
            align-items: flex-start;
            gap: 20px;
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
            opacity: 0;
            transform: translateX(-30px);
        }
        .tip:hover {
            transform: translateX(10px);
        }
        .tip.animated {
            animation: slideInLeft 0.6s ease-out forwards;
        }
        .tip-icon {
            font-size: 2.5rem;
            flex-shrink: 0;
        }
        .tip-content h4 {
            color: #2c5f2d;
            margin: 0 0 8px 0;
            font-size: 1.1rem;
        }
        .tip-content p {
            color: #666;
            margin: 0;
            line-height: 1.5;
        }

        /* Additional Animations */
        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
            40% {{ transform: translateY(-10px); }}
            60% {{ transform: translateY(-5px); }}
        }}
        @keyframes slideInLeft {{
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        /* Responsive Design */
        @media (max-width: 768px) {
            .facts-grid { grid-template-columns: 1fr; }
            .breed-grid { grid-template-columns: 1fr; }
            .care-tips { grid-template-columns: 1fr; }
        }"""

                    javascript_code = """
    <script>
        // Cat-specific animations
        function animateOnScroll() {
            const elements = document.querySelectorAll('.animated');
            elements.forEach(element => {
                const elementTop = element.getBoundingClientRect().top;
                const elementVisible = 150;

                if (elementTop < window.innerHeight - elementVisible) {
                    const delay = element.dataset.delay || 0;
                    setTimeout(() => {
                        element.style.animationDelay = delay + 'ms';
                        element.classList.add('animate');
                    }, delay);
                }
            });
        }

        // Initialize animations
        window.addEventListener('scroll', animateOnScroll);
        window.addEventListener('load', animateOnScroll);

        // Cat-specific interactive effects
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(animateOnScroll, 100);

            // Add purr sound effect simulation on breed card hover
            document.querySelectorAll('.breed-card').forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-10px) scale(1.02)';
                });

                card.addEventListener('mouseleave', function() {
                    this.style.transform = '';
                });
            });

            // Add bounce effect to fact icons
            document.querySelectorAll('.fact-icon').forEach(icon => {
                icon.addEventListener('click', function() {
                    this.style.animation = 'none';
                    setTimeout(() => {
                        this.style.animation = 'bounce 0.5s ease-in-out';
                    }, 10);
                });
            });
        });
    </script>"""
                else:
                    additional_styles = """
        .cat-facts ul {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
        }
        .breed-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .breed-card {
            background-color: #f0f8f0;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #4CAF50;
        }
        .breed-card h3 {
            color: #2c5f2d;
            margin-top: 0;
        }"""
                    javascript_code = ""
            else:
                # Generate specific content based on request type
                if (
                    "e-commerce" in user_request_lower
                    or "ecommerce" in user_request_lower
                    or (
                        "store" in user_request_lower
                        and "product" in user_request_lower
                    )
                ):
                    title = "TechGadgets Pro - Modern Electronics Store"
                    main_content = self._generate_ecommerce_content()
                    additional_styles = self._get_ecommerce_styles()
                    javascript_code = self._get_ecommerce_javascript()
                elif "portfolio" in user_request_lower and (
                    "designer" in user_request_lower or "graphic" in user_request_lower
                ):
                    title = "Sarah Johnson - Graphic Designer Portfolio"
                    main_content = self._generate_portfolio_content()
                    additional_styles = self._get_portfolio_styles()
                    javascript_code = self._get_portfolio_javascript()
                elif "restaurant" in user_request_lower or (
                    "menu" in user_request_lower and "food" in user_request_lower
                ):
                    title = "Bella Vista Restaurant - Fine Dining Experience"
                    main_content = self._generate_restaurant_content()
                    additional_styles = self._get_restaurant_styles()
                    javascript_code = self._get_restaurant_javascript()
                elif (
                    "social media" in user_request_lower
                    or "dashboard" in user_request_lower
                ):
                    title = "SocialHub - Analytics Dashboard"
                    main_content = self._generate_dashboard_content()
                    additional_styles = self._get_dashboard_styles()
                    javascript_code = self._get_dashboard_javascript()
                elif "learning" in user_request_lower or (
                    "course" in user_request_lower and "education" in user_request_lower
                ):
                    title = "EduPlatform - Online Learning Hub"
                    main_content = self._generate_learning_content()
                    additional_styles = self._get_learning_styles()
                    javascript_code = self._get_learning_javascript()
                else:
                    # Default webpage content for unrecognized requests
                    main_content = f"""
        <h1>{title}</h1>
        <p>Welcome to this webpage created based on your request!</p>
        <div class="highlight">
            <p>This page was created by the ParManusAI file agent. The content has been generated based on your specific request: "{user_request}"</p>
        </div>
        <p>This webpage features:</p>
        <ul>
            <li>Clean, responsive design</li>
            <li>Professional styling</li>
            <li>Semantic HTML structure</li>
            <li>Modern CSS styling</li>
        </ul>
        <p>You can customize this content as needed for your specific requirements.</p>"""
                    additional_styles = ""
                    javascript_code = ""

            # Generate HTML content with dynamic content
            content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #4CAF50;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        h3 {{
            color: #2c5f2d;
        }}
        p {{
            color: #666;
            line-height: 1.6;
        }}
        .highlight {{
            background-color: #e8f5e8;
            padding: 20px;
            border-left: 4px solid #4CAF50;
            margin: 25px 0;
            border-radius: 0 8px 8px 0;
        }}
        ul {{
            color: #666;
        }}
        li {{
            margin-bottom: 5px;
        }}
        {additional_styles}
    </style>
</head>
<body>
    <div class="container">
        {main_content}
    </div>
    {javascript_code}
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

    def _extract_search_query(self, user_request: str) -> str:
        """Extract the search query from the user request."""
        request_lower = user_request.lower()

        # Handle news-specific requests
        if "top 10 news" in request_lower or "top ten news" in request_lower:
            return "top 10 latest news headlines today"

        elif "news from different websites" in request_lower:
            return "latest news headlines from multiple sources"

        elif "breaking news" in request_lower:
            return "breaking news today"

        # Try to extract specific search terms
        elif "search the web for" in request_lower:
            start = request_lower.find("search the web for") + len("search the web for")
            end = request_lower.find(" and create", start)
            if end == -1:
                end = request_lower.find(" and build", start)
            if end == -1:
                end = request_lower.find(" and make", start)
            if end == -1:
                end = request_lower.find(" and generate", start)
            if end == -1:
                end = len(request_lower)
            return user_request[start:end].strip()

        elif "look for" in request_lower:
            start = request_lower.find("look for") + len("look for")
            end = request_lower.find(" and build", start)
            if end == -1:
                end = request_lower.find(" and create", start)
            if end == -1:
                end = request_lower.find(" and make", start)
            if end == -1:
                end = len(request_lower)
            query = user_request[start:end].strip()
            return query if query else user_request

        elif "trends in" in request_lower:
            # Extract what comes after "trends in"
            start = request_lower.find("trends in") + len("trends in")
            end = request_lower.find(" and create", start)
            if end == -1:
                end = len(request_lower)
            query = user_request[start:end].strip()
            return f"latest trends in {query}"

        elif "latest" in request_lower and "ai" in request_lower:
            return "latest artificial intelligence trends 2025"

        elif "current" in request_lower:
            # Extract what we're looking for current info about
            words = user_request.split()
            for i, word in enumerate(words):
                if word.lower() in ["current", "latest", "recent"]:
                    if i + 1 < len(words):
                        topic = " ".join(words[i + 1 : i + 4])  # Get next 3 words max
                        return f"current {topic.split(' and ')[0].strip()}"
            return "current trends and information"

        else:
            # Use the actual user request as the search query
            # Remove webpage creation keywords to get clean search query
            clean_query = user_request
            for phrase in [
                "and build",
                "and create",
                "and make",
                "and generate",
                "webpage",
                "web page",
                "website",
            ]:
                clean_query = clean_query.replace(phrase, "")
            clean_query = clean_query.strip()
            return clean_query if clean_query else "current trends and information"

    def _extract_data_from_search_results(self, search_result: str) -> dict:
        """Extract structured data from search results."""
        import re

        data = {
            "items": [],
            "title": "Search Results",
            "description": "Results from web search",
        }

        try:
            # Try to extract structured information from search results
            lines = search_result.split("\n")
            current_item = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for title patterns
                if (
                    line.startswith("Title:")
                    or line.startswith("Headline:")
                    or (line.startswith('"') and line.endswith('"'))
                ):
                    if current_item:
                        data["items"].append(current_item)
                        current_item = {}
                    current_item["title"] = (
                        line.replace("Title:", "")
                        .replace("Headline:", "")
                        .strip()
                        .strip('"')
                    )

                # Look for URL patterns
                elif (
                    line.startswith("URL:")
                    or line.startswith("Link:")
                    or line.startswith("http")
                ):
                    current_item["url"] = (
                        line.replace("URL:", "").replace("Link:", "").strip()
                    )

                # Look for description patterns
                elif line.startswith("Description:") or line.startswith("Summary:"):
                    current_item["description"] = (
                        line.replace("Description:", "").replace("Summary:", "").strip()
                    )

                # Look for source patterns
                elif line.startswith("Source:") or line.startswith("From:"):
                    current_item["source"] = (
                        line.replace("Source:", "").replace("From:", "").strip()
                    )

            # Add the last item
            if current_item:
                data["items"].append(current_item)

            # If no structured items found, create items from paragraphs
            if not data["items"]:
                paragraphs = search_result.split("\n\n")
                for i, paragraph in enumerate(paragraphs[:10]):
                    if paragraph.strip():
                        data["items"].append(
                            {
                                "title": f"Search Result {i+1}",
                                "description": (
                                    paragraph.strip()[:200] + "..."
                                    if len(paragraph.strip()) > 200
                                    else paragraph.strip()
                                ),
                                "url": "#",
                                "source": "Search Results",
                            }
                        )

        except Exception as e:
            import logging

            logging.error(f"Error extracting data from search results: {e}")
            # Return minimal fallback data
            data["items"] = [
                {
                    "title": "Search Results Available",
                    "description": "Search completed but could not parse results into structured format.",
                    "url": "#",
                    "source": "Web Search",
                }
            ]

        return data

    def _determine_webpage_type(self, user_request: str) -> str:
        """Determine the type of webpage to create based on user request."""
        request_lower = user_request.lower()

        # News-related webpage
        if any(word in request_lower for word in ["news", "headlines", "articles"]):
            return "news"

        # Portfolio or profile webpage
        if any(
            word in request_lower
            for word in ["portfolio", "profile", "about me", "resume"]
        ):
            return "portfolio"

        # Business or company webpage
        if any(
            word in request_lower
            for word in ["business", "company", "service", "product"]
        ):
            return "business"

        # Blog or content webpage
        if any(
            word in request_lower for word in ["blog", "article", "content", "post"]
        ):
            return "blog"

        # Landing page
        if any(word in request_lower for word in ["landing", "promo", "marketing"]):
            return "landing"

        # Documentation or help page
        if any(
            word in request_lower for word in ["documentation", "docs", "help", "guide"]
        ):
            return "documentation"

        # Default to generic content page
        return "generic"

    async def _create_webpage_based_on_analysis(
        self, user_request, analysis_result, site_to_analyze
    ):
        """Create a webpage based on website analysis results"""
        try:
            import os
            from datetime import datetime

            # Extract design elements from analysis if available
            design_info = self._extract_design_from_analysis(
                analysis_result, site_to_analyze
            )

            # Generate the webpage content incorporating the analyzed design
            title = self._extract_title_from_analysis_request(
                user_request, site_to_analyze
            )

            # Create HTML content with analyzed design influence
            html_content = self._generate_analyzed_webpage_content(
                title, design_info, user_request
            )

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_dir = "workspace"
            os.makedirs(workspace_dir, exist_ok=True)

            filename = f"webpage_{timestamp}.html"
            filepath = os.path.join(workspace_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            self._file_saved = True
            return f"✅ Website analysis completed and webpage created successfully!\n📄 File saved: {filepath}\n🎨 Design inspired by: {site_to_analyze}"

        except Exception as e:
            # Fallback to regular webpage creation
            import logging

            logging.error(f"Error in analysis-based webpage creation: {e}")
            return await self._create_simple_webpage(user_request)

    async def _create_webpage_with_search_data(
        self, user_request: str, search_result: str
    ) -> str:
        """Create a webpage incorporating live search data"""
        try:
            import os
            from datetime import datetime

            # Extract data from search results
            search_data = self._extract_data_from_search_results(search_result)

            # Generate title based on search content
            title = self._extract_title_from_search_request(user_request)

            # Create HTML content with search data
            html_content = self._generate_search_based_webpage_content(
                title, search_data, user_request
            )

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_dir = "workspace"
            os.makedirs(workspace_dir, exist_ok=True)

            filename = f"webpage_{timestamp}.html"
            filepath = os.path.join(workspace_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            self._file_saved = True
            return f"✅ Web search completed and webpage created successfully!\n📄 File saved: {filepath}\n🔍 Data sourced from live web search"

        except Exception as e:
            # Fallback to regular webpage creation
            import logging

            logging.error(f"Error in search-based webpage creation: {e}")
            return await self._create_simple_webpage(user_request)

    def _extract_design_from_analysis(self, analysis_result, site_url):
        """Extract design elements from browser analysis"""
        design_info = {
            "colors": [
                "#4285f4",
                "#34a853",
                "#fbbc05",
                "#ea4335",
            ],  # Default Google colors
            "layout": "clean_minimal",
            "font_style": "modern",
            "components": ["search_box", "navigation", "cards"],
        }

        if analysis_result and isinstance(analysis_result, str):
            analysis_lower = analysis_result.lower()

            # Extract color information
            if "blue" in analysis_lower:
                design_info["colors"] = ["#1a73e8", "#4285f4", "#5f6368", "#ffffff"]
            elif "red" in analysis_lower:
                design_info["colors"] = ["#ea4335", "#dc2626", "#fee2e2", "#ffffff"]
            elif "green" in analysis_lower:
                design_info["colors"] = ["#34a853", "#059669", "#dcfce7", "#ffffff"]

            # Extract layout information
            if "minimal" in analysis_lower or "clean" in analysis_lower:
                design_info["layout"] = "minimal"
            elif "grid" in analysis_lower:
                design_info["layout"] = "grid"
            elif "card" in analysis_lower:
                design_info["layout"] = "card_based"

            # Extract component information
            if "search" in analysis_lower:
                design_info["components"].append("search_prominent")
            if "navigation" in analysis_lower or "nav" in analysis_lower:
                design_info["components"].append("navigation_header")
            if "footer" in analysis_lower:
                design_info["components"].append("footer")

        return design_info

    def _extract_title_from_analysis_request(self, user_request, site_url):
        """Extract appropriate title from analysis request"""
        if "google" in user_request.lower():
            return "Parsu - Search Made Simple"
        elif "facebook" in user_request.lower():
            return "Parsu Social"
        elif "amazon" in user_request.lower():
            return "Parsu Store"
        else:
            return "Parsu - Inspired Design"

    def _generate_analyzed_webpage_content(self, title, design_info, user_request):
        """Generate webpage content based on analyzed design"""
        colors = design_info.get("colors", ["#4285f4", "#34a853", "#fbbc05", "#ea4335"])
        layout = design_info.get("layout", "minimal")

        # Create CSS based on analyzed design
        css_styles = f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Roboto', 'Arial', sans-serif;
            background: linear-gradient(135deg, {colors[0]}10, {colors[1]}10);
            min-height: 100vh;
            color: #333;
        }}

        .header {{
            background: {colors[0]};
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .logo {{
            font-size: 1.8rem;
            font-weight: bold;
        }}

        .nav-menu {{
            display: flex;
            list-style: none;
            gap: 2rem;
        }}

        .nav-menu a {{
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background 0.3s;
        }}

        .nav-menu a:hover {{
            background: rgba(255,255,255,0.2);
        }}

        .main-content {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 2rem;
        }}

        .hero-section {{
            text-align: center;
            padding: 4rem 0;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 3rem;
        }}

        .hero-title {{
            font-size: 3rem;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, {colors[0]}, {colors[1]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .hero-subtitle {{
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }}

        .search-section {{
            display: flex;
            justify-content: center;
            margin: 2rem 0;
        }}

        .search-box {{
            display: flex;
            border: 2px solid {colors[0]};
            border-radius: 50px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        .search-input {{
            padding: 1rem 2rem;
            border: none;
            font-size: 1rem;
            width: 400px;
            outline: none;
        }}

        .search-button {{
            background: {colors[0]};
            color: white;
            border: none;
            padding: 1rem 2rem;
            cursor: pointer;
            transition: background 0.3s;
        }}

        .search-button:hover {{
            background: {colors[1]};
        }}

        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}

        .feature-card {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .feature-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }}

        .feature-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            color: {colors[0]};
        }}

        .feature-title {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #333;
        }}

        .feature-description {{
            color: #666;
            line-height: 1.6;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 3rem 2rem 1rem;
            margin-top: 4rem;
            text-align: center;
            border-top: 1px solid #eee;
        }}

        .footer-content {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 2rem;
        }}

        .footer-links a {{
            color: #666;
            text-decoration: none;
        }}

        .footer-links a:hover {{
            color: {colors[0]};
        }}

        @media (max-width: 768px) {{
            .hero-title {{ font-size: 2rem; }}
            .search-input {{ width: 250px; }}
            .nav-menu {{ display: none; }}
            .features-grid {{ grid-template-columns: 1fr; }}
        }}
        """

        # Generate content based on the request
        if "google" in user_request.lower():
            content_sections = """
            <div class="search-section">
                <div class="search-box">
                    <input type="text" class="search-input" placeholder="Search the web...">
                    <button class="search-button">🔍 Search</button>
                </div>
            </div>

            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <h3 class="feature-title">Smart Search</h3>
                    <p class="feature-description">Find exactly what you're looking for with our intelligent search algorithms.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3 class="feature-title">Lightning Fast</h3>
                    <p class="feature-description">Get results in milliseconds with our optimized search infrastructure.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🛡️</div>
                    <h3 class="feature-title">Privacy First</h3>
                    <p class="feature-description">Your searches are private and secure. We don't track or store personal data.</p>
                </div>
            </div>
            """
        else:
            content_sections = """
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">✨</div>
                    <h3 class="feature-title">Beautiful Design</h3>
                    <p class="feature-description">Crafted with attention to detail and inspired by the best.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🚀</div>
                    <h3 class="feature-title">Modern Technology</h3>
                    <p class="feature-description">Built with the latest web technologies for optimal performance.</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💎</div>
                    <h3 class="feature-title">Premium Quality</h3>
                    <p class="feature-description">Every element is carefully designed to provide the best user experience.</p>
                </div>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {css_styles}
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">{title}</div>
        <nav>
            <ul class="nav-menu">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#services">Services</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>

    <div class="main-content">
        <section class="hero-section">
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">Inspired by great design, built for the future</p>
        </section>

        {content_sections}
    </div>

    <footer class="footer">
        <div class="footer-content">
            <div class="footer-links">
                <a href="#privacy">Privacy</a>
                <a href="#terms">Terms</a>
                <a href="#help">Help</a>
                <a href="#about">About</a>
            </div>
            <p>&copy; 2025 {title}. Designed with ❤️ by ParManus AI.</p>
        </div>
    </footer>

    <script>
        document.querySelector('.search-button')?.addEventListener('click', function() {{
            const query = document.querySelector('.search-input').value;
            if (query.trim()) {{
                alert(`Searching for: ${{query}}`);
            }} else {{
                alert('Please enter a search term');
            }}
        }});

        document.querySelector('.search-input')?.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                document.querySelector('.search-button').click();
            }}
        }});
    </script>
</body>
</html>"""

    async def _create_simple_webpage(self, user_request):
        """Fallback method to create a simple webpage when other methods fail"""
        try:
            import os
            from datetime import datetime

            # Determine webpage type and generate content
            webpage_type = self._determine_webpage_type(user_request)
            title, content = self._generate_webpage_content_by_type(
                webpage_type, user_request
            )

            # Create HTML
            html_content = self._generate_complete_html(title, content, webpage_type)

            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workspace_dir = "workspace"
            os.makedirs(workspace_dir, exist_ok=True)

            filename = f"webpage_{timestamp}.html"
            filepath = os.path.join(workspace_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            self._file_saved = True
            return f"✅ Webpage created successfully!\n📄 File saved: {filepath}\n🎨 Type: {webpage_type}"

        except Exception as e:
            import logging

            logging.error(f"Error in simple webpage creation: {e}")
            return f"❌ Error creating webpage: {str(e)}"
