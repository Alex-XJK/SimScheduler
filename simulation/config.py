from dataclasses import dataclass

from simulation.types import ReplicaType

@dataclass
class BaseRequestGeneratorConfig:
    """
    Base class for request generator configurations.
    """
    pass

@dataclass
class BaseSchedulerConfig:
    """
    Base class for scheduler configurations.
    """
    pass

@dataclass
class MemoryConfig:
    """
    Configuration for the memory of a replica.
    """
    capacity: int
    max_memory_usage: float

@dataclass
class ReplicaConfig:
    """
    Configuration for a single replica in the cluster.
    """
    # TODO: parallelism
    id: int
    replica_type: ReplicaType
    memory_config: MemoryConfig
    scheduler_config: BaseSchedulerConfig

@dataclass
class ClusterConfig:
    replica_configs: list[ReplicaConfig]
    # TODO: network configuration

@dataclass
class MetricStoreConfig:
    output_dir: str
    write_json_trace: bool
    write_chrome_trace: bool

@dataclass
class SimulationConfig:
    time_limit: float
    cluster_config: ClusterConfig
    request_generator_config: BaseRequestGeneratorConfig
    metric_store_config: MetricStoreConfig
