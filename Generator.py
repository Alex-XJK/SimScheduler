import simpy
import logging
from Job import Job

class Generator:
    """
    Creates new Jobs.
    - speed: how many jobs to generate per step (i.e. 'per second').
    - total: total number of jobs to generate (stop after X).
    - init_fn: function to generate initial size of a job.
    - output_fn: function to generate expected output size of a job.
    """

    def __init__(self, env, scheduler, speed, total, init_fn, output_fn):
        self.env = env
        self.scheduler = scheduler
        self.speed = speed
        self._slow_mode = False
        if speed < 1:
            self._slow_mode = True
            self.speed = -speed
        self.total_limit = total
        self.init_size_fn = init_fn
        self.output_size_fn = output_fn
        self.job_id = 1
        self.generated_count = 0
        self._slow_mode_acc = self.speed

        self.counter_init : list[int]= []
        self.counter_output : list[int]= []


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

            P = self.init_size_fn()
            M = self.output_size_fn()

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
        if self._slow_mode:
            string += f"1 job per {self.speed} steps, "
        else:
            string += f"{self.speed} jobs per step, "
        string += f"{self.generated_count}/{self.total_limit} jobs generated. "
        string += f"{min(self.counter_init)} ~ {max(self.counter_init)} initial size, "
        string += f"{min(self.counter_output)} ~ {max(self.counter_output)} output size"
        return string