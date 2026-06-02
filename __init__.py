"""
Agnes AI - Agnes.ai API integration for ComfyUI

Supports:
- Text-to-Image (outputs IMAGE tensor + URL string)
- Text-to-Video (outputs IMAGE frames + AUDIO + URL string)
- Image-to-Video (accepts URL string, outputs IMAGE frames + AUDIO + URL string)

API Docs: https://agnes-ai.com/doc/agnes-video-v20
"""

from .nodes.agnes_config import Agnes_Config
from .nodes.agnes_image_to_url import Agnes_ImageToURL
from .nodes.agnes_text2image import Agnes_Text2Image
from .nodes.agnes_text2video import Agnes_Text2Video
from .nodes.agnes_image2video import Agnes_Image2Video

NODE_CLASS_MAPPINGS = {
    "Agnes_Config": Agnes_Config,
    "Agnes_ImageToURL": Agnes_ImageToURL,
    "Agnes_Text2Image": Agnes_Text2Image,
    "Agnes_Text2Video": Agnes_Text2Video,
    "Agnes_Image2Video": Agnes_Image2Video,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Agnes_Config": "🔧 Agnes AI Config",
    "Agnes_ImageToURL": "🖼️ Agnes Image-to-URL",
    "Agnes_Text2Image": "🎨 Agnes Text-to-Image",
    "Agnes_Text2Video": "🎬 Agnes Text-to-Video",
    "Agnes_Image2Video": "🎬 Agnes Image-to-Video",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
