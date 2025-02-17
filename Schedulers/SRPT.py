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

    def pick_next_task(self) -> list[Job]:
        sorted_jobs = sorted(self.run_queue, key=lambda job: (not job.is_priority, job.final_size - job.current_size))
        selected_jobs = sorted_jobs[:self.batch]

        if self.priority_quantum is not None and self.starvation_threshold is not None:
            for job in selected_jobs:
                job.last_scheduled_time = self.env.now
                if job.is_priority:
                    job.quantum -= 1
            for job in sorted_jobs[self.batch:]:
                job.starvation_count += 1
            for job in self.run_queue:
                if job.starvation_count >= self.starvation_threshold:
                    job.is_priority = True
                    job.starvation_count = 0
                    job.quantum = self.priority_quantum

        return selected_jobs