---
title: "动作"
description: "动作定义以及调用接口"
---

动作表示一个具有固定语义和确定性执行边界的设备过程。

## 动作定义

```json
{
  "name": "move_object",
  "title": "移动对象",
  "description": "把设备工作区内的对象移动到已声明的内部位置。",
  "input_schema": {
    "type": "object",
    "properties": {
      "object_id": {
        "type": "string",
        "minLength": 1
      },
      "target_location": {
        "type": "string",
        "minLength": 1
      }
    },
    "required": ["object_id", "target_location"],
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
  "effects": [
    "updates:physical_resources.{object_id}.location"
  ],
  "preconditions": [
    {"path": "device.status", "operator": "eq", "value": "IDLE"},
    {
      "path_template": "physical_resources.${arguments.object_id}.boundary_state",
      "operator": "eq",
      "value": "present"
    },
    {
      "path_template": "workspace.${arguments.target_location}.occupied",
      "operator": "eq",
      "value": false
    }
  ],
  "constraint_ids": [
    "workspace.target_compatibility",
    "motion.safe_envelope"
  ],
  "execution_mode": "orchestrated",
  "result_confirmation": "recommended",
  "idempotent": false,
  "timeout_ms": 30000
}
```

前置条件必须使用结构化条件表达式，不得把任意代码或通用表达式交给服务端执行。条件表达式包含 `path` 或 `path_template`、`operator` 和比较值；核心操作符为 `eq`、`ne`、`lt`、`lte`、`gt`、`gte`、`in`、`contains` 和 `exists`。模板只允许引用当前动作的 `arguments`，或当前工作流的 `inputs` 与已完成步骤输出。

`effects` 是用于审查、规划和审计的声明，不自行授予写权限。实际状态变化仍必须来自动作实现和受控状态更新。

`execution_mode`：

| 值 | 含义 |
| --- | --- |
| `atomic` | 对外表现为一个不可拆分的确定性动作 |
| `orchestrated` | 服务端按经过审核的固定步骤执行，但只返回一个动作结果 |
| `device_program` | 由 PLC、控制器或设备固件执行固定程序 |

#### `invoke`

```json
{
  "jsonrpc": "2.0",
  "id": "invoke-1",
  "method": "invoke",
  "params": {
    "device_id": "device-001",
    "action": "move_object",
    "arguments": {
      "object_id": "object-001",
      "target_location": "workspace.position-02"
    },
    "options": {
      "expected_revision": 325,
      "deadline": "2026-08-31T10:22:00+08:00",
      "dry_run": false,
      "wait": true,
      "timeout_ms": 30000
    }
  }
}
```

```json
{
  "resultType": "complete",
  "outcome": "succeeded",
  "device_id": "device-001",
  "action": "move_object",
  "arguments": {
    "object_id": "object-001",
    "target_location": "workspace.position-02"
  },
  "value": {
    "final_location": "workspace.position-02"
  },
  "previous_revision": 325,
  "new_revision": 326,
  "started_at": "2026-08-31T10:21:02.120+08:00",
  "completed_at": "2026-08-31T10:21:09.504+08:00",
  "evidence": [],
  "error": null
}
```

动作必须默认视为非幂等，除非动作定义明确证明其可以安全去重。
