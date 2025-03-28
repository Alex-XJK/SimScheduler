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
    def __init__(self, env, device, memory, batch, name="Base Scheduler"):
        self.name = name
        self.env = env
        self.device = device
        self.memory : Memory = memory
        self.batch : int = batch
        self.run_queue : list[Job] = []

    def add_job(self, job : Job) -> bool:
        self.run_queue.append(job)
        return True

    def remove_job(self, job : Job):
        if job in self.run_queue:
            self.run_queue.remove(job)
        else:
            raise ValueError("Job not in run queue.")

    def step(self) -> list[Job]:
        picked_jobs = []

        # Clean up finished jobs first:
        finished_jobs = [j for j in self.run_queue if j.is_finished]
        for job in finished_jobs:
            self.memory.release(job.current_size)
            self.remove_job(job)
            job.state = Job.State.FINISHED
            self.device.global_scheduler.finished_jobs.append(job)

        if not self.run_queue:
            logging.info(f"{self.device.name} >> No jobs to run - Empty run queue.")
            return picked_jobs

        logging.debug(f"{self.device.name} >> {self.memory}")

        # Template Method pattern
        next_jobs = self.pick_next_task()
        # logging.info(f"Scheduler Picked: {next_jobs}")

        if next_jobs is None or len(next_jobs) == 0:
            logging.info(f"{self.device.name} >> No jobs to run - Scheduler decision.")
            return picked_jobs

        for next_job in next_jobs:
            # If this is a swapped out job, we need to re-allocate memory for it
            if next_job.current_size == 0 and next_job.swap_size > 0 and next_job.decode_start_time is not None:
                if self.memory.request(next_job.swap_size):
                    next_job.current_size = next_job.swap_size
                    next_job.swap_size = 0
                    logging.debug(f"{self.device.name} >> Job({next_job.job_id}) swapped back in...")
                else:
                    logging.warning(f"{self.device.name} >> Job({next_job.job_id}) waiting for {next_job.swap_size} memory... Swap failed.")
                    continue

            # First time running this job
            if next_job.current_size == 0 and next_job.decode_start_time is None:
                if self.memory.request(next_job.init_size):
                    # Allocate memory for this new job
                    next_job.current_size = next_job.init_size
                    next_job.decode_start_time = self.env.now
                    logging.info(f"{self.device.name} >> Job({next_job.job_id}) starting...")
                else:
                    logging.warning(f"{self.device.name} >> Job({next_job.job_id}) waiting for {next_job.init_size} memory... Initiate failed.")
                    continue

            # Run the job for 1 step
            if self.memory.request(1):
                next_job.advance(self.env.now)
            else:
                logging.warning(f"{self.device.name} >> Job({next_job.job_id}) waiting for 1 memory... Run failed.")
                continue

            # Collect the job that was run
            picked_jobs.append(next_job)

            # If job finished after this increment, mark finish time
            if next_job.is_finished:
                next_job.decode_finish_time = self.env.now
                logging.info(f"{self.device.name} >> Job({next_job.job_id}) finished.")

        # Return the next(current) job and a list of finished jobs
        return picked_jobs

    @abstractmethod
    def pick_next_task(self) -> list[Job]:
        """
        Concrete subclasses must implement this method.
        Note: When called, the run_queue should never be empty.
        :return: The next job to run.
        """
        raise NotImplementedError("Subclasses should implement pick_next_task()")

    def pick_movable_job(self, expected_stages: list[Job.State]) -> Job|None:
        """
        Pick a job that can be moved to another device.
        TODO: Not quite sure our preference for moving jobs yet.
        :return: The job to move or None if no job can be moved.
        """
        possible_jobs = None
        for i, job in enumerate(self.run_queue):
            # If job is not in the expected stage, skip
            if job.state not in expected_stages:
                continue
            # First {batch} jobs are probably already running
            if i < self.batch:
                continue
            # We prefer to move jobs that are not yet running (to reduce memory transfer)
            if job.current_size == 0:
                return job
            # If we have not found a job that is not running yet, we will pick the first running job
            else:
                if possible_jobs is None:
                    possible_jobs = job
        return possible_jobs

    def preempt_job(self, job : Job) -> bool:
        """
        Force a job to be preempted.
        :param job: The job to preempt.
        :return: True if job was preempted, False otherwise.
        """
        if job not in self.run_queue:
            return False
        # If job is not running, we can just remove it
        if job.current_size == 0:
            self.run_queue.remove(job)
            return True
        # If job is running, we need to treat it as a swap out and release memory
        self.memory.release(job.current_size)
        job.swap_size = job.current_size
        job.current_size = 0
        self.run_queue.remove(job)
        return True

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
        return f"{self.name}: Batch Size {self.batch}, {self.num_jobs} to run."