from Schedulers.BaseScheduler import Scheduler

class FCFS(Scheduler):
    """
    A First-Come-First-Serve Scheduler.
    """
    def __init__(self, env, device, memory, batch):
        super().__init__(env, device, memory, batch,"FCFS")

    def pick_next_task(self):
        # Every time, pick the first batch jobs in the queue
        chosen_jobs = []
        memory_available = self.memory.available_tokens
        for i in range(min(self.num_jobs, self.batch)):
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
