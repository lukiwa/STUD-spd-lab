from collections import defaultdict
import datetime, csv

from libs.helpers import get_c_max, create_random_grouped_task, time_resolve
from libs.load_file import load_file
from libs.resolver import InsertDecisionGenerator, IterNoStopOption, NehResolver, BruteForceResolver, JohnsonResolver, SwapDecisionGenerator, TimeStopOption, TsResolver

#from libs.gantt_plot import GanttPlot

def main():
    filenames = ['data78.txt', 'data79.txt', 'data80.txt']
    resolvers = [JohnsonResolver(), NehResolver()]

    for neighbours_max in [10, 100]:
        for first_order in [JohnsonResolver(), NehResolver()]:
            for decision_generator in [SwapDecisionGenerator(), InsertDecisionGenerator()]:
                for tabu_list_length in [10, 100]:
                    for stop_option in [TimeStopOption(10), IterNoStopOption(150)]:
                        resolvers.append(TsResolver(neighbours_max, first_order, decision_generator, tabu_list_length, stop_option))


    global_result = defaultdict(lambda: dict())
    filename_to_tasks = {}

    for filename in filenames:
        grouped_tasks = load_file(filename)
        filename_to_tasks[filename] = grouped_tasks
        for resolver in resolvers:
            result, time = time_resolve(resolver, grouped_tasks)
            global_result[resolver][filename] = (result, time)

            print (f'Done: {filename}--{resolver}')

    with open('output.csv', 'w', newline='') as output:
        writer = csv.writer(output)

        for resolver, filename_to_results in global_result.items():
            writer.writerow(('zadania', 'c_max', 'czas'))
            writer.writerow((resolver,))
            for filename, result_and_time in filename_to_results.items():
                result, time = result_and_time
                writer.writerow((filename, get_c_max(filename_to_tasks[filename], result), str(time)))
            writer.writerow(())



if __name__ == '__main__':
    main()
