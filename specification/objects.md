---
title: "对象"
description: "ALL 作业对象类型、实例、关系和接口"
---

对象模块只描述作业对象。作业对象是设备读取、写入、操作、处理、检查、测量或测试的实体。

对象由“类型定义”和“运行实例”组成。类型定义说明对象有哪些属性、属性的含义与约束；运行实例记录属性当前值、空间关系、生命周期和来源。属性可以表达身份、物理特征、空间位置、当前状态、测量值、作业结果或补充说明。

## 方法列表

| 方法 | 必须实现 | 需要权限 | 是否改变物理状态 |
| --- | --- | --- | --- |
| `objects/list` | 支持对象时 | `all:objects:read` | 否 |
| `objects/get` | 支持对象时 | `all:objects:read` | 否 |
| `objects/register` | 允许登记时 | `all:objects:write` | 否；只登记协议事实 |
| `objects/update` | 允许修改时 | `all:objects:write` | 否；不得代替物理操作 |

对象接口只能记录已经确认的事实。需要移动、装载、取放、加注、排出或处理对象时，必须调用 `operations/invoke`，并由操作结果更新对象状态。

## 对象类型定义

每种对象类型必须在 `system/get_manifest` 的 `objects.object_types` 中完整声明：

```json
{
  "object_type": "generic_container",
  "title": "通用容器",
  "description": "可以容纳其他作业对象的容器型对象。",
  "property_definitions": [
    {
      "name": "capacity",
      "title": "容量",
      "description": "对象能够容纳的最大体积。",
      "semantic_type": "physical",
      "value_schema": {"type": "number", "minimum": 0},
      "unit": "mL",
      "required": true,
      "update_policy": "registered",
      "allowed_sources": ["manufacturer_data", "operator_confirmed"],
      "freshness_ms": null,
      "safety_relevant": true
    }
  ],
  "allowed_parent_types": [],
  "allowed_child_types": ["generic_sample"],
  "allowed_locations": ["workspace.input", "workspace.output"],
  "required_scopes": ["all:objects:read"]
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `object_type` | `string` | 是 | 设备能力清单内唯一、稳定的机器标识 |
| `title` | `string` | 是 | 面向人的名称 |
| `description` | `string` | 是 | 类型语义，不包含具体实例状态 |
| `property_definitions` | `ObjectPropertyDefinition[]` | 是 | 属性定义；无属性时为空数组 |
| `allowed_parent_types` | `string[]` | 是 | 可以直接容纳该对象的类型；无父对象时为空 |
| `allowed_child_types` | `string[]` | 是 | 可以直接容纳的对象类型；不容纳对象时为空 |
| `allowed_locations` | `string[]` | 是 | 允许出现的设备内位置路径 |
| `required_scopes` | `string[]` | 是 | 读取该类型至少需要的权限范围 |

对象类型数组按 `object_type` 升序排列。类型定义、关系限制或属性数据结构变化时必须递增能力清单修订号。

## 对象属性定义

`property_definitions` 中每一项定义一个可被客户端理解和校验的对象属性。`read`、`write`、`invoke` 不在这里充当属性名或固定指令；对象属性只描述对象事实，能够执行的具体指令由操作模块按独立名称声明。

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | `string` | 是 | 对象类型内唯一、稳定的属性标识 |
| `title` | `string` | 是 | 面向人的属性名称 |
| `description` | `string` | 是 | 属性语义、测量口径或状态含义 |
| `semantic_type` | `ObjectPropertySemanticType` | 是 | 身份、物理、空间、状态、测量、结果或说明 |
| `value_schema` | `JsonSchema` | 是 | 属性 `value` 的 JSON Schema 2020-12 |
| `unit` | `string \| null` | 是 | 统一单位标识；无量纲或枚举值为 `null` |
| `required` | `boolean` | 是 | 每个实例是否必须包含该属性 |
| `update_policy` | `ObjectPropertyUpdatePolicy` | 是 | 哪类已确认事实可以更新该属性 |
| `allowed_sources` | `ObjectPropertySource[]` | 是 | 允许的值来源 |
| `freshness_ms` | `integer \| null` | 是 | 动态值最大有效期；静态值为 `null` |
| `safety_relevant` | `boolean` | 是 | 是否参与约束或安全判断 |

语义类型：

```text
identity physical spatial state measurement result annotation
```

更新策略：

| 值 | 含义 |
| --- | --- |
| `immutable` | 实例创建后不得修改 |
| `registered` | 仅允许可信登记或人工确认更新 |
| `observed` | 由设备回读、传感器或视觉观测更新 |
| `operation_managed` | 只能由已完成操作的确认结果更新 |

属性定义必须明确值的含义、单位、合法范围和来源。质量、位置、压力、温度、容量、运动范围、测量结果或危险条件等信息不得仅写在自然语言描述中；凡是需要机器校验、比较或参与安全判断的内容，都必须使用结构化属性及 `value_schema` 表达。自然语言只用于补充解释。

## 对象实例

```json
{
  "object_id": "object-001",
  "object_type": "generic_container",
  "name": "作业对象 001",
  "lifecycle_state": "available",
  "location": "workspace.input",
  "contained_in": null,
  "position": null,
  "properties": {
    "capacity": {
      "value": 100,
      "unit": "mL",
      "quality": "confirmed",
      "source": "manufacturer_data",
      "recorded_at": "2026-08-31T09:00:00+08:00",
      "expires_at": null,
      "evidence_ids": []
    }
  },
  "labels": {},
  "revision": 4,
  "created_at": "2026-08-31T09:00:00+08:00",
  "updated_at": "2026-08-31T10:00:00+08:00"
}
```

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `object_id` | `string` | 是 | 服务端范围内稳定且唯一；不得重用已归档标识 |
| `object_type` | `string` | 是 | 必须能在能力清单中解析 |
| `name` | `string` | 是 | 非空；只用于显示 |
| `lifecycle_state` | `ObjectLifecycleState` | 是 | 固定枚举 |
| `location` | `string \| null` | 是 | 设备内位置；未知时为 `null` |
| `contained_in` | `string \| null` | 是 | 直接父对象标识；顶层对象为 `null` |
| `position` | `string \| null` | 是 | 父对象内部位置；没有父对象时为 `null` |
| `properties` | `Record<string, ObjectPropertyValue>` | 是 | 属性当前值；键必须存在于类型定义中 |
| `labels` | `object` | 是 | 非安全关键字符串标签；不得用于授权或设备约束 |
| `revision` | `integer` | 是 | 当前对象实例修订号，大于或等于 `0` |
| `created_at` | `string` | 是 | 带时区 RFC 3339 时间 |
| `updated_at` | `string` | 是 | 最近一次确认更新的时间 |

### 属性值

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `value` | `unknown` | 是 | 必须通过对应 `value_schema` 校验 |
| `unit` | `string \| null` | 是 | 必须与属性定义一致 |
| `quality` | `ObjectPropertyQuality` | 是 | `confirmed`、`estimated`、`stale`、`unknown` 或 `invalid` |
| `source` | `ObjectPropertySource` | 是 | 必须属于属性定义允许的来源 |
| `recorded_at` | `string` | 是 | 值被确认或观测的带时区 RFC 3339 时间 |
| `expires_at` | `string \| null` | 是 | 到期时间；静态值为 `null` |
| `evidence_ids` | `string[]` | 是 | 支撑该值的证据引用 |

动态属性到期后，服务端必须把 `quality` 视为 `stale`，不得继续把旧值用于安全关键前置条件。未知值必须显式使用 `quality=unknown`；不得用零、空字符串或上一次值代替未知事实。

生命周期状态：

```text
registered
available
reserved
in_use
completed
removed
unknown
```

`removed` 表示对象已经离开当前设备管理边界或不再可用，但服务端仍保留审计记录。协议不提供物理对象的硬删除接口。

## 包含与位置关系

- 一个对象最多有一个直接父对象。
- `contained_in` 不得形成循环。
- `contained_in` 非空时，`position` 必须符合父对象类型的位置规则。
- 父子类型必须同时满足 `allowed_parent_types` 和 `allowed_child_types`。
- 同一父对象中的位置占用必须唯一，除非父对象类型明确允许共享。
- 更新父对象位置时，服务端必须以一致方式更新或推导其全部后代位置。
- 无法确认位置时必须使用 `null` 或 `unknown`，不得保留已知过期位置并标记为已确认。

## `objects/list`

### 请求

```json
{
  "jsonrpc": "2.0",
  "id": "objects-list-1",
  "method": "objects/list",
  "params": {
    "device_id": "device-001",
    "object_type": null,
    "lifecycle_states": ["available", "reserved", "in_use"],
    "location_prefix": "workspace.",
    "contained_in": null,
    "cursor": null,
    "limit": 100,
    "if_revision": null
  }
}
```

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `device_id` | `string` | 是 | 当前身份可见设备 |
| `object_type` | `string \| null` | 否 | 精确类型过滤 |
| `lifecycle_states` | `ObjectLifecycleState[]` | 否 | 状态过滤；空数组等价于不过滤 |
| `location_prefix` | `string \| null` | 否 | 设备内位置前缀过滤 |
| `contained_in` | `string \| null` | 否 | 直接父对象过滤 |
| `cursor` | `string \| null` | 否 | 服务端返回的不透明分页游标 |
| `limit` | `integer` | 否 | `1..500`，默认 `100` |
| `if_revision` | `integer \| null` | 否 | 对象目录修订号缓存复验 |

### 响应

```json
{
  "resultType": "complete",
  "ttlMs": 0,
  "cacheScope": "private",
  "revision": 91,
  "not_modified": false,
  "items": [],
  "next_cursor": null
}
```

对象实例是动态状态，默认 `ttlMs=0`。`items` 按 `object_id` 升序排列。分页期间目录修订号变化时，服务端必须返回 `RevisionConflict`，客户端必须从第一页重新读取。

## `objects/get`

```json
{
  "jsonrpc": "2.0",
  "id": "object-get-1",
  "method": "objects/get",
  "params": {
    "device_id": "device-001",
    "object_id": "object-001",
    "if_revision": null
  }
}
```

成功响应：

```json
{
  "resultType": "complete",
  "not_modified": false,
  "object": {
    "object_id": "object-001",
    "object_type": "generic_container",
    "name": "作业对象 001",
    "lifecycle_state": "available",
    "location": "workspace.input",
    "contained_in": null,
    "position": null,
    "properties": {
      "capacity": {
        "value": 100,
        "unit": "mL",
        "quality": "confirmed",
        "source": "manufacturer_data",
        "recorded_at": "2026-08-31T09:00:00+08:00",
        "expires_at": null,
        "evidence_ids": []
      }
    },
    "labels": {},
    "revision": 4,
    "created_at": "2026-08-31T09:00:00+08:00",
    "updated_at": "2026-08-31T10:00:00+08:00"
  }
}
```

当 `if_revision` 与对象修订号相等时，可以返回 `not_modified=true` 并省略 `object`。

## `objects/register`

该方法只登记已经存在并已由可信来源确认的对象，不执行装载或移动。

```json
{
  "jsonrpc": "2.0",
  "id": "object-register-1",
  "method": "objects/register",
  "params": {
    "device_id": "device-001",
    "object": {
      "object_id": "object-001",
      "object_type": "generic_container",
      "name": "作业对象 001",
      "lifecycle_state": "registered",
      "location": "workspace.input",
      "contained_in": null,
      "position": null,
      "properties": {
        "capacity": {
          "value": 100,
          "unit": "mL",
          "quality": "confirmed",
          "source": "manufacturer_data",
          "recorded_at": "2026-08-31T10:00:00+08:00",
          "expires_at": null,
          "evidence_ids": []
        }
      },
      "labels": {}
    },
    "confirmation": {
      "source": "operator_confirmed",
      "confirmed_at": "2026-08-31T10:00:00+08:00",
      "evidence_ids": []
    }
  }
}
```

服务端必须校验标识唯一性、对象类型、必需属性、属性值、单位、来源、位置、关系、权限和确认来源。成功返回新对象及目录修订号。

## `objects/update`

使用字段掩码和期望修订号修改协议事实：

```json
{
  "jsonrpc": "2.0",
  "id": "object-update-1",
  "method": "objects/update",
  "params": {
    "device_id": "device-001",
    "object_id": "object-001",
    "expected_revision": 4,
    "field_mask": ["name", "labels.batch"],
    "changes": {
      "name": "作业对象 001-A",
      "labels": {"batch": "batch-001"}
    },
    "confirmation": {
      "source": "operator_confirmed",
      "confirmed_at": "2026-08-31T10:05:00+08:00",
      "evidence_ids": []
    }
  }
}
```

`field_mask` 中的路径必须唯一，并与 `changes` 对应。服务端必须在同一事务中比较 `expected_revision`、校验全部变更并递增对象修订号。

修改 `properties.<name>` 时，服务端还必须校验属性的 `update_policy`、`allowed_sources`、单位、值数据结构和确认时间：

- `immutable` 属性不得修改；
- `registered` 属性只接受可信登记或人工确认；
- `observed` 属性只接受声明允许的观测来源；
- `operation_managed` 属性不得通过 `objects/update` 修改，必须由已完成操作写回。

以下字段不得由普通 `objects/update` 直接修改：

- `object_id`；
- `object_type`；
- 由正在执行的操作拥有的状态；
- 需要物理动作才能改变的位置、包含关系或作业结果。

这些变化必须由 `operations/invoke` 完成并由服务端根据已确认结果更新。

## 错误

| 情况 | 错误名 |
| --- | --- |
| 对象不存在或对当前身份不可见 | `ObjectNotFound` |
| 对象标识已经存在 | `AlreadyExists` |
| 对象类型、属性值、单位或来源无效 | `SchemaValidationFailed` |
| 父子类型、位置或容量不兼容 | `ConstraintViolation` |
| 对象修订号已经变化 | `RevisionConflict` |
| 对象被操作或 Workflow 占用 | `ObjectBusy` |
| 试图用对象更新伪造物理变化 | `PhysicalChangeRequired` |

## 正式类型定义

```typescript
type JsonSchema = Record<string, unknown>;

