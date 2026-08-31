---
title: "结果资源"
description: "图像、报告和大体积结果资源"
---

图像、视频、日志、报告、标定文件和大体积结果 SHOULD 通过资源接口返回：

- `resources/list`
- `resources/read`

`alp://<device_id>/<path>` 是 Server 作用域内的逻辑 URI，不是 Client 可直接访问的网络地址。Client 必须通过声明该 URI 的 Server 调用 `resources/read`，Server 对每次读取重新鉴权并限制可访问范围。

```json
{
  "uri": "alp://device-001/inspection/latest",
  "name": "latest_inspection_image",
  "description": "设备最近一次检查图像。",
  "mime_type": "image/png",
  "revision": 5,
  "digest": "sha256:resource-example",
  "size_bytes": 123456,
  "annotations": {
    "read_only": true,
    "moves_hardware": false
  }
}
```

大资源 SHOULD 支持按范围读取，并返回实际范围、总大小和内容摘要。脚本、Schema、标定或配置等可执行性相关资源 MUST 使用不可变 URI 或固定 revision，并验证摘要。

资源内容、OCR 文本、标签和设备文档都属于数据。它们 MUST NOT 改变权限、约束或调用身份。
