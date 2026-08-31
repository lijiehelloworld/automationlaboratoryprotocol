---
title: "工作流"
description: "ALL 工作流模板、组合算子、校验和运行接口"
---

工作流（Workflow）是由设备发布、可检查、可版本化的研究对象状态转换组合。工作流只能引用能力清单已声明的研究对象类型和操作；它不能扩大权限、绕过操作契约或把自由文本当作可执行指令。

## 方法列表

工作流模块**只定义四个对外接口**：

| 方法 | 权限 | 说明 |
| --- | --- | --- |
| `workflows/list` | `all:workflows:read` | 查询可见工作流摘要 |
| `workflows/get` | `all:workflows:read` | 取得固定版本完整模板 |
| `workflows/validate` | `all:workflows:run` | 校验输入、对象、权限、结构与当前状态 |
| `workflows/run` | `all:workflows:run` 及内部操作权限 | 运行固定版本工作流 |

不支持工作流的设备必须在能力清单中声明 `workflows.methods=[]` 和 `workflows.definitions=[]`。不得额外公开 `workflows/create`、`workflows/update` 或任意脚本执行接口。

## 工作流定义

```json
{
  "name": "standard_research_object_process",
  "version": "1.0.0",
  "revision": 3,
  "digest": "sha256:example",
  "title": "标准研究对象处理",
  "description": "在已声明约束下处理研究对象并确认结果。",
  "input_schema": {"type": "object", "additionalProperties": false},
  "object_roles": [{
    "role": "target", "required": true, "min_count": 1, "max_count": 1,
    "allowed_object_types": ["research_object.generic"]
  }],
  "required_scopes": ["all:workflows:run", "all:operations:execute"],
  "preconditions": [{"path": "system.state", "operator": "eq", "value": "idle"}],
  "program": {
    "node_id": "root",
    "type": "sequence",
    "children": [{
      "node_id": "move_target", "type": "operation", "method": "operations/invoke",
      "name": "move_object", "object_bindings": {"target": "${objects.target}"},
      "arguments": {"target_location": "${inputs.target_location}"}
    }]
  },
  "result_schema": {"type": "object", "additionalProperties": false},
  "result_mapping": {},
  "execution": {"may_change_physical_state": true, "may_return_task": true, "may_require_input": false, "cancellable": true, "default_timeout_ms": 90000}
}
```

