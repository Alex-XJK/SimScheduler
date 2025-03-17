import logging
from Schedulers.BaseScheduler import Scheduler

class RR(Scheduler):
    """
    A round-robin scheduler with a time slice.
    But queue new jobs when the memory is (near) full.
    And swap out jobs when the memory is full.
    """
    def __init__(self, env, device, memory, batch, time_slice=1):
        super().__init__(env, device, memory, batch, f"RR{time_slice}")
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

        # Each every time slice, we modify the run queue to dequeue the first job and enqueue it at the end.
        if self.env.now % self.time_slice == 0:
            for _ in range(self.time_slice):
                j = self.run_queue.pop(0)
                self.run_queue.append(j)

        return selected_jobs