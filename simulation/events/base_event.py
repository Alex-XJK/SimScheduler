from abc import ABC, abstractmethod

from simulation.types import EventType

class Event(ABC):
    __glob_id = -1

    @classmethod
    def __generate_id(cls):
        cls.__glob_id += 1
        return cls.__glob_id

    def __init__(self, time: float, event_type: EventType):
        self.__time = time
        self.__id = self.__generate_id()
        self.__event_type = event_type
    
    @property
    def time(self) -> float:
        return self.__time
    
    @property
    def id(self) -> int:
        return self.__id

    @property
    def event_type(self) -> EventType:
        return self.__event_type
    
    def __lt__(self, other: "Event") -> bool:
        return (self.time, self.id, self.event_type) < (other.time, other.id, other.event_type)
    
    def __eq__(self, other: "Event") -> bool:
        return self.time == other.time and self.id == other.id and self.event_type == other.event_type

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def to_chrome_trace(self):
        pass