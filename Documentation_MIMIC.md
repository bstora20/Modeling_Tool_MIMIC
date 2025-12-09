# MIMIC User Guide

## Table of Contents
1. [Intriduction](#intorduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Component DSL Reference](#component-dsl-reference)
6. [Execution Models](#execution-models)
7. [Input Generation](#input-generation)
8. [Termination Conditions](#termination-conditions)
9. [Event-Driven Execution](#event-driven-execution)
10. [Command-Line Interface](#command-line-interface)
11. [Complete Examples](#complete-exemples)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

--

## Introduction

MIMIC (Modeling Interface for Multi-mode Integrated Components) is a Python-based framework for modeling and simulating components that can execute either synchronously or in event-driven mode. Components are defined using YAML files rather than extensive Python code, making the framework accessible to students and researchers who want to focus on component logic rather than implementation details. 

### What MIMIC Does

- Components are defined using declarative YAML specifications
- Two execution modes are supported: round-based execution for discrete steps and event-driven execution for simulated time
- Both execution modes use the same CLI interface
- Input can be generated interactively (synchronous only), randomly or from scheduled configuration (event-driven only)
- Termination conditions work consistently across both execution modes
- All execution can be logged to JSON or CSV files
- PyYAML is the only dependency
- Event-driven mode supports parallel task execution using htreads

### Use Cases

MIMIC can model various systems including sensor networks, IoT devices, state machines, control systems, distributed algorithms such as merge sort or leader election, network protocols, data processing pipelines, and simulations requiringg realistic timing behavior. 

---

## Installation

### Requirements

-Python 3.7 or newer
-PyYAML 6.0 or newer

### Setup

```bash
# Navigate to the project directory
cd mimic

# Create a virtual environment (recommended)
python -m venv venv

#Activate the virtual environment 
# On macOS or Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Requirements
pip install -r requirements.txt

# Verify installation
python -c "from modeling_tool import Executor; print('Installation successful')"
```

---

## Quick Start

### Creating Your First Component

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

### Running the Component

```bash
python -m modeling_tool.cli my_counter.yaml \
    --input-mode interactive \
    --rounds 5 \
    --verbose
```

The program will prompt you to enter values and display the ocunter incrementing. 

--- 

## Core Concepts

### Components

A component is the fundamental building block in MIMIC. Each component consists of state variables that persist between executions, inputs that come from external sources, outputs that the component produces, and tasks that contain the computational logic. 

### Component Types

**Synchronous Components**
- Tasks execute sequentially in dependency order
- Each execution cycle is called a "round"
- Behavior is predictable and deterministic
- Suitable for batch processing and step-by-step algorithms

**Event-Driven Components**
- Tasks execute when triggered by events
- Uses simulated time that advances instantaneously
- More flexible and reactive that synchronous components
- Suitable for sensor systems, reactive algorithms, and simulations requiring realistic timing

### Tasks

Tasks are code blocks that can read from inputs and state, write to outputs and state, specify dependencies on other takss (synchronous mode), specify triggers for execution (event-driven mode), and execute Python code in a controlled namespace.

### State, Inputs, and Outputs

```yaml
state:
    counter: 0      # Persists between rounds/events
    history: []
    
inputs:
    - value         # Provided each round or event

outputs:
    - result        # Calculated by tasks
    - status
```

---

## Component DSL Reference

### Basic Structure

Components are defined using the following YAML structure:

```yaml
component:
    name: ComponentName
    type: synchronous       # or asynchronous
    
    state:                  # Initial values for state variables
        var1: initial_value
        var2: []
    
    inputs:                 # Component input variables
        - input1
        - input2
        
    outputs:                # Component output variables
        - output1
        - output2
        
    tasks:                  # Computational logic
        - name: task1
          code: |
            # Python code
```

### Synchronous Tasks

```yaml
tasks:
    - name: task_name
      code: |
        #Your Python code
        state.counter +=1
        outputs.result = state.counter
        
    - name: dependent_task
      depends_on: [task_name]   #Executes after task_name
      code: |
        outputs.status = "done"
```

Execution order is determined automatically based on dependencies using topological sort. 

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

### Available Variables in Task Code

Tasks have access to the following variables:

- `inputs.variable_name` for input values
- `state.variable_name` for state variables
- `outputs.variable_name` for output vairables
- `current_time` for the current simulation time (event-driven only)
- `event_data` for data from the triggering event (event-driven only)
- `emit_event(name, data, delay, priority)` to emit new events (event-driven only)

**Example:**
```python
# Reading inputs and state
value = inputs.sensor_reading
history = state.readings

# Modifying state
state.readings.append(value)
state.count +=1

# Setting outputs
outputs.average = sum(state.readings) / len(state.readings)
outputs.total = state.count

# For event-driven mode
print(f"Processing at time {current_time}")
emit_event("processing_complete", data=value)
```

---

## Execution Models

### Round-Based Execution

Synchronous components execute through the following process:
1. Generate inputs for the current round
2. Execute all tasks in dependency order
3. Log the results
4. Check termination condition
5. Repeat until termination 

### Event-Driven Execution

Event-driven components use discrete0event simulation:
1. Events are scheduled in a priority queue sorted by time
2. The simulation advances to the next event time instantaneously
3. tasks triggered by that event execute in parallel
4. Tasks can emit new events that are added to the queue
5. Process continues untils termination condition is met

---

## Input Generation

Input generation works differently for synchronous and event-driven components due to fundamental differences in their execution models.

### Interactive Input

Interactive input prompts the user for values at each round. **This only works for synchronous components**   because they execute round-by-round and can pause between rounds.

```bash
python -m modeling_tool.cli component.yaml \
    --input-mode interactive \
    --rounds 5
```

When executed, the program will prompt you at each round:

```
--- Round 1 ---
Current state: {'count': 0}
Enter value for 'increment': 5

--- Round 2 ---
Current state: {'count': 5}
Enter value for 'increment': 3
```

### Random Input

Random input generates values based on specifications you provide. This works for both synchronous and event-driven components. 

** For synchronous components:**

```bash
python -m modeling_tool.cli component.yaml \
    --input-mode random \
    --random-inputs "value:int:1:10,flag:bool" \
    --rounds 10 \
    --seed 42
```

** For event-driven components with periodic inputs:**

```bash
python -m modeling_tool.cli async_component.yaml
    --input-mode random \
    --random-inputs "sensor:float:0:100" \
    --input-interval 2.0 \
    --max-time 60.0 \
    --seed 42
```

The format is `name:type:min:max` where types can be `int`, `float`, `bool`, or `str`. For int and float, you must specify min and max values. For bool, min and maxare not needed.

When using periodic inputs with event-driven components, new inputs are generated at regular intervals in simulated time, an input event is emitted witht he default name `input_ready`, and tasks can listen for this event to process the new inputs.

```yaml
# In your event-driven component
task:
            - name: process_sensor_data
              trigger:
                    type: event
                    event: input_ready
              code: |
                    senser_value = inputs.sensor_value
                    state.readings.append(sensor_value)
                    print(f"[{current_time:.1f}s] New reading: {sensor_value}")
```

### Initial Inputs

For event-driven components, you can set starting input values that are provided once at the beginning of the simulation.

```bash
python -m modeling_tool.cli async_component.yaml \
    --initial-inputs "temperature=20.0, active=true" \
    --max-time 30.0
```

This is useful when your component needs values to start with but does not need them to change during execution. For example, a merge component that neds two lists:

```bash
python -m modeling_tool.cli async_merge.yaml \
    --initial-inputs "list_a=[1,3,5,7], list_b=[2,4,6,8]" \
    --verbose
```

YOur component can access these initial inputs when it starts:

```yaml
tasks:
    - name: initialize
      trigger:
            type: event
            event: input_ready  # Fires once at start with initial_inputs
      code: |
            state.list_a = inputs.list_a
            state.list_b = inputs.list_b
            emit_event("start_processing")
 ```
 
 Note that the CLI's ability to parse complex values like lists may be limited. 
 
 ### Why Interactive Input Does Not Work for Event-Driven Components
 
 Event-drive components cannot pause for interactive input because they execute in simulated time rather than real time. Understanding this limitation requires understanding how simulated time works. 
 
 In event-driven execution, time exists only as metadata on events. The simulation advances from one event to the next instantaneously, without any actual waiting. For example:
 
 ```
 Real time:         [-------0.001 seconds-------]      
 Simulated time: 0.0s → 1.0s → 2.0s → 10.0s → 50.0s
 ```
 
 A simulation covering 50 seconds of simulated time might complete in 1 millisecond of real time. The entire simulation finishes before a human could event see what happened, much less type input.
 
 This is by design. Simulated type advance instantly between events, allowing the simulation to run as fast as possible without actually waiting. This enables you to simulate hours or days of activity in seconds of computer time. However, it creates a fundamental mismatch between comput processing time, which operates at microsecond scales, and human reaction time, which requires seconds to read prompts, understand requests, and type responses.
 
 If you need to provide inputs for an event-driven component, you have several options: use initial inputs to set starting values, use periodic random inputs with `--input-interval` for automated variatio, or use a synchronous component if you need interactive control.
 
 ## Termination Conditions
 
 Termination conditions determine when simulation should stop. They work consistently across both synchronous and event-driven components.
 
 ### For Synchronous Components
 
 **Max Rounds** 
 Stop after a specified number of rounds:
 
 ```bash
 --rounds 100
 ```
 
 **State Condition**
 
 Stop when a condition becomes true:
 
 ```bash
 --condition "state['counter'] >= 50"
 ```
 
 ### For Event-Driven Components
 
 **Max Time**
 
 Stop after a specific amount of simulated time:
 
 ```bash
 --max-time 100.0
```

**Max Events**

Stop after processing a specified numer of events:

```bash
--max-events 1000
```

**Empty Queue**

Stop when there are no more events scheduled. This is the default termination condition if no other is specified

**State Condition**

This works the same as for synchronous components:

```bash
--condition "state['done'] == True"
```

### Combining Conditions

YOu can combine multiple conditions. The simulation stops when any condition is met:

```bash
# For synchronous: stop at 100 rounfs OR when done
--rounds 100 --condition"state['done']"

# For event-driven: stop at 100s OR 1000 events OR when error occurs
--max-time 100.0 --max-events 1000 --condition "state['error']"
```

---

## Event-Driven Execution

### Overview

Event-driven execution enables components to react to events in simulated time. This is useful for sensor systems, reactive algorithms, simulations requiring realistic timing, and systems where timing varies dynabically. 

### Events

An event represents something happening at a specific time in simulation:

```python
Event(
    time=5.0,               # When it occurs (simulated seconds)
    name="sensor_reading",  # What happened
    data={'value': 25.3},   # Optional data
    priority=0              # Lower number = higher priority
)
```

### Triggers

Triggers determine when tasks should execute:

**Periodic Trigger**

Executes at regular intervals:

```yaml
trigger:
    type: periodic
    interval: 1.0 # Every 1 second
```

**Event Trigger**

Executes when a specific event occurs:

```yaml
trigger:
        type: event
        event: data_ready
```

**Condition Trigger**

Executes when a condition transitions from false to true:

```yaml
trigger:
    type: condition
    condition: "state['temperature'] > 100"
```

**Immediate Trigger**

Executes once at the start:

```yaml
trigger:
    type: immediate
```

### Emitting Events

Tasks can emit events to trigger other tasks:

```python
# Basic emission
emit_event("alarm")

# With data
emit_event("reading", data=25.5)

# With delay (schedule for later)
emit_event("delayed_action", delay =2.0)

# With priority
emit_event("urgent", priority=0)
```

### Self-Triggering Pattern

Tasks can re-emit their own trigger event to execut emultiple times;

```yaml
tasks:
    - name: countdown
      trigger:
            type: event
            event: tick
      code: |
            state.counter -=1
            print(f"Counter: {state.counter}")
            
            # Trigger itself again if not done
            if state.counter > 0:
                emit_event("tick", delay-0.0)
```

This pattern is useful for fraining buffers, polling until a condition is met, implementing iterative algorithms, and implementing retry logic. 

### Parallel Execution

When multiple tasks are tirggered by the same event, they execute in parallel using treads:

```yaml
tasks:
    - name: sensor_a
      trigger: {type: event, event: read_all}
      code: state.a = read_sensor_a()
        
    - name: sensor_b
      trigger: {type: event, event: read_all}
      code: state.b = read_sensor_b()
        
    - name: sensor_c
      trigger: {type: event, event: read_all}
      code: state.c = read_sensor_c()
        
#All three execute concurrently when "read_all" fires
```
---

## Modeling True Asynchronous Components

The event-driven examples in this guide demonstrate the framework's capabilities but do not strictly model true asynchronous components. In real asynchronous systems, each task performs exactly one atomic operation: reading one input, modifying one state variable, or writing one output.

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
    

---
## Command-Line Interface

The CLI automatically detects the component type from your YAML file and executes it appropriately. 

### Basic Usage

```bash
python -m modeling_tool.cli <component_file> [options]
```

/periodic
### Examples

**Synchronous with random inputs:**
```bash
python -m modeling_tool.cli counter.yaml \
    --input-mode random \
    --random-inputs "values:int:1:100" \
    --rounds 50 \
    --seeds 42 \
    --verbose
```

**Event-driven with time limit:**
```bash
python -m modeling_tool.cli sensor.yaml \
    --max-time 100.0 \
    --verbose
```

**Event-driven with periodic inputs:**
```bash
python -m modeling_tool.cli temperature.yaml \
    --input-mode random \
    --random-inputs "ambient_temp:float:15:35" \
    --input-interval 2.0 \
    --max-time 60.0 \
    --verbose
```

**Multiple termination conditions:**
```bash
python -m modeling_tool.cli component.yaml \
    --rounds 100 \
    --condition "state['done'] == True" \
    --output results.json
```

**Saving to CSV:**
```bash
python -m modeling_tool.cli component.yaml \
    --input-mode random \
    --random-inputs "x:float:0:1,y:float:0:1" \
    --rounds 50 \
    --output data.csv
```

---

## Complete Examples

### Example 1: Simple Counter

This demonstrates a basic synchronous component:

```yaml
component:
    name: Counter
    type: synchronous
    
    state:
        total: 0
    
    inputs:
        - increment
    
    outputs:
        - running_total
    
    tasks:
        - name: update
          code: |
                state.total += inputs.increment
                outputs.running_total = state.total
```

**Execution:**
```bash
python -m modeling_tool.clo counter.yaml \
    --input-mode random \
    --random-inputs "increment:int:1:5" \
    --rounds 10 \
    --verbose
```

### Example 2: Temperature Monitor

This demonstrates an event-driven component that reads temperature inputs:

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

**Execution:**
```bash
python -m modeling_tool.cli temperature.yaml \
    --input-mode random \
    --random-inputs "ambient_temp:float:18:32" \
    --input-interval 2.0 \
    --max-time 30.0 \
    --seed 42 \
    --verbose
```

### Example 3: Periodi Task

This demonstrates a simple periodic task:

```yaml
component:
    name: PeriodicLogger
    type: asynchronous
    
    state:
        tick_count: 0
        
    inputs: []
    
    outputs:
        - ticks
        
    tasks:
        - name: periodic_tick
          trigger:
                type: periodic
                interval: 1.0
          code: |
                state.tick_count +=1
                outputs.ticks = state.tick_count
                print(f"{current_time:.1f}s Tick {state.tick_count}"))
```

**Execution:**
```bash
python -m modeling_tool.cli periodic.yaml \
    --max-time 10.0
```

---

## Best Practices

### General Guidelines

- Start with synchronous components to learn the basics before attempting event-driven components
- Test tasks individually before combining them into complex workflows
- Use clear, descriptive names for tasks and variables
- Add comments to explain complex logic
- Use print statements to observe execution behavior

### For Round-Based Components

- Keep each task focused on a single responsibility
- Only add dependencies when tasks must execute in a specific order
- Ensure initial state values are appropriate for your use case
- Test with fixed input using interactive mode before using random inputs

### For Event-Driven Components

- Always include a termination condition such as max-time or max-events to prevent infinite execution
- Be careful with self-triggering to avoid inifinite loops
- Use delay=0.0 for immediate events, delay=1.0 or more for spacing them out
- Use .get() with default values when accessing event data to handle missing keys
- Add timing information to print statement like `print(f"[{current_time}s] ...)`
- Verify that events fire when expected
- Use input generators with input intervals for periodic inputs
- For true, asynchronous modeling, keep tasks granular ( each task should ideally only perform one operation: read one input, modify one state variablem or write one output

### For Termination Conditions

- Always set a termination condition to prevent infinite execution
- Test each condition separately before combining them
- Use state conditions to stop when you reach your goal

### Performance Guidelines

- Set max-workers if you need to limit parallelism
- Keep task code efficient and avoid slow operations
- Use periodic triggers for regular sampling, event triggers for reactions
- Process multiple items per task execution when possible

---

## Troubleshooting

### Common Issues

**"dict object has no attribute 'x'"**

You are using bracket notation instead of dot notation. Use `state.x` not `state['x']` in your task code. 

**"Task has no attribute 'trigger'"**

You forgot to set a trigger for an event-driven task. Event-driven tasks require:
```yaml
trigger:
    type: event
    event: event_name
```

**"Circular task dependencies"**

Your tasks depend on each other in a loop. Check the depends_on relationships and remove the circular dependencies.

**"Simulation runs forever"**

Either you did not set a termination condition or there is an inifinite loop in your self-triggering. Add a max-time or max-events parameter, check that self-triggering conditions have an exit, and add debug prints to track execution.

**"No tasks ready to execute"**

All you tasks have dependencies that are not satisfied. Ensure at least one task has no dependencies or is triggered by an initial event.

**"Synchronous components require --input-mode"**

You forgot to specify the input mode. Add either `--input-mode interactive` or `--inputs-mode random`. 

### Getting Help

- Examine the examples in the example directory
- Use the --verbose flag to see detaile dexecution information
- Add print statements ti your task code for debugging
- Use --track-tasks to see the execution order

For more information, review the examples directory for completeworking examples and examine the YAML files to learn the syntax. 
            
