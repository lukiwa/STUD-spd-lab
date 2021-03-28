from itertools import permutations, chain
from collections import deque

from .order import Order
from .grouped_tasks import GroupedTasks
from .helpers import get_c_max, pick_min, decay_grouped_tasks_to_2_machines, get_sorted_task_order, task_processing_time_on_all_machines, insert_into_task_order
from .helpers import get_partial_c_max
import numpy as np


class Resolver:
    def resolve(self, grouped_tasks: GroupedTasks) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")


class BruteForceResolver(Resolver):
    def resolve(self, grouped_tasks: GroupedTasks) -> Order:
        order = tuple(i for i in range(grouped_tasks.tasks_no()))

        best_order = order
        best_c_max = get_c_max(grouped_tasks, Order(order))

        for p in permutations(order):
            c_max = get_c_max(grouped_tasks, Order(p))
            if c_max < best_c_max:
                best_c_max = c_max
                best_order = p

        return Order(best_order)

# does this return the best order for problems with more than 2 machine?
# clarify


class JohnsonResolver(Resolver):
    def resolve(self, grouped_tasks: GroupedTasks) -> Order:
        grouped_tasks = decay_grouped_tasks_to_2_machines(grouped_tasks)

        a = [i for i in range(grouped_tasks.tasks_no())]
        l1 = []
        l2 = deque()

        while len(a) > 0:
            min_task_and_machine = pick_min(a, grouped_tasks)
            a.remove(min_task_and_machine[0])

            if min_task_and_machine[1] == 0:
                l1.append(min_task_and_machine[0])
            else:
                l2.appendleft(min_task_and_machine[0])

        return Order(tuple(chain(l1, l2)))



class NehResolver(Resolver):
    def resolve(self, grouped_tasks: GroupedTasks) -> Order:
        order = get_sorted_task_order(grouped_tasks)
        best_order = Order(order.order)
        current_order = Order(order.order[0])
        # for each task
        for task in range(1, grouped_tasks.tasks_no()):
            min_cmax = float('inf')
            # go through all places where you can place a task
            for index in range(0, task + 1):
                #try to add task at given position
                tmp_order = insert_into_task_order(current_order, index, order.order[task])
                #calculate c_max with task at this position
                tmp_cmax = get_partial_c_max(grouped_tasks, tmp_order, len(tmp_order.order))
                #check if it is better, if yes, this is new best order
                if min_cmax > tmp_cmax:
                    best_order = tmp_order
                    min_cmax = tmp_cmax
            current_order = best_order
        
        return current_order


