import simpy
import logging
from Scheduler import Scheduler

class RR(Scheduler):
    """
    A round-robin scheduler with a time slice.
    But queue new jobs when the memory is (near) full.
    And swap out jobs when the memory is full.
    """
    def __init__(self, env, memory, batch, time_slice=1):
        super().__init__(env, memory, batch, f"RR{time_slice}")
        self.time_slice = time_slice
        self.wait_queue = []

    def _find_target_job(self):
        """
        Find the last job in the run queue that occupies memory.
        :return: int - index of the job in the run queue
        """
        for i in range(len(self.run_queue)-1, 0, -1):
            if self.run_queue[i].current_size > 0:
                return i
        return None

    def add_job(self, job):
        # Check if we have enough memory to accept this new job
        if job.init_size <= self.memory.safe_capacity - self._get_expected_memory():
            self.run_queue.append(job)
            return True
        else:
            self.wait_queue.append(job)
            logging.debug(f"Job({job.job_id}) blocked due to memory shortage.")
            return True

    def pick_next_task(self):
        # Unblock waiting jobs if memory is available
        while self._get_expected_memory() < self.memory.safe_capacity and self.wait_queue:
            job = self.wait_queue.pop(0)
            logging.debug(f"Job({job.job_id}) unblocked thanks to memory availability.")
            self.run_queue.append(job)

        chosen_jobs = []
        chosen_idx = []
        current_memory_available = self.memory.available_tokens

        # Choose the first `batch size` jobs in the run queue and make sure they can fit in the memory
        for i in range(self.batch):
            if i >= self.num_jobs:
                break

            if self.run_queue[i].current_size > 0:
                # Job already been allocated at least initial memory
                chosen_jobs.append(self.run_queue[i])
                chosen_idx.append(i)
                current_memory_available -= 1
            else:
                # New Job, need to judge memory capacity
                if current_memory_available > self.run_queue[i].init_size:
                    chosen_jobs.append(self.run_queue[i])
                    chosen_idx.append(i)
                    current_memory_available -= (self.run_queue[i].init_size + 1)
                else:
                    # Not enough memory to run this job, skip it
                    continue

        # Swap out the last job in the run queue that occupies memory
        while current_memory_available <= self.batch and len(self.run_queue) > 1:
            idx = self._find_target_job()
            if idx is not None and idx not in chosen_idx:
                target_job = self.run_queue[idx]
                logging.debug(f"Swapping out Job({target_job.job_id}) for {target_job.current_size} memory...")
                self.memory.release(target_job.current_size)
                target_job.swap_size = target_job.current_size
                target_job.current_size = 0
                current_memory_available += target_job.swap_size
                logging.info(f"Memory Status >> {self.memory}")
            else:
                break

        # Each every time slice, we modify the run queue to dequeue the first job and enqueue it at the end.
        if self.env.now % self.time_slice == 0:
            j = self.run_queue.pop(0)
            self.run_queue.append(j)

        return chosen_jobs