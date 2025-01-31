import simpy
from Scheduler import Scheduler

class RRScheduler(Scheduler):
    """
    A round-robin scheduler with a time slice.
    """
    def __init__(self, env, memory, time_slice=1):
        super().__init__(env, memory)
        self.time_slice = time_slice
        self.current_index = 0  # track which job is next in round-robin order


    def step(self):
        """
        Each call picks the next job in run_queue (if any).
        If the current job is finished, remove it.
        Then pick the next job in RR order.
        """
        # Clean up finished jobs first:
        finished_jobs = [j for j in self.run_queue if j.is_finished]
        for job in finished_jobs:
            self.remove_job(job)

        if not self.run_queue:
            return None

        # Ensure current_index is valid
        self.current_index %= len(self.run_queue)
        job = self.run_queue[self.current_index]

        # Move round-robin pointer forward for the next step
        self.current_index = (self.current_index + 1) % len(self.run_queue)
        return job