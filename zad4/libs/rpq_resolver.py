from .order import Order
from .rpq_task import RPQTask
import numpy as np
from typing import Iterable, Tuple
from .priority_queue import PriorityQueue

class RPQResolver:
    def resolve(self, queue: Iterable) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")
    def pmtn_resolve(self, queue: Iterable) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")


class SchrageN2Resolver(RPQResolver):
    def resolve(self, queue: list) -> Order:
        G = []
        N = queue

        ready_task = RPQTask(0,0,0,0)
        t = min(N, key=lambda task: task.R).R

        order = []
        cmax = 0

        while len(G) != 0 or len(N) != 0:
            
            while len(N) != 0 and min(N, key=lambda task: task.R).R <= t:
                ready_task = min(N, key=lambda task: task.R) 

                G.append(ready_task)
                N.remove(ready_task)
            
            if len(G) == 0:
                t = min(N, key=lambda task: task.R).R
            else:
                ready_task = max(G, key=lambda task: task.Q)
                G.remove(ready_task)
                order.append(ready_task.task_no)
                t += ready_task.P
                
            cmax = max(cmax, t + ready_task.Q)
            

        return [Order(order), cmax]

    def pmtn_resolve(self, queue: list) -> Order:
        ready_task = RPQTask(0,0,0,0)
        task_on_machine = RPQTask(0,0,0, np.iinfo(np.uint16).max)

        t = 0
        G = []
        N = queue

        order = []
        cmax = 0

        while len(G) != 0 or len(N) != 0:
            
            while len(N) != 0 and min(N, key=lambda task: task.R).R <= t:
                ready_task = min(N, key=lambda task: task.R) 

                G.append(ready_task)
                N.remove(ready_task)

                if ready_task.Q > task_on_machine.Q:
                    task_on_machine.P = t - ready_task.R
                    t = ready_task.R
                    if task_on_machine.P > 0:
                        G.append(task_on_machine)
            
            if len(G) == 0:
                t = min(N, key=lambda task: task.R).R
            else:
                ready_task = max(G, key=lambda task: task.Q)
                G.remove(ready_task)
                task_on_machine = ready_task
                order.append(ready_task.task_no)
                t += ready_task.P
                
            cmax = max(cmax, t + ready_task.Q)
            

        return [Order(order), cmax]

class SchrageLogNResolver(RPQResolver):
    def resolve(self, queue: list) -> Order:
        G = PriorityQueue(compare = lambda task1, task2:  task1.Q >= task2.Q )
        
        N = PriorityQueue(compare = lambda task1, task2:  task1.R <= task2.R )
        for task in queue:
            N.push(task)

        ready_task = RPQTask(0,0,0,0)
        t = N.peek().R

        order = []
        cmax = 0

        while G.len() != 0 or N.len() != 0:
            
            while N.len() != 0 and N.peek().R <= t:
                ready_task = N.pop()
                G.push(ready_task)
            
            if G.len() == 0:
                t = N.peek().R
            else:
                ready_task = G.pop()
                order.append(ready_task.task_no)
                t += ready_task.P
                
            cmax = max(cmax, t + ready_task.Q)
            

        return [Order(order), cmax]

    def pmtn_resolve(self, queue: list) -> Order:
        ready_task = RPQTask(0,0,0,0)
        task_on_machine = RPQTask(0,0,0, np.iinfo(np.uint16).max)

        t = 0

        G = PriorityQueue(compare = lambda task1, task2:  task1.Q >= task2.Q )
        N = PriorityQueue(compare = lambda task1, task2:  task1.R <= task2.R )
        for task in queue:
            N.push(task)

        order = []
        cmax = 0

        while G.len() != 0 or N.len() != 0:
            
            while N.len() != 0 and N.peek().R <= t:
                ready_task = N.pop()
                G.push(ready_task)
                

                if ready_task.Q > task_on_machine.Q:
                    task_on_machine.P = t - ready_task.R
                    t = ready_task.R
                    if task_on_machine.P > 0:
                        G.push(task_on_machine)
            
            if G.len() == 0:
                t = N.peek().R
            else:
                ready_task = G.pop()
                task_on_machine = ready_task
                order.append(ready_task.task_no)
                t += ready_task.P
                
            cmax = max(cmax, t + ready_task.Q)
        
        return [Order(order), cmax]
    