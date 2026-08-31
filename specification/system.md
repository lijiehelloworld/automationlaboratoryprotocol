---
title: "系统"
description: "ALL 系统发现、能力清单、状态与事件接口"
---

系统模块提供连接后首先需要的公共信息，包括协议版本、服务身份、设备目录、四模块能力清单、运行状态和事件。

## 方法列表

| 方法 | 必须实现 | 需要权限 | 是否改变物理状态 |
| --- | --- | --- | --- |
| `system/discover` | 是 | `all:system:read` | 否 |
| `system/get_manifest` | 是 | `all:system:read` | 否 |
| `system/get_status` | 是 | `all:system:read` | 否 |
| `system/events/subscribe` | 支持事件时 | `all:system:read` | 否 |
| `system/events/poll` | 支持事件时 | `all:system:read` | 否 |
| `system/events/unsubscribe` | 支持事件时 | `all:system:read` | 否 |

## `system/discover`

### 功能

返回服务端支持的协议版本、远程端点、四模块支持状态和可见设备摘要。该方法不建立会话，不返回完整对象、操作或 Workflow 定义。

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "discover-1",
  "method": "system/discover",
  "params": {
    "preferred_versions": ["2026-08-31"],
    "if_revision": null
  },
  "_meta": {
    "all": {
      "protocolVersion": "2026-08-31",
      "requestId": "discover-1",
      "clientInfo": {
        "name": "laboratory-agent",
        "version": "1.0.0"
      }
    }
  }
}
```

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `preferred_versions` | `string[]` | 是 | 按客户端偏好降序排列；不得为空；日期格式 `YYYY-MM-DD` |
| `if_revision` | `integer \| null` | 否 | 大于或等于 `0`；用于复验发现目录缓存 |

### 完整响应

```json
{
  "jsonrpc": "2.0",
  "id": "discover-1",
  "result": {
    "resultType": "complete",
    "ttlMs": 60000,
    "cacheScope": "private",
    "revision": 12,
    "not_modified": false,
    "selected_version": "2026-08-31",
    "supported_versions": ["2026-08-31"],
    "endpoint": "https://lab.example.com/all",
    "modules": {
      "system": true,
      "objects": true,
      "operations": true,
      "workflows": true
    },
    "features": {
      "events": true,
      "operation_tasks": true,
      "input_required": true
    },
    "devices": [
      {
        "device_id": "device-001",
        "device_type": "automation_device",
        "display_name": "示例设备",
        "manifest_revision": 7
      }
    ]
  },
  "_meta": {
    "all": {
      "serverInfo": {
        "name": "laboratory-device-service",
        "version": "1.0.0"
      }
    }
  }
}
```

### 未修改响应

```json
{
  "jsonrpc": "2.0",
  "id": "discover-1",
  "result": {
    "resultType": "complete",
    "ttlMs": 60000,
    "cacheScope": "private",
    "revision": 12,
    "not_modified": true,
    "selected_version": "2026-08-31"
  }
}
```

只有 `if_revision` 与当前发现目录修订号相等时才允许省略目录正文。客户端权限变化时，即使目录内容看似相同，服务端也必须重新计算可见范围或使用身份隔离的缓存修订号。

### 响应字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `resultType` | `"complete"` | 是 | 固定值 |
| `ttlMs` | `integer` | 是 | 建议缓存毫秒数；大于或等于 `0` |
| `cacheScope` | `"private"` | 是 | 发现结果按身份隔离 |
| `revision` | `integer` | 是 | 当前发现目录修订号 |
| `not_modified` | `boolean` | 是 | 是否继续使用指定修订号缓存 |
| `selected_version` | `string` | 是 | 双方共同支持的最高优先版本 |
| `supported_versions` | `string[]` | 完整响应必填 | 服务端支持的版本，按新到旧排列 |
| `endpoint` | `string` | 完整响应必填 | 当前 ALL HTTPS 端点 |
| `modules` | `ModuleSupport` | 完整响应必填 | 四个模块是否可用；`system` 必须为 `true` |
| `features` | `FeatureSupport` | 完整响应必填 | 模块内可选交互能力 |
| `devices` | `DeviceSummary[]` | 完整响应必填 | 当前身份可见设备，按 `device_id` 排序 |

服务身份位于响应 `_meta.all.serverInfo`，只用于显示、日志和调试，不得用于授权。

## `system/get_manifest`

### 功能

返回一个设备在四模块中的完整能力定义。客户端不得根据设备名称或说明推测未声明能力。

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "method": "system/get_manifest",
  "params": {
    "device_id": "device-001",
    "if_revision": null
  },
  "_meta": {
    "all": {
      "protocolVersion": "2026-08-31",
      "requestId": "manifest-1",
      "clientInfo": {"name": "laboratory-agent", "version": "1.0.0"}
    }
  }
}
```

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `device_id` | `string` | 是 | 必须是当前身份通过 `system/discover` 可见的设备标识 |
| `if_revision` | `integer \| null` | 否 | 大于或等于 `0`；仅用于能力清单缓存复验 |

