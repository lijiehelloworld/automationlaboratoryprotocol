---
title: "设备与能力发现"
description: "服务发现、设备清单与设备模型"
---

#### `server/discover`

所有服务端必须实现 `server/discover`。该方法不得移动硬件。

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

### 功能说明

所有服务端必须实现 `devices/get_manifest`，使客户端不依赖任何可选资源能力即可取得指定设备的完整能力清单。该接口只读取静态或低频变化的能力定义，不读取设备运行状态，也不得移动硬件或触发设备动作。

| 项目 | 规定 |
| --- | --- |
| 是否必须实现 | 是 |
| 是否需要可选扩展 | 否 |
| 是否可能触发设备动作 | 否 |
| 修订号域 | `manifest` |
| 缓存范围 | 必须为 `private` |

### 请求参数

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

| 参数 | 类型 | 必填 | 允许值与约束 | 说明 |
| --- | --- | --- | --- | --- |
| `device_id` | `string` | 是 | 非空；必须是 `server/discover` 返回的稳定设备标识 | 要读取的设备 |
| `if_revision` | `integer \| null` | 否 | 大于或等于 `0`；省略与 `null` 等价 | 客户端已经缓存的能力清单修订号 |

请求对象不得包含未声明字段。`if_revision` 仅用于缓存复验，不是并发写入条件：

- 省略或为 `null` 时，服务端必须返回完整能力清单；
- 等于当前能力清单修订号时，服务端可以返回未修改响应；
- 不等于当前能力清单修订号时，服务端必须返回当前完整能力清单，不得返回 `RevisionConflict`。

### 成功响应

