"""
Analytics Agent

An intelligent agent that can query and analyze platform analytics data
using natural language queries. Provides insights, generates reports, and
answers questions about user behavior, ambassador performance, and business metrics.

Examples:
- "How many users did we have this week?"
- "Which ambassador is performing best?"
- "Show me the conversion rate for the onboarding funnel"
- "What's the retention rate for users who joined last month?"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.basic_agent import BasicAgent
from utils.analytics import (
    AnalyticsStorage, FunnelAnalyzer, CohortAnalyzer,
    AmbassadorPerformanceAnalyzer, EventTypes
)
from utils.azure_file_storage import AzureFileStorageManager
from datetime import datetime, timedelta
import json


class AnalyticsAgent(BasicAgent):
    """Agent for querying and analyzing platform analytics data"""

    def __init__(self):
        self.name = 'Analytics'
        self.metadata = {
            "name": self.name,
            "description": "Query analytics data and generate insights about user behavior, ambassador performance, and business metrics. Supports natural language queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query about analytics data (e.g., 'How many users this week?', 'Best performing ambassador', 'Funnel conversion rate')"
                    },
                    "time_period": {
                        "type": "string",
                        "description": "Time period for analysis: 'today', 'week', 'month', 'quarter', 'year', or specific number of days (e.g., '7', '30')",
                        "default": "week"
                    },
                    "ambassador_id": {
                        "type": "string",
                        "description": "Optional ambassador ID to filter results"
                    }
                },
                "required": ["query"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Initialize analytics components
        self.storage_manager = AzureFileStorageManager()
        self.storage = AnalyticsStorage(self.storage_manager)
        self.funnel_analyzer = FunnelAnalyzer(self.storage)
        self.cohort_analyzer = CohortAnalyzer(self.storage)
        self.ambassador_analyzer = AmbassadorPerformanceAnalyzer(self.storage)

    def _parse_time_period(self, time_period: str) -> tuple:
        """
        Parse time period string into start and end dates

        Args:
            time_period: Time period string

        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.utcnow()

        if time_period == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == 'week':
            start_date = end_date - timedelta(days=7)
        elif time_period == 'month':
            start_date = end_date - timedelta(days=30)
        elif time_period == 'quarter':
            start_date = end_date - timedelta(days=90)
        elif time_period == 'year':
            start_date = end_date - timedelta(days=365)
        elif time_period.isdigit():
            days = int(time_period)
            start_date = end_date - timedelta(days=days)
        else:
            # Default to week
            start_date = end_date - timedelta(days=7)

        return start_date, end_date

    def _get_summary_metrics(self, start_date: datetime, end_date: datetime, ambassador_id: str = None) -> dict:
        """Get summary metrics for a time period"""
        events = self.storage.get_events_by_date_range(start_date, end_date)

        if ambassador_id:
            events = [e for e in events if e.get('ambassador_id') == ambassador_id]

        unique_users = len(set(e.get('user_id') for e in events if e.get('user_id')))
        unique_sessions = len(set(e.get('session_id') for e in events if e.get('session_id')))

        event_counts = {}
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            'total_events': len(events),
            'unique_users': unique_users,
            'unique_sessions': unique_sessions,
            'event_counts': event_counts,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }

    def _analyze_user_query(self, query: str) -> dict:
        """
        Analyze user query to determine intent and extract parameters

        Args:
            query: Natural language query

        Returns:
            Dictionary with intent and parameters
        """
        query_lower = query.lower()

        # Determine intent
        intent = 'summary'  # default

        if any(word in query_lower for word in ['user', 'users', 'visitor', 'visitors']):
            if 'how many' in query_lower or 'count' in query_lower:
                intent = 'user_count'
            elif 'growth' in query_lower or 'trend' in query_lower:
                intent = 'user_growth'

        elif any(word in query_lower for word in ['ambassador', 'ambassadors']):
            if 'best' in query_lower or 'top' in query_lower or 'perform' in query_lower:
                intent = 'top_ambassadors'
            elif 'compare' in query_lower or 'comparison' in query_lower:
                intent = 'ambassador_comparison'

        elif 'funnel' in query_lower or 'conversion' in query_lower:
            intent = 'funnel_analysis'

        elif 'retention' in query_lower or 'cohort' in query_lower:
            intent = 'retention_analysis'

        elif 'session' in query_lower:
            intent = 'session_metrics'

        elif 'message' in query_lower or 'chat' in query_lower:
            intent = 'messaging_metrics'

        elif 'qr' in query_lower or 'scan' in query_lower:
            intent = 'qr_metrics'

        return {
            'intent': intent,
            'query': query
        }

    def _format_user_count_response(self, metrics: dict, time_period: str) -> str:
        """Format response for user count queries"""
        users = metrics['unique_users']
        sessions = metrics['unique_sessions']

        return f"""**User Activity Analysis**

📊 **Time Period**: {time_period}

**Key Metrics:**
- **Unique Users**: {users:,}
- **Active Sessions**: {sessions:,}
- **Average Sessions per User**: {sessions/users if users > 0 else 0:.2f}

**Event Breakdown:**
{self._format_event_breakdown(metrics['event_counts'])}
"""

    def _format_event_breakdown(self, event_counts: dict) -> str:
        """Format event breakdown"""
        if not event_counts:
            return "- No events recorded"

        lines = []
        for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{event_type}**: {count:,}")

        return '\n'.join(lines)

    def _format_ambassador_performance(self, metrics: dict) -> str:
        """Format ambassador performance response"""
        summary = metrics.get('summary', {})

        return f"""**Ambassador Performance Report**

🎯 **Ambassador**: {metrics.get('ambassador_id', 'N/A')}
📅 **Period**: {metrics.get('date_range', {}).get('start', 'N/A')} to {metrics.get('date_range', {}).get('end', 'N/A')}

**Summary:**
- **Unique Users**: {summary.get('unique_users', 0):,}
- **Total Sessions**: {summary.get('total_sessions', 0):,}
- **Total Messages**: {summary.get('total_messages', 0):,}
- **QR Scans**: {summary.get('total_qr_scans', 0):,}
- **Engagement Rate**: {summary.get('engagement_rate', 0):.2f} messages/session

**Top Daily Performance:**
{self._format_daily_metrics(metrics.get('daily_metrics', []))}
"""

    def _format_daily_metrics(self, daily_metrics: list) -> str:
        """Format daily metrics"""
        if not daily_metrics:
            return "- No daily data available"

        # Show top 5 days
        sorted_days = sorted(daily_metrics, key=lambda x: x.get('users', 0), reverse=True)[:5]

        lines = []
        for day in sorted_days:
            lines.append(f"- **{day.get('date')}**: {day.get('users', 0)} users, {day.get('messages', 0)} messages")

        return '\n'.join(lines)

    def _compare_ambassadors(self, start_date: datetime, end_date: datetime, ambassador_ids: list = None) -> str:
        """Compare multiple ambassadors"""
        if not ambassador_ids:
            # Get all ambassadors from events
            events = self.storage.get_events_by_date_range(start_date, end_date)
            ambassador_ids = list(set(e.get('ambassador_id') for e in events if e.get('ambassador_id')))

        if not ambassador_ids:
            return "No ambassador data available for comparison."

        results = self.ambassador_analyzer.compare_ambassadors(ambassador_ids, start_date, end_date)

        output = f"""**Ambassador Comparison Report**

📅 **Period**: {results.get('date_range', {}).get('start', 'N/A')} to {results.get('date_range', {}).get('end', 'N/A')}

"""
        ambassadors = results.get('ambassadors', [])
        if not ambassadors:
            return output + "No data available."

        # Sort by unique users
        ambassadors_sorted = sorted(ambassadors, key=lambda x: x.get('summary', {}).get('unique_users', 0), reverse=True)

        output += "**Rankings:**\n\n"
        for i, amb in enumerate(ambassadors_sorted, 1):
            summary = amb.get('summary', {})
            output += f"{i}. **{amb.get('ambassador_id')}**\n"
            output += f"   - Users: {summary.get('unique_users', 0):,}\n"
            output += f"   - Sessions: {summary.get('total_sessions', 0):,}\n"
            output += f"   - Engagement: {summary.get('engagement_rate', 0):.2f}\n\n"

        return output

    def perform(self, query: str, time_period: str = 'week', ambassador_id: str = None, **kwargs) -> str:
        """
        Execute analytics query

        Args:
            query: Natural language query
            time_period: Time period for analysis
            ambassador_id: Optional ambassador filter

        Returns:
            Formatted analysis results
        """
        try:
            # Parse time period
            start_date, end_date = self._parse_time_period(time_period)

            # Analyze query
            analysis = self._analyze_user_query(query)
            intent = analysis['intent']

            # Execute based on intent
            if intent == 'user_count' or intent == 'summary':
                metrics = self._get_summary_metrics(start_date, end_date, ambassador_id)
                return self._format_user_count_response(metrics, time_period)

            elif intent == 'top_ambassadors' or intent == 'ambassador_comparison':
                return self._compare_ambassadors(start_date, end_date)

            elif intent == 'ambassador_performance' and ambassador_id:
                metrics = self.ambassador_analyzer.get_ambassador_metrics(
                    ambassador_id, start_date, end_date
                )
                return self._format_ambassador_performance(metrics)

            elif intent == 'session_metrics':
                metrics = self._get_summary_metrics(start_date, end_date, ambassador_id)
                return f"**Session Metrics**\n\nTotal Active Sessions: {metrics['unique_sessions']:,}\nUnique Users: {metrics['unique_users']:,}\nAverage Sessions per User: {metrics['unique_sessions']/metrics['unique_users'] if metrics['unique_users'] > 0 else 0:.2f}"

            elif intent == 'messaging_metrics':
                metrics = self._get_summary_metrics(start_date, end_date, ambassador_id)
                message_count = metrics['event_counts'].get(EventTypes.MESSAGE_SENT, 0)
                return f"**Messaging Activity**\n\nTotal Messages Sent: {message_count:,}\nActive Users: {metrics['unique_users']:,}\nMessages per User: {message_count/metrics['unique_users'] if metrics['unique_users'] > 0 else 0:.2f}"

            elif intent == 'qr_metrics':
                metrics = self._get_summary_metrics(start_date, end_date, ambassador_id)
                qr_count = metrics['event_counts'].get(EventTypes.QR_SCAN, 0)
                return f"**QR Code Scans**\n\nTotal Scans: {qr_count:,}\nUnique Users: {metrics['unique_users']:,}\nConversion to Session: {metrics['unique_sessions']/qr_count*100 if qr_count > 0 else 0:.1f}%"

            elif intent == 'funnel_analysis':
                return "Funnel analysis requires a specific funnel ID. Please specify which funnel to analyze."

            elif intent == 'retention_analysis':
                cohort_data = self.cohort_analyzer.analyze_retention(
                    start_date=start_date,
                    cohort_period='weekly',
                    retention_periods=12
                )
                return f"**Retention Analysis**\n\nCohort Period: {cohort_data['cohort_period']}\nNumber of Cohorts: {len(cohort_data.get('cohorts', {}))}\n\n*Use the analytics dashboard for detailed cohort visualization.*"

            else:
                # Default summary
                metrics = self._get_summary_metrics(start_date, end_date, ambassador_id)
                return self._format_user_count_response(metrics, time_period)

        except Exception as e:
            return f"Error analyzing query: {str(e)}\n\nPlease try rephrasing your question or check that analytics data is available."


# Test the agent
if __name__ == "__main__":
    agent = AnalyticsAgent()

    # Test queries
    test_queries = [
        "How many users did we have this week?",
        "Which ambassador is performing best?",
        "Show me messaging activity",
        "How many QR codes were scanned?"
    ]

    print("Testing AnalyticsAgent:")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 60)
        result = agent.perform(query=query, time_period='week')
        print(result)
        print("=" * 60)
