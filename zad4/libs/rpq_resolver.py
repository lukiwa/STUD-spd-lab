from .order import Order
from .rpq_task import RPQTask
import numpy as np
import heapq

class RPQResolver:
    def resolve(self, N: list) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")
    def pmtn_resolve(self, N: list) -> Order:
        raise RuntimeError("Resolver::resolve(...): method not implemented")


class SchrageN2Resolver(RPQResolver):
    def resolve(self, N: list) -> Order:
        ready_task = RPQTask(0,0,0,0)

        t = min(N, key=lambda task: task.R).R
        G = []

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

    def pmtn_resolve(self, N: list) -> Order:
        ready_task = RPQTask(0,0,0,0)
        task_on_machine = RPQTask(0,0,0, np.iinfo(np.uint16).max)

        t = 0
        G = []

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
