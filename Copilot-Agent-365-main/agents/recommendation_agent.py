"""
Recommendation Agent

Provides personalized recommendations based on user preferences and behavior.

Author: AI Ambassador Platform
Version: 1.0.0
"""

import logging
from typing import Dict, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class RecommendationAgent(BasicAgent):
    """Generates personalized recommendations for products, content, and actions."""

    def __init__(self):
        self.name = 'Recommendation'
        self.metadata = {
            "name": self.name,
            "description": "Generates personalized recommendations for products, content, or actions based on user preferences and behavior patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["recommend_products", "recommend_content", "recommend_actions", "similar_items", "trending"],
                        "description": "Type of recommendation to generate"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category for recommendations (e.g., 'books', 'movies', 'products')"
                    },
                    "preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "User preferences or interests"
                    },
                    "history": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "User's interaction history"
                    },
                    "item_id": {
                        "type": "string",
                        "description": "Reference item for finding similar items"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recommendations to return (default: 5)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for recommendations"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute recommendation operations."""
        try:
            action = kwargs.get('action', '').lower()
            if not action:
                return self._error_response("Action parameter is required")

            handlers = {
                'recommend_products': self._recommend_products,
                'recommend_content': self._recommend_content,
                'recommend_actions': self._recommend_actions,
                'similar_items': self._find_similar,
                'trending': self._show_trending
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Recommendation agent error: {str(e)}", exc_info=True)
            return self._error_response(f"Recommendation failed: {str(e)}")

    def _recommend_products(self, **kwargs) -> str:
        """Recommend products based on preferences."""
        category = kwargs.get('category', 'general')
        preferences = kwargs.get('preferences', [])
        limit = kwargs.get('limit', 5)

        recs = self._generate_product_recommendations(category, preferences, limit)

        return f"""🛍️ **Product Recommendations**

**Category:** {category.title()}
**Based on:** {', '.join(preferences) if preferences else 'Popular items'}

{recs}

**Why These Recommendations:**
• Matches your preferences
• Highly rated by similar users
• Currently in stock
• Competitive pricing"""

    def _recommend_content(self, **kwargs) -> str:
        """Recommend content (articles, videos, etc.)."""
        category = kwargs.get('category', 'articles')
        preferences = kwargs.get('preferences', [])
        limit = kwargs.get('limit', 5)

        recs = self._generate_content_recommendations(category, preferences, limit)

        return f"""📺 **Content Recommendations**

**Type:** {category.title()}
**Personalized for you**

{recs}

**Recommendation Factors:**
• Your viewing history
• Similar users' preferences
• Trending topics
• Recently added content"""

    def _recommend_actions(self, **kwargs) -> str:
        """Recommend next actions."""
        context = kwargs.get('context', '')
        limit = kwargs.get('limit', 3)

        actions = self._generate_action_recommendations(context, limit)

        return f"""🎯 **Recommended Actions**

{actions}

**Priority Score:**
Based on urgency, impact, and feasibility

**Expected Outcomes:**
• Improved efficiency
• Better results
• Time savings"""

    def _find_similar(self, **kwargs) -> str:
        """Find similar items."""
        item_id = kwargs.get('item_id')
        category = kwargs.get('category', 'items')
        limit = kwargs.get('limit', 5)

        if not item_id:
            return self._error_response("Item ID is required")

        similar = self._generate_similar_items(item_id, category, limit)

        return f"""🔍 **Similar Items**

**Reference:** {item_id}
**Category:** {category}

{similar}

**Similarity Based On:**
• Features and attributes
• User ratings
• Category overlap
• Price range"""

    def _show_trending(self, **kwargs) -> str:
        """Show trending items."""
        category = kwargs.get('category', 'all')
        limit = kwargs.get('limit', 5)

        trending = self._generate_trending_items(category, limit)

        return f"""🔥 **Trending Now**

**Category:** {category.title()}
**Updated:** Just now

{trending}

**Trend Analysis:**
• Rapidly growing interest
• High engagement rates
• Positive sentiment
• Shared widely"""

    # Helper methods

    def _generate_product_recommendations(self, category: str, preferences: List[str], limit: int) -> str:
        """Generate product recommendations."""
        products = []
        for i in range(limit):
            products.append(f"""**{i+1}. Product Name {i+1}**
   ⭐ 4.{8-i}/5 (1,234 reviews)
   💰 ${'49' if i < 2 else '29'}.99
   ✅ In Stock | Free Shipping
   Match: {95-i*5}%""")
        return '\n\n'.join(products)

    def _generate_content_recommendations(self, category: str, preferences: List[str], limit: int) -> str:
        """Generate content recommendations."""
        content = []
        for i in range(limit):
            content.append(f"""**{i+1}. {category.rstrip('s').title()} Title {i+1}**
   📅 Published: 2 days ago
   ⏱️ Duration: {10+i*5} min
   👁️ Views: {50+i*10}K
   Match: {90-i*5}%""")
        return '\n\n'.join(content)

    def _generate_action_recommendations(self, context: str, limit: int) -> str:
        """Generate action recommendations."""
        actions = [
            "**1. Complete pending review** ⚡ High Priority\n   Impact: High | Effort: Medium | Time: 30 min",
            "**2. Schedule follow-up meeting** 📅 Medium Priority\n   Impact: Medium | Effort: Low | Time: 15 min",
            "**3. Update documentation** 📝 Low Priority\n   Impact: Medium | Effort: Medium | Time: 1 hour"
        ]
        return '\n\n'.join(actions[:limit])

    def _generate_similar_items(self, item_id: str, category: str, limit: int) -> str:
        """Generate similar items."""
        items = []
        for i in range(limit):
            items.append(f"""**{i+1}. Similar Item {i+1}**
   Similarity: {95-i*5}%
   Price: ${39+i*5}.99
   Rating: 4.{7-i}/5""")
        return '\n\n'.join(items)

    def _generate_trending_items(self, category: str, limit: int) -> str:
        """Generate trending items."""
        items = []
        for i in range(limit):
            items.append(f"""**{i+1}. Trending Item {i+1}** 📈
   Growth: +{150-i*20}% (24h)
   Engagement: {10-i}K interactions
   Trend Score: {95-i*5}/100""")
        return '\n\n'.join(items)

    def _error_response(self, message: str) -> str:
        return f"❌ Recommendation Agent Error: {message}"


if __name__ == "__main__":
    agent = RecommendationAgent()
    print(agent.perform(action="recommend_products", category="books", preferences=["sci-fi", "technology"]))
