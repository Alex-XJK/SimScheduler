from simulation.types import RequestState


class Request:
    """
    Implements a finite state machine to track the state of a request in the simulation.
    Note that the accounting for num_processed_tokens assumes that upon prefill completion, no decode tokens are processed for simplicity.
    """
    __glob_id = -1

    @classmethod
    def __generate_id(cls):
        cls.__glob_id += 1
        return cls.__glob_id

    def __init__(
        self,
        num_prefill_tokens: int,
        num_decode_tokens: int,
    ):
        assert num_prefill_tokens >= 0, f"Number of prefill tokens is negative: {num_prefill_tokens}"
        assert num_decode_tokens >= 0, f"Number of decode tokens is negative: {num_decode_tokens}"

        self.__id = self.__generate_id()
        self.__num_prefill_tokens = num_prefill_tokens
        self.__num_decode_tokens = num_decode_tokens

        self.__num_processed_tokens = 0
        self.__state = RequestState.WAITING
    
    @property
    def id(self) -> int:
        return self.__id

    @property
    def num_prefill_tokens(self) -> int:
        return self.__num_prefill_tokens

    @property
    def num_decode_tokens(self) -> int:
        return self.__num_decode_tokens

    @property
    def num_processed_tokens(self) -> int:
        return self.__num_processed_tokens

    @property
    def total_tokens(self) -> int:
        return self.__num_prefill_tokens + self.__num_decode_tokens

    @property
    def num_processed_prefill_tokens(self) -> int:
        return min(self.__num_processed_tokens, self.__num_prefill_tokens)

    @property
    def num_processed_decode_tokens(self) -> int:
        return max(self.__num_processed_tokens - self.__num_prefill_tokens, 0)
    
    @property
    def state(self) -> RequestState:
        return self.__state
    
    @property
    def pending_prefill(self) -> bool:
        return self.__state == RequestState.WAITING or self.__state == RequestState.PREEMPTED_PREFILL
    
    @property
    def pending_decode(self) -> bool:
        return self.__state == RequestState.FINISHED_PREFILL or self.__state == RequestState.PREEMPTED_DECODE
    
    @property
    def completed(self) -> bool:
        return self.__state == RequestState.COMPLETED
    
    def on_batch_start(self) -> None:
        if self.pending_prefill:
            self.__state = RequestState.RUNNING_PREFILL
        elif self.pending_decode:
            self.__state = RequestState.RUNNING_DECODE
        else:
            raise ValueError(f"Invalid state transition from {self.__state} to a running state")
    
    def on_batch_end(self, num_tokens_processed: int) -> None:
        assert num_tokens_processed >= 0, f"Number of tokens processed is negative: {num_tokens_processed}"
        assert self.__state in (RequestState.RUNNING_PREFILL, RequestState.RUNNING_DECODE), f"Invalid state transition from {self.__state} to a completed/preempted state"

        self.__num_processed_tokens += num_tokens_processed
        if self.num_processed_tokens == self.total_tokens:
            self.__state = RequestState.COMPLETED
        elif self.num_processed_tokens < self.num_prefill_tokens:
            self.__state = RequestState.PREEMPTED_PREFILL
        elif self.num_processed_tokens == self.num_prefill_tokens:
            self.__state = RequestState.FINISHED_PREFILL
        elif self.num_processed_tokens > self.num_prefill_tokens:
            self.__state = RequestState.PREEMPTED_DECODE

    def restart(self):
        # when we restart the request, we can process all the previously
        # decoded tokens in parallel (i.e., we can prefill all the tokens)
        total_tokens = self.__num_prefill_tokens + self.__num_decode_tokens
        self.__num_prefill_tokens = self.__num_processed_tokens
        self.__num_decode_tokens = total_tokens - self.__num_prefill_tokens
        self.__num_processed_tokens = 0
        self.__state = RequestState.WAITING

    def to_dict(self) -> dict:
        return {
            "id": self.__id,
            "state": self.__state.value,
            "num_processed_tokens": self.__num_processed_tokens,
            "num_prefill_tokens": self.__num_prefill_tokens,
            "num_decode_tokens": self.__num_decode_tokens,
        }

    def __str__(self) -> str:
        return f"Request {self.__id}: {self.__state.name}, {self.__num_processed_tokens} tokens processed, {self.__num_prefill_tokens} prefill tokens, {self.__num_decode_tokens} decode tokens"