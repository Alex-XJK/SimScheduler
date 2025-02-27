from enum import Enum

from Memory import Memory
from Scheduler import Scheduler
from Job import Job


class Device:
    """
    Represents a device with its own memory and scheduler.

    Parameters:
      - env: SimPy environment.
      - memory_capacity: Total memory capacity for the device.
      - scheduler_cls: The Scheduler class to use (e.g., FCFSScheduler, RRScheduler, etc.).
      - scheduler_kwargs: Additional keyword arguments for the scheduler.
      - name: Name of the device (for easy debugging).
      - tag: Operational mode of the device (e.g., Prefill, Decode, Mixed).
    """
    class Mode(Enum):
        """
        The operational mode of the device.
        """
        PREFILL = "Prefill Only"
        DECODE  = "Decode Only"
        MIXED   = "Mixed Operations"

    def __init__(self, env, memory_capacity, scheduler_cls, scheduler_kwargs, name="Device", tag=Mode.DECODE):
        self.env = env
        self.name = name
        self.tag = tag
        self.memory = Memory(env, capacity=memory_capacity)
        self.scheduler = scheduler_cls(env, self, self.memory, **scheduler_kwargs)
        self.global_scheduler = None

    def set_global_scheduler(self, global_scheduler):
        self.global_scheduler = global_scheduler

    def add_job(self, job: Job) -> bool:
        """
        Add a job to the device's scheduler.
        """
        if not self.job_state_supported(job):
            return False
        return self.scheduler.add_job(job)

    def step(self) -> list[Job]:
        """
        Advance the device's scheduler by one step.
        """
        return self.scheduler.step()

    @property
    def workload(self) -> int:
        """
        Return the current workload of the device.
        The minimum value the better in this case.
        """
        return -self.memory.available_tokens

    @property
    def is_finished(self) -> bool:
        return self.scheduler.num_jobs == 0

    def job_state_supported(self, job) -> bool:
        """
        Check if the job's state is supported by this device.
        """
        if self.tag == Device.Mode.PREFILL:
            return job.state == Job.State.PREFILL or job.state == Job.State.INITIAL
        elif self.tag == Device.Mode.DECODE:
            return job.state == Job.State.DECODE
        elif self.tag == Device.Mode.MIXED:
            return True
        return False

    def __str__(self):
        return f"{self.name} ({self.tag})\n\t{self.scheduler}\n\t{self.memory}"
