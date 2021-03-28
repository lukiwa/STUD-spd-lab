import numpy as np
import datetime
from numpy.lib.npyio import load

from libs.resolver import BruteForceResolver, JohnsonResolver, NehResolver
from libs.grouped_tasks import GroupedTasks
from libs.order import Order
from libs.load_file import load_file
from libs.helpers import get_c_max
from libs.helpers import create_random_grouped_task
from libs.helpers import task_processing_time_on_all_machines
from libs.helpers import get_sorted_task_order
from libs.helpers import insert_into_task_order


from libs.gantt_plot import GanttPlot 

def main():
    plot = GanttPlot()
    task = load_file("test_file.txt")
    #task = create_random_grouped_task(7, 6, 10, 50)
    plot.InsertTaskGroup(task)
   


    start = datetime.datetime.now()
    print("START: " + str(start))
    #order_brute = BruteForceResolver().resolve(task)
    #order_johnson = JohnsonResolver().resolve(task)
    order_neh = NehResolver().resolve(task)
    end = datetime.datetime.now()
    delta = end - start

    #cmax_brute = get_c_max(task, order_brute)
    #cmax_johnson = get_c_max(task, order_johnson)
    cmax_neh = get_c_max(task, order_neh)

    #print("BRUTE: " + str(cmax_brute))
    #print("JOHNSON: " + str(cmax_johnson))
    print("NEH: " + str(cmax_neh))
    print("ELAPSED: " + str(delta))
    
    
    #plot.InsertOrder(order_johnson)
    #plot.Show("Johnson")
    #plot.InsertOrder(order_brute)
    #plot.Show("Brute")
    plot.InsertOrder(order_neh)
    for i in order_neh.order:
        print(str(i+1), end=' ')

    plot.Show("Neh")




if __name__ == '__main__':
    main()
