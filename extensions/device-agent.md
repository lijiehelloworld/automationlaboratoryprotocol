---
title: "设备智能体"
description: "可选单设备智能体的定义、方法和安全边界"
---

每个设备能力清单必须保留 `device_agent` 字段。供应商可以随设备提供单设备智能体，也可以由部署方接入；未提供时字段值必须为 `null`。

一个设备节点最多公开一个活动的逻辑设备智能体。供应商内部可以组合多个模型或模块，但对外仍表现为一个 `device_agent`。

## 设备智能体定义

```json
{
  "device_agent": {
    "agent_id": "device-001-agent",
    "display_name": "示例设备智能体",
    "provider": "device-vendor",
    "version": "1.0.0",
    "modes": ["plan_only", "execute_workflow", "execute_experiment"],
    "capabilities": [
      "explain_device",
      "diagnose_state",
      "interpret_natural_language_goal",
      "propose_workflow",
      "execute_declared_workflow",
      "orchestrate_complete_experiment",
      "manage_physical_resources",
      "control_transfer_robot"
    ],
    "allowed_action_scope": [
      "prepare_operation",
      "execute_operation",
      "finalize_operation"
    ],
    "workflow_scope": [
      "standard_object_process"
    ],
    "management_scope": [
      "physical_resources:read",
      "physical_resources:write",
      "transfers:prepare",
      "transfers:confirm",
      "workflows:draft",
      "workflows:submit"
    ],
    "guidance_resources": [
      "all://device-001/guidance/operation"
    ],
    "requires_human_approval": [
      "execute_workflow",
      "execute_experiment"
    ]
  }
}
```

规则：

- `provider` 只说明来源，不代表自动受信任。
- `modes` 必须至少包含 `plan_only`。
- `execute_workflow` 和 `execute_experiment` 可以不提供；声明后必须遵守完整执行规范。
- 声明 `execute_experiment` 的设备必须同时实现 `ALL-Operations`，使完整实验可以显式查询、取消或处理输入等待。
- 智能体权限不能超过调用者权限与智能体范围的交集。
- 凭据、模型密钥和供应商内部端点不得出现在能力清单中。

## 设备智能体方法

提供智能体的设备必须实现：

- `agent/describe`
- `agent/invoke`

长时间智能体任务复用 `operations/get`，等待输入时使用 `operations/respond`；设备声明可以安全取消时再提供 `operations/cancel`。

##### `agent/describe`

返回智能体定义、支持模式、输入数据结构定义和当前可用状态。该方法不得移动设备。

##### `agent/invoke`

```json
{
  "jsonrpc": "2.0",
  "id": "agent-1",
  "method": "agent/invoke",
  "params": {
    "device_id": "device-001",
    "mode": "plan_only",
    "goal": "处理对象 object-001，并把结果放入位置 position-02。",
    "context": {
      "expected_revision": 412,
      "object_refs": [
        "object-001",
        "carrier-current"
      ],
      "resource_uris": []
    },
    "limits": {
      "allowed_actions": [
        "prepare_operation",
        "execute_operation",
        "finalize_operation"
      ],
      "allowed_workflows": [
        "standard_object_process"
      ],
      "deadline": "2026-08-31T11:30:00+08:00"
    }
  }
}
```

```json
{
  "resultType": "complete",
  "mode": "plan_only",
  "proposal_id": "proposal-1001",
  "bound_revision": 412,
  "manifest_digest": "sha256:manifest-example",
  "workflow": {
    "name": "standard_object_process",
    "version": "1.0.0",
    "template_digest": "sha256:example",
    "inputs": {
      "object_id": "object-001",
      "target_position": "position-02"
    }
  },
  "required_approvals": ["execute_workflow"],
  "warnings": [],
  "error": null
}
```

执行模式必须引用已生成的 `proposal_id`、能力清单摘要、工作流摘要、最新修订号和可信授权。服务端必须重新执行工作流校验，然后通过 `workflows/run` 或普通 `invoke` 执行。

##### 自然语言实验执行

声明 `execute_experiment` 的单设备智能体可以接收完整自然语言实验目标，并在一个受控操作任务中完成：

1. 解析目标、对象、容器、耗材、参数和结果要求；
2. 读取当前设备、对象、耗材和环境状态；
3. 选择已有工作流，或在授权范围内生成临时计划；
4. 需要时控制机器人完成本设备边界的耗材或实验对象进出；
5. 调用已声明的动作、工作流和受限脚本步骤；
6. 处理中间 `input_required` 和人工授权；
7. 汇总步骤结果、证据、异常和最终状态；
8. 对可复用计划创建或修改工作流草稿并提交人工审批。

执行请求：

```json
{
  "jsonrpc": "2.0",
  "id": "agent-experiment-1",
  "method": "agent/invoke",
  "params": {
    "device_id": "device-001",
    "mode": "execute_experiment",
    "goal": "确认样品载具已经进入交接点，安装耗材包，处理 object-001，并在完成后返回状态和可用证据。",
    "context": {
      "expected_revision": 412,
      "object_refs": ["carrier-incoming-001", "consumable-pack-current", "object-001"],
      "resource_uris": []
    },
    "limits": {
      "allowed_actions": [
        "prepare_operation",
        "execute_operation",
        "finalize_operation"
      ],
      "allowed_workflows": ["standard_object_process"],
      "allow_workflow_draft": true,
      "allow_robot_transfer": true,
      "deadline": "2026-08-31T11:45:00+08:00"
    },
    "approval_ref": "server-issued-approval-handle"
  }
}
```

`approval_ref` 必须由可信授权流程签发，并绑定调用身份、设备、模式、动作范围、参数范围和有效期。请求正文中的姓名、角色或布尔值不能代替该句柄。

完整实验通常返回 `resultType=operation`。操作任务必须显式记录当前阶段：

```text
INTERPRETING
READING_STATE
WAITING_FOR_INPUT
WAITING_FOR_APPROVAL
PREPARING_TRANSFER
MANAGING_CONSUMABLES
RUNNING_ACTION
RUNNING_WORKFLOW
VERIFYING_RESULT
SUCCEEDED
FAILED
UNKNOWN
```

智能体可以生成临时计划，但每个物理步骤仍必须映射到已声明的动作、工作流、交接或脚本。自然语言本身不能成为原始设备命令。

如果没有合适的工作流，智能体可以：

- 在当前授权范围内直接编排已声明动作完成本次实验；
- 创建 `draft` 工作流；
- 调用 `workflows/submit` 交由人工审批；
- 在模板被人工锁定后只读使用，不能继续修改。

## 设备智能体安全

设备智能体必须：

1. 未获得本次实验执行授权时默认使用 `plan_only`；
2. 不直接访问串口、寄存器、私有控制方法或维修接口；
3. 使用调用者权限和智能体权限的交集；
4. 不跳过人工授权；
5. 不修改能力清单、约束、锁定工作流或审计记录；
6. 只选择已声明的动作、交接、工作流和受限脚本；
7. 在状态修订号改变后使旧提案失效；
8. 遇到 `unknown` 时停止自动执行并请求回读或人工处理；
9. 不承担硬实时闭环、急停、安全门或运动限位；
10. 在远程服务不可用时不影响普通设备控制接口。
11. 创建和修改工作流时只能操作未锁定草稿，并保留作者、原因和修订号。
12. 修改设备供给物料状态时必须使用物理资源接口，不能直接改写设备内部数据库。

调用方始终通过服务端的 `agent/*` 方法访问设备智能体。智能体内部部署方式不得改变 ALL 对外数据结构。

---
