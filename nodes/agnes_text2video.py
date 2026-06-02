"""
Agnes_Text2Video Node - Text to Video generation via Agnes.ai API

Outputs:
  - IMAGE: frame batch tensor [N, H, W, C] for VHS_VideoCombine
  - AUDIO: audio dict for VHS_VideoCombine
  - STRING: video URL (for Agnes_Image2Video connection)
"""

import os
import json
import shutil
import urllib.request
import urllib.error
import ssl
import time
import subprocess

try:
    import torch
    import numpy as np
    import cv2
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import folder_paths
    HAS_FOLDER_PATHS = True
except ImportError:
    HAS_FOLDER_PATHS = False

try:
    from videohelpersuite.utils import lazy_get_audio as vhs_lazy_get_audio
    HAS_VHS_AUDIO = True
except ImportError:
    HAS_VHS_AUDIO = False

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    HAS_IMAGEIO_FFMPEG = True
except ImportError:
    HAS_IMAGEIO_FFMPEG = False


DURATION_PRESETS = [
    "3.4s (81 frames)",
    "5.0s (121 frames)",
    "6.7s (161 frames)",
    "10.0s (241 frames)",
    "13.4s (321 frames)",
]


class Agnes_Text2Video:
    """
    Generate videos from text prompts using Agnes.ai API.
    Outputs IMAGE tensor batch + AUDIO for VHS_VideoCombine, plus URL for I2V.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("AGNES_CONFIG", {
                    "tooltip": "Agnes configuration from Agnes_Config node"
                }),
                "prompt": ("STRING", {
                    "default": "A majestic eagle soaring over mountains at golden sunset, cinematic drone shot",
                    "multiline": True,
                    "tooltip": "Describe the video you want to generate"
                }),
                "duration": (DURATION_PRESETS, {
                    "default": "5.0s (121 frames)",
                    "tooltip": "Video duration"
                }),
                "width": ("INT", {
                    "default": 1152,
                    "min": 512,
                    "max": 1920,
                    "step": 64,
                    "tooltip": "Video width in pixels"
                }),
                "height": ("INT", {
                    "default": 768,
                    "min": 512,
                    "max": 1920,
                    "step": 64,
                    "tooltip": "Video height in pixels"
                }),
                "frame_rate": ("INT", {
                    "default": 24,
                    "min": 12,
                    "max": 60,
                    "step": 1,
                    "tooltip": "Frames per second"
                }),
            },
            "optional": {
                "negative_prompt": ("STRING", {
                    "default": "blurry, low quality, distorted, deformed",
                    "multiline": True,
                    "tooltip": "What to avoid in the video"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "step": 1,
                    "tooltip": "Random seed (-1 for random)"
                }),
                "num_inference_steps": ("INT", {
                    "default": 30,
                    "min": 10,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Inference steps (more = better quality, slower)"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUDIO", "STRING")
    RETURN_NAMES = ("images", "audio", "url")
    FUNCTION = "generate"
    CATEGORY = "AgnesAI"
    OUTPUT_NODE = False

    def generate(self, config, prompt, duration, width, height, frame_rate,
                 negative_prompt="blurry, low quality, distorted, deformed",
                 seed=-1, num_inference_steps=30):
        api_key = config["api_key"]
        base_url = config["base_url"]
        url = f"{base_url}/videos"

        # Parse num_frames from duration string
        num_frames = int(duration.split("(")[1].split(" ")[0])

        # Validate 8n+1
        if (num_frames - 1) % 8 != 0:
            n = (num_frames - 1) // 8
            num_frames = 8 * n + 1

        payload = {
            "prompt": prompt,
            "model": "agnes-video-v2.0",
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
            "num_inference_steps": num_inference_steps,
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

        dur_sec = num_frames / frame_rate
        print(f"[Agnes] Text-to-Video: {prompt[:50]}...")
        print(f"[Agnes] ~{dur_sec:.1f}s ({num_frames}f @ {frame_rate}fps), {width}x{height}")

        try:
            # Submit task
            result = self._submit_task(url, data, headers)

            task_id = self._extract_task_id(result)
            if not task_id:
                raise ValueError(f"No task_id in response: {json.dumps(result)[:200]}")

            print(f"[Agnes] Task submitted: {task_id}")

            # Poll for completion
            video_url = self._poll(task_id, api_key, base_url)
            if not video_url:
                return (self._empty_image(), self._empty_audio(), "")

            print(f"[Agnes] Video ready: {video_url[:80]}...")

            # Download
            local_path = self._download(video_url, task_id)
            if not local_path:
                return (self._empty_image(), self._empty_audio(), "")

            # Decode video to frames + extract audio
            images = self._decode_video(local_path)
            audio = self._extract_audio(local_path)

            return (images, audio, video_url)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"[Agnes] HTTP Error {e.code}: {body[:200]}")
            return (self._empty_image(), self._empty_audio(), "")
        except Exception as e:
            print(f"[Agnes] Error: {e}")
            return (self._empty_image(), self._empty_audio(), "")

    def _extract_task_id(self, result):
        for key in ("id", "task_id"):
            if key in result:
                return str(result[key])
        inner = result.get("data", {}).get("data", {})
        for key in ("id", "task_id"):
            if key in inner:
                return str(inner[key])
        return ""

    def _submit_task(self, url, data, headers, attempts=3, timeout=90):
        ctx = ssl.create_default_context()
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last_error = e
                print(f"[Agnes] Submit attempt {attempt}/{attempts} failed: {e}")
                if attempt < attempts:
                    time.sleep(3)
        raise last_error

    def _poll(self, task_id, api_key, base_url, max_wait=900):
        query_url = f"{base_url}/videos/{task_id}"
        start = time.time()
        ctx = ssl.create_default_context()

        while True:
            elapsed = time.time() - start
            if elapsed > max_wait:
                print(f"[Agnes] Timeout after {int(elapsed)}s")
                return None

            try:
                req = urllib.request.Request(query_url)
                req.add_header("Authorization", f"Bearer {api_key}")
                with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                status = result.get("status", "unknown")

                if status == "unknown" and "error" in result:
                    err = result["error"]
                    if isinstance(err, dict):
                        err = err.get("message", str(err))
                    print(f"[Agnes] Failed: {err}")
                    return None

                if status == "unknown":
                    data = result.get("data", {})
                    inner = data.get("data", {})
                    status = inner.get("status", data.get("status", "unknown"))

                progress = result.get("progress", 0)
                print(f"[Agnes] [{int(elapsed)}s] {status} ({progress}%)")

                if status in ("completed", "succeeded"):
                    for field in ("remixed_from_video_id", "video_url"):
                        vurl = result.get(field, "")
                        if vurl and vurl.startswith("http"):
                            return vurl
                    data = result.get("data", {})
                    for field in ("video_url", "remixed_from_video_id"):
                        vurl = data.get(field, "")
                        if vurl and vurl.startswith("http"):
                            return vurl
                    return None

                elif status in ("failed", "error"):
                    err = result.get("error", "Unknown")
                    if isinstance(err, dict):
                        err = err.get("message", str(err))
                    print(f"[Agnes] Failed: {err}")
                    return None

                time.sleep(10)

            except (urllib.error.HTTPError, urllib.error.URLError, ssl.SSLError, OSError):
                print(f"[Agnes] Network error, retrying...")
                time.sleep(10)
                continue

    def _download(self, url, task_id):
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url)

            if HAS_FOLDER_PATHS:
                output_dir = folder_paths.get_output_directory()
            else:
                output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")

            os.makedirs(output_dir, exist_ok=True)
            filename = f"agnes_t2v_{task_id[:12]}.mp4"
            filepath = os.path.join(output_dir, filename)

            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                with open(filepath, "wb") as f:
                    f.write(resp.read())

            print(f"[Agnes] Saved: {filepath}")
            return filepath

        except Exception as e:
            print(f"[Agnes] Download failed: {e}")
            return ""

    def _decode_video(self, filepath):
        """Decode video file into IMAGE tensor batch [N, H, W, C]."""
        cap = cv2.VideoCapture(filepath)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # BGR -> RGB, normalize to 0-1 float32
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(np.array(frame_rgb).astype(np.float32) / 255.0)
        cap.release()

        if not frames:
            return self._empty_image()

        # Stack into [N, H, W, C] tensor
        tensor = torch.from_numpy(np.stack(frames, axis=0))
        print(f"[Agnes] Decoded {len(frames)} frames, shape={tensor.shape}")
        return tensor

    def _extract_audio(self, filepath):
        """Extract audio from video file into VHS AUDIO format."""
        try:
            if HAS_VHS_AUDIO:
                return vhs_lazy_get_audio(filepath)

            ffmpeg_path = self._resolve_ffmpeg_path()
            if not ffmpeg_path:
                print("[Agnes] Audio extraction skipped: no ffmpeg available")
                return self._empty_audio()

            # -vn: skip video  -ac 2: force stereo  -ar 44100: known sample rate
            # -acodec pcm_f32le -f f32le: raw float32 little-endian output
            result = subprocess.run(
                [ffmpeg_path, "-i", filepath, "-vn", "-ac", "2", "-ar", "44100",
                 "-acodec", "pcm_f32le", "-f", "f32le", "-"],
                capture_output=True, timeout=30
            )
            if result.returncode != 0 or len(result.stdout) == 0:
                stderr_msg = result.stderr.decode("utf-8", errors="replace")[-200:]
                print(f"[Agnes] No audio track found (ffmpeg stderr: {stderr_msg})")
                return self._empty_audio()

            audio = torch.frombuffer(bytearray(result.stdout), dtype=torch.float32)

            sample_rate = 44100
            channels = 2

            # Reshape: [samples] -> [1, channels, num_samples]
            audio = audio.reshape((-1, channels)).transpose(0, 1).unsqueeze(0)

            print(f"[Agnes] Audio: {sample_rate}Hz, {channels}ch, {audio.shape[-1]} samples")
            return {'waveform': audio.contiguous(), 'sample_rate': sample_rate}

        except Exception as e:
            print(f"[Agnes] Audio extraction failed: {e}")
            return self._empty_audio()

    def _resolve_ffmpeg_path(self):
        if HAS_IMAGEIO_FFMPEG:
            try:
                return get_ffmpeg_exe()
            except Exception:
                pass
        return shutil.which("ffmpeg")

    def _empty_image(self):
        return torch.zeros(1, 64, 64, 3, dtype=torch.float32)

    def _empty_audio(self):
        return {'waveform': torch.zeros(1, 2, 1, dtype=torch.float32), 'sample_rate': 44100}
