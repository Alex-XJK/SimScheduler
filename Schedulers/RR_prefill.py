import simpy
import logging
import math
from dataclasses import dataclass
from Scheduler import Scheduler
from Job import Job

@dataclass
class Progress:
    """
    A data class to store the progress of a job.
    """
    job: Job
    expected_time: int
    total_running_time: int = 0
    iter_running_time: int = 0
    memory_allocated: bool = False

class RRPre(Scheduler):
    """
    A Round-Robin Scheduler specialized for prefilling memory.
    """
    def __init__(self, env, device, memory, chunk_size, chunk_time):
        super().__init__(env, device, memory, 1,"RR-Pre")
        self.chunk_size = chunk_size
        self.chunk_time = chunk_time
        self.run_queue : list[Progress] = []
        self.cur_progress: Progress|None = None

    def add_job(self, job : Job) -> bool:
        """
        Override the add_job method to include our progress information.
        """
        time = int(math.ceil(job.init_size / self.chunk_size)) * self.chunk_time
        self.run_queue.append(Progress(job=job, expected_time=time))
        return True

    def step(self) -> list[Job]:
        """
        We have to override the entire step method to handle the prefill stage.
        """
        logging.debug(f"{self.device.name} >> {self.memory}")

        # If we have a job in progress
        if self.cur_progress is not None:
            # If the job is done --> Cleanup & Choose next job
            if self.cur_progress.total_running_time >= self.cur_progress.expected_time:
                logging.debug(f"{self.device.name} >> Job({self.cur_progress.job.job_id}) prefill complete.")
                # Cleanup local resources
                self.memory.release(self.cur_progress.job.init_size)
                self.run_queue.remove(self.cur_progress)
                # Hand back to the global scheduler
                self.cur_progress.job.state = Job.State.DECODE
                self.cur_progress.job.prefill_finish_time = self.env.now
                self.device.global_scheduler.receive_job(self.cur_progress.job)
                # Reset local state
                self.cur_progress = None
            # This iteration is done --> Choose next job
            elif self.cur_progress.iter_running_time >= self.chunk_time:
                self.cur_progress.iter_running_time = 0
                self.run_queue.append(self.run_queue.pop(0))
                self.cur_progress = None
            # If this iteration is in progress --> Continue & Return
            else:
                self.cur_progress.total_running_time += 1
                self.cur_progress.iter_running_time += 1
                logging.debug(f"{self.device.name} >> Job({self.cur_progress.job.job_id}) prefilling for {self.cur_progress.total_running_time}/{self.cur_progress.expected_time} steps...")
                return [self.cur_progress.job]

        # Now we have to choose next job to run
        # If nothing in queue, Return
        if len(self.run_queue) == 0:
            logging.debug(f"{self.device.name} >> No jobs to run - Empty run queue.")
            return []

        # Check memory, if near full, we only run already allocated jobs
        if self.memory.occupied_tokens > self.memory.safe_capacity:
            allocated_run_queue = [p for p in self.run_queue if p.memory_allocated]
            if len(allocated_run_queue) == 0:
                logging.debug(f"{self.device.name} >> No jobs to run - Memory near full.")
                return []
            self.cur_progress = allocated_run_queue[0]
        # If memory is not near full, we can run next job
        else:
            self.cur_progress = self.run_queue[0]
            # If next job not in memory (e.g., a new job), allocate memory for it
            if not self.cur_progress.memory_allocated:
                if not self.memory.request(self.cur_progress.job.init_size):
                    logging.warning(f"{self.device.name} >> Job({self.cur_progress.job.job_id}) failed to allocate {self.cur_progress.job.init_size} tokens.")
                    return []
                logging.debug(f"{self.device.name} >> Job({self.cur_progress.job.job_id}) start prefilling for {self.cur_progress.expected_time} steps...")
            # Update this new Job's state
            self.cur_progress.job.prefill_start_time = self.env.now
            self.cur_progress.job.state = Job.State.PREFILL
            self.cur_progress.memory_allocated = True
            self.cur_progress.total_running_time = 0
            self.cur_progress.iter_running_time = 0

        # No matter what, we now have a job to run
        self.cur_progress.job.advance(self.env.now)
        self.cur_progress.iter_running_time += 1
        self.cur_progress.total_running_time += 1
        logging.debug(f"{self.device.name} >> Job({self.cur_progress.job.job_id}) prefilling for {self.cur_progress.total_running_time}/{self.cur_progress.expected_time} steps...")
        return [self.cur_progress.job]

    def pick_movable_job(self, expected_stages: list[Job.State]) -> Job|None:
        """
        Override the pick_movable_job method for prefill specific behavior.
        We do not know how to move a Prefill stage job.
        """
        # TODO: Implement this method
        return None

    def preempt_job(self, job : Job) -> bool:
        """
        Override the preempt_job method to adopt the prefill specific behavior.
        We do not know how to move a Prefill stage job.
        """
        # TODO: Implement this method
        return False

    def pick_next_task(self):
        pass

    def __str__(self):
        """
        Override the __str__ method to include the prefill chunk size and time.
        """
        return f"{self.name}: Chunk (Size {self.chunk_size} ~ {self.chunk_time} steps), {self.num_jobs} to run."