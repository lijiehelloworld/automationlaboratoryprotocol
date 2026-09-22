# FSP 从实现提炼规范的修订记录

日期：2026-09-21。来源任务：[分析 midware 参考资料](codex://threads/01a0bc4c-9479-7731-beb4-b7549419bb25)。

范围：参考任务、现有研究记录、框架说明和本地源码静态阅读；没有连接设备，没有运行参考实现测试，没有发布或认定该实现符合本轮草案。正式文档只提炼通用协议规则，不收录厂商代码、特定类名或历史验收结论。

## 来源与规范落点

运行时代码路径以下均相对于 `references/midware/middleware_deployment/`。

| 参考材料 | 提炼内容 | 正式落点 |
| --- | --- | --- |
| `references/midware/00-通用技术框架.md` | 共享契约、精确绑定、静态 Skill 与运行事实分离 | `docs/specification/fsp/capabilities.mdx` CAP01–04 |
| `runtime/packages/symbiosis-core/src/symbiosis_core/registry.py` | 批量注册原子生效、无跨设备默认兜底 | CAP02、ADP01、C08 |
| `runtime/packages/scientific-instruments/src/scientific_instruments/runtime/service.py` | 受理、幂等、资源所有权、回执和实测分离、外部观察、未知恢复 | `fsp/lifecycle.mdx` LIF01–06、OPS01–03、SYS01–02 |
| `runtime/packages/scientific-instruments/src/scientific_instruments/device_skills.py` | 能力描述是声明投影而非驱动探测，部署限制及来源需要显式表达 | CAP03–04、C09 |
| [既有研究记录](midware-framework-code-analysis-20260921.md) 中的 onboarding、Adapter、Driver 分层 | 审阅材料与映射的责任边界、溯源不等于语义正确、协议回执不等于物理完成 | `device-integration/overview.mdx` ADP01–04 |

## 明确不是照搬实现

1. 参考 Service 存在顶层 `operation_id`；本轮规范请求统一为 `operation.operation_id`。既有实现需要版本化适配，不能直接宣称原生符合。
2. 参考请求指纹基于其规范化请求；本规范明确要求覆盖契约/定义版本、目标、对象版本及安全条件，并排除通信跟踪 ID。必须对实际实现逐项验证。
3. `implemented: true` 或动态包装绑定不能证明驱动动作分支完整。规范增加实现、就绪与运行时分别报告要求。
4. 参考交付入口为 Python API 和 JSON Lines，未把生产 MCP 网关视为已交付。正式文档的 MCP、HTTP、CLI 仅为等价承载规则。
5. 本轮是对协议草案的细化，不代表所有规则已被该参考实现满足，也不是既有 `0.1` 版本的正式发布。实现需要声明文档版本或提交并逐项验证。

## 本轮主要变化

- 新增能力/契约和任务生命周期两页，贯通版本、幂等、锁、取消、未知和重启。
- 修正对象事实只能在成功后更新的旧表述，保留失败时的部分变化与字段失效。
- 用一份规范请求/受理响应和承载映射表替代三份重复样例，避免不同承载的示例漂移。
- 编译、仿真、执行例子统一对象数组和嵌套操作标识；执行未知结果不再伪报成功。
- C01–C07 保留，新增 C08–C22 行为场景；这是验收要求，不是已执行的测试报告。
- 保留本轮之前已有的目录重组、重定向和未提交内容；未改动研究原件及设备运行时代码。

## 本地来源摘要

用于识别本次阅读的本地快照，不代表上游版本或验收结果：

| 文件 | SHA-256 |
| --- | --- |
| 框架说明 | `f5f1d8e6563e8ee21f7c2169008bca2dde4c80a516d82beca2a9571456fd46f8` |
| registry.py | `ac267e3531f66fa8a043a7252af3b3ea58adcf82ae945fab97655b6d6223cac2` |
| service.py | `105ccde8e072c5f84fb4d6417be1a32c0ca3ed0b31aa8d9ea0bc2a1b3c8eaf3c` |
| device_skills.py | `965bb556140796310c69a8f7647dce12795ad086c818cd41d410fc2685a65265` |

## 文档验证与未验证项

- 导航 28 页、25 条重定向及站内链接静态检查通过；17 个 JSON 示例均可解析。
- 编译、仿真、执行示例检查了嵌套操作标识、来源/目标角色和预期对象修订号；C01–C22 编号完整。
- Mintlify `broken-links` 检查通过；`git diff --check` 通过，另外检查了未跟踪 MDX 的行尾空白。
- Mintlify `validate` 未完成：共享预览缓存 `.mintlify/previews/shared-last/.../.next/BUILD_ID` 的清理操作被沙箱以 EPERM 拒绝。没有为此修改权限或删除共享预览。
- 未执行浏览器视觉验收、设备仿真/真机验收，未生成完整机器可读 Schema 或符合性测试运行器，未提交或发布。
