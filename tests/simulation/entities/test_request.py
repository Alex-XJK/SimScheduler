import pytest
from simulation.entities.request import Request
from simulation.types import RequestState


class TestRequest:
    def test_initialization(self):
        # Test basic initialization
        request = Request(num_prefill_tokens=10, num_decode_tokens=20)
        assert request.num_prefill_tokens == 10
        assert request.num_decode_tokens == 20
        assert request.num_processed_tokens == 0
        assert request.total_tokens == 30
        
        # Test initialization with zero tokens
        request_zero = Request(num_prefill_tokens=0, num_decode_tokens=0)
        assert request_zero.num_prefill_tokens == 0
        assert request_zero.num_decode_tokens == 0
        
        # Test initialization with negative tokens (should raise assertion error)
        with pytest.raises(AssertionError):
            Request(num_prefill_tokens=-1, num_decode_tokens=10)
        
        with pytest.raises(AssertionError):
            Request(num_prefill_tokens=10, num_decode_tokens=-1)
    
    def test_id_generation(self):
        request1 = Request(num_prefill_tokens=5, num_decode_tokens=5)
        request2 = Request(num_prefill_tokens=5, num_decode_tokens=5)
        assert request1.id != request2.id
        assert request2.id == request1.id + 1
    
    def test_token_processing_properties(self):
        request = Request(num_prefill_tokens=10, num_decode_tokens=20)
        
        # No tokens processed yet
        assert request.num_processed_prefill_tokens == 0
        assert request.num_processed_decode_tokens == 0
        
        # Process some prefill tokens
        request.on_batch_start()
        request.on_batch_end(5)
        assert request.num_processed_prefill_tokens == 5
        assert request.num_processed_decode_tokens == 0
        
        # Process all prefill tokens
        request.on_batch_start()
        request.on_batch_end(5)
        assert request.num_processed_prefill_tokens == 10
        assert request.num_processed_decode_tokens == 0
        
        # Process some decode tokens
        request.on_batch_start()
        request.on_batch_end(5)
        assert request.num_processed_prefill_tokens == 10
        assert request.num_processed_decode_tokens == 5
    
    def test_state_transitions(self):
        request = Request(num_prefill_tokens=10, num_decode_tokens=10)
        
        # Initial state should be WAITING
        assert request.pending_prefill is True
        assert request.pending_decode is False
        assert request.completed is False
        
        # Start processing - should be in RUNNING_PREFILL
        request.on_batch_start()
        
        # Process half the prefill tokens - should be in PREEMPTED_PREFILL
        request.on_batch_end(5)
        assert request.pending_prefill is True
        assert request.pending_decode is False
        assert request.completed is False
        
        # Continue processing - finish prefill tokens
        request.on_batch_start()
        request.on_batch_end(5)
        assert request.pending_prefill is False
        assert request.pending_decode is True
        assert request.completed is False
        
        # Process all decode tokens - should be completed
        request.on_batch_start()
        request.on_batch_end(10)
        assert request.pending_prefill is False
        assert request.pending_decode is False
        assert request.completed is True
    
    def test_restart(self):
        request = Request(num_prefill_tokens=10, num_decode_tokens=10)
        
        # Process some tokens
        request.on_batch_start()
        request.on_batch_end(15)  # Processed 10 prefill + 5 decode
        
        assert request.num_processed_prefill_tokens == 10
        assert request.num_processed_decode_tokens == 5
        
        # Restart the request
        request.restart()
        
        # After restart, all previously processed tokens should be considered prefill
        assert request.num_prefill_tokens == 15
        assert request.num_decode_tokens == 5
        assert request.num_processed_tokens == 0
        assert request.pending_prefill is True
    
    def test_invalid_transitions(self):
        request = Request(num_prefill_tokens=10, num_decode_tokens=10)
        
        # Cannot end batch before starting
        with pytest.raises(AssertionError):
            request.on_batch_end(5)
        
        # Cannot process negative tokens
        request.on_batch_start()
        with pytest.raises(AssertionError):
            request.on_batch_end(-1)
    
    def test_to_dict(self):
        request = Request(num_prefill_tokens=10, num_decode_tokens=20)
        request_dict = request.to_dict()
        
        assert isinstance(request_dict, dict)
        assert request_dict["id"] == request.id
        assert request_dict["num_prefill_tokens"] == 10
        assert request_dict["num_decode_tokens"] == 20
        assert request_dict["num_processed_tokens"] == 0

    def test_initial_state(self):
        # Test that a new request starts in WAITING state
        request = Request(num_prefill_tokens=10, num_decode_tokens=10)
        assert request.state == RequestState.WAITING

    def test_state_during_prefill(self):
        request = Request(num_prefill_tokens=10, num_decode_tokens=10)
        
        # Check initial state
        assert request.state == RequestState.WAITING
        
        # Start batch - should transition to RUNNING_PREFILL
        request.on_batch_start()
        assert request.state == RequestState.RUNNING_PREFILL
        
        # Process some tokens, but not all prefill tokens
        request.on_batch_end(5)
        assert request.state == RequestState.PREEMPTED_PREFILL
        
        # Start batch again
        request.on_batch_start()
        assert request.state == RequestState.RUNNING_PREFILL
        
        # Process remaining prefill tokens exactly
        request.on_batch_end(5)
        assert request.state == RequestState.FINISHED_PREFILL

    def test_state_during_decode(self):
        request = Request(num_prefill_tokens=5, num_decode_tokens=10)
        
        # Process all prefill tokens
        request.on_batch_start()
        request.on_batch_end(5)
        assert request.state == RequestState.FINISHED_PREFILL
        
        # Start decoding
        request.on_batch_start()
        assert request.state == RequestState.RUNNING_DECODE
        
        # Process some decode tokens but not all
        request.on_batch_end(3)
        assert request.state == RequestState.PREEMPTED_DECODE
        
        # Continue decoding
        request.on_batch_start()
        assert request.state == RequestState.RUNNING_DECODE
        
        # Process remaining decode tokens
        request.on_batch_end(7)
        assert request.state == RequestState.COMPLETED

    def test_all_tokens_in_one_batch(self):
        # Test processing all tokens in a single batch
        request = Request(num_prefill_tokens=5, num_decode_tokens=5)
        
        request.on_batch_start()
        request.on_batch_end(10)
        assert request.state == RequestState.COMPLETED

    def test_state_after_restart(self):
        request = Request(num_prefill_tokens=5, num_decode_tokens=5)
        
        # Process some tokens
        request.on_batch_start()
        request.on_batch_end(7)  # 5 prefill + 2 decode
        
        # Before restart, should be in PREEMPTED_DECODE
        assert request.state == RequestState.PREEMPTED_DECODE
        
        # Restart the request
        request.restart()
        
        # After restart, should be back to WAITING
        assert request.state == RequestState.WAITING
        
        # And the prefill tokens should now be equal to the processed tokens before restart
        assert request.num_prefill_tokens == 7
        assert request.num_decode_tokens == 3

    def test_invalid_state_transitions(self):
        request = Request(num_prefill_tokens=5, num_decode_tokens=5)
        
        # Process all tokens
        request.on_batch_start()
        request.on_batch_end(10)
        assert request.state == RequestState.COMPLETED
        
        # Try to start a batch on a completed request
        with pytest.raises(ValueError, match="Invalid state transition"):
            request.on_batch_start()