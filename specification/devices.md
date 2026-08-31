---
title: "设备与能力发现"
description: "服务发现、设备清单与设备模型"
---

#### `server/discover`

所有 Server MUST 实现 `server/discover`。该方法 MUST NOT 移动硬件。

请求：

```json
{
  "jsonrpc": "2.0",
  "id": "discover-1",
  "method": "server/discover",
  "params": {}
}
```

响应：

```json
{
  "jsonrpc": "2.0",
  "id": "discover-1",
  "result": {
    "resultType": "complete",
    "ttlMs": 60000,
    "cacheScope": "private",
    "revision": 12,
    "protocolVersions": ["2026-08-31"],
    "serverInfo": {
      "name": "automation-device-gateway",
      "version": "1.0.0"
    },
    "capabilities": {
      "read": true,
      "write": true,
      "invoke": true,
      "physicalResources": true,
      "transfers": true,
      "workflows": true,
      "resources": true,
      "operations": true,
      "events": true,
      "deviceAgent": true,
      "extensions": {}
    },
    "devices": [
      {
        "device_id": "device-001",
        "manifest_uri": "alp://device-001/manifest"
      }
    ]
  }
}
```

#### `devices/get_manifest`

所有 Server MUST 实现 `devices/get_manifest`，使 Client 不依赖任何可选资源能力即可取得设备 Manifest：

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "method": "devices/get_manifest",
  "params": {
    "device_id": "device-001",
    "if_revision": null
  }
}
```

响应 MUST 包含 `resultType`、`ttlMs`、`cacheScope`、Manifest `revision` 和完整 `manifest`。如果 `if_revision` 与当前 Manifest revision 相同，Server MAY 返回 `not_modified=true` 而省略 Manifest 正文。该方法 MUST NOT 移动硬件。

## 设备清单

每个设备 MUST 具有稳定 `device_id` 和机器可读 Manifest。

```json
{
  "protocol_version": "2026-08-31",
  "device": {
    "device_id": "device-001",
    "device_type": "automation_device",
    "device_kind": "composite",
    "display_name": "示例组合设备",
    "description": "由多个成员设备组成并对外提供统一能力的自动化设备节点。",
    "manufacturer": null,
    "model": null,
    "firmware_version": null,
    "members": [
      {"device_id": "member-001", "role": "motion"},
      {"device_id": "member-002", "role": "process"},
      {"device_id": "member-003", "role": "handling"}
    ]
  },
  "revision": 7,
  "properties": [],
  "actions": [],
  "physical_resource_types": [],
  "transfer_points": [],
  "workflows": [],
  "resources": [],
  "constraints": [],
  "device_agent": {
    "agent_id": "device-001-agent",
    "definition_uri": "alp://device-001/device-agent"
  }
}
```

Manifest 字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `protocol_version` | 是 | Manifest 对应的协议版本 |
| `device` | 是 | 设备身份、`single/composite` 类型和可选成员列表 |
| `revision` | 是 | Manifest 域版本；能力、Schema、约束或成员定义变化时递增 |
| `properties` | 是 | 状态和可写属性定义 |
| `actions` | 是 | 可执行动作定义；只读设备可以为空 |
| `physical_resource_types` | 是 | `work_object` 与 `device_supply` 类型定义；不适用时为空 |
| `transfer_points` | 是 | 物理资源进入或离开设备工作区的边界；不适用时为空 |
| `workflows` | 是 | 可选 Workflow；不支持时为空数组 |
| `resources` | 是 | 资源定义；不适用时为空 |
| `constraints` | 是 | 机器可校验的限制 |
| `device_agent` | 是 | 单设备智能体说明；未提供时为 `null` |
