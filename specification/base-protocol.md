---
title: "基础协议"
description: "ALP 生命周期、消息、版本与传输规范"
---

## 生命周期

推荐调用生命周期：

```mermaid
flowchart LR
    D[server/discover]
    R[read state]
    V[dry run / validate]
    X[write / invoke / workflows/run]
    O[complete / operation]
    E[evidence]
    R2[read final state]

    D --> R --> V --> X --> O --> E --> R2
```

1. Client 发现协议版本、设备和能力。
2. Client 读取动作所需的当前状态和 `revision`。
3. Client 使用 Action `dry_run` 检查可执行性；使用 Workflow 时再调用 `workflows/validate`。
4. Client 使用相同 `expected_revision` 正式执行。
5. Server 在执行锁内再次检查状态和 revision。
6. Server 返回同步结果或长任务句柄。
7. Client 检查 Evidence，并重新读取最终状态。

## 事件传递

事件用于通知已发生的协议事实变化，不能代替请求响应，也不能作为动作成功的唯一依据。声明 `events=true` 的 Server MUST 实现：

| 方法 | 作用 | 是否改变设备状态 |
| --- | --- | --- |
| `events/subscribe` | 创建带主题和过滤条件的订阅 | 否 |
| `events/poll` | 按游标读取一批事件，可有限长轮询 | 否 |
| `events/unsubscribe` | 释放订阅 | 否 |

标准事件主题为：

```text
device.state.changed
physical_resource.changed
operation.changed
catalog.changed
```

创建订阅：

```json
{
  "jsonrpc": "2.0",
  "id": "events-subscribe-1",
  "method": "events/subscribe",
  "params": {
    "device_id": "device-001",
    "topics": ["device.state.changed", "physical_resource.changed"],
    "filters": {
      "resource_kinds": ["work_object", "device_supply"]
    },
    "after_event_id": null
  }
}
```

响应 MUST 返回 `subscription_id`、`snapshot_revision`、`expires_at` 和可用的 `delivery_modes`。Core HTTP MUST 支持 `poll`；其他推送方式只能通过扩展协商。

```json
{
  "resultType": "complete",
  "subscription_id": "sub-001",
  "snapshot_revision": 318,
  "expires_at": "2026-08-31T11:00:00+08:00",
  "delivery_modes": ["poll"]
}
```

轮询请求：

```json
{
  "jsonrpc": "2.0",
  "id": "events-poll-1",
  "method": "events/poll",
  "params": {
    "subscription_id": "sub-001",
    "after_event_id": "evt-0098",
    "limit": 100,
    "max_wait_ms": 20000
  }
}
```

事件信封：

```json
{
  "event_id": "evt-0099",
  "topic": "physical_resource.changed",
  "device_id": "device-001",
  "occurred_at": "2026-08-31T10:10:00+08:00",
  "revision_domain": "device_state",
  "revision": 319,
  "data": {},
  "evidence": []
}
```

`events/poll` 的完整结果：

```json
{
  "resultType": "complete",
  "subscription_id": "sub-001",
  "events": [],
  "next_event_id": "evt-0099",
  "has_more": false,
  "subscription_expires_at": "2026-08-31T11:00:00+08:00"
}
```

`events/unsubscribe` 接收 `subscription_id`，成功时返回 `resultType=complete` 和 `unsubscribed=true`。对同一身份重复取消已经结束的订阅 SHOULD 返回相同成功结果；跨身份访问订阅 MUST 返回 `PermissionDenied`。

事件必须满足以下规则：

- `event_id` 在同一 Server 事件域内 MUST 稳定且可用于续读；
- 同一订阅中的事件 MUST 按 Server 观察顺序返回，Client 不得仅依赖到达时间推断跨设备全局顺序；
- Server MAY 重复投递事件，因此 Client MUST 按 `event_id` 去重；
- Server MUST NOT 丢弃仍处于声明保留期内的事件；游标过期时返回 `EventCursorExpired`，并给出需要重新读取的快照范围；
- `max_wait_ms` MUST 有 Server 声明的上限，超时且无事件时返回空 `events` 数组而不是错误；
- 事件只陈述已记录事实。动作的最终结果仍由同步结果或 Operation 终态及其 Evidence 确认；
- HTTP 连接中断后，Client 使用最后已处理的 `event_id` 继续轮询，不得要求 Server 依赖同一 TCP 连接恢复状态。

## 消息

