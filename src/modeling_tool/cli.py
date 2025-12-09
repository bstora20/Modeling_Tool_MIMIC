#cli.py

import argparse
import sys
from pathlib import Path 
from .parser import ComponentParser
from .executor import Executor
from .event_executor import EventDrivenExecutor
from .input_generator import InteractiveInputGenerator, RandomInputGenerator
from .termination import MaxRoundsCondition, StateCondition, CompositeCondition, MaxTimeCondition, MaxEventsCondition, EmptyQueueCondition
from .exceptions import ModelingToolError

def parse_random_inputs(input_str: str) -> dict:

    """ Format: name:type:min:max,name:type,etc..
        Ex: increment:int:1:10,flag:bool"""

    specs = {}
    for item in input_str.split(','):
        parts = item.split(':')
        if len(parts) <2:
            raise ValueError("Invalid input spec: {item}")

        name = parts[0]
        input_type = parts[1]

        spec = {'type': input_type}

        if input_type in ['int', 'float'] and len(parts) >=4:
            if input_type == 'int':
                spec['min'] = int(parts[2])
                spec['max'] = int(parts[3])
            else:
                spec['min'] = float(parts[2])
                spec['max'] = float(parts[3])

        specs[name] = spec

    return specs

def parse_initial_inputs(input_str: str) -> dict:
    """Format: key=value, key=value"""

    inputs = {}
    for pair in input_str.split(','):
        if '=' not in pair:
            raise ValueError(f"Invalid initial input format: {pair}")

        key, value = pair.split('=', 1)
        key = key.strip()
        value = value.strip()

        try:
            inputs[key]=int(value)
        except ValueError:
            try: 
                inputs[key] = float(value)
            except ValueError:
                if value.lower() in ['true', 'false']:
                    inputs[key] = value.lower() == 'true'
                else:
                    inputs[key] = value

    return inputs

