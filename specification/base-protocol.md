---
title: "基础协议"
description: "ALL 远程 HTTPS、JSON-RPC、消息、版本、缓存和数据结构规范"
---

## 协议边界

ALL 规范客户端与实验室设备服务端之间可观察的远程通信行为。服务端内部的驱动、数据库、队列、控制器、进程和部署拓扑不属于符合性判断范围。

ALL 线协议固定使用 HTTPS 远程连接。

## 远程端点

一个 ALL 服务端必须提供一个稳定 HTTPS 端点，例如：

```text
POST https://lab.example.com/all
```

所有 JSON-RPC 请求使用 HTTP `POST`。服务端不得依赖 Cookie、连接粘性或隐藏协议会话。任何请求都必须能由持有相同设备状态的服务实例独立处理。

## HTTP 请求

```http
POST /all HTTP/1.1
Host: lab.example.com
Authorization: Bearer <access-token>
Content-Type: application/json
Accept: application/json
ALL-Protocol-Version: 2026-08-31
ALL-Method: operations/invoke
ALL-Name: move_object
ALL-Request-Id: req-0001
```

| 请求头 | 必填 | 说明 |
| --- | --- | --- |
| `Authorization` | 是 | OAuth Bearer 访问令牌 |
| `Content-Type` | 是 | 必须为 `application/json` |
| `Accept` | 是 | 必须接受 `application/json` |
| `ALL-Protocol-Version` | 是 | 当前请求使用的日期版本 |
| `ALL-Method` | 是 | 与 JSON-RPC `method` 完全相同 |
| `ALL-Name` | 条件必填 | 请求引用操作或 Workflow 名称时必须提供 |
| `ALL-Request-Id` | 是 | 与 JSON-RPC `id`、`_meta.all.requestId` 完全相同 |

头部与正文冲突时，服务端必须返回 `HeaderMismatch`。网关可以使用头部完成路由、限流、鉴权和审计，但业务处理仍必须校验完整正文。

## 请求消息

```json
{
  "jsonrpc": "2.0",
  "id": "req-0001",
  "method": "operations/invoke",
  "params": {
    "device_id": "device-001",
    "name": "move_object",
    "object_bindings": {"target": ["object-001"]},
    "arguments": {"target_location": "workspace.output"}
  },
  "_meta": {
    "all": {
      "protocolVersion": "2026-08-31",
      "requestId": "req-0001",
      "clientInfo": {
        "name": "laboratory-agent",
        "version": "1.0.0"
      },
      "clientCapabilities": {
        "inputRequired": true,
        "operationTasks": true
      }
    }
  }
}
```

| 字段 | 必填 | 规则 |
| --- | --- | --- |
| `jsonrpc` | 是 | 固定为 `2.0` |
| `id` | 是 | 非空字符串；一次请求内唯一 |
| `method` | 是 | 必须属于四个命名空间之一 |
| `params` | 是 | 对象；不得为数组或 `null` |
| `_meta.all.protocolVersion` | 是 | 与 HTTP 版本头一致 |
| `_meta.all.requestId` | 是 | 与 `id` 和请求头一致 |
| `_meta.all.clientInfo` | 是 | 客户端名称和版本；不得用于授权 |
| `_meta.all.clientCapabilities` | 是 | 客户端可处理的交互能力 |

ALL 不允许 JSON-RPC 通知和批处理。每个请求必须有 `id`，每个 HTTP 请求正文只能包含一个 JSON-RPC 请求。

## 方法命名空间

所有标准方法只能属于以下四个命名空间：

```text
system/*
objects/*
operations/*
workflows/*
```

服务端不得在标准能力清单中发布其他顶层命名空间。

## 成功响应

