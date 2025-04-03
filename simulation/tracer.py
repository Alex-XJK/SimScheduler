import json

from simulation.events.base_event import BaseEvent
from simulation.config import SimulationConfig


class Tracer:
    def __init__(self, config: SimulationConfig):
        self.__config = config
        self.__event_trace = []
        self.__event_chrome_trace = []
    
    def handle_event(self, event: BaseEvent) -> None:
        if self.__config.metric_store_config.write_json_trace:
            self.__event_trace.append(event.to_dict())

        if self.__config.metric_store_config.write_chrome_trace:
            chrome_trace = event.to_chrome_trace()
            if chrome_trace:
                self.__event_chrome_trace.append(chrome_trace)
        
    def write_traces(self) -> None:
        if self.__config.metric_store_config.write_json_trace:
            self.__write_event_trace()
        
        if self.__config.metric_store_config.write_chrome_trace:
            self.__write_chrome_trace()

    def __write_event_trace(self) -> None:
        trace_file = f"{self._config.metric_store_config.output_dir}/event_trace.json"
        with open(trace_file, "w") as f:
            json.dump(self._event_trace, f)

    def __write_chrome_trace(self) -> None:
        trace_file = f"{self._config.metric_store_config.output_dir}/chrome_trace.json"
        chrome_trace = {"traceEvents": self._event_chrome_trace}

        with open(trace_file, "w") as f:
            json.dump(chrome_trace, f)
 