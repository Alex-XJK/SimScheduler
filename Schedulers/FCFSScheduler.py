import simpy
from Scheduler import Scheduler

class FCFSScheduler(Scheduler):
    """
    A First-Come-First-Serve Scheduler.
    """
    def __init__(self, env, memory):
        super().__init__(env, memory, "FCFS")

    def introduction(self):
        return "First-Come-First-Serve Scheduler"

    def pick_next_task(self):
        # Every time, pick the first job in the queue
        return self.run_queue[0]