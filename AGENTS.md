# ALL 项目协作与研究记录

## 项目上下文

- 本仓库目前是 ALL / FSP 的 Mintlify 规范文档站，不是已实现的语言引擎或设备网关。
- 正式文档在 `docs/`，网站图片在 `images/`，计划在 `planning/`；`references/` 和 `artifacts/` 是被 Git 忽略的本地资料。
- 首页 `index.mdx`、`docs.json`、`style.css` 留在根目录。移动正式页面时同步更新导航、内部链接和旧地址重定向。
- GitHub 收录正式文档、站点配置、`README.md`、本文件和 `planning/`；Mintlify 通过 `.mintignore` 排除维护记录、项目计划及所有本地参考资料。不要将研究原件、截图或临时输出加入 `docs/` 和 `images/`，也不要仅以不加入导航作为禁止发布的手段。
- 规范依据：[接口契约](docs/specification/base-protocol.mdx)、[设备接口](docs/specification/device-integration/overview.mdx)、[执行器](docs/specification/engine/executor.mdx)、[符合性 C01–C07](docs/specification/conformance.mdx)。外部参考项目研究只保存在本文件和 `planning/research/`，不得写入正式协议文档。
- 保留现有用户修改；所有新增代码注释、Docstring、JSDoc 使用中文。编码前按项目规模执行已有阶段规则。

## JiuwenSymbiosis 研究基线

