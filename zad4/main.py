from collections import defaultdict
import datetime, csv
import heapq

from libs.load_file import rpq_load_file
from libs.rpq_resolver import SchrageN2Resolver

#from libs.gantt_plot import GanttPlot

def main():
    queue = rpq_load_file('in100.txt')
    resolver = SchrageN2Resolver()
    order, cmax = resolver.pmtn_resolve(queue)
    print(cmax)
    #for i in order.order:
        #print(i + 1)

if __name__ == '__main__':
    main()
