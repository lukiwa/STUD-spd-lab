from collections import deque
from .order import Order
from .rpq_task import RPQTask
import numpy as np
from typing import Iterable, Tuple
from .priority_queue import PriorityQueue
import math

class RPQResolver:
    def resolve(self, queue: Iterable) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")
    def pmtn_resolve(self, queue: Iterable) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")


class SchrageN2Resolver(RPQResolver):
    def resolve(self, queue: list) -> Order:
        G = []
        N = queue

        t = min(N, key=lambda task: task.R).R

        order = []
        cmax = 0

        while len(G) != 0 or len(N) != 0:
            while len(N) != 0 and min(N, key=lambda task: task.R).R <= t:
                moved_task = min(N, key=lambda task: task.R)

                G.append(moved_task)
                N.remove(moved_task)

            if len(G) == 0:
                t = min(N, key=lambda task: task.R).R
            else:
                task = max(G, key=lambda task: task.Q)
                G.remove(task)
                order.append(task.task_no)
                t += task.P

                cmax = max(cmax, t + task.Q)


        return [Order(order), cmax]

    def pmtn_resolve(self, queue: list) -> Order:
        task_on_machine = None

        t = -math.inf
        G = []
        N = queue

        order = []
        cmax = 0

        while len(G) != 0 or len(N) != 0:
            while len(N) != 0 and min(N, key=lambda task: task.R).R <= t:
                moved_task = min(N, key=lambda task: task.R)

                G.append(moved_task)
                N.remove(moved_task)

                if task_on_machine is not None and moved_task.Q > task_on_machine.Q:
                    task_on_machine.P = t - moved_task.R
                    t = moved_task.R
                    if task_on_machine.P > 0:
                        G.append(task_on_machine)

            if len(G) == 0:
                t = min(N, key=lambda task: task.R).R
            else:
                task = max(G, key=lambda task: task.Q)
                G.remove(task)
                task_on_machine = task
                order.append(task.task_no)
                t += task.P

                cmax = max(cmax, t + task.Q)


        return [Order(order), cmax]

class SchrageLogNResolver(RPQResolver):
    def resolve(self, queue: list) -> Order:
        G = PriorityQueue(compare = lambda task1, task2:  task1.Q > task2.Q )
        N = PriorityQueue(compare = lambda task1, task2:  task1.R < task2.R )

        for task in queue:
            N.push(task)

        t = N.peek().R

        order = []
        cmax = 0

        while G.len() != 0 or N.len() != 0:
            while N.len() != 0 and N.peek().R <= t:
                G.push(N.pop())

            if G.len() == 0:
                # skip some time
                t = N.peek().R
            else:
                task = G.pop()
                order.append(task.task_no)
                t += task.P

                cmax = max(cmax, t + task.Q)


        return [Order(order), cmax]

    def pmtn_resolve(self, queue: list) -> Order:
        #ready_task = RPQTask(0,0,0,0)
        #task_on_machine = RPQTask(0,0,0, np.iinfo(np.uint16).max)
        task_on_machine = None

        G = PriorityQueue(compare = lambda task1, task2:  task1.Q > task2.Q )
        N = PriorityQueue(compare = lambda task1, task2:  task1.R < task2.R )
        for task in queue:
            N.push(task)

        t = N.peek().R

        order = []
        cmax = 0

        while G.len() != 0 or N.len() != 0:
            while N.len() != 0 and N.peek().R <= t:
                moved_task = N.pop()
                G.push(moved_task)

                if task_on_machine is not None and moved_task.Q > task_on_machine.Q:
                    task_on_machine.P = t - moved_task.R
                    t = moved_task.R
                    if task_on_machine.P > 0:
                        G.push(task_on_machine)

            if G.len() == 0:
                t = N.peek().R
            else:
                task = G.pop()
                task_on_machine = task
                order.append(task.task_no)
                t += task.P

                cmax = max(cmax, t + task.Q)

        return [Order(order), cmax]

