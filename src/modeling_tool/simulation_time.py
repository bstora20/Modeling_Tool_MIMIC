#simulation_time.py

class SimulationTime:
    def __init__(self, initial_time: float = 0.0):
        self.current_time = initial_time
        self.start_time = initial_time

    def advance_to(self, new_time: float):
        if new_time < self.current_time:
            raise ValueError(f"Cannot move time backwards: {new_time}<{self.current_time}")
        self.current_time = new_time

    def advance_by(self, delta: float):
        if delta<0:
            raise ValueError(f"cannot advance by a negative time:{delta}")
        self.current_time +=delta

    def elapsed(self)->float:
        return self.current_time-self.start_time

    def reset(self, time:float = 0.0):
        self.current_time = time
        self.start_time - time

    def __repr__(self):
        return f"Simulation(current={self.current_time})"

