import pytest
from unittest.mock import MagicMock, patch
from simulation.entities.batch import Batch
from simulation.entities.request import Request
from simulation.types import RequestState


class TestBatch:
    def test_initialization(self):
        # Create some requests
        request1 = Request(num_prefill_tokens=5, num_decode_tokens=10)
        request2 = Request(num_prefill_tokens=10, num_decode_tokens=5)
        
        # Initialize a batch with these requests
        batch = Batch(requests=[request1, request2])
        
        # Verify the batch has a unique ID
        assert isinstance(batch.id, int)
    
    def test_id_generation(self):
        # Test that IDs are unique and incrementing
        batch1 = Batch(requests=[])
        batch2 = Batch(requests=[])
        
        assert batch1.id != batch2.id
        assert batch2.id == batch1.id + 1
    
    def test_batch_to_dict(self):
        # Create requests and a batch
        request1 = Request(num_prefill_tokens=5, num_decode_tokens=5)
        request2 = Request(num_prefill_tokens=10, num_decode_tokens=10)
        batch = Batch(requests=[request1, request2])
        
        # Get the dictionary representation
        batch_dict = batch.to_dict()
        
        # Verify structure
        assert batch_dict["id"] == batch.id
        assert isinstance(batch_dict["requests"], list)
        assert len(batch_dict["requests"]) == 2
        
        # Verify requests in the dict
        request_ids = [r["id"] for r in batch_dict["requests"]]
        assert request1.id in request_ids
        assert request2.id in request_ids
    
    def test_batch_string_representation(self):
        # Create requests and a batch
        request1 = Request(num_prefill_tokens=5, num_decode_tokens=5)
        request2 = Request(num_prefill_tokens=10, num_decode_tokens=10)
        batch = Batch(requests=[request1, request2])
        
        # Get string representation
        batch_str = str(batch)
        
        # Verify content
        assert f"Batch {batch.id}" in batch_str
        assert str(request1.id) in batch_str
        assert str(request2.id) in batch_str
    
    def test_batch_operations_with_mocked_requests(self):
        # Create mock requests
        mock_request1 = MagicMock()
        mock_request2 = MagicMock()
        
        # Create batch with mock requests
        batch = Batch(requests=[mock_request1, mock_request2])
        
        # Test batch_start
        batch.on_batch_start()
        mock_request1.on_batch_start.assert_called_once()
        mock_request2.on_batch_start.assert_called_once()
        
        # Test batch_end - note there's an issue with the implementation
        # as it doesn't pass token counts to requests
        batch.on_batch_end()
        mock_request1.on_batch_end.assert_called_once()
        mock_request2.on_batch_end.assert_called_once()
    
    def test_batch_operations_with_real_requests(self):
        # Create real requests
        request1 = Request(num_prefill_tokens=5, num_decode_tokens=5)
        request2 = Request(num_prefill_tokens=10, num_decode_tokens=10)
        
        # Use patches to verify method calls
        with patch.object(Request, 'on_batch_start') as mock_start:
            with patch.object(Request, 'on_batch_end') as mock_end:
                batch = Batch(requests=[request1, request2])
                
                # Test on_batch_start
                batch.on_batch_start()
                assert mock_start.call_count == 2
                
                # Test on_batch_end
                batch.on_batch_end()
                assert mock_end.call_count == 2
    
    def test_integration_with_request_state_changes(self):
        # Create real requests
        request1 = Request(num_prefill_tokens=5, num_decode_tokens=5)
        request2 = Request(num_prefill_tokens=3, num_decode_tokens=7)
        
        # Create a batch with the real requests
        batch = Batch(requests=[request1, request2])
        
        # Initial state
        assert request1.pending_prefill is True
        assert request2.pending_prefill is True
        
        # Start the batch
        batch.on_batch_start()
        
        # Process some tokens
        batch.on_batch_end(tokens_per_request=2)
        
        # Verify state changes
        assert request1.num_processed_tokens == 2
        assert request2.num_processed_tokens == 2
        
        # Continue processing
        batch.on_batch_start()
        batch.on_batch_end(tokens_per_request=3)
        
        # Verify continued progress
        assert request1.num_processed_tokens == 5
        assert request2.num_processed_tokens == 5
