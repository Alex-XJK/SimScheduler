import simpy
from Scheduler import Scheduler

class RRScheduler(Scheduler):
    """
    A round-robin scheduler with a time slice.
    """
    def __init__(self, env, memory, time_slice=1):
        super().__init__(env, memory, "Round Robin")
        self.time_slice = time_slice

    def pick_next_task(self):
        # Each every time slice, we modify the run queue to dequeue the first job and enqueue it at the end.
        next_job = self.run_queue[0]
        if self.env.now % self.time_slice == 0:
            j = self.run_queue.pop(0)
            self.run_queue.append(j)
        return next_job