`name + version + digest` 唯一确定可运行模板。程序、输入、结果、权限、前置条件、研究对象角色或物理语义改变时，服务端必须发布新的 `version` 和 `digest`；同一组合不得返回不同语义内容。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name`、`version`、`digest` | `string` | 是 | 稳定名称、不可变语义版本和规范化内容 SHA-256 摘要 |
| `revision` | `integer` | 是 | 同一版本元数据修订号 |
| `input_schema`、`result_schema` | `JsonSchema` | 是 | 输入和成功结果的 JSON Schema 2020-12 |
| `object_roles` | `ObjectRoleDefinition[]` | 是 | 参与研究对象角色 |
| `required_scopes` | `string[]` | 是 | 工作流及全部内部操作所需权限的并集 |
| `preconditions` | `Condition[]` | 是 | 运行前必须成立的条件 |
| `program` | `WorkflowNode` | 是 | 递归组合程序，必须恰好有一个根节点 |
| `result_mapping` | `object` | 是 | 从已完成节点输出映射最终结果 |
| `execution` | `WorkflowExecutionDefinition` | 是 | 副作用、异步、输入、取消和超时能力 |

## 五种组合算子

`program` 只能由下列五种组合算子和叶子节点递归组成。叶子节点 `operation`、`assert` 与 `wait` 不属于额外对外接口。

| 类型 | 中文名称 | 必填字段 | 强制结构规则 |
| --- | --- | --- | --- |
| `sequence` | 顺序 | `children` | 子节点按数组顺序执行；上一步输出与状态必须满足下一步输入域 |
| `loop` | 有限循环 | `body`、`continue_when`、`max_iterations` | `max_iterations` 必须为正整数；达到上限时条件仍成立，返回 `LoopNonConvergent` |
| `branch` | 条件分支 | `cases`、`otherwise` | 分支条件必须得到唯一结果；没有匹配分支时执行 `otherwise` 或失败 |
| `parallel` | 并行汇合 | `branches` | 并行分支的写集合不得冲突；共享状态变更必须完全一致后才可汇合 |
| `protected` | 受保护区间 | `resource_keys`、`body` | 区间必须在调度中连续、不可被未声明节点插入；相关资源锁须覆盖整个区间 |

### 叶子节点

```json
{
  "node_id": "measure", "type": "operation", "method": "operations/invoke",
  "name": "start_measurement", "object_bindings": {"target": "${objects.target}"}, "arguments": {}
}
```

`operation` 必须引用同一能力清单中声明的操作，参数、研究对象绑定、前置条件、约束和状态变化均由该操作定义校验。

`assert` 只可使用 ALL 条件操作符；`wait` 必须声明正的 `poll_interval_ms` 和有限 `timeout_ms`。模板表达式只允许引用：

```text
${inputs.<path>}
${objects.<role>}
${nodes.<node_id>.value.<path>}
```

服务端必须把引用作为结构化路径解析，禁止使用动态代码、通用表达式语言或任意模板执行器。

### 组合节点示例

```json
{
  "node_id": "bounded-repeat",
  "type": "loop",
  "max_iterations": 3,
  "continue_when": {"path": "nodes.measure.value.accepted", "operator": "eq", "value": false},
  "body": {"node_id": "measure", "type": "operation", "method": "operations/invoke", "name": "measure", "object_bindings": {}, "arguments": {}}
}
```

```json
{
  "node_id": "protected-transfer",
  "type": "protected",
  "resource_keys": ["objects.${objects.target}"],
  "body": {"node_id": "transfer-steps", "type": "sequence", "children": []}
}
```

## 静态与运行时校验

`workflows/validate` 必须在不接触物理设备的前提下校验：模板摘要、权限、输入 Schema、研究对象角色与修订号、节点引用、五种算子的结构规则、类型兼容性、写集合、保护资源和当前前置条件。成功时返回短期 `validation_token`，它绑定主体、客户端、设备、模板摘要、输入摘要、研究对象修订号与系统修订号。

`workflows/run` 必须在锁内重新校验同一组易变条件；`validation_token` 不可替代锁内复验。运行中：

1. 只在前置条件和全部强制约束通过时调度叶子操作；
2. 对每个节点记录输入摘要、输出、诊断、时间与研究对象修订号；
3. 操作的强制失败不得提交研究对象状态，建议失败必须记录为警告；
4. 并行汇合前必须检查写集合和共享变更的一致性；
5. 物理结果为 `unknown` 时，必须停止依赖该结果的后续物理节点；
6. 返回同步结果或 `resultType=operation` 任务句柄；异步进度与最终结果统一由 `operations/get` 获取。

## 四个接口

### `workflows/list`

请求参数为 `device_id`、可选 `object_type`、`cursor`、`limit` 和 `if_revision`。响应必须返回缓存字段、`items` 和 `next_cursor`；项目按 `name`、`version` 升序。每个摘要至少包含 `name`、`version`、`revision`、`digest`、`title`、`required_scopes` 与 `may_change_physical_state`。

### `workflows/get`

请求必须包含 `device_id`、`name`、`version` 与可选 `if_digest`。完整响应返回上述完整 `WorkflowDefinition`；`if_digest` 命中时可以返回 `not_modified=true` 并省略 `workflow`。

### `workflows/validate`

```json
{
  "jsonrpc": "2.0", "id": "workflow-validate-1", "method": "workflows/validate",
  "params": {
    "device_id": "device-001", "name": "standard_research_object_process", "version": "1.0.0", "digest": "sha256:example",
    "inputs": {"target_location": "workspace.output"}, "object_bindings": {"target": ["research-object-001"]},
    "expected_state_revision": 325, "expected_object_revisions": {"research-object-001": 4}
  }
}
```

响应必须包含 `valid`、`checks`、`diagnostics`、`state_revision`、`object_revisions`、`validation_token`（仅 `valid=true` 时）和 `expires_at`。强制校验失败时 `valid=false`，不得发出物理命令。

### `workflows/run`

请求使用同一模板、输入、对象绑定和修订号，并在 `options` 中传入 `validation_token`（可选）、`deadline`、`execution_mode`、`timeout_ms` 与 `idempotency_key`。服务端必须冻结本次运行使用的 `name + version + digest`，并在返回的同步结果或操作任务中报告该三元组。

## 正式类型定义

```typescript
type WorkflowNode = SequenceNode | LoopNode | BranchNode | ParallelNode | ProtectedNode | OperationNode | AssertNode | WaitNode;

interface SequenceNode { node_id: string; type: "sequence"; children: WorkflowNode[]; }
interface LoopNode { node_id: string; type: "loop"; body: WorkflowNode; continue_when: Condition; max_iterations: number; }
interface BranchNode { node_id: string; type: "branch"; cases: Array<{ when: Condition; body: WorkflowNode }>; otherwise?: WorkflowNode; }
interface ParallelNode { node_id: string; type: "parallel"; branches: WorkflowNode[]; }
interface ProtectedNode { node_id: string; type: "protected"; resource_keys: string[]; body: WorkflowNode; }
interface OperationNode { node_id: string; type: "operation"; method: "operations/read" | "operations/write" | "operations/invoke"; name: string; object_bindings: Record<string, string | string[]>; arguments: Record<string, unknown>; }
interface AssertNode { node_id: string; type: "assert"; condition: Condition; }
interface WaitNode { node_id: string; type: "wait"; condition: Condition; poll_interval_ms: number; timeout_ms: number; }

interface WorkflowExecutionDefinition {
  may_change_physical_state: boolean;
  may_return_task: boolean;
  may_require_input: boolean;
  cancellable: boolean;
  default_timeout_ms: number;
}
```
