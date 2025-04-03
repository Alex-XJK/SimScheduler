from simulation.entities.request import Request
from simulation.events.base_event import BaseEvent


class RequestArrivalEvent(BaseEvent):
    def __init__(
        self,
        time: float,
        request: Request,
    ):
        super().__init__(time)
        self.__request = request
    
    def handle_event(self, scheduler: BaseGlobalScheduler, metric_store: MetricStore) -> list[BaseEvent]:
        new_events = scheduler.add_request(self.__request)
        metric_store.on_request_arrival(self.__request)

        return new_events
    
    def to_dict(self) -> dict:
        return {
            "time": self.time,
            "id": self.id,
            "event_type": self.event_type,
            "request": self.__request.to_dict(),
        }