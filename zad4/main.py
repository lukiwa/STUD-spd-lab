from collections import defaultdict
import datetime
import csv


from libs.rpq_task import RPQTask
from libs.load_file import rpq_load_file
from libs.rpq_resolver import SchrageN2Resolver, SchrageLogNResolver
from libs.priority_queue import PriorityQueue
from libs.helpers import RPQtime_resolve, create_random_rpq_task_queue

# from libs.gantt_plot import GanttPlot


def main():
    
    tasks = []
    for i in range(10, 500):
        tasks.append(create_random_rpq_task_queue(i, 2, 2000))

    resolvers = [SchrageN2Resolver().resolve, SchrageN2Resolver().pmtn_resolve,
                 SchrageLogNResolver().resolve, SchrageLogNResolver().pmtn_resolve]    

    global_result = defaultdict(lambda: dict())

    for task in tasks:
        for resolver in resolvers:
            [[order, cmax], time] = RPQtime_resolve(resolver, task.copy())
            global_result[resolver][len(task)] = (cmax, time)
            print(f'Done: {len(task)}--{resolver}')
            print("Time: " + str(time))
            print("Cmax: " + str(cmax) + "\n")

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
