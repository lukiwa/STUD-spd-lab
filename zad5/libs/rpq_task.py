from dataclasses import dataclass
import numpy as np


@dataclass
class RPQTask:
    task_no: np.uint16
    R: np.uint16  
    P: np.uint16  
    Q: np.uint16  

    def __init__(self, task_no, R, P, Q):
        self.task_no = task_no
        self.R = R
        self.P = P
        self.Q = Q

    def __lt__(self, other):
        return self.task_no < other.task_no