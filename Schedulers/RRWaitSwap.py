import simpy
import logging
from Scheduler import Scheduler

class RRWaitSwapScheduler(Scheduler):
    """
    A round-robin scheduler with a time slice.
    But queue new jobs when the memory is (near) full.
    And swap out jobs when the memory is full.
    """
    def __init__(self, env, memory, time_slice=1, threshold=1.0):
        super().__init__(env, memory, "RR-wait-swap")
        self.time_slice = time_slice
        self.threshold = threshold
        self.wait_queue = []

    def introduction(self):
        return f"Round Robin({self.time_slice}), push new jobs to wait queue when memory is full, swap out jobs when memory is full."

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
        if job.init_size <= self.memory.capacity * self.threshold - self._get_expected_memory():
            self.run_queue.append(job)
            return True
        else:
            self.wait_queue.append(job)
            logging.debug(f"Job({job.job_id}) blocked due to memory shortage.")
            return True

    def pick_next_task(self):
        # Unblock waiting jobs if memory is available
        while self._get_expected_memory() < self.memory.capacity * self.threshold and self.wait_queue:
            job = self.wait_queue.pop(0)
            logging.debug(f"Job({job.job_id}) unblocked thanks to memory availability.")
            self.run_queue.append(job)

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