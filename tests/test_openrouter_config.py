"""
Test to verify the OpenRouter endpoint configuration fix - ensures
the client uses the config value instead of hardcoded URL.
"""

# Enable test mode to use separate test database
import os

os.environ["TEST_MODE"] = "1"

import sys

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import OPENROUTER_ENDPOINT
from utils.open_router_client import OpenRouterClient


def test_default_endpoint_from_config():
    """Test that OpenRouterClient uses config endpoint by default."""
    client = OpenRouterClient(api_key="test_key")

    # Normalize URLs (OpenAI client adds trailing slash)
    client_url = str(client.base_url).rstrip("/")
    config_url = OPENROUTER_ENDPOINT.rstrip("/")

    assert (
        client_url == config_url
    ), f"Client URL '{client_url}' does not match config URL '{config_url}'"


def test_custom_endpoint_override():
    """Test that a custom endpoint can still override the config value."""
    custom_url = "https://custom.example.com/v1"
    client = OpenRouterClient(api_key="test_key", base_url=custom_url)

    client_url = str(client.base_url).rstrip("/")
    expected_url = custom_url.rstrip("/")

    assert (
        client_url == expected_url
    ), f"Client URL '{client_url}' does not match custom URL '{expected_url}'"


def test_config_value_correctness():
    """Verify the config endpoint is set (actual URL may vary by .env)."""
    assert OPENROUTER_ENDPOINT, "OPENROUTER_ENDPOINT is empty or None in config"
