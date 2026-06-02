"""
Agnes_Config Node - Configuration node for Agnes.ai API
"""

import json
import os
import urllib.request
import urllib.error
import ssl


class Agnes_Config:
    """
    Configuration node for Agnes.ai API credentials and settings.
    Stores API key and endpoint for use by other Agnes nodes.
    """
    DEFAULT_API_KEY = ""
    DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "default": cls.DEFAULT_API_KEY,
                    "multiline": False,
                    "tooltip": "Your Agnes.ai API key. Leave blank to use AGNES_API_KEY from the environment."
                }),
                "base_url": ("STRING", {
                    "default": cls.DEFAULT_BASE_URL,
                    "multiline": False,
                    "tooltip": "Agnes.ai API base URL"
                }),
            },
        }

    RETURN_TYPES = ("AGNES_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "create_config"
    CATEGORY = "AgnesAI"
    OUTPUT_NODE = True

    def create_config(self, api_key, base_url):
        resolved_api_key = (
            api_key.strip()
            or os.getenv("AGNES_API_KEY", "").strip()
        )
        resolved_base_url = (
            base_url.strip()
            or os.getenv("AGNES_BASE_URL", "").strip()
            or self.DEFAULT_BASE_URL
        )
        config = {
            "api_key": resolved_api_key,
            "base_url": resolved_base_url,
        }

        # Test connection
        connected, msg = self._test_connection(config["api_key"], config["base_url"])
        print(f"{'✓' if connected else '✗'} Agnes Config: {msg}")

        return (config,)

    @staticmethod
    def _test_connection(api_key, base_url):
        """Test if the API key is valid."""
        try:
            req = urllib.request.Request(f"{base_url}/videos", method="GET")
            req.add_header("Authorization", f"Bearer {api_key}")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                return True, "Connected"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return False, f"Auth failed (HTTP {e.code})"
            return True, f"Connected (HTTP {e.code})"
        except Exception as e:
            return False, f"Connection failed: {e}"
