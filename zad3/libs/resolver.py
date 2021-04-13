from dataclasses import dataclass
from random import randint
from itertools import permutations, chain
from collections import deque
from typing import Tuple
from time import time

import numpy as np
from numpy.core.fromnumeric import _swapaxes_dispatcher

from .order import NpOrder, Order
from .grouped_tasks import GroupedTasks
from .helpers import (get_c_max, pick_min, decay_grouped_tasks_to_2_machines, get_sorted_task_order,
    task_processing_time_on_all_machines, get_partial_c_max)




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
        current_order = Order(deque([order.order[0]]))

        # for each task
        for task in range(1, grouped_tasks.tasks_no()):
            min_cmax = float('inf')
            best_order_for_index = None

            # add current task to beginning of an order
            current_order.order.appendleft(order.order[task])
            foo = current_order.order

            # go through all places where you can place a task
            for index in range(0, task + 1):
                #calculate c_max with task at this position
                tmp_cmax = get_partial_c_max(grouped_tasks, current_order, len(current_order.order))

                #check if it is better, if yes, this is new best order
                if min_cmax > tmp_cmax:
                    # remember index for which best order occured
                    best_order_for_index = index
                    min_cmax = tmp_cmax

                # don't go inside on last loop
                if index != task:
                    # advance added task to next index
                    foo[index], foo[index+1] = foo[index+1], foo[index]

            # pop last item (task added in line 65)
            current_order.order.pop()
            current_order.order.insert(best_order_for_index, order.order[task])

        return current_order


class TsResolver(Resolver):
    def __init__(self, neighbours_max, first_order=None):
        self.neighbours_max = neighbours_max
        self.first_order = first_order

    def gen_idx(self, max):
        idx_a = randint(0, max)
        idx_b = randint(0, max)
        while idx_a == idx_b:
            idx_b = randint(0, max)
        return (idx_a, idx_b)

    class SwapDecision:
        def __init__(self, idx_a, idx_b):
            self.idx_a = idx_a
            self.idx_b = idx_b

        def __call__(self, order: Order):
            f = order.order
            f[self.idx_a], f[self.idx_b] = f[self.idx_b], f[self.idx_a]


    def random_swap_decision(self, order):
        return self.SwapDecision(*self.gen_idx(len(order.order) - 1))

    def gen_order_decision(self, order: Order) -> Tuple[Order, SwapDecision]:
        for _ in range(self.neighbours_max):
            swap_decision = self.random_swap_decision(order)

            # apply swap on current order
            swap_decision(order)

            # yield order only for c_max evaulation
            # as it will change
            yield (order, swap_decision)

            # revert to original order
            swap_decision(order)


    class TabuList:
        def __init__(self, max_size):
            self.max_size = max_size
            self.tabu_history = deque()
            self.tabu_set = set()

        def __contains__(self, obj):
            #return obj in self.tabu_set
            return obj in self.tabu_set

        def add(self, obj):
            assert obj not in self

            if len(self.tabu_history) >= self.max_size:
                self.tabu_set.remove(self.tabu_history[0])
                self.tabu_history.popleft()

            self.tabu_history.append(obj)
            self.tabu_set.add(obj)


    def resolve(self, grouped_tasks: GroupedTasks) -> Order:
        current = self.first_order
        current = NpOrder(np.array(current.order))
        best = NpOrder(np.copy(current.order))
        best_c_max = get_c_max(grouped_tasks, best)

        tabu_list = self.TabuList(1000)
        stop_time = time() + .5 * 60

        iteration = 0

        while time() < stop_time:
            iteration += 1

            order_decisions = ((order, swap_decision) for order, swap_decision in self.gen_order_decision(current)
                if order not in tabu_list)

            # order is dynamically changed current
            _, decision = min(order_decisions, default=(None, None), key=lambda order_and_decision: get_c_max(grouped_tasks, order_and_decision[0]))

            if decision is None:
                continue

            # generate min order in current
            decision(current)


            # add to tabu list
            not_writeable_copy = np.copy(current.order)
            not_writeable_copy.flags.writeable = False
            tabu_list.add(NpOrder(not_writeable_copy))

            current_c_max = get_c_max(grouped_tasks, current)
            if current_c_max < best_c_max:
                best_c_max = current_c_max
                best = NpOrder(np.copy(current.order))

        print(f'Tabu list iterations: {iteration}')

        return best
