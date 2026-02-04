"""
Test to verify the OpenRouter endpoint configuration fix - ensures
the client uses the config value instead of hardcoded URL.
"""

# Enable test mode to use separate test database
import os
os.environ['TEST_MODE'] = '1'

import sys

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.open_router_client import OpenRouterClient
from config import OPENROUTER_ENDPOINT


def test_default_endpoint_from_config():
    """Test that OpenRouterClient uses config endpoint by default"""
    print("\n=== Testing Default Endpoint from Config ===")

    client = OpenRouterClient(api_key='test_key')

    # Normalize URLs (OpenAI client adds trailing slash)
    client_url = str(client.base_url).rstrip('/')
    config_url = OPENROUTER_ENDPOINT.rstrip('/')

    if client_url == config_url:
        print(f"   ✓ Client uses config endpoint: {client.base_url}")
        print(f"   ✓ Config value: {OPENROUTER_ENDPOINT}")
        return True
    else:
        print(f"   ✗ Client endpoint: {client.base_url}")
        print(f"   ✗ Expected config value: {OPENROUTER_ENDPOINT}")
        return False


def test_custom_endpoint_override():
    """Test that custom endpoint can still override config"""
    print("\n=== Testing Custom Endpoint Override ===")

    custom_url = "https://custom.example.com/v1"
    client = OpenRouterClient(api_key='test_key', base_url=custom_url)

    # Normalize URLs (OpenAI client adds trailing slash)
    client_url = str(client.base_url).rstrip('/')
    expected_url = custom_url.rstrip('/')

    if client_url == expected_url:
        print(f"   ✓ Client uses custom endpoint: {client.base_url}")
        print(f"   ✓ Backward compatibility maintained")
        return True
    else:
        print(f"   ✗ Client endpoint: {client.base_url}")
        print(f"   ✗ Expected custom value: {custom_url}")
        return False


def test_config_value_correctness():
    """Verify the config value is set (actual URL may vary by .env)"""
    print("\n=== Testing Config Value is Set ===")

    official_url = "https://api.openrouter.ai/v1"

    if OPENROUTER_ENDPOINT:
        print(f"   ✓ Config has endpoint set: {OPENROUTER_ENDPOINT}")
        if OPENROUTER_ENDPOINT.rstrip('/') == official_url.rstrip('/'):
            print(f"   ✓ Using official OpenRouter API endpoint")
        else:
            print(f"   ⓘ Using custom endpoint (official is: {official_url})")
        return True
    else:
        print(f"   ✗ Config endpoint is empty or None")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing OpenRouter Endpoint Configuration Fix")
    print("="*60)

    all_passed = True

    # Test 1: Default uses config
    if not test_default_endpoint_from_config():
        all_passed = False

    # Test 2: Can override with custom
    if not test_custom_endpoint_override():
        all_passed = False

    # Test 3: Config value is correct
    if not test_config_value_correctness():
        all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        print("="*60)
        sys.exit(0)
    else:
        print("SOME TESTS FAILED ✗")
        print("="*60)
        sys.exit(1)
