import simpy
from Scheduler import Scheduler
from Job import Job


class SRPT(Scheduler):
    """
    Shortest Remaining Processing Time (SRPT) Scheduler.
    """

    def __init__(self, env, memory):
        super().__init__(env, memory, "SRPT")

    def introduction(self):
        return "Shortest Remaining Processing Time (SRPT) Scheduler"

    def pick_next_task(self) -> Job:
        next_job = min(self.run_queue, key=lambda job: ((job.final_size - job.current_size), job.arrival_time))
        return next_job
