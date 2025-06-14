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

                # Run the browser agent to get search results
                search_result = await browser_agent.run()

                # Now create webpage with the search results
                return await self._create_webpage_with_search_data(
                    user_request, search_result
                )

            except Exception as e:
                # Log the exception for debugging
                import logging

                logging.error(f"Web search failed: {e}")
                # Fallback to creating webpage without live data
                pass

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

        # Try to extract specific search terms
        if "trends in" in request_lower:
            # Extract what comes after "trends in"
            start = request_lower.find("trends in") + len("trends in")
            end = request_lower.find(" and create", start)
            if end == -1:
                end = len(request_lower)
            query = user_request[start:end].strip()
            return f"latest trends in {query}"

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
            # Generic fallback
            return "current trends and information"

    async def _create_webpage_with_search_data(
        self, user_request: str, search_data: str
    ) -> str:
        """Create a webpage incorporating real search data."""
        import os
        from datetime import datetime

        user_request_lower = user_request.lower()

        # Extract the topic from the user request
        search_query = self._extract_search_query(user_request)

        # Generate appropriate title based on the search query
        if (
            "ai" in user_request_lower
            or "artificial intelligence" in user_request_lower
        ):
            title = "Latest AI Trends 2025"
            topic_emoji = "🤖"
            topic_description = "Latest AI and Technology Insights"
        elif "climate" in user_request_lower or "environment" in user_request_lower:
            title = "Climate & Environment News"
            topic_emoji = "🌍"
            topic_description = "Current Environmental and Climate Information"
        elif "technology" in user_request_lower or "tech" in user_request_lower:
            title = "Technology Trends & News"
            topic_emoji = "💻"
            topic_description = "Latest Technology Developments"
        elif "health" in user_request_lower or "medical" in user_request_lower:
            title = "Health & Medical News"
            topic_emoji = "🏥"
            topic_description = "Current Health and Medical Information"
        elif "business" in user_request_lower or "finance" in user_request_lower:
            title = "Business & Finance News"
            topic_emoji = "💼"
            topic_description = "Latest Business and Financial Insights"
        else:
            # Generic title based on search query
            title = f"Latest Information: {search_query.title()}"
            topic_emoji = "📊"
            topic_description = f"Web Research Results for: {search_query}"

        # Create content with search data
        html_content = f"""<!DOCTYPE html>
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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            animation: fadeInUp 0.6s ease-out;
        }}
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5em;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
        }}
        .search-info {{
            background: linear-gradient(45deg, #3498db, #2ecc71);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .trend-card {{
            background: #f8f9fa;
            border-left: 5px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .trend-card:hover {{
            transform: translateX(10px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .trend-number {{
            background: #3498db;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }}
        .search-data {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #bdc3c7;
        }}
        .data-title {{
            color: #2980b9;
            font-weight: bold;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{topic_emoji} {title}</h1>

        <div class="search-info">
            <h3>🔍 Live Web Search Results</h3>
            <p>{topic_description}</p>
            <p><strong>Search Query:</strong> {search_query}</p>
        </div>

        <div class="search-data">
            <div class="data-title">📊 Search Results Data:</div>
            <pre style="white-space: pre-wrap; font-family: inherit; max-height: 400px; overflow-y: auto;">{search_data[:3000]}{"..." if len(search_data) > 3000 else ""}</pre>
        </div>

        <div class="trend-card">
            <span class="trend-number">✅</span>
            <h3>Web Search Completed</h3>
            <p>Successfully gathered current information from the web and incorporated it into this webpage.</p>
        </div>

        <div class="trend-card">
            <span class="trend-number">🌐</span>
            <h3>Real-Time Data</h3>
            <p>This page contains the most recent information available on the web about your requested topic.</p>
        </div>

        <div class="trend-card">
            <span class="trend-number">🔄</span>
            <h3>Updated Information</h3>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} with fresh web search results.</p>
        </div>
    </div>
</body>
</html>"""
        # Save the HTML content to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"webpage_{timestamp}.html"
        file_path = os.path.join("workspace", filename)

        # Ensure workspace directory exists
        os.makedirs("workspace", exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Mark as saved
        self._file_saved = True

        return f"Html webpage created and saved to {os.path.abspath(file_path)}"

    async def _create_css_file(self, user_request: str) -> str:
        """Create a standalone CSS file based on user request."""
        import os
        from datetime import datetime

        user_request_lower = user_request.lower()

        # Determine CSS type and content
        css_content = ""
        filename_base = "styles"

        if (
            "navigation" in user_request_lower
            or "navbar" in user_request_lower
            or "menu" in user_request_lower
        ):
            filename_base = "navigation"
            css_content = """/* Modern Navigation CSS */
.navbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 2rem;
    position: fixed;
    top: 0;
    width: 100%;
    z-index: 1000;
    box-shadow: 0 2px 20px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}

.navbar.scrolled {
    background: rgba(102, 126, 234, 0.95);
    backdrop-filter: blur(10px);
    padding: 0.5rem 2rem;
}

.nav-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.nav-logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
    text-decoration: none;
    transition: transform 0.3s ease;
}

.nav-logo:hover {
    transform: scale(1.05);
}

.nav-menu {
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
    gap: 2rem;
}

.nav-item {
    position: relative;
}

.nav-link {
    color: white;
    text-decoration: none;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 25px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.nav-link::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: rgba(255,255,255,0.2);
    transition: left 0.3s ease;
    z-index: -1;
}

.nav-link:hover::before {
    left: 0;
}

.nav-link:hover {
    color: white;
    transform: translateY(-2px);
}

.nav-toggle {
    display: none;
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .nav-toggle {
        display: block;
    }

    .nav-menu {
        position: fixed;
        top: 70px;
        left: -100%;
        width: 100%;
        height: calc(100vh - 70px);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        padding-top: 2rem;
        transition: left 0.3s ease;
    }

    .nav-menu.active {
        left: 0;
    }

    .nav-item {
        margin: 1rem 0;
    }
}

/* Animation for mobile menu */
.nav-menu.active .nav-item {
    animation: slideInFromTop 0.5s ease forwards;
}

.nav-menu.active .nav-item:nth-child(1) { animation-delay: 0.1s; }
.nav-menu.active .nav-item:nth-child(2) { animation-delay: 0.2s; }
.nav-menu.active .nav-item:nth-child(3) { animation-delay: 0.3s; }
.nav-menu.active .nav-item:nth-child(4) { animation-delay: 0.4s; }

@keyframes slideInFromTop {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}"""

        elif "button" in user_request_lower or "btn" in user_request_lower:
            filename_base = "buttons"
            css_content = """/* Modern Button CSS Collection */

/* Primary Button */
.btn-primary {
    background: linear-gradient(45deg, #3498db, #2ecc71);
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 25px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.btn-primary::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, #2ecc71, #3498db);
    transition: left 0.3s ease;
    z-index: -1;
}

.btn-primary:hover::before {
    left: 0;
}

.btn-primary:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(52, 152, 219, 0.3);
}

.btn-primary:active {
    transform: translateY(-1px);
}

/* Glass Button */
.btn-glass {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 12px 30px;
    border-radius: 15px;
    font-size: 16px;
    cursor: pointer;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
    position: relative;
}

.btn-glass:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

/* Neon Button */
.btn-neon {
    background: transparent;
    border: 2px solid #ff6b6b;
    color: #ff6b6b;
    padding: 12px 30px;
    border-radius: 5px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.btn-neon:hover {
    background: #ff6b6b;
    color: white;
    box-shadow: 0 0 20px #ff6b6b, 0 0 40px #ff6b6b;
    text-shadow: 0 0 10px white;
}

/* 3D Button */
.btn-3d {
    background: linear-gradient(to bottom, #4CAF50, #45a049);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.1s ease;
    box-shadow: 0 6px 0 #3d8b40, 0 8px 15px rgba(0,0,0,0.3);
    position: relative;
    top: 0;
}

.btn-3d:hover {
    background: linear-gradient(to bottom, #5CBF60, #4CAF50);
}

.btn-3d:active {
    top: 4px;
    box-shadow: 0 2px 0 #3d8b40, 0 4px 8px rgba(0,0,0,0.3);
}

/* Ripple Effect Button */
.btn-ripple {
    background: #2196F3;
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transition: background 0.3s ease;
}

.btn-ripple:before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.5);
    transition: width 0.6s, height 0.6s;
    transform: translate(-50%, -50%);
    z-index: 0;
}

.btn-ripple:active:before {
    width: 300px;
    height: 300px;
}

/* Floating Action Button */
.btn-fab {
    width: 56px;
    height: 56px;
    background: #ff4757;
    border: none;
    border-radius: 50%;
    position: fixed;
    bottom: 20px;
    right: 20px;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(255, 71, 87, 0.4);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 24px;
}

.btn-fab:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(255, 71, 87, 0.6);
}

/* Loading Button */
.btn-loading {
    background: #6c5ce7;
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 25px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
}

.btn-loading.loading {
    pointer-events: none;
    opacity: 0.7;
}

.btn-loading.loading::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    margin: auto;
    border: 2px solid transparent;
    border-top-color: white;
    border-radius: 50%;
    animation: button-loading-spinner 1s ease infinite;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
}

@keyframes button-loading-spinner {
    from {
        transform: rotate(0turn);
    }
    to {
        transform: rotate(1turn);
    }
}"""

        elif "animation" in user_request_lower or "keyframe" in user_request_lower:
            filename_base = "animations"
            css_content = """/* CSS Animation Library */

/* Fade Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes fadeInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Scale Animations */
@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.3);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
}

@keyframes bounce {
    0%, 20%, 53%, 80%, 100% {
        animation-timing-function: cubic-bezier(0.215, 0.610, 0.355, 1.000);
        transform: translate3d(0,0,0);
    }
    40%, 43% {
        animation-timing-function: cubic-bezier(0.755, 0.050, 0.855, 0.060);
        transform: translate3d(0, -30px, 0);
    }
    70% {
        animation-timing-function: cubic-bezier(0.755, 0.050, 0.855, 0.060);
        transform: translate3d(0, -15px, 0);
    }
    90% {
        transform: translate3d(0,-4px,0);
    }
}

/* Rotation Animations */
@keyframes rotateIn {
    from {
        opacity: 0;
        transform: rotate(-200deg);
    }
    to {
        opacity: 1;
        transform: rotate(0);
    }
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

/* Slide Animations */
@keyframes slideInLeft {
    from {
        transform: translateX(-100%);
    }
    to {
        transform: translateX(0);
    }
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
    }
    to {
        transform: translateX(0);
    }
}

@keyframes slideInUp {
    from {
        transform: translateY(100%);
    }
    to {
        transform: translateY(0);
    }
}

@keyframes slideInDown {
    from {
        transform: translateY(-100%);
    }
    to {
        transform: translateY(0);
    }
}

/* Shake Animation */
@keyframes shake {
    0%, 100% {
        transform: translateX(0);
    }
    10%, 30%, 50%, 70%, 90% {
        transform: translateX(-10px);
    }
    20%, 40%, 60%, 80% {
        transform: translateX(10px);
    }
}

/* Wobble Animation */
@keyframes wobble {
    0% {
        transform: translateX(0%);
    }
    15% {
        transform: translateX(-25%) rotate(-5deg);
    }
    30% {
        transform: translateX(20%) rotate(3deg);
    }
    45% {
        transform: translateX(-15%) rotate(-3deg);
    }
    60% {
        transform: translateX(10%) rotate(2deg);
    }
    75% {
        transform: translateX(-5%) rotate(-1deg);
    }
    100% {
        transform: translateX(0%);
    }
}

/* Flip Animations */
@keyframes flipInX {
    from {
        transform: perspective(400px) rotateX(90deg);
        animation-timing-function: ease-in;
        opacity: 0;
    }
    40% {
        transform: perspective(400px) rotateX(-20deg);
        animation-timing-function: ease-in;
    }
    60% {
        transform: perspective(400px) rotateX(10deg);
        opacity: 1;
    }
    80% {
        transform: perspective(400px) rotateX(-5deg);
    }
    100% {
        transform: perspective(400px);
    }
}

@keyframes flipInY {
    from {
        transform: perspective(400px) rotateY(90deg);
        animation-timing-function: ease-in;
        opacity: 0;
    }
    40% {
        transform: perspective(400px) rotateY(-20deg);
        animation-timing-function: ease-in;
    }
    60% {
        transform: perspective(400px) rotateY(10deg);
        opacity: 1;
    }
    80% {
        transform: perspective(400px) rotateY(-5deg);
    }
    100% {
        transform: perspective(400px);
    }
}

/* Animation Classes */
.animate-fadeIn { animation: fadeIn 1s ease-in-out; }
.animate-fadeInUp { animation: fadeInUp 0.6s ease-out; }
.animate-fadeInDown { animation: fadeInDown 0.6s ease-out; }
.animate-fadeInLeft { animation: fadeInLeft 0.6s ease-out; }
.animate-fadeInRight { animation: fadeInRight 0.6s ease-out; }
.animate-scaleIn { animation: scaleIn 0.5s ease-out; }
.animate-pulse { animation: pulse 2s infinite; }
.animate-bounce { animation: bounce 2s infinite; }
.animate-rotateIn { animation: rotateIn 0.6s ease-out; }
.animate-spin { animation: spin 1s linear infinite; }
.animate-slideInLeft { animation: slideInLeft 0.5s ease-out; }
.animate-slideInRight { animation: slideInRight 0.5s ease-out; }
.animate-slideInUp { animation: slideInUp 0.5s ease-out; }
.animate-slideInDown { animation: slideInDown 0.5s ease-out; }
.animate-shake { animation: shake 0.82s cubic-bezier(.36,.07,.19,.97) both; }
.animate-wobble { animation: wobble 1s ease-in-out; }
.animate-flipInX { animation: flipInX 0.75s ease-in-out; }
.animate-flipInY { animation: flipInY 0.75s ease-in-out; }

/* Hover Effects */
.hover-grow { transition: transform 0.3s ease; }
.hover-grow:hover { transform: scale(1.05); }

.hover-shrink { transition: transform 0.3s ease; }
.hover-shrink:hover { transform: scale(0.95); }

.hover-rotate { transition: transform 0.3s ease; }
.hover-rotate:hover { transform: rotate(5deg); }

.hover-skew { transition: transform 0.3s ease; }
.hover-skew:hover { transform: skew(-5deg); }"""

        elif "card" in user_request_lower or "grid" in user_request_lower:
            filename_base = "cards"
            css_content = """/* Modern Card Components CSS */

/* Basic Card */
.card {
    background: white;
       border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    transition: all 0.3s ease;
    border: 1px solid #e2e8f0;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

/* Card with Image */
.card-image {
    border-radius: 12px;
    overflow: hidden;
    background: white;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.card-image:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-image img {
    width: 100%;
    height: 200px;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.card-image:hover img {
    transform: scale(1.05);
}

.card-content {
    padding: 1.5rem;
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #1a202c;
}

.card-description {
    color: #718096;
    line-height: 1.6;
    margin-bottom: 1rem;
}

/* Glass Card */
.card-glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 2rem;
    color: white;
    transition: all 0.3s ease;
}

.card-glass:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateY(-4px);
}

/* Gradient Card */
.card-gradient {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.card-gradient::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.card-gradient:hover::before {
    opacity: 1;
}

.card-gradient:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
}

.card-gradient * {
    position: relative;
    z-index: 1;
}

/* Card Grid Layout */
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    padding: 2rem;
}

/* Responsive Card Grid */
@media (max-width: 768px) {
    .card-grid {
        grid-template-columns: 1fr;
        padding: 1rem;
        gap: 1rem;
    }
}

/* Profile Card */
.profile-card {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    max-width: 300px;
    margin: 0 auto;
}

.profile-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.profile-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin: 0 auto 1rem;
    border: 4px solid #667eea;
    overflow: hidden;
}

.profile-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.profile-name {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #1a202c;
}

.profile-role {
    color: #667eea;
    font-weight: 500;
    margin-bottom: 1rem;
}

.profile-stats {
    display: flex;
    justify-content: space-around;
    padding: 1rem 0;
    border-top: 1px solid #e2e8f0;
}

.stat-item {
    text-align: center;
}

.stat-number {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1a202c;
}

.stat-label {
    font-size: 0.875rem;
    color: #718096;
}

/* Pricing Card */
.pricing-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    border: 2px solid #e2e8f0;
    transition: all 0.3s ease;
    position: relative;
}

.pricing-card.featured {
    border-color: #667eea;
    transform: scale(1.05);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
}

.pricing-card:hover {
    border-color: #667eea;
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.pricing-badge {
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    background: #667eea;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
}

.pricing-plan {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #1a202c;
}

.pricing-price {
    font-size: 3rem;
    font-weight: 700;
    color: #667eea;
    margin-bottom: 0.5rem;
}

.pricing-period {
    color: #718096;
    margin-bottom: 2rem;
}

.pricing-features {
    list-style: none;
    padding: 0;
    margin: 0 0 2rem 0;
}

.pricing-features li {
    padding: 0.5rem 0;
    color: #4a5568;
    position: relative;
    padding-left: 1.5rem;
}

.pricing-features li::before {
    content: '✓';
    position: absolute;
    left: 0;
    color: #667eea;
    font-weight: bold;
}

.pricing-button {
    width: 100%;
    background: #667eea;
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.pricing-button:hover {
    background: #5a67d8;
    transform: translateY(-2px);
}"""

        else:
            # Generic/Custom CSS based on request content
            filename_base = "custom"
            css_content = """/* Custom CSS File */

/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}

/* Container */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    margin-bottom: 1rem;
    font-weight: 600;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.75rem; }
h4 { font-size: 1.5rem; }
h5 { font-size: 1.25rem; }
h6 { font-size: 1rem; }

p {
    margin-bottom: 1rem;
}

/* Links */
a {
    color: #3498db;
    text-decoration: none;
    transition: color 0.3s ease;
}

a:hover {
    color: #2980b9;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 12px 24px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.3s ease;
    font-size: 16px;
}

.btn:hover {
    background: #2980b9;
    transform: translateY(-2px);
}

.btn-secondary {
    background: #95a5a6;
}

.btn-secondary:hover {
    background: #7f8c8d;
}

/* Grid System */
.row {
    display: flex;
    flex-wrap: wrap;
    margin: -10px;
}

.col {
    flex: 1;
    padding: 10px;
}

.col-1 { flex: 0 0 8.333%; }
.col-2 { flex: 0 0 16.666%; }
.col-3 { flex: 0 0 25%; }
.col-4 { flex: 0 0 33.333%; }
.col-6 { flex: 0 0 50%; }
.col-8 { flex: 0 0 66.666%; }
.col-9 { flex: 0 0 75%; }
.col-12 { flex: 0 0 100%; }

/* Utility Classes */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mt-3 { margin-top: 1.5rem; }
.mt-4 { margin-top: 2rem; }

.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
.mb-4 { margin-bottom: 2rem; }

.p-1 { padding: 0.5rem; }
.p-2 { padding: 1rem; }
.p-3 { padding: 1.5rem; }
.p-4 { padding: 2rem; }

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }

    .row {
        flex-direction: column;
    }

    .col,
    .col-1, .col-2, .col-3, .col-4,
    .col-6, .col-8, .col-9, .col-12 {
        flex: 0 0 100%;
    }

    h1 { font-size: 2rem; }
    h2 { font-size: 1.75rem; }
    h3 { font-size: 1.5rem; }
}"""

        # Create the CSS file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_base}_{timestamp}.css"

        workspace_dir = os.path.join(os.getcwd(), "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        file_path = os.path.join(workspace_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(css_content)

        self._file_saved = True

        return f"CSS file created and saved to {file_path}. The file contains {filename_base} styles with modern CSS techniques including animations, transitions, and responsive design."

    def _generate_ecommerce_content(self):
        return """
        <header class="header">
            <nav class="navbar">
                <div class="logo">TechGadgets Pro</div>
                <ul class="nav-menu">
                    <li><a href="#home">Home</a></li>
                    <li><a href="#products">Products</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
                <div class="cart-icon">🛒 <span class="cart-count">3</span></div>
            </nav>
        </header>

        <section class="hero">
            <div class="hero-content">
                <h1>Premium Electronics Store</h1>
                <p>Discover the latest technology and gadgets</p>
                <button class="cta-button">Shop Now</button>
            </div>
        </section>

        <section class="featured-products">
            <h2>Featured Products</h2>
            <div class="product-grid">
                <div class="product-card">
                    <div class="product-image">📱</div>
                    <h3>Smartphone Pro Max</h3>
                    <p class="price">$999.99</p>
                    <button class="add-to-cart">Add to Cart</button>
                </div>
                <div class="product-card">
                    <div class="product-image">💻</div>
                    <h3>Gaming Laptop</h3>
                    <p class="price">$1,299.99</p>
                    <button class="add-to-cart">Add to Cart</button>
                </div>
                <div class="product-card">
                    <div class="product-image">🎧</div>
                    <h3>Wireless Headphones</h3>
                    <p class="price">$199.99</p>
                    <button class="add-to-cart">Add to Cart</button>
                </div>
            </div>
        </section>

        <footer class="footer">
            <p>&copy; 2025 TechGadgets Pro. All rights reserved.</p>
        </footer>"""

    def _get_ecommerce_styles(self):
        return """
        .header { background: #1a1a1a; color: white; padding: 1rem 0; }
        .navbar { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
        .logo { font-size: 1.5rem; font-weight: bold; }
        .nav-menu { display: flex; list-style: none; gap: 2rem; margin: 0; padding: 0; }
        .nav-menu a { color: white; text-decoration: none; }
        .cart-icon { font-size: 1.2rem; }
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 4rem 2rem; }
        .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
        .cta-button { background: #ff6b6b; color: white; border: none; padding: 1rem 2rem; font-size: 1.1rem; border-radius: 5px; cursor: pointer; }
        .featured-products { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem; }
        .product-card { background: white; border-radius: 10px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; transition: transform 0.3s; }
        .product-card:hover { transform: translateY(-5px); }
        .product-image { font-size: 4rem; margin-bottom: 1rem; }
        .price { font-size: 1.5rem; color: #e74c3c; font-weight: bold; }
        .add-to-cart { background: #27ae60; color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 5px; cursor: pointer; }
        .footer { background: #1a1a1a; color: white; text-align: center; padding: 2rem; }"""

    def _get_ecommerce_javascript(self):
        return """
        let cartCount = 3;
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', function() {
                cartCount++;
                document.querySelector('.cart-count').textContent = cartCount;
                this.textContent = 'Added!';
                setTimeout(() => this.textContent = 'Add to Cart', 2000);
            });
        });"""

    def _generate_portfolio_content(self):
        return """
        <header class="portfolio-header">
            <nav class="portfolio-nav">
                <div class="portfolio-logo">Sarah Johnson</div>
                <ul class="portfolio-menu">
                    <li><a href="#home">Home</a></li>
                    <li><a href="#portfolio">Portfolio</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </header>

        <section class="portfolio-hero">
            <div class="hero-text">
                <h1>Creative Graphic Designer</h1>
                <p>Bringing your vision to life through innovative design</p>
                <button class="portfolio-cta">View My Work</button>
            </div>
        </section>

        <section class="portfolio-gallery">
            <h2>My Portfolio</h2>
            <div class="gallery-grid">
                <div class="gallery-item">🎨<h3>Brand Identity</h3><p>Logo & Brand Design</p></div>
                <div class="gallery-item">📱<h3>Mobile App UI</h3><p>User Interface Design</p></div>
                <div class="gallery-item">🌐<h3>Web Design</h3><p>Responsive Websites</p></div>
                <div class="gallery-item">📄<h3>Print Design</h3><p>Brochures & Flyers</p></div>
            </div>
        </section>

        <section class="contact-form">
            <h2>Get In Touch</h2>
            <form class="contact-form-container">
                <input type="text" placeholder="Your Name" required>
                <input type="email" placeholder="Your Email" required>
                <textarea placeholder="Your Message" rows="5" required></textarea>
                <button type="submit">Send Message</button>
            </form>
        </section>"""

    def _get_portfolio_styles(self):
        return """
        .portfolio-header { background: #2c3e50; color: white; padding: 1rem 0; }
        .portfolio-nav { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
        .portfolio-logo { font-size: 1.8rem; font-weight: bold; }
        .portfolio-menu { display: flex; list-style: none; gap: 2rem; margin: 0; padding: 0; }
        .portfolio-menu a { color: white; text-decoration: none; }
        .portfolio-hero { background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); color: white; text-align: center; padding: 6rem 2rem; }
        .portfolio-cta { background: #e74c3c; color: white; border: none; padding: 1rem 2rem; border-radius: 25px; cursor: pointer; }
        .portfolio-gallery { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
        .gallery-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-top: 2rem; }
        .gallery-item { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
        .contact-form { background: #ecf0f1; padding: 4rem 2rem; }
        .contact-form-container { max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; gap: 1rem; }
        .contact-form-container input, .contact-form-container textarea { padding: 1rem; border: 1px solid #bdc3c7; border-radius: 5px; }
        .contact-form-container button { background: #3498db; color: white; border: none; padding: 1rem; border-radius: 5px; cursor: pointer; }"""

    def _get_portfolio_javascript(self):
        return """
        document.querySelector('.contact-form-container').addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Thank you for your message! I will get back to you soon.');
            this.reset();
        });"""

    def _generate_restaurant_content(self):
        return """
        <header class="restaurant-header">
            <nav class="restaurant-nav">
                <div class="restaurant-logo">🍽️ Bella Vista</div>
                <ul class="restaurant-menu">
                    <li><a href="#home">Home</a></li>
                    <li><a href="#menu">Menu</a></li>
                    <li><a href="#reservations">Reservations</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </header>

        <section class="restaurant-hero">
            <h1>Fine Dining Experience</h1>
            <p>Authentic Italian cuisine in the heart of the city</p>
            <button class="restaurant-cta">Make Reservation</button>
        </section>

        <section class="menu-section">
            <h2>Our Menu</h2>
            <div class="menu-categories">
                <div class="menu-category">
                    <h3>🍝 Pasta</h3>
                    <div class="menu-item">
                        <span>Spaghetti Carbonara</span>
                        <span class="menu-price">$18.99</span>
                    </div>
                    <div class="menu-item">
                        <span>Fettuccine Alfredo</span>
                        <span class="menu-price">$16.99</span>
                    </div>
                </div>
                <div class="menu-category">
                    <h3>🥩 Main Courses</h3>
                    <div class="menu-item">
                        <span>Grilled Salmon</span>
                        <span class="menu-price">$24.99</span>
                    </div>
                    <div class="menu-item">
                        <span>Ribeye Steak</span>
                        <span class="menu-price">$32.99</span>
                    </div>
                </div>
            </div>
            <button class="order-online">Order Online</button>
        </section>

        <section class="location-section">
            <h2>Visit Us</h2>
            <div class="location-info">
                <p>📍 123 Gourmet Street, Foodie District</p>
                <p>📞 (555) 123-4567</p>
                <p>🕒 Open Daily: 5:00 PM - 11:00 PM</p>
            </div>
        </section>"""

    def _get_restaurant_styles(self):
        return """
        .restaurant-header { background: #8b4513; color: white; padding: 1rem 0; }
        .restaurant-nav { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
        .restaurant-logo { font-size: 1.8rem; font-weight: bold; }
        .restaurant-menu { display: flex; list-style: none; gap: 2rem; margin: 0; padding: 0; }
        .restaurant-menu a { color: white; text-decoration: none; }
        .restaurant-hero { background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600" fill="%23654321"><rect width="1200" height="600"/></svg>'); color: white; text-align: center; padding: 6rem 2rem; background-size: cover; }
        .restaurant-cta { background: #d35400; color: white; border: none; padding: 1rem 2rem; border-radius: 5px; cursor: pointer; font-size: 1.1rem; }
        .menu-section { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
        .menu-categories { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 2rem 0; }
        .menu-category { background: #fff8dc; padding: 2rem; border-radius: 10px; }
        .menu-item { display: flex; justify-content: space-between; margin: 1rem 0; padding: 0.5rem 0; border-bottom: 1px dotted #ddd; }
        .menu-price { color: #d35400; font-weight: bold; }
        .order-online { background: #27ae60; color: white; border: none; padding: 1rem 2rem; border-radius: 5px; cursor: pointer; display: block; margin: 2rem auto; }
        .location-section { background: #f8f9fa; padding: 4rem 2rem; text-align: center; }
        .location-info { max-width: 600px; margin: 0 auto; }
        .location-info p { font-size: 1.1rem; margin: 1rem 0; }"""

    def _get_restaurant_javascript(self):
        return """
        document.querySelector('.restaurant-cta').addEventListener('click', function() {
            alert('Reservation system coming soon! Please call us at (555) 123-4567');
        });

        document.querySelector('.order-online').addEventListener('click', function() {
            alert('Online ordering coming soon! Please call us at (555) 123-4567');
        });"""

    def _generate_dashboard_content(self):
        return """
        <header class="dashboard-header">
            <div class="dashboard-nav">
                <div class="dashboard-logo">📊 SocialHub</div>
                <div class="user-info">Welcome, Admin</div>
            </div>
        </header>

        <div class="dashboard-container">
            <aside class="dashboard-sidebar">
                <ul class="sidebar-menu">
                    <li><a href="#overview">📈 Overview</a></li>
                    <li><a href="#analytics">📊 Analytics</a></li>
                    <li><a href="#posts">📝 Post Scheduler</a></li>
                    <li><a href="#engagement">💬 Engagement</a></li>
                    <li><a href="#settings">⚙️ Settings</a></li>
                </ul>
            </aside>

            <main class="dashboard-main">
                <section class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Followers</h3>
                        <div class="stat-number">45,234</div>
                        <div class="stat-change">+12.5%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Engagement Rate</h3>
                        <div class="stat-number">8.3%</div>
                        <div class="stat-change">+2.1%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Posts This Week</h3>
                        <div class="stat-number">23</div>
                        <div class="stat-change">+5</div>
                    </div>
                </section>

                <section class="chart-section">
                    <h2>Analytics Chart</h2>
                    <div class="chart-placeholder">📊 Interactive Chart Would Go Here</div>
                </section>

                <section class="post-scheduler">
                    <h2>Schedule New Post</h2>
                    <div class="scheduler-form">
                        <textarea placeholder="What's on your mind?"></textarea>
                        <div class="scheduler-controls">
                            <input type="datetime-local">
                            <button class="schedule-btn">Schedule Post</button>
                        </div>
                    </div>
                </section>
            </main>
        </div>"""

    def _get_dashboard_styles(self):
        return """
        .dashboard-header { background: #2c3e50; color: white; padding: 1rem 0; }
        .dashboard-nav { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; padding: 0 2rem; }
        .dashboard-logo { font-size: 1.5rem; font-weight: bold; }
        .dashboard-container { display: flex; max-width: 1400px; margin: 0 auto; min-height: 90vh; }
        .dashboard-sidebar { width: 250px; background: #34495e; color: white; padding: 2rem 0; }
        .sidebar-menu { list-style: none; padding: 0; margin: 0; }
        .sidebar-menu li { margin: 0.5rem 0; }
        .sidebar-menu a { color: white; text-decoration: none; padding: 1rem 2rem; display: block; }
        .sidebar-menu a:hover { background: #2c3e50; }
        .dashboard-main { flex: 1; padding: 2rem; background: #ecf0f1; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2rem; font-weight: bold; color: #2c3e50; }
        .stat-change { color: #27ae60; font-size: 0.9rem; }
        .chart-section { background: white; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
        .chart-placeholder { height: 300px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; border-radius: 4px; }
        .post-scheduler { background: white; padding: 2rem; border-radius: 8px; }
        .scheduler-form textarea { width: 100%; padding: 1rem; border: 1px solid #bdc3c7; border-radius: 4px; resize: vertical; }
        .scheduler-controls { display: flex; gap: 1rem; margin-top: 1rem; }
        .schedule-btn { background: #3498db; color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 4px; cursor: pointer; }"""

    def _get_dashboard_javascript(self):
        return """
        document.querySelector('.schedule-btn').addEventListener('click', function() {
            const textarea = document.querySelector('.scheduler-form textarea');
            if (textarea.value.trim()) {
                alert('Post scheduled successfully!');
                textarea.value = '';
            } else {
                alert('Please enter some content for your post.');
            }
        });"""

    def _generate_learning_content(self):
        return """
        <header class="learning-header">
            <nav class="learning-nav">
                <div class="learning-logo">🎓 EduPlatform</div>
                <ul class="learning-menu">
                    <li><a href="#home">Home</a></li>
                    <li><a href="#courses">Courses</a></li>
                    <li><a href="#progress">My Progress</a></li>
                    <li><a href="#community">Community</a></li>
                </ul>
                <div class="user-profile">👤 John Doe</div>
            </nav>
        </header>

        <section class="learning-hero">
            <div class="hero-content">
                <h1>Learn New Skills Online</h1>
                <p>Join thousands of students in our interactive learning platform</p>
                <button class="learning-cta">Browse Courses</button>
            </div>
        </section>

        <section class="course-listings">
            <h2>Featured Courses</h2>
            <div class="course-grid">
                <div class="course-card">
                    <div class="course-image">💻</div>
                    <h3>Web Development Bootcamp</h3>
                    <p>Learn HTML, CSS, JavaScript and React</p>
                    <div class="course-meta">
                        <span class="duration">⏱️ 40 hours</span>
                        <span class="students">👥 1,234 students</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress" style="width: 65%"></div>
                    </div>
                    <button class="continue-btn">Continue Learning</button>
                </div>
                <div class="course-card">
                    <div class="course-image">🎨</div>
                    <h3>Digital Design Fundamentals</h3>
                    <p>Master the principles of digital design</p>
                    <div class="course-meta">
                        <span class="duration">⏱️ 25 hours</span>
                        <span class="students">👥 856 students</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress" style="width: 0%"></div>
                    </div>
                    <button class="start-btn">Start Course</button>
                </div>
            </div>
        </section>

        <section class="video-player-section">
            <h2>Current Lesson: JavaScript Basics</h2>
            <div class="video-container">
                <div class="video-placeholder">
                    🎥 Video Player Would Go Here
                    <div class="video-controls">
                        <button>⏯️ Play/Pause</button>
                        <span>Progress: 15:32 / 24:18</span>
                        <button>⚙️ Settings</button>
                    </div>
                </div>
            </div>
        </section>"""

    def _get_learning_styles(self):
        return """
        .learning-header { background: #8e44ad; color: white; padding: 1rem 0; }
        .learning-nav { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
        .learning-logo { font-size: 1.5rem; font-weight: bold; }
        .learning-menu { display: flex; list-style: none; gap: 2rem; margin: 0; padding: 0; }
        .learning-menu a { color: white; text-decoration: none; }
        .user-profile { font-size: 1rem; }
        .learning-hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 4rem 2rem; }
        .learning-cta { background: #e74c3c; color: white; border: none; padding: 1rem 2rem; border-radius: 5px; cursor: pointer; }
        .course-listings { padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }
        .course-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; margin-top: 2rem; }
        .course-card { background: white; border-radius: 10px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .course-image { font-size: 3rem; text-align: center; margin-bottom: 1rem; }
        .course-meta { display: flex; gap: 1rem; margin: 1rem 0; font-size: 0.9rem; color: #7f8c8d; }
        .progress-bar { background: #ecf0f1; height: 8px; border-radius: 4px; margin: 1rem 0; }
        .progress { background: #27ae60; height: 100%; border-radius: 4px; }
        .continue-btn, .start-btn { background: #3498db; color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 5px; cursor: pointer; width: 100%; }
        .video-player-section { background: #2c3e50; color: white; padding: 4rem 2rem; }
        .video-container { max-width: 800px; margin: 0 auto; }
        .video-placeholder { background: #34495e; height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px; }
        .video-controls { display: flex; gap: 2rem; margin-top: 2rem; align-items: center; }
        .video-controls button { background: #e74c3c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }"""

    def _get_learning_javascript(self):
        return """
        document.querySelectorAll('.continue-btn, .start-btn').forEach(button => {
            button.addEventListener('click', function() {
                const courseName = this.closest('.course-card').querySelector('h3').textContent;
                alert(`Opening ${courseName}...`);
            });
        });

        document.querySelector('.video-controls button').addEventListener('click', function() {
            this.textContent = this.textContent.includes('Play') ? '⏸️ Pause' : '⏯️ Play';
        });"""
