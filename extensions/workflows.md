---
title: "工作流"
description: "工作流类型、模板、步骤和协议方法"
---

Workflow 是设备可选能力。设备可以不提供 Workflow；此时 Manifest 中 `workflows=[]`，能力声明为不支持。提供 Workflow 的设备可以包含供应商内置模板，也可以允许上位机操作员或单设备智能体创建、修改和提交模板。

Workflow 是可检查、可版本化、可锁定的流程定义，不能绕过单步 Action 的权限和安全约束。

## 工作流类型

| 来源 | 含义 | 默认权限 |
| --- | --- | --- |
| `vendor` | 供应商随设备提供 | 可以是只读内置模板，也可以复制后编辑 |
| `operator` | 操作员通过上位机创建或修改 | 按授权提交或批准；只有最高人工角色可以锁定 |
| `device_agent` | 单设备智能体创建或修改 | 只能在授权范围内提交，不能越过人工锁 |

支持 Workflow 的设备 SHOULD 提供与其能力相符的基础模板：

- 只读传感器：`observe_and_record`；
- 可操作设备：`initialize`、`basic_operation` 或真实核心流程；
- 支持安全停机的设备：`safe_shutdown`；
- 需要装载对象的设备：装载确认、运行和卸载清理流程。

Workflow 生命周期：

```text
draft → submitted → approved → locked → deprecated
```

- `draft`：作者可继续修改。
- `submitted`：等待具有审批权限的人确认。
- `approved`：可以执行，但仍可按权限修改并产生新 revision。
- `locked`：人工最高权限锁定，任何程序和设备智能体都不能修改。
- `deprecated`：保留历史和审计，但禁止启动新的运行。

Server MUST NOT 暴露实际无法执行的伪 Workflow。

## 工作流模板

```json
{
  "name": "standard_object_process",
  "version": "1.0.0",
  "revision": 7,
  "title": "标准对象处理流程",
  "description": "准备对象、执行已声明的处理动作并读取最终状态。",
  "origin": "vendor",
  "status": "approved",
  "created_by": "device-vendor",
  "updated_by": "operator-17",
  "locked": false,
  "locked_by": null,
  "locked_at": null,
  "execution_mode": "orchestrated",
  "input_schema": {
    "type": "object",
    "properties": {
      "object_id": {
        "type": "string",
        "minLength": 1
      },
      "target_position": {
        "type": "string",
        "minLength": 1
      }
    },
    "required": ["object_id", "target_position"],
    "additionalProperties": false
  },
  "required_capabilities": [
    "prepare_operation",
    "execute_operation",
    "finalize_operation"
  ],
  "required_object_types": [
    "sample_carrier",
    "multi_position_container"
  ],
  "required_device_supplies": [
    {
      "device_supply_type": "supply_pack",
      "minimum_quantity": 1,
      "quantity_unit": "piece"
    }
  ],
  "preconditions": [
    {"path": "device.status", "operator": "eq", "value": "IDLE"},
    {
      "path_template": "physical_resources.${inputs.object_id}.boundary_state",
      "operator": "eq",
      "value": "present"
    },
    {
      "path": "physical_resources.supply-pack-current.supply_status",
      "operator": "eq",
      "value": "installed"
    },
    {
      "path": "physical_resources.supply-pack-current.quantity.value",
      "operator": "gte",
      "value": 1
    },
    {
      "path_template": "workspace.${inputs.target_position}.occupied",
      "operator": "eq",
      "value": false
    }
  ],
  "steps": [
    {
      "step_id": "read_state",
      "type": "read",
      "paths": [
        "device.status",
        "physical_resources.${inputs.object_id}.boundary_state",
        "physical_resources.supply-pack-current.quantity.value",
        "workspace.${inputs.target_position}.occupied"
      ]
    },
    {
      "step_id": "prepare",
      "type": "invoke",
      "action": "prepare_operation",
      "arguments": {
        "object_id": "${inputs.object_id}"
      }
    },
    {
      "step_id": "execute",
      "type": "invoke",
      "action": "execute_operation",
      "arguments": {
        "object_id": "${inputs.object_id}",
        "target_position": "${inputs.target_position}"
      }
    },
    {
      "step_id": "verify",
      "type": "read",
      "paths": [
        "physical_resources.${inputs.object_id}.process_result"
      ]
    },
    {
      "step_id": "finalize",
      "type": "invoke",
      "action": "finalize_operation",
      "arguments": {
        "object_id": "${inputs.object_id}"
      }
    }
  ],
  "device_supply_effects": [
    {
      "device_supply_type": "supply_pack",
      "operation": "decrease",
      "quantity": 1,
      "quantity_unit": "piece"
    }
  ],
  "evidence_requirements": [
    "prepare_action_result",
    "execute_action_result",
    "final_state_read",
    "finalize_action_result"
  ],
  "result_confirmation": "recommended",
  "timeout_ms": 90000,
  "template_digest": "sha256:example"
}
```

