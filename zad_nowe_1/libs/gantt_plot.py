import plotly.express as px
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
from dataclasses import dataclass
from typing import Tuple
import random

from .grouped_tasks import GroupedTasks
from .order import Order


class GanttPlot:

    def InsertTaskGroup(self, grouped_tasks: GroupedTasks):
        self.__groupTasks = grouped_tasks.matrix
        self.__numberOfMachines = grouped_tasks.machines_no()
        self.__numberOfTasks = grouped_tasks.tasks_no()

    def InsertOrder(self, task_order: Order):
        self.__order = task_order.order

    def Show(self, chart_title):
        df = pd.DataFrame()
        finished = dict()
        def r(): return random.randint(10, 255)
        # color of each task
        colors = ['#%02X%02X%02X' % (r(), r(), r())]

        start = 0
        finish = 0
        # first (0) machine order. Add end time of each task to the finished dict
        for i in self.__order:
            start = finish
            finish = finish+self.__groupTasks[i, 0]
            finished[i] = finish
            df = df.append(dict(Task=0, Start=start, Finish=finish,
                                Color=str(i)), ignore_index=True)
            colors.append('#%02X%02X%02X' % (r(), r(), r()))

        # for each machine (but the 0) go through order list and calculate duration based on duration of the first machine
        for machine in range(1, self.__numberOfMachines):
            finish = 0
            start = 0
            for i in self.__order:

                # if task on this machine would end later than on the 0 machine, adjust end time to avoid task overlaping
                if finished[i] < finish:
                    start = finish
                else:
                    start = finished[i]

                df = df.append(dict(
                    Task=machine, Start=start, Finish=start+self.__groupTasks[i, machine], Color=str(i)), ignore_index=True)
                finish = start+self.__groupTasks[i, machine]
                # let know next machine that this task finished at this time
                finished[i] = finish
                colors.append('#%02X%02X%02X' % (r(), r(), r()))

        fig = ff.create_gantt(
            df, index_col='Color', colors=colors, show_colorbar=True, group_tasks=True, showgrid_x=True, title=chart_title)

        # lower the hoverdistance if you would the chart not to display(or make trigger area lower) the ending time of
        #  each task on hover (but the task number itself)
        fig.update_layout(xaxis_type='linear',
                          legend_title="Task no.", hoverdistance=5)
        fig.update_xaxes(title="Time[s]")
        fig.update_yaxes(title="Machine no.")
        fig.show()
