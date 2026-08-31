---
title: "研究对象"
description: "ALL 研究对象的类型、状态、证据与来源接口"
---

对象模块定义**研究对象（Research Object）**：实验室中被设备读取、处理、检查、测量或测试，并随操作演化的可追溯实体。研究对象不是泛化属性袋；其规范结构固定为 `identity`、`sample`、`container`、`evidence`、`provenance` 与可扩展字段。

对象接口只登记已经确认的事实。移动、装载、取放、加注、排出、处理或测量必须通过操作模块完成，并由操作结果提交新的研究对象状态。

## 方法列表

| 方法 | 必须实现 | 需要权限 | 是否改变物理状态 |
| --- | --- | --- | --- |
| `objects/list` | 支持研究对象时 | `all:objects:read` | 否 |
| `objects/get` | 支持研究对象时 | `all:objects:read` | 否 |
| `objects/register` | 允许登记时 | `all:objects:write` | 否；只登记已确认事实 |
| `objects/update` | 允许修正元数据时 | `all:objects:write` | 否；不得代替物理操作 |

## 研究对象类型

每种研究对象类型必须在 `system/get_manifest` 的 `objects.object_types` 中声明。类型规定五个固定分区的 JSON Schema、允许的位置和嵌套关系；客户端不得从自然语言说明推测未声明字段。

