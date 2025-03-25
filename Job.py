from enum import Enum

class Job:
    """
    Represents a single job/request.
    - It starts with P tokens required (P <= capacity).
    - Each 'step' it grows by 1 token until total usage = M tokens.
    - arrival_time: when this job arrived in the system.
    - decode_start_time: when it first got scheduled/allocated memory.
    - decode_finish_time: when it completed generating M tokens.
    """

    class State(Enum):
        """
        The current state of the job.
        """
        INITIAL     = 0
        PREFILL     = 1
        DECODE      = 2
        FINISHED    = 3

    def __init__(self, job_id, arrival_time, init_size, expected_output):
        self.job_id = job_id
        self.state = Job.State.INITIAL
        self.init_size = init_size
        self.final_size = init_size + expected_output
        self.current_size = 0
        self.swap_size = 0  # For swapping-enabled schedulers only
        # For statistics
        self.arrival_time = arrival_time
        self.prefill_start_time = None
        self.prefill_finish_time = None
        self.decode_start_time = None
        self.decode_finish_time = None
        self.execution_time = 0

        # Only used for SRPT scheduler
        self.last_scheduled_time = None
        self.starvation_count = 0
        self.quantum = 0
        self.is_priority = False

    @property
    def is_finished(self):
        return self.current_size >= self.final_size or self.decode_finish_time is not None

    @property
    def total_time_in_system(self):
        if self.decode_finish_time is not None:
            return self.decode_finish_time - self.arrival_time
        return None

    def advance(self, curr_time):
        self.execution_time += 1

        if self.state == Job.State.DECODE:
            if self.decode_start_time is None:
                self.decode_start_time = curr_time
            self.current_size += 1
        elif self.state == Job.State.PREFILL:
            if self.prefill_start_time is None:
                self.prefill_start_time = curr_time

    def __repr__(self):
        if self.is_finished or self.state == Job.State.FINISHED:
            return f"Job({self.job_id}): Finished at {self.decode_finish_time}"
        elif self.state == Job.State.PREFILL:
            return f"Job({self.job_id}): Prefilling... started at {self.prefill_start_time}"
        else:
            progress = ((self.current_size - self.init_size) / (self.final_size - self.init_size)) * 100
            return f"Job({self.job_id}): Decoding... [{self.init_size} --> {self.current_size} --> {self.final_size}] {progress:.1f}%"