### 完整响应

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "result": {
    "resultType": "complete",
    "ttlMs": 60000,
    "cacheScope": "private",
    "revision": 7,
    "not_modified": false,
    "manifest": {
      "protocol_version": "2026-08-31",
      "device": {
        "device_id": "device-001",
        "device_type": "automation_device",
        "display_name": "示例设备",
        "description": "公开四模块能力的实验室设备。",
        "manufacturer": null,
        "model": null,
        "firmware_version": null
      },
      "revision": 7,
      "system": {
        "methods": [
          "system/discover",
          "system/get_manifest",
          "system/get_status",
          "system/events/subscribe",
          "system/events/poll",
          "system/events/unsubscribe"
        ],
        "events_supported": true
      },
      "objects": {
        "methods": ["objects/list", "objects/get", "objects/register", "objects/update"],
        "object_types": []
      },
      "operations": {
        "methods": [
          "operations/list",
          "operations/read",
          "operations/write",
          "operations/invoke",
          "operations/get",
          "operations/respond",
          "operations/cancel"
        ],
        "definitions": []
      },
      "workflows": {
        "methods": ["workflows/list", "workflows/get", "workflows/validate", "workflows/run"],
        "definitions": []
      }
    }
  }
}
```

不支持可选功能时，对应数组必须为空、布尔值必须为 `false`，不得省略整个四模块对象。四个模块之外的顶层能力对象不属于本规范。

### 能力清单字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol_version` | `string` | 是 | 能力清单适用的 ALL 日期版本 |
| `device` | `DeviceDescriptor` | 是 | 设备稳定身份和显示信息 |
| `revision` | `integer` | 是 | `manifest` 域修订号 |
| `system` | `SystemCapability` | 是 | 系统方法和事件能力 |
| `objects` | `ObjectCapability` | 是 | 对象方法和完整对象类型定义 |
| `operations` | `OperationCapability` | 是 | 操作方法和完整操作定义 |
| `workflows` | `WorkflowCapability` | 是 | Workflow 方法和完整模板定义 |

`device` 字段：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `device_id` | `string` | 是 | 服务端内稳定且唯一；必须与请求一致 |
| `device_type` | `string` | 是 | 稳定机器类型 |
| `display_name` | `string` | 是 | 面向人的名称，不用于能力判断 |
| `description` | `string` | 是 | 设备说明，不得包含调用指令 |
| `manufacturer` | `string \| null` | 是 | 制造商；未知时为 `null` |
| `model` | `string \| null` | 是 | 型号；未知时为 `null` |
| `firmware_version` | `string \| null` | 是 | 当前公开固件版本；未知时为 `null` |

方法数组必须按方法名升序排列，定义数组分别按 `object_type`、操作 `name`、Workflow `name + version` 排序。同一稳定主键不得重复。