以下为包含完整能力清单的成功响应。数组为空表示该设备没有声明对应能力，不代表字段可以省略。

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
        "device_kind": "composite",
        "display_name": "示例组合设备",
        "description": "由多个成员设备组成并对外提供统一能力的自动化设备节点。",
        "manufacturer": null,
        "model": null,
        "firmware_version": null,
        "members": [
          {"device_id": "member-001", "role": "motion"},
          {"device_id": "member-002", "role": "process"}
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
        "display_name": "示例设备智能体",
        "provider": "device-vendor",
        "version": "1.0.0",
        "modes": ["plan_only"],
        "capabilities": ["explain_device", "diagnose_state"],
        "allowed_action_scope": [],
        "workflow_scope": [],
        "management_scope": ["physical_resources:read"],
        "guidance_resources": [],
        "requires_human_approval": []
      }
    }
  }
}
```

### 未修改响应

只有 `if_revision` 与当前能力清单修订号完全相等时，服务端才可以返回 `not_modified=true`。此时必须省略 `manifest`。

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

响应顶层字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `resultType` | `"complete"` | 是 | 该接口只返回同步完成结果 |
| `ttlMs` | `integer` | 是 | 建议缓存时间，单位为毫秒；必须大于或等于 `0` |
| `cacheScope` | `"private"` | 是 | 能力清单按调用身份隔离，不得使用共享缓存 |
| `revision` | `integer` | 是 | 当前 `manifest` 域修订号；必须与完整响应中的 `manifest.revision` 相同 |
| `not_modified` | `boolean` | 是 | 是否可以继续使用指定修订号的本地缓存 |
| `manifest` | `DeviceManifest` | 条件必填 | `not_modified=false` 时必须存在；为 `true` 时必须省略 |

## 设备清单

每个设备必须具有稳定 `device_id` 和机器可读能力清单。

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

能力清单字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `protocol_version` | `string` | 是 | 能力清单对应的 ALP 日期版本 |
| `device` | `Device` | 是 | 设备身份和组成 |
| `revision` | `integer` | 是 | 能力清单域版本；能力、数据结构定义、约束或成员定义变化时必须递增 |
| `properties` | `PropertyDefinition[]` | 是 | [属性](./properties)定义；没有属性时为空数组 |
| `actions` | `ActionDefinition[]` | 是 | [动作](./actions)定义；没有动作时为空数组 |
| `physical_resource_types` | `PhysicalResourceTypeDefinition[]` | 是 | [物理资源](./physical-resources)类型定义；不适用时为空数组 |
| `transfer_points` | `TransferPointDefinition[]` | 是 | 物理资源进入或离开设备工作区的交接点；不适用时为空数组 |
| `workflows` | `WorkflowDefinition[]` | 是 | [工作流](../extensions/workflows)定义；不支持时为空数组 |
| `resources` | `ResourceDefinition[]` | 是 | [结果资源](../extensions/resources)定义；不适用时为空数组 |
| `constraints` | `ConstraintDefinition[]` | 是 | 可由服务端检查的结构化限制 |
| `device_agent` | `DeviceAgentDefinition \| null` | 是 | [设备智能体](../extensions/device-agent)定义；未提供时为 `null` |

### `Device` 对象

| 字段 | 类型 | 必填 | 允许值与约束 | 说明 |
| --- | --- | --- | --- | --- |
| `device_id` | `string` | 是 | 非空；在当前服务端内稳定且唯一 | 设备标识 |
| `device_type` | `string` | 是 | 非空 | 设备的机器可读类型 |
| `device_kind` | `"single" \| "composite"` | 是 | 固定枚举 | 单一设备或组合设备 |
| `display_name` | `string` | 是 | 非空 | 面向人的名称 |
| `description` | `string \| null` | 是 | — | 设备说明 |
| `manufacturer` | `string \| null` | 是 | — | 制造商 |
| `model` | `string \| null` | 是 | — | 型号 |
| `firmware_version` | `string \| null` | 是 | — | 固件版本 |
| `members` | `DeviceMember[]` | 是 | `single` 时必须为空；`composite` 时至少一项 | 组合设备成员 |

`DeviceMember` 包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `device_id` | `string` | 是 | 成员设备的稳定标识；不得等于父设备标识 |
| `role` | `string` | 是 | 成员在组合设备中的机器可读职责；非空 |

同一 `members` 数组中的 `device_id` 必须唯一。成员列表变化属于能力清单变化，必须递增能力清单修订号。

### 能力数组元素

能力数组必须按下表中的稳定主键升序排列，同一数组内主键不得重复：

| 类型 | 稳定主键 | 最低必需内容 |
| --- | --- | --- |
| `PropertyDefinition` | `path` | `path`、`title`、`description`、`schema`、`unit`、`access`、`source`、`freshness_ms`、`read_side_effect`、`constraint_ids` |
| `ActionDefinition` | `name` | `name`、`title`、`description`、`input_schema`、`output_schema`、`effects`、`preconditions`、`constraint_ids`、`execution_mode`、`result_confirmation`、`idempotent`、`timeout_ms` |
| `PhysicalResourceTypeDefinition` | `type` | `type`、`kind`、`name`、`state_schema`、`transferable`；其余字段按物理资源规范提供 |
| `TransferPointDefinition` | `transfer_point_id` | `transfer_point_id`、`workspace_path`、`directions`、`allowed_resource_types`、`physical_actors`、`confirmation_sources`、`capacity` |
| `WorkflowDefinition` | `name + version` | 完整工作流模板；字段和步骤规则由工作流规范定义 |
| `ResourceDefinition` | `uri` | `uri`、`name`、`description`、`mime_type`、`revision`、`digest`、`size_bytes`、`annotations` |
| `ConstraintDefinition` | `constraint_id` | `constraint_id`、`description`、`applies_to`、`expression`、`severity` |

`schema`、`input_schema`、`output_schema`、`state_schema` 和 `expression` 必须遵守[数据结构定义与数据校验](./base-protocol#数据结构定义与数据校验)规则。引用的约束标识、资源类型、动作、属性、工作流和资源 URI 必须能在同一能力清单中解析。

### `DeviceAgentDefinition` 对象

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `agent_id` | `string` | 是 | 当前设备内稳定且唯一的智能体标识 |
| `display_name` | `string` | 是 | 面向人的名称 |
| `provider` | `string` | 是 | 智能体提供方；不表示自动受信任 |
| `version` | `string` | 是 | 智能体实现版本 |
| `modes` | `DeviceAgentMode[]` | 是 | 至少包含 `plan_only` |
| `capabilities` | `string[]` | 是 | 智能体公开的机器可读能力 |
| `allowed_action_scope` | `string[]` | 是 | 可以规划或请求的动作名称，必须是 `actions` 的子集 |
| `workflow_scope` | `string[]` | 是 | 可以使用的工作流名称，必须能在 `workflows` 中解析 |
| `management_scope` | `string[]` | 是 | 可以请求的管理能力；实际权限仍取调用者权限与该范围的交集 |
| `guidance_resources` | `string[]` | 是 | 指导资源 URI，必须能通过已声明的资源能力读取 |
| `requires_human_approval` | `DeviceAgentMode[]` | 是 | 必须获得人工批准的模式，必须是 `modes` 的子集 |

`DeviceAgentMode` 允许 `plan_only`、`execute_workflow` 和 `execute_experiment`。能力清单不得包含凭据、模型密钥、内部网络端点或供应商私有配置。

### 正式类型定义

下列 TypeScript 定义是本接口的结构约束。被引用的能力定义类型必须同时满足各自章节的字段和语义要求。

```typescript
type JsonSchema = Record<string, unknown>;

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

interface DeviceManifest {
  protocol_version: string;
  device: Device;
  revision: number;
  properties: PropertyDefinition[];
  actions: ActionDefinition[];
  physical_resource_types: PhysicalResourceTypeDefinition[];
  transfer_points: TransferPointDefinition[];
  workflows: WorkflowDefinition[];
  resources: ResourceDefinition[];
  constraints: ConstraintDefinition[];
  device_agent: DeviceAgentDefinition | null;
}

interface Device {
  device_id: string;
  device_type: string;
  device_kind: "single" | "composite";
  display_name: string;
  description: string | null;
  manufacturer: string | null;
  model: string | null;
  firmware_version: string | null;
  members: DeviceMember[];
}

interface DeviceMember {
  device_id: string;
  role: string;
}

interface PropertyDefinition {
  path: string;
  title: string;
  description: string;
  schema: JsonSchema;
  unit: string | null;
  access: Array<"read" | "write">;
  source: string;
  freshness_ms: number | null;
  read_side_effect: "none" | "sensor_acquisition";
  constraint_ids: string[];
}