```json
{
  "object_type": "research_object.generic",
  "title": "通用研究对象",
  "description": "具有样品、容器、证据和来源记录的研究对象。",
  "identity_schema": {"type": "object", "required": ["identifier"]},
  "sample_schema": {"type": ["object", "null"]},
  "container_schema": {"type": ["object", "null"]},
  "evidence_schema": {"type": "array"},
  "provenance_schema": {"type": "array"},
  "extension_schema": {"type": "object", "additionalProperties": true},
  "allowed_parent_types": [],
  "allowed_child_types": [],
  "allowed_locations": ["workspace.input", "workspace.output"],
  "required_scopes": ["all:objects:read"]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `object_type` | `string` | 是 | 能力清单内唯一、稳定的机器标识 |
| `title`、`description` | `string` | 是 | 面向人的类型名称和固定语义 |
| `identity_schema` | `JsonSchema` | 是 | 身份分区定义；至少要求稳定标识 |
| `sample_schema` | `JsonSchema` | 是 | 样品分区定义；不含样品时允许 `null` |
| `container_schema` | `JsonSchema` | 是 | 容器与位置分区定义；无容器时允许 `null` |
| `evidence_schema`、`provenance_schema` | `JsonSchema` | 是 | 证据和来源条目数组定义 |
| `extension_schema` | `JsonSchema` | 是 | 扩展字段定义；不得改写五个固定分区的语义 |
| `allowed_parent_types`、`allowed_child_types` | `string[]` | 是 | 可直接包含的研究对象类型；无关系时为空数组 |
| `allowed_locations` | `string[]` | 是 | 允许出现的设备内位置路径 |
| `required_scopes` | `string[]` | 是 | 读取本类型需要的最低权限范围 |

类型定义或其中任一 Schema 变化时，服务端必须递增能力清单修订号。

## 研究对象实例

```json
{
  "object_id": "research-object-001",
  "object_type": "research_object.generic",
  "identity": {"identifier": "research-object-001", "display_name": "研究对象 001"},
  "sample": {
    "identity": {"name": "unknown"},
    "composition": [],
    "phase": "unknown",
    "amount": {"value": 100, "unit": "uL"}
  },
  "container": {
    "type": "generic_container",
    "identifier": "container-001",
    "capacity": {"value": 1, "unit": "mL"},
    "closure_state": "closed",
    "location": "workspace.input",
    "contained_in": null,
    "position": null
  },
  "evidence": [],
  "provenance": [{
    "event_id": "origin-001", "kind": "registered",
    "recorded_at": "2026-08-31T09:00:00+08:00", "actor": "operator", "source_refs": []
  }],
  "extensions": {},
  "lifecycle_state": "available",
  "revision": 4,
  "created_at": "2026-08-31T09:00:00+08:00",
  "updated_at": "2026-08-31T10:00:00+08:00"
}
```

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `object_id`、`object_type` | `string` | 是 | 服务端范围内稳定且唯一；类型必须能在能力清单中解析 |
| `identity` | `object` | 是 | 持久身份；不得在物理操作后被替换 |
| `sample` | `object \| null` | 是 | 样品身份、组成、相态和量；未知事实必须明确表示 `unknown` 或 `null` |
| `container` | `object \| null` | 是 | 容器类型、标识、几何/容量、封闭状态、位置及包含关系 |
| `evidence` | `Evidence[]` | 是 | 观测值、数据产物或结果引用；按 `recorded_at` 升序 |
| `provenance` | `ProvenanceEntry[]` | 是 | 来源与状态演化的追加记录；不得用更新覆盖既有条目 |
| `extensions` | `object` | 是 | 类型 Schema 明确许可的非核心扩展；不得参与未声明的安全判断 |
| `lifecycle_state` | `ResearchObjectLifecycleState` | 是 | `registered`、`available`、`reserved`、`in_use`、`completed`、`removed` 或 `unknown` |
| `revision` | `integer` | 是 | 实例修订号，大于或等于 `0` |
| `created_at`、`updated_at` | `string` | 是 | 带时区 RFC 3339 时间 |

### 固定分区

`identity` 必须包含稳定标识；可包含显示名称、外部标识或分类，但不能删除原标识。

`sample` 用于表达样品身份、组成、相态、质量、体积或其他量。`amount` 必须使用 `{ "value": number, "unit": string }`；未知、估计和确认状态必须在相应子 Schema 中显式区分。

`container` 用于表达容器类型、标识、几何、容量、封闭/持有状态、设备位置、`contained_in` 与 `position`。容器仅是研究对象的一部分，而不是独立的协议模块；设备直接处理容器时，它可以由自己的研究对象实例表达。

`evidence` 记录观测与数据产物，不得将大文件内容内联到响应中：

```json
{
  "evidence_id": "evidence-001",
  "kind": "observation",
  "name": "temperature",
  "value": {"value": 24.6, "unit": "Cel"},
  "quality": "confirmed",
  "recorded_at": "2026-08-31T10:20:31+08:00",
  "source_operation": {"name": "read_environment_temperature", "task_id": null},
  "data_refs": []
}
```

`provenance` 记录登记、观测、操作提交、导入或人工更正的来源。每一个会改变研究对象状态的成功操作必须追加 `operation_committed` 条目，其中至少记录操作名、任务标识（如有）、前一修订号、新修订号、时间和相关证据引用。

### 包含与位置

- 一个研究对象最多有一个直接父对象，`contained_in` 不得形成循环。
- 父子类型必须同时满足双方类型定义；同一父对象中的 `position` 不得冲突，除非类型明确允许共享。
- 服务端更新父对象位置时必须一致地更新或推导其全部后代的位置。
- 无法确认的位置必须显式为 `null` 或 `unknown`，不得把过期位置作为已确认事实。

## `objects/list`

```json
{
  "jsonrpc": "2.0", "id": "objects-list-1", "method": "objects/list",
  "params": {
    "device_id": "device-001", "object_type": null,
    "lifecycle_states": ["available", "reserved"], "location_prefix": "workspace.",
    "contained_in": null, "cursor": null, "limit": 100, "if_revision": null
  }
}
```

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `device_id` | `string` | 是 | 当前身份可见的设备 |
| `object_type`、`location_prefix`、`contained_in` | `string \| null` | 否 | 精确类型、位置前缀或直接父对象过滤 |
| `lifecycle_states` | `string[]` | 否 | 空数组表示不过滤 |
| `cursor` | `string \| null` | 否 | 服务端返回的不透明分页游标 |
| `limit` | `integer` | 否 | `1..500`，默认 `100` |
| `if_revision` | `integer \| null` | 否 | 对象目录缓存复验 |

响应必须包含 `resultType`、`ttlMs`、`cacheScope`、`revision`、`not_modified`、`items` 与 `next_cursor`。`items` 按 `object_id` 升序排列；缓存复验命中时可以省略 `items`。

## `objects/get`

请求参数为 `device_id`、`object_id` 与可选 `if_revision`。完整响应必须返回一个符合其类型 Schema 的研究对象实例；修订号相等时可以返回 `not_modified=true` 并省略 `object`。

## `objects/register`

`objects/register` 仅登记新研究对象或已确认的起始事实。请求必须包含 `device_id`、完整的 `object` 和可选 `idempotency_key`。服务端必须校验类型 Schema、身份唯一性、包含关系、位置占用和权限；成功后返回登记后的对象。它不得声称已经完成任何物理动作。

## `objects/update`

`objects/update` 用于有限的事实修正。请求必须包含 `device_id`、`object_id`、`expected_revision`、`patch`、`reason` 与可选 `idempotency_key`。`patch` 只允许修改类型定义允许的登记字段、人工确认字段或扩展字段；它不得直接变更由操作管理的样品量、容器位置、封闭状态、证据或来源。违反此规则必须返回 `PhysicalChangeRequired`。

服务端必须把成功修正追加为 `provenance.kind=corrected`，保留前值与修正依据的引用，并递增对象修订号。

## 状态与修订规则

客户端在会影响研究对象的 `operations/write`、`operations/invoke` 或 `workflows/run` 请求中必须携带涉及对象的 `expected_revision`。服务端必须在持有执行锁后复验修订号和强制前置条件；不匹配时返回 `RevisionConflict` 或 `StaleState`，不得开始物理执行。

任何强制约束失败均不得提交受影响研究对象的新状态；建议性约束失败可以返回警告，但必须保留在诊断中。

## 正式类型定义

```typescript
interface ResearchObject {
  object_id: string;
  object_type: string;
  identity: { identifier: string; display_name?: string; external_ids?: Record<string, string> };
  sample: SampleRecord | null;
  container: ContainerRecord | null;
  evidence: Evidence[];
  provenance: ProvenanceEntry[];
  extensions: Record<string, unknown>;
  lifecycle_state: "registered" | "available" | "reserved" | "in_use" | "completed" | "removed" | "unknown";
  revision: number;
  created_at: string;
  updated_at: string;
}

interface SampleRecord {
  identity: Record<string, unknown>;
  composition: Array<Record<string, unknown>>;
  phase: string;
  amount?: { value: number; unit: string };
}

interface ContainerRecord {
  type: string;
  identifier: string;
  geometry?: Record<string, unknown>;
  capacity?: { value: number; unit: string };
  closure_state?: string;
  location: string | null;
  contained_in: string | null;
  position: string | null;
}

interface Evidence {
  evidence_id: string;
  kind: "observation" | "measurement" | "data_product" | "result";
  name: string;
  value: unknown;
  quality: "confirmed" | "estimated" | "stale" | "unknown" | "invalid";
  recorded_at: string;
  source_operation: { name: string; task_id: string | null } | null;
  data_refs: Array<{ uri: string; media_type: string; digest?: string }>;
}

interface ProvenanceEntry {
  event_id: string;
  kind: "registered" | "observed" | "operation_committed" | "imported" | "corrected";
  recorded_at: string;
  actor: string;
  source_refs: string[];
  operation?: { name: string; task_id: string | null; previous_revision: number; new_revision: number };
}
```
