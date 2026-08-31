---
title: "符合性"
description: "ALL 四模块实现要求和检查清单"
---

## 符合性声明

实现必须声明：

```json
{
  "protocol_version": "2026-08-31",
  "transport": "https",
  "authentication": "oauth2.1",
  "modules": {
    "system": true,
    "objects": true,
    "operations": true,
    "workflows": true
  }
}
```

`system` 和 `operations` 为必需模块。没有研究对象的只读设备可以声明 `objects=false`；不提供模板的设备可以声明 `workflows=false`。

## 系统模块

所有实现必须：

- 只提供 HTTPS 远程端点；
- 发布 OAuth 受保护资源元数据；
- 验证访问令牌发行方、受众、有效期和权限；
- 实现 `system/discover`、`system/get_manifest` 和 `system/get_status`；
- 返回四模块结构的能力清单；
- 支持明确协议版本和无会话请求；
- 对目录提供稳定顺序、修订号和私有缓存提示；
- 使用结构化错误；
- 对改变状态的请求保存审计记录。

声明事件能力时必须同时实现：

```text
system/events/subscribe
system/events/poll
system/events/unsubscribe
```

## 研究对象模块

声明 `objects=true` 时必须：

- 只使用 `ResearchObject`（研究对象）模型；
- 发布 `identity`、`sample`、`container`、`evidence`、`provenance` 与扩展字段的完整类型 Schema；
- 实现 `objects/list` 和 `objects/get`；
- 明确是否支持 `objects/register` 和 `objects/update`；
- 强制研究对象数据结构、位置、包含关系、证据、来源和修订号；
- 禁止用研究对象更新接口伪造物理动作或覆盖来源记录；
- 对不存在和不可见对象使用不泄露信息的错误语义。

## 操作模块

所有实现必须：

- 实现 `operations/list` 和 `operations/read`；
- 为每个操作声明工作站命名空间、种类、数据结构、权限、研究对象角色、前置条件、注意事项、强制/建议约束、状态变化、返回与执行属性；
- 只允许调用能力清单中的操作；
- 在物理执行前完成完整校验和锁内复验；
- 采用先校验、后提交：强制约束失败不得提交研究对象状态，建议约束失败必须返回警告诊断；
- 区分成功、失败和未知结果；
- 对非幂等操作禁止盲目重放。

声明写入或调用时实现相应接口：

```text
operations/write
operations/invoke
```

可能返回长任务时必须实现 `operations/get`；可能请求输入时必须实现 `operations/respond`；声明可安全取消时必须实现 `operations/cancel`。

## Workflow 模块

声明 `workflows=true` 时必须且只能公开以下标准 Workflow 接口：

```text
workflows/list
workflows/get
workflows/validate
workflows/run
```

实现必须：

- 以 `name + version + digest` 固定模板；
- 支持顺序、有限循环、条件分支、并行汇合和受保护区间五种组合算子，以及 `operation`、`assert`、`wait` 叶子节点；
- 验证全部内部操作和对象引用；
- 拒绝循环无界、分支歧义、并行写冲突和无法保持连续的受保护区间；
- 计算并执行权限范围并集；
- 在运行时重新校验状态、对象和前置条件；
- 保存逐步审计结果；
- 在未知物理结果后停止后续物理步骤。

## 必需测试

符合性测试至少覆盖：

1. 缺少、过期、错误发行方和错误受众令牌；
2. 权限不足和权限范围提示；
3. 协议版本不支持及头部正文冲突；
4. `system/discover` 和能力清单缓存复验；
5. 四模块之外的方法拒绝；
6. 研究对象固定分区、关系、证据/来源追加、修订号和并发冲突；
7. 操作参数、研究对象角色、前置条件、MUST/SHOULD 诊断和锁竞争；
8. `dry_run` 不接触物理设备；
9. 同步成功、明确失败和结果未知；
10. 长任务查询、输入响应和安全取消；
11. 工作流固定摘要、校验句柄过期、五类组合算子及其结构错误；
12. 事件至少一次投递、游标续读和过期恢复；
13. 日志和错误中不泄露凭据或隐藏资源；
14. 连接中断后非幂等操作不被自动重放。

## 判定边界

符合性只根据远程可观察行为判断。内部驱动、数据库、队列、程序语言、设备 SDK 和部署方式不影响符合性，只要它们不能绕过 ALL 的权限、安全、状态和审计要求。
