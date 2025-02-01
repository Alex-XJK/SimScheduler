import simpy
import logging
from abc import abstractmethod
from Memory import Memory
from Job import Job


class Scheduler:
    """
    Base Scheduler class.
    Manages a queue/list of waiting jobs and picks which job runs next.
    """
    def __init__(self, env, memory, name="Base Scheduler"):
        self.name = name
        self.env = env
        self.memory : Memory = memory
        self.run_queue = []
        self.finished_jobs = []

    def add_job(self, job : Job):
        self.run_queue.append(job)

    def remove_job(self, job : Job):
        if job in self.run_queue:
            self.run_queue.remove(job)
            self.finished_jobs.append(job)
        else:
            raise ValueError("Job not in run queue.")

    def step(self) -> Job | None:
        # Clean up finished jobs first:
        finished_jobs = [j for j in self.run_queue if j.is_finished]
        for job in finished_jobs:
            self.memory.release(job.current_size)
            self.remove_job(job)

        if not self.run_queue:
            logging.info("No jobs to run - Empty run queue.")
            return None

        # Template Method pattern
        next_job = self.pick_next_task()

        if next_job is None:
            logging.info("No jobs to run - Scheduler decision.")
            return None

        # First time running this job
        if next_job.current_size == 0:
            if self.memory.request(next_job.init_size):
                # Allocate memory for this new job
                next_job.current_size = next_job.init_size
                next_job.start_time = self.env.now
                logging.info(f"Job({next_job.job_id}) starting...")
            else:
                logging.warning("No jobs to run - Not enough initial memory.")
                logging.info(f"Job({next_job.job_id}) waiting for {next_job.init_size} memory...")
                return None

        # Run the job for 1 step
        if self.memory.request(1):
            next_job.advance()
        else:
            logging.warning("No jobs to run - No additional memory.")
            logging.info(f"Job({next_job.job_id}) waiting for 1 memory...")
            return None

        # If job finished after this increment, mark finish time
        if next_job.is_finished:
            next_job.finish_time = self.env.now
            logging.info(f"Job({next_job.job_id}) finished.")

        # Return the next(current) job and a list of finished jobs
        return next_job

    @abstractmethod
    def pick_next_task(self) -> Job:
        """
        Concrete subclasses must implement this method.
        Note: When called, the run_queue should never be empty.
        :return: The next job to run.
        """
        raise NotImplementedError("Subclasses should implement pick_next_task()")

    @property
    def num_jobs(self):
        return len(self.run_queue)

    def __str__(self):
        return f"{self.name}: {self.num_jobs} to run, {len(self.finished_jobs)} finished."