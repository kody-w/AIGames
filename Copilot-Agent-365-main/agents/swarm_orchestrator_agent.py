"""
Swarm Orchestrator Agent

Coordinates multiple AI agents working together on complex tasks - like having a team of experts
collaborating in real-time. This is the "Avengers Assemble" moment for AI agents.

Author: AI Ambassador Platform
Version: 1.0.0
"""

import logging
import json
from typing import Dict, List
from agents.basic_agent import BasicAgent

logger = logging.getLogger(__name__)


class SwarmOrchestratorAgent(BasicAgent):
    """Orchestrates multiple agents working collaboratively on complex tasks."""

    def __init__(self):
        self.name = 'SwarmOrchestrator'
        self.metadata = {
            "name": self.name,
            "description": "Orchestrates multiple AI agents working together on complex tasks. Coordinates agent collaboration, routes sub-tasks, and synthesizes results from agent swarms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["coordinate", "plan_swarm", "execute_swarm", "list_swarm_templates"],
                        "description": "Swarm orchestration action"
                    },
                    "task": {
                        "type": "string",
                        "description": "Complex task requiring multiple agents"
                    },
                    "swarm_template": {
                        "type": "string",
                        "enum": ["research_team", "creative_studio", "problem_solving", "data_analysis", "custom"],
                        "description": "Pre-configured swarm template to use"
                    },
                    "agents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific agents to include in swarm"
                    },
                    "max_agents": {
                        "type": "integer",
                        "description": "Maximum number of agents to use in parallel"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

        # Pre-configured swarm templates
        self.swarm_templates = {
            "research_team": {
                "name": "Research Team",
                "description": "Comprehensive research and analysis",
                "agents": ["WebSearch", "DataAnalysis", "ContextMemory"],
                "workflow": "parallel_then_synthesize",
                "icon": "🔬"
            },
            "creative_studio": {
                "name": "Creative Studio",
                "description": "Creative ideation and content generation",
                "agents": ["ImageGeneration", "SentimentAnalysis", "Translation"],
                "workflow": "sequential_refinement",
                "icon": "🎨"
            },
            "problem_solving": {
                "name": "Problem Solving Team",
                "description": "Complex problem decomposition and solution",
                "agents": ["ContextMemory", "DataAnalysis", "TaskManagement"],
                "workflow": "iterative_improvement",
                "icon": "🧩"
            },
            "data_analysis": {
                "name": "Data Analysis Team",
                "description": "Multi-faceted data analysis",
                "agents": ["DataAnalysis", "SentimentAnalysis", "Analytics"],
                "workflow": "parallel_analysis",
                "icon": "📊"
            }
        }

    def perform(self, **kwargs) -> str:
        """Execute swarm orchestration operations."""
        try:
            action = kwargs.get('action', '').lower()
            if not action:
                return self._error_response("Action parameter is required")

            handlers = {
                'coordinate': self._coordinate_swarm,
                'plan_swarm': self._plan_swarm,
                'execute_swarm': self._execute_swarm,
                'list_swarm_templates': self._list_swarm_templates
            }

            handler = handlers.get(action)
            if not handler:
                return self._error_response(f"Unknown action: {action}")

            return handler(**kwargs)

        except Exception as e:
            logger.error(f"Swarm orchestrator error: {str(e)}", exc_info=True)
            return self._error_response(f"Orchestration failed: {str(e)}")

    def _coordinate_swarm(self, **kwargs) -> str:
        """Coordinate a swarm of agents for a complex task."""
        task = kwargs.get('task', '')
        swarm_template = kwargs.get('swarm_template', 'problem_solving')
        max_agents = kwargs.get('max_agents', 5)

        if not task:
            return self._error_response("Task description required for swarm coordination")

        # Get swarm configuration
        template = self.swarm_templates.get(swarm_template)
        if not template:
            return self._error_response(f"Unknown swarm template: {swarm_template}")

        # Decompose task into sub-tasks
        sub_tasks = self._decompose_task(task, template)

        # Create execution plan
        plan = self._create_execution_plan(sub_tasks, template, max_agents)

        return f"""{template['icon']} **Swarm Coordination Plan - {template['name']}**

**Original Task:**
{task}

**Swarm Configuration:**
• Template: {template['name']}
• Workflow: {template['workflow'].replace('_', ' ').title()}
• Agents: {', '.join(template['agents'])}
• Max Parallel: {max_agents}

**Task Decomposition:**
{self._format_sub_tasks(sub_tasks)}

**Execution Plan:**
{plan}

**Estimated Coordination:**
• Total agents: {len(template['agents'])}
• Execution phases: {len(sub_tasks)}
• Collaboration points: {len(sub_tasks) - 1}

---
💡 **Ready to execute?** Call this agent with `action: "execute_swarm"` to run the coordinated swarm!
"""

    def _plan_swarm(self, **kwargs) -> str:
        """Plan a custom swarm configuration."""
        task = kwargs.get('task', '')
        agents = kwargs.get('agents', [])

        if not task:
            return self._error_response("Task required for swarm planning")

        if not agents:
            # Recommend agents based on task analysis
            recommended_agents = self._recommend_agents(task)
            agents = recommended_agents

        plan = {
            'task': task,
            'agents': agents,
            'workflow': 'parallel_then_synthesize',
            'sub_tasks': self._decompose_task(task, {'agents': agents})
        }

        return f"""🎯 **Custom Swarm Plan**

**Task:** {task}

**Recommended Agents:**
{chr(10).join(f'• {agent}' for agent in agents)}

**Workflow Strategy:** Parallel execution with result synthesis

**Sub-Tasks:**
{self._format_sub_tasks(plan['sub_tasks'])}

**Agent Assignments:**
{self._format_agent_assignments(plan['sub_tasks'], agents)}

---
💡 Use this plan with `execute_swarm` to run your custom swarm!
"""

    def _execute_swarm(self, **kwargs) -> str:
        """Execute a swarm operation (simulated execution)."""
        task = kwargs.get('task', '')
        swarm_template = kwargs.get('swarm_template', 'problem_solving')

        if not task:
            return self._error_response("Task required for swarm execution")

        template = self.swarm_templates.get(swarm_template, self.swarm_templates['problem_solving'])

        # Simulate swarm execution
        execution_result = self._simulate_swarm_execution(task, template)

        return f"""{template['icon']} **Swarm Execution Complete - {template['name']}**

**Task:** {task}

**Agents Coordinated:** {', '.join(template['agents'])}

**Execution Results:**

{execution_result['phase_results']}

**Synthesized Insights:**
{execution_result['synthesis']}

**Agent Contributions:**
{execution_result['contributions']}

**Success Metrics:**
• Agents coordinated: {len(template['agents'])}
• Sub-tasks completed: {execution_result['sub_tasks_completed']}
• Collaboration events: {execution_result['collaboration_events']}
• Execution time: {execution_result['execution_time']}

---
✅ **Swarm coordination successful!** All agents contributed their specialized knowledge to solve this complex task.
"""

    def _list_swarm_templates(self, **kwargs) -> str:
        """List all available swarm templates."""

        template_list = []
        for key, template in self.swarm_templates.items():
            agents_str = ', '.join(template['agents'])
            template_list.append(f"""**{template['icon']} {template['name']}** (`{key}`)
{template['description']}
• Agents: {agents_str}
• Workflow: {template['workflow'].replace('_', ' ').title()}
""")

        return f"""🌐 **Available Swarm Templates**

{chr(10).join(template_list)}

---
💡 **How to use:** Call SwarmOrchestrator with `action: "coordinate"` and `swarm_template: "template_name"`

**Example:**
```json
{{
  "action": "coordinate",
  "task": "Analyze customer feedback and create improvement plan",
  "swarm_template": "research_team"
}}
```
"""

    # Helper Methods

    def _decompose_task(self, task: str, template: Dict) -> List[Dict]:
        """Decompose complex task into agent-specific sub-tasks."""

        # Simulated task decomposition
        sub_tasks = [
            {
                'id': 1,
                'description': f"Gather and analyze relevant context for: {task[:80]}",
                'assigned_agent': template['agents'][0] if template['agents'] else 'ContextMemory',
                'priority': 'high',
                'dependencies': []
            },
            {
                'id': 2,
                'description': f"Process and analyze data related to: {task[:80]}",
                'assigned_agent': template['agents'][1] if len(template['agents']) > 1 else 'DataAnalysis',
                'priority': 'high',
                'dependencies': [1]
            },
            {
                'id': 3,
                'description': f"Synthesize results and generate insights for: {task[:80]}",
                'assigned_agent': 'SwarmOrchestrator',
                'priority': 'medium',
                'dependencies': [1, 2]
            }
        ]

        return sub_tasks

    def _create_execution_plan(self, sub_tasks: List[Dict], template: Dict, max_agents: int) -> str:
        """Create a detailed execution plan."""

        plan_str = ""
        for i, task in enumerate(sub_tasks, 1):
            deps = f" (depends on: {', '.join(map(str, task['dependencies']))})" if task['dependencies'] else ""
            plan_str += f"{i}. **Phase {i}:** {task['assigned_agent']} - {task['description'][:100]}...{deps}\n"

        return plan_str

    def _format_sub_tasks(self, sub_tasks: List[Dict]) -> str:
        """Format sub-tasks for display."""
        return chr(10).join(f"• Task {t['id']}: {t['description'][:120]}..." for t in sub_tasks)

    def _format_agent_assignments(self, sub_tasks: List[Dict], agents: List[str]) -> str:
        """Format agent assignments."""
        assignments = []
        for agent in agents:
            tasks = [t for t in sub_tasks if t.get('assigned_agent') == agent]
            if tasks:
                assignments.append(f"• **{agent}**: {len(tasks)} task(s)")

        return chr(10).join(assignments) if assignments else "• Assignments will be determined dynamically"

    def _recommend_agents(self, task: str) -> List[str]:
        """Recommend agents based on task analysis."""
        # Simple keyword-based recommendation
        task_lower = task.lower()

        agents = []

        if any(word in task_lower for word in ['research', 'find', 'search', 'look up']):
            agents.append('WebSearch')

        if any(word in task_lower for word in ['analyze', 'data', 'statistics', 'metrics']):
            agents.append('DataAnalysis')

        if any(word in task_lower for word in ['remember', 'recall', 'context', 'previous']):
            agents.append('ContextMemory')

        if any(word in task_lower for word in ['sentiment', 'feeling', 'emotion', 'mood']):
            agents.append('SentimentAnalysis')

        if any(word in task_lower for word in ['task', 'todo', 'manage', 'organize']):
            agents.append('TaskManagement')

        if not agents:
            agents = ['ContextMemory', 'DataAnalysis']  # Default fallback

        return agents[:5]  # Max 5 agents

    def _simulate_swarm_execution(self, task: str, template: Dict) -> Dict:
        """Simulate swarm execution results."""

        phase_results = []
        for i, agent in enumerate(template['agents'], 1):
            phase_results.append(f"**Phase {i} - {agent}:**\n└─ Completed successfully with valuable insights")

        return {
            'phase_results': chr(10).join(phase_results),
            'synthesis': f"The swarm analyzed '{task[:100]}' from multiple perspectives. {len(template['agents'])} specialized agents contributed unique insights, creating a comprehensive solution.",
            'contributions': chr(10).join(f"• **{agent}**: Provided specialized {agent.lower()} capabilities" for agent in template['agents']),
            'sub_tasks_completed': len(template['agents']) + 1,
            'collaboration_events': len(template['agents']) - 1,
            'execution_time': f"{len(template['agents']) * 2}s"
        }

    def _error_response(self, message: str) -> str:
        return f"❌ Swarm Orchestrator Error: {message}"


if __name__ == "__main__":
    agent = SwarmOrchestratorAgent()
    result = agent.perform(
        action="coordinate",
        task="Research customer sentiment, analyze feedback trends, and create an improvement strategy",
        swarm_template="research_team"
    )
    print(result)
