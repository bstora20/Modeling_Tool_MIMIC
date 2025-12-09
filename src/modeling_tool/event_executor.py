#event_executor.py

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List
from queue import Queue
from .component import Component, AsynchronousComponent
from .task import Task, TaskContext
from .event import Event, EventEmitter
from .event_queue import EventQueue
from .trigger import PeriodicTrigger
from .simulation_time import SimulationTime
from .execution_log import ExecutionLog
from .exceptions import ComponentError, TaskError
from .input_generator import InputGenerator
from .termination import TerminationCondition, EmptyQueueCondition

class EventDrivenExecutor:
    
    def __init__(
        self,
        component: Component,
        input_generator: Optional[InputGenerator]=None,
        termination_condition: Optional[TerminationCondition] = None,
        input_event_name: str = "input_ready",
        input_interval: Optional[Dict[str, Any]]=None,
        initial_inputs: Optional[Dict[str, Any]]=None,
        max_workers: Optional[int] = None
    ):
        if not isinstance(component, AsynchronousComponent):
            raise ComponentError("EventDrivenExecutor requires AsynchronousComponent")
        
        self.component = component
        self.input_generator=input_generator
        self.termination_condition=termination_condition or EmptyQueueCondition()
        self.input_event_name = input_event_name
        self.input_interval = input_interval
        self.initial_inputs = initial_inputs.copy() if initial_inputs else {}
        self.max_workers = max_workers
        
        self.event_queue = EventQueue()
        self.sim_time = SimulationTime()
        self.log = ExecutionLog()
        self.event_count = 0
        self.input_round = 0 
        self.state_lock = threading.Lock()
        self.output_lock = threading.Lock()
    
    def _should_terminate(self) -> bool:
        result = self.termination_condition.should_terminate(
        round_number=self.event_count,
        state=self.component.state,
        log=self.log,
        current_time=self.sim_time.current_time,
        event_count=self.event_count,
        event_queue=self.event_queue
    )
        return result

    def _schedule_input_generation(self):
        if self.input_generator and self.input_interval:
            event = Event(time=0.0, name=f"_generate_input", data={'round':1})
            self.event_queue.push(event)

    def _generate_and_emit_input(self):
        if self.input_generator:
            self.input_round +=1
            try:
                new_inputs = self.input_generator.generate(self.component.inputs, self.input_round, self.component.state)
                with self.state_lock:
                    self.initial_inputs.update(new_inputs)

                input_event = Event(time=self.sim_time.current_time, name=self.input_event_name, data=new_inputs)
                self.event_queue.push(input_event)

                if self.input_interval:
                    next_event = Event(time=self.sim_time.current_time + self.input_interval, name=f"_generate_input", data={'round': self.input_round +1})
                    self.event_queue.push(next_event)
            except Exception as e:
                raise ComponentError(f"Error generating unputs: {e}")



    def _schedule_periodic_tasks(self):
        for task in self.component.tasks:
            if hasattr(task, 'trigger') and isinstance(task.trigger, PeriodicTrigger):
                event = Event(
                    time=0.0,
                    name=f"periodic_{task.name}",
                    data={'task': task.name}
                )
                self.event_queue.push(event)
    
    def _execute_task(
        self, 
        task: Task, 
        event: Optional[Event] = None,
        error_queue: Queue = None
    ) -> Optional[List[Dict[str, Any]]]:
        from .task import DictWrapper
        event_emitter = EventEmitter()
        
        try:
            with self.state_lock:
                context = TaskContext(
                    inputs=self.initial_inputs.copy(),
                    outputs=self.component.current_outputs.copy(),
                    state=self.component.state.copy()
                )
            inputs_wrapper = DictWrapper(context.inputs)
            outputs_wrapper = DictWrapper(context.outputs)
            state_wrapper = DictWrapper(context.state)

            namespace_extras = {
                'emit_event': event_emitter.emit,
                'current_time': self.sim_time.current_time,
                'event_data': event.data if event else {}
            }
            
            task_namespace = {
                'inputs': inputs_wrapper,
                'outputs': outputs_wrapper,
                'state': state_wrapper,
                **namespace_extras
            }
            exec(task.compiled_code, task_namespace)
            
            with self.state_lock:
                self.component.state.update(context.state)
            
            with self.output_lock:
                self.component.current_outputs.update(context.outputs)
            
            return event_emitter.get_pending_events()
            
        except Exception as e:
            if error_queue:
                error_queue.put((task.name, e))
            else:
                raise TaskError(f"Error executing task '{task.name}': {e}")
            return None
    
    def _get_activated_tasks(
        self, 
        event: Event
    ) -> List[Task]:
        activated_tasks = []
        for task in self.component.tasks:
            should_run = False
            
            if hasattr(task, 'trigger'):
                should_run = task.trigger.should_activate(
                    event.name,
                    self.component.state,
                    self.sim_time.current_time
                )
                
                if isinstance(task.trigger, PeriodicTrigger) and should_run:
                    next_time = task.trigger.get_next_time(self.sim_time.current_time)
                    next_event = Event(
                        time=next_time,
                        name=f"periodic_{task.name}",
                        data={'task': task.name}
                    )
                    self.event_queue.push(next_event)
            
            if should_run and hasattr(task, 'condition') and task.condition:
                namespace = {
                    'state': self.component.state, 
                    'current_time': self.sim_time.current_time
                }
                try:
                    should_run = bool(eval(task.condition, namespace))
                except Exception:
                    should_run = False
            
            if should_run:
                activated_tasks.append(task)
        
        return activated_tasks
    
    def _execute_tasks_parallel(
        self, 
        tasks: List[Task], 
        event: Event
    ):
        if not tasks:
            return
        
        if len(tasks) == 1:
            pending_events = self._execute_task(tasks[0], event)
            if pending_events:
                self._schedule_pending_events(pending_events, tasks[0].name)
            return
        
        error_queue = Queue()
        all_pending_events = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._execute_task, task, event, error_queue): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    pending_events = future.result()
                    if pending_events:
                        all_pending_events.append((task.name, pending_events))
                except Exception as e:
                    error_queue.put((task.name, e))
        
        if not error_queue.empty():
            task_name, error = error_queue.get()
            raise TaskError(f"Error in task '{task_name}': {error}")
        
        for task_name, pending_events in all_pending_events:
            self._schedule_pending_events(pending_events, task_name)
    
    def _schedule_pending_events(
        self, 
        pending_events: List[Dict[str, Any]], 
        source_task: str
    ):
        for pending_event in pending_events:
            new_event = Event(
                time=self.sim_time.current_time + pending_event['delay'],
                name=pending_event['name'],
                data=pending_event['data'],
                priority=pending_event['priority'],
                source_task=source_task
            )
            self.event_queue.push(new_event)
    
    def run(self) -> ExecutionLog:
        self._schedule_periodic_tasks()
        self._schedule_input_generation()
        if self.event_queue.is_empty():
            self.event_queue.push(Event(time=0.0, name="start"))
        
        while not self._should_terminate():
            event = self.event_queue.pop()
            if event is None:
                break
            self.sim_time.advance_to(event.time)
            self.event_count +=1

            if event.name == "_generate_input":
                self._generate_and_emit_input()
                continue

            activated_tasks = self._get_activated_tasks(event)
            self._execute_tasks_parallel(activated_tasks, event)

            self.log.add_round(
                    round_number = self.event_count,
                    inputs={'event': event.name, 'time': event.time, **self.initial_inputs},
                    outputs = self.component.current_outputs.copy(),
                    state=self.component.state.copy(),
                    task_order=[t.name for t in activated_tasks] if activated_tasks else None
                    )
        return self.log
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        return {
            'total_events': self.event_count,
            'simulation_time': self.sim_time.current_time,
            'final_state': self.component.state.copy(),
            'final_outputs': self.component.current_outputs.copy(),
            'input_rounds': self.input_round
        }
