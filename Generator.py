import simpy
import random
import Job

class Generator:
    """
    Creates new Jobs.
    - S: how many jobs to generate per step (i.e. 'per second').
    - X: total number of jobs to generate (stop after X).
    - L: average initial size (P).
    - M_fn: a function or distribution to pick final size M (or a fixed value).
    """

    def __init__(self, env, scheduler, S, X, L, M_fn):
        self.env = env
        self.scheduler = scheduler
        self.S = S
        self.X = X
        self.L = L
        self.M_fn = M_fn
        self.job_id = 0
        self.generated_count = 0

    def generate_jobs(self):
        """
        Called once per step by the System.
        Generate up to S new jobs in one second.
        """
        for _ in range(self.S):
            if self.generated_count >= self.X:
                break

            self.job_id += 1
            arrival_time = self.env.now

            P = max(1, int(random.gauss(self.L, 5)))
            M = self.M_fn()

            job = Job.Job(job_id=self.job_id, arrival_time=arrival_time, P=P, M=M)
            self.scheduler.add_job(job)
            self.generated_count += 1


    def __str__(self):
        return f"Generator: {self.S} jobs/sec, {self.generate_jobs()}/{self.X} jobs generated, {self.L} avg size"