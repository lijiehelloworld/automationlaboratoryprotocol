---
title: "协议工具"
description: "长任务、执行证据与结构化错误"
---

## 操作

动作无法在普通请求时限内完成时，服务端返回：

```json
{
  "resultType": "operation",
  "operation": {
    "operation_id": "op-1008",
    "device_id": "device-001",
    "action": "long_running_operation",
    "state": "RUNNING",
    "revision": 3,
    "progress": 0.35,
    "created_at": "2026-08-31T10:30:00+08:00",
    "updated_at": "2026-08-31T10:30:09+08:00"
  }
}
```

支持长任务的实现必须提供：

- `operations/get`
- `operations/respond`，仅当操作任务可能进入 `INPUT_REQUIRED` 时必须提供
- `operations/cancel`，仅当设备可以安全取消时提供

状态：

```text
QUEUED
RUNNING
INPUT_REQUIRED
SUCCEEDED
FAILED
CANCELLED
UNKNOWN
```

操作任务进入 `INPUT_REQUIRED` 时，`operations/get` 必须返回 `inputRequests` 和不透明 `requestState`。客户端使用下列方法补充输入：

```json
{
  "jsonrpc": "2.0",
  "id": "operation-respond-1",
  "method": "operations/respond",
  "params": {
    "operation_id": "op-1008",
    "requestState": "server-issued-state-token",
    "inputResponses": {
      "confirmation-01": true
    },
    "expected_operation_revision": 4
  }
}
```

服务端必须重新验证调用身份、授权、`requestState`、操作任务修订号、设备状态和截止时间，再决定继续、再次请求输入或结束操作任务。

取消是协作式动作。收到取消请求不等于设备已经安全停止，最终状态必须通过查询或设备回读确认。

## 执行证据

证据说明服务端根据什么判断状态或动作结果。

| 来源 | 典型证据 | 最高质量 |
| --- | --- | --- |
| `device_readback` | 完成位、编码器、寄存器 | `confirmed` |
| `sensor` | 称重、温度、压力、流量 | `confirmed` |
| `vision` | 载具、液面或位置识别 | 验证后为 `confirmed`，否则为 `estimated` |
| `operator_confirmed` | 操作员现场确认 | `confirmed`，必须保留确认主体 |
| `software_derived` | 根据成功动作计算的预计值 | `estimated` |

```json
{
  "evidence_id": "ev-9021",
  "quantity": "physical_resources.object-001.process_result",
  "value": 1,
  "unit": null,
  "source": "software_derived",
  "quality": "estimated",
  "captured_at": "2026-08-31T10:21:09.504+08:00",
  "resource_uri": null
}
```

软件推导值不得标记为设备回读。关联图像或文件时必须使用资源 URI，不得返回服务端本机路径。

## 错误

解析、方法和参数错误使用标准 JSON-RPC 错误。ALL 应用错误：

- 在物理执行开始前发现的拒绝、权限、数据结构定义、前置条件和并发错误使用 JSON-RPC `error`。
- 一旦物理执行已经开始，服务端必须返回普通 `result`，使用 `outcome=failed` 或 `outcome=unknown`，并在结果内保留同结构的错误、修订号和证据。
- 服务端不得用缺少结果正文的连接关闭来表示动作失败；连接关闭只能表示结果未知。

| 编码 | 名称 | 说明 |
| --- | --- | --- |
| `-32050` | `UnsupportedProtocolVersion` | 不支持请求版本 |
| `-32051` | `HeaderMismatch` | 头部和正文不一致 |
| `-32052` | `DeviceNotFound` | 未找到设备 |
| `-32053` | `UnsupportedCapability` | 不支持状态、动作或资源 |
| `-32054` | `PermissionDenied` | 已验证身份没有权限 |
| `-32055` | `PreconditionFailed` | 当前状态不允许执行 |
| `-32056` | `ConstraintViolation` | 参数或物理限制被违反 |
| `-32057` | `RevisionConflict` | 状态修订号已变化 |
| `-32058` | `StaleState` | 必需状态已过期 |
| `-32059` | `DeviceBusy` | 设备被其他动作占用 |
| `-32060` | `DeviceExecutionError` | 底层设备执行明确失败 |
| `-32061` | `ResultUnknown` | 物理结果无法确认 |
| `-32062` | `UnsafeCancellation` | 当前不能安全取消 |
| `-32063` | `AlreadyExists` | 稳定标识已经存在，不能用创建操作覆盖 |
| `-32064` | `LockedResource` | 目标模板或资源已被人工锁定 |
| `-32065` | `EventCursorExpired` | 事件游标已超过保留期，必须重新读取快照 |

```json
{
  "jsonrpc": "2.0",
  "id": "invoke-1",
  "error": {
    "code": -32057,
    "message": "状态版本已经变化",
    "data": {
      "name": "RevisionConflict",
      "recoverable": true,
      "revision_domain": "device_state",
      "current_revision": 327,
      "suggested_action": "重新读取状态并再次校验"
    }
  }
}
```

---
