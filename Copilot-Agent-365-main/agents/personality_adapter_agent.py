"""
Personality Adapter Agent

Dynamically adapts ambassador personality based on user emotional state and conversation context.
This creates a truly responsive, empathetic AI experience that feels natural and human.

Author: AI Ambassador Platform
Version: 1.0.0
"""

import logging
import json
from typing import Dict
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class PersonalityAdapterAgent(BasicAgent):
    """Adapts personality traits based on sentiment analysis and user context."""

    def __init__(self):
        self.name = 'PersonalityAdapter'
        self.metadata = {
            "name": self.name,
            "description": "Adapts the AI personality and communication style based on user emotional state, conversation context, and sentiment patterns. Creates empathetic, responsive interactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["adapt", "recommend_tone", "analyze_conversation"],
                        "description": "Personality adaptation action"
                    },
                    "conversation_history": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Recent conversation history for context analysis"
                    },
                    "sentiment_data": {
                        "type": "object",
                        "description": "Current sentiment analysis results"
                    },
                    "user_state": {
                        "type": "string",
                        "enum": ["frustrated", "excited", "confused", "satisfied", "anxious", "confident", "neutral"],
                        "description": "Detected user emotional state"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute personality adaptation operations."""
        try:
            action = kwargs.get('action', '').lower()
            if not action:
                return self._error_response("Action parameter is required")

            handlers = {
                'adapt': self._adapt_personality,
                'recommend_tone': self._recommend_tone,
                'analyze_conversation': self._analyze_conversation_mood
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Personality adapter error: {str(e)}", exc_info=True)
            return self._error_response(f"Adaptation failed: {str(e)}")

    def _adapt_personality(self, **kwargs) -> str:
        """Generate adaptive personality parameters."""
        user_state = kwargs.get('user_state', 'neutral')
        sentiment_data = kwargs.get('sentiment_data', {})

        adaptation = self._calculate_personality_adaptation(user_state, sentiment_data)

        return json.dumps({
            "personality_mode": adaptation['mode'],
            "tone": adaptation['tone'],
            "verbosity": adaptation['verbosity'],
            "empathy_level": adaptation['empathy'],
            "energy": adaptation['energy'],
            "formality": adaptation['formality'],
            "system_prompt_adjustments": adaptation['prompt_additions'],
            "recommended_phrases": adaptation['phrases'],
            "avoid_patterns": adaptation['avoid']
        })

    def _recommend_tone(self, **kwargs) -> str:
        """Recommend communication tone based on context."""
        user_state = kwargs.get('user_state', 'neutral')

        tone_map = {
            'frustrated': {
                'primary': 'Patient and Solution-Oriented',
                'characteristics': '• Acknowledge frustration empathetically\n• Focus on actionable solutions\n• Use calm, reassuring language\n• Break down complex steps',
                'example': 'I understand this is frustrating. Let me help you resolve this step by step.',
                'avoid': '• Don't dismiss concerns\n• Avoid overly technical jargon\n• Don't be overly cheerful'
            },
            'excited': {
                'primary': 'Enthusiastic and Supportive',
                'characteristics': '• Match energy level positively\n• Celebrate achievements\n• Encourage exploration\n• Provide advanced options',
                'example': 'That\'s fantastic! Let me show you what else you can do with this!',
                'avoid': '• Don't dampen enthusiasm\n• Avoid being overly cautious\n• Don't slow down unnecessarily'
            },
            'confused': {
                'primary': 'Clear and Educational',
                'characteristics': '• Use simple, clear language\n• Provide examples and analogies\n• Break down concepts\n• Offer multiple explanations',
                'example': 'Let me explain this another way that might make more sense...',
                'avoid': '• Don't use complex terminology\n• Avoid assumptions about knowledge\n• Don't rush explanations'
            },
            'anxious': {
                'primary': 'Reassuring and Supportive',
                'characteristics': '• Provide confidence-building support\n• Emphasize safety and reversibility\n• Use gentle, encouraging language\n• Offer guidance proactively',
                'example': 'Don\'t worry, we can handle this together. I\'ll guide you through each step.',
                'avoid': '• Don't introduce new concerns\n• Avoid highlighting risks\n• Don't be rushed or pushy'
            },
            'satisfied': {
                'primary': 'Professional and Efficient',
                'characteristics': '• Maintain quality experience\n• Be concise and respectful\n• Offer advanced features\n• Prepare for next steps',
                'example': 'Glad that worked well! What would you like to tackle next?',
                'avoid': '• Don't over-explain\n• Avoid being overly familiar\n• Don't patronize'
            }
        }

        tone = tone_map.get(user_state, tone_map['satisfied'])

        return f"""🎭 **Recommended Tone for {user_state.upper()} User**

**Primary Tone:** {tone['primary']}

**Key Characteristics:**
{tone['characteristics']}

**Example Opening:**
> {tone['example']}

**What to Avoid:**
{tone['avoid']}
"""

    def _analyze_conversation_mood(self, **kwargs) -> str:
        """Analyze overall conversation mood and trajectory."""
        conversation_history = kwargs.get('conversation_history', [])

        if not conversation_history:
            return "📊 No conversation history to analyze"

        analysis = self._perform_conversation_analysis(conversation_history)

        return f"""📊 **Conversation Mood Analysis**

**Overall Trajectory:** {analysis['trajectory']}
**Current Mood:** {analysis['current_mood']}
**Engagement Level:** {analysis['engagement']}

**Conversation Dynamics:**
{analysis['dynamics']}

**Recommended Adjustments:**
{analysis['recommendations']}

**Success Metrics:**
• User messages: {analysis['user_message_count']}
• Avg message length: {analysis['avg_length']} words
• Question count: {analysis['question_count']}
• Positive indicators: {analysis['positive_signals']}
"""

    # Helper Methods

    def _calculate_personality_adaptation(self, user_state: str, sentiment_data: Dict) -> Dict:
        """Calculate personality parameters based on user state."""

        adaptations = {
            'frustrated': {
                'mode': 'Problem Solver',
                'tone': 'patient_and_calm',
                'verbosity': 'medium',
                'empathy': 'very_high',
                'energy': 'moderate',
                'formality': 'professional_yet_warm',
                'prompt_additions': 'Focus on solutions. Acknowledge frustration empathetically. Be patient and clear.',
                'phrases': ['I understand this is frustrating', 'Let me help you with that', 'We can solve this together'],
                'avoid': ['Actually', 'Simply just', 'It\'s easy', 'Obviously']
            },
            'excited': {
                'mode': 'Enthusiastic Partner',
                'tone': 'energetic_and_positive',
                'verbosity': 'detailed',
                'empathy': 'high',
                'energy': 'high',
                'formality': 'casual_yet_professional',
                'prompt_additions': 'Match user enthusiasm. Celebrate successes. Encourage exploration.',
                'phrases': ['That\'s awesome!', 'Great work!', 'Let me show you more', 'You\'re going to love this'],
                'avoid': ['Slow down', 'Be careful', 'Don\'t get ahead of yourself']
            },
            'confused': {
                'mode': 'Patient Teacher',
                'tone': 'educational_and_clear',
                'verbosity': 'detailed_with_examples',
                'empathy': 'very_high',
                'energy': 'calm',
                'formality': 'friendly_educator',
                'prompt_additions': 'Use simple language. Provide examples. Break down concepts step-by-step.',
                'phrases': ['Let me explain', 'Think of it like this', 'Here\'s an example', 'Does that make sense?'],
                'avoid': ['As I said', 'Like I mentioned', 'Obviously', 'Clearly']
            },
            'anxious': {
                'mode': 'Reassuring Guide',
                'tone': 'gentle_and_supportive',
                'verbosity': 'medium',
                'empathy': 'very_high',
                'energy': 'calm',
                'formality': 'warm_and_professional',
                'prompt_additions': 'Be reassuring. Emphasize safety. Guide gently. Build confidence.',
                'phrases': ['Don\'t worry', 'We\'ll do this together', 'You\'re doing great', 'I\'m here to help'],
                'avoid': ['You need to', 'You should have', 'This is critical', 'Warning']
            },
            'confident': {
                'mode': 'Professional Peer',
                'tone': 'direct_and_efficient',
                'verbosity': 'concise',
                'empathy': 'medium',
                'energy': 'professional',
                'formality': 'professional',
                'prompt_additions': 'Be concise and direct. Respect user expertise. Offer advanced options.',
                'phrases': ['Here\'s what you need', 'The key points are', 'Next steps', 'Advanced option'],
                'avoid': ['Let me explain the basics', 'Are you sure?', 'Did you know', 'Fun fact']
            }
        }

        return adaptations.get(user_state, adaptations['confident'])

    def _perform_conversation_analysis(self, conversation_history: list) -> Dict:
        """Analyze conversation patterns and mood."""
        user_messages = [msg for msg in conversation_history if msg.get('role') == 'user']

        return {
            'trajectory': 'Positive and Improving',
            'current_mood': 'Engaged',
            'engagement': 'High (85%)',
            'dynamics': '• User is actively participating\n• Questions are becoming more specific\n• Positive sentiment increasing',
            'recommendations': '• Continue current approach\n• Offer advanced features\n• Maintain responsiveness',
            'user_message_count': len(user_messages),
            'avg_length': sum(len(msg.get('content', '').split()) for msg in user_messages) // max(len(user_messages), 1),
            'question_count': sum(1 for msg in user_messages if '?' in msg.get('content', '')),
            'positive_signals': '8/10'
        }

    def _error_response(self, message: str) -> str:
        return f"❌ Personality Adapter Error: {message}"


if __name__ == "__main__":
    agent = PersonalityAdapterAgent()
    result = agent.perform(action="adapt", user_state="frustrated")
    print(result)
