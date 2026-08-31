---
title: "协议契约"
description: "ALP 的符合性边界、协议角色、方法面与交互模式"
---

## 符合性边界

ALP 规范的是 Client 与 Server 之间可观察的通信行为，包括方法名、请求和响应结构、能力协商、状态一致性、错误、事件、长任务、安全语义及符合性要求。Server 内部采用单体程序、网关、PLC、设备 SDK、独立服务或其他实现方式，不属于协议符合性判断范围。

符合性测试 MUST 只依据以下外部行为：

- `server/discover` 和 Device Manifest 实际声明的能力；
- 线协议消息及其 Schema；
- 方法调用产生的状态、事件、Operation、Evidence 和错误；
- 版本、权限、revision、幂等、取消和结果确认语义；
- Manifest 声明与实际可调用能力是否一致。

架构图、内部模块名称、进程数量、数据库、队列、Driver 类型和部署拓扑均为非规范性背景。实现可以自由组织内部结构，但不得改变本规范定义的外部行为或绕过安全要求。

## 协议角色

ALP 线协议只定义三个角色：

| 角色 | 协议责任 |
| --- | --- |
| Client | 集成在用户应用、自动化系统或智能体运行时中；发送请求、声明能力、校验响应并保存显式句柄 |
| Server | 提供 ALP 端点；发布设备能力并处理请求、事件、长任务、错误和审计语义 |
| Device Node | 由 `device_id` 唯一寻址的能力与状态边界，可以对应单台设备或组合设备 |

User、Handoff Actor、设备智能体和物理执行机构可以参与业务过程，但不是新的线协议连接层。ALP Client MUST 集成在调用方内部，不被定义为独立服务。调用方和 Server 之间的每次交互始终表现为 Client 请求、Server 响应，或已协商事件通道上的 Server 事件。

## 对外方法面

ALP 对外接口按方法族组织。除 `server/discover`、`devices/get_manifest` 和 `read` 外，方法族只在 Server 明确声明对应能力时才成为该实现的协议表面。

| 方法族 | 核心方法 | 支持条件 | 对外语义 |
| --- | --- | --- | --- |
| Discovery | `server/discover`、`devices/get_manifest` | 必须 | 版本协商、设备枚举、Manifest 和能力发现 |
| Properties | `read`、`write` | `read` 必须；`write` 按声明 | 读取状态或修改 Manifest 声明为可写的属性 |
| Actions | `invoke` | 按声明 | 调用确定性 Action，可 dry-run、同步完成或转为 Operation |
| Physical Resources | `physical_resources/list/get/register/update`、`device_supplies/replenish/replace/install/uninstall` | 按声明 | 查询或修改 Work Object 与 Device Supply 的协议事实 |
| Transfers | `transfers/prepare/get/confirm/cancel` | 按声明 | 确认 Physical Resource 进入或离开 Device Node 边界 |
| Workflows | `workflows/list/get/create/update/submit/approve/lock/unlock/deprecate/validate/run` | 按声明 | 管理并运行可检查、可版本化的 Action 组合 |
| Resources | `resources/list/read` | 按声明 | 读取 Schema、图像、报告或大体积结果 |
| Operations | `operations/get/respond/cancel` | 产生长任务时必须 | 查询长任务、补充输入和协作式取消 |
| Events | `events/subscribe/poll/unsubscribe` | 声明事件能力时必须 | 获取状态、资源、Operation 和目录变化 |
| Device Agent | `agent/describe/invoke` | 按声明 | 获取单设备智能体说明并提交受权规划或执行请求 |

Server MUST NOT 在 Manifest 中声明无法调用的方法、Schema、Action、Workflow、事件主题或资源类型。Client MUST 以发现结果和 Manifest 为准，不得根据设备名称或自然语言描述推测未声明接口。

## 交互模式

所有 ALP 能力必须落入以下一种外部交互模式：

| 模式 | 请求结果 | 后续动作 |
| --- | --- | --- |
| 同步查询 | `resultType=complete` | 使用返回值；按 `ttlMs`、`revision` 和新鲜度决定是否缓存 |
| 同步修改或调用 | `resultType=complete`，并在物理执行后包含 `outcome` | 检查状态 revision、Evidence 和结果质量 |
| 长任务 | `resultType=operation` | 使用 `operation_id` 调用 `operations/get`，必要时 `respond` 或 `cancel` |
| 补充输入 | `resultType=input_required` | 使用新请求 ID、原方法、`requestState` 和 `inputResponses` 重试 |
| 事件流 | `events/subscribe` 返回订阅句柄 | 使用 `events/poll` 或已协商事件传输按游标续读 |
| 大体积结果 | 普通结果返回 Resource URI | 使用 `resources/read` 读取，不在普通响应中嵌入无上限二进制数据 |

一次标准通信流程为：

```text
discover → get_manifest → read → invoke(dry_run) / workflows/validate
         → write / invoke / workflows/run
         → complete | input_required | operation
         → evidence + final revision
```

`server/discover` 是能力协商入口，不建立隐藏会话。每个后续请求仍 MUST 自带协议版本、客户端能力、身份上下文所需的传输凭据和显式对象引用。Server 可以水平扩展，只要同一 `device_id` 的状态、执行所有权和显式句柄保持一致。

---
