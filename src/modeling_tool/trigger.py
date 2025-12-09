#trigger.py

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

class Trigger(ABC):

    @abstractmethod
    def should_activate(self, event_name: Optional[str], state: Dict[str, Any], current_time: float) -> bool:
        pass

class PeriodicTrigger(Trigger):
    def __init__(self, interval: float):
        self.interval=interval
        self.last_execution = -float('inf')

    def should_activate(self, event_name: Optional[str], state: Dict[str,Any], current_time: float) -> bool:
        if current_time - self.last_execution >= self.interval:
            self.last_execution = current_time
            return True
        return False

    def get_next_time(self, current_time: float) -> float:
        return self.last_execution + self.interval

class EventTrigger(Trigger):
    #triggers when a specific event occurs
    def __init__(self, event_name: str):
        self.event_name = event_name

    def should_activate(self, event_name: Optional[str], state: Dict[str, Any], current_time: float) -> bool:
        return event_name == self.event_name

class ConditionTrigger(Trigger):
    #triggers when a condition becomes true
    def __init__(self, condition_code: str):
        self.condition_code = condition_code
        self.compiled_condition=compile(condition_code, "<condition>", "eval")
        self.was_true = False

    def should_activate(self, event_name: Optional[str], state:Dict[str, Any], current_time: float)-> bool:
        namespace = {'state': state, 'current_time': current_time}
        try:
            is_true = bool(eval(self.compiled_condition, namespace))

            should_trigger = is_true and not self.was_true
            self.was_true = is_true
            return should_trigger
        except Exception:
            return False

class ImmediateTrigger(Trigger):
    #initialization trigger
    def __init__(self):
        self.has_run = False

    def should_activate(self, event_name:Optional[str], state: Dict[str, Any], current_time:float) -> bool:
        if not self.has_run:
            self.has_run = True
            return True
        return False
