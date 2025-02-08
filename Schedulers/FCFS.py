import simpy
from Scheduler import Scheduler

class FCFS(Scheduler):
    """
    A First-Come-First-Serve Scheduler.
    """
    def __init__(self, env, memory, batch):
        super().__init__(env, memory, batch,"FCFS")

    def introduction(self):
        return "First-Come-First-Serve Scheduler"

    def pick_next_task(self):
        # Every time, pick the first batch jobs in the queue
        chosen_jobs = []
        memory_available = self.memory.available_tokens
        for i in range(self.batch):
            if i >= self.num_jobs:
                break

            if self.run_queue[i].current_size > 0:
                chosen_jobs.append(self.run_queue[i])
                memory_available -= 1
            else:
                # Job has not been allocated memory yet
                if memory_available > self.run_queue[i].init_size:
                    memory_available -= self.run_queue[i].init_size
                    chosen_jobs.append(self.run_queue[i])
                else:
                    # Not enough memory to run this job, we need to wait
                    break

        return chosen_jobs
