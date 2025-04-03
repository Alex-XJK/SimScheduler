from simulation.entities.request import Request


class Batch:
    __glob_id = -1

    @classmethod
    def __generate_id(cls):
        cls.__glob_id += 1
        return cls.__glob_id
    
    def __init__(
        self,
        requests: list[Request],
    ):
        self.__id = self.__generate_id()
        self.__requests = requests
    
    @property
    def id(self) -> int:
        return self.__id
    
    def on_batch_start(self) -> None:
        # Replace map with a for loop to ensure it executes
        for request in self.__requests:
            request.on_batch_start()
    
    def on_batch_end(self, tokens_per_request: int = 1) -> None:
        # Add tokens_per_request parameter and pass it to each request
        for request in self.__requests:
            request.on_batch_end(tokens_per_request)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "requests": list(map(lambda request: request.to_dict(), self.__requests)),
        }
    
    def __str__(self) -> str:
        return f"Batch {self.id}: {list(map(lambda request: request.id, self.__requests))}"