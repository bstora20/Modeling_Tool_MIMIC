# MIMIC: Modeling Interface for Multi-mode Integrated Components

A declarative Python framework for modeling and simulating components using both synchronous (round-based) and event-driven execution from a single YAML specification.

## Overview

MIMIC (Modeling Interface for Multi-mode Integrated Components) enables you to define and simulate components without writing extensive Python code. Components are specified using declarative YAML files that describe component behavior, and the framework handles execution and logging. 

The framework supports two execution models:
- **Synchronous execution**: Tasks execute in rounds, one after another in dependency order
- **Event-driven execution**: Tasks execute based on events and triggers in simulated time

## Features

- Declarative YAML-based component definitions
- Dual execution models (round-based and event-driven)
- Unified CLI that automatically detects component type
- Flexible input generation (interactive for synchronous, random, scheduled)
- Condigurable termination conditions applicable to both modes
- JSON and CSV execution logging
- Command-line interface for rapid prototyping
- Python API for programmatic control
- Only dependency: PyYAML

## Installation

### Requirements

- Python 3.7 or higher
- PyYAML 6.0 or higher

### Setup 

```bash
# Navigate to the project directory
cd mimic

# Create a virtual environmnet (recommended)
python -m venv venv

#Activate the virtual environmnet
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

#Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "from modeling-tool import Executor; print('Installation successful')"
```

## Quick Start

### Example 1: Simple Counter (Synchronous)

Create a file called `my_counter.yaml`:

```yaml
component:
    name: MyCounter
    type: synchronous
    
    state:
        count = 0
        
    inputs:
        - current_count
        
    tasks:
        - name: add
          code: |
            state.count += inputs.increment
            outputs.current_count = state.count
            
```

Execute from the command line:

```bash
python -m modeling_tool.cli my_counter.yaml \
    --input-mode interactive \
    --rounds 5 \
    --verbose
```

### Example 2: Temperature Sensor (Event-Driven)

Create a fie called `sensor.yaml`:

```yaml
component:
    name: TemperatureMonitor
    type: asynchronous

    state:
        temperature: 20.0
        alert_count: 0
        readings: []
        tick_count: 0

    inputs: []

    outputs:
        - status
        - alerts
        - total_readings

    tasks:
        - name: read_sensor
          trigger:
                type: periodic
                interval: 2.0
          code: |
                #Simulate reading temperature (random between 18-32)
                import random
                state.temperature = random.uniform(18.0, 32.0)
                state.readings.append(state.temperature)
                state.tick_count +=1
                print(f"[{current_time:.1f}s] Reading {state.tick_count}: {state.temperature:.1f}°C")
                emit_event("check_threshold")

        - name: check_threshold
          trigger:
                type: event
                event: check_threshold
          code: |
                if state.temperature >25.0:
                    state.alert_count +=1
                    outputs.status = "HOT"
                    outputs.alerts = state.alert_count
                    emit_event("alert")
                else:
                    outputs.status = "normal"

        - name: log_alert
          trigger:
                type: event
                event: alert
          code: |
            print(f"ALERT at {current_time}s: Temp {state.temperature:.1f}°C")
```

Execute from the command line:

```bash
python -m modeling_tool.cli temperature.yaml \
    --input-mode random \
    --random-inputs "ambient_temp:float:18:32" \
    --input-interval 2.0 \
    --max-time 30.0 \
    --seed 42 \
    --verbose
```

## Basic Usage

### Command-Line Interface

The CLI automatically detects whether your component is synchronous or event-driven based on the 'type' field in your YAML file and uses the appropriate executor.

**General syntax:**
```bash
python -m modeling_tool.cli <component_file.yaml> [options]
```

### Options for Both Types

```bash
--condition "expression"    # State-based termination
--output FILE               # Save results to JSON or CSV file
--track-tasks               # Track task execution order
--verbose                   # Set random seed
```

### Synchronous Options

```bash
--rounds N                  # Number of rounds to execute
--input-mode MODE           # interactive or random (required)
--random-inputs "spec"      # Random input specification
```

### Event-Driven Options

```bash
--max-time SECONDs          # Maximum simulated time
--max-events N              # Maximum number of events
--input-mode MODE           # random (optional)
--random-inputs "spec"      # Random input specification
--input-interval SECONDS    # Input generation frequency
--input-event NAME          # Input event name (default: input_ready)
--initial-inputs "spec"     # Starting input values
--max-workers N             # Parallel task limit
```
## Component Structure

A component YAML file has to following structure:

```yaml
component: 
    name: ComponentName
    type: synchronous # or asynchronous
    
    state:
        #Initial state variables
        variable_name: initial_value
        
    inputs;
        # List of input variables
        - input1
        - input2
        
    outputs:
        # List of output variable names
        - output1
        - output2
    
    tasks:
        #List of tasks to execute
        - name: task_name
          code: |
            #Python code here
            # Access: inputs.input1, state.variable_name, outputs.output1
```

### Synchronous Tasks

