import simpy
import random
import logging

from Job import Job

class Generator:
    """
    Creates new Jobs.
    - speed: jobs to generate per step (can be fractional).
      E.g., speed=0.5 means on average 1 job every 2 steps.
    - total: total number of jobs to generate (stop after X).
    - init_fn: function to generate initial size of a job.
    - output_fn: function to generate expected output size of a job.
    - dropout: probability to drop a job (simulate uncertain server load).
    """

    def __init__(self, env, scheduler, speed, total, init_fn, output_fn, dropout=0.0):
        self.env = env
        self.scheduler = scheduler
        self.speed = speed  # This value may be fractional.
        self.total_limit = total
        self.init_size_fn = init_fn
        self.output_size_fn = output_fn
        self.dropout = dropout

        self.job_id = 1
        self.generated_count = 0

        # Accumulator for fractional job generation.
        self._acc = 0.0

        self.counter_init: list[int] = []
        self.counter_output: list[int] = []

    def generate_jobs(self):
        """
        Called once per step by the System.
        The function accumulates fractional jobs and generates one full job
        every time the accumulator reaches or exceeds 1.
        """
        tmp_cnt = 0

        # Accumulate the fractional jobs
        self._acc += self.speed

        # Determine how many whole jobs to generate this step
        num_jobs_this_step = int(self._acc)
        self._acc -= num_jobs_this_step

        for _ in range(num_jobs_this_step):
            if self.is_finished:
                break

            # Randomly drop jobs to simulate uncertain server loads
            if random.random() < self.dropout:
                continue

            arrival_time = self.env.now

            P = self.init_size_fn()
            M = self.output_size_fn()

            # Assuming Job is defined elsewhere
            job = Job(job_id=self.job_id, arrival_time=arrival_time, init_size=P, expected_output=M)
            if self.scheduler.add_job(job):
                self.generated_count += 1
                tmp_cnt += 1
                self.job_id += 1
                self.counter_init.append(P)
                self.counter_output.append(M)

        if tmp_cnt > 0:
            logging.debug(f"Generator Status >> Generated {tmp_cnt} jobs this step.")
        return tmp_cnt

    @property
    def is_finished(self):
        return self.generated_count >= self.total_limit

    def __str__(self):
        string = "Generator: "
        if self.speed < 1:
            period = round(1 / self.speed, 2)
            string += f"~1 job per {period} steps, "
        else:
            string += f"{self.speed} jobs per step, "
        string += f"{self.dropout:.2f} dropout, "
        string += f"{self.generated_count}/{self.total_limit} jobs generated. "
        if self.counter_init and self.counter_output:
            string += f"{min(self.counter_init)} ~ {max(self.counter_init)} initial size, "
            string += f"{min(self.counter_output)} ~ {max(self.counter_output)} output size"
        return string

