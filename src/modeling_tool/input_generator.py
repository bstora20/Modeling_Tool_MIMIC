"""
Input generation for component execution.
"""

import random
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class InputGenerator(ABC):
    """Abstract base class for input generators."""
    
    @abstractmethod
    def generate(
        self, 
        input_names: List[str], 
        round_number: int,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate input values for a round.
        
        Args:
            input_names: List of required input names
            round_number: Current round number
            current_state: Current component state
            
        Returns:
            Dictionary mapping input names to values
        """
        pass


class InteractiveInputGenerator(InputGenerator):
    """Prompts user for input values each round."""
    
    def generate(
        self, 
        input_names: List[str], 
        round_number: int,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prompt user for each input."""
        print(f"\n--- Round {round_number} ---")
        print(f"Current state: {current_state}")
        
        inputs = {}
        for name in input_names:
            while True:
                try:
                    value_str = input(f"Enter value for '{name}': ")
                    # Try to parse as number, otherwise keep as string
                    try:
                        value = int(value_str)
                    except ValueError:
                        try:
                            value = float(value_str)
                        except ValueError:
                            # Handle boolean
                            if value_str.lower() in ['true', 'false']:
                                value = value_str.lower() == 'true'
                            else:
                                value = value_str
                    inputs[name] = value
                    break
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Invalid input: {e}. Please try again.")
        
        return inputs


class RandomInputGenerator(InputGenerator):
    """Generates random input values based on specifications."""
    
    def __init__(self, input_specs: Dict[str, Dict[str, Any]], seed: Optional[int] = None):
        """
        Initialize random input generator.
        
        Args:
            input_specs: Dictionary mapping input names to their specifications
                Example: {
                    'value': {'type': 'int', 'min': 0, 'max': 10},
                    'flag': {'type': 'bool'},
                    'name': {'type': 'str', 'choices': ['a', 'b', 'c']}
                }
            seed: Random seed for reproducibility
        """
        self.input_specs = input_specs
        self.random = random.Random(seed)  # Create instance-specific Random
    
    def generate(
        self, 
        input_names: List[str], 
        round_number: int,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate random values based on specifications."""
        inputs = {}
        
        for name in input_names:
            if name not in self.input_specs:
                raise ValueError(f"No specification found for input '{name}'")
            
            spec = self.input_specs[name]
            input_type = spec.get('type', 'int')
            
            if input_type == 'int':
                min_val = spec.get('min', 0)
                max_val = spec.get('max', 100)
                inputs[name] = self.random.randint(min_val, max_val)
            
            elif input_type == 'float':
                min_val = spec.get('min', 0.0)
                max_val = spec.get('max', 1.0)
                inputs[name] = self.random.uniform(min_val, max_val)
            
            elif input_type == 'bool':
                inputs[name] = self.random.choice([True, False])
            
            elif input_type == 'str':
                choices = spec.get('choices', ['a', 'b', 'c'])
                inputs[name] = self.random.choice(choices)
            
            else:
                raise ValueError(f"Unknown input type: {input_type}")
        
        return inputs


class FixedInputGenerator(InputGenerator):
    """Returns predetermined input sequences."""
    
    def __init__(self, input_sequence: List[Dict[str, Any]]):
        """
        Initialize with a sequence of inputs.
        
        Args:
            input_sequence: List of input dictionaries, one per round
        """
        self.input_sequence = input_sequence
    
    def generate(
        self, 
        input_names: List[str], 
        round_number: int,
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return the input for this round from the sequence."""
        if round_number > len(self.input_sequence):
            raise ValueError(f"No input defined for round {round_number}")
        
        return self.input_sequence[round_number - 1]
