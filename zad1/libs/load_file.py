import numpy as np

from .grouped_tasks import GroupedTasks

def load_file(filename: str) -> GroupedTasks:
    with open(filename) as file:
        first_line = file.readline()
        tasks, machines = tuple(int(s) for s in first_line.split())

        result = GroupedTasks(np.ndarray([tasks, machines]))

        for task in range(tasks):
            line = file.readline()
            machine_time_values = tuple(int(s) for s in line.split())
            assert len(machine_time_values) == machines
            for machine in range(machines):
                result.matrix[task, machine] = machine_time_values[machine]

        return result
