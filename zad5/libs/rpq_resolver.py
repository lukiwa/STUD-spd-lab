from collections import deque
from libs.helpers import get_c_max_rpq
from .order import Order
from .rpq_task import RPQTask
import numpy as np
from typing import Iterable, Tuple
from .priority_queue import PriorityQueue
from .int_ptr import IntPtr
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
        pass

    @staticmethod
    def _find_a(order, queue, c_max, b_order_index):
        b_task = queue[order[b_order_index]]
        #a_order_index = None

        for order_index, task_index in enumerate(order.order):
            task = queue[task_index]
            if task.R + sum(queue[order[s]].P for s in range(order_index, b_order_index + 1)) + b_task.Q == c_max:
                return order_index

        raise RuntimeError()

    @staticmethod
    def _find_b(order, queue, c_max):
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

    @staticmethod
    def _find_c(order, queue, a_order_index, b_order_index):
        c_order_index = None
        b_task = queue[order[b_order_index]]

        for order_index in range(a_order_index, b_order_index + 1):
            task = queue[order[order_index]]
            if task.Q < b_task.Q:
                c_order_index = order_index

        return c_order_index

    @staticmethod
    def r_func(K, queue, order):
        r_times = (queue[order[k]].R for k in K)
        return min(r_times)

    @staticmethod
    def q_func(K, queue, order):
        q_times = (queue[order[k]].Q for k in K)
        return min(q_times)

    @staticmethod
    def p_func(K, queue, order):
        p_times = (queue[order[k]].P for k in K)
        return sum(p_times)

    @staticmethod
    def h_func(K, queue, order):
        return (
            CarlierResolver.r_func(K, queue, order)
            + CarlierResolver.q_func(K, queue, order)
            + CarlierResolver.p_func(K, queue, order))

    def _impl(self, queue: Iterable, upper_bound: IntPtr, pi_star: Order) -> Order:
        u_order, u_cmax = SchrageN2Resolver().resolve([*queue])
        #original_c_max = get_c_max_rpq(queue, self.original_queue)

        if u_cmax < u_cmax:
            upper_bound.val = u_cmax
            pi_star.order = deepcopy(u_order.order)

        b_order_index = CarlierResolver._find_b(u_order, queue, u_cmax)
        a_order_index = CarlierResolver._find_a(u_order, queue, u_cmax, b_order_index)
        c_order_index = CarlierResolver._find_c(u_order, queue, a_order_index, b_order_index)

        if c_order_index is None:
            #raise CarlierDoneExcption()
            return

        K = [*range(c_order_index+1, b_order_index+1)]

        self._recursion_on_r(queue, u_order, c_order_index, K, upper_bound, pi_star)
        self._recursion_on_q(queue, u_order, c_order_index, K, upper_bound, pi_star)



    def _recursion_on_r(self, queue, order, c_order_index, K, upper_bound: IntPtr, pi_star: Order):
        r_task = queue[order[c_order_index]]
        r_task_r_old = r_task.R
        r_task.R = max(r_task.R, CarlierResolver.r_func(K, queue, order) + CarlierResolver.p_func(K, queue, order))

        _, least_bound_c_max = SchrageN2Resolver().pmtn_resolve([*queue])
        #least_bound_c_max = max(least_bound_c_max, CarlierResolver.h_func(K, queue, order), CarlierResolver.h_func([c_order_index] + K, queue, order))

        if least_bound_c_max < upper_bound.val:
            self._impl(queue, upper_bound, pi_star)
            #self.tasks_from_recursion.append((deepcopy(queue), self.upper_bound_c_max))
        r_task.R = r_task_r_old


    def _recursion_on_q(self, queue, order, c_order_index, K, upper_bound, pi_star):
        r_task = queue[order[c_order_index]]
        r_task_q_old = r_task.Q
        r_task.Q = max(r_task.Q, CarlierResolver.q_func(K, queue, order) + CarlierResolver.p_func(K, queue, order))

        _, least_bound_c_max = SchrageN2Resolver().pmtn_resolve([*queue])
        #least_bound_c_max = max(least_bound_c_max, CarlierResolver.h_func(K, queue, order), CarlierResolver.h_func([c_order_index] + K, queue, order))

        if least_bound_c_max < upper_bound.val:
            self._impl(queue, upper_bound, pi_star)
            #self.tasks_from_recursion.append((deepcopy(queue), upper_bound_c_max))
        r_task.Q = r_task_q_old

    def resolve(self, queue: Iterable) -> Order:
        pi_star = Order(order=None)
        upper_bound = IntPtr(math.inf)

        self.original_queue = tuple(queue)

        try:
            self._impl(deepcopy(queue), upper_bound, pi_star)

            '''
            from multiprocessing import Pool

            while len(self.tasks_from_recursion) > 0:
                tasks, upper_bound = self.tasks_from_recursion[0]
                self.tasks_from_recursion.popleft()
                self._impl(tasks)
            '''


        except CarlierDoneException:
            pass

        return [
            pi_star,
            upper_bound]
