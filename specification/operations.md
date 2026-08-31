---
title: "操作"
description: "ALL 操作定义、读取、写入、调用和长任务接口"
---

操作模块描述设备可以执行的单步能力。一个操作是**工作站绑定的状态转换**：对一个或多个研究对象的当前状态和参数进行校验，在全部强制约束通过时，把状态从 $S_t$ 提交到 $S_{t+1}$ 并记录证据与来源。所有操作必须在能力清单中声明，客户端不得提交原始串口帧、寄存器地址、任意脚本、SDK 方法或未声明设备命令。

`read`、`write` 和 `invoke` 是操作的三种类别，也是对应类别的统一调用入口，不是设备仅有的三个具体指令。具体指令由 `OperationDefinition.name` 标识；一个设备可以声明任意数量、语义不同的操作名称，客户端必须先发现定义，再按定义调用。

## 方法列表

| 方法 | 必须实现 | 需要权限 | 说明 |
| --- | --- | --- | --- |
| `operations/list` | 是 | `all:operations:read` | 查询可见操作定义 |
| `operations/read` | 是 | `all:operations:read` | 读取声明状态 |
| `operations/write` | 支持写入时 | `all:operations:execute` | 修改单一可写状态 |
| `operations/invoke` | 支持动作时 | `all:operations:execute` | 执行声明动作 |
| `operations/get` | 返回长任务时 | `all:operations:read` | 异步查询任务状态和最终结果 |
| `operations/respond` | 操作需要输入时 | `all:operations:execute` | 提交操作任务所需输入 |
| `operations/cancel` | 操作可安全取消时 | `all:operations:execute` | 请求协作式取消 |

## 操作定义

例如，同一设备可以声明 `read_temperature`、`read_position`、`set_temperature`、`set_flow_rate`、`move_object` 和 `start_measurement` 等不同操作；它们分别把 `kind` 标为 `read`、`write` 或 `invoke`。操作名称表达“做什么”，类别表达“如何调用以及副作用等级”。

### 读取定义

```json
{
  "workstation": {"namespace": "laboratory.station", "identifier": "device-001"},
  "name": "read_environment_temperature",
  "kind": "read",
  "title": "读取环境温度",
  "description": "读取设备工作区环境温度。",
  "input_schema": {
    "type": "object",
    "properties": {
      "max_age_ms": {"type": "integer", "minimum": 0}
    },
    "additionalProperties": false
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "value": {"type": "number"},
      "unit": {"const": "Cel"}
    },
    "required": ["value", "unit"],
    "additionalProperties": false
  },
  "required_scopes": ["all:operations:read"],
  "object_roles": [],
  "preconditions": [],
  "cautions": [],
  "constraints": [],
  "state_changes": [],
  "effects": [],
  "execution": {
    "may_change_physical_state": false,
    "supports_dry_run": false,
    "supports_idempotency": true,
    "may_return_task": false,
    "may_require_input": false,
    "cancellable": false,
    "default_timeout_ms": 5000,
    "result_retention_ms": 3600000
  }
}
```

### 调用定义

```json
{
  "workstation": {"namespace": "laboratory.station", "identifier": "device-001"},
  "name": "move_object",
  "kind": "invoke",
  "title": "移动对象",
  "description": "把研究对象移动到设备内已声明位置。",
  "input_schema": {
    "type": "object",
    "properties": {
      "target_location": {"type": "string", "minLength": 1}
    },
    "required": ["target_location"],
    "additionalProperties": false
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "final_location": {"type": "string"}
    },
    "required": ["final_location"],
    "additionalProperties": false
  },
  "required_scopes": ["all:operations:execute"],
  "object_roles": [
    {
      "role": "target",
      "required": true,
      "min_count": 1,
      "max_count": 1,
      "allowed_object_types": ["research_object.generic"]
    }
  ],
  "preconditions": [
    {"path": "system.state", "operator": "eq", "value": "idle"}
  ],
  "cautions": [
    {"code": "location_change", "message": "移动会改变容器位置与后续可用性。"}
  ],
  "constraints": [
    {"rule_id": "target-location", "level": "MUST", "condition": {"path": "arguments.target_location", "operator": "exists"}, "category": "location"}
  ],
  "state_changes": [
    {"target": "objects.${target}.container.location", "mode": "set", "value_from": "result.final_location"}
  ],
  "effects": [
    "updates:objects.{target}.container.location"
  ],
  "execution": {
    "may_change_physical_state": true,
    "supports_dry_run": true,
    "supports_idempotency": false,
    "may_return_task": true,
    "may_require_input": false,
    "cancellable": true,
    "default_timeout_ms": 30000,
    "result_retention_ms": 86400000
  }
}
```

