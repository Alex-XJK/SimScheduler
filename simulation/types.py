from enum import Enum


class ReplicaType(Enum):
    """
    Enum representing the type of a replica in the cluster.
    """
    PREFILL = "Prefill-only"
    DECODE = "Decode-only"
    HYBRID = "Hybrid"


class EventType(Enum):
    """
    Enum representing the type of an event in the simulation.
    """
    GLOBAL_REQUEST_ARRIVAL = "Global Request Arrival"
    GLOBAL_SCHEDULER_STEP = "Global Scheduler Step"
    # NOTE: for now we assume a model where global scheduler pushes requests to replicas rather than replicas pulling
    # NOTE: Global scheduling must be idempotent
    # NOTE: There cannot be another replica scheduler step between a replica scheduler step and when the replica batch ends
    REPLICA_SCHEDULER_STEP = "Replica Scheduler Step"
    REPLICA_BATCH_START = "Replica Batch Start"  # NOTE: we differentiate with REPLICA_SCHEDULER_STEP in case we need to do synchronous ops before batch starts
    REPLICA_BATCH_END = "Replica Batch End"

    # Global request arrival triggers global scheduler step
    # Global scheduler step triggers replica scheduler step for each request scheduled, but only if the replica is not busy (see note above)
    # Replica scheduler step triggers replica batch start only if the scheduled batch is not empty
    # Replica batch start triggers replica batch end when the batch is finished
    # When should replica batch end trigger global scheduler step?
    # Some worries:
        # Every replica will trigger this event if we do it naively - too many events
        # We only want to triger a global scheduler step if there are requests pending in the global scheduler queue


class RequestState(Enum):
    """
    Enum representing the state of a request in the simulation.
    """
    WAITING = "Waiting"
    RUNNING_PREFILL = "Running Prefill"
    PREEMPTED_PREFILL = "Preempted Prefill"
    FINISHED_PREFILL = "Finished Prefill"
    PREEMPTED_DECODE = "Preempted Decode"
    RUNNING_DECODE = "Running Decode"
    COMPLETED = "Completed"
    ABORTED = "Aborted"