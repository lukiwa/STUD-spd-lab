import numpy as np
from numpy.lib.npyio import load

from libs.resolver import BruteForceResolver, JohnsonResolver
from libs.grouped_tasks import GroupedTasks
from libs.order import Order
from libs.load_file import load_file
from libs.helpers import get_c_max

def main():
    task = GroupedTasks(np.matrix([
        [1, 3, 8],
        [9, 3, 5],
        [7, 8, 6],
        [4, 8, 7]
    ]))

    order_brute = BruteForceResolver().resolve(task)
    assert order_brute.order == (0, 3, 2, 1)

    order_johnson = JohnsonResolver().resolve(task)
    assert order_johnson.order == (0, 3, 2, 1)

if __name__ == '__main__':
    main()