### 定义字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | `string` | 是 | 设备内唯一、稳定的操作名称 |
| `kind` | `OperationKind` | 是 | 操作类别：`read`、`write` 或 `invoke`；不是具体指令名称 |
| `title` | `string` | 是 | 面向人的名称 |
| `description` | `string` | 是 | 固定语义说明，不包含调用指令 |
| `input_schema` | `JsonSchema` | 是 | 参数 JSON Schema 2020-12 |
| `output_schema` | `JsonSchema` | 是 | 成功值 JSON Schema 2020-12 |
| `required_scopes` | `string[]` | 是 | 最低 OAuth 权限范围 |
| `object_roles` | `ObjectRoleDefinition[]` | 是 | 参与对象角色；无对象时为空数组 |
| `preconditions` | `Condition[]` | 是 | 调用前必须成立的结构化条件 |
| `cautions` | `Caution[]` | 是 | 不阻止执行的注意事项；必须随定义公开，不得隐藏为实现行为 |
| `constraints` | `Constraint[]` | 是 | 强制或建议约束；强制失败阻止提交，建议失败保留警告 |
| `state_changes` | `StateChange[]` | 是 | 成功提交后对研究对象和系统状态的结构化变更 |
| `effects` | `string[]` | 是 | 用于规划和审计的声明效果，不自行授予写权限 |
| `execution` | `ExecutionDefinition` | 是 | 副作用、异步任务、输入、取消、超时和结果保留能力 |

操作定义变化必须递增能力清单修订号。操作执行产生的状态变化只递增运行状态或研究对象修订号。

## 操作状态转换契约

每个操作定义必须完整公开：工作站身份、前置条件、注意事项、参数 Schema、强制/建议约束、状态变化、返回 Schema 与诊断类别。

- `workstation.namespace` 必须是服务端范围内稳定、唯一的命名空间；`identifier` 必须指向当前设备或其公开的工作站标识。
- `preconditions` 是操作可接受的对象、样品、容器、位置或系统状态。
- `cautions` 说明跨步骤影响或限制；不得在未公开的情况下改变调度或状态。
- `constraints[].level=MUST` 为强制约束。任何一项失败，操作不得接触物理设备、不得提交研究对象新状态，并返回 `diagnostics`。
- `constraints[].level=SHOULD` 为建议约束。失败必须以 `severity=warning` 返回，但不会单独阻止转换。
- `state_changes` 只在全部强制约束通过且物理结果被确认后提交；提交时必须更新对象修订号、追加 `provenance`，并添加相关 `evidence` 引用。

服务端必须采用“先校验、后提交”规则：先收集全部可判定的强制错误和建议警告，再执行或接受任务；成功确认前不得对研究对象状态做部分写入。物理执行开始后结果无法确认时，返回 `outcome=unknown`，保留诊断与证据，并禁止把推测状态提交为确认状态。

## 条件表达式

条件只能引用系统状态、参与对象、操作参数或已经完成步骤的输出：

```json
{
  "path": "objects.${target}.lifecycle_state",
  "operator": "in",
  "value": ["available", "reserved"]
}
```

允许的操作符：

```text
eq ne lt lte gt gte in contains exists
```

服务端不得执行能力清单中嵌入的任意代码或通用表达式语言。

