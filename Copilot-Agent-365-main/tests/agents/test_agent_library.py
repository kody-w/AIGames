"""
Comprehensive test suite for AI Ambassador Agent Library
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Import agents
from agents.calendar_agent import CalendarAgent
from agents.data_analysis_agent import DataAnalysisAgent
from agents.document_agent import DocumentAgent
from agents.email_agent import EmailAgent
from agents.task_management_agent import TaskManagementAgent


class TestCalendarAgent(unittest.TestCase):
    """Test suite for Calendar Agent"""

    def setUp(self):
        self.agent = CalendarAgent()

    def test_create_event(self):
        """Test event creation"""
        result = self.agent.perform(
            action="schedule_meeting",
            title="Test Meeting",
            start_time="2025-11-08T14:00:00",
            end_time="2025-11-08T15:00:00",
            attendees=["test@example.com"],
        )
        self.assertIn("Meeting scheduled successfully", result)
        self.assertIn("Test Meeting", result)

    def test_check_availability(self):
        """Test availability checking"""
        result = self.agent.perform(
            action="check_availability",
            start_time="2025-11-08T14:00:00",
            end_time="2025-11-08T15:00:00",
            attendees=["test@example.com"],
        )
        self.assertIn("Group Availability Check", result)
        self.assertIn("test@example.com", result)


class TestEmailAgent(unittest.TestCase):
    """Test suite for Email Agent"""

    def setUp(self):
        self.agent = EmailAgent()

    def test_compose_email(self):
        """Test email composition"""
        result = self.agent.perform(
            action="draft",
            recipient="recipient@example.com",
            subject="Test Email",
            body="Test message",
            tone="professional",
        )
        self.assertIn("Email Draft Created", result)
        self.assertIn("Test Email", result)


class TestDataAnalysisAgent(unittest.TestCase):
    """Test suite for Data Analysis Agent"""

    def setUp(self):
        self.agent = DataAnalysisAgent()

    def test_calculate_statistics(self):
        """Test statistics calculation"""
        data = json.dumps([100, 150, 200, 175, 225, 190])
        result = self.agent.perform(action="statistics", data=data)
        self.assertIn("Statistical Analysis", result)
        self.assertIn("Mean", result)
        self.assertIn("Median", result)


class TestDocumentAgent(unittest.TestCase):
    """Test suite for Document Agent"""

    def setUp(self):
        self.agent = DocumentAgent()

    def test_create_document(self):
        """Test document creation"""
        result = self.agent.perform(
            action="create",
            title="Business Letter",
            content="Dear John Doe, Test content",
        )
        self.assertIn("Document Created", result)
        self.assertIn("Business Letter", result)

    def test_convert_format(self):
        """Test format conversion"""
        result = self.agent.perform(
            action="convert",
            format_from="word",
            format_to="pdf",
            content="Test content",
        )
        self.assertIn("Document Converted", result)
        self.assertIn("Conversion successful", result)


class TestTaskManagementAgent(unittest.TestCase):
    """Test suite for Task Management Agent"""

    def setUp(self):
        self.agent = TaskManagementAgent()

    def test_create_task(self):
        """Test task creation"""
        result = self.agent.perform(
            action="create_task",
            task_title="Test Task",
            description="Test description",
            priority="high",
        )
        self.assertIn("Task Created", result)
        self.assertIn("Test Task", result)

    def test_list_tasks(self):
        """Test task listing"""
        result = self.agent.perform(action="list_tasks")
        self.assertIn("tasks", result)

    def test_complete_task(self):
        """Test task completion"""
        # First create a task
        create_result = self.agent.perform(
            action="create_task", task_title="Task to Complete"
        )
        # Extract task ID (simplified)
        task_id = "task_0001"

        result = self.agent.perform(action="complete_task", task_id=task_id)
        self.assertIn("Completed", result)


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
        result = agent.perform(action="draft")
        self.assertIn("Error", result)

    def test_invalid_date_format(self):
        """Test invalid date format"""
        agent = CalendarAgent()
        result = agent.perform(
            action="schedule_meeting",
            title="Test",
            start_time="invalid-date",
            end_time="invalid-date",
        )
        self.assertIn("Error", result)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCalendarAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestDataAnalysisAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskManagementAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentErrorHandling))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result


if __name__ == "__main__":
    run_tests()