type ObjectLifecycleState =
  | "registered"
  | "available"
  | "reserved"
  | "in_use"
  | "completed"
  | "removed"
  | "unknown";

interface ObjectTypeDefinition {
  object_type: string;
  title: string;
  description: string;
  property_definitions: ObjectPropertyDefinition[];
  allowed_parent_types: string[];
  allowed_child_types: string[];
  allowed_locations: string[];
  required_scopes: string[];
}

type ObjectPropertySemanticType =
  | "identity"
  | "physical"
  | "spatial"
  | "state"
  | "measurement"
  | "result"
  | "annotation";

type ObjectPropertyUpdatePolicy =
  | "immutable"
  | "registered"
  | "observed"
  | "operation_managed";

type ObjectPropertySource =
  | "manufacturer_data"
  | "operator_confirmed"
  | "device_readback"
  | "sensor"
  | "vision"
  | "system_import"
  | "operation_result";

type ObjectPropertyQuality =
  | "confirmed"
  | "estimated"
  | "stale"
  | "unknown"
  | "invalid";

interface ObjectPropertyDefinition {
  name: string;
  title: string;
  description: string;
  semantic_type: ObjectPropertySemanticType;
  value_schema: JsonSchema;
  unit: string | null;
  required: boolean;
  update_policy: ObjectPropertyUpdatePolicy;
  allowed_sources: ObjectPropertySource[];
  freshness_ms: number | null;
  safety_relevant: boolean;
}

interface ObjectPropertyValue {
  value: unknown;
  unit: string | null;
  quality: ObjectPropertyQuality;
  source: ObjectPropertySource;
  recorded_at: string;
  expires_at: string | null;
  evidence_ids: string[];
}

interface WorkObject {
  object_id: string;
  object_type: string;
  name: string;
  lifecycle_state: ObjectLifecycleState;
  location: string | null;
  contained_in: string | null;
  position: string | null;
  properties: Record<string, ObjectPropertyValue>;
  labels: Record<string, string>;
  revision: number;
  created_at: string;
  updated_at: string;
}

interface ObjectConfirmation {
  source: "operator_confirmed" | "device_readback" | "vision" | "system_import";
  confirmed_at: string;
  evidence_ids: string[];
}
```
