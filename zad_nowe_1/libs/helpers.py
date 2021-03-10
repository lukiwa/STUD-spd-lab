from typing import List, Tuple
import numpy as np

from .grouped_tasks import GroupedTasks
from .order import Order

def get_c_max(groupedTasks: GroupedTasks, order: Order) -> int:
    # a[i] -> time when i-th machine is free
    a = np.zeros(groupedTasks.machines_no())

    for taskIdx in range(groupedTasks.tasks_no()):
        # time when previous machine is free,
        # relative to machine variable
        previous_machine_end_time = 0

        for machine in range(groupedTasks.machines_no()):

            task_time = groupedTasks.matrix[order.order[taskIdx], machine]

            if a[machine] > previous_machine_end_time:
                # operation on previous machine was finished before
                # operation on current machine could continue
                a[machine] += task_time
            else:
                # next machine were free before end of previous operation
                a[machine] = previous_machine_end_time + task_time

            previous_machine_end_time = a[machine]

    return a[groupedTasks.machines_no() - 1]

def pick_min(tasksQueue: List[int], groupedTasks: GroupedTasks) -> Tuple[int, int]:
    min_time = groupedTasks.matrix[tasksQueue[0], 0]
    min_time_task_machine = (tasksQueue[0], 0)

    for taskIdx in tasksQueue:
        for machine in range(groupedTasks.machines_no()):
            if min_time > groupedTasks.matrix[taskIdx, machine]:
                min_time = groupedTasks.matrix[taskIdx, machine]
                min_time_task_machine = (taskIdx, machine)

    return min_time_task_machine

def decay_grouped_tasks_to_2_machines(groupedTasks: GroupedTasks) -> GroupedTasks:
    result = groupedTasks

    while result.machines_no() > 2:
        new_result = np.ndarray([result.tasks_no(), result.machines_no() - 1])

        for task_idx in range(result.tasks_no()):
            for new_machine in range(result.machines_no() - 1):
                new_result[task_idx, new_machine] = result.matrix[task_idx, new_machine] + result.matrix[task_idx, new_machine + 1]

        result = GroupedTasks(new_result)

    return result
