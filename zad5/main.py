from collections import defaultdict
import datetime
import csv


from libs.rpq_task import RPQTask
from libs.load_file import rpq_load_file
from libs.rpq_resolver import CarlierStrategy, SchrageN2Resolver, SchrageLogNResolver, CarlierResolver
from libs.priority_queue import PriorityQueue
from libs.helpers import RPQtime_resolve, create_random_rpq_task_queue, get_c_max_rpq

# from libs.gantt_plot import GanttPlot


def main():

    tasks = [
        rpq_load_file('in50.txt'),
        rpq_load_file('in100.txt'),
        rpq_load_file('in200.txt'),
        #rpq_load_file('data.000'),
        #rpq_load_file('data.txt'),
        rpq_load_file('data.003'),
        rpq_load_file('data.004'),
        #rpq_load_file('data.007')
        #rpq_load_file('przyklad.txt')
    ] #+ [rpq_load_file(f'data.00{i}') for i in range(5, 9) if i != 6]

    resolvers_factory = [
        #lambda: SchrageLogNResolver().resolve,
        #lambda: SchrageLogNResolver().pmtn_resolve
        lambda: CarlierResolver(CarlierStrategy.Normal, SchrageLogNResolver).resolve,
        lambda: CarlierResolver(CarlierStrategy.BFS, SchrageLogNResolver).resolve
        #lambda: SchrageN2Resolver().resolve,
        #lambda: SchrageN2Resolver().pmtn_resolve
        ]

    global_result = defaultdict(lambda: dict())

    for task in tasks:
        task_t = tuple(task)
        for resolver in resolvers_factory:
            [[order, cmax], time] = RPQtime_resolve(resolver(), [*task_t])
            global_result[resolver][len(task)] = (cmax, time)
            print(f'Done: {len(task)}--{resolver}')
            print("Time: " + str(time))
            print("Cmax: " + str(cmax) + ", other cmax: " + str(get_c_max_rpq(task, order)))
            print("Result: " + str(order))
            print()

    with open('output2.csv', 'w', newline='') as output:
        writer = csv.writer(output, delimiter=';')

        for resolver, tasks_to_results in global_result.items():
            writer.writerow(('ilosc_zadan', 'czas'))
            writer.writerow((resolver, ))
            for task, result_and_time in tasks_to_results.items():
                _, time = result_and_time
                writer.writerow((task, str(time)))
            writer.writerow(())

if __name__ == '__main__':
    main()
