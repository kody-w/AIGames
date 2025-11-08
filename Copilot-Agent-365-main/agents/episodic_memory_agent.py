"""
Episodic Memory Synthesis Agent

Creates rich, narrative episodic memories from conversations - transforming cold data into warm stories.
Enables "Remember when..." moments that feel like talking to an old friend.

Author: AI Ambassador Platform
Version: 1.0.0
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List
from agents.basic_agent import BasicAgent

try:
    from utils.azure_file_storage import AzureFileStorageManager as StorageManager
except:
    from utils.local_file_storage import LocalFileStorageManager as StorageManager

logger = logging.getLogger(__name__)


class EpisodicMemoryAgent(BasicAgent):
    """Synthesizes episodic memories and creates conversational narratives."""

    def __init__(self):
        self.name = 'EpisodicMemory'
        self.metadata = {
            "name": self.name,
            "description": "Creates and recalls episodic memories - meaningful moments, breakthroughs, and shared experiences from conversations. Enables 'Remember when...' functionality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_episode", "recall_episode", "list_episodes", "find_similar", "create_milestone", "get_timeline"],
                        "description": "Episodic memory action"
                    },
                    "conversation_history": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Recent conversation for episode creation"
                    },
                    "episode_type": {
                        "type": "string",
                        "enum": ["first_meeting", "breakthrough", "funny_moment", "conflict", "resolution", "milestone", "learning", "celebration"],
                        "description": "Type of episode to create"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for finding episodes"
                    },
                    "episode_id": {
                        "type": "string",
                        "description": "Specific episode ID to recall"
                    },
                    "user_guid": {
                        "type": "string",
                        "description": "User GUID for personalized memories"
                    }
                },
                "required": ["action"]
            }
        }
        self.storage_manager = StorageManager()
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute episodic memory operations."""
        try:
            action = kwargs.get('action', '').lower()
            if not action:
                return self._error_response("Action parameter is required")

            # Set user context
            user_guid = kwargs.get('user_guid')
            if user_guid:
                self.storage_manager.set_memory_context(user_guid)

            handlers = {
                'create_episode': self._create_episode,
                'recall_episode': self._recall_episode,
                'list_episodes': self._list_episodes,
                'find_similar': self._find_similar_episodes,
                'create_milestone': self._create_milestone,
                'get_timeline': self._get_timeline
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Episodic memory agent error: {str(e)}", exc_info=True)
            return self._error_response(f"Memory operation failed: {str(e)}")

    def _create_episode(self, **kwargs) -> str:
        """Create a new episodic memory from conversation."""
        conversation_history = kwargs.get('conversation_history', [])
        episode_type = kwargs.get('episode_type', 'learning')

        if not conversation_history:
            return self._error_response("Conversation history required to create episode")

        # Analyze conversation to extract meaningful moments
        episode_data = self._synthesize_episode(conversation_history, episode_type)

        # Store episode
        episode_id = str(uuid.uuid4())
        episode_data['id'] = episode_id
        episode_data['created_at'] = datetime.now().isoformat()

        # Save to episodic memories storage
        self._save_episode(episode_id, episode_data)

        emoji_map = {
            'first_meeting': '👋',
            'breakthrough': '💡',
            'funny_moment': '😄',
            'conflict': '⚔️',
            'resolution': '🤝',
            'milestone': '🎯',
            'learning': '📚',
            'celebration': '🎉'
        }

        emoji = emoji_map.get(episode_type, '💭')

        return f"""{emoji} **Episodic Memory Created**

**Type:** {episode_type.replace('_', ' ').title()}
**Episode ID:** {episode_id[:8]}...

**Memory Summary:**
{episode_data['summary']}

**Key Moments:**
{chr(10).join(f'• {moment}' for moment in episode_data['key_moments'])}

**Emotional Tone:** {episode_data['emotional_tone']}

This memory has been permanently saved. You can recall it anytime by saying "Remember when {episode_data['trigger_phrase']}" """

    def _recall_episode(self, **kwargs) -> str:
        """Recall a specific episodic memory."""
        episode_id = kwargs.get('episode_id')
        query = kwargs.get('query')

        if episode_id:
            episode = self._load_episode(episode_id)
            if not episode:
                return "I don't have a memory with that ID."
        elif query:
            episodes = self._search_episodes(query)
            if not episodes:
                return f"I don't recall any moments about '{query}'. Maybe we haven't talked about that yet?"
            episode = episodes[0]  # Get most relevant
        else:
            return self._error_response("Need either episode_id or query to recall a memory")

        return self._format_episode_recall(episode)

    def _list_episodes(self, **kwargs) -> str:
        """List all episodic memories."""
        episodes = self._get_all_episodes()

        if not episodes:
            return "We haven't created any episodic memories yet. Let's make some memorable moments together!"

        # Sort by date, most recent first
        sorted_episodes = sorted(episodes, key=lambda x: x.get('created_at', ''), reverse=True)

        episode_list = []
        for i, ep in enumerate(sorted_episodes[:10], 1):  # Show last 10
            date_str = self._format_date(ep.get('created_at', ''))
            episode_list.append(f"{i}. **{ep.get('type', 'memory').title()}** - {ep.get('summary', 'No summary')[:80]}... ({date_str})")

        total_count = len(episodes)
        showing = min(10, total_count)

        return f"""💭 **Your Episodic Memories**

Showing {showing} of {total_count} memories:

{chr(10).join(episode_list)}

---
💡 **Tip:** Say "Remember when [topic]" to recall specific moments, or ask me to create a milestone for important achievements!
"""

    def _find_similar_episodes(self, **kwargs) -> str:
        """Find episodes similar to a query."""
        query = kwargs.get('query', '')

        if not query:
            return self._error_response("Query required to find similar episodes")

        similar_episodes = self._search_episodes(query)

        if not similar_episodes:
            return f"I couldn't find any memories similar to '{query}'. Want to create one?"

        results = []
        for i, ep in enumerate(similar_episodes[:5], 1):
            date_str = self._format_date(ep.get('created_at', ''))
            results.append(f"{i}. {ep.get('summary', 'No summary')[:100]}... ({date_str})")

        return f"""🔍 **Similar Memories Found**

Query: "{query}"

{chr(10).join(results)}

---
Want me to recall any of these in detail?
"""

    def _create_milestone(self, **kwargs) -> str:
        """Create a milestone episodic memory."""
        conversation_history = kwargs.get('conversation_history', [])

        if not conversation_history:
            return self._error_response("Conversation history required for milestone")

        # Create a special milestone episode
        kwargs['episode_type'] = 'milestone'
        return self._create_episode(**kwargs)

    def _get_timeline(self, **kwargs) -> str:
        """Get chronological timeline of episodic memories."""
        episodes = self._get_all_episodes()

        if not episodes:
            return "Our story is just beginning! No timeline yet."

        # Sort chronologically
        sorted_episodes = sorted(episodes, key=lambda x: x.get('created_at', ''))

        # Group by month
        timeline = self._build_timeline(sorted_episodes)

        return f"""📅 **Memory Timeline - Our Story Together**

{timeline}

---
**Total Memories:** {len(episodes)}
**Journey Started:** {self._format_date(sorted_episodes[0].get('created_at', ''))}
**Latest Memory:** {self._format_date(sorted_episodes[-1].get('created_at', ''))}
"""

    # Helper Methods

    def _synthesize_episode(self, conversation_history: List[Dict], episode_type: str) -> Dict:
        """Analyze conversation and synthesize an episodic memory."""

        # Extract user messages for context
        user_messages = [msg.get('content', '') for msg in conversation_history if msg.get('role') == 'user']
        assistant_messages = [msg.get('content', '') for msg in conversation_history if msg.get('role') == 'assistant']

        # Create rich narrative summary
        summary = self._create_narrative_summary(user_messages, assistant_messages, episode_type)

        # Identify key moments
        key_moments = self._extract_key_moments(conversation_history, episode_type)

        # Detect emotional tone
        emotional_tone = self._detect_emotional_tone(conversation_history)

        # Generate trigger phrase for recall
        trigger_phrase = self._generate_trigger_phrase(summary, episode_type)

        return {
            'type': episode_type,
            'summary': summary,
            'key_moments': key_moments,
            'emotional_tone': emotional_tone,
            'trigger_phrase': trigger_phrase,
            'message_count': len(conversation_history),
            'topics': self._extract_topics(conversation_history)
        }

    def _create_narrative_summary(self, user_messages: List[str], assistant_messages: List[str], episode_type: str) -> str:
        """Create a narrative summary of the episode."""

        # Simulated narrative generation (in production, use GPT-4 for better summaries)
        narratives = {
            'first_meeting': f"We first met when you asked about {user_messages[0][:50] if user_messages else 'getting started'}. I introduced myself and we began our journey together.",
            'breakthrough': f"You had a breakthrough moment when we worked through {user_messages[-1][:50] if user_messages else 'a challenging problem'}. Everything clicked and you saw the solution clearly.",
            'funny_moment': f"We shared a laugh when {user_messages[-1][:50] if user_messages else 'something unexpected happened'}. It lightened the mood and made our conversation more enjoyable.",
            'learning': f"You learned something new about {user_messages[-1][:50] if user_messages else 'an interesting topic'}. Your questions showed genuine curiosity and engagement.",
            'milestone': f"You achieved an important milestone: {user_messages[-1][:80] if user_messages else 'completing a significant goal'}. This was a proud moment worth celebrating.",
            'celebration': f"We celebrated your success with {user_messages[-1][:50] if user_messages else 'accomplishing something meaningful'}. Your hard work paid off!",
        }

        return narratives.get(episode_type, "We had a meaningful conversation that I'll remember.")

    def _extract_key_moments(self, conversation_history: List[Dict], episode_type: str) -> List[str]:
        """Extract key moments from conversation."""

        moments = [
            "Initial connection and context setting",
            "Deep dive into the main topic",
            "Breakthrough or key insight",
            "Action items or next steps identified"
        ]

        return moments[:3]  # Return top 3

    def _detect_emotional_tone(self, conversation_history: List[Dict]) -> str:
        """Detect the emotional tone of the conversation."""
        # Simulated emotion detection
        tones = ["Excited and Enthusiastic", "Curious and Engaged", "Thoughtful and Reflective",
                 "Determined and Focused", "Joyful and Celebratory"]

        return tones[len(conversation_history) % len(tones)]

    def _generate_trigger_phrase(self, summary: str, episode_type: str) -> str:
        """Generate a natural trigger phrase for recalling this memory."""
        # Extract key words from summary
        words = summary.split()[:5]
        return ' '.join(words)

    def _extract_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract main topics from conversation."""
        return ["collaboration", "problem-solving", "learning"]

    def _save_episode(self, episode_id: str, episode_data: Dict):
        """Save episode to storage."""
        try:
            # Read existing episodes
            episodes_file = "episodic_memories.json"
            try:
                episodes_json = self.storage_manager.read_file('memories', episodes_file)
                episodes = json.loads(episodes_json) if episodes_json else {}
            except:
                episodes = {}

            # Add new episode
            episodes[episode_id] = episode_data

            # Write back
            self.storage_manager.write_file('memories', episodes_file, json.dumps(episodes, indent=2))

        except Exception as e:
            logger.error(f"Error saving episode: {e}")

    def _load_episode(self, episode_id: str) -> Dict:
        """Load a specific episode."""
        try:
            episodes_json = self.storage_manager.read_file('memories', 'episodic_memories.json')
            episodes = json.loads(episodes_json) if episodes_json else {}
            return episodes.get(episode_id)
        except:
            return None

    def _get_all_episodes(self) -> List[Dict]:
        """Get all episodes."""
        try:
            episodes_json = self.storage_manager.read_file('memories', 'episodic_memories.json')
            episodes_dict = json.loads(episodes_json) if episodes_json else {}
            return list(episodes_dict.values())
        except:
            return []

    def _search_episodes(self, query: str) -> List[Dict]:
        """Search episodes by query."""
        all_episodes = self._get_all_episodes()

        # Simple keyword matching (in production, use vector search)
        query_lower = query.lower()
        matches = []

        for ep in all_episodes:
            summary = ep.get('summary', '').lower()
            topics = ' '.join(ep.get('topics', [])).lower()

            if query_lower in summary or query_lower in topics:
                matches.append(ep)

        return matches

    def _format_episode_recall(self, episode: Dict) -> str:
        """Format an episode for beautiful recall."""
        if not episode:
            return "I couldn't find that memory."

        emoji_map = {
            'first_meeting': '👋',
            'breakthrough': '💡',
            'funny_moment': '😄',
            'learning': '📚',
            'milestone': '🎯',
            'celebration': '🎉'
        }

        emoji = emoji_map.get(episode.get('type', ''), '💭')
        date_str = self._format_date(episode.get('created_at', ''))

        return f"""{emoji} **Remember When...**

{episode.get('summary', 'No summary available')}

**What Made It Special:**
{chr(10).join(f'• {moment}' for moment in episode.get('key_moments', []))}

**How It Felt:** {episode.get('emotional_tone', 'Meaningful')}
**When:** {date_str}

---
💭 That was a great moment we shared. Want to create more memories like this?
"""

    def _format_date(self, iso_date: str) -> str:
        """Format ISO date to human-readable."""
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            return "Some time ago"

    def _build_timeline(self, sorted_episodes: List[Dict]) -> str:
        """Build a visual timeline."""
        timeline_str = ""

        for ep in sorted_episodes[-5:]:  # Last 5
            date = self._format_date(ep.get('created_at', ''))
            timeline_str += f"**{date}**\n└─ {ep.get('type', 'Memory').title()}: {ep.get('summary', '')[:80]}...\n\n"

        return timeline_str

    def _error_response(self, message: str) -> str:
        return f"❌ Episodic Memory Error: {message}"


if __name__ == "__main__":
    agent = EpisodicMemoryAgent()
    result = agent.perform(
        action="create_episode",
        episode_type="breakthrough",
        conversation_history=[
            {"role": "user", "content": "I finally understand how this works!"},
            {"role": "assistant", "content": "That's fantastic! Your breakthrough moment is here."}
        ]
    )
    print(result)
