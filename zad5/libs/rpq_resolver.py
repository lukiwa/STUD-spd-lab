from collections import deque
from os import sched_rr_get_interval
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
                    task_on_machine = RPQTask(
                        task_no = task_on_machine.task_no,
                        R = task_on_machine.R,
                        P = t - moved_task.R,
                        Q = task_on_machine.Q)
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
                    task_on_machine = RPQTask(
                        task_no = task_on_machine.task_no,
                        R = task_on_machine.R,
                        P = t - moved_task.R,
                        Q = task_on_machine.Q)
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

from enum import Enum

class CarlierStrategy(Enum):
    Normal = 0
    BFS = 1

class CarlierDoneException(Exception):
    pass

class CarlierResolver(RPQResolver):
    def __init__(self, strategy: CarlierStrategy, schrage):
        self.strategy = strategy
        self.schrage = schrage


    def add_vertex(self, queue, upper_bound: IntPtr, pi_star: Order, u_cmax: int):
        if self.strategy == CarlierStrategy.Normal:
            self._impl(queue, upper_bound, pi_star)
        else:
            self.tasks_from_recursion.append(((deepcopy(queue), u_cmax)))

    @staticmethod
    def _find_a(order, queue, c_max, b_order_index):
        b_task = queue[order[b_order_index]]

        for order_index, task_index in enumerate(order.order):
            task = queue[task_index]
            if task.R + sum(queue[order[s]].P for s in range(order_index, b_order_index + 1)) + b_task.Q == c_max:
                return order_index

        raise RuntimeError('a not found')

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
    def _find_a_b(order, queue, c_max):
        t = 0
        a_order_index, b_order_index = None, None

        for order_index, task_index in enumerate(order.order):
            task = queue[task_index]
            if task.R > t:
                a_order_index = order_index
                t = task.R
            t += task.P
            if t + task.Q == c_max:
                b_order_index = order_index

        return a_order_index, b_order_index

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
        u_order, u_cmax = self.schrage().resolve([*queue])

        if u_cmax < upper_bound.val:
            upper_bound.val = u_cmax
            pi_star.order = deepcopy(u_order.order)
            self.current_cmax_iter = 0
        else:
            self.current_cmax_iter += 1

        if self.current_cmax_iter > self.max_iter:
            raise CarlierDoneException()

        b_order_index = CarlierResolver._find_b(u_order, queue, u_cmax)
        a_order_index = CarlierResolver._find_a(u_order, queue, u_cmax, b_order_index)
        #a_order_index, b_order_index = CarlierResolver._find_a_b(u_order, queue, u_cmax)
        if a_order_index is None or b_order_index is None:
            raise CarlierDoneException()

        c_order_index = CarlierResolver._find_c(u_order, queue, a_order_index, b_order_index)
        if c_order_index is None:
            raise CarlierDoneException()

        K = [*range(c_order_index+1, b_order_index+1)]

        self._recursion_on_r(queue, u_order, c_order_index, K, upper_bound, pi_star, u_cmax)
        self._recursion_on_q(queue, u_order, c_order_index, K, upper_bound, pi_star, u_cmax)



    def _recursion_on_r(self, queue, order, c_order_index, K, upper_bound: IntPtr, pi_star: Order, u_cmax):
        r_task = queue[order[c_order_index]]
        queue[order[c_order_index]] = RPQTask(
            task_no = r_task.task_no,
            R = max(r_task.R, CarlierResolver.r_func(K, queue, order) + CarlierResolver.p_func(K, queue, order)),
            P = r_task.P,
            Q = r_task.Q
        )

        _, least_bound_c_max = self.schrage().pmtn_resolve([*queue])
        least_bound_c_max = max(least_bound_c_max, CarlierResolver.h_func(K, queue, order), CarlierResolver.h_func([c_order_index] + K, queue, order))

        if least_bound_c_max < upper_bound.val:
            self.add_vertex(queue, upper_bound, pi_star, u_cmax)

        queue[order[c_order_index]] = r_task

    def _recursion_on_q(self, queue, order, c_order_index, K, upper_bound, pi_star, u_cmax):
        r_task = queue[order[c_order_index]]
        queue[order[c_order_index]] = RPQTask(
            task_no = r_task.task_no,
            R = r_task.R,
            P = r_task.P,
            Q = max(r_task.Q, CarlierResolver.q_func(K, queue, order) + CarlierResolver.p_func(K, queue, order))
        )

        _, least_bound_c_max = self.schrage().pmtn_resolve([*queue])
        least_bound_c_max = max(least_bound_c_max, CarlierResolver.h_func(K, queue, order), CarlierResolver.h_func([c_order_index] + K, queue, order))

        if least_bound_c_max < upper_bound.val:
            self.add_vertex(queue, upper_bound, pi_star, u_cmax)

        queue[order[c_order_index]] = r_task

    def resolve(self, queue: Iterable) -> Order:
        pi_star = Order(order=None)
        upper_bound = IntPtr(math.inf)
        self.max_iter = 1000
        self.current_cmax_iter = 0
        self.tasks_from_recursion = []

        try:
            self._impl(deepcopy(queue), upper_bound, pi_star)

            while len(self.tasks_from_recursion) > 0:
                processing = min(self.tasks_from_recursion, key=lambda obj: obj[1])
                self.tasks_from_recursion.remove(processing)
                self._impl(processing[0], upper_bound, pi_star)

        except CarlierDoneException:
            pass

        return [
            pi_star,
            upper_bound]

    def __repr__(self):
        return f"CarlierResolver({self.schrage}, {self.strategy})"
