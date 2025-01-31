from abc import abstractmethod
from Memory import Memory
from Job import Job


class Scheduler:
    """
    Base Scheduler class.
    Manages a queue/list of waiting jobs and picks which job runs next.
    """
    def __init__(self, env, memory):
        self.env = env
        self.memory : Memory = memory
        self.run_queue = []

    def add_job(self, job : Job):
        self.run_queue.append(job)

    def remove_job(self, job : Job):
        if job in self.run_queue:
            self.run_queue.remove(job)
        else:
            raise ValueError("Job not in run queue.")

    @abstractmethod
    def step(self):
        raise NotImplementedError("Subclasses should implement step()")

    def __str__(self):
        return "Scheduler"