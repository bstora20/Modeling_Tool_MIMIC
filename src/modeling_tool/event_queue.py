#event_queue.py

import heapq
from typing import List, Optional
from .event import Event

class EventQueue:
    #events get processed in order of time then priority
    def __init__(self):
        self._queue: List[Event] = []
        self._counter=0

    def push(self, event: Event):
        heapq.heappush(self._queue, (event.time, event.priority, self._counter, event))
        self._counter+=1

    def pop(self) ->Optional[Event]:
        #get and remove next event
        if self._queue:
            _,_,_, event = heapq.heappop(self._queue)
            return event
        return None

    def peek(self) -> Optional[Event]:
        #look at next event without removing it
        if self._queue:
            return self._queue[0][3]
        return None

    def is_empty(self)-> bool:
        return len(self._queue)==0

    def self(self) -> int:
        return len(self._queue)

    def clear(self):
        self._queue.clear()
        self._counter=0

    def __len__(self):
        return len(self._queue)

    def __repr__(self):
        return f"EventQueue(size={len(self._queue)})"
