"""
Agent Collaboration Utilities

Provides inter-agent communication, shared context management, and result aggregation
for multi-agent swarm operations.

Author: AI Ambassador Platform
Version: 1.0.0
"""

import logging
import json
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentCollaboration:
    """Manages collaboration between multiple agents."""

    def __init__(self):
        self.shared_context = {}
        self.agent_results = {}
        self.collaboration_events = []

    def register_agent_result(self, agent_name: str, result: Any, metadata: Dict = None):
        """Register a result from an agent."""
        self.agent_results[agent_name] = {
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        self.collaboration_events.append({
            'type': 'result_registered',
            'agent': agent_name,
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"Agent {agent_name} registered result")

    def get_agent_result(self, agent_name: str) -> Any:
        """Get result from a specific agent."""
        return self.agent_results.get(agent_name, {}).get('result')

    def update_shared_context(self, key: str, value: Any):
        """Update shared context accessible to all agents."""
        self.shared_context[key] = value

        self.collaboration_events.append({
            'type': 'context_updated',
            'key': key,
            'timestamp': datetime.now().isoformat()
        })

    def get_shared_context(self, key: str = None) -> Any:
        """Get shared context."""
        if key:
            return self.shared_context.get(key)
        return self.shared_context

    def aggregate_results(self, strategy: str = 'concatenate') -> str:
        """Aggregate results from all agents."""
        if strategy == 'concatenate':
            return self._concatenate_results()
        elif strategy == 'synthesize':
            return self._synthesize_results()
        elif strategy == 'vote':
            return self._vote_on_results()
        else:
            return self._concatenate_results()

    def _concatenate_results(self) -> str:
        """Concatenate all agent results."""
        results = []
        for agent_name, data in self.agent_results.items():
            results.append(f"**{agent_name}:**\n{data['result']}\n")

        return "\n".join(results)

    def _synthesize_results(self) -> str:
        """Synthesize results into cohesive output."""
        # Simulated synthesis
        summary = f"Synthesized insights from {len(self.agent_results)} agents:\n"

        for agent_name, data in self.agent_results.items():
            result_preview = str(data['result'])[:100]
            summary += f"• {agent_name} contributed: {result_preview}...\n"

        return summary

    def _vote_on_results(self) -> str:
        """Use voting to determine consensus."""
        # Simulated voting
        if not self.agent_results:
            return "No results to vote on"

        # Count similar results
        result_counts = {}
        for data in self.agent_results.values():
            result_str = str(data['result'])
            result_counts[result_str] = result_counts.get(result_str, 0) + 1

        # Get most common result
        consensus = max(result_counts, key=result_counts.get)
        vote_count = result_counts[consensus]

        return f"Consensus result ({vote_count}/{len(self.agent_results)} votes):\n{consensus}"

    def get_collaboration_summary(self) -> Dict:
        """Get summary of collaboration activity."""
        return {
            'total_agents': len(self.agent_results),
            'collaboration_events': len(self.collaboration_events),
            'shared_context_keys': list(self.shared_context.keys()),
            'timeline': self.collaboration_events[-10:]  # Last 10 events
        }

    def clear(self):
        """Clear all collaboration data."""
        self.shared_context.clear()
        self.agent_results.clear()
        self.collaboration_events.clear()


class ConflictResolver:
    """Resolves conflicts when agents disagree."""

    @staticmethod
    def resolve_disagreement(agent_results: Dict[str, Any], strategy: str = 'majority') -> Any:
        """Resolve conflicts between agent results."""

        if strategy == 'majority':
            return ConflictResolver._majority_vote(agent_results)
        elif strategy == 'confidence':
            return ConflictResolver._highest_confidence(agent_results)
        elif strategy == 'synthesis':
            return ConflictResolver._synthesize_disagreement(agent_results)
        else:
            return ConflictResolver._majority_vote(agent_results)

    @staticmethod
    def _majority_vote(agent_results: Dict[str, Any]) -> Any:
        """Return result with majority agreement."""
        if not agent_results:
            return None

        # Count occurrences of each result
        result_counts = {}
        for result in agent_results.values():
            result_str = str(result)
            result_counts[result_str] = result_counts.get(result_str, 0) + 1

        # Return most common
        return max(result_counts, key=result_counts.get)

    @staticmethod
    def _highest_confidence(agent_results: Dict[str, Any]) -> Any:
        """Return result from agent with highest confidence."""
        # Simulated confidence-based selection
        return list(agent_results.values())[0] if agent_results else None

    @staticmethod
    def _synthesize_disagreement(agent_results: Dict[str, Any]) -> str:
        """Synthesize disagreeing results into cohesive output."""
        synthesis = "Agents provided different perspectives:\n\n"

        for i, (agent, result) in enumerate(agent_results.items(), 1):
            synthesis += f"{i}. **{agent}** suggests: {result}\n"

        synthesis += "\nConsidering all perspectives for a balanced approach."

        return synthesis


class SwarmCommunicationProtocol:
    """Defines communication protocol for agent swarms."""

    MESSAGE_TYPES = {
        'TASK_ASSIGNMENT': 'task_assignment',
        'RESULT_SUBMISSION': 'result_submission',
        'CONTEXT_SHARE': 'context_share',
        'REQUEST_HELP': 'request_help',
        'COMPLETION': 'completion'
    }

    @staticmethod
    def create_message(msg_type: str, sender: str, recipient: str, payload: Dict) -> Dict:
        """Create a standardized swarm message."""
        return {
            'type': msg_type,
            'sender': sender,
            'recipient': recipient,
            'payload': payload,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def parse_message(message: Dict) -> Dict:
        """Parse and validate swarm message."""
        required_fields = ['type', 'sender', 'recipient', 'payload']

        for field in required_fields:
            if field not in message:
                raise ValueError(f"Missing required field: {field}")

        return {
            'valid': True,
            'type': message['type'],
            'sender': message['sender'],
            'recipient': message['recipient'],
            'payload': message['payload']
        }


if __name__ == "__main__":
    # Test collaboration
    collab = AgentCollaboration()

    collab.register_agent_result('Agent1', 'Result from agent 1')
    collab.register_agent_result('Agent2', 'Result from agent 2')
    collab.update_shared_context('task_id', '123')

    print(collab.aggregate_results('synthesize'))
    print(json.dumps(collab.get_collaboration_summary(), indent=2))