- 研究日期：2026-09-09。
- 用户指定项目：[GitCode / openJiuwen/jiuwensymbiosis](https://gitcode.com/openJiuwen/jiuwensymbiosis)。网页读取被浏览工具安全策略拦截；用户随后说明已有 SSH 配置，本次使用该配置成功执行只读版本核验。
- 源码阅读来源：[openJiuwen 官方 GitHub 仓库](https://github.com/openJiuwen-ai/jiuwensymbiosis)。通过 GitHub 连接器读取固定提交的文档和源码；GitHub HTTPS clone 因网络连接失败未完成。
- 固定提交：[`6becf1e43a729a9ef393bf620647af6435445f24`](https://github.com/openJiuwen-ai/jiuwensymbiosis/commit/6becf1e43a729a9ef393bf620647af6435445f24)，提交时间为 2026-09-08 02:38:49 UTC。`git ls-remote git@gitcode.com:openJiuwen/jiuwensymbiosis.git HEAD refs/heads/main` 返回的两项均为该提交，与 GitHub 研究快照一致；此结论限定于本次读取的 HEAD/main，不涵盖其他分支或未来更新。
- 验证层级：文档阅读、源码静态核对；未安装上游依赖，未执行其单元测试、模型任务或真机操作。下面“已确认”仅指这一源码快照。

### 1. 项目定位与 adapter 的位置

JiuwenSymbiosis 是基于 openjiuwen 的具身智能执行框架，连接任务规划、感知、动作调用和机器人本体。[S1]

Adapter 是按机器人本体组织的适配包，封装厂商 I/O、环境状态、几何差异、动作实现和会话装配。其主调用关系可概括为：

```text
配置 → Config → Session builder → Env + Api + 可选感知服务
共享 ActionSpec + 本体 @implements 绑定
    → build_robot_tools 按能力筛选
    → Agent / Rails → LocalFunction → Api → Env → Driver → 硬件
    ← 动作结果 / 观测 → 执行记忆与后续规划
```

这不是强制每次调用都逐层经过 Env：机型专属 Api 可通过受控的低层接口读取标定、相机或驱动数据。研究时应沿具体动作追踪，不能仅凭架构图推断完整调用路径。[S1][S4][S7]

### 2. Adapter 文件与职责

以下是上游当前采用的组织方式。[S1][S5]

| 文件或模块 | 职责 | 实现要点 |
| --- | --- | --- |
| `config.py` | 配置加载、连接参数、单位、标定和限位 | 配置描述设备，不混入实验任务文本 |
| `lowlevel.py` | 厂商 SDK、CAN、串口、ROS 等 I/O | 保留既有驱动，隔离供应商差异 |
| `env.py` | 能力、连接/断开、观测、安全属性、驱动委托 | 把可观测状态与硬件边界显式交给上层 |
| `api.py` | 将共享动作绑定到本体实现，处理坐标和姿态差异 | 标准操作语义与设备执行方式分开 |
| `session.py` | 装配 Config、Env、Api 和 sidecar | 生命周期统一收口，不承担业务编排 |
| `config_template.yaml` | 可部署配置起点 | 显式给出单位、超时、校准和安全范围 |
| `geometry.py`、标定模块 | 机型几何与相机标定 | 仅在确有物理差异时增加，不能去掉校准参数 |

`make_builder()` 返回带 `.from_yaml()` / `.from_dict()` 的构建函数。Piper 的 session 使用配置字段映射和检测服务 sidecar，避免重复装配逻辑；创建 Session 不等于已完成硬件连接。[S5]

### 3. 共享动作契约

已确认当前代码采用 `ActionSpec` 与 `@implements(SPEC)`；内置 Piper、SO-101、Cruzr 的 Api 直接继承 `BaseRobotApi`。旧搜索快照中的“以 capability Mixins 为核心”不能作为当前实现依据。[S2][S7]

- `api/decorators.py` 定义 `ActionSpec` / `ToolMeta`；`api/actions.py` 集中声明动作词表并实现 `@implements`。
- `ActionSpec` 包含动作名称、能力条件、参数名及必填参数、结果类型、`requires` / `provides` / `invalidates`、位置产生/消费/失效标记，以及 `opens_access` / `closes_access` 等规划信息。
- `ToolMeta` 持有原始 spec 与本体调用 Schema，不复制一份契约字段。共享语义只维护一处。
- `@implements` 在装饰时检查方法能否接受契约参数，生成调用 Schema 并绑定元数据；缺参可触发 `ContractViolation`。它不等同于完整运行时输入校验，更不证明动作物理正确。
- 参数类型来自本体签名并可由契约 Schema 补充，因此“共享动作名称”不表示所有机器人的参数类型、枚举和姿态能力完全相同。读取具体本体 Schema，不能仅凭动作名移植计划。

### 4. 能力筛选与驱动协议

`build_robot_tools(api, env=env)` 取 Api 能力与 Env 有效能力的交集，再应用 allow/deny 和规划可见性筛选，生成 openjiuwen `LocalFunction`。未传 Env 时只依据 Api 能力；它不是无条件验证硬件就绪的机制。[S4]

Env 的 `effective_capabilities` 可增加由本体模型推导的能力，如可达性所需的 URDF 与运动链信息。能力存在仅表示可提供该类功能；在线状态、标定有效性、当前前置条件仍需另行检查。[S4][S6]

`env/protocol.py` 使用结构化 `typing.Protocol` 按能力切分驱动接口：`RobotDriver` 仅要求 `close()`；笛卡尔、关节、底盘、双臂、夹爪、相机分别有接口，不迫使每台设备实现全部动作。命名关节与索引关节也保留不同接口。[S3]

### 5. 三种本体说明了哪些差异需要留在 adapter

| 本体 | 源码中的主要差异 | Adapter 实现结论 |
| --- | --- | --- |
| Piper | 六轴、倾斜工具的 TIP/FLANGE 变换、夹爪、眼在手视觉 | TCP 偏移和标定不能作为通用固定常量 |
| SO-101 | 五自由度欠驱动、姿态约束与 IK 策略、眼在手外视觉 | 相同移动动作不代表相同姿态保证，需要读取能力与参数限制 |
| Cruzr | 底盘、腰部、升降、双臂，多个相机与 ROS 驱动相关逻辑 | 多执行机构设备需要按能力组合，不能强行套单臂模型 |

以上为实现阅读结论，未做硬件验收。Driver 的运动目标可能使用 FLANGE，Api 对外可能使用 TIP；底盘距离采用米，视觉定位常采用毫米，关节还需核对弧度/角度。新 Adapter 必须记录单位、坐标系和执行完成条件。[S1][S3][S7]

### 6. 状态、结果与安全限制

执行记忆以动作的状态效果和位置失效声明更新；移动本体后旧定位需要失效，定位失败不能沿用旧目标缓存。固定提交还修正了放置目标的残留缓存，并使实际观测只覆盖它明确否定的状态，而不是清空所有同类状态。[S8][S11]

静态阅读确认以下实现边界：

1. `api/memory.py:action_succeeded()` 仅把映射中显式 `ok is False` 判为失败；`None`、普通值和缺少 `ok` 的映射均可被视为成功。[S8]
2. `ExecutionMemory.observe()` 对判定失败的动作直接返回，未覆盖动作部分执行后仍改变物理状态的情况。[S8]
3. `SafetyRail` 的边界来自显式参数或 Env；若边界为 `None`，相应数值范围检查可能跳过。[S9]
4. `BaseRobotEnv.emergency_stop()` 默认无操作；物理急停需要硬件实现。[S6]

### 7. 上游验证器边界

上游提供 `scripts/validate_adapter.py` 做目录、签名、能力和驱动成员检查，`scripts/smoke_test_adapter.py` 用桩驱动调用工具。源码中的 smoke 会把未抛异常的调用标为 `pass`，并以 `_jsonable()` 将无法序列化的值兜底为 `repr()`；它不严格证明业务成功、原始响应可 JSON 序列化或结果符合 Schema，仍需单独完成真机验收。[S10]

## 固定版本源码索引

链接均指向本次核验提交。再次研究时先记录新提交，再核对文档与实现，避免混用旧 Mixin 说明和新动作契约代码。

- [S1：Adapter 参考文档](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/docs/zh/reference/adapter-reference.md)
- [S2：ActionSpec / ToolMeta](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/api/decorators.py)、[共享动作及 implements](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/api/actions.py)
- [S3：Driver Protocol](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/env/protocol.py)
- [S4：工具生成与能力筛选](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/tools/builder.py)
- [S5：共享 Session builder](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/adapters/_common/builder.py)、[Piper 装配实例](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/adapters/piper/session.py)
- [S6：BaseRobotEnv](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/env/base.py)
- [S7：Piper Api](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/adapters/piper/api.py)、[SO-101 Api](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/adapters/so101/api.py)、[Cruzr Api](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/adapters/cruzr/api.py)
- [S8：ExecutionMemory 与成功判定](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/api/memory.py)
- [S9：SafetyRail](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/jiuwensymbiosis/rails/safety.py)
- [S10：静态验证器](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/scripts/validate_adapter.py)、[冒烟检查实现](https://github.com/openJiuwen-ai/jiuwensymbiosis/blob/6becf1e43a729a9ef393bf620647af6435445f24/scripts/smoke_test_adapter.py)
- [S11：感知缓存与观测修正提交](https://github.com/openJiuwen-ai/jiuwensymbiosis/commit/6becf1e43a729a9ef393bf620647af6435445f24)
