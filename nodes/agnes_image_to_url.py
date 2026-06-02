"""
Agnes_ImageToURL Node - Upload a ComfyUI IMAGE and return a public URL.

Uses storage.to as a short-lived public host so Agnes image-to-video can
consume images generated locally inside ComfyUI.
"""

import io
import json
import ssl
import time
import urllib.error
import urllib.request
import uuid

try:
    import numpy as np
    from PIL import Image
    HAS_IMAGE_LIBS = True
except ImportError:
    HAS_IMAGE_LIBS = False


class Agnes_ImageToURL:
    """
    Upload the first frame of a ComfyUI IMAGE batch and return a public URL.
    """

    STORAGE_TO_API = "https://storage.to/api/sharex/upload"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "Connect any ComfyUI image output here"
                }),
            },
            "optional": {
                "filename_prefix": ("STRING", {
                    "default": "agnes_i2v_source",
                    "multiline": False,
                    "tooltip": "Used only for the temporary uploaded filename"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("url",)
    FUNCTION = "upload"
    CATEGORY = "AgnesAI"

    def upload(self, image, filename_prefix="agnes_i2v_source"):
        if not HAS_IMAGE_LIBS:
            print("[Agnes] Image-to-URL unavailable: numpy/Pillow not installed")
            return ("",)

        try:
            png_bytes = self._image_to_png_bytes(image)
            safe_prefix = self._sanitize_filename(filename_prefix)
            filename = f"{safe_prefix}_{int(time.time())}.png"
            public_url = self._upload_storage_to(png_bytes, filename)
            print(f"[Agnes] Image uploaded: {public_url}")
            return (public_url,)
        except Exception as e:
            print(f"[Agnes] Image-to-URL error: {e}")
            return ("",)

    def _image_to_png_bytes(self, image):
        if getattr(image, "ndim", None) != 4 or image.shape[0] < 1:
            raise ValueError("Expected IMAGE tensor shaped like [N, H, W, C]")

        frame = image[0].cpu().numpy()
        frame = np.clip(frame * 255.0, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(frame, mode="RGB")

        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return buffer.getvalue()

    def _upload_storage_to(self, png_bytes, filename):
        last_error = None
        for attempt in range(1, 4):
            try:
                boundary = f"----AgnesUpload{uuid.uuid4().hex}"
                body = []
                body.append(f"--{boundary}\r\n".encode("utf-8"))
                body.append(
                    (
                        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                    ).encode("utf-8")
                )
                body.append(b"Content-Type: image/png\r\n\r\n")
                body.append(png_bytes)
                body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

                data = b"".join(body)
                headers = {
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(data)),
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/137.0.0.0 Safari/537.36"
                    ),
                }

                ctx = ssl.create_default_context()
                req = urllib.request.Request(
                    self.STORAGE_TO_API,
                    data=data,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                if not result.get("success"):
                    raise ValueError(f"Upload failed: {json.dumps(result)[:200]}")

                raw_url = result.get("raw_url", "")
                if not raw_url.startswith("https://storage.to/r/"):
                    raise ValueError(f"Unexpected upload URL: {raw_url}")

                return raw_url
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
                last_error = e
                print(f"[Agnes] Upload attempt {attempt}/3 failed: {e}")
                if attempt < 3:
                    time.sleep(2)

        raise last_error

    def _sanitize_filename(self, filename_prefix):
        cleaned = "".join(
            ch if ch.isalnum() or ch in ("-", "_") else "_"
            for ch in (filename_prefix or "agnes_i2v_source")
        )
        return cleaned.strip("_") or "agnes_i2v_source"
