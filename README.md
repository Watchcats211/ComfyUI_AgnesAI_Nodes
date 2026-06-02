# ComfyUI_AgnesAI

Agnes.ai nodes and example workflows for ComfyUI.  
Agnes.ai 的 ComfyUI 节点与示例工作流仓库。

## Overview / 概览

This repository includes:  
本仓库包含：

- `Agnes_Config`
- `Agnes_Text2Image`
- `Agnes_Text2Video`
- `Agnes_ImageToURL`
- `Agnes_Image2Video`

It also ships example workflows for:  
同时附带以下示例工作流：

- text to image / 文生图
- text to video with in-app preview / 文生视频并在 ComfyUI 内预览
- local image to video with automatic upload and in-app preview / 本地图生视频并自动上传图片、在 ComfyUI 内预览

## Features / 功能

- Agnes image generation with `agnes-image-2.1-flash`  
  使用 `agnes-image-2.1-flash` 进行 Agnes 文生图
- Agnes video generation with `agnes-video-v2.0`  
  使用 `agnes-video-v2.0` 进行 Agnes 生视频
- ComfyUI-friendly video outputs: frame batch + audio + source URL  
  适配 ComfyUI 的视频输出：帧序列 + 音频 + 源视频 URL
- Preview-ready video workflows via `VHS_VideoCombine`  
  通过 `VHS_VideoCombine` 直接在 ComfyUI 里预览视频
- Local image to public URL conversion for Agnes image-to-video  
  支持把 ComfyUI 本地图片转成公网 URL，再交给 Agnes 图生视频

## Installation / 安装

```bash
cd ~/ComfyUI/custom_nodes
git clone <your-repo-url> ComfyUI_AgnesAI
```

Restart ComfyUI after cloning.  
克隆完成后，重启 ComfyUI。

## Configuration / 配置

Use `Agnes_Config` in your workflow.  
在工作流中使用 `Agnes_Config` 节点。

- `api_key`: your Agnes key  
  `api_key`：你的 Agnes API Key
- `base_url`: defaults to `https://apihub.agnes-ai.com/v1`  
  `base_url`：默认是 `https://apihub.agnes-ai.com/v1`

If you leave `api_key` blank, the node will try `AGNES_API_KEY` from the environment.  
如果把 `api_key` 留空，节点会尝试从环境变量 `AGNES_API_KEY` 读取。

## Included Workflows / 内置工作流

### `workflows/agnes_text2image_workflow.json`

- Minimal text-to-image example  
  最小文生图示例

### `workflows/agnes_text2video_workflow.json`

- Agnes text-to-video  
  Agnes 文生视频
- Saves the original Agnes mp4 into ComfyUI `output/`  
  会把 Agnes 原始 mp4 保存到 ComfyUI `output/` 目录
- Also returns a ComfyUI preview video via `VHS_VideoCombine`  
  同时通过 `VHS_VideoCombine` 返回 ComfyUI 内可播放预览

### `workflows/agnes_image2video_workflow.json`

- Load a local image in ComfyUI  
  在 ComfyUI 中载入本地图片
- Upload it through `Agnes_ImageToURL`  
  通过 `Agnes_ImageToURL` 自动上传
- Send the public URL to Agnes image-to-video  
  把公网图片 URL 交给 Agnes 图生视频接口
- Return a preview video in ComfyUI  
  在 ComfyUI 内返回可播放预览

## Example Media / 示例素材

### `examples/videos/text_to_video_original.mp4`

- Original Agnes text-to-video output saved into ComfyUI `output/`  
  Agnes 文生视频原始输出，来自 ComfyUI `output/`

### `examples/videos/text_to_video_comfy_preview.mp4`

- The corresponding ComfyUI in-app preview video produced through `VHS_VideoCombine`  
  对应的 ComfyUI 内预览视频，由 `VHS_VideoCombine` 生成

### `examples/videos/image_to_video_original.mp4`

- Original Agnes image-to-video output saved into ComfyUI `output/`  
  Agnes 图生视频原始输出，来自 ComfyUI `output/`

### `examples/videos/image_to_video_comfy_preview.mp4`

- The corresponding ComfyUI in-app preview video produced through `VHS_VideoCombine`  
  对应的 ComfyUI 内预览视频，由 `VHS_VideoCombine` 生成

## Image-to-Video Notes / 图生视频说明

Agnes image-to-video expects a public image URL.  
Agnes 图生视频接口要求输入公网可访问的图片 URL。

This repo includes `Agnes_ImageToURL`, which uploads a ComfyUI `IMAGE` to `storage.to` and returns a URL that Agnes can read.  
本仓库提供了 `Agnes_ImageToURL`，会把 ComfyUI 的 `IMAGE` 上传到 `storage.to`，再返回 Agnes 可读取的 URL。

The sample image at `examples/agnes_i2v_source.png` is only for reference. After importing the workflow, pick your own image in ComfyUI `LoadImage`.  
`examples/agnes_i2v_source.png` 只是示例图。导入工作流后，你可以在 ComfyUI 的 `LoadImage` 节点里换成自己的图片。

## Outputs / 输出

### `Agnes_Text2Image`

- `IMAGE`
- `STRING` url

### `Agnes_Text2Video`

- `IMAGE` frames / 帧序列
- `AUDIO`
- `STRING` url

### `Agnes_Image2Video`

- `IMAGE` frames / 帧序列
- `AUDIO`
- `STRING` url

## Dependencies / 依赖

This node relies on packages typically already present in a working ComfyUI install:  
这些依赖通常在正常可用的 ComfyUI 环境里已经存在：

- `torch`
- `numpy`
- `Pillow`
- `opencv-python`

Optional fallback for audio extraction:  
音频提取的可选兜底依赖：

- `imageio-ffmpeg`

For video preview workflows you also need:  
如果要使用视频预览工作流，还需要：

- `ComfyUI-VideoHelperSuite`

## Security / Release Workflow / 安全与发布流程

Before publishing to GitHub, run:  
发布到 GitHub 之前，建议先运行：

```bash
python3 scripts/sanitize_release.py --write .
python3 scripts/sanitize_release.py --check .
```

What it does:  
这个脚本会做：

- clears Agnes API keys from workflow JSON  
  清理工作流 JSON 中的 Agnes API key
- clears preview metadata that contains local paths  
  清理包含本机路径的预览元数据
- normalizes `LoadImage` placeholders  
  统一 `LoadImage` 的占位文件名
- scans the repo for likely secrets before release  
  在发布前扫描仓库中的疑似敏感信息

## Recommended Release Checklist / 推荐发布检查清单

1. Run the sanitize script in `--write` mode.  
   先运行 `--write` 模式做自动清理。
2. Run the sanitize script in `--check` mode.  
   再运行 `--check` 模式做检查。
3. Open the workflow JSONs and confirm `api_key` is blank.  
   打开工作流 JSON，确认 `api_key` 是空的。
4. Confirm no `sk-...` key remains anywhere in the repo.  
   确认仓库里不再残留任何 `sk-...` 密钥。
5. Then commit and push.  
   最后再提交并推送。

## API Docs / 官方文档

- [Agnes API Overview](https://agnes-ai.com/doc/overview)
