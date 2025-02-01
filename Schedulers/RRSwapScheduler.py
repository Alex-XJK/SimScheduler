import simpy
import logging
from Scheduler import Scheduler

class RRSwapScheduler(Scheduler):
    """
    A round-robin scheduler with a time slice.
    But stop accepting new jobs when the memory is (near) full.
    And swap out jobs when the memory is full.
    """
    def __init__(self, env, memory, time_slice=1, threshold=1.0):
        super().__init__(env, memory, "RR-rej-swap")
        self.time_slice = time_slice
        self.threshold = threshold

    def _get_expected_memory(self):
        total_expected_memory = 0
        for job in self.run_queue:
            if job.current_size == 0:
                total_expected_memory += job.init_size
            else:
                total_expected_memory += job.current_size
        return total_expected_memory

    def _find_target_job(self):
        for i in range(len(self.run_queue)-1, 0, -1):
            if self.run_queue[i].current_size > 0:
                return i
        return None


    def add_job(self, job):
        # Check if we have enough memory to accept this new job
        if job.init_size <= self.memory.capacity * self.threshold - self._get_expected_memory():
            self.run_queue.append(job)
            return True
        else:
            logging.warning("Not enough memory to accept new job.")
            return False

    def pick_next_task(self):
        next_job = self.run_queue[0]

        # Swap out the last job in the run queue that occupies memory
        if self._get_expected_memory() > self.memory.capacity * self.threshold and len(self.run_queue) > 1:
            idx = self._find_target_job()
            if idx is not None:
                target_job = self.run_queue[idx]
                logging.debug(f"Swapping out Job({target_job.job_id}) for {target_job.current_size} memory...")
                self.memory.release(target_job.current_size)
                target_job.swap_size = target_job.current_size
                target_job.current_size = 0

        # Each every time slice, we modify the run queue to dequeue the first job and enqueue it at the end.
        if self.env.now % self.time_slice == 0:
            j = self.run_queue.pop(0)
            self.run_queue.append(j)
        return next_job