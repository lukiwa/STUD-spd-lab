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
    def __repr__(self) -> str:
        return 'JohnsonResolver'

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
    def __repr__(self):
        return 'NehResolver'

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


class DecisionGenerator:
    class Decision:
        def apply(self, order: Order):
            raise NotImplementedError()

        def revert(self, order: Order):
            raise NotImplementedError()

    def random_decision(self, order: Order):
        raise NotImplementedError()


class SwapDecisionGenerator(DecisionGenerator):
    class SwapDecision(DecisionGenerator.Decision):
        def __init__(self, idx_a, idx_b):
            self.idx_a = idx_a
            self.idx_b = idx_b

        def apply(self, order: Order):
            f = order.order
            f[self.idx_a], f[self.idx_b] = f[self.idx_b], f[self.idx_a]

        def revert(self, order: Order):
            self.apply(order)

    def random_decision(self, order: Order):
        return self.SwapDecision(*self._gen_idx(len(order.order) - 1))

    def _gen_idx(self, max):
        idx_a = randint(0, max)
        idx_b = randint(0, max)
        while idx_a == idx_b:
            idx_b = randint(0, max)
        return (idx_a, idx_b)

    def __repr__(self):
        return 'SwapDecision'


class InsertDecisionGenerator(DecisionGenerator):
    class InsertDecision(DecisionGenerator.Decision):
        def __init__(self, idx_from, idx_to):
            self.idx_from = idx_from
            self.idx_to = idx_to

        def apply(self, order: Order):
            f = order.order
            f[self.idx_from:self.idx_to] = np.roll(f[self.idx_from:self.idx_to], -1)

        def revert(self, order: Order):
            f = order.order
            f[self.idx_from:self.idx_to] = np.roll(f[self.idx_from:self.idx_to], 1)

    def random_decision(self, order: Order):
        return self.InsertDecision(*self._gen_idx(len(order.order) - 1))

    def _gen_idx(self, max):
        idx_a = randint(0, max)
        idx_b = randint(0, max)
        while idx_a == idx_b:
            idx_b = randint(0, max)
        return (idx_a, idx_b)

    def __repr__(self):
        return 'InsertDecision'

class StopOption:
    def should_stop(self) -> bool:
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def next_iter(self):
        raise NotImplementedError()

class TimeStopOption(StopOption):
    def __init__(self, duration):
        self.duration = duration

    def start(self):
        self.start_time = time()

    def should_stop(self) -> bool:
        return time() > self.start_time + self.duration

    def next_iter(self):
        pass

    def __repr__(self):
        return f'TimeStop({self.duration})'

class IterNoStopOption(StopOption):
    def __init__(self, max_iter):
        self.max_iter = max_iter

    def start(self):
        self.iter = 0

    def should_stop(self):
        return self.iter >= self.max_iter

    def next_iter(self):
        self.iter += 1

    def __repr__(self):
        return f'IterNoStop({self.max_iter})'


class TsResolver(Resolver):
    def __init__(self,
            neighbours_max=10,
            first_order: Resolver=JohnsonResolver(),
            decision_generator: DecisionGenerator=SwapDecisionGenerator(),
            tabu_list_length=10,
            stop_option: StopOption=TimeStopOption(60)):
        self.neighbours_max = neighbours_max
        self.first_order = first_order
        self.stop_option = stop_option
        self.decision_generator = decision_generator
        self.tabu_list_length = tabu_list_length

    def __repr__(self):
        return f'TsResolver:neighbours={self.neighbours_max}:first_order={self.first_order}:{self.decision_generator}:tabu_list_length={self.tabu_list_length}:stop_option={self.stop_option}'

    def gen_order_decision(self, order: Order) -> Tuple[Order, DecisionGenerator.Decision]:
        for _ in range(self.neighbours_max):
            decision = self.decision_generator.random_decision(order)

            # apply decision on current order
            decision.apply(order)

            # yield order only for c_max evaulation
            # as it will change
            yield (order, decision)

            # revert to original order
            decision.revert(order)

    class TabuList:
        def __init__(self, max_size):
            self.max_size = max_size
            self.tabu_history = deque()
            self.tabu_set = set()

        def __contains__(self, obj):
            return obj in self.tabu_set

        def add(self, obj):
            if len(self.tabu_history) >= self.max_size:
                self.tabu_set.remove(self.tabu_history[0])
                self.tabu_history.popleft()

            self.tabu_history.append(obj)
            self.tabu_set.add(obj)

    def resolve(self, grouped_tasks: GroupedTasks) -> Order:
        current = self.first_order.resolve(grouped_tasks)
        current = NpOrder(np.array(current.order))
        best = NpOrder(np.copy(current.order))
        best_c_max = get_c_max(grouped_tasks, best)

        tabu_list = self.TabuList(self.tabu_list_length)
        self.stop_option.start()

        while not self.stop_option.should_stop():
            order_decisions = ((order, swap_decision) for order, swap_decision in self.gen_order_decision(current) if order not in tabu_list)

            # order is dynamically changed current
            _, decision = min(order_decisions, default=(None, None), key=lambda order_and_decision: get_c_max(grouped_tasks, order_and_decision[0]))

            if decision is None:
                continue

            # generate min order in current
            decision.apply(current)

            # add to tabu list
            not_writeable_copy = np.copy(current.order)
            not_writeable_copy.flags.writeable = False
            tabu_list.add(NpOrder(not_writeable_copy))

            current_c_max = get_c_max(grouped_tasks, current)
            if current_c_max < best_c_max:
                best_c_max = current_c_max
                best = NpOrder(np.copy(current.order))

            self.stop_option.next_iter()

        return best
