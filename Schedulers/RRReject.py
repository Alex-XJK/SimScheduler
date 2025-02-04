import simpy
import logging
from Scheduler import Scheduler

class RRRejectScheduler(Scheduler):
    """
    A round-robin scheduler with a time slice.
    But stop accepting new jobs when the memory is (near) full.
    """
    def __init__(self, env, memory, time_slice=1, threshold=1.0):
        super().__init__(env, memory, "RR-rej")
        self.time_slice = time_slice
        self.threshold = threshold

    def introduction(self):
        return "Round Robin, rejecting new jobs when memory is full."

    def add_job(self, job):
        # Check if we have enough memory to accept this new job
        if job.init_size <= self.memory.capacity * self.threshold - self._get_expected_memory():
            self.run_queue.append(job)
            return True
        else:
            logging.warning("Not enough memory to accept new job.")
            return False

    def pick_next_task(self):
        # Each every time slice, we modify the run queue to dequeue the first job and enqueue it at the end.
        next_job = self.run_queue[0]
        if self.env.now % self.time_slice == 0:
            j = self.run_queue.pop(0)
            self.run_queue.append(j)
        return next_job