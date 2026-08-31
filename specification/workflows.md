---
title: "Workflow"
description: "ALL Workflow 模板、校验和运行接口"
---

Workflow 是由设备发布、可检查、可版本化的操作组合。Workflow 只能使用能力清单已经声明的对象类型和操作，不得扩大调用者权限或绕过单步操作的安全规则。

## 方法列表

Workflow 模块只定义四个接口：

| 方法 | 需要权限 | 说明 |
| --- | --- | --- |
| `workflows/list` | `all:workflows:read` | 查询可见 Workflow 摘要 |
| `workflows/get` | `all:workflows:read` | 取得完整固定版本模板 |
| `workflows/validate` | `all:workflows:run` | 校验输入、对象、权限和当前状态 |
| `workflows/run` | `all:workflows:run` 及内部操作权限 | 运行固定版本 Workflow |

不支持 Workflow 的设备必须在能力清单中声明 `workflows.methods=[]` 和 `workflows.definitions=[]`。

## Workflow 定义

```json
{
  "name": "standard_object_process",
  "version": "1.0.0",
  "revision": 3,
  "digest": "sha256:example",
  "title": "标准对象处理",
  "description": "读取状态、执行对象处理并确认结果。",
  "input_schema": {
    "type": "object",
    "properties": {
      "target_location": {"type": "string", "minLength": 1}
    },
    "required": ["target_location"],
    "additionalProperties": false
  },
  "object_roles": [
    {
      "role": "target",
      "required": true,
      "min_count": 1,
      "max_count": 1,
      "allowed_object_types": ["generic_container"]
    }
  ],
  "required_scopes": [
    "all:workflows:run",
    "all:operations:read",
    "all:operations:execute"
  ],
  "preconditions": [
    {"path": "system.state", "operator": "eq", "value": "idle"}
  ],
  "steps": [
    {
      "step_id": "read_status",
      "type": "operation",
      "method": "operations/read",
      "name": "read_device_status",
      "object_bindings": {},
      "arguments": {}
    },
    {
      "step_id": "move_target",
      "type": "operation",
      "method": "operations/invoke",
      "name": "move_object",
      "object_bindings": {
        "target": "${objects.target}"
      },
      "arguments": {
        "target_location": "${inputs.target_location}"
      }
    },
    {
      "step_id": "verify_result",
      "type": "assert",
      "condition": {
        "path": "steps.move_target.value.final_location",
        "operator": "eq",
        "value_from": "inputs.target_location"
      }
    }
  ],
  "result_schema": {
    "type": "object",
    "properties": {
      "final_location": {"type": "string"}
    },
    "required": ["final_location"],
    "additionalProperties": false
  },
  "result_mapping": {
    "final_location": "${steps.move_target.value.final_location}"
  },
  "execution": {
    "may_change_physical_state": true,
    "may_return_task": true,
    "may_require_input": false,
    "cancellable": true,
    "default_timeout_ms": 90000
  }
}
```

## 定义字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | `string` | 是 | 设备内稳定、唯一的 Workflow 名称 |
| `version` | `string` | 是 | 不可变语义版本 |
| `revision` | `integer` | 是 | 同一版本的元数据修订号 |
| `digest` | `string` | 是 | 规范化模板内容的 SHA-256 摘要 |
| `title` | `string` | 是 | 面向人的名称 |
| `description` | `string` | 是 | 固定流程语义 |
| `input_schema` | `JsonSchema` | 是 | Workflow 输入定义 |
| `object_roles` | `ObjectRoleDefinition[]` | 是 | 参与对象角色 |
| `required_scopes` | `string[]` | 是 | Workflow 与全部步骤权限范围的并集 |
| `preconditions` | `Condition[]` | 是 | Workflow 启动前置条件 |
| `steps` | `WorkflowStep[]` | 是 | 非空、有序步骤列表 |
| `result_schema` | `JsonSchema` | 是 | Workflow 成功结果定义 |
| `result_mapping` | `object` | 是 | 从步骤输出映射最终结果 |
| `execution` | `WorkflowExecutionDefinition` | 是 | 副作用、任务、输入、取消和超时能力 |

`name + version + digest` 唯一确定一个可运行模板。步骤、输入、结果、权限、前置条件、对象角色或物理语义发生变化时必须发布新版本和新摘要。

## 步骤类型

只允许三种步骤类型：

### `operation`

调用 `operations/read`、`operations/write` 或 `operations/invoke`。引用的操作必须存在于同一能力清单，参数和对象绑定必须通过该操作定义校验。

### `assert`

检查系统状态、对象状态、Workflow 输入或已完成步骤输出。断言只能使用 ALL 条件操作符，不能执行任意表达式或代码。

### `wait`

等待结构化条件成立：

```json
{
  "step_id": "wait_until_idle",
  "type": "wait",
  "condition": {
    "path": "system.state",
    "operator": "eq",
    "value": "idle"
  },
  "poll_interval_ms": 500,
  "timeout_ms": 30000
}
```

`poll_interval_ms` 必须大于 `0`，`timeout_ms` 必须明确且不得超过 Workflow 默认超时。

## 模板表达式

模板值只允许引用：

```text
${inputs.<path>}
${objects.<role>}
${steps.<step_id>.value.<path>}
```