For synchronous components, tasks can specify dependencies to control execution order;

```yaml
tasks:
    - name: first_task
      code: |
        state.value = inputs.x * 2
    - name: second_task
      depends_on: [first_task]
      code: |
            outputs.result = state.value + 10
```

The framework uses topological sort to determine execution order based on dependencies.

### Event-Driven Tasks

For event-driven components, tasks require a trigger sepcifications:

```yaml
tasks:
    - name: periodic
      trigger:
        type: periodic
        interval: 1.0           # Executes every 1 simulated second
      code: |
        state.ticks +=1
    
    - name: event_task
      trigger:
        type: event
        event: data_ready       # Executes when this event occurs
      code: |
        process_data()
        
    - name: condition_task
      trigger:
            type: condition
            condition: "state['temp'] > 100"    # Executes when condition becomes true
      code: |
            outputs.alert = "OVERHEAT"
```
### Modleing True Asynchronous Components

**Important Note**:The event-driven examples in this README demonstrate the framework's capabilities but do not strictly model true asynchronous components. In real asynchronous systems, each task performs exactly one atomic operation: reading one input, modifying one state variable, or writing one output.

To model true asynchronous behavior, design tasks that are granular:
```yaml
tasks:
    - name: read_sensor
      trigger:
            type: event
            event: input_ready
      code: |
            state.raw_value = inputs.sensor_reading
            emit_event("value_read")
            
    - name: process _value
      trigger:
            type: event
            event: value_read
      code: |
            state.processed_value = state.raw_value * 2
            emit_event("value_processed")
         
    - name: write_output
      trigger:
            type; event
            event: value_processed
      code: |
            outputs.result - state.processed_value
```

This granular approach more accurately represents asynchronous execution where operations can be interleaved, reordered, or executed in parallel without coordinate. The rest of the examples in this guide prioritize clarity and demonstration of features over strict asynchronous modeling. 

## Understanding Simulated Time

Event-driven components use simulated-time, which advances instantaneously between events rather than waiting in real time. This enables fast simulation of long time periods.

For example:
 ```
 Real time:         [-------0.001 seconds-------]      
 Simulated time: 0.0s → 1.0s → 2.0s → 10.0s → 50.0s
 ```
 
 A simulation covering 50 seconds of simulated time might complete in 1 millisecond of real time. The entire simulation finishes before a human could event see what happened, much less type input.
 
 **Important consequences**: Interactive input is not supported for event-driven components because the simulation completes before a human could respond. Use synchronous mode if interactive control is required, or provide inputs programmatically for event-driven mode. 
 
 ## Examples
 
 The `examples/` directory contains several sample components;
 
 - `simple_couter.yaml` - Basic synchronous counter
 - `async_periodic.yaml` - Periodic task execution
 - `async_temperature.yaml` - Event-driven sensor system
 - `synchronous_merge.yaml` - Merge sort implementation
 - `async_merge.yaml` - Parallel merge with race conditions
 - `synchronous_leader election.yaml` Leader Election (round-based)
 - `async_leader_election.yaml` - Leader Election (event-driven)
 
 To execute an example:
 
 ```bash
 python -m modeling_tool.cli examples/simple_counter.yaml \ 
    --input-mode random \
    --random-inputs "increment:int:1:5" \
    --rounds 10
```

## Documentation

For comprehensive information, see;

**[User Guide](Documentation_MIMIC.md)** - COmplete documentation including:
- Detailed component DSL reference
- Input generation strategies
- Termination conditions
- Event-driven execution details
- Best Practices
- Troubleshooting Guide
- Extended examples

## Project Structure

```
modeling_tool/
├── __init__.py              # Package initialization
├── cli.py                   # Command-line interface
├── component.py             # Component classes
├── executor.py              # Round-based executor
├── event_executor.py        # Event-driven executor
├── task.py                  # Task execution
├── parser.py                # YAML parser
├── input_generator.py       # Input generation
├── termination.py           # Termination conditions
├── event.py                 # Event system
├── event_queue.py           # Event priority queue
├── trigger.py               # Task triggers
├── simulation_time.py       # Simulated time management
├── execution_log.py         # Execution logging
└── exceptions.py            # Custom exceptions

examples/
├── simple_counter.yaml
├── async_temperature.yaml
└── ...

tests/
└── test_unified_execution.py
```

## Technical Details

MIMIC implements discrete-event simulation for event-driven components, using a priority queue to manage events sorted by time and priority. Tasks triggered by the same event execute in parallel using multi-threading . Synchronous ocmponents use topological sort for dependency resolution and sequential task execution.

The framework reduces code requirements significantly compared to raw Python implementations for typical components, while maintaining sufficient expressiveness for educational and prototyping use cases.

## Limitatios

- Single-machine execution (no distributed components)
- Task code limited to basic Python expressions (no function definitions or imports)
- Event-driven components cannot accept interactive user input during execution
- Not optimized for large-scale production simulations (millions of events)
- Best suited for educational purposes and rapid prototyping
