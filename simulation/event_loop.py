import heapq

from simulation.config import SimulationConfig
from simulation.events.base_event import BaseEvent
from simulation.tracer import Tracer


def event_loop(
    config: SimulationConfig,
    metric_store: MetricStore,
    tracer: Tracer,
) -> None:
    """
    Main event loop for the simulation.
    This function is responsible for processing events in the simulation.
    It handles the event queue and manages the simulation time.
    """

    time = 0
    terminate = False

    # Initialize events and heapify
    event_queue = generate_requests(config)
    heapq.heapify(event_queue)

    # Main event loop
    while event_queue and not config.terminate:
        _, event = heapq.heappop(event_queue)

        assert (
            event._time >= config.time
        ), f"Event time {event._time} is less than current time {config.time}"
        time = event._time
        if time > config.time_limit:
            terminate = True
            break

        new_events = event.handle_event(cluster, metric_store)

        # Add new resulting events to the event queue
        for new_event in new_events:
            heapq.heappush(event_queue, new_event)

        tracer.handle_event(event)
    
    assert cluster.is_empty() or terminate
    tracer.write_traces()
    metric_store.write_metrics()