JSON-RPC 固定字段使用其既定名称。ALP 的协议控制字段（例如 `resultType`、`protocolVersion`、`requestId`）使用 lowerCamelCase；设备、对象、动作和参数等领域字段使用 snake_case。实现不得同时发送同一字段的多种命名别名。

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "req-0001",
  "method": "read",
  "params": {
    "device_id": "device-001",
    "path": "device.status",
    "parameters": {}
  },
  "_meta": {
    "alp": {
      "protocolVersion": "2026-08-31",
      "requestId": "req-0001",
      "traceId": "trace-0042",
      "clientInfo": {
        "name": "experiment-client",
        "version": "1.0.0"
      },
      "clientCapabilities": {
        "operations": true,
        "resources": true,
        "events": true,
        "inputRequests": true,
        "physicalResources": true,
        "transfers": true,
        "workflows": true,
        "deviceAgent": false,
        "extensions": {}
      },
      "traceContext": {
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        "tracestate": null,
        "baggage": null
      }
    }
  }
}
```

每个请求 MUST 包含：

- `jsonrpc="2.0"`；
- 唯一请求 `id`；
- `method`；
- `params`；
- `_meta.alp.protocolVersion`；
- `_meta.alp.requestId`；
- 客户端能力声明。

JSON-RPC `id` 与 `_meta.alp.requestId` MUST 是相同的非空字符串；HTTP 使用 `ALP-Request-Id` 时也必须一致。不带 `id` 的通知不能用于 ALP 方法。

`clientInfo` 用于诊断和兼容性判断，不是授权凭据。调用身份必须来自经过验证的连接、令牌、证书或可信本地运行环境。

下文请求示例为突出方法参数，通常省略重复的 `_meta`；实际线协议请求仍必须携带本节规定的完整 `_meta.alp`。

### 完成结果

```json
{
  "jsonrpc": "2.0",
  "id": "req-0001",
  "result": {
    "resultType": "complete",
    "value": {
      "path": "device.status",
      "value": "IDLE",
      "unit": null,
      "quality": "confirmed",
      "source": "device_readback",
      "revision": 318,
      "observed_at": "2026-08-31T10:00:00+08:00",
      "expires_at": null,
      "error": null
    }
  }
}
```

除 JSON-RPC 错误响应外，所有成功响应的 `result` 对象 MUST 包含 `resultType`。下文为简洁起见，部分响应示例只展示 JSON-RPC `result` 对象内部结构。

### 结果类型

| `resultType` | 说明 |
| --- | --- |
| `complete` | 请求已经完成，结果位于当前响应 |
| `input_required` | 需要用户或外部系统补充信息后重试 |
| `operation` | 请求转为长任务，通过 `operations/get` 查询 |

### 执行结果

会改变物理状态的结果 MUST 包含 `outcome`：

```text
succeeded | failed | rejected | unknown
```

- `succeeded`：设备或控制器按 Action 声明的完成条件报告成功。
- `failed`：设备明确报告失败。
- `rejected`：请求未进入设备执行阶段。
- `unknown`：命令可能已经执行，但物理结果无法确认。

`unknown` 禁止被转换为普通成功，也禁止自动重试非幂等动作。

动作可以声明结果确认策略：

```text
required | recommended | none
```

- `required`：缺少规定的设备回读或测量证据时，结果只能为 `unknown`。
- `recommended`：建议返回证据；没有独立测量时仍可以按控制器回执报告动作成功，但物理量质量只能为 `estimated` 或 `unknown`。
- `none`：不要求附加结果证据，适用于纯软件动作或无需物理确认的操作。

默认策略为 `recommended`。设备供应商或部署方可以对高风险 Action 改为 `required`。

### 自包含请求

ALP 核心不建立协议级会话，也不使用隐藏连接状态保存协议版本或客户端能力。每个请求 MUST 自带：

- 协议版本；
- 客户端能力；
- 所需扩展；
- 请求和追踪标识；
- 完成当前请求所需的显式对象、Workflow、Operation 或状态引用。

任意请求都可以被路由到具有相同设备所有权和共享状态访问能力的 Server 实例。应用需要跨请求状态时，Server MUST 签发显式句柄，例如 `operation_id`、`requestState`、`transfer_id` 或 `proposal_id`，并由 Client 在后续请求中传回。

### 扩展协商

本规范已经定义的方法族使用 `clientCapabilities` 与 `server/discover.capabilities` 中的同名字段协商，不重复放入 `extensions`。尚未进入本规范正文的附加能力才通过 `extensions` 显式协商：

```json
{
  "clientCapabilities": {
    "extensions": {
      "com.example.telemetry": {"version": "1"}
    }
  }
}
```

- 扩展标识 MUST 使用稳定、唯一的命名空间。
- `alp/` 前缀保留给本标准；供应商扩展 SHOULD 使用反向域名或其他可证明唯一的前缀。
- Client 和 Server 均声明支持后，Server 才能返回扩展专有结果。
- Client MUST 忽略未知扩展声明，但 MUST NOT 猜测其语义。
- Server MUST 对未协商扩展返回 `UnsupportedCapability`。
- 扩展不能覆盖核心鉴权、安全约束、执行锁和结果语义。
- 破坏性扩展升级 MUST 使用新的扩展标识或主版本后缀。

### 多轮输入

Server MUST NOT 主动向 Client 发起新的反向请求。需要补充参数、确认或授权时，Server 返回 `input_required`。Client 使用新的请求 `id`、原始方法、原始参数、`requestState` 和 `inputResponses` 重试。

`requestState` MUST 是不透明、限时、不可由 Client 篡改的句柄，并绑定原始方法、参数摘要、设备、调用身份和待补充输入。Server MUST 拒绝过期、跨身份、跨设备或已完成的句柄。

这种方式允许每一轮请求独立路由和审计，不要求保持长连接。Server 在重试时 MUST 重新检查截止时间、权限、状态新鲜度和 revision。

### 可缓存目录结果

以下目录结果 MUST 包含缓存提示，并按稳定字段确定性排序：

- `server/discover`；
- Manifest；
- `workflows/list`；
- `resources/list`。

```json
{
  "resultType": "complete",
  "ttlMs": 60000,
  "cacheScope": "private",
  "revision": 18,
  "items": []
}
```

| 字段 | 说明 |
| --- | --- |
| `ttlMs` | Client 可以使用缓存的最长建议时间；`0` 表示必须重新验证 |
| `cacheScope` | `public` 或 `private`；含设备身份、库存或运行状态的结果 MUST 为 `private` |
| `revision` | 目录版本；内容变化时必须递增 |

列表 MUST 按 `name`、`object_type`、`consumable_type` 或其他规范指定的稳定主键排序。动态设备状态和对象实例默认 `ttlMs=0`，不得使用共享缓存。

### 追踪上下文

Client MAY 在 `_meta.alp.traceContext` 中传递 `traceparent`、`tracestate` 和 `baggage`。Server SHOULD 将有效追踪上下文关联到 Workflow、Operation、底层执行和审计记录，但 MUST：

- 校验字段长度和格式；
- 丢弃不可信或超限 baggage；
- 不把追踪字段用于授权；
- 不在追踪字段中放置凭据或敏感样品数据。

### 传输中断

传输连接或响应中断后，Client MUST 认为当前请求结果未知。协议不提供隐式消息重投或响应恢复：

- 只读请求可以使用新的请求 `id` 重发；
- 物理动作必须先通过 Operation、设备回读或状态 revision 确认结果；
- 非幂等动作禁止使用原请求标识直接重放；
- 新请求必须重新携带协议版本和客户端能力。

### Schema 与数据校验

ALP 的 `input_schema`、`output_schema`、输入请求 Schema 和对象字段 Schema 使用 JSON Schema 2020-12 语义。

- Schema MUST 声明根类型；面向信任边界的对象 Schema MUST 明确 `additionalProperties`。
- 数值 MUST 同时声明单位或引用带固定单位的 Property；不得依赖显示文字推断单位。
- 日期时间 MUST 使用带时区的 RFC 3339 字符串。
- 二进制内容 MUST 通过 Resource URI 返回，不得作为无上限 Base64 字段嵌入普通结果。
- `$ref` MUST 指向 Manifest 内定义；声明 `ALP-Resources` 时也可以指向通过 `resources/read` 可读取的不可变 Schema 资源。
- Server MUST 限制 Schema 大小、引用深度、解析时间和循环引用。
- Client MUST 将未知字段视为扩展数据；只有 Schema 明确禁止时才拒绝未知输入字段。
- 对同一名称和版本，Schema 内容摘要 MUST 稳定；内容变化必须更新 revision 或版本。

### 修订号域

revision 只在所属域内比较，不能把不同域的数值相互比较：

| 域 | 适用内容 | 并发控制字段 |
| --- | --- | --- |
| `device_state` | Property、对象位置、耗材安装、Transfer confirm 后的运行状态 | `expected_revision` |
| `manifest` | 设备能力、Schema、约束和成员定义 | Manifest `revision` 或摘要 |
| `catalog` | 可缓存目录内容 | 目录响应 `revision` |
| `workflow` | 单个 Workflow 模板 | 模板 `revision` 与 `template_digest` |

未显式标域的运行时 `revision` 默认属于 `device_state`。`workflows/create/update/lock` 中的 `expected_revision` 属于 `workflow` 域；`workflows/validate/run` 中的 `expected_revision` 属于 `device_state` 域，并同时通过模板版本、模板 revision 和摘要绑定 Workflow。Server MUST 在 `RevisionConflict` 中返回冲突域和当前 revision。

## 版本管理

ALP 使用日期版本：

```text
YYYY-MM-DD
```

Client 使用自己支持的首选日期版本调用 `server/discover`，Server 在响应中返回支持版本列表。双方后续请求使用共同支持的最新版本。Server 收到不支持的版本时 MUST 返回 `UnsupportedProtocolVersion`，并在错误数据中列出其支持版本；Client 不得静默降级。

同一日期版本只能增加兼容性字段或澄清，不得删除字段、改变字段含义或放宽安全语义。破坏性修改 MUST 使用新的日期版本。

功能状态分为：

```text
ACTIVE | DEPRECATED | REMOVED
```

- 弃用功能 MUST 至少保留一个完整日期版本周期。
- Manifest 和目录 MUST 标出弃用状态、替代项和最早移除版本。
- 新实现 SHOULD NOT 采用 `DEPRECATED` 功能。
- `REMOVED` 功能 MUST 返回明确的版本或能力错误，不能静默改变行为。

## 传输

ALP Core 只定义 HTTP 和标准输入输出两种线协议；Code API 是本地语言绑定。其他网络、消息总线或实时流传输必须通过显式扩展定义，不能改变核心消息和结果语义。

#### HTTP

远程 Server SHOULD 使用单一端点：

```text
POST /alp
```

请求头：

```http
ALP-Protocol-Version: 2026-08-31
ALP-Method: invoke
ALP-Name: move_object
ALP-Request-Id: req-0001
Content-Type: application/json
Accept: application/json
```

`ALP-Method`、`ALP-Name` 和 `ALP-Request-Id` 使网关可以在不解析请求正文的情况下完成路由、鉴权、限流、审计和计量。`ALP-Name` 仅在请求引用明确动作、Workflow 或资源时使用。HTTP 头和 JSON-RPC 正文冲突时，Server MUST 返回 `HeaderMismatch`。

HTTP 请求 MUST 是自包含请求。Server MUST NOT 使用 Cookie 或隐式连接会话保存协议能力。设备所有权、执行锁和运行状态可以保存在共享后端，但必须通过显式设备 ID 和句柄访问。

- 成功解析的 JSON-RPC 请求 SHOULD 返回 HTTP `200`，应用错误放在 JSON-RPC `error` 中。
- 身份凭据缺失或无效可以使用 HTTP `401`；身份有效但无权限可以使用 `403`。
- 不支持的媒体类型使用 `415`，超限请求使用 `413`，限流使用 `429`。
- HTTP 重定向不得把授权头转发到未验证的不同来源。
- 长任务进度通过显式 Operation 查询，不依赖保持单个 HTTP 响应连接。

### 标准输入输出

本地进程可以通过标准输入输出传输 JSON-RPC 消息。默认帧格式为 UTF-8 JSON Lines：每行一个完整 JSON 对象，以 `LF` 结束。

- 每条协议消息 MUST 可独立解析；
- 单条消息中的换行符 MUST 使用 JSON 转义，不能跨行形成一个帧；
- 实现 MUST 设置最大帧大小，并对超限消息返回协议错误后终止该帧；
- 诊断日志 MUST 写入标准错误；
- 日志 MUST NOT 混入标准输出中的协议消息。

### 代码接口

嵌入式实现可以提供同名接口：

```text
request(method, params, meta)
discover()
get_manifest(device_id)
read(device_id, path, parameters)
write(device_id, path, value, options)
invoke(device_id, action, arguments, options)
```

`request` 可以访问实现声明的全部核心和可选方法；其他函数只是便利封装。Code API MUST 保留相同方法名、参数结构、权限、校验、执行互斥和结果语义，不能成为绕过协议安全边界的私有入口。

---
