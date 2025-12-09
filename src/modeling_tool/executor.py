#executor.py

from typing import Dict, Any, Optional, List
from .component import Component
from .input_generator import InputGenerator
from .termination import TerminationCondition
from .execution_log import ExecutionLog
from .exceptions import ComponentError

class Executor:
    def __init__(
            self,
            component: Component,
            input_generator: InputGenerator,
            termination_condition: TerminationCondition,
            track_task_order: bool = False
            ):
        
        self.component = component
        self.input_generator = input_generator
        self.termination_condition = termination_condition
        self.track_task_order = track_task_order
        self.log = ExecutionLog()
        self.current_round = 0

    def run(self) -> ExecutionLog:
        self.current_round = 0
        self.log = ExecutionLog()

        while not self.termination_condition.should_terminate(self.current_round, self.component.state, self.log):
            self.current_round +=1
            inputs = self.input_generator.generate(self.component.inputs, self.current_round, self.component.state)

            task_order = None
            if self.track_task_order:
                task_order = [task.name for task in self.component.get_task_execution_order()]

            try:
                outputs = self.component.execute_round(inputs)
            except Exception as e:
                raise ComponentError(f"Error in round {self.current_round}: {e}")
            self.log.add_round(round_number=self.current_round, inputs=inputs.copy(),outputs=outputs.copy(),state=self.component.state.copy(),task_order=task_order)

        return self.log
    def reset(self) -> None:
        self.current_round = 0
        self.log = ExecutionLog()

