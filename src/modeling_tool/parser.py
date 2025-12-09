#parser.py

import yaml
from typing import Any, Dict, List
from pathlib import Path
from .component import Component, SynchronousComponent, AsynchronousComponent
from .task import Task
from .exceptions import ParserError, ValidationError
from .trigger import PeriodicTrigger, EventTrigger, ConditionTrigger, ImmediateTrigger

class ComponentParser:

    REQUIRED_FIELDS = ['component']
    REQUIRED_COMPONENT_FIELDS = ['name', 'type', 'state', 'inputs', 'outputs', 'tasks']
    VALID_COMPONENT_TYPES = ['synchronous', 'asynchronous']

    @staticmethod
    def parse_file(file_path: str) -> Component:
        path = Path(file_path)

        if not path.exists():
            raise ParserError(f"File not found: {file_path}")

        if not path.suffix in ['.yaml', '.yml']:
            raise ParserError(f"File must have .yaml or .yml extension: {file_path}")
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)

        except yaml.YAMLError as e:
            raise ParserError(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise ParserError(f"Error reading file: {e}")

        return ComponentParser.parse_dict(data)

    @staticmethod
    def _validate_structure(data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationError("component file must contain a dictionary")
        for field in ComponentParser.REQUIRED_FIELDS:
            if field not in data:
                raise ValidationError(f"Missing required top-level field: '{field}'")

        component_data = data['component']
        if not isinstance(component_data, dict):
            raise ValidationError("'component' must be a dictionary")

        for field in ComponentParser.REQUIRED_COMPONENT_FIELDS:
            if field not in component_data:
                raise ValidationError(f"Missing required component field: {field}'")
    
    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> Component:

        ComponentParser._validate_structure(data)

        component_data = data['component']

        name = ComponentParser._extract_name(component_data)
        component_type = ComponentParser._extract_type(component_data)
        state = ComponentParser._extract_state(component_data)
        inputs = ComponentParser._extract_inputs(component_data)
        outputs = ComponentParser._extract_outputs(component_data)
        tasks = ComponentParser._extract_tasks(component_data)

        if component_type == 'synchronous':
            return SynchronousComponent(name, state, inputs, outputs, tasks)
        else:
            return AsynchronousComponent(name, state, inputs, outputs, tasks)


    @staticmethod
    def _extract_name(component_data: Dict[str, Any]) -> str:

        name = component_data['name']
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Component 'name' must be a non0empty string")
        return name.strip()

    @staticmethod
    def _extract_type(component_data: Dict[str, Any]) -> str:

        comp_type = component_data['type']
        if not isinstance(comp_type, str):
            raise ValidationError("Component 'type' must be a string")

        comp_type = comp_type.lower().strip()
        if comp_type not in ComponentParser.VALID_COMPONENT_TYPES:
            raise ValidationError(f"Component 'type' must be on of {ComponentParse.VALID_COMPONENT_TYPES}, got 'comp_type")

        return comp_type
    
    @staticmethod
    def _extract_state(component_data: Dict[str, Any]) -> Dict[str, Any]:
        state = component_data['state']
        if not isinstance(state, dict):
            raise ValidationError("component 'state' must be a dictionary")

        return state

    @staticmethod
    def _extract_inputs(component_data: Dict[str, Any]) -> List[str]:
        inputs = component_data['inputs']
        if not isinstance(inputs, list):
            raise ValidationError("Component 'inputs' must be a list")

        input_names = []
        for item in inputs:
            if isinstance(item,str):
                input_names.append(item.strip())
            elif isinstance(item, dict):
                if len(item) != 1:
                    raise ValdiationError(f"Invalid input format: {item}")
                input_name = list(item.keys())[0]
                input_names.append(input_name.strip())
            else:
                raise ValidationError(f"Invalid input format: {item}")

        return input_names

    @staticmethod
    def _extract_outputs(component_data: Dict[str, Any]) -> List[str]:
        outputs = component_data['outputs']
        if not isinstance(outputs, list):
            raise ValidationError("Component 'outputs' must be a list")

        output_names = []
        for item in outputs:
            if isinstance(item,str):
                output_names.append(item.strip())
            elif isinstance(item, dict):
                if len(item) != 1:
                    raise ValdiationError(f"Invalid output format: {item}")
                output_name = list(item.keys())[0]
                output_names.append(output_name.strip())
            else:
                raise ValidationError(f"Invalid output format: {item}")

        return output_names

    @staticmethod
    def _extract_tasks(component_data: Dict[str, Any]) -> List[Task]:
        tasks_data = component_data['tasks']
        if not isinstance(tasks_data, list):
            raise ValidationError("Component 'tasks' must be a list")

        if not tasks_data:
            raise ValidationError("Component must have at least one task")

        tasks = []
        task_names = set()

        for i, task_data in enumerate(tasks_data):
            if not isinstance(task_data, dict):
                raise ValidationError(f"Task {i} must be a dictionary")

            if 'name' not in task_data:
                raise ValdiationError(f"Task{i} missing required field 'name'")
            if 'code' not in task_data:
                raise ValdiationError(f"Task{i} missing required field 'code'")
            task_name = task_data['name']
            if not isinstance(task_name,str) or not task_name.strip():
                raise ValidationError(f"Task {i} 'name' must be a non-empty string")
            task_name = task_name.strip()
            if task_name in task_names:
                raise ValidationError(f"Duplicate task name: '{task_name}'")
            task_names.add(task_name)

            code = task_data['code']
            if not isinstance(code, str):
                raise ValidationError(f"Task '{task_name}' 'code' must be a string")

            depends_on = task_data.get('depends_on',[])
            if not isinstance(depends_on, list):
                raise ValidationError(f"Tasl '{task_name}' 'depends_on' must be a lsit")

            for dep in depends_on:
                if not isinstance(dep, str):
                    raise ValidationError(f"Task '{task_name} dependency must be a string, got {type(dep)}")

            task = Task(task_name, code, depends_on)

            if 'trigger' in task_data:
                trigger_data = task_data['trigger']
                if not isinstance(trigger_data, dict):
                    raise ValidationError(f"Task '{task_name}' 'trigger' must be a dictionary")

                if 'type' not in trigger_data:
                    raise ValidationError(f"Task '{task_name}' trigger missing 'type' ")

                trigger_type = trigger_data['type']

                if trigger_type == 'periodic':
                    if 'interval' not in trigger_data:
                        raise ValidationError(f"Task '{task_name}' periodic trigger missing 'interval' ")
                    task.trigger = PeriodicTrigger(interval=trigger_data['interval'])

                elif trigger_type == 'event':
                    if 'event' not in trigger_data:
                        raise ValidationError(f"Task '{task_name}' event trigger missing 'event' ")
                    task.trigger = EventTrigger(event_name=trigger_data['event'])

                elif trigger_type == 'condition':
                    if 'condition' not in trigger_data:
                        raise ValidationError(f"Task '{task_name}' condition trigger missing 'condition'")
                    task.trigger = ConditionTrigger(condition=trigger_data['condition'])

                elif trigger_type == 'immediate':
                    task.trigger = ImmediateTrigger()

                else:
                    raise ValidationError(f"Tasl '{task_name}' unknown trigger type: '{trigger-type}'")

            if 'condition' in task_data:
                task.condition=task_data['condition']
            else:
                task.condition = None
            tasks.append(task)
        return tasks


