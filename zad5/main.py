from collections import defaultdict
import datetime
import csv


from libs.rpq_task import RPQTask
from libs.load_file import load_file, rpq_load_file
from libs.rpq_resolver import CarlierStrategy, SchrageN2Resolver, SchrageLogNResolver, CarlierResolver
from libs.priority_queue import PriorityQueue
from libs.helpers import RPQtime_resolve, create_random_rpq_task_queue, get_c_max_rpq

# from libs.gantt_plot import GanttPlot


def main():
    '''
    tasks = []
    for i in range(10, 1000):
        tasks.append(create_random_rpq_task_queue(i, 2, 2000))
    '''

    '''
    tasks = [rpq_load_file('data.008')]
    '''
    filenames = [f'data.00{i}' for i in range(0, 9)]

    resolvers_factory = [
        #CarlierResolver(CarlierStrategy.BFS, SchrageN2Resolver),
        CarlierResolver(CarlierStrategy.BFS, SchrageLogNResolver),
        #CarlierResolver(CarlierStrategy.Normal, SchrageN2Resolver),
        #CarlierResolver(CarlierStrategy.Normal, SchrageLogNResolver)
        ]

    global_result = defaultdict(lambda: dict())

    for filename in filenames:
        #task_t = tuple(task)
        task_t = tuple(rpq_load_file(filename))
        for resolver in resolvers_factory:
            [[order, cmax], time] = RPQtime_resolve(resolver, [*task_t])
            global_result[resolver][filename] = (cmax, time)
            print(f'Done: {filename}--{resolver}')
            print("Time: " + str(time))
            print("Cmax: " + str(cmax) + ", other cmax: " + str(get_c_max_rpq(task_t, order)))
            print("Result: " + str(order))
            print()


    with open('output.csv', 'w', newline='') as output:
        writer = csv.writer(output, delimiter=';')

        for resolver, tasks_to_results in global_result.items():
            writer.writerow(('nazwa', 'czas', 'cmax'))
            writer.writerow((resolver, ))
            for task, result_and_time in tasks_to_results.items():
                cmax, time = result_and_time
                writer.writerow((task, str(time), cmax))
            writer.writerow(())

if __name__ == '__main__':
    main()
