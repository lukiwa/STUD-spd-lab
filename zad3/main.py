import datetime

from libs.helpers import get_c_max, create_random_grouped_task
from libs.load_file import load_file
from libs.resolver import NehResolver, BruteForceResolver, JohnsonResolver, TsResolver

#from libs.gantt_plot import GanttPlot

def main():
    #plot = GanttPlot()
    task = load_file("data102.txt")

    #plot.InsertTaskGroup(task)

    start = datetime.datetime.now()
    print("START: " + str(start))
    #order_brute = BruteForceResolver().resolve(task)
    order_johnson = JohnsonResolver().resolve(task)
    #order_neh = NehResolver().resolve(task)
    order_tabu = TsResolver(10, order_johnson).resolve(task)
    end = datetime.datetime.now()
    delta = end - start

    #cmax_brute = get_c_max(task, order_brute)
    cmax_johnson = get_c_max(task, order_johnson)
    #cmax_neh = get_c_max(task, order_neh)
    cmax_tabu = get_c_max(task, order_tabu)

    #print("BRUTE: " + str(cmax_brute))
    print("JOHNSON: " + str(cmax_johnson))
    #print("NEH: " + str(cmax_neh))
    print(f"TABU: {cmax_tabu}")
    print("ELAPSED: " + str(delta))


    #plot.InsertOrder(order_johnson)
    #plot.Show("Johnson")
    #plot.InsertOrder(order_brute)
    #plot.Show("Brute")
    #plot.InsertOrder(order_neh)

    #plot.Show("Neh")




if __name__ == '__main__':
    main()
