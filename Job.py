class Job:
    """
    Represents a single job/request.
    - It starts with P tokens required (P <= capacity).
    - Each 'step' it grows by 1 token until total usage = M tokens.
    - arrival_time: when this job arrived in the system.
    - start_time: when it first got scheduled/allocated memory.
    - finish_time: when it completed generating M tokens.
    """

    def __str__(self):
        return "Job"