from itertools import count

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
        self._slow_mode = False
        if speed < 1:
            self._slow_mode = True
            self.speed = -speed
        self.total_limit = total
        self.avg_init_size = init_size
        self.final_size_fn = final_fn
        self.job_id = 1
        self.generated_count = 0
        self._slow_mode_acc = self.speed


    def generate_jobs(self):
        """
        Called once per step by the System.
        Generate up to S new jobs in one second.
        """
        tmp_cnt = 0

        num_jobs_this_step = self.speed  # Generate `Speed` jobs per step

        # Slow Mode: Generate 1 job per `speed` steps
        if self._slow_mode:
            if self._slow_mode_acc < self.speed:
                self._slow_mode_acc += 1
                return 0
            else:
                self._slow_mode_acc = 0
            num_jobs_this_step = 1  # Generate 1 job per step

        for _ in range(num_jobs_this_step):
            if self.is_finished:
                break

            arrival_time = self.env.now

            P = max(1, int(random.gauss(self.avg_init_size, 5)))
            M = self.final_size_fn()

            job = Job(job_id=self.job_id, arrival_time=arrival_time, init_size=P, expected_output=M)
            if self.scheduler.add_job(job):
                self.generated_count += 1
                tmp_cnt += 1
                self.job_id += 1

        if tmp_cnt > 0:
            logging.debug(f"Generator Status >> Generated {tmp_cnt} jobs this step.")
        return tmp_cnt

    @property
    def is_finished(self):
        return self.generated_count >= self.total_limit

    def __str__(self):
        if self._slow_mode:
            return f"Generator: 1 job per {self.speed} steps, {self.generated_count}/{self.total_limit} jobs generated, {self.avg_init_size} avg size"
        return f"Generator: {self.speed} jobs per step, {self.generated_count}/{self.total_limit} jobs generated, {self.avg_init_size} avg size"