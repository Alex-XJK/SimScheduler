class Job:
    """
    Represents a single job/request.
    - It starts with P tokens required (P <= capacity).
    - Each 'step' it grows by 1 token until total usage = M tokens.
    - arrival_time: when this job arrived in the system.
    - start_time: when it first got scheduled/allocated memory.
    - finish_time: when it completed generating M tokens.
    """

    def __init__(self, job_id, arrival_time, init_size, expected_output):
        self.job_id = job_id
        self.init_size = init_size
        self.final_size = init_size + expected_output
        self.current_size = 0
        self.swap_size = 0  # For swapping-enabled schedulers only
        # For statistics
        self.arrival_time = arrival_time
        self.start_time = None
        self.finish_time = None

        # Only used for SRPT scheduler
        self.last_scheduled_time = None
        self.starvation_count = 0
        self.quantum = 0
        self.is_priority = False

    @property
    def is_finished(self):
        return self.current_size >= self.final_size or self.finish_time is not None

    @property
    def total_time_in_system(self):
        if self.finish_time is not None:
            return self.finish_time - self.arrival_time
        return None

    def advance(self):
        self.current_size += 1

    def __repr__(self):
        if self.is_finished:
            return f"Job({self.job_id}): Finished at {self.finish_time}"
        else:
            progress = ((self.current_size - self.init_size) / (self.final_size - self.init_size)) * 100
            return f"Job({self.job_id}): [{self.init_size} --> {self.current_size} --> {self.final_size}] {progress:.1f}%"
