---
title: "安全与保障"
description: "身份、授权、设备安全、幂等、审计与可观察执行"
---

## 身份与授权

- 非本机远程连接 MUST 使用经过验证的加密传输；标准输入输出和同进程 Code API 不适用该要求。
- 写动作 MUST 使用经过验证的身份机制。
- 请求正文、设备描述、资源文字和智能体输出不能自行授予权限。
- 高风险动作 MAY 要求独立人工授权。
- 授权 MUST 限定设备、动作、参数范围和有效期。
- Server MUST 把访问凭据绑定到已验证的签发方、预期受众和客户端身份；同名主体来自不同签发方时不得视为同一身份。
- 凭据包含签发方、受众、有效期或生效时间时，Server MUST 全部验证，不能只验证签名。
- Server MUST NOT 把某一签发方取得的注册信息、密钥或令牌复用于另一签发方。
- 公共客户端、机密客户端和设备本机客户端 SHOULD 使用不同的注册类型和凭据策略；不能安全保存密钥的客户端不得被要求持有长期共享密钥。
- 访问令牌、客户端密钥和授权码 MUST NOT 放入请求参数、查询字符串、Manifest、Resource URI 或日志。

## 设备安全

- 本地设备控制与安全层 MUST 强制硬件限位和底层参数范围。
- Server MUST 强制 Schema、前置条件、状态新鲜度和约束。
- 急停和安全门 MUST 在网络或智能体不可用时继续有效。
- 原始串口、任意寄存器写入、维修和强制动作 MUST NOT 作为普通能力公开。
- 所有真实硬件入口 MUST 共享同一设备执行锁。

## 幂等与重试

- `read` 可以安全重试。
- 纯软件 `write` 只有明确声明幂等时才可以自动重试。
- 物理 `write`、`invoke` 和 `workflows/run` 默认非幂等。
- `ResultUnknown` 后 MUST 先重新读取设备和现场状态。
- `requestId` 只用于追踪，不自动提供幂等性。
- 只有能力明确声明支持去重时，Client 才可发送 `idempotency_key`。Server 必须把该键绑定到调用身份、设备、方法和规范化参数摘要；同一键对应不同参数时必须拒绝。

## 审计

物理写动作的审计记录 MUST 至少包含：

```text
request_id
trace_id
verified_actor
authorized_by
device_id
method
action_or_workflow
validated_arguments
previous_revision
new_revision
started_at
completed_at
outcome
error
evidence_ids
```

审计日志 MUST NOT 记录密码、访问令牌或无必要的敏感样品信息。

## 可观察执行要求

本标准不规定 Server 如何连接底层设备，只规定对 Client 可观察的执行结果：

- 每个公开 Property 和 Action MUST 来源于已登记实现，不能只存在于说明文字中；
- Client 只能选择 Manifest 声明的路径、Action 和参数，不能通过标准接口传入任意串口帧、寄存器地址、SDK 方法或原始设备命令；
- Server 在接触物理设备前 MUST 完成身份、Schema、权限、revision、前置条件、约束和执行互斥检查；
- 底层仅报告“命令已发送”时，Server MUST NOT 返回 `outcome=succeeded`；
- 底层明确完成、明确失败或无法确认时，ALP 结果 MUST 分别表现为 `succeeded`、`failed` 或 `unknown`；
- 设备断连、超时、部分执行和重连不得改变幂等及重试规则；
- 取消请求只有在设备达到可确认的安全终态后才能返回 `CANCELLED`，否则返回当前状态或 `UNKNOWN`；
- Server MUST 将底层错误转换为本规范定义的结构化错误或执行结果，不得要求 Client 解析供应商日志；
- Server 内部的任何控制入口都不得扩大经 ALP 验证的调用权限或绕过设备安全机制。

---
