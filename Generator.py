import simpy
import random
import logging
from Job import Job

class Generator:
    """
    Creates new Jobs.
    - S: how many jobs to generate per step (i.e. 'per second').
    - X: total number of jobs to generate (stop after X).
    - L: average initial size (P).
    - M_fn: a function or distribution to pick final size M (or a fixed value).
    """

    def __init__(self, env, scheduler, speed, total, init_size, final_fn):
        self.env = env
        self.scheduler = scheduler
        self.speed = speed
        self.total_limit = total
        self.avg_init_size = init_size
        self.final_size_fn = final_fn
        self.job_id = 0
        self.generated_count = 0

    def generate_jobs(self):
        """
        Called once per step by the System.
        Generate up to S new jobs in one second.
        """
        tmp_cnt = 0
        for _ in range(self.speed):
            if self.is_finished:
                break

            self.job_id += 1
            arrival_time = self.env.now

            P = max(1, int(random.gauss(self.avg_init_size, 5)))
            M = self.final_size_fn()

            job = Job(job_id=self.job_id, arrival_time=arrival_time, init_size=P, expected_output=M)
            if self.scheduler.add_job(job):
                self.generated_count += 1
                tmp_cnt += 1

        if tmp_cnt > 0:
            logging.debug(f"Generator Status >> Generated {tmp_cnt} jobs this step.")
        return tmp_cnt

    @property
    def is_finished(self):
        return self.generated_count >= self.total_limit

    def __str__(self):
        return f"Generator: {self.speed} jobs/sec, {self.generated_count}/{self.total_limit} jobs generated, {self.avg_init_size} avg size"