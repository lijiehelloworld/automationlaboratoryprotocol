---
title: "协议契约"
description: "ALP 的符合性边界、协议角色、方法面与交互模式"
---

## 符合性边界

ALP 规范的是客户端与服务端之间可观察的通信行为，包括方法名、请求和响应结构、能力协商、状态一致性、错误、事件、长任务、安全语义及符合性要求。服务端内部采用单体程序、网关、PLC、设备 SDK、独立服务或其他实现方式，不属于协议符合性判断范围。

符合性测试必须只依据以下外部行为：

- `server/discover` 和设备能力清单实际声明的能力；
- 线协议消息及其数据结构定义；
- 方法调用产生的状态、事件、操作任务、证据和错误；
- 版本、权限、修订号、幂等、取消和结果确认语义；
- 能力清单声明与实际可调用能力是否一致。

架构图、内部模块名称、进程数量、数据库、队列、驱动类型和部署拓扑均为非规范性背景。实现可以自由组织内部结构，但不得改变本规范定义的外部行为或绕过安全要求。

## 协议角色

ALP 线协议只定义三个角色：

| 角色 | 协议责任 |
| --- | --- |
| 客户端 | 集成在用户应用、自动化系统或智能体运行时中；发送请求、声明能力、校验响应并保存显式句柄 |
| 服务端 | 提供 ALP 端点；发布设备能力并处理请求、事件、长任务、错误和审计语义 |
| 设备节点 | 由 `device_id` 唯一寻址的能力与状态边界，可以对应单台设备或组合设备 |

用户、交接参与者、设备智能体和物理执行机构可以参与业务过程，但不是新的线协议连接层。ALP 客户端必须集成在调用方内部，不被定义为独立服务。调用方和服务端之间的每次交互始终表现为客户端请求、服务端响应，或已协商事件通道上的服务端事件。

## 对外方法面

ALP 对外接口按方法族组织。除 `server/discover`、`devices/get_manifest` 和 `read` 外，方法族只在服务端明确声明对应能力时才成为该实现的协议表面。

| 方法族 | 核心方法 | 支持条件 | 对外语义 |
| --- | --- | --- | --- |
| 能力发现 | `server/discover`、`devices/get_manifest` | 必须 | 版本协商、设备枚举、能力清单和能力发现 |
| 属性 | `read`、`write` | `read` 必须；`write` 按声明 | 读取状态或修改能力清单声明为可写的属性 |
| 动作 | `invoke` | 按声明 | 调用确定性动作，可试运行、同步完成或转为操作任务 |
| 物理资源 | `physical_resources/list/get/register/update`、`device_supplies/replenish/replace/install/uninstall` | 按声明 | 查询或修改作业对象与设备供给物料的协议事实 |
| 物理资源交接 | `transfers/prepare/get/confirm/cancel` | 按声明 | 确认物理资源进入或离开设备节点边界 |
| 工作流 | `workflows/list/get/create/update/submit/approve/lock/unlock/deprecate/validate/run` | 按声明 | 管理并运行可检查、可版本化的动作组合 |
| 资源 | `resources/list/read` | 按声明 | 读取数据结构定义、图像、报告或大体积结果 |
| 操作任务 | `operations/get/respond/cancel` | 产生长任务时必须 | 查询长任务、补充输入和协作式取消 |
| 事件 | `events/subscribe/poll/unsubscribe` | 声明事件能力时必须 | 获取状态、资源、操作任务和目录变化 |
| 设备智能体 | `agent/describe/invoke` | 按声明 | 获取单设备智能体说明并提交受权规划或执行请求 |

服务端不得在能力清单中声明无法调用的方法、数据结构定义、动作、工作流、事件主题或资源类型。客户端必须以发现结果和能力清单为准，不得根据设备名称或自然语言描述推测未声明接口。

## 交互模式

所有 ALP 能力必须落入以下一种外部交互模式：

| 模式 | 请求结果 | 后续动作 |
| --- | --- | --- |
| 同步查询 | `resultType=complete` | 使用返回值；按 `ttlMs`、`revision` 和新鲜度决定是否缓存 |
| 同步修改或调用 | `resultType=complete`，并在物理执行后包含 `outcome` | 检查状态修订号、证据和结果质量 |
| 长任务 | `resultType=operation` | 使用 `operation_id` 调用 `operations/get`，必要时 `respond` 或 `cancel` |
| 补充输入 | `resultType=input_required` | 使用新请求 ID、原方法、`requestState` 和 `inputResponses` 重试 |
| 事件流 | `events/subscribe` 返回订阅句柄 | 使用 `events/poll` 或已协商事件传输按游标续读 |
| 大体积结果 | 普通结果返回资源 URI | 使用 `resources/read` 读取，不在普通响应中嵌入无上限二进制数据 |

一次标准通信流程为：

```text
discover → get_manifest → read → invoke(dry_run) / workflows/validate
         → write / invoke / workflows/run
         → complete | input_required | operation
         → evidence + final revision
```

`server/discover` 是能力协商入口，不建立隐藏会话。每个后续请求仍必须自带协议版本、客户端能力、身份上下文所需的传输凭据和显式对象引用。服务端可以水平扩展，只要同一 `device_id` 的状态、执行所有权和显式句柄保持一致。

---