对象类型遵守[对象类型定义](./objects#对象类型定义)，操作遵守[操作定义](./operations#操作定义)，Workflow 遵守[workflow-定义](./workflows#workflow-定义)。能力清单必须内联这些定义，客户端不依赖其他方法才能理解完整接口。

### 未修改响应

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "result": {
    "resultType": "complete",
    "ttlMs": 60000,
    "cacheScope": "private",
    "revision": 7,
    "not_modified": true
  }
}
```

`if_revision` 不等于当前修订号时必须返回完整清单，不得返回版本冲突。

### 修订规则

以下变化必须递增能力清单 `revision`：

- 设备身份或公开固件版本变化；
- 方法支持状态变化；
- 对象类型、操作定义或 Workflow 定义发生语义变化；
- 输入输出数据结构、权限范围、前置条件、效果或安全等级变化；
- 事件主题或长任务能力变化。

对象实例、设备当前状态、操作执行进度和 Workflow 运行进度变化不得递增能力清单修订号。

## `system/get_status`

返回设备公共运行状态，不返回对象目录或操作定义。

```json
{
  "jsonrpc": "2.0",
  "id": "status-1",
  "method": "system/get_status",
  "params": {
    "device_id": "device-001",
    "max_age_ms": 1000
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": "status-1",
  "result": {
    "resultType": "complete",
    "device_id": "device-001",
    "state": "idle",
    "health": "ok",
    "revision": 324,
    "observed_at": "2026-08-31T10:20:31.203+08:00",
    "expires_at": "2026-08-31T10:20:32.203+08:00",
    "active_operation_ids": [],
    "warnings": []
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `state` | `SystemState` | 是 | `offline`、`idle`、`busy`、`paused`、`error` 或 `unknown` |
| `health` | `SystemHealth` | 是 | `ok`、`degraded`、`fault` 或 `unknown` |
| `revision` | `integer` | 是 | 设备运行状态修订号 |
| `observed_at` | `string` | 是 | 带时区的 RFC 3339 时间 |
| `expires_at` | `string \| null` | 是 | 超过后必须重新读取；无缓存时为 `null` |
| `active_operation_ids` | `string[]` | 是 | 当前身份可见的活动操作任务 |
| `warnings` | `SystemWarning[]` | 是 | 结构化警告；无警告时为空数组 |

## 系统事件

事件是可选系统能力。远程连接使用显式订阅和轮询，不依赖长期连接或隐藏会话。

### `system/events/subscribe`

```json
{
  "jsonrpc": "2.0",
  "id": "event-sub-1",
  "method": "system/events/subscribe",
  "params": {
    "device_id": "device-001",
    "topics": ["system.status", "objects.changed", "operations.changed", "workflows.changed"],
    "after_cursor": null,
    "ttl_ms": 3600000
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": "event-sub-1",
  "result": {
    "resultType": "complete",
    "subscription_id": "sub-001",
    "topics": ["system.status", "objects.changed", "operations.changed", "workflows.changed"],
    "next_cursor": "cur-1000",
    "expires_at": "2026-08-31T11:20:31.203+08:00"
  }
}
```

### `system/events/poll`

```json
{
  "jsonrpc": "2.0",
  "id": "event-poll-1",
  "method": "system/events/poll",
  "params": {
    "subscription_id": "sub-001",
    "after_cursor": "cur-1000",
    "limit": 100,
    "wait_ms": 20000
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "id": "event-poll-1",
  "result": {
    "resultType": "complete",
    "events": [
      {
        "event_id": "evt-1001",
        "topic": "system.status",
        "device_id": "device-001",
        "revision": 325,
        "occurred_at": "2026-08-31T10:21:01.000+08:00",
        "data": {"state": "busy", "health": "ok"}
      }
    ],
    "next_cursor": "cur-1001",
    "has_more": false
  }
}
```

`limit` 必须在 `1..500`，`wait_ms` 必须在 `0..30000`。事件允许至少一次投递，客户端必须按 `event_id` 去重，并按每个设备的 `revision` 判断顺序。

### `system/events/unsubscribe`

```json
{
  "jsonrpc": "2.0",
  "id": "event-unsub-1",
  "method": "system/events/unsubscribe",
  "params": {"subscription_id": "sub-001"}
}
```

成功时返回：

```json
{
  "resultType": "complete",
  "unsubscribed": true
}
```

同一身份重复取消订阅必须返回相同成功结果。跨身份访问订阅必须返回 `PermissionDenied`。

## 正式类型定义

```typescript
interface DiscoverParams {
  preferred_versions: string[];
  if_revision?: number | null;
}

type DiscoverResult =
  | {
      resultType: "complete";
      ttlMs: number;
      cacheScope: "private";
      revision: number;
      not_modified: false;
      selected_version: string;
      supported_versions: string[];
      endpoint: string;
      modules: ModuleSupport;
      features: FeatureSupport;
      devices: DeviceSummary[];
    }
  | {
      resultType: "complete";
      ttlMs: number;
      cacheScope: "private";
      revision: number;
      not_modified: true;
      selected_version: string;
    };

interface GetManifestParams {
  device_id: string;
  if_revision?: number | null;
}

type GetManifestResult =
  | {
      resultType: "complete";
      ttlMs: number;
      cacheScope: "private";
      revision: number;
      not_modified: false;
      manifest: DeviceManifest;
    }
  | {
      resultType: "complete";
      ttlMs: number;
      cacheScope: "private";
      revision: number;
      not_modified: true;
    };

interface ModuleSupport {
  system: true;
  objects: boolean;
  operations: boolean;
  workflows: boolean;
}

interface FeatureSupport {
  events: boolean;
  operation_tasks: boolean;
  input_required: boolean;
}

interface DeviceSummary {
  device_id: string;
  device_type: string;
  display_name: string;
  manifest_revision: number;
}

interface DeviceManifest {
  protocol_version: string;
  device: DeviceDescriptor;
  revision: number;
  system: SystemCapability;
  objects: ObjectCapability;
  operations: OperationCapability;
  workflows: WorkflowCapability;
}

interface DeviceDescriptor {
  device_id: string;
  device_type: string;
  display_name: string;
  description: string;
  manufacturer: string | null;
  model: string | null;
  firmware_version: string | null;
}

interface SystemCapability {
  methods: string[];
  events_supported: boolean;
}

interface ObjectCapability {
  methods: string[];
  object_types: ObjectTypeDefinition[];
}

interface OperationCapability {
  methods: string[];
  definitions: OperationDefinition[];
}

interface WorkflowCapability {
  methods: string[];
  definitions: WorkflowDefinition[];
}

type SystemState = "offline" | "idle" | "busy" | "paused" | "error" | "unknown";
type SystemHealth = "ok" | "degraded" | "fault" | "unknown";

interface SystemWarning {
  code: string;
  message: string;
  recoverable: boolean;
}
```