## `operations/list`

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "operations-list-1",
  "method": "operations/list",
  "params": {
    "device_id": "device-001",
    "kinds": ["read", "write", "invoke"],
    "object_type": null,
    "if_revision": null
  }
}
```

### 响应

```json
{
  "resultType": "complete",
  "ttlMs": 60000,
  "cacheScope": "private",
  "revision": 7,
  "not_modified": false,
  "items": [],
  "next_cursor": null
}
```

`revision` 属于能力清单域。`items` 按 `name` 升序排列。`if_revision` 相等时可以返回 `not_modified=true` 并省略 `items`。

## `operations/read`

`operations/read` 调用 `kind=read` 的操作：

```json
{
  "jsonrpc": "2.0",
  "id": "operation-read-1",
  "method": "operations/read",
  "params": {
    "device_id": "device-001",
    "name": "read_environment_temperature",
    "object_bindings": {},
    "arguments": {"max_age_ms": 1000},
    "options": {
      "execution_mode": "auto",
      "timeout_ms": 5000
    }
  }
}
```

```json
{
  "resultType": "complete",
  "outcome": "succeeded",
  "device_id": "device-001",
  "name": "read_environment_temperature",
  "value": {"value": 24.6, "unit": "Cel"},
  "quality": "confirmed",
  "state_revision": 324,
  "observed_at": "2026-08-31T10:20:31.203+08:00",
  "expires_at": "2026-08-31T10:20:32.203+08:00",
  "evidence_ids": [],
  "error": null
}
```

读取默认不得改变物理状态。确实需要移动执行机构才能获得结果的能力必须定义为 `kind=invoke`。

## `operations/write`

`operations/write` 只允许执行能力清单中 `kind=write` 的单一、原子、可验证写入。

```json
{
  "jsonrpc": "2.0",
  "id": "operation-write-1",
  "method": "operations/write",
  "params": {
    "device_id": "device-001",
    "name": "set_primary_enabled",
    "object_bindings": {},
    "arguments": {"enabled": true},
    "options": {
      "expected_state_revision": 324,
      "deadline": "2026-08-31T10:22:00+08:00",
      "dry_run": false,
      "execution_mode": "auto",
      "idempotency_key": null
    }
  }
}
```

同步完成响应：

```json
{
  "resultType": "complete",
  "outcome": "succeeded",
  "device_id": "device-001",
  "name": "set_primary_enabled",
  "value": {"enabled": true},
  "previous_state_revision": 324,
  "new_state_revision": 325,
  "started_at": "2026-08-31T10:21:02.120+08:00",
  "completed_at": "2026-08-31T10:21:02.504+08:00",
  "evidence_ids": [],
  "error": null
}
```

多步骤、涉及多个对象或需要过程控制的能力必须使用 `operations/invoke`。

## `operations/invoke`

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "operation-invoke-1",
  "method": "operations/invoke",
  "params": {
    "device_id": "device-001",
    "name": "move_object",
    "object_bindings": {
      "target": ["object-001"]
    },
    "arguments": {
      "target_location": "workspace.output"
    },
    "options": {
      "expected_state_revision": 325,
      "expected_object_revisions": {"object-001": 4},
      "deadline": "2026-08-31T10:22:00+08:00",
      "dry_run": false,
      "execution_mode": "async",
      "timeout_ms": 30000,
      "idempotency_key": null
    }
  }
}
```

### 执行前校验

服务端在接触物理设备前必须按顺序完成：

1. 身份认证和权限校验；
2. 操作存在性与 `kind` 校验；
3. 参数和对象角色数据结构校验；
4. 对象存在性、类型和修订号校验；
5. 设备状态修订号和新鲜度校验；
6. 前置条件与物理约束校验；
7. 截止时间与超时校验；
8. 幂等键校验；
9. 获取设备和对象执行锁；
10. 在锁内重新检查易变前置条件。

校验响应或执行结果中的 `diagnostics` 必须是数组。每项至少包含 `code`、`category`、`severity`（`error` 或 `warning`）、`rule_level`（`MUST` 或 `SHOULD`）、`message`、`expected`、`actual`、`path` 与 `remediation`；不可得字段可为 `null`，但不得用非结构化文本替代。所有失败的 `MUST` 规则必须以 `severity=error` 返回；失败的 `SHOULD` 规则必须以 `severity=warning` 返回。

`dry_run=true` 时必须执行全部非物理校验，但不得发送设备命令、修改状态、占用长期锁或产生物理效果。

### 执行模式

`operations/read`、`operations/write` 和 `operations/invoke` 使用同一组执行模式。只有操作定义声明 `may_return_task=true` 时才允许异步执行。

