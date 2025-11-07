"""
Comprehensive test suite for AI Ambassador Agent Library
"""
import unittest
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import agents
from agents.calendar_agent import CalendarAgent
from agents.email_agent import EmailAgent
from agents.data_analysis_agent import DataAnalysisAgent
from agents.web_research_agent import WebResearchAgent
from agents.document_agent import DocumentAgent
from agents.task_management_agent import TaskManagementAgent
from agents.knowledge_base_agent import KnowledgeBaseAgent
from agents.notification_agent import NotificationAgent


class TestCalendarAgent(unittest.TestCase):
    """Test suite for Calendar Agent"""

    def setUp(self):
        self.agent = CalendarAgent()

    def test_create_event(self):
        """Test event creation"""
        result = self.agent.perform(
            action="create_event",
            title="Test Meeting",
            start="2025-11-08T14:00:00",
            end="2025-11-08T15:00:00",
            attendees=["test@example.com"]
        )
        self.assertIn("Event created successfully", result)
        self.assertIn("Test Meeting", result)

    def test_check_availability(self):
        """Test availability checking"""
        result = self.agent.perform(
            action="check_availability",
            start="2025-11-08T14:00:00",
            end="2025-11-08T15:00:00",
            attendees=["test@example.com"]
        )
        self.assertIn("Availability for", result)


class TestEmailAgent(unittest.TestCase):
    """Test suite for Email Agent"""

    def setUp(self):
        self.agent = EmailAgent()

    def test_compose_email(self):
        """Test email composition"""
        result = self.agent.perform(
            action="compose_email",
            to=["recipient@example.com"],
            subject="Test Email",
            body_template="professional",
            context={"recipient_name": "John", "message": "Test message"}
        )
        self.assertIn("Email composed successfully", result)

    def test_send_email(self):
        """Test email sending"""
        result = self.agent.perform(
            action="send_email",
            to=["recipient@example.com"],
            subject="Test",
            body="Test body"
        )
        self.assertIn("Email sent successfully", result)


class TestDataAnalysisAgent(unittest.TestCase):
    """Test suite for Data Analysis Agent"""

    def setUp(self):
        self.agent = DataAnalysisAgent()

    def test_calculate_statistics(self):
        """Test statistics calculation"""
        data = json.dumps([100, 150, 200, 175, 225, 190])
        result = self.agent.perform(
            action="calculate_statistics",
            data=data
        )
        self.assertIn("Statistical Analysis Results", result)
        self.assertIn("Mean", result)
        self.assertIn("Median", result)

    def test_detect_outliers(self):
        """Test outlier detection"""
        data = json.dumps([100, 150, 200, 175, 225, 190, 500, 1000])
        result = self.agent.perform(
            action="detect_outliers",
            data=data
        )
        self.assertIn("Outlier Detection Results", result)


class TestWebResearchAgent(unittest.TestCase):
    """Test suite for Web Research Agent"""

    def setUp(self):
        self.agent = WebResearchAgent()

    def test_search_web(self):
        """Test web search"""
        result = self.agent.perform(
            action="search_web",
            query="AI ambassadors",
            num_results=5
        )
        self.assertIn("Found", result)
        self.assertIn("results", result)

    def test_generate_citations(self):
        """Test citation generation"""
        sources = [{
            "author": "Smith, J.",
            "year": "2025",
            "title": "Test Article",
            "source": "Test Journal",
            "url": "https://example.com"
        }]
        result = self.agent.perform(
            action="generate_citations",
            sources=sources,
            citation_format="apa"
        )
        self.assertIn("APA", result)
        self.assertIn("Smith, J.", result)


class TestDocumentAgent(unittest.TestCase):
    """Test suite for Document Agent"""

    def setUp(self):
        self.agent = DocumentAgent()

    def test_create_document(self):
        """Test document creation"""
        result = self.agent.perform(
            action="create_document",
            template="business_letter",
            data={
                "recipient_name": "John Doe",
                "body": "Test content"
            }
        )
        self.assertIn("Document created successfully", result)

    def test_convert_format(self):
        """Test format conversion"""
        result = self.agent.perform(
            action="convert_format",
            file_path="/tmp/test.docx",
            target_format="pdf"
        )
        self.assertIn("Document Converted Successfully", result)


