#execution.py

from typing import Dict, Any, List, Optional
import json
import csv

class RoundRecord:
    def __init__(self, round_number: int, inputs: Dict[str, Any], outputs: Dict[str, Any], state: Dict[str,Any], task_order: Optional[List[str]] = None):
        self.round_number = round_number
        self.inputs = inputs
        self.outputs = outputs
        self.state = state
        self.task_order = task_order

    def to_dict(self) -> Dict[str, Any]:
        record = {'round':self.round_number, 'inputs': self.inputs, 'outputs': self.outputs, 'state': self.state,}
        if self.task_order is not None:
            record['task_order'] = self.task_order
        return record

    def __repr__(self):
        return f"RoundRecord(round{self.round_number}, inputs={self.inputs}, outputs={self.outputs})"

class ExecutionLog:
    def __init__(self):
        self.rounds: List[RoundRecord] = []

    def add_round(self, round_number: int, inputs: Dict[str, Any], outputs: Dict[str, Any], state: Dict[str, Any], task_order: Optional[List[str]] = None) -> None:
        record = RoundRecord(round_number, inputs, outputs, state, task_order)
        self.rounds.append(record)

    def get_round(self, round_number: int) -> Optional[RoundRecord]:
        for record in self.rounds:
            if record.round_number == round_number:
                return record
        return None

    def to_json(self, filepath: str) -> None:
        data = {'total_rounds': len(self.rounds), 'rounds':[record.to_dict() for record in self.rounds]}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def to_csv(self, filepath: str) -> None:
        if not self.rounds:
            return
    
        with open(filepath, 'w', newline='') as f:
        # Determine all keys from first record
            first_record = self.rounds[0]
        
            fieldnames = ['round']
            fieldnames.extend([f'input_{k}' for k in sorted(first_record.inputs.keys())])
            fieldnames.extend([f'output_{k}' for k in sorted(first_record.outputs.keys())])
            fieldnames.extend([f'state_{k}' for k in sorted(first_record.state.keys())])
        
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        
            for record in self.rounds:
                row = {'round': record.round_number}
                row.update({f'input_{k}': v for k, v in record.inputs.items()})
                row.update({f'output_{k}': v for k, v in record.outputs.items()})
                row.update({f'state_{k}': v for k, v in record.state.items()})
                writer.writerow(row)

    def __len__(self):
        return len(self.rounds)

    def __repr__(self):
        return f"ExecutionLog({len(self.round)} rounds)"
