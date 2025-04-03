from simulation.config import SimulationConfig
from simulation.entities.replica import Replica


class Cluster:
    def __init__(self, config: SimulationConfig):
        self.__config = config
        self.__replicas = [
            Replica(replica_config) for replica_config in config.cluster_config.replica_configs
        ]
        self.__global_scheduler = create_global_scheduler(config.scheduler_config)