class TestTaskManagementAgent(unittest.TestCase):
    """Test suite for Task Management Agent"""

    def setUp(self):
        self.agent = TaskManagementAgent()

    def test_create_task(self):
        """Test task creation"""
        result = self.agent.perform(
            action="create_task",
            title="Test Task",
            description="Test description",
            priority="high"
        )
        self.assertIn("Task Created Successfully", result)

    def test_list_tasks(self):
        """Test task listing"""
        result = self.agent.perform(action="list_tasks")
        self.assertIn("tasks", result)

    def test_complete_task(self):
        """Test task completion"""
        # First create a task
        create_result = self.agent.perform(
            action="create_task",
            title="Task to Complete"
        )
        # Extract task ID (simplified)
        task_id = "task_0001"

        result = self.agent.perform(
            action="complete_task",
            task_id=task_id
        )
        self.assertIn("Completed", result)


class TestKnowledgeBaseAgent(unittest.TestCase):
    """Test suite for Knowledge Base Agent"""

    def setUp(self):
        self.agent = KnowledgeBaseAgent()

    def test_add_article(self):
        """Test article addition"""
        result = self.agent.perform(
            action="add_article",
            title="Test Article",
            content="Test content for the article",
            category="Testing",
            tags=["test", "example"]
        )
        self.assertIn("Article Added Successfully", result)

    def test_search_kb(self):
        """Test knowledge base search"""
        result = self.agent.perform(
            action="search_kb",
            query="getting started"
        )
        self.assertIn("article", result)


class TestNotificationAgent(unittest.TestCase):
    """Test suite for Notification Agent"""

    def setUp(self):
        self.agent = NotificationAgent()

    def test_send_sms(self):
        """Test SMS sending"""
        result = self.agent.perform(
            action="send_sms",
            to="+12345678900",
            message="Test SMS"
        )
        self.assertIn("SMS Sent Successfully", result)

    def test_send_email_notification(self):
        """Test email notification"""
        result = self.agent.perform(
            action="send_email_notification",
            to="test@example.com",
            template="welcome",
            data={"name": "John"}
        )
        self.assertIn("Email Sent Successfully", result)

    def test_send_batch(self):
        """Test batch notifications"""
        notifications = [
            {"type": "sms", "recipient": "+12345678900", "message": "Test 1"},
            {"type": "email", "recipient": "test@example.com", "message": "Test 2"}
        ]
        result = self.agent.perform(
            action="send_batch",
            notifications=notifications
        )
        self.assertIn("Batch Notifications Sent", result)


class TestAgentErrorHandling(unittest.TestCase):
    """Test error handling across agents"""

    def test_invalid_action(self):
        """Test invalid action handling"""
        agent = CalendarAgent()
        result = agent.perform(action="invalid_action")
        self.assertIn("Error", result)

    def test_missing_required_parameter(self):
        """Test missing parameter handling"""
        agent = EmailAgent()
        result = agent.perform(action="send_email")
        self.assertIn("Error", result)

    def test_invalid_date_format(self):
        """Test invalid date format"""
        agent = CalendarAgent()
        result = agent.perform(
            action="create_event",
            title="Test",
            start="invalid-date",
            end="invalid-date"
        )
        self.assertIn("Error", result)


class TestAgentRegistry(unittest.TestCase):
    """Test agent registry functionality"""

    def test_agent_discovery(self):
        """Test that agents can be discovered"""
        from utils.agent_registry import AgentRegistry

        registry = AgentRegistry()
        count = registry.register_all_agents()

        self.assertGreaterEqual(count, 12, "Should discover at least 12 agents")

    def test_agent_metadata(self):
        """Test agent metadata retrieval"""
        from utils.agent_registry import AgentRegistry

        registry = AgentRegistry()
        registry.register_all_agents()

        metadata = registry.get_all_metadata()
        self.assertIsInstance(metadata, list)
        self.assertGreater(len(metadata), 0)

    def test_health_check(self):
        """Test agent health checking"""
        from utils.agent_registry import AgentRegistry

        registry = AgentRegistry()
        registry.register_all_agents()

        health = registry.health_check_all()
        self.assertIsInstance(health, dict)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCalendarAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestDataAnalysisAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestWebResearchAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskManagementAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestKnowledgeBaseAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentRegistry))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result


if __name__ == "__main__":
    run_tests()