class CarlierResolver(RPQResolver):
    SCHRAGE_RESOLVER = SchrageLogNResolver()

    def __init__(self):
        self.upper_bound_c_max = None
        self.pi_star_order = None

        self.tasks_from_recursion = deque()

    def _find_a_b(self, order, queue, c_max):
        t_global_current = -math.inf
        a_order_index, b_order_index = None, None

        for order_index, task_index in enumerate(order.order):
            task = queue[task_index]
            if task.R > t_global_current:
                a_order_index = order_index
                t_global_current = task.R
            t_global_current += task.P
            if t_global_current + task.Q == c_max:
                b_order_index = order_index

        assert a_order_index is not None and b_order_index is not None

        return a_order_index, b_order_index

    def _find_c(self, order, queue, a_order_index, b_order_index):
        c_order_index = None
        b_task = queue[order[b_order_index]]

        for order_index in range(a_order_index, b_order_index + 1):
            task = queue[order[order_index]]
            if task.Q < b_task.Q:
                c_order_index = order_index
        return c_order_index


    def _impl(self, queue: Iterable, swapped = False) -> Order:
        from libs.helpers import get_c_max_rpq

        u_order, u_cmax = self.SCHRAGE_RESOLVER.resolve([*queue])
        u_cmax_n = get_c_max_rpq(queue, u_order)

        assert u_cmax == u_cmax_n

        if self.upper_bound_c_max is None or u_cmax < self.upper_bound_c_max:
            self.upper_bound_c_max = u_cmax
            self.pi_star_order = u_order

        a_order_index, b_order_index = self._find_a_b(u_order, queue, u_cmax)
        c_order_index = self._find_c(u_order, queue, a_order_index, b_order_index)

        if c_order_index is None:
            return

        K = [*range(c_order_index + 1, b_order_index + 1)]
        assert len(K) > 0
        r_k = lambda K: min(K, key = lambda k: queue[u_order[k]].R)
        q_k = lambda K: min(K, key = lambda k: queue[u_order[k]].Q)
        p_k = lambda K: sum(queue[u_order[k]].P for k in K)

        only_k = {
            'r_k': r_k(K),
            'q_k': q_k(K),
            'p_k': p_k(K)
        }

        k_plus_c = {
            'r_k': r_k([c_order_index] + K),
            'q_k': q_k([c_order_index] + K),
            'p_k': p_k([c_order_index] + K)
        }

        if swapped:
            self._recursion_on_q(queue, u_order, c_order_index, only_k, k_plus_c, swapped)
            self._recursion_on_r(queue, u_order, c_order_index, only_k, k_plus_c, swapped)
        else:
            self._recursion_on_r(queue, u_order, c_order_index, only_k, k_plus_c, swapped)
            self._recursion_on_q(queue, u_order, c_order_index, only_k, k_plus_c, swapped)


    def _recursion_on_r(self, queue, order, c_order_index, only_k, k_plus_c, swapped):
        r_task = queue[order[c_order_index]]
        r_task_r_old = r_task.R
        r_task.R = max(r_task.R, only_k['r_k'] + only_k['p_k'])

        _, least_bound_c_max = self.SCHRAGE_RESOLVER.pmtn_resolve([*queue])
        least_bound_c_max = max(least_bound_c_max, sum(only_k.values()), sum(k_plus_c.values()))
        if least_bound_c_max < self.upper_bound_c_max:
            #self._impl(queue)
            from copy import deepcopy
            self.tasks_from_recursion.append(deepcopy(queue))
        r_task.R = r_task_r_old

    def _recursion_on_q(self, queue, order, c_order_index, only_k, k_plus_c, swapped):
        r_task = queue[order[c_order_index]]
        r_task_q_old = r_task.Q
        r_task.Q = max(r_task.Q, only_k['q_k'] + only_k['p_k'])

        _, least_bound_c_max = self.SCHRAGE_RESOLVER.pmtn_resolve([*queue])
        least_bound_c_max = max(least_bound_c_max, sum(only_k.values()), sum(k_plus_c.values()))
        if least_bound_c_max < self.upper_bound_c_max:
            #self._impl(queue)
            from copy import deepcopy
            self.tasks_from_recursion.append(deepcopy(queue))
        r_task.Q = r_task_q_old

    def resolve(self, queue: Iterable) -> Order:
        self._impl(queue)

        while len(self.tasks_from_recursion) > 0:
            self._impl(self.tasks_from_recursion[0])
            self.tasks_from_recursion.popleft()

        assert isinstance(self.pi_star_order, Order)
        return [self.pi_star_order, self.upper_bound_c_max]