interface ActionDefinition {
  name: string;
  title: string;
  description: string;
  input_schema: JsonSchema;
  output_schema: JsonSchema;
  effects: string[];
  preconditions: ConditionExpression[];
  constraint_ids: string[];
  execution_mode: "atomic" | "orchestrated" | "device_program";
  result_confirmation: "required" | "recommended" | "not_required";
  idempotent: boolean;
  timeout_ms: number;
}

interface ConditionExpression {
  path?: string;
  path_template?: string;
  operator: "eq" | "ne" | "lt" | "lte" | "gt" | "gte" | "in" | "contains" | "exists";
  value?: unknown;
}

interface PhysicalResourceTypeDefinition {
  type: string;
  kind: "work_object" | "device_supply";
  name: string;
  description?: string;
  state_schema: JsonSchema;
  metadata_schema?: JsonSchema;
  allowed_locations?: string[];
  transferable: boolean;
}

interface TransferPointDefinition {
  transfer_point_id: string;
  workspace_path: string;
  directions: Array<"ingress" | "egress">;
  allowed_resource_types: string[];
  physical_actors: Array<"human" | "robot" | "device_agent_controlled_robot">;
  confirmation_sources: Array<"operator_confirmed" | "vision" | "device_readback">;
  capacity: number;
}

interface ResourceDefinition {
  uri: string;
  name: string;
  description: string;
  mime_type: string;
  revision: number;
  digest: string;
  size_bytes: number;
  annotations: {
    read_only: boolean;
    moves_hardware: boolean;
  };
}

interface ConstraintDefinition {
  constraint_id: string;
  description: string;
  applies_to: string[];
  expression: ConditionExpression;
  severity: "error" | "warning";
}

type DeviceAgentMode = "plan_only" | "execute_workflow" | "execute_experiment";

interface DeviceAgentDefinition {
  agent_id: string;
  display_name: string;
  provider: string;
  version: string;
  modes: DeviceAgentMode[];
  capabilities: string[];
  allowed_action_scope: string[];
  workflow_scope: string[];
  management_scope: string[];
  guidance_resources: string[];
  requires_human_approval: DeviceAgentMode[];
}

interface WorkflowDefinition extends Record<string, unknown> {
  name: string;
  version: string;
  revision: number;
  template_digest: string;
}
```

### 错误响应

该接口在返回错误时使用 JSON-RPC `error`，不返回部分能力清单。

| 情况 | 编码 | 名称 | 是否可恢复 | 处理方式 |
| --- | --- | --- | --- | --- |
| 参数缺失、类型错误、负修订号或未知字段 | `-32602` | `InvalidParams` | 是 | 修正请求参数 |
| `device_id` 不存在或调用者不可见 | `-32052` | `DeviceNotFound` | 否 | 重新调用 `server/discover` |
| 请求的协议日期版本不受支持 | `-32050` | `UnsupportedProtocolVersion` | 是 | 从 `supported_versions` 选择双方共同支持的最新版本 |
| 调用身份无权读取该设备能力清单 | `-32054` | `PermissionDenied` | 否 | 使用获得授权的身份重新请求 |

设备不存在：

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "error": {
    "code": -32052,
    "message": "未找到指定设备",
    "data": {
      "name": "DeviceNotFound",
      "recoverable": false,
      "device_id": "device-unknown",
      "suggested_action": "重新调用 server/discover"
    }
  }
}
```

参数错误：

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "error": {
    "code": -32602,
    "message": "请求参数无效",
    "data": {
      "name": "InvalidParams",
      "recoverable": true,
      "field": "if_revision",
      "reason": "必须是大于或等于 0 的整数或 null"
    }
  }
}
```

协议版本不受支持：

```json
{
  "jsonrpc": "2.0",
  "id": "manifest-1",
  "error": {
    "code": -32050,
    "message": "不支持请求的协议版本",
    "data": {
      "name": "UnsupportedProtocolVersion",
      "recoverable": true,
      "requested_version": "2026-07-28",
      "supported_versions": ["2026-08-31"],
      "suggested_action": "使用双方共同支持的最新协议版本"
    }
  }
}
```

`if_revision` 与当前能力清单修订号不同不是错误。`RevisionConflict` 只用于有并发控制语义的写入或执行请求，不得用于本接口的缓存复验。

### 一致性要求

- 相同调用身份、相同设备和相同修订号必须得到语义相同的能力清单；数组顺序必须稳定。
- `result.revision` 必须与 `manifest.revision` 相同。
- 属性、动作、物理资源类型、交接点、工作流、资源、约束、设备成员或设备智能体定义发生任何语义变化时，必须递增 `manifest.revision`。
- 仅运行状态、资源实例余量、当前位置或操作任务变化时，不得递增 `manifest.revision`；这些变化属于其他修订号域。
- 服务端必须在发送前校验全部内部引用；不得返回指向清单外未知定义的悬空引用。
- 能力清单不得包含设备凭据、访问令牌、私钥、内部串口参数或供应商私有端点。
