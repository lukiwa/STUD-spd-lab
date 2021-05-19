from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class RPQTask:
    task_no: int
    R: int
    P: int
    Q: int

    def __lt__(self, other):
        return self.task_no < other.task_no
