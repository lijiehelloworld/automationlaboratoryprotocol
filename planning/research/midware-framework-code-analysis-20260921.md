# Midware 通用框架与代码对应分析

日期：2026-09-21。范围：本地框架文档与交付源码静态分析；未连接设备、未运行实机动作或重新执行回归测试。

## 架构定位

`symbiosis-core` 提供 ActionSpec、implements、Registry 和顺序解析/执行。`scientific-instruments` 提供仪器契约、配置校验、Service、WorkflowRuntime、Adapter、Driver、SQLite 持久化和反馈。`instrument-onboarding` 提供审阅候选的溯源校验、配置安装与 Skill 导出。上层规划器不属于运行时包，当前入口为 Python API 与常驻 JSON Lines，生产 MCP 网关未包含在交付代码中。

## 两条主要路径

- 离线接入：设备文档 → 人工/Agent 审阅候选 → onboarding 校验 → extensions 与设备配置 → 契约/配置共同驱动 Function Skill 导出与一致性核对。
- 在线执行：上层计划 → CommandDispatcher/Python API → WorkflowRuntime → Service 门控与资源所有权 → Adapter → Driver → 设备；状态、诊断和完成证据回传。单动作不必经过 WorkflowRuntime。

## 与框架相符的机制

1. ActionSpec 保存契约，ToolMeta 引用 spec；Registry 先验证候选后注册，拒绝冲突绑定，按动作和实现 ID 精确解析。
2. 仪器使用逐动作声明与 action_readiness，运行时再检查版本、参数、资源、对象事实与前置条件。
3. Adapter 负责动作到协议序列，Driver 负责传输与报文；本地串口、SSH 字节桥、HTTP 和 Modbus TCP 分开实现。
4. Skill 从契约和配置导出，连接信息省略；verify-skills 在临时目录重新生成并比对，不覆盖原产物。
5. Service 和 WorkflowRuntime 增加框架未要求的持久化任务、幂等、预留、外部观察、未知状态对账和故障后不自动重放。

## 不应把框架目标当作已验证性质

1. 动作词表和注册表的唯一性作用于当前 Service/Registry；没有跨服务的全局契约权威。
2. bind_adapter 按配置为 adapter.start 动态创建包装方法；绑定检查不能证明每个自定义 Adapter 分支真正实现了动作。device_skills 的 implemented 字段直接置 true，属于声明投影，不是驱动探测结果。
3. connection、protocol 在 DeviceProfile 中是字典；顶层严格校验不代表所有嵌套协议字段均有完整静态 Schema。
4. 构造 Adapter 不代表连接成功；静态能力发现和 Skill 导出不做硬件探测，不能认为连接阶段已经自动缩减所有不可用能力。
5. _device_skill_sources 提供本体特定限制、来源与可观测性说明；若严格采用框架“实现侧没有向规划器传递特有信息通道”的措辞，需要明确这些部署说明的合法边界。
6. 同动作契约便于迁移，但另一台设备的动作就绪、参数范围、对象位置、revision 和完成证据仍需重新满足，不能理解成计划无需适配即可执行。
7. 溯源检查验证摘要与片段存在，不证明候选对协议语义的解释正确。mapped_protocol v1 的成功范围是协议响应，不是异步物理过程完成。

## 关键源码

- `references/midware/00-通用技术框架.md`
- `runtime/packages/symbiosis-core/src/symbiosis_core/contracts.py`
- `runtime/packages/symbiosis-core/src/symbiosis_core/registry.py`
- `runtime/packages/symbiosis-core/src/symbiosis_core/sequence.py`
- `runtime/packages/scientific-instruments/src/scientific_instruments/runtime/service.py`
- `runtime/packages/scientific-instruments/src/scientific_instruments/workflows/runtime.py`
- `runtime/packages/scientific-instruments/src/scientific_instruments/device_skills.py`
- `runtime/packages/scientific-instruments/src/scientific_instruments/skill_verification.py`
- `runtime/packages/instrument-onboarding/src/instrument_onboarding/bundle.py`

上述 runtime 路径相对于 `references/midware/middleware_deployment/`。
