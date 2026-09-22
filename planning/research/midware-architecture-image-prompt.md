# Midware architecture image prompt

Mode: built-in GPT Image, followed by a targeted correction pass.

Use case: infographic-diagram. Create a polished high-resolution landscape technical architecture diagram, wide 16:10 format, white background, crisp Chinese typography with exact English code identifiers. Title: "异构仪器中间件 · 代码架构". Subtitle: "动作契约 · 能力门控 · Adapter ｜ 基于当前交付源码". Flat technical vector-like bitmap design, navy text, blue execution modules, teal offline modules, purple shared core, amber dashed future extension. Clear whitespace, no photos, no robot mascots, no decorative 3D. Diagram must be readable, not a wall of text.

Layout: main middle execution column occupying 60% width, offline column left 23%, support column right 17%. Package boundaries explicit. Top external band across middle/right: "上层规划器 / Agent / 人" with small caption "生成计划 · 读取结果"; beneath it box "Python API / JSON Lines" then arrow down into large central boundary titled "scientific-instruments". An amber dashed small box beside top band "MCP 网关（待接入）", explicitly future not existing, dashed connector only to existing entry.

Inside central package stack:
1 "CommandDispatcher" / "命令与参数校验"
2 "WorkflowRuntime" / "模板展开 · 顺序执行 · 结果引用"
3 large core box "Service" with three short rows "动作就绪 · 参数范围 · 实时前提", "revision · 幂等 · 设备与容器锁", "任务状态 · 取消 · unknown 对账"
4 "Adapter" row with three aligned cells: "CleaningAdapter", "UltrasonicAdapter", "CentrifugeAdapter"
5 aligned driver row: "串口 JSON / SSH桥", "HTTP JSON", "Modbus TCP"
outside package bottom hardware row: simple line icons "清洗加注", "超声", "离心机".
Downward blue arrows represent requests; one upward teal arrow routed on right edge of central stack from hardware through service to planner labeled "状态 / 结果 / 完成证据". Don't imply physical sensors exist for all devices.

Left column top: bounded teal package "instrument-onboarding": "设备文档 + 人工/Agent审阅" → "候选校验 / 溯源绑定" → "扩展配置". Small note "ASCII串口行 / HTTP JSON". Arrow from extension configuration to central Service/Adapter with small label "mapped_protocol"; keep mapped_protocol represented as a fourth small adapter box beneath/beside the three native adapters without connecting it to specific physical device.
Left middle separate source card "deployment.json" / "连接 · 协议 · 限值 · 动作就绪" with arrow into Service and into offline export.
Left bottom separate card "Skill 导出 / 一致性校验" → "Function Skills" / "SKILL.md · Schema · 摘要". Arrow from Function Skills up to planner labeled "静态能力描述". A source arrow from shared core contract to exporter. Important: Function Skills never connect directly to hardware. Small note "不含端点与凭据".

Right column under top external band: purple bounded package "symbiosis-core" with three internal cards "ActionSpec / implements", "Registry", "parse_sequence / run_sequence". Fine dependency connectors to central workflow and Service labeled "共享契约与绑定". Below purple package two blue-tinted support cards belonging to central runtime: "SQLite Store" / "任务 · 幂等键 · 对象版本"; "FeedbackMonitor" / "缓存反馈 · 新鲜度". Connect both to Service, feedback to upward result return path. Small note under core "符号效果 ≠ 硬件观测".

Footer slim strip exact: "已实现：3 类原生设备 / 23 个登记动作    ｜    配置就绪 ≠ 实机验收    ｜    接受回执 ≠ 物理完成"
Tiny legend "实线：已有调用/数据路径    虚线：待接入". No claims of full FSP certification or automatic document understanding. Draw all arrows deliberately; avoid intersections and do not make shared core a transport hop. Keep all text spelled accurately. Prioritize logical accuracy and large readable labels.

## Correction pass

Remove layout percentages; mark mapped_protocol as implemented with solid border; separate onboarding ownership from scientific-instruments Skill export; add direct single-action CommandDispatcher-to-Service route; label Registry exact binding and conflict rejection; originate static-description arrow at Function Skills. Only MCP gateway is pending.
