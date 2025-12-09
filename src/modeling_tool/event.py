#event.py

from typing import Any, Dict, Optional
from dataclasses import dataclass, field

@dataclass(order=True)
class Event:
    time: float
    name: str = field(compare=False)
    priority: int = field(default=0, compare=True)
    data: Dict[str, Any] = field(default_factory=dict, compare=False)
    source_task: Optional[str] = field(default=None, compare=False)

    def __repr__(self):
        return f"Event(time={self.time}, name='{self.name}', data={self.data})"

class EventEmitter:
    def __init__(self):
        self.pending_events = []

    def emit(self, event_name: str, data: Any = None, delay: float = 0.0, priority: int =0):
        event_data={'value':data} if data is not None else {}
        self.pending_events.append({'name':event_name, 'data': event_data, 'delay': delay, 'priority':priority})

    def get_pending_events(self):
        events = self.pending_events.copy()
        self.pending_events.clear()
        return events
