from collections import defaultdict
import datetime
import csv


from libs.rpq_task import RPQTask
from libs.load_file import rpq_load_file
from libs.rpq_resolver import SchrageN2Resolver, SchrageLogNResolver, CarlierResolver
from libs.priority_queue import PriorityQueue
from libs.helpers import RPQtime_resolve, create_random_rpq_task_queue, get_c_max_rpq

# from libs.gantt_plot import GanttPlot


def main():

    tasks = [
        #rpq_load_file('in50.txt'),
        #rpq_load_file('in100.txt'),
        #rpq_load_file('in200.txt')
        rpq_load_file('data.001'),
        rpq_load_file('data.002'),
        rpq_load_file('data.003')
        #rpq_load_file('data.004')
    ]
    #+ [rpq_load_file(f'data.00{i}') for i in range(5, 9)]

    resolvers_factory = [
        #lambda: SchrageLogNResolver().resolve,
        #lambda: SchrageLogNResolver().pmtn_resolve
        lambda: CarlierResolver().resolve
        ]

    global_result = defaultdict(lambda: dict())

    for task in tasks:
        task_t = tuple(task)
        for resolver in resolvers_factory:
            from copy import deepcopy
            [[order, cmax], time] = RPQtime_resolve(resolver(), task_t)
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

    '''
    filenames = ['test.txt', 'in50.txt', 'in100.txt', 'in200.txt']
    resolvers = [SchrageN2Resolver().resolve, SchrageN2Resolver().pmtn_resolve,
                 SchrageLogNResolver().resolve, SchrageLogNResolver().pmtn_resolve]

    global_result = defaultdict(lambda: dict())

    for filename in filenames:
        for resolver in resolvers:
            tasks = rpq_load_file(filename)
            [[order, cmax], time] = RPQtime_resolve(resolver, tasks)
            global_result[resolver][filename] = (cmax, time)
            print(f'Done: {filename}--{resolver}')
            print("Time: " + str(time))
            print("Cmax: " + str(cmax) + "\n")

    with open('output.csv', 'w', newline='') as output:
        writer = csv.writer(output, delimiter=';')

        for resolver, filename_to_results in global_result.items():
            writer.writerow(('zadania', 'c_max', 'czas'))
            writer.writerow((resolver, ))
            for filename, result_and_time in filename_to_results.items():
                result, time = result_and_time
                writer.writerow((filename, result, str(time)))
            writer.writerow(())
    '''

if __name__ == '__main__':
    main()
