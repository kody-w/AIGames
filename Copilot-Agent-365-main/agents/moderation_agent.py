"""
Moderation Agent for AI Ambassador Platform

This agent provides content moderation explanations and suggestions for content improvements.
It can be called by other agents or used directly for moderation assistance.
"""

from agents.basic_agent import BasicAgent
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils.content_moderation import get_moderator, ModerationResult
except ImportError:
    # Fallback if running outside the full context
    pass


class ModerationAgent(BasicAgent):
    """Agent that provides content moderation services and explanations"""

    def __init__(self):
        self.name = 'Moderation'
        self.metadata = {
            "name": self.name,
            "description": "Checks content for policy violations, provides moderation explanations, and suggests content improvements. Use this when you need to verify if content is appropriate or help users understand content policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["check", "explain", "suggest_improvement", "check_user_status"],
                        "description": "Action to perform: 'check' = check content for violations, 'explain' = explain why content was flagged, 'suggest_improvement' = suggest how to improve content, 'check_user_status' = check if user is banned or has violations"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to check or analyze (required for check, explain, suggest_improvement actions)"
                    },
                    "user_guid": {
                        "type": "string",
                        "description": "User GUID for tracking violations and checking ban status"
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional context about where the content came from (e.g., 'user_input', 'ai_output')"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        """
        Perform moderation action

        Args:
            action: The moderation action to perform
            content: Content to analyze (optional)
            user_guid: User identifier (optional)
            context: Additional context (optional)

        Returns:
            str: Human-readable response about moderation status
        """
        action = kwargs.get('action', 'check')
        content = kwargs.get('content', '')
        user_guid = kwargs.get('user_guid')
        context = kwargs.get('context', 'general')

        try:
            moderator = get_moderator('/Users/kodyw/AIGames/Copilot-Agent-365-main/moderation_config.json')

            if action == 'check':
                return self._check_content(moderator, content, user_guid, context)
            elif action == 'explain':
                return self._explain_moderation(moderator, content, user_guid, context)
            elif action == 'suggest_improvement':
                return self._suggest_improvement(moderator, content, user_guid, context)
            elif action == 'check_user_status':
                return self._check_user_status(moderator, user_guid)
            else:
                return f"Unknown moderation action: {action}"

        except Exception as e:
            return f"Moderation error: {str(e)}"

    def _check_content(self, moderator, content, user_guid, context):
        """Check content and return simple status"""
        if not content:
            return "No content provided to check."

        result = moderator.check_content(content, user_guid, context)

        if not result.flagged:
            return "Content passed moderation checks. No policy violations detected."

        # Build response
        response_parts = [
            f"Content moderation alert: {result.severity.upper()} severity violation detected.",
            f"\nAction recommended: {result.action.upper()}",
            f"\nReasons: {', '.join(result.reasons)}",
        ]

        if result.filtered_content and result.action == "filter":
            response_parts.append(f"\nFiltered version: {result.filtered_content}")

        response_parts.append(f"\nLatency: {result.latency_ms}ms | Method: {result.method}")

        return "\n".join(response_parts)

    def _explain_moderation(self, moderator, content, user_guid, context):
        """Provide detailed explanation of why content was flagged"""
        if not content:
            return "No content provided to explain."

        result = moderator.check_content(content, user_guid, context)

        if not result.flagged:
            return "This content did not trigger any moderation flags. It appears to be in compliance with our content policies."

        # Build detailed explanation
        explanation = [
            f"Content Moderation Analysis:",
            f"",
            f"Severity Level: {result.severity.upper()}",
            f"Recommended Action: {result.action.upper()}",
            f"",
            f"Why this content was flagged:",
        ]

        # Add category-specific explanations
        for category, score in result.categories.items():
            explanation.append(f"  - {category.replace('_', ' ').title()}: {score:.2f}/1.0")

            # Add helpful explanations for each category
            if category == 'profanity':
                explanation.append(f"    The content contains language that may be offensive or inappropriate.")
            elif category == 'pii':
                explanation.append(f"    Personal identifiable information (PII) was detected. This includes emails, phone numbers, addresses, or other sensitive data that should not be shared.")
            elif category == 'spam':
                explanation.append(f"    The content exhibits spam-like patterns such as promotional language, repetition, or commercial solicitation.")
            elif category == 'prompt_injection':
                explanation.append(f"    The content appears to be attempting to manipulate the AI system's behavior or bypass safety measures.")
            elif category == 'hate_speech':
                explanation.append(f"    The content contains language targeting protected groups or promoting discrimination.")
            elif category == 'harassment':
                explanation.append(f"    The content contains threatening or harassing language directed at individuals.")
            elif category == 'threat':
                explanation.append(f"    The content contains threats of violence or harm.")
            elif category == 'adult_content':
                explanation.append(f"    The content contains sexually explicit material or references.")
            elif category == 'violence':
                explanation.append(f"    The content contains graphic descriptions of violence or harm.")
            elif category == 'malicious_urls':
                explanation.append(f"    The content contains suspicious URLs or links that may be harmful.")

        explanation.append("")
        explanation.append("Our content policies:")
        explanation.append("  - We maintain a safe, respectful environment for all users")
        explanation.append("  - Personal information should not be shared for privacy protection")
        explanation.append("  - Commercial spam and promotional content are not allowed")
        explanation.append("  - Attempts to manipulate the AI system violate our terms")
        explanation.append("  - Hate speech, harassment, and threats are strictly prohibited")

        if result.action == "filter":
            explanation.append("")
            explanation.append("The content has been automatically filtered. Here's the cleaned version:")
            explanation.append(f"  {result.filtered_content}")

        return "\n".join(explanation)

    def _suggest_improvement(self, moderator, content, user_guid, context):
        """Suggest how to improve flagged content"""
        if not content:
            return "No content provided to improve."

        result = moderator.check_content(content, user_guid, context)

        if not result.flagged:
            return "This content looks good! No improvements needed from a moderation perspective."

        suggestions = [
            "Content Improvement Suggestions:",
            "",
            "Your message was flagged for the following reasons:",
        ]

        # Add category-specific suggestions
        for category, score in result.categories.items():
            suggestions.append(f"  - {category.replace('_', ' ').title()}")

            if category == 'profanity':
                suggestions.append("    Suggestion: Please rephrase without profanity or offensive language.")
                suggestions.append("    Try: Use professional language and express frustration constructively.")
            elif category == 'pii':
                suggestions.append("    Suggestion: Remove personal information like emails, phone numbers, or addresses.")
                suggestions.append("    Try: Describe your situation without sharing sensitive details.")
            elif category == 'spam':
                suggestions.append("    Suggestion: Remove promotional language and focus on genuine questions or feedback.")
                suggestions.append("    Try: Be specific about what you need help with.")
            elif category == 'prompt_injection':
                suggestions.append("    Suggestion: Interact naturally without trying to change the AI's behavior.")
                suggestions.append("    Try: Ask direct questions about what you need help with.")
            elif category == 'hate_speech':
                suggestions.append("    Suggestion: Remove language targeting groups based on identity.")
                suggestions.append("    Try: Express disagreement respectfully without attacking groups.")
            elif category == 'harassment':
                suggestions.append("    Suggestion: Remove threatening or harassing language.")
                suggestions.append("    Try: Provide constructive feedback without personal attacks.")
            elif category == 'threat':
                suggestions.append("    Suggestion: Remove threats of violence or harm.")
                suggestions.append("    Try: Express concerns calmly and constructively.")
            elif category == 'adult_content':
                suggestions.append("    Suggestion: This is a general-audience platform. Keep content appropriate.")
                suggestions.append("    Try: Focus on the topic without explicit content.")
            elif category == 'violence':
                suggestions.append("    Suggestion: Avoid graphic descriptions of violence.")
                suggestions.append("    Try: Discuss topics without explicit violent content.")
            elif category == 'malicious_urls':
                suggestions.append("    Suggestion: Remove suspicious or shortened URLs.")
                suggestions.append("    Try: Share links from trusted, well-known domains only.")

        suggestions.append("")
        suggestions.append("General tips:")
        suggestions.append("  - Be respectful and constructive in your communication")
        suggestions.append("  - Keep personal information private")
        suggestions.append("  - Focus on the topic or question you need help with")
        suggestions.append("  - Use clear, professional language")

        if result.filtered_content:
            suggestions.append("")
            suggestions.append("Here's an automatically cleaned version you could use:")
            suggestions.append(f"  \"{result.filtered_content}\"")

        return "\n".join(suggestions)

    def _check_user_status(self, moderator, user_guid):
        """Check if user is banned or has violations"""
        if not user_guid:
            return "No user GUID provided to check status."

        is_banned = moderator._is_user_banned(user_guid)

        if is_banned:
            if user_guid in moderator.banned_users:
                return f"User {user_guid} is permanently banned due to critical policy violations."
            elif user_guid in moderator.temp_banned_users:
                from datetime import datetime
                expiry = datetime.fromtimestamp(moderator.temp_banned_users[user_guid])
                return f"User {user_guid} is temporarily banned until {expiry.strftime('%Y-%m-%d %H:%M:%S UTC')} due to repeated policy violations."

        # Get violation history
        violations = moderator.get_user_violations(user_guid)

        if not violations:
            return f"User {user_guid} has a clean record with no policy violations."

        # Summarize violations
        violation_summary = [
            f"User {user_guid} violation history:",
            f"  Total violations in last hour: {len(violations)}",
            ""
        ]

        severity_counts = {}
        for v in violations:
            severity = v['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for severity, count in sorted(severity_counts.items(), key=lambda x: x[1], reverse=True):
            violation_summary.append(f"  - {severity.upper()}: {count}")

        if len(violations) >= moderator.config.get('max_violations_per_hour', 10) * 0.7:
            violation_summary.append("")
            violation_summary.append("WARNING: User is approaching violation limit and may be temporarily banned.")

        return "\n".join(violation_summary)
