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

    def add_job(self, job : Job) -> bool:
        self.run_queue.append(job)
        return True

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

        logging.debug(f"Memory Status >> {self.memory}")

        # Template Method pattern
        next_job = self.pick_next_task()

        if next_job is None:
            logging.info("No jobs to run - Scheduler decision.")
            return None

        # If this is a swapped out job, we need to re-allocate memory for it
        if next_job.current_size == 0 and next_job.swap_size > 0 and next_job.start_time is not None:
            if self.memory.request(next_job.swap_size):
                next_job.current_size = next_job.swap_size
                next_job.swap_size = 0
                logging.debug(f"Job({next_job.job_id}) swapped back in...")
            else:
                logging.warning("No jobs to run - Not enough memory.")
                logging.debug(f"Job({next_job.job_id}) waiting for {next_job.swap_size} memory...")
                return None

        # First time running this job
        if next_job.current_size == 0 and next_job.start_time is None:
            if self.memory.request(next_job.init_size):
                # Allocate memory for this new job
                next_job.current_size = next_job.init_size
                next_job.start_time = self.env.now
                logging.info(f"Job({next_job.job_id}) starting...")
            else:
                logging.warning("No jobs to run - Not enough initial memory.")
                logging.debug(f"Job({next_job.job_id}) waiting for {next_job.init_size} memory...")
                return None

        # Run the job for 1 step
        if self.memory.request(1):
            next_job.advance()
        else:
            logging.warning("No jobs to run - No additional memory.")
            logging.debug(f"Job({next_job.job_id}) waiting for 1 memory...")
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

    def _get_expected_memory(self):
        """
        Calculate the expected memory usage of the run queue.
        Includes currently running jobs and jobs that are not yet running.
        :return: Total expected memory usage.
        """
        total_expected_memory = 0
        for job in self.run_queue:
            if job.current_size == 0:
                total_expected_memory += job.init_size
            else:
                total_expected_memory += job.current_size
        return total_expected_memory


    @property
    def num_jobs(self):
        return len(self.run_queue)

    def __str__(self):
        return f"{self.name}: {self.num_jobs} to run, {len(self.finished_jobs)} finished."