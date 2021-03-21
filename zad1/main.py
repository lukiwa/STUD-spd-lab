import numpy as np
from numpy.lib.npyio import load

from libs.resolver import BruteForceResolver, JohnsonResolver
from libs.grouped_tasks import GroupedTasks
from libs.order import Order
from libs.load_file import load_file
from libs.helpers import get_c_max
from libs.gantt_plot import GanttPlot 

def main():
    plot = GanttPlot()
    task = GroupedTasks(np.matrix([
        [1, 3, 8],
        [9, 3, 5],
        [7, 8, 6],
        [4, 8, 7]
    ]))
    plot.InsertTaskGroup(task)

    order_brute = BruteForceResolver().resolve(task)
    assert order_brute.order == (0, 3, 2, 1)
    plot.InsertOrder(order_brute)
    plot.Show("Brute")

    order_johnson = JohnsonResolver().resolve(task)
    assert order_johnson.order == (0, 3, 2, 1)
    plot.InsertOrder(order_johnson)
    plot.Show("Johnson")

if __name__ == '__main__':
    main()
