from collections import defaultdict
import datetime
import csv


from libs.rpq_task import RPQTask
from libs.load_file import rpq_load_file
from libs.rpq_resolver import SchrageN2Resolver, SchrageLogNResolver
from libs.priority_queue import PriorityQueue
from libs.helpers import RPQtime_resolve

# from libs.gantt_plot import GanttPlot


def main():
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


if __name__ == '__main__':
    main()
