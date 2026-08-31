---
title: "错误"
description: "ALL 标准错误编码、结构和恢复规则"
---

## 错误结构

```typescript
interface AllErrorData {
  name: string;
  recoverable: boolean;
  details?: Array<Record<string, unknown>>;
  suggested_action?: string;
  retry_after_ms?: number;
  revision_domain?: string;
  current_revision?: number;
}
```

`message` 面向人，客户端逻辑必须使用 `code` 和 `data.name`。错误不得包含访问令牌、内部堆栈、串口内容、隐藏设备名称或其他主体信息。

## 标准编码

| 编码 | 名称 | 说明 |
| --- | --- | --- |
| `-32700` | `ParseError` | JSON 无法解析 |
| `-32600` | `InvalidRequest` | JSON-RPC 请求结构无效 |
| `-32601` | `MethodNotFound` | 方法不存在或未声明 |
| `-32602` | `InvalidParams` | 参数类型、字段或数据结构无效 |
| `-32603` | `InternalError` | 无法映射的内部协议故障 |
| `-32001` | `UnsupportedProtocolVersion` | 不支持请求版本 |
| `-32002` | `HeaderMismatch` | HTTP 头与 JSON-RPC 正文不一致 |
| `-32003` | `AuthenticationRequired` | 需要有效访问令牌；通常配合 HTTP 401 |
| `-32004` | `PermissionDenied` | 身份有效但权限不足 |
| `-32005` | `DeviceNotFound` | 设备不存在或当前身份不可见 |
| `-32006` | `CapabilityNotFound` | 研究对象类型、操作或工作流未声明 |
| `-32007` | `PreconditionFailed` | 当前状态不允许执行 |
| `-32008` | `ConstraintViolation` | 参数、对象、位置或物理限制被违反 |
| `-32009` | `RevisionConflict` | 指定修订号已经变化 |
| `-32010` | `StaleState` | 强前置状态已经过期 |
| `-32011` | `DeviceBusy` | 设备执行锁被占用 |
| `-32012` | `ObjectNotFound` | 对象不存在或当前身份不可见 |
| `-32013` | `ObjectBusy` | 对象正在被操作占用 |
| `-32014` | `AlreadyExists` | 稳定标识已经存在 |
| `-32015` | `SchemaValidationFailed` | 输入或输出不符合声明数据结构 |
| `-32016` | `PhysicalChangeRequired` | 试图用数据更新代替物理操作 |
| `-32017` | `OperationNotFound` | 操作任务不存在或当前身份不可见 |
| `-32018` | `OperationExecutionFailed` | 底层执行明确失败 |
| `-32019` | `ResultUnknown` | 物理结果无法确认 |
| `-32020` | `UnsafeCancellation` | 当前阶段不能安全取消 |
| `-32021` | `IdempotencyConflict` | 同一幂等键对应不同请求内容 |
| `-32022` | `WorkflowNotFound` | Workflow 名称或固定版本不存在 |
| `-32023` | `WorkflowDigestMismatch` | Workflow 摘要与固定版本不一致 |
| `-32024` | `ValidationExpired` | Workflow 校验句柄已过期或上下文变化 |
| `-32025` | `EventCursorExpired` | 事件游标超过保留期 |
| `-32026` | `RateLimited` | ALL 方法级限流 |
| `-32027` | `OperationResultExpired` | 操作任务仍可审计，但异步结果正文已超过保留期 |
| `-32028` | `LoopNonConvergent` | 有限循环达到上限仍不满足停止条件 |
| `-32029` | `ParallelWriteConflict` | 并行分支声明或产生相互冲突的状态写入 |
| `-32030` | `ProtectedIntervalViolation` | 受保护区间不能保证连续执行或资源独占 |
| `-32031` | `StateTransitionRejected` | 操作或工作流的状态转换未被接受 |

## 版本错误

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "error": {
    "code": -32001,
    "message": "不支持请求的协议版本",
    "data": {
      "name": "UnsupportedProtocolVersion",
      "recoverable": true,
      "requested_version": "2026-07-28",
      "supported_versions": ["2026-08-31"],
      "suggested_action": "选择双方共同支持的最新版本"
    }
  }
}
```

## 修订号冲突

```json
{
  "jsonrpc": "2.0",
  "id": "req-2",
  "error": {
    "code": -32009,
    "message": "对象修订号已经变化",
    "data": {
      "name": "RevisionConflict",
      "recoverable": true,
      "revision_domain": "object",
      "current_revision": 5,
      "suggested_action": "重新读取对象并再次校验"
    }
  }
}
```

## 多项校验错误

```json
{
  "jsonrpc": "2.0",
  "id": "req-3",
  "error": {
    "code": -32015,
    "message": "请求参数不符合操作定义",
    "data": {
      "name": "SchemaValidationFailed",
      "recoverable": true,
      "details": [
        {
          "path": "arguments.target_location",
          "keyword": "minLength",
          "message": "字符串不能为空"
        }
      ],
      "suggested_action": "根据能力清单修正参数"
    }
  }
}
```

## 诊断结构

操作和工作流的校验、失败或警告必须使用统一 `diagnostics` 数组。`MUST` 失败是阻断性错误；`SHOULD` 失败是非阻断性警告。服务端必须在物理执行前尽可能收集所有可判定诊断，并且强制诊断存在时不得提交研究对象状态。

```json
{
  "code": "container-capacity",
  "category": "container",
  "severity": "error",
  "rule_level": "MUST",
  "message": "容器容量不满足操作要求",
  "path": "objects.target.container.capacity",
  "expected": {"minimum": {"value": 1, "unit": "mL"}},
  "actual": {"value": 0.5, "unit": "mL"},
  "remediation": "选择满足容量要求的研究对象"
}
```

`code`、`category`、`severity`、`rule_level`、`message`、`path`、`expected`、`actual` 和 `remediation` 为固定字段；没有值时使用 `null`。诊断不得包含令牌、内部堆栈、原始驱动帧或不可见资源信息。

## 物理执行错误

在发送任何物理设备命令之前发现的错误使用 JSON-RPC `error`。物理执行开始后，失败和未知结果必须保留在普通执行结果中：

```json
{
  "resultType": "complete",
  "outcome": "unknown",
  "value": null,
  "previous_state_revision": 325,
  "new_state_revision": null,
  "started_at": "2026-08-31T10:21:02.120+08:00",
  "completed_at": "2026-08-31T10:21:32.120+08:00",
  "evidence_ids": [],
  "error": {
    "name": "ResultUnknown",
    "message": "设备连接中断，无法确认最终物理状态",
    "recoverable": true,
    "suggested_action": "重新读取系统和对象状态，禁止直接重放"
  }
}
```

## 不存在与不可见

为防止枚举隐藏资源，设备、对象、操作任务和 Workflow 对当前身份不可见时，服务端可以返回与不存在相同的错误。错误不得说明目标实际存在但无权访问。

## 重试规则

| 错误 | 自动重试 |
| --- | --- |
| `RateLimited` | 可以按 `retry_after_ms` 重试只读请求 |
| `DeviceBusy`、`ObjectBusy` | 可以在重新读取状态后重试 |
| `RevisionConflict`、`StaleState` | 必须先重新读取对应修订号域 |
| `PermissionDenied` | 必须先获得新授权，不得原样重试 |
| `ResultUnknown` | 禁止直接重放物理操作 |
| `InvalidParams`、`SchemaValidationFailed` | 必须修正请求 |
| `UnsupportedProtocolVersion` | 必须重新选择明确支持版本 |
