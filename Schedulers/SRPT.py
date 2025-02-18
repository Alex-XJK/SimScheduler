import logging
import simpy

from Scheduler import Scheduler
from Job import Job


class SRPT(Scheduler):
    """
    Shortest Remaining Processing Time (SRPT) Scheduler.
    """
    def __init__(self, env, memory, batch, priority_quantum, starvation_threshold):
        super().__init__(env, memory, batch,"SRPT")
        self.priority_quantum = priority_quantum
        self.starvation_threshold = starvation_threshold
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

    def pick_next_task(self) -> list[Job]:
        # Unblock waiting jobs if memory is available
        while self._get_expected_memory() < self.memory.safe_capacity and self.wait_queue:
            job = self.wait_queue.pop(0)
            logging.debug(f"Job({job.job_id}) unblocked thanks to memory availability.")
            self.run_queue.append(job)

        self.run_queue = sorted(self.run_queue, key=lambda job: (not job.is_priority, job.final_size - job.current_size))
        selected_jobs = []
        i = 0
        while i < min(self.batch, len(self.run_queue)):
            job = self.run_queue[i]
            if job.current_size == 0:
                assert job.swap_size > 0 or job.init_size > 0
                can_swap_in = True

                # Swap out lowest priority request until we can swap in
                while not self.memory.request(max(job.swap_size, job.init_size)):
                    found = False
                    for j in range(len(self.run_queue)-1, i, -1):
                        if self.run_queue[j].current_size > 0:
                            self.memory.release(self.run_queue[j].current_size)
                            self.run_queue[j].swap_size = self.run_queue[j].current_size
                            self.run_queue[j].current_size = 0
                            found = True
                            break
                    if not found:
                        can_swap_in = False
                        break
                if can_swap_in:
                    job.current_size = max(job.swap_size, job.init_size)
                    job.swap_size = 0
                else:
                    break
            selected_jobs.append(job)
            i += 1

        if self.priority_quantum is not None and self.starvation_threshold is not None:
            for job in selected_jobs:
                job.last_scheduled_time = self.env.now
                if job.is_priority:
                    job.quantum -= 1
            for job in self.run_queue[i:]:  # Unselected jobs
                job.starvation_count += 1
            for job in self.run_queue:
                if job.starvation_count >= self.starvation_threshold:
                    job.is_priority = True
                    job.starvation_count = 0
                    job.quantum = self.priority_quantum

        return selected_jobs
        
        # TODO: make this memory aware
        # TODO: let's try maxxing out batch size to compute-bound region.
        # Concern: right now it sems like we're blocking if it doesn't fit into GPU memory in RR
        # let's introduce a swapped requests var instead
        # ALso round robin assumes chosen requests won't overflow memory - not always true.