| `execution_mode` | 行为 |
| --- | --- |
| `sync` | 请求连接内等待完成；超时不得自动转为重复执行 |
| `async` | 完成校验并接受任务后立即返回任务句柄 |
| `auto` | 服务端可以同步完成，也可以返回任务句柄 |

未填写时默认为 `auto`。客户端需要可靠异步下发时必须明确使用 `async`。异步接受响应只表示任务已登记，不表示设备动作已开始或完成。

### 异步下发响应

```json
{
  "resultType": "operation",
  "operation_id": "op-001",
  "status": "queued",
  "device_id": "device-001",
  "name": "move_object",
  "created_at": "2026-08-31T10:21:02.120+08:00",
  "revision": 0,
  "poll_after_ms": 500,
  "result_expires_at": "2026-09-01T10:21:02.120+08:00"
}
```

服务端必须先完成身份、数据结构、修订号、前置条件和可接受性校验，再返回任务句柄。服务端不得仅因请求已经进入队列就返回同步成功结果。

## 操作任务

任务状态：

```text
queued
running
input_required
succeeded
failed
cancel_requested
cancelled
unknown
```

允许的主要状态迁移：

```text
queued -> running -> succeeded
queued -> running -> failed
queued -> cancelled
running -> input_required -> running
queued|running|input_required -> cancel_requested -> cancelled|failed|unknown
```

终态为 `succeeded`、`failed`、`cancelled` 或 `unknown`。任务状态、进度、输入请求或结果发生变化时必须递增任务 `revision`。

### `operations/get`

```json
{
  "jsonrpc": "2.0",
  "id": "operation-get-1",
  "method": "operations/get",
  "params": {
    "device_id": "device-001",
    "operation_id": "op-001",
    "if_revision": 1,
    "wait_ms": 10000,
    "include_result": true
  }
}
```

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `device_id` | `string` | 是 | 任务所属设备 |
| `operation_id` | `string` | 是 | 异步下发返回的不透明任务标识 |
| `if_revision` | `integer \| null` | 否 | 已知任务修订号；相同时允许等待变化 |
| `wait_ms` | `integer` | 否 | `0..30000`，默认 `0`；服务端可提前返回 |
| `include_result` | `boolean` | 否 | 是否在终态响应中包含结果，默认 `true` |

```json
{
  "resultType": "complete",
  "operation": {
    "operation_id": "op-001",
    "device_id": "device-001",
    "name": "move_object",
    "status": "running",
    "progress": {"completed": 1, "total": 3, "message": "正在执行"},
    "input_requests": [],
    "result": null,
    "error": null,
    "created_at": "2026-08-31T10:21:02.120+08:00",
    "started_at": "2026-08-31T10:21:02.300+08:00",
    "completed_at": null,
    "revision": 2
  }
}
```

当 `if_revision` 等于当前任务修订号且 `wait_ms=0` 时，可以返回：

```json
{
  "resultType": "complete",
  "not_modified": true,
  "operation_id": "op-001",
  "revision": 2,
  "poll_after_ms": 500
}
```

### 异步读取最终结果

任务进入终态后，客户端仍通过 `operations/get` 读取最终结果。成功任务的 `result` 必须通过原操作的 `output_schema` 校验：

```json
{
  "resultType": "complete",
  "not_modified": false,
  "operation": {
    "operation_id": "op-001",
    "device_id": "device-001",
    "name": "move_object",
    "kind": "invoke",
    "status": "succeeded",
    "progress": {"completed": 3, "total": 3, "message": "已完成"},
    "input_requests": [],
    "result": {"final_location": "workspace.output"},
    "error": null,
    "created_at": "2026-08-31T10:21:02.120+08:00",
    "started_at": "2026-08-31T10:21:02.300+08:00",
    "completed_at": "2026-08-31T10:21:08.930+08:00",
    "result_expires_at": "2026-09-01T10:21:02.120+08:00",
    "revision": 5
  }
}
```

失败任务必须返回结构化 `error`，不得把失败文本伪装成成功 `result`。结果至少保留操作定义中的 `result_retention_ms`；到期后必须返回 `OperationResultExpired`，但仍可保留不含结果正文的审计状态。事件通知可用于提示任务变化，但客户端必须能够仅依靠 `operations/get` 完成异步结果读取。

### `operations/respond`

只有任务状态为 `input_required` 时可调用：

