# 符合性

## 符合性等级

| 等级 | 必须实现 |
| --- | --- |
| `ALP-Core` | 日期版本、消息、发现、`devices/get_manifest`、`read`、Schema、错误和安全基础 |
| `ALP-Control` | `write` 或 `invoke`、Schema、前置条件、约束、执行锁、dry-run 和审计 |
| `ALP-PhysicalResources` | `PhysicalResource`、`WorkObject`、`DeviceSupply` Schema，统一查询、登记、修改、状态事件及专用操作 |
| `ALP-Transfers` | 本设备边界的 `prepare/confirm/get/cancel`、Transfer Point 和物理资源位置更新 |
| `ALP-Workflow` | `workflows/validate/run`、模板摘要、结果和审计 |
| `ALP-Resources` | `resources/list/read`、URI 和 MIME 类型 |
| `ALP-Operations` | `operations/get`；需要中途输入时实现 `respond`，支持安全取消时实现 `cancel` |
| `ALP-Events` | `events/subscribe/poll/unsubscribe`、主题过滤、游标续读、重复投递去重和过期恢复 |
| `ALP-DeviceAgent` | 单逻辑智能体、`agent/describe/invoke`、计划模式、最小权限和受控执行 |

要求：

- 所有设备 MUST 达到 `ALP-Core`。
- 只读设备可以只实现 `ALP-Core`。
- 改变物理状态的设备 MUST 达到 `ALP-Control`；Workflow 是独立可选等级。
- 管理 Work Object 或 Device Supply 的设备 MUST 达到 `ALP-PhysicalResources`。
- 接受 Physical Resource 进出的设备 MUST 达到 `ALP-Transfers`。
- Device Supply 管理不要求实现采购、仓储或供应链系统。
- 声明 Workflow 能力的设备 MUST 达到 `ALP-Workflow`；未声明时普通 `read/write/invoke` 仍须独立可用。
- 声明 `events=true` 的 Server MUST 达到 `ALP-Events`；仅支持 HTTP 时至少提供 `poll` 交付模式。
- `device_agent` 字段 MUST 保留，能力本身 MAY 不提供。
- 组合设备 MUST 声明成员设备、成员角色、统一状态 revision 和物理执行锁所有权。
- 不支持的可选能力 MUST 从能力声明中省略。

## 必需检查

一致性检查至少包括：

1. `server/discover` 中每个设备都能通过 `devices/get_manifest` 取得一致 Manifest，且其中每个 Property 都能读取或返回规范错误。
2. 每个 Action 都有输入和输出 Schema，并对应真实、已登记的可执行实现。
3. 未知参数在 `additionalProperties=false` 时被拒绝。
4. dry-run 不产生设备写操作。
5. 过期 revision 在执行锁内被拒绝。
6. 同一执行互斥域内的冲突物理动作不能并发进入底层设备执行。
7. 明确失败、超时和结果未知可以区分。
8. `required`、`recommended` 和 `none` 三种结果确认策略按定义处理，软件推导 Evidence 不会被标记为 `confirmed`。
9. 请求正文不能伪造权限。
10. Physical Resource 的稳定 `id`、`kind`、位置、包含关系和 revision 保持一致，容器不形成第三种资源类别。
11. 组合设备的成员标识、成员角色与实际执行边界一致。
12. Device Supply 的登记、补充、替换、安装和卸载检查权限、幂等键与 revision，并记录修改主体、原因、旧值和新值。
13. 外部 Device Supply 在 Transfer confirm 前不能被标记为已安装或已移除。
14. Transfer prepare 不改变最终位置；confirm 原子更新位置、关系、占用和 revision。
15. 交接结果不确定时相关 Physical Resource 进入 `unknown`，依赖其位置的动作被拒绝。
16. 未声明 Workflow 时设备仍可通过核心接口运行；声明后，Workflow 校验不移动设备。
17. Workflow 运行绑定模板版本、revision、摘要和启动设备 revision。
18. 人工锁定的 Workflow 拒绝程序和设备智能体修改。
19. Device Agent 权限不超过调用者、智能体声明和本次授权三者交集。
20. Device Agent 不可用时，普通设备接口仍然可用。
21. 目录结果确定性排序并返回缓存提示；动态状态不进入共享缓存。
22. 每个请求自带版本和能力，未知扩展不会改变核心语义。
23. 流中断后不会自动重放非幂等动作。
24. 跨设备 Physical Resource 运输不被错误地当作本设备的协议事务。
25. 事件可按 `event_id` 去重和续读；游标过期会要求重新读取快照，而不是静默漏报。
26. 符合性测试不依赖 Server 的内部模块、Driver ABI、数据库或部署拓扑。

---
