"""
Task representation and execution.
"""

from typing import Any, Dict, List, Optional
from .exceptions import TaskError


class DictWrapper:
    """
    Wrapper that allows accessing dictionary values with dot notation.
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value
    
    def __repr__(self):
        return f"DictWrapper({self._data})"


class TaskContext:
    """
    Execution context for a task, providing access to inputs, outputs, and state.
    """
    
    def __init__(self, inputs: Dict[str, Any], outputs: Dict[str, Any], state: Dict[str, Any]):
        """
        Initialize task context.
        
        Args:
            inputs: Dictionary of input variables
            outputs: Dictionary of output variables
            state: Dictionary of state variables
        """
        self.inputs = inputs
        self.outputs = outputs
        self.state = state
    
    def __repr__(self):
        return f"TaskContext(inputs={self.inputs}, outputs={self.outputs}, state={self.state})"


class Task:
    """
    Represents a single task within a component.
    """
    
    def __init__(self, name: str, code: str, depends_on: Optional[List[str]] = None):
        """
        Initialize a task.
        
        Args:
            name: Unique name for the task
            code: Python code to execute
            depends_on: List of task names this task depends on
        """
        self.name = name
        self.code = code
        self.depends_on = depends_on or []
        
        # Compile the code for efficiency
        try:
            self.compiled_code = compile(code, f"<task:{name}>", "exec")
        except SyntaxError as e:
            raise TaskError(f"Syntax error in task '{name}': {e}")
    
    def execute(self, context: TaskContext) -> None:
        """
        Execute the task with the given context.
        
        Args:
            context: TaskContext containing inputs, outputs, and state
            
        Raises:
            TaskError: If execution fails
        """
        # Wrap dictionaries to allow dot notation
        inputs_wrapper = DictWrapper(context.inputs)
        outputs_wrapper = DictWrapper(context.outputs)
        state_wrapper = DictWrapper(context.state)
        
        # Create execution namespace with access to wrapped context
        namespace = {
            'inputs': inputs_wrapper,
            'outputs': outputs_wrapper,
            'state': state_wrapper,
        }
        
        try:
            exec(self.compiled_code, namespace)
            
            # Update context with any modifications
            # (outputs and state are mutable dicts, so changes persist)
            
        except Exception as e:
            raise TaskError(f"Error executing task '{self.name}': {e}")
    
    def __repr__(self):
        return f"Task(name='{self.name}', depends_on={self.depends_on})"
    
    def __str__(self):
        return self.name
