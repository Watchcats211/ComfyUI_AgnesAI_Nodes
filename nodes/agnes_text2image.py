"""
Agnes_Text2Image Node - Text to Image generation via Agnes.ai API
"""

import os
import json
import urllib.request
import urllib.error
import ssl
import io
import time

try:
    import torch
    import numpy as np
    from PIL import Image
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


class Agnes_Text2Image:
    """
    Generate images from text prompts using Agnes.ai API.
    Outputs: IMAGE tensor (for ComfyUI preview) + URL string (for Image2Video)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("AGNES_CONFIG", {
                    "tooltip": "Agnes configuration from Agnes_Config node"
                }),
                "prompt": ("STRING", {
                    "default": "A beautiful landscape with mountains and a lake at sunset, cinematic lighting, 8k",
                    "multiline": True,
                    "tooltip": "Describe the image you want to generate"
                }),
                "size": ([
                    "1152x768", "768x1152", "1024x1024",
                    "1344x768", "768x1344", "1536x640", "640x1536",
                    "512x512", "768x768",
                ], {
                    "default": "1152x768",
                    "tooltip": "Image resolution"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "step": 1,
                    "tooltip": "Random seed (-1 for random)"
                }),
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "What to avoid in the image"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "url")
    FUNCTION = "generate"
    CATEGORY = "AgnesAI"
    OUTPUT_NODE = True

    def generate(self, config, prompt, size, seed, negative_prompt=""):
        api_key = config["api_key"]
        base_url = config["base_url"]
        url = f"{base_url}/images/generations"

        payload = {
            "prompt": prompt,
            "model": "agnes-image-2.1-flash",
            "size": size,
            "n": 1,
        }
        if seed >= 0:
            payload["seed"] = seed
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = json.dumps(payload).encode("utf-8")

        print(f"🎨 Agnes Text-to-Image: {prompt[:60]}...")

        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            # Extract image URL
            img_url = ""
            if "data" in result and len(result["data"]) > 0:
                img_url = result["data"][0].get("url", "")
            elif "url" in result:
                img_url = result["url"]

            if not img_url:
                raise ValueError(f"No image URL in response: {json.dumps(result)[:200]}")

            print(f"  ✓ Image URL: {img_url[:80]}...")

            # Download and convert to ComfyUI tensor
            image_tensor = self._download_to_tensor(img_url)
            return (image_tensor, img_url)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"  ✗ HTTP Error {e.code}: {body[:200]}")
            return (self._error_image(), "")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return (self._error_image(), "")

    def _download_to_tensor(self, url):
        """Download image and convert to ComfyUI IMAGE tensor [1, H, W, C]."""
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                image_bytes = resp.read()

            pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            np_array = np.array(pil_image).astype(np.float32) / 255.0
            tensor = torch.from_numpy(np_array).unsqueeze(0)  # [1, H, W, C]
            return tensor
        except Exception as e:
            print(f"  ⚠️  Download failed: {e}")
            return self._error_image()

    def _error_image(self):
        """Return a red placeholder image tensor."""
        img = Image.new("RGB", (512, 512), (255, 50, 50))
        arr = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(arr).unsqueeze(0)
