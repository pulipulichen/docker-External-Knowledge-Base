import base64
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to allow importing from python_packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from python_packages.image_describe.image_describe import image_describe

def test_image_describe_mocked():
    """
    Tests image_describe with mocked Redis and Requests to ensure logic is correct.
    """
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    with patch('python_packages.image_describe.image_describe.redis_client') as mock_redis, \
         patch('python_packages.image_describe.image_describe.requests.post') as mock_post:
        
        # Scenario 1: Not in cache
        mock_redis.get.return_value = None
        mock_post.return_value.json.return_value = {
            'choices': [{'message': {'content': 'A tiny red dot'}}]
        }
        mock_post.return_value.status_code = 200
        
        print("Testing Scenario 1: Not in cache...")
        result = image_describe(test_image_b64)
        print(f"Result: {result}")
        
        assert result == "A tiny red dot"
        mock_redis.setex.assert_called()
        print("Scenario 1 passed.")

        # Scenario 2: In cache
        mock_redis.get.return_value = "Cached description"
        
        print("\nTesting Scenario 2: In cache...")
        result = image_describe(test_image_b64)
        print(f"Result: {result}")
        
        assert result == "Cached description"
        mock_post.assert_called_once() # Should not be called again
        print("Scenario 2 passed.")

if __name__ == "__main__":
    try:
        test_image_describe_mocked()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
