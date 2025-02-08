import simpy
from Scheduler import Scheduler
from Job import Job


class SRPT(Scheduler):
    """
    Shortest Remaining Processing Time (SRPT) Scheduler.
    """
    def __init__(self, env, memory, batch):
        super().__init__(env, memory, batch,"SRPT")

    def pick_next_task(self) -> list[Job]:
        sorted_jobs = sorted(self.run_queue, key=lambda job: (job.final_size - job.current_size))
        return sorted_jobs[:self.batch]