def main():

    parser = argparse.ArgumentParser(description='Modeling Tool - execute synchronous and asynchronous components', formatter_class=argparse.RawDescriptionHelpFormatter, epilog="""
    Examples:
        #Synchronous with interactive input
        python -m modeling_tool.cli component.yaml --rounds 1- --inputs-mode interactive

        #Synchronous with random inputs
        python -m modeling_tool.cli component.yaml --rounds 1- --input-mode random 
        --random inputs "value:int:1:10"

        #Asynchronous with time limit
        python -m modeling_tool.cli async_component.yaml --max-time 100.0

        #Asynchronous with inputs at intervals
        python -m modeling_tool.cli async_component.yaml --max-time 50.0
        --input-mode random --random-inputs "temp:float:15:30"  --input-interval 1.0

        #Mixed termination conditions
        python -m modeling_tool.cli component.yaml --rounds 100
        --conidtion "state['done'] == True"
        """
                                     )

    parser.add_argument('component_file', help='Path to component YAML file')
    
    term_group = parser.add_argument_group('termination conditions')
    term_group.add_argument('--rounds', type=int, help='Maximum number of rounds (synchronous) or events (ashynchronous)')
    term_group.add_argument('--max-time', type = float, help='Maximum simulation time (asynchronous only)')
    term_group.add_argument('--max-events', type=int, help="Maximum number of events (asynchronous only)")
    term_group.add_argument('--condition', type = str, help='Termination condition (Python expression using state dict)')

    input_group = parser.add_argument_group('input generation')
    input_group.add_argument('--input-mode', choices=['interactive', 'random'], help= 'Input generation mode (required for synchronous or asynchronous with inputs)')
    input_group.add_argument('--random-inputs', type=str, help='Random input specification (format: name:type:min:mac,...)')
    input_group.add_argument('--seed', type=int, help='Random seed for reproducible random inputs')
    input_group.add_argument('--initial-inputs', type=str, help='Initial input values for async (format: key=value, key=value)')
    input_group.add_argument('--input-interval', type=float, help='Interval for periodic input generation (async only)')
    input_group.add_argument('--input-event', type = str, default='input_ready', help='Event name for input generation (default: input_ready)')
    
    output_group = parser.add_argument_group('output options')
    output_group.add_argument('--output', type=str, help='Output file path (JSON or CSV)')
    output_group.add_argument('--track-tasks', action='store_true', help='Track and display task execution order')
    output_group.add_argument('--verbose', action='store_true', help='Print detailed execution information')

    async_group = parser.add_argument_group(' asynchronous execution option')
    async_group.add_argument('--max-workers', type=int, help='Maximum parallel workers for task execution')
    
    args = parser.parse_args()

    try:
        if args.verbose:
            print(f"Loading component from: {args.component_file}")

        component = ComponentParser.parse_file(args.component_file)

        if args.verbose:
            print(f"Component: {component.name} ({component.component_type})")
            print(f"Inputs: {component.inputs}")
            print(f"Outputs: {component.outputs}")
            print(f"State: {component.state}")
            print()

        is_async = component.component_type == 'asynchronous'
        if args.verbose:
            print(f"Execution mode: {'Event-driven' if is_async else 'Round-based'}")
        input_generator = None
        initial_inputs={}

        if args.input_mode:
            if args.input_mode == 'interactive':
                input_generator = InteractiveInputGenerator()
            elif args.input_mode == 'random':
                if not args.random_inputs:
                    print("Error: --random-inputs required when using --input-mode random")
                sys.exit(1)

                input_specs = parse_random_inputs(args.random_inputs)
                input_generator = RandomInputGenerator(input_specs, args.seed)
        
        if args.initial_inputs:
            initial_inputs = parse_initial_inputs(args.initial_inputs)

        conditions = []

        if is_async:
            if args.rounds:
                conditions.append(MaxEventCondition(args.rounds))
            if args.max_time:
                conditions.append(MaxTimeCondition(args.max_time))
            if args.max_events:
                conditions.append(MaxEventsCondition(args.max_events))
            if args.condition:
                conditions.append(StateCondition(args.condition))

            if not conditions:
                conditions.append(EmptyQueueCondition())
        else:
            if args.rounds:
                conditions.append(MaxRoundsCondition(args.rounds))
            if args.condition:
                conditions.append(StateCondition(args.condition))
            if not conditions:
                conditions.append(MaxRoundsCondition(10))

            if args.max_time or args.max_events:
                print("Warning: --max-time and --max events are ignored for synchronous components")

        if len(conditions) ==1:
            termination = conditions[0]
        else:
            termination = CompositeCondition(conditions)

        if is_async:
            if args.verbose:
                print(f"Creating event-driven executor...")
                if input_generator and args.input_interval:
                    print(f"Input generation: every {args.input_interval}s")
                if initial_inputs:
                    print(f"Initial inputs: {initial_inputs}")

            executor = EventDrivenExecutor(
                    component= component,
                    input_generator = input_generator,
                    termination_condition = termination,
                    input_event_name = args.input_event,
                    input_interval=args.input_interval,
                    initial_inputs=initial_inputs,
                    max_workers = args.max_workers)

        else:
            if not input_generator:
                print("error: Synchronous components require --input-mode")
                sys.exit(1)
            if args.verbose:
                print(f"Creating round-based executor...")

            executor = Executor(
                    component = component, 
                    input_generator = input_generator,
                    termination_condition= termination,
                    track_task_order=args.track_tasks)

        if args.verbose:
            print("Starting execution... \n")

        log = executor.run()

        if is_async:
            stats = executor.get_statistics()
            print(f"Simulation complete!")
            print(f"Events processed: {stats['total_events']}")
            print(f"Simulation time: {stats['simulation_time']:.2f}s")
            if stats['input_rounds'] > 0:
                print(f"Input rounds: {stats['input_rounds']}")
            print(f" Final state: {stats['final_state']}")
            print(f" Final outputs: {stats['final_outputs']}")
        else:
            print(f"\nExecution complete: {len(log)} rounds")


        if args.verbose:
            print("\n --- Execution Log ---")
            for record in log.rounds:
                if is_async:
                    print(f"\nEvent {record.round_number} (t={record.inputs.get('time', 0):.2f}s):")
                else:
                    print(f"\nRound {record.round_number}:")
                print(f" Inputs: {record.inputs}")
                print(f" Outputs: {record.outputs}")
                print(f"State: {record.state}")
                if record.task_order:
                    print(f"Tasls: {' -> '.join(record.task_order)}")

        if args.output:
            output_path=Path(args.output)
            if output_path.suffix == '.json':
                log.to_json(args.output)
                print(f"\nSaved log to: {args.output}")
            elif output_path.suffix == '.csv':
                log.to_csv(args.output)
                print(f"\n Saved log to:{args.output}")
            else:
                print(f"\n Varning: Unknown output format '{output_path.suffix}', skipping save")

    except ModelingToolError as e:
        print(f"Error: {e}", file = sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file = sys.stderr)
        if args.verbose:
            import traceback
            traceback.printexc()
        sys.exit(1)

if __name__ == '__main__':
    main()