实现必须把引用当作结构化路径解析，不得使用通用脚本、模板执行器或动态代码求值。引用不存在、越界或类型不匹配时校验失败。

## `workflows/list`

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-list-1",
  "method": "workflows/list",
  "params": {
    "device_id": "device-001",
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
  "items": [
    {
      "name": "standard_object_process",
      "version": "1.0.0",
      "revision": 3,
      "digest": "sha256:example",
      "title": "标准对象处理",
      "description": "读取状态、执行对象处理并确认结果。",
      "required_scopes": ["all:workflows:run"],
      "may_change_physical_state": true
    }
  ],
  "next_cursor": null
}
```

`items` 按 `name`、`version` 升序排列。`revision` 属于能力清单域。

## `workflows/get`

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-get-1",
  "method": "workflows/get",
  "params": {
    "device_id": "device-001",
    "name": "standard_object_process",
    "version": "1.0.0",
    "if_digest": null
  }
}
```

完整响应：

```json
{
  "resultType": "complete",
  "not_modified": false,
  "workflow": {}
}
```

`if_digest` 与当前摘要相等时可以返回 `not_modified=true` 并省略 `workflow`。服务端不得在同一 `name + version` 下返回不同语义模板。

## `workflows/validate`

校验固定模板、输入、对象、权限和当前设备状态，但不执行物理动作：

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-validate-1",
  "method": "workflows/validate",
  "params": {
    "device_id": "device-001",
    "name": "standard_object_process",
    "version": "1.0.0",
    "digest": "sha256:example",
    "inputs": {"target_location": "workspace.output"},
    "object_bindings": {"target": ["object-001"]},
    "expected_state_revision": 325,
    "expected_object_revisions": {"object-001": 4}
  }
}
```

```json
{
  "resultType": "complete",
  "valid": true,
  "validated_at": "2026-08-31T10:20:31.203+08:00",
  "state_revision": 325,
  "object_revisions": {"object-001": 4},
  "checks": [
    {"name": "schema", "status": "passed", "message": null},
    {"name": "authorization", "status": "passed", "message": null},
    {"name": "objects", "status": "passed", "message": null},
    {"name": "preconditions", "status": "passed", "message": null}
  ],
  "validation_token": "validation-opaque-token",
  "expires_at": "2026-08-31T10:21:01.203+08:00"
}
```

`validation_token` 是短期、不透明、绑定主体、客户端、设备、模板摘要、输入摘要、对象修订号和设备状态修订号的句柄。它不能替代 `workflows/run` 的锁内复验。

## `workflows/run`

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-run-1",
  "method": "workflows/run",
  "params": {
    "device_id": "device-001",
    "name": "standard_object_process",
    "version": "1.0.0",
    "digest": "sha256:example",
    "inputs": {"target_location": "workspace.output"},
    "object_bindings": {"target": ["object-001"]},
    "options": {
      "expected_state_revision": 325,
      "expected_object_revisions": {"object-001": 4},
      "validation_token": "validation-opaque-token",
      "deadline": "2026-08-31T10:25:00+08:00",
      "execution_mode": "async",
      "timeout_ms": 90000,
      "idempotency_key": null
    }
  }
}
```

Workflow 运行必须：

1. 固定 `name + version + digest`；
2. 校验调用者拥有 Workflow 和全部内部操作权限；
3. 校验输入与对象角色；
4. 获取设备与参与对象执行锁；
5. 在锁内重新检查状态修订号、对象修订号和全部前置条件；
6. 按模板顺序执行步骤；
7. 保存每步输入摘要、输出、时间、结果和错误；
8. 失败时停止未开始步骤，并按模板声明执行安全收尾；
9. 返回同步结果或 `resultType=operation` 的操作任务句柄；异步状态和最终结果统一通过 `operations/get` 读取。

Workflow 内部步骤的物理结果不明确时，整个 Workflow 结果必须为 `unknown`，不得继续依赖该步骤结果执行后续物理步骤。

## 正式类型定义

```typescript
interface WorkflowDefinition {
  name: string;
  version: string;
  revision: number;
  digest: string;
  title: string;
  description: string;
  input_schema: Record<string, unknown>;
  object_roles: ObjectRoleDefinition[];
  required_scopes: string[];
  preconditions: Condition[];
  steps: WorkflowStep[];
  result_schema: Record<string, unknown>;
  result_mapping: Record<string, string>;
  execution: WorkflowExecutionDefinition;
}

type WorkflowStep = OperationStep | AssertStep | WaitStep;

interface OperationStep {
  step_id: string;
  type: "operation";
  method: "operations/read" | "operations/write" | "operations/invoke";
  name: string;
  object_bindings: Record<string, string | string[]>;
  arguments: Record<string, unknown>;
}

interface AssertStep {
  step_id: string;
  type: "assert";
  condition: Condition;
}

interface WaitStep {
  step_id: string;
  type: "wait";
  condition: Condition;
  poll_interval_ms: number;
  timeout_ms: number;
}

interface WorkflowExecutionDefinition {
  may_change_physical_state: boolean;
  may_return_task: boolean;
  may_require_input: boolean;
  cancellable: boolean;
  default_timeout_ms: number;
}
```
