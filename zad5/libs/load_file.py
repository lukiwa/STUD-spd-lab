import numpy as np
import heapq

from .grouped_tasks import GroupedTasks
from .rpq_task import RPQTask


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

# will return priority queue of rpq task with argument as R


def rpq_load_file(filename: str):
    queue = []

    with open(filename) as file:
        first_line = file.readline()
        input = tuple(int(s) for s in first_line.split())

        if len(input) == 2:
            assert input[1] == 3

        tasks = input[0]

        for task in range(tasks):
            line = file.readline()

            R, P, Q = tuple(int(s) for s in line.split())
            rpq_task = RPQTask(task, R, P, Q)
            queue.append(rpq_task)

            #todo use priority queue here
            #heapq.heappush(queue, (rpq_task.prepare_time, rpq_task))

    return queue
