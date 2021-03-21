from itertools import permutations, chain
from collections import deque

from .order import Order
from .grouped_tasks import GroupedTasks
from .helpers import get_c_max, pick_min, decay_grouped_tasks_to_2_machines

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
