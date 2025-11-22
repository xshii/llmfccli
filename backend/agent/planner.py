"""
Intent recognition and TODO generation for task planning
"""

import json
from typing import Dict, Any, List, Optional
from ..llm.client import OllamaClient
from ..llm.prompts import get_intent_prompt, get_todo_prompt


class Planner:
    """Task planner with intent recognition and TODO generation"""
    
    def __init__(self, client: Optional[OllamaClient] = None):
        """
        Initialize planner
        
        Args:
            client: OllamaClient instance
        """
        self.client = client or OllamaClient()
    
    def recognize_intent(self, user_input: str, 
                        project_root: str = "",
                        active_file: str = "",
                        recent_changes: str = "") -> Dict[str, Any]:
        """
        Recognize user intent and estimate required tools
        
        Args:
            user_input: User's request
            project_root: Project root directory
            active_file: Currently active file
            recent_changes: Recent changes summary
            
        Returns:
            Dict with task_type, estimated_tools, estimated_complexity, reasoning
        """
        prompt = get_intent_prompt(
            user_input=user_input,
            project_root=project_root,
            active_file=active_file,
            recent_changes=recent_changes
        )
        
        messages = [
            {'role': 'system', 'content': 'You are a task intent analyzer.'},
            {'role': 'user', 'content': prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.3)
            content = response['message']['content']
            
            # Extract JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            # Validate result
            if 'task_type' not in result:
                result['task_type'] = 'general'
            if 'estimated_tools' not in result:
                result['estimated_tools'] = []
            if 'estimated_complexity' not in result:
                result['estimated_complexity'] = 'medium'
            
            return result
            
        except Exception as e:
            # Fallback to default
            return {
                'task_type': 'general',
                'estimated_tools': ['view_file', 'edit_file'],
                'estimated_complexity': 'medium',
                'reasoning': f'Failed to parse intent: {e}'
            }
    
    def generate_todo(self, task_description: str, 
                     context: str = "",
                     intent: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate TODO list for task execution
        
        Args:
            task_description: Task description
            context: Additional context
            intent: Optional intent recognition result
            
        Returns:
            Dict with todos, estimated_steps, risks
        """
        # Add intent to context if available
        if intent:
            context += f"\n\nIntent: {intent.get('task_type', 'general')}"
            context += f"\nEstimated tools: {', '.join(intent.get('estimated_tools', []))}"
        
        prompt = get_todo_prompt(
            task_description=task_description,
            context=context
        )
        
        messages = [
            {'role': 'system', 'content': 'You are a task planning assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        try:
            response = self.client.chat(messages, temperature=0.3)
            content = response['message']['content']
            
            # Extract JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            # Validate result
            if 'todos' not in result:
                result['todos'] = []
            if 'estimated_steps' not in result:
                result['estimated_steps'] = len(result['todos'])
            if 'risks' not in result:
                result['risks'] = []
            
            return result
            
        except Exception as e:
            # Fallback to simple TODO
            return {
                'todos': [
                    {
                        'step': 1,
                        'action': 'Analyze the task requirements',
                        'tool': 'view_file',
                        'priority': 'high'
                    },
                    {
                        'step': 2,
                        'action': 'Execute the task',
                        'tool': 'edit_file',
                        'priority': 'high'
                    }
                ],
                'estimated_steps': 2,
                'risks': [f'Failed to generate detailed plan: {e}']
            }
    
    def update_todo(self, todos: List[Dict[str, Any]], 
                   completed_step: int,
                   result: Any) -> List[Dict[str, Any]]:
        """
        Update TODO list based on execution result
        
        Args:
            todos: Current TODO list
            completed_step: Completed step number
            result: Execution result
            
        Returns:
            Updated TODO list
        """
        # Mark step as completed
        for todo in todos:
            if todo.get('step') == completed_step:
                todo['status'] = 'completed'
                todo['result'] = str(result)[:100]  # Keep result summary
        
        # Re-prioritize remaining steps if needed
        remaining = [t for t in todos if t.get('status') != 'completed']
        
        # If step failed, may need to adjust
        if isinstance(result, dict) and 'error' in result:
            # Mark remaining steps as pending review
            for todo in remaining:
                if todo.get('priority') == 'high':
                    todo['priority'] = 'review'
        
        return todos
    
    def format_todo_display(self, todos: List[Dict[str, Any]]) -> str:
        """
        Format TODO list for display
        
        Args:
            todos: TODO list
            
        Returns:
            Formatted string
        """
        lines = ["TODO List:", "=" * 50]
        
        for todo in todos:
            step = todo.get('step', '?')
            action = todo.get('action', 'Unknown action')
            tool = todo.get('tool', '')
            priority = todo.get('priority', 'medium')
            status = todo.get('status', 'pending')
            
            status_icon = '✓' if status == 'completed' else '○'
            priority_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢',
                'review': '🔵'
            }.get(priority, '⚪')
            
            line = f"{status_icon} Step {step}: {action}"
            if tool:
                line += f" [{tool}]"
            line += f" {priority_icon}"
            
            lines.append(line)
        
        return '\n'.join(lines)
