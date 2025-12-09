#termination.py

from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod

class TerminationCondition(ABC):
    @abstractmethod
    def should_terminate(self, round_number: int, state: Dict[str, Any], log: Any, **kwargs) -> bool:
        pass

class MaxRoundsCondition(TerminationCondition):
    def __init__(self, max_rounds: int):
        if max_rounds <= 0:
            raise ValueError("max_rounds must be positive")
        self.max_rounds = max_rounds
    """Temporarily only terminates at max roun number"""
    def should_terminate(self,round_number: int, state: Dict[str, Any], log: Any, **kwargs) -> bool:
        return round_number >=self.max_rounds
        
class StateCondition(TerminationCondition):
    def __init__(self, condition_code: str):
        self.condition_code = condition_code
        self.compiled_condition = compile(condition_code, "<condition>", "eval")

    def should_terminate(self, round_number: int, state: Dict[str, Any], log: Any, **kwargs) -> bool:
        if round_number ==0:
            return False

        namespace = {'state': state}
        try:
            result = eval(self.compiled_condition, namespace)
            return bool(result)
        except Exception as e:
            raise RuntimeError(f"Error evaluating termination condition: {e}")

class CompositeCondition(TerminationCondition):
    def __init__(self, conditions:list):
        if not conditions:
            raise ValueError("Must provide at least one condition")
        self.conditions = conditions

    def should_terminate(self, round_number: int, state: Dict[str,Any], log: Any, **kwargs) -> bool:
        return any(cond.should_terminate(round_number, state, log, **kwargs)
                   for cond in self.conditions)

class MaxTimeCondition(TerminationCondition):
    def __init__(self, max_time: float):
        if max_time <= 0:
            raise ValueError("max_time must be positive")
        self.max_time = max_time
        
    def should_terminate(self, round_number: int, state: Dict[str, Any], log: Any, **kwargs) -> bool:
        current_time = kwargs.get('current_time', 0.0)
        result = current_time >= self.max_time
        if round_number %1000==0:
            print(f"MaxTimeCondition: current_time={current_time}, max_time={self.max_time}, result={result}")
        return result

class MaxEventsCondition(TerminationCondition):
    def __init__(self, max_events:int):
        if max_events <= 0:
            raise ValueError("max_events must be positive")
        self.max_events = max_events
    def should_terminate(self, round_number: int, state: Dict[str, Any], log: Any, **kwargs) -> bool:
        event_count = kwargs.get('event_count', 0)
        return event_count >= self.max_events

class EmptyQueueCondition(TerminationCondition):
    def should_terminate(self, round_number: int, state: Dict[str, Any], log: Any, **kwargs) -> bool:
        event_queue=kwargs.get('event_queue', None)
        if event_queue is None:
            return True
        return event_queue.is_empty()
