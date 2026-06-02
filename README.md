# ComfyUI_AgnesAI

Agnes.ai nodes and example workflows for ComfyUI.

This repository includes:

- `Agnes_Config`
- `Agnes_Text2Image`
- `Agnes_Text2Video`
- `Agnes_ImageToURL`
- `Agnes_Image2Video`

It also ships example workflows for:

- text to image
- text to video with in-app preview
- local image to video with automatic image upload and in-app preview

## Features

- Agnes image generation with `agnes-image-2.1-flash`
- Agnes video generation with `agnes-video-v2.0`
- ComfyUI-friendly video outputs: frame batch + audio + source URL
- Preview-ready video workflows via `VHS_VideoCombine`
- Local image to public URL conversion for Agnes image-to-video

## Installation

```bash
cd ~/ComfyUI/custom_nodes
git clone <your-repo-url> ComfyUI_AgnesAI
```

Restart ComfyUI after cloning.

## Configuration

Use `Agnes_Config` in your workflow.

- `api_key`: your Agnes key
- `base_url`: defaults to `https://apihub.agnes-ai.com/v1`

If you leave `api_key` blank, the node will try `AGNES_API_KEY` from the environment.

## Included Workflows

`workflows/agnes_text2image_workflow.json`

- Minimal text-to-image example

`workflows/agnes_text2video_workflow.json`

- Agnes text-to-video
- Saves the original Agnes mp4 into ComfyUI `output/`
- Also returns a ComfyUI preview video via `VHS_VideoCombine`

`workflows/agnes_image2video_workflow.json`

- Load a local image in ComfyUI
- Upload it through `Agnes_ImageToURL`
- Send the public URL to Agnes image-to-video
- Return a preview video in ComfyUI

## Included Example Media

`examples/videos/text_to_video_original.mp4`

- Original Agnes text-to-video output saved into ComfyUI `output/`

`examples/videos/text_to_video_comfy_preview.mp4`

- The corresponding ComfyUI in-app preview video produced through `VHS_VideoCombine`

`examples/videos/image_to_video_original.mp4`

- Original Agnes image-to-video output saved into ComfyUI `output/`

`examples/videos/image_to_video_comfy_preview.mp4`

- The corresponding ComfyUI in-app preview video produced through `VHS_VideoCombine`

## Image-to-Video Notes

Agnes image-to-video expects a public image URL.

This repo includes `Agnes_ImageToURL`, which uploads a ComfyUI `IMAGE` to `storage.to` and returns a URL that Agnes can read.

The sample image at `examples/agnes_i2v_source.png` is only for reference. After importing the workflow, pick your own image in ComfyUI `LoadImage`.

## Outputs

`Agnes_Text2Image`

- `IMAGE`
- `STRING` url

`Agnes_Text2Video`

- `IMAGE` frames
- `AUDIO`
- `STRING` url

`Agnes_Image2Video`

- `IMAGE` frames
- `AUDIO`
- `STRING` url

## Dependencies

This node relies on packages typically already present in a working ComfyUI install:

- `torch`
- `numpy`
- `Pillow`
- `opencv-python`

Optional fallback for audio extraction:

- `imageio-ffmpeg`

For video preview workflows you also need:

- `ComfyUI-VideoHelperSuite`

## Security / Release Workflow

Before publishing to GitHub, run:

```bash
python3 scripts/sanitize_release.py --write .
python3 scripts/sanitize_release.py --check .
```

What it does:

- clears Agnes API keys from workflow JSON
- clears preview metadata that contains local paths
- normalizes `LoadImage` placeholders
- scans the repo for likely secrets before release

## Recommended GitHub Release Checklist

1. Run the sanitize script in `--write` mode.
2. Run the sanitize script in `--check` mode.
3. Open the workflow JSONs and confirm `api_key` is blank.
4. Confirm no `sk-...` key remains anywhere in the repo.
5. Then commit and push.

## API Docs

- [Agnes API Overview](https://agnes-ai.com/doc/overview)
