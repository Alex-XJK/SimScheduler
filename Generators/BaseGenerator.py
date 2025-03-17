import random
import logging
from abc import abstractmethod

from Schedulers.GlobalScheduler import GlobalScheduler


class Generator:
    """
    Creates new Jobs.
    - speed: jobs to generate per step (can be fractional).
      E.g., speed=0.5 means on average 1 job every 2 steps.
    - total: total number of jobs to generate (stop after X).
    - dropout: probability to drop a job (simulate uncertain server load).
    - name: name of the generator (for debugging).
    """

    def __init__(self, env, scheduler: GlobalScheduler, speed: float, total: int, dropout: float = 0.0, name: str = "Base Generator"):
        self.env = env
        self.name = name
        self.scheduler = scheduler
        self.speed = speed  # This value may be fractional.
        self.total_limit = total
        self.dropout = dropout

        self.job_id = 1
        self.generated_count = 0

        # Accumulator for fractional job generation.
        self._acc = 0.0


    def generate_jobs(self) -> int:
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

            # Let the concrete generator try to add a job
            is_add_success = self.try_add_one_job()

            if is_add_success:
                self.generated_count += 1
                tmp_cnt += 1
                self.job_id += 1

        if tmp_cnt > 0:
            logging.debug(f"Generator >> Generated {tmp_cnt} jobs this step.")
        return tmp_cnt

    @abstractmethod
    def try_add_one_job(self) -> bool:
        """
        Try to create and add one job to the scheduler.
        Return True if successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @property
    def is_finished(self):
        return self.generated_count >= self.total_limit

    def __str__(self):
        string = f"{self.name}: "
        if self.speed < 1:
            period = round(1 / self.speed, 2)
            string += f"~1 job per {period} steps, "
        else:
            string += f"{self.speed} jobs per step, "
        string += f"{self.dropout:.2f} dropout, "
        string += f"{self.generated_count}/{self.total_limit} jobs generated."
        return string

