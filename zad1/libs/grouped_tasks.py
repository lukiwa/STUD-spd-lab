from dataclasses import dataclass
import numpy as np

@dataclass
class GroupedTasks:
    matrix: np.ndarray

    def machines_no(self):
        return self.matrix.shape[1]

    def tasks_no(self):
        return self.matrix.shape[0]