## 工作流步骤类型

核心步骤类型：

```text
read
write
invoke
assert
wait
input
resource
subworkflow
script
```

- `wait` MUST 有明确条件和超时。
- `assert` 只能检查已声明状态和前序输出。
- `input` 不能替代安全联锁。
- `subworkflow` MUST 固定名称和版本。
- `script` MUST 引用已登记资源，不能在 Workflow 中直接嵌入任意代码。

脚本步骤：

```json
{
  "step_id": "calculate_parameters",
  "type": "script",
  "script": {
    "resource_uri": "alp://device-001/scripts/calculate_parameters.py",
    "digest": "sha256:script-example",
    "runtime": "python",
    "entrypoint": "calculate",
    "arguments": {
      "target_position": "${inputs.target_position}"
    },
    "permissions": {
      "network": false,
      "device_actions": [],
      "resource_read": ["alp://device-001/config/*"]
    },
    "timeout_ms": 5000
  }
}
```

脚本 MUST：

- 绑定不可变内容摘要；
- 声明运行时、入口、参数、权限和超时；
- 在隔离环境运行；
- 禁止直接访问串口、寄存器、私有控制接口和未声明网络；
- 通过返回结构化输出影响后续步骤；
- 如需设备动作，仍调用已声明的 `invoke`，不能在脚本内绕过 Server。

## 工作流方法

声明 Workflow 能力的设备 MUST 实现：

- `workflows/list`
- `workflows/get`
- `workflows/validate`
- `workflows/run`
- `workflows/create`
- `workflows/update`
- `workflows/submit`
- `workflows/approve`
- `workflows/lock`
- `workflows/unlock`
- `workflows/deprecate`

##### Workflow Editing

`workflows/create` 和 `workflows/update` MUST 接受完整模板或字段掩码，并使用模板级 `expected_revision` 防止覆盖他人修改。

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-update-1",
  "method": "workflows/update",
  "params": {
    "device_id": "device-001",
    "workflow": "standard_object_process",
    "workflow_version": "1.0.0",
    "field_mask": ["description", "result_confirmation"],
    "values": {
      "description": "准备对象、执行处理并读取最终状态。",
      "result_confirmation": "recommended"
    },
    "options": {
      "expected_revision": 7,
      "reason": "操作员更新流程说明"
    }
  }
}
```

权限规则：

- 上位机操作员可以在授权范围内创建、修改和提交 Workflow。
- 单设备智能体可以在授权范围内创建、修改和提交 `draft`，但不能自行批准高风险模板。
- 只有具有人工最高权限的主体可以执行 `workflows/lock` 和 `workflows/unlock`。
- `locked=true` 后，Server MUST 拒绝来自上位机程序、普通操作员和设备智能体的所有模板修改。
- 解锁、重新锁定、批准和弃用 MUST 进入审计记录。
- 已启动的运行始终绑定启动时的 `version + revision + template_digest`，后续编辑不得改变运行中实例。

##### `workflows/validate`

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-check-1",
  "method": "workflows/validate",
  "params": {
    "device_id": "device-001",
    "workflow": "standard_object_process",
    "workflow_version": "1.0.0",
    "inputs": {
      "object_id": "object-001",
      "target_position": "position-02"
    },
    "expected_revision": 412
  }
}
```

```json
{
  "resultType": "complete",
  "valid": true,
  "workflow": "standard_object_process",
  "workflow_version": "1.0.0",
  "template_digest": "sha256:example",
  "validated_revision": 412,
  "checks": {
    "schema": "passed",
    "objects": "passed",
    "capabilities": "passed",
    "preconditions": "passed",
    "constraints": "passed"
  },
  "error": null
}
```

校验 MUST NOT 移动设备或发送写命令。

##### `workflows/run`

```json
{
  "jsonrpc": "2.0",
  "id": "workflow-run-1",
  "method": "workflows/run",
  "params": {
    "device_id": "device-001",
    "workflow": "standard_object_process",
    "workflow_version": "1.0.0",
    "template_digest": "sha256:example",
    "inputs": {
      "object_id": "object-001",
      "target_position": "position-02"
    },
    "options": {
      "expected_revision": 412,
      "deadline": "2026-08-31T11:20:00+08:00",
      "dry_run": false,
      "wait": true,
      "timeout_ms": 90000
    }
  }
}
```

`workflows/run` MUST 复用普通 `write`、`invoke`、统一执行锁、Evidence 和审计路径。

`name + version + template_digest` 唯一确定一个模板。任何步骤、参数、安全语义或效果变化 MUST 更新版本和摘要。