```json
{
  "jsonrpc": "2.0",
  "id": "req-0001",
  "result": {
    "resultType": "complete",
    "outcome": "succeeded",
    "value": {},
    "error": null
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

每个成功 `result` 必须包含 `resultType`。`serverInfo` 只用于显示和调试，不得用于授权或能力推断。

## 结果类型

| `resultType` | 说明 |
| --- | --- |
| `complete` | 请求已经完成，结果在当前响应中 |
| `input_required` | 需要调用者补充结构化输入后重试原请求 |
| `operation` | 请求转为可查询的长任务 |

### 完成结果

改变状态的完成结果必须包含：

```typescript
interface CompleteExecutionResult {
  resultType: "complete";
  outcome: "succeeded" | "failed" | "unknown";
  value: unknown | null;
  previous_state_revision: number | null;
  new_state_revision: number | null;
  started_at: string;
  completed_at: string;
  evidence_ids: string[];
  error: ExecutionError | null;
}
```

一旦物理执行已经开始，明确失败或结果未知也必须返回普通 `result`，不得改用缺少执行上下文的 JSON-RPC 错误。

### 补充输入结果

```json
{
  "resultType": "input_required",
  "requestState": "opaque-request-state",
  "inputRequests": [
    {
      "id": "approval-1",
      "title": "确认执行",
      "description": "该操作需要人工确认。",
      "schema": {
        "type": "object",
        "properties": {"approved": {"type": "boolean"}},
        "required": ["approved"],
        "additionalProperties": false
      },
      "sensitive": false,
      "expires_at": "2026-08-31T10:22:00+08:00"
    }
  ]
}
```

客户端使用新的请求 `id` 重试相同方法和业务参数，并携带：

```json
{
  "requestState": "opaque-request-state",
  "inputResponses": {
    "approval-1": {"approved": true}
  }
}
```

`requestState` 必须不可伪造、短期有效，并绑定主体、客户端、方法和原始参数摘要。服务端必须重新执行权限和易变状态校验。

### 长任务结果

```json
{
  "resultType": "operation",
  "operation_id": "op-001",
  "status": "queued",
  "poll_after_ms": 500
}
```

客户端通过 `operations/get` 查询，不能依赖原 HTTP 连接保持打开。

## JSON-RPC 错误

请求在物理执行开始前被拒绝时返回 JSON-RPC `error`：

```json
{
  "jsonrpc": "2.0",
  "id": "req-0001",
  "error": {
    "code": -32007,
    "message": "设备当前状态不满足操作前置条件",
    "data": {
      "name": "PreconditionFailed",
      "recoverable": true,
      "details": [],
      "suggested_action": "重新读取系统和对象状态"
    }
  }
}
```

错误编码和数据结构见[错误](./errors)。

## HTTP 状态

| HTTP 状态 | 使用场景 |
| --- | --- |
| `200` | JSON-RPC 成功响应或已认证请求的 JSON-RPC 错误 |
| `400` | 无法解析的 HTTP/JSON 请求 |
| `401` | 缺少或无效访问令牌 |
| `403` | 身份有效但权限不足 |
| `404` | ALL 端点不存在；不得用于泄露隐藏设备或对象 |
| `405` | 使用了非 `POST` 方法 |
| `413` | 请求超过服务端限制 |
| `415` | 不支持的媒体类型 |
| `429` | 传输层限流；必须提供合理重试提示 |
| `500` | 无法形成规范 JSON-RPC 响应的服务端故障 |

业务繁忙、前置条件失败、对象不存在和设备执行失败应使用 JSON-RPC 结果或错误，不应使用通用 HTTP `500`。

## 协议版本

ALL 使用日期版本：

```text
YYYY-MM-DD
```

- 每个请求必须携带一个明确版本。
- `system/discover` 返回双方共同支持的版本。
- 不支持请求版本时必须返回 `UnsupportedProtocolVersion` 和服务端支持列表。
- 同一日期版本只能增加兼容字段或澄清，不得删除字段、改变含义或降低安全要求。
- 破坏性变更必须使用新的日期版本。
- 客户端不得静默降级到未获允许的旧版本。

## 无会话原则

ALL 不建立协议级会话，不发送会话标识。跨请求状态必须使用显式句柄：

- `object_id`；
- `operation_id`；
- `subscription_id`；
- `requestState`；
- `validation_token`。

句柄必须绑定身份与权限上下文，不得跨主体复用。服务端可以水平扩展，但必须保证显式句柄和设备执行所有权的一致性。

## 数据结构定义

ALL 使用 JSON Schema 2020-12 语义：

- 每个数据结构必须声明根类型；
- 信任边界上的对象必须明确 `additionalProperties`；
- 数值必须同时声明单位或引用固定单位定义；
- 时间必须使用带时区 RFC 3339 字符串；
- 标识必须声明最小长度和稳定性要求；
- 服务端必须限制数据结构大小、引用深度、解析时间和循环引用；
- 能力清单内引用必须可解析，不能返回悬空引用；
- 同一名称与版本的数据结构内容必须稳定。

普通结果不得嵌入无上限二进制数据。需要返回图像、文件或报告时，由操作结果提供经过授权、短期有效的 HTTPS 下载地址及内容摘要；下载地址不构成新的 ALL 方法族。

## 缓存

可缓存目录结果必须包含：

```json
{
  "resultType": "complete",
  "ttlMs": 60000,
  "cacheScope": "private",
  "revision": 18,
  "not_modified": false,
  "items": []
}
```

| 字段 | 规则 |
| --- | --- |
| `ttlMs` | 大于或等于 `0`；`0` 表示每次使用前重新验证 |
| `cacheScope` | 带身份的 ALL 结果固定为 `private` |
| `revision` | 所属目录修订号；语义内容变化时递增 |
| `not_modified` | 仅在请求修订号与当前修订号相等时为 `true` |

缓存必须按资源标识、发行方、主体、客户端、权限摘要、协议版本和方法隔离。

## 修订号域

| 域 | 内容 |
| --- | --- |
| `manifest` | 四模块能力定义 |
| `system_state` | 设备公共运行状态 |
| `object_catalog` | 对象目录 |
| `object` | 单个对象实例 |
| `operation` | 单个操作任务 |
| `workflow_catalog` | Workflow 目录 |

不同域的修订号不得相互比较。需要并发控制的方法必须明确参数所属域。

## 传输中断

- 只读请求可以使用新请求标识重新发送。
- 改变状态的请求不得因网络错误直接重放。
- 客户端必须通过 `operations/get`、`system/get_status` 或 `objects/get` 确认结果。
- 无法确认物理结果时必须按 `unknown` 处理。
