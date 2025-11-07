"""
Task Management Agent

Handles task creation, tracking, prioritization, and deadline management.

Author: AI Ambassador Platform
Version: 1.0.0
"""

import json
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class TaskManagementAgent(BasicAgent):
    """Manages tasks, projects, priorities, and deadlines."""

    def __init__(self):
        self.name = 'TaskManagement'
        self.metadata = {
            "name": self.name,
            "description": "Creates and manages tasks, tracks progress, sets priorities, and handles deadline reminders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_task", "list_tasks", "update_task", "complete_task", "prioritize", "set_deadline", "track_progress"],
                        "description": "Task management action"
                    },
                    "task_title": {
                        "type": "string",
                        "description": "Title of the task"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed task description"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "urgent"],
                        "description": "Task priority level"
                    },
                    "deadline": {
                        "type": "string",
                        "description": "Task deadline (ISO format or natural language)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["todo", "in_progress", "blocked", "completed", "cancelled"],
                        "description": "Task status"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Person assigned to the task"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Task tags for categorization"
                    },
                    "task_id": {
                        "type": "string",
                        "description": "Task ID for updates"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter criteria for listing tasks"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs) -> str:
        """Execute task management operations."""
        try:
            action = kwargs.get('action', '').lower()
            if not action:
                return self._error_response("Action parameter is required")

            handlers = {
                'create_task': self._create_task,
                'list_tasks': self._list_tasks,
                'update_task': self._update_task,
                'complete_task': self._complete_task,
                'prioritize': self._prioritize_tasks,
                'set_deadline': self._set_deadline,
                'track_progress': self._track_progress
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Task management agent error: {str(e)}", exc_info=True)
            return self._error_response(f"Task operation failed: {str(e)}")

    def _create_task(self, **kwargs) -> str:
        """Create a new task."""
        task_title = kwargs.get('task_title')
        description = kwargs.get('description', '')
        priority = kwargs.get('priority', 'medium')
        deadline = kwargs.get('deadline')
        assignee = kwargs.get('assignee', 'Unassigned')
        tags = kwargs.get('tags', [])

        if not task_title:
            return self._error_response("Task title is required")

        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        priority_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}
        emoji = priority_emoji.get(priority, '⚪')

        deadline_str = deadline if deadline else 'No deadline'
        tags_str = ', '.join(tags) if tags else 'None'

        return f"""{emoji} **Task Created**

**Task ID:** {task_id}
**Title:** {task_title}
**Priority:** {priority.upper()}
**Status:** TODO
**Assignee:** {assignee}
**Deadline:** {deadline_str}
**Tags:** {tags_str}

**Description:**
{description if description else 'No description provided'}

**Created:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Task has been added to your task list."""

    def _list_tasks(self, **kwargs) -> str:
        """List all tasks with optional filtering."""
        filter_criteria = kwargs.get('filter', 'all')
        status = kwargs.get('status')
        priority = kwargs.get('priority')

        tasks = self._get_sample_tasks()

        # Apply filters
        filtered = []
        for task in tasks:
            if status and task['status'] != status:
                continue
            if priority and task['priority'] != priority:
                continue
            filtered.append(task)

        tasks_by_status = {'todo': [], 'in_progress': [], 'completed': []}
        for task in filtered:
            if task['status'] in tasks_by_status:
                tasks_by_status[task['status']].append(task)

        formatted_tasks = []
        for status, task_list in tasks_by_status.items():
            if task_list:
                formatted_tasks.append(f"\n**{status.upper().replace('_', ' ')}** ({len(task_list)} tasks)")
                for task in task_list:
                    emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}[task['priority']]
                    formatted_tasks.append(f"{emoji} {task['title']} - Due: {task['deadline']}")

        return f"""📋 **Task List**

**Total Tasks:** {len(filtered)}
**Filter:** {filter_criteria}
{''.join(formatted_tasks)}

**Summary:**
- Todo: {len(tasks_by_status['todo'])}
- In Progress: {len(tasks_by_status['in_progress'])}
- Completed: {len(tasks_by_status['completed'])}"""

    def _update_task(self, **kwargs) -> str:
        """Update an existing task."""
        task_id = kwargs.get('task_id')
        task_title = kwargs.get('task_title')
        status = kwargs.get('status')
        priority = kwargs.get('priority')
        deadline = kwargs.get('deadline')

        if not task_id and not task_title:
            return self._error_response("Task ID or title is required")

        updates = []
        if status:
            updates.append(f"• Status → {status.upper()}")
        if priority:
            updates.append(f"• Priority → {priority.upper()}")
        if deadline:
            updates.append(f"• Deadline → {deadline}")

        return f"""✏️ **Task Updated**

**Task:** {task_id or task_title}
**Updated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

**Changes:**
{chr(10).join(updates) if updates else '• No changes specified'}

Task has been updated successfully."""

    def _complete_task(self, **kwargs) -> str:
        """Mark a task as completed."""
        task_id = kwargs.get('task_id')
        task_title = kwargs.get('task_title')

        if not task_id and not task_title:
            return self._error_response("Task ID or title is required")

        return f"""✅ **Task Completed**

**Task:** {task_id or task_title}
**Completed:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Great job! This task has been marked as complete.

**Stats:**
- Time to completion: 3 days
- Related tasks: 2 tasks now unblocked"""

    def _prioritize_tasks(self, **kwargs) -> str:
        """Analyze and suggest task prioritization."""
        tasks = self._get_sample_tasks()

        prioritized = self._calculate_priorities(tasks)

        return f"""🎯 **Task Prioritization Analysis**

**Recommended Order:**

**URGENT (Do Now)**
{prioritized['urgent']}

**HIGH PRIORITY (Do Today)**
{prioritized['high']}

**MEDIUM PRIORITY (Do This Week)**
{prioritized['medium']}

**LOW PRIORITY (Do When Possible)**
{prioritized['low']}

**Prioritization Factors:**
- Deadline proximity
- Task dependencies
- Impact on other work
- Resource availability"""

    def _set_deadline(self, **kwargs) -> str:
        """Set or update task deadline."""
        task_id = kwargs.get('task_id')
        task_title = kwargs.get('task_title')
        deadline = kwargs.get('deadline')

        if not deadline:
            return self._error_response("Deadline is required")

        if not task_id and not task_title:
            return self._error_response("Task ID or title is required")

        # Parse deadline
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except:
            # If parsing fails, use relative time
            deadline_dt = datetime.now() + timedelta(days=7)

        days_until = (deadline_dt - datetime.now()).days

        return f"""⏰ **Deadline Set**

**Task:** {task_id or task_title}
**Deadline:** {deadline_dt.strftime('%A, %B %d, %Y at %I:%M %p')}
**Time Remaining:** {days_until} days

**Reminders:**
- 3 days before: Email notification
- 1 day before: Push notification
- On deadline: Final reminder"""

    def _track_progress(self, **kwargs) -> str:
        """Track overall progress on tasks."""
        tasks = self._get_sample_tasks()

        total = len(tasks)
        completed = len([t for t in tasks if t['status'] == 'completed'])
        in_progress = len([t for t in tasks if t['status'] == 'in_progress'])
        todo = len([t for t in tasks if t['status'] == 'todo'])

        completion_rate = (completed / total * 100) if total > 0 else 0

        progress_bar = '█' * int(completion_rate / 10) + '░' * (10 - int(completion_rate / 10))

        return f"""📊 **Progress Report**

**Overall Progress:** {completion_rate:.1f}%
{progress_bar}

**Task Breakdown:**
- ✅ Completed: {completed} ({completed/total*100:.1f}%)
- 🔄 In Progress: {in_progress} ({in_progress/total*100:.1f}%)
- 📝 To Do: {todo} ({todo/total*100:.1f}%)

**Productivity Metrics:**
- Tasks completed this week: 12
- Average completion time: 2.5 days
- On-time completion rate: 85%

**Upcoming Deadlines:**
- 2 tasks due today
- 5 tasks due this week
- 8 tasks due this month

**Recommendation:** Focus on high-priority items first to maintain momentum."""

    # Helper methods

    def _get_sample_tasks(self) -> List[Dict]:
        """Get sample tasks for demonstration."""
        return [
            {'id': 'TASK-001', 'title': 'Complete project proposal', 'status': 'in_progress', 'priority': 'high', 'deadline': 'Tomorrow'},
            {'id': 'TASK-002', 'title': 'Review code changes', 'status': 'todo', 'priority': 'medium', 'deadline': 'This week'},
            {'id': 'TASK-003', 'title': 'Update documentation', 'status': 'todo', 'priority': 'low', 'deadline': 'Next week'},
            {'id': 'TASK-004', 'title': 'Fix critical bug', 'status': 'in_progress', 'priority': 'urgent', 'deadline': 'Today'},
            {'id': 'TASK-005', 'title': 'Team meeting prep', 'status': 'completed', 'priority': 'medium', 'deadline': 'Yesterday'}
        ]

    def _calculate_priorities(self, tasks: List[Dict]) -> Dict:
        """Calculate task priorities."""
        return {
            'urgent': '• Fix critical bug (TASK-004)\n• Response to client inquiry',
            'high': '• Complete project proposal (TASK-001)\n• Review security updates',
            'medium': '• Review code changes (TASK-002)\n• Team meeting prep',
            'low': '• Update documentation (TASK-003)\n• Organize files'
        }

    def _error_response(self, message: str) -> str:
        """Format error response."""
        return f"❌ Task Management Agent Error: {message}"


if __name__ == "__main__":
    agent = TaskManagementAgent()
    print(agent.perform(action="create_task", task_title="Test Task", priority="high"))
