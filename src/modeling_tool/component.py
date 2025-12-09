#component.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from .task import Task, TaskContext
from .exceptions import ComponentError


class Component(ABC):
    
    def __init__(
        self,
        name: str,
        state: Dict[str, Any],
        inputs: List[str],
        outputs: List[str],
        tasks: List[Task]
    ):
        self.name = name
        self.state = state.copy()  # Copy to avoid mutation of initial state
        self.inputs = inputs
        self.outputs = outputs
        self.tasks = tasks
        
        self._validate_tasks()
        
        self.current_outputs = {output: None for output in outputs}
    
    def _validate_tasks(self) -> None:
        task_names = {task.name for task in self.tasks}
        
        for task in self.tasks:
            for dependency in task.depends_on:
                if dependency not in task_names:
                    raise ComponentError(
                        f"Task '{task.name}' depends on unknown task '{dependency}'"
                    )
        
        if self._has_circular_dependencies():
            raise ComponentError(f"Circular task dependencies detected in component '{self.name}'")
    
    def _has_circular_dependencies(self) -> bool:
        graph = {task.name: task.depends_on for task in self.tasks}
        
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_name in graph:
            if task_name not in visited:
                if dfs(task_name):
                    return True
        
        return False
    
    def get_task_execution_order(self) -> List[Task]:
        graph = {task.name: task for task in self.tasks}
        in_degree = {task.name: 0 for task in self.tasks}
        adjacency = {task.name: [] for task in self.tasks}
        
        for task in self.tasks:
            for dependency in task.depends_on:
                adjacency[dependency].append(task.name)
                in_degree[task.name] += 1
        
        # Kahn's algorithm for topological sort
        queue = [name for name, degree in in_degree.items() if degree == 0]
        ordered_tasks = []
        
        while queue:
            current = queue.pop(0)
            ordered_tasks.append(graph[current])
            
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(ordered_tasks) != len(self.tasks):
            raise ComponentError(f"Failed to order tasks for component '{self.name}'")
        
        return ordered_tasks
   
    @abstractmethod
    def execute_round(self, input_values: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def reset(self) -> None:
        pass 
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', tasks={len(self.tasks)})"


class SynchronousComponent(Component):
    
    def __init__(
        self,
        name: str,
        state: Dict[str, Any],
        inputs: List[str],
        outputs: List[str],
        tasks: List[Task]
    ):
        super().__init__(name, state, inputs, outputs, tasks)
        self.component_type = "synchronous"
    
    def execute_round(self, input_values: Dict[str, Any]) -> Dict[str, Any]:
        for input_name in self.inputs:
            if input_name not in input_values:
                raise ComponentError(
                    f"Missing required input '{input_name}' for component '{self.name}'"
                )
        
        context = TaskContext(
            inputs=input_values,
            outputs=self.current_outputs,
            state=self.state
        )
        
        ordered_tasks = self.get_task_execution_order()
        for task in ordered_tasks:
            task.execute(context)
        
        # Return outputs
        return self.current_outputs.copy()


class AsynchronousComponent(Component):
    """currently running synchronously, this will be changed to implement multithreading in the future"""
    
    def __init__(
        self,
        name: str,
        state: Dict[str, Any],
        inputs: List[str],
        outputs: List[str],
        tasks: List[Task]
    ):
        super().__init__(name, state, inputs, outputs, tasks)
        self.component_type = "asynchronous"
    
    def execute_round(self, input_values: Dict[str, Any]) -> Dict[str, Any]:
        for input_name in self.inputs:
            if input_name not in input_values:
                raise CompnonentError(f"Missing required input '{input_name}' for component '{self.name}'")

        context = TaskContext(inputs=input_values, outputs = self.current_outputs, state=self.state)
        
        ordered_tasks=self.get_task_execution_order()
        for task in ordered_task:
            task.execute(context)

        return self.current_outputs.copy()