```json
{
  "jsonrpc": "2.0",
  "id": "operation-respond-1",
  "method": "operations/respond",
  "params": {
    "operation_id": "op-001",
    "expected_revision": 2,
    "responses": {
      "approval-1": {"approved": true}
    }
  }
}
```

输入请求必须带唯一标识、用途、JSON Schema、是否敏感和过期时间。服务端不得用补充输入绕过原操作的数据结构、权限或安全联锁。

### `operations/cancel`

```json
{
  "jsonrpc": "2.0",
  "id": "operation-cancel-1",
  "method": "operations/cancel",
  "params": {
    "operation_id": "op-001",
    "expected_revision": 2,
    "reason": "调用方终止流程"
  }
}
```

取消是请求，不保证立即停止。只有设备达到确认安全终态后才能返回 `cancelled`；无法确认时必须返回 `unknown`。

## 幂等与重试

- `operations/list`、`operations/read` 和 `operations/get` 可以使用新请求标识安全重试。
- `operations/write`、`operations/invoke`、`operations/respond` 和 `operations/cancel` 默认不得自动重放。
- 只有定义声明 `supports_idempotency=true` 时才接受 `idempotency_key`。
- 幂等键必须绑定主体、客户端、设备、方法、操作名称、对象绑定和规范化参数摘要。
- 同一键用于不同请求内容时必须返回 `IdempotencyConflict`。
- 连接中断后，客户端必须先通过 `operations/get` 或重新读取现场状态确认结果。

## 正式类型定义

```typescript
type OperationKind = "read" | "write" | "invoke";
type OperationOutcome = "succeeded" | "failed" | "unknown";
type OperationTaskStatus =
  | "queued"
  | "running"
  | "input_required"
  | "succeeded"
  | "failed"
  | "cancel_requested"
  | "cancelled"
  | "unknown";

interface OperationDefinition {
  workstation: { namespace: string; identifier: string };
  name: string;
  kind: OperationKind;
  title: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  required_scopes: string[];
  object_roles: ObjectRoleDefinition[];
  preconditions: Condition[];
  cautions: Caution[];
  constraints: Constraint[];
  state_changes: StateChange[];
  effects: string[];
  execution: ExecutionDefinition;
}

interface ObjectRoleDefinition {
  role: string;
  required: boolean;
  min_count: number;
  max_count: number;
  allowed_object_types: string[];
}

interface ExecutionDefinition {
  may_change_physical_state: boolean;
  supports_dry_run: boolean;
  supports_idempotency: boolean;
  may_return_task: boolean;
  may_require_input: boolean;
  cancellable: boolean;
  default_timeout_ms: number;
  result_retention_ms: number;
}

interface Condition {
  path: string;
  operator: "eq" | "ne" | "lt" | "lte" | "gt" | "gte" | "in" | "contains" | "exists";
  value?: unknown;
}

interface Caution {
  code: string;
  message: string;
}

interface Constraint {
  rule_id: string;
  level: "MUST" | "SHOULD";
  condition: Condition;
  category: string;
}

interface StateChange {
  target: string;
  mode: "set" | "append" | "remove";
  value_from?: string;
  value?: unknown;
}

interface Diagnostic {
  code: string;
  category: string;
  severity: "error" | "warning";
  rule_level: "MUST" | "SHOULD";
  message: string;
  expected: unknown | null;
  actual: unknown | null;
  path: string | null;
  remediation: string | null;
}

interface OperationOptions {
  expected_state_revision?: number;
  expected_object_revisions?: Record<string, number>;
  deadline?: string;
  dry_run?: boolean;
  execution_mode?: "sync" | "async" | "auto";
  timeout_ms?: number;
  idempotency_key?: string | null;
}

interface OperationTask {
  operation_id: string;
  device_id: string;
  name: string;
  kind: OperationKind;
  status: OperationTaskStatus;
  progress: {
    completed: number;
    total: number | null;
    message: string | null;
  } | null;
  input_requests: Array<Record<string, unknown>>;
  result: unknown | null;
  error: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  result_expires_at: string;
  revision: number;
}

interface GetOperationParams {
  device_id: string;
  operation_id: string;
  if_revision?: number | null;
  wait_ms?: number;
  include_result?: boolean;
}
```
