from enum import Enum

from simulation.config import MemoryConfig, ReplicaConfig
from simulation.entities.batch import Batch
from simulation.entities.request import Request
from simulation.types import ReplicaType


class Memory:
    """
    A memory object is used to store the requests and their states.
    """

    def __init__(self, config: MemoryConfig):
        self.__capacity = config.capacity
        self.__max_memory_usage = config.max_memory_usage
        self.__occupied_tokens = 0

    @property
    def capacity(self):
        return self.__capacity

    @property
    def occupied_tokens(self):
        return self.__occupied_tokens

    @property
    def safe_capacity(self):
        return self.__capacity * self.__max_memory_usage
    
    def allocate(self, amount: int):
        """
        Allocate memory for the given amount of tokens.
        """
        if self.__occupied_tokens + amount > self.safe_capacity:
            raise ValueError("Not enough memory available.")
        self.__occupied_tokens += amount
    
    def free(self, amount: int):
        """
        Free memory for the given amount of tokens.
        """
        if self.__occupied_tokens - amount < 0:
            raise ValueError("Freeing more memory than occupied.")
        self.__occupied_tokens -= amount


class Replica:
    """
    A replica (assumed to be only a single device for now) contains its own memory and scheduler.
    """

    def __init__(
        self,
        config: ReplicaConfig,
    ):
        self.__id = config.id
        self.__replica_type = config.replica_type

        self.__replica_memory = Memory(config.memory_config)
        self.__scheduler = create_replica_scheduler(config.scheduler_config, self.__replica_memory)
    
    def on_request_arrival(self, request: Request):
        # Make sure the request is supported 
        assert not request.completed
        assert not self.__replica_type == ReplicaType.PREFILL or request.pending_prefill
        assert not self.__replica_type == ReplicaType.DECODE or request.pending_decode
        assert not self.__replica_type == ReplicaType.MIXED or request.pending_prefill or request.pending_decode

        self.__scheduler.add_request(request)
    
    def step(self) -> Batch:
        """
        Advance the device's scheduler by one step.
        """
        return self.__scheduler.step()

    @property
    def workload(self) -> int:
        """
        Return the current workload of the device.
        The minimum value the better in this case.
        """
        return 0.02 * self.scheduler.num_jobs + 1.0 * (self.memory.occupied_tokens / self.memory.safe_capacity)

    @property
    def is_finished(self) -> bool:
        return self.scheduler.num_jobs == 0
    
    def __str__(self):
        return f"{self.name} ({self.tag.value})\n\t{self.scheduler}\n\t{self.memory}"
