import logging
import math
from Schedulers.BaseScheduler import Scheduler
from Job import Job

class FCFSPre(Scheduler):
    """
    A First-Come-First-Serve Scheduler specialized for prefilling memory.
    """
    def __init__(self, env, device, memory, chunk_size, chunk_time):
        super().__init__(env, device, memory, 1,"FCFS-Pre")
        self.chunk_size = chunk_size
        self.chunk_time = chunk_time
        self.cur_job: Job|None = None
        self.cur_job_time = 0
        self.cur_job_expected_time = 0

    def step(self) -> list[Job]:
        """
        We have to override the entire step method to handle the prefill stage.
        """
        logging.debug(f"{self.device.name} >> {self.memory}")

        # If we have a job in progress, check if it's done.
        if self.cur_job is not None:
            if self.cur_job_time >= self.cur_job_expected_time:
                logging.debug(f"{self.device.name} >> Job({self.cur_job.job_id}) prefill complete.")
                # Cleanup local resources
                self.memory.release(self.cur_job.init_size)
                self.remove_job(self.cur_job)
                # Hand back to the global scheduler
                self.cur_job.state = Job.State.DECODE
                self.cur_job.prefill_finish_time = self.env.now
                self.device.global_scheduler.receive_job(self.cur_job)
                # Reset local state
                self.cur_job = None
                self.cur_job_time = 0
                self.cur_job_expected_time = 0
            else:
                self.cur_job_time += 1
                self.cur_job.advance(self.env.now)
                logging.debug(f"{self.device.name} >> Job({self.cur_job.job_id}) prefilling for {self.cur_job_time}/{self.cur_job_expected_time} steps...")
                return [self.cur_job]

        # If we have no job in progress, check if we have any jobs to start.
        if len(self.run_queue) == 0:
            logging.debug(f"{self.device.name} >> No jobs to run - Empty run queue.")
            return []

        # Start the next job in the queue
        self.cur_job = self.run_queue[0]

        # Allocate memory for this job
        if not self.memory.request(self.cur_job.init_size):
            logging.warning(f"{self.device.name} >> Job({self.cur_job.job_id}) failed to allocate {self.cur_job.init_size} tokens.")
            return []

        self.cur_job.state = Job.State.PREFILL
        self.cur_job.advance(self.env.now)
        self.cur_job_time = 0

        # Calculate the expected time for this job
        iterations = int(math.ceil(self.cur_job.init_size / self.chunk_size))
        self.cur_job_expected_time = iterations * self.chunk_time
        logging.debug(f"{self.device.name} >> Job({self.cur_job.job_id}) start prefilling for {self.cur_job_expected_time} steps...")
        return [self.cur_job]

    def pick_movable_job(self, expected_stages: list[Job.State]) -> Job|None:
        """
        Override the pick_movable_job method for prefill specific behavior.
        We do not know how to move a Prefill stage job.
        But due to the FCFS nature, all non-running jobs are movable.
        """
        if len(self.run_queue) == 0 or Job.State.PREFILL not in expected_stages:
            return None
        for i, job in enumerate(self.run_queue):
            if job == self.cur_job:
                continue
            if i < self.batch:
                continue
            return job
        return None

    def preempt_job(self, job : Job) -> bool:
        """
        Override the preempt_job method to adopt the prefill specific behavior.
        """
        # We do not support preemption in the prefill stage
        if job == self.cur_job:
            return False
        # We do not need to free up memory for a job that is not running
        self.run_queue.remove(job)
        return True

    def pick_next_task(self):
        pass

    def __str__(self):
        """
        Override the __str__ method to include the prefill chunk size and time.
        """
        return f"{self.name}: Chunk (Size {self.chunk_size} ~ {self.chunk_time} steps), {self.num_jobs} to run."