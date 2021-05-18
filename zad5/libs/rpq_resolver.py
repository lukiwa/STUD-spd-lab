from collections import deque
from libs.helpers import get_c_max_rpq
from .order import Order
from .rpq_task import RPQTask
import numpy as np
from typing import Iterable, Tuple
from .priority_queue import PriorityQueue
import math
from queue import Queue as Queue_synchronized
from copy import deepcopy

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
        G = PriorityQueue(compare = lambda task1, task2:  task1.Q >= task2.Q )
        N = PriorityQueue(compare = lambda task1, task2:  task1.R <= task2.R )

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
        task_on_machine = None

        G = PriorityQueue(compare = lambda task1, task2:  task1.Q >= task2.Q )
        N = PriorityQueue(compare = lambda task1, task2:  task1.R <= task2.R )
        for task in queue:
            N.push(task)

        t = 0

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


class CarlierDoneException(Exception):
    pass

def range_helper(a, b):
    if a < b:
        return range(a, b)
    else:
        return range(b, a)

class CarlierResolver(RPQResolver):
    def __init__(self):
        self.upper_bound_c_max = math.inf
        self.pi_star_order = None

        #self.tasks_from_recursion = Queue_synchronized()
        self.tasks_from_recursion = deque()

    def _find_a(self, order, queue, c_max, b_order_index):
        b_task = queue[order[b_order_index]]
        a_order_index = None

        for order_index, task_index in enumerate(order.order):
            task = queue[task_index]
            if task.R + sum(queue[order[s]].P for s in range(order_index, b_order_index + 1)) + b_task.Q == c_max:
                a_order_index = order_index

        assert a_order_index is not None
        return a_order_index

    def _find_b(self, order, queue, c_max):
        t = 0
        b_order_index = None

        for order_index, task_index in enumerate(order.order):
            task = queue[task_index]
            if task.R > t:
                t = task.R
            t += task.P
            if t + task.Q == c_max:
                b_order_index = order_index

        assert b_order_index is not None
        return b_order_index


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
        assert a_order_index <= b_order_index
        return a_order_index, b_order_index

    def _find_c(self, order, queue, a_order_index, b_order_index):
        c_order_index = None
        b_task = queue[order[b_order_index]]

        for order_index in range(a_order_index, b_order_index + 1):
            task = queue[order[order_index]]
            if task.Q < b_task.Q:
                c_order_index = order_index
        return c_order_index


    def r_func(self, K, queue, order):
        return min(queue[order[k]].R for k in K)

    def q_func(self, K, queue, order):
        return min(queue[order[k]].Q for k in K)

    def p_func(self, K, queue, order):
        return sum(queue[order[k]].P for k in K)

    def h_func(self, K, queue, order):
        return self.r_func(K, queue, order) + self.q_func(K, queue, order) + self.p_func(K, queue, order)


    def _impl(self, queue: Iterable) -> Order:
        from libs.helpers import get_c_max_rpq
        from copy import deepcopy

        u_order, u_cmax = SchrageLogNResolver().resolve(tuple(queue))

        if u_cmax < self.upper_bound_c_max:
            self.upper_bound_c_max = u_cmax
            self.pi_star_order = deepcopy(u_order)

        #a_order_index, b_order_index = self._find_a_b(u_order, queue, u_cmax)
        b_order_index = self._find_b(u_order, queue, u_cmax)
        a_order_index = self._find_a(u_order, queue, u_cmax, b_order_index)
        c_order_index = self._find_c(u_order, queue, a_order_index, b_order_index)

        if c_order_index is None:
            #raise CarlierDoneException()
            return

        K = [*range(c_order_index + 1, b_order_index + 1)]

        self._recursion_on_r(queue, u_order, c_order_index, K)
        self._recursion_on_q(queue, u_order, c_order_index, K)


    def _recursion_on_r(self, queue, order, c_order_index, K):
        r_task = queue[order[c_order_index]]
        r_task_r_old = r_task.R
        r_task.R = max(r_task.R, self.r_func(K, queue, order) + self.p_func(K, queue, order))

        _, least_bound_c_max = SchrageLogNResolver().pmtn_resolve([*queue])
        least_bound_c_max = max(least_bound_c_max, self.h_func(K, queue, order), self.h_func(K + [c_order_index], queue, order))
        if least_bound_c_max < self.upper_bound_c_max:
            #self._impl(queue)
            self.tasks_from_recursion.append((deepcopy(queue), self.upper_bound_c_max))
        r_task.R = r_task_r_old

    def _recursion_on_q(self, queue, order, c_order_index, K):
        r_task = queue[order[c_order_index]]
        r_task_q_old = r_task.Q
        r_task.Q = max(r_task.Q, self.q_func(K, queue, order) + self.p_func(K, queue, order))

        _, least_bound_c_max = SchrageLogNResolver().pmtn_resolve([*queue])
        least_bound_c_max = max(least_bound_c_max, self.h_func(K, queue, order), self.h_func(K + [c_order_index], queue, order))
        if least_bound_c_max < self.upper_bound_c_max:
            #self._impl(queue)
            self.tasks_from_recursion.append((deepcopy(queue), self.upper_bound_c_max))
        r_task.Q = r_task_q_old

    def resolve(self, queue: Iterable) -> Order:
        try:
            self._impl(deepcopy(queue))

            #from multiprocessing import Pool

            while len(self.tasks_from_recursion) > 0:
                tasks, upper_bound = self.tasks_from_recursion[0]
                self.tasks_from_recursion.popleft()
                self._impl(tasks)


        except CarlierDoneException:
            pass

        return [
            self.pi_star_order,
            self.upper_bound_c_max]
