import plotly.express as px
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
from dataclasses import dataclass
from typing import Tuple

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

        start = 0
        finish = 0
        for i in self.__order:
            start = finish
            finish = finish+self.__groupTasks[i, 0]
            finished[i] = finish
            df = df.append(dict(Task=0, Start=start, Finish=finish,
                                Color=str(i)), ignore_index=True)

        for machine in range(1, self.__numberOfMachines):
            finish = 0
            start = 0
            for i in self.__order:
                if finished[i] < finish:
                    start = finish
                else:
                    start = finished[i]

                df = df.append(dict(
                    Task=machine, Start=start, Finish=start+self.__groupTasks[i, machine], Color=str(i)), ignore_index=True)
                finish = start+self.__groupTasks[i, machine]
                finished[i] = finish

        fig = ff.create_gantt(
            df, index_col='Color', show_colorbar=True, group_tasks=True, showgrid_x=True, title=chart_title)
        fig.update_layout(xaxis_type='linear', xaxis_tick0='',
                          xaxis_dtick=1, legend_title="Task no.")
        fig.update_xaxes(title="Time[s]")
        fig.update_yaxes(title="Machine no.")
        fig.show()
