# 物理资源

Physical Resource（物理资源）统一表示与设备实际运行有关的物理实体。协议只定义两个互斥的顶层类别：

```text
Physical Resource
├─ Work Object      作业对象
└─ Device Supply    设备供给物料
```

| 类别 | `kind` | 定义 |
| --- | --- | --- |
| Work Object | `work_object` | 设备直接操作、处理、检查、测量、表征或测试的物理实体 |
| Device Supply | `device_supply` | 设备运行中会被消耗、损耗、排出、替换或需要补充的物料和物品 |

Container 不构成第三个顶层类别。设备直接操作容器时，该容器是 `WorkObject`；容器只承担容纳作用时，通过子对象的 `contained_in` 和 `position` 表达包含关系及内部位置。

## 通用 Schema

所有物理资源 MUST 使用统一身份、状态、位置、修订号和时间字段，并根据 `kind` 选择专用 Schema：

```typescript
type PhysicalResourceKind = "work_object" | "device_supply";

interface ResourceLocation {
  device_id: string | null;
  workspace_path: string | null;
  quality: "confirmed" | "estimated" | "unknown";
}

interface PhysicalResource {
  id: string;
  kind: PhysicalResourceKind;
  type: string;
  name: string;
  state: Record<string, unknown>;
  location: ResourceLocation;
  metadata: Record<string, unknown>;
  revision: number;
  created_at: string;
  updated_at: string;
}

interface WorkObject extends PhysicalResource {
  kind: "work_object";
  contained_in?: string | null;
  position?: string | null;
  work_status:
    | "available"
    | "reserved"
    | "in_use"
    | "completed"
    | "rejected"
    | "unknown";
  result_refs: string[];
}

interface Quantity {
  value: number | null;
  unit: string;
  quality: "measured" | "estimated" | "unknown";
}

interface DeviceSupply extends PhysicalResource {
  kind: "device_supply";
  quantity: Quantity;
  lot_id?: string | null;
  expires_at?: string | null;
  replenish_threshold?: number | null;
  supply_status:
    | "available"
    | "installed"
    | "in_use"
    | "low"
    | "depleted"
    | "expired"
    | "contaminated"
    | "removed"
    | "unknown";
}

type NewPhysicalResource =
  | Omit<WorkObject, "revision" | "created_at" | "updated_at">
  | Omit<DeviceSupply, "revision" | "created_at" | "updated_at">;
```

规范实现 MUST 使用以下 JSON Schema 判别联合或与其等价的约束；`kind` 是判别字段，且不得出现第三种值：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://alp.example/schema/physical-resource.json",
  "title": "PhysicalResource",
  "oneOf": [
    {"$ref": "#/$defs/WorkObject"},
    {"$ref": "#/$defs/DeviceSupply"}
  ],
  "$defs": {
    "ResourceLocation": {
      "type": "object",
      "properties": {
        "device_id": {"type": ["string", "null"]},
        "workspace_path": {"type": ["string", "null"]},
        "quality": {
          "enum": ["confirmed", "estimated", "unknown"]
        }
      },
      "required": ["device_id", "workspace_path", "quality"],
      "additionalProperties": false
    },
    "Quantity": {
      "type": "object",
      "properties": {
        "value": {"type": ["number", "null"], "minimum": 0},
        "unit": {"type": "string", "minLength": 1},
        "quality": {
          "enum": ["measured", "estimated", "unknown"]
        }
      },
      "required": ["value", "unit", "quality"],
      "additionalProperties": false
    },
    "PhysicalResourceBase": {
      "type": "object",
      "properties": {
        "id": {"type": "string", "minLength": 1},
        "kind": {"enum": ["work_object", "device_supply"]},
        "type": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "state": {"type": "object"},
        "location": {"$ref": "#/$defs/ResourceLocation"},
        "metadata": {"type": "object"},
        "revision": {"type": "integer", "minimum": 0},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
      },
      "required": [
        "id", "kind", "type", "name", "state", "location",
        "metadata", "revision", "created_at", "updated_at"
      ]
    },
    "WorkObject": {
      "allOf": [
        {"$ref": "#/$defs/PhysicalResourceBase"},
        {
          "type": "object",
          "properties": {
            "kind": {"const": "work_object"},
            "contained_in": {"type": ["string", "null"]},
            "position": {"type": ["string", "null"]},
            "work_status": {
              "enum": [
                "available", "reserved", "in_use", "completed",
                "rejected", "unknown"
              ]
            },
            "result_refs": {
              "type": "array",
              "items": {"type": "string"},
              "uniqueItems": true
            }
          },
          "required": [
            "kind", "contained_in", "position", "work_status", "result_refs"
          ]
        }
      ],
      "unevaluatedProperties": false
    },
    "DeviceSupply": {
      "allOf": [
        {"$ref": "#/$defs/PhysicalResourceBase"},
        {
          "type": "object",
          "properties": {
            "kind": {"const": "device_supply"},
            "quantity": {"$ref": "#/$defs/Quantity"},
            "lot_id": {"type": ["string", "null"]},
            "expires_at": {
              "type": ["string", "null"],
              "format": "date-time"
            },
            "replenish_threshold": {
              "type": ["number", "null"],
              "minimum": 0
            },
            "supply_status": {
              "enum": [
                "available", "installed", "in_use", "low", "depleted",
                "expired", "contaminated", "removed", "unknown"
              ]
            }
          },
          "required": [
            "kind", "quantity", "lot_id", "expires_at",
            "replenish_threshold", "supply_status"
          ]
        }
      ],
      "unevaluatedProperties": false
    }
  }
}
```

公共字段规则：

- `id` MUST 在当前 Device Node 内稳定且唯一，不能仅使用数组位置表示身份；
- `kind` MUST 只能是 `work_object` 或 `device_supply`；
- `type` MUST 引用 Manifest 中的 `physical_resource_types` 定义；
- `state` MUST 符合对应资源类型声明的 `state_schema`；
- `location` MUST 表示设备边界、工作区、包含关系和位置质量；
- `metadata` MAY 保存非控制性扩展信息，不得覆盖规范字段语义；
- `revision` MUST 在资源事实变化时单调递增；
- `created_at` 和 `updated_at` MUST 使用 RFC 3339 时间。

## 资源类型定义

Manifest 中的每个资源类型 MUST 至少声明：

```typescript
interface PhysicalResourceTypeDefinition {
  type: string;
  kind: PhysicalResourceKind;
  name: string;
  description?: string;
  state_schema: Record<string, unknown>;
  metadata_schema?: Record<string, unknown>;
  allowed_locations?: string[];
  transferable: boolean;
}
```

Work Object 类型 MAY 额外声明容纳能力、允许的子对象类型和位置地址规则。Device Supply 类型 SHOULD 声明计量单位、兼容位置、补充方式、批次要求和消耗影响。

## 物理资源操作

声明 `physicalResources=true` 的 Server MUST 实现以下统一接口：

| 方法 | 作用 | 修改事实 |
| --- | --- | --- |
| `physical_resources/list` | 按 `kind`、`type`、位置或状态列出资源 | 否 |
| `physical_resources/get` | 按稳定 `id` 读取单个资源 | 否 |
| `physical_resources/register` | 登记一个新资源事实 | 是 |
| `physical_resources/update` | 使用字段掩码和 revision 修改允许字段 | 是 |
| `events/subscribe` | 以 `physical_resource.changed` 主题订阅资源创建、变化、移动和移除事件 | 否 |

统一操作参数和结果 Schema：

```typescript
interface ListPhysicalResourcesParams {
  device_id: string;
  kind?: PhysicalResourceKind;
  type?: string;
  workspace_path?: string;
  contained_in?: string;
  state_filter?: Record<string, unknown>;
  cursor?: string;
  limit?: number;
}

interface ListPhysicalResourcesResult {
  items: Array<WorkObject | DeviceSupply>;
  next_cursor: string | null;
  snapshot_revision: number;
}

interface GetPhysicalResourceParams {
  device_id: string;
  resource_id: string;
}

interface RegisterPhysicalResourceParams {
  device_id: string;
  resource: NewPhysicalResource;
  options: {
    idempotency_key: string;
  };
}

interface UpdatePhysicalResourceParams {
  device_id: string;
  resource_id: string;
  field_mask: string[];
  values: Record<string, unknown>;
  options: {
    expected_revision: number;
    reason: string;
  };
}

interface PhysicalResourceMutationResult {
  resource: WorkObject | DeviceSupply;
  previous_revision: number | null;
  new_revision: number;
  evidence: string[];
}

interface SubscribePhysicalResourceEventsParams {
  device_id: string;
  topics: ["physical_resource.changed"];
  filters?: {
    resource_kinds?: PhysicalResourceKind[];
    resource_ids?: string[];
    change_types?: Array<
      "registered" | "updated" | "moved" | "consumed" |
      "replenished" | "replaced" | "installed" |
      "uninstalled" | "removed" | "unknown"
    >;
  };
  after_event_id?: string;
}

interface PhysicalResourceChangedEvent {
  event_id: string;
  device_id: string;
  resource_id: string;
  kind: PhysicalResourceKind;
  change_type: string;
  previous_revision: number | null;
  new_revision: number;
  changed_fields: string[];
  occurred_at: string;
  actor: string;
  evidence: string[];
}
```

`limit` MUST 在 `1..500` 范围内；Server MAY 采用更小的最大值。分页结果 MUST 固定在 `snapshot_revision`，避免调用方在翻页期间把不同资源快照拼接为同一状态。`get` 找不到资源时 MUST 返回 `RESOURCE_NOT_FOUND`。

`register` 遇到已存在的 `id` 时，只有相同调用身份、相同 `idempotency_key` 和相同请求摘要才能返回原结果；其他情况 MUST 返回 `RESOURCE_ID_CONFLICT`。Server 负责填写 `revision`、`created_at` 和 `updated_at`。

`events/subscribe` 使用 Base Protocol 定义的统一事件接口，过滤条件放入 `filters`。事件传输断开后，Client SHOULD 使用最后确认的 `event_id` 调用 `events/poll` 续读；若事件已过期，Server MUST 返回 `EventCursorExpired`，调用方随后重新执行 `physical_resources/list` 获取完整快照并建立新订阅。

`physical_resources/list` 和 `physical_resources/get` MUST 返回 `PhysicalResource` 的完整公共字段，并根据 `kind` 返回对应专用字段。调用方不得依赖未在类型 Schema 中声明的字段。

登记请求示例：

```json
{
  "jsonrpc": "2.0",
  "id": "resource-register-1",
  "method": "physical_resources/register",
  "params": {
    "device_id": "device-001",
    "resource": {
      "id": "resource-001",
      "kind": "work_object",
      "type": "work_object.generic",
      "name": "作业对象",
      "state": {},
      "location": {
        "device_id": null,
        "workspace_path": null,
        "quality": "confirmed"
      },
      "metadata": {},
      "work_status": "available",
      "result_refs": []
    },
    "options": {
      "idempotency_key": "register-resource-001"
    }
  }
}
```

修改请求 MUST 使用字段掩码和乐观并发控制：

```json
{
  "jsonrpc": "2.0",
  "id": "resource-update-1",
  "method": "physical_resources/update",
  "params": {
    "device_id": "device-001",
    "resource_id": "resource-001",
    "field_mask": ["metadata.operator_note"],
    "values": {
      "metadata": {
        "operator_note": "已复核"
      }
    },
    "options": {
      "expected_revision": 7,
      "reason": "操作员修正描述信息"
    }
  }
}
```

`physical_resources/update` MUST NOT 直接修改以下事实：

- `id`、`kind`、`type` 和 `created_at`；
- 未经 Transfer confirm 的跨边界位置；
- 未经已完成 Action、Workflow 或可信回读证明的设备内部位置；
- 由设备测量产生但请求方无法验证的状态；
- 审计记录、Evidence 和其他调用方创建的结果。

每次成功登记或修改 MUST 返回旧 revision、新 revision 和变更后的资源。资源变化 MUST 产生事件，事件至少包含 `event_id`、`resource_id`、`kind`、`change_type`、`previous_revision`、`new_revision`、`changed_fields`、`occurred_at` 和可验证的 `actor`。

## 作业对象操作

Work Object 的位置、包含关系和作业状态必须与真实物理事实一致：

- 跨越 Device Node 边界 MUST 使用 Physical Resource Transfer 的 `transfers/prepare` 与 `transfers/confirm`；
- `contained_in` MUST 引用另一个 `WorkObject.id`，不得引用 `DeviceSupply`；
- `position` MUST 符合父 Work Object 类型声明的位置地址规则；
- 父 Work Object 移动时，其子对象 MUST 作为同一聚合关系更新；
- `result_refs` 只能引用已存在的结果或 Evidence；
- Action 或 Workflow 开始、完成或失败时，Server MUST 原子更新相关 `work_status` 和 revision。

## 设备供给物料操作

Device Supply 除统一接口外，还定义以下语义操作：

| 方法 | 作用 |
| --- | --- |
| `device_supplies/replenish` | 在原实例上增加可用数量或容量 |
| `device_supplies/replace` | 原子结束旧实例并登记、安装新实例 |
| `device_supplies/install` | 确认供给物料与设备位置的安装关系 |
| `device_supplies/uninstall` | 解除安装关系并保留审计事实 |

```typescript
interface ReplenishDeviceSupplyParams {
  device_id: string;
  resource_id: string;
  add_quantity: { value: number; unit: string };
  lot_id?: string | null;
  expires_at?: string | null;
  options: {
    expected_revision: number;
    idempotency_key: string;
    reason: string;
    source: string;
  };
}

interface ReplaceDeviceSupplyParams {
  device_id: string;
  old_resource_id: string;
  new_resource: Omit<DeviceSupply,
    "revision" | "created_at" | "updated_at">;
  install_path?: string | null;
  confirmed_transfer_id?: string | null;
  options: {
    expected_revision: number;
    idempotency_key: string;
    reason: string;
  };
}

interface InstallDeviceSupplyParams {
  device_id: string;
  resource_id: string;
  install_path: string;
  confirmed_transfer_id?: string | null;
  options: {
    expected_revision: number;
    idempotency_key: string;
    reason: string;
  };
}

interface UninstallDeviceSupplyParams {
  device_id: string;
  resource_id: string;
  install_path: string;
  confirmed_transfer_id?: string | null;
  options: {
    expected_revision: number;
    idempotency_key: string;
    reason: string;
  };
}
```

补充请求 MUST 声明 `resource_id`、增加量、单位、`expected_revision`、修改原因和来源。Server MUST 校验单位兼容性、容量上限、批次与有效期要求，并在成功后更新 `quantity`、`supply_status` 和 revision。

替换操作 MUST 原子完成以下变化：旧资源进入 `removed` 或适用的终态；新资源以新的稳定 `id` 登记；安装位置只指向新资源；数量、批次、有效期和审计记录同步更新。不得通过覆盖旧资源 `id` 实现替换。

`install` 与 `uninstall` 只确认设备内的安装关系，不替代真实物理交接。Device Supply 从 Device Node 外部进入或离开时，`confirmed_transfer_id` MUST 引用已完成的对应 Transfer；仅在设备内部自动换位且 Server 能提供已完成 Action 或可信回读时 MAY 省略。

四个专用操作都 MUST 返回 `PhysicalResourceMutationResult`，支持幂等键，并在 revision 冲突时返回 `RESOURCE_REVISION_CONFLICT`。数量为负、单位不兼容、超过容量、批次冲突、已过期或位置不兼容时 MUST 拒绝，不得部分更新资源事实。

动作和 Workflow SHOULD 声明 `required_device_supplies` 与 `device_supply_effects`。供给物料只在动作结果明确成功后扣减；结果为 `unknown` 时，相关 `quantity.quality` 和 `supply_status` SHOULD 进入 `unknown`，直到可信回读或人工复核。

## 物理资源安全与错误

权限 SHOULD 至少区分：

| 权限 | 允许操作 |
| --- | --- |
| `physical_resources:read` | `list`、`get` 和事件订阅 |
| `physical_resources:write` | `register` 与允许字段的 `update` |
| `physical_resources:transfer` | Physical Resource Transfer |
| `device_supplies:manage` | `replenish`、`replace`、`install`、`uninstall` |

修改操作 MUST 在同一资源锁或同一设备状态事务中校验权限、Schema、`expected_revision`、位置约束和业务前置条件，并原子提交资源状态、设备状态、事件和审计记录。任何一步失败都不得留下部分更新。

规范错误至少包括：

| 错误码 | 含义 |
| --- | --- |
| `RESOURCE_NOT_FOUND` | 资源不存在或调用方无权查看 |
| `RESOURCE_ID_CONFLICT` | 新资源 `id` 已被其他事实占用 |
| `RESOURCE_KIND_MISMATCH` | `kind` 与类型定义或操作不匹配 |
| `RESOURCE_TYPE_UNSUPPORTED` | Manifest 未声明该资源类型 |
| `RESOURCE_SCHEMA_INVALID` | 资源或修改值不符合 Schema |
| `RESOURCE_REVISION_CONFLICT` | `expected_revision` 已过期 |
| `RESOURCE_FIELD_IMMUTABLE` | 尝试修改不可变或受保护字段 |
| `RESOURCE_LOCATION_UNCONFIRMED` | 位置变化缺少 Transfer、Action 或可信回读 |
| `RESOURCE_RELATION_INVALID` | 包含关系、位置地址或循环关系无效 |
| `SUPPLY_UNIT_INCOMPATIBLE` | Device Supply 单位不可换算或不兼容 |
| `SUPPLY_LIMIT_EXCEEDED` | 补充后超过声明容量或限制 |
| `SUPPLY_NOT_USABLE` | Device Supply 已耗尽、过期、污染或状态未知 |

同一幂等键重试 MUST 返回原结果；同一键绑定不同请求摘要 MUST 返回冲突。超时发生在物理动作可能已执行之后时，Server MUST 返回 `outcome=unknown`，并将受影响资源状态或质量标记为 `unknown`，不得猜测回滚。

## 作业对象类型定义

```json
{
  "object_type": "sample_carrier",
  "display_name": "样品载具",
  "ownership_class": "external_transfer",
  "traits": ["carrier", "container"],
  "description": "由人或外部机器人整体装入或取出的通用载具。",
  "physical_properties": {
    "dimensions_mm": {
      "x": 127.8,
      "y": 85.5,
      "z": 18.0
    },
    "mass_g": null,
    "orientation_policy": "fixed"
  },
  "detectable_by": ["operator_confirmed", "vision"],
  "movable_by": ["external_robot"],
  "state_schema": {
    "type": "object",
    "properties": {
      "present": {"type": "boolean"},
      "pose_confirmed": {"type": "boolean"}
    },
    "required": ["present", "pose_confirmed"],
    "additionalProperties": false
  }
}
```

## 容器型作业对象

容器不定义新的 `kind`。当设备直接操作容器时，其类型定义 MUST 使用 `kind=work_object`，并通过容纳能力扩展 Work Object Schema。

```json
{
  "object_type": "multi_position_container",
  "display_name": "多位置容器",
  "ownership_class": "external_transfer",
  "traits": ["container"],
  "container": {
    "capacity": {
      "kind": "multi_slot",
      "slot_count": 12
    },
    "slot_schema": {
      "address_pattern": "^P(?:0[1-9]|1[0-2])$",
      "coordinate_convention": {
        "origin": "declared_reference",
        "examples": {
          "first": "P01",
          "last": "P12"
        }
      },
      "single_slot_capacity": {
        "value": 10,
        "unit": "mL"
      }
    },
    "allowed_contents": [
      {
        "content_class": "liquid",
        "compatibility": "declared_by_workflow"
      }
    ],
    "closure": {
      "supported": false,
      "states": []
    }
  }
}
```

Container Definition MUST 声明：

- 总容量或槽位容量；
- 槽位地址规则；
- 坐标原点和方向；
- 允许的内容物类型；
- 是否有盖、门、阀或其他封闭结构；
- 温度、压力、材料兼容性和填充限制；
- 约束的单位和执行位置。

## 作业对象实例

```json
{
  "object_id": "carrier-current",
  "object_type": "sample_carrier",
  "ownership_class": "external_transfer",
  "revision": 412,
  "lifecycle_state": "in_use",
  "boundary_state": "present",
  "location": {
    "device_id": "device-001",
    "workspace_path": "workspace.position-01"
  },
  "pose": {
    "frame": "position-01",
    "position": null,
    "orientation": "fixed",
    "quality": "confirmed"
  },
  "relationships": [
    {
      "relation": "contains",
      "object_id": "container-current"
    }
  ],
  "observed_at": "2026-08-31T11:10:00+08:00",
  "source": "operator_confirmed"
}
```

每个运行实例 MUST 具有稳定 `object_id`。对象身份 MUST NOT 仅由数组位置表示。

## 作业对象包含关系

```text
sample_carrier
└─ multi_position_container
   ├─ position P01
   ├─ position P02
   └─ ...
```

父容器从工作区移除时，其子对象 MUST 同步离开该工作区。Server MUST NOT 继续把子对象标记为已装载。

内容物通过状态路径读取：

```text
objects.<object_id>.contents.total_volume_ul
objects.<object_id>.slots.P01.contents.quantity
objects.<object_id>.slots.P01.contents.material_id
objects.<object_id>.closure.state
```

领域别名可以存在，但 MUST 指向同一状态事实和同一 revision。

## 作业对象兼容方法别名

规范接口是 `physical_resources/list` 和 `physical_resources/get`。为兼容早期实现，Server MAY 在协商兼容扩展后提供以下别名：

- `objects/list`
- `objects/get`

```json
{
  "jsonrpc": "2.0",
  "id": "objects-1",
  "method": "objects/list",
  "params": {
    "device_id": "device-001",
    "workspace_path": "workspace.position-01",
    "object_type": null
  }
}
```

这些别名默认只读，并且 MUST 返回相同 `id`、位置和 revision，不得建立第二套资源身份。设备工作区内部的抓取、开合和处理 MUST 通过明确的 `write` 或 `invoke` 完成；Work Object 进入或离开 Device Node 边界 MUST 使用 Physical Resource Transfer 接口。

动作引用对象时 SHOULD 使用结构化引用：

```json
{
  "source": {
    "object_id": "source-container-001",
    "slot": "P01"
  },
  "target": {
    "object_id": "target-container-001",
    "slot": "P02"
  },
  "quantity": {
    "value": 1,
    "unit": "mL"
  }
}
```

Server MUST 在执行锁内再次验证对象位置、类型、状态新鲜度和 revision。

## 设备供给物料兼容方法别名

早期 `Consumable` 概念统一映射为 `DeviceSupply`。`consumable_type` MUST 与对应 `DeviceSupply.type` 使用同一标识，`consumable_id` MUST 与对应 `DeviceSupply.id` 使用同一标识。Server 不得为同一实体建立第二套身份、数量或位置关系。

ALP 只管理设备当前能够使用或已经装入的耗材，不定义采购、供应商订单、仓库库位、补货预测或完整库存系统。

##### Legacy Consumable Type

```json
{
  "consumable_type": "consumable_pack",
  "display_name": "可更换耗材包",
  "ownership_class": "external_transfer",
  "traits": ["consumable", "carrier"],
  "description": "设备操作使用的可更换耗材载具。",
  "quantity_unit": "piece",
  "single_use": false,
  "contained_item_single_use": true,
  "compatible_slots": ["workspace.consumable_mount"],
  "compatible_actions": [
    "prepare_operation",
    "execute_operation",
    "finalize_operation"
  ],
  "tracked_fields": [
    "status",
    "remaining_quantity",
    "lot_id",
    "expires_at"
  ]
}
```

类型定义保持轻量，必填字段只有：

| 字段 | 说明 |
| --- | --- |
| `consumable_type` | 稳定类型标识 |
| `display_name` | 面向人的名称 |
| `quantity_unit` | `piece`、`mL`、`g` 等计量单位 |
| `single_use` | 是否一次性使用 |
| `compatible_slots` | 可以安装或放置的位置 |
| `compatible_actions` | 会使用该耗材的动作 |

批次、有效期和最大使用次数是可选字段；设备不需要为了符合协议实现仓储能力。

##### Legacy Consumable Instance

```json
{
  "consumable_id": "consumable-pack-current",
  "consumable_type": "consumable_pack",
  "ownership_class": "external_transfer",
  "boundary_state": "present",
  "status": "installed",
  "remaining_quantity": 24,
  "quantity_unit": "piece",
  "lot_id": null,
  "expires_at": null,
  "installed_at": "workspace.consumable_mount",
  "revision": 51,
  "quality": "confirmed",
  "source": "operator_confirmed",
  "observed_at": "2026-08-31T09:00:00+08:00"
}
```

状态值：

```text
available | installed | in_use | depleted | expired | contaminated | removed | unknown
```

`remaining_quantity` 可以是准确值、估算值或 `null`。其质量和来源通过普通状态字段或 Evidence 表达。

##### Legacy Consumable Methods

规范接口是 `physical_resources/*` 和 `device_supplies/*`。Server MAY 在协商兼容扩展后提供以下旧方法别名：

- `consumables/list`
- `consumables/get`
- `consumables/register`
- `consumables/update`
- `consumables/install`
- `consumables/uninstall`

`consumables/register` 用于添加设备当前可见的耗材实例；它只登记事实，不代表耗材已经物理安装：

```json
{
  "jsonrpc": "2.0",
  "id": "consumable-register-1",
  "method": "consumables/register",
  "params": {
    "device_id": "device-001",
    "instance": {
      "consumable_id": "consumable-pack-current",
      "consumable_type": "consumable_pack",
      "ownership_class": "external_transfer",
      "boundary_state": "outside",
      "remaining_quantity": 24,
      "quantity_unit": "piece",
      "lot_id": null,
      "expires_at": null
    },
    "options": {
      "expected_revision": 50,
      "source": "operator_confirmed"
    }
  }
}
```

请求中的 `source` 是声明来源，Server 只有在能够绑定已验证操作员、设备或传感器身份时才可按该来源记录；否则必须拒绝或标记为 `unknown`。

`consumables/register` 遇到已存在的 `consumable_id` MUST 返回冲突，不得覆盖原实例；修改现有实例必须使用 `consumables/update` 和 revision。

`consumables/update` 使用字段掩码避免无意覆盖未提交字段：

```json
{
  "jsonrpc": "2.0",
  "id": "consumable-update-1",
  "method": "consumables/update",
  "params": {
    "device_id": "device-001",
    "consumable_id": "consumable-pack-current",
    "field_mask": ["remaining_quantity"],
    "values": {
      "remaining_quantity": 23
    },
    "options": {
      "expected_revision": 51,
      "reason": "操作员在上位机中修正数量"
    }
  }
}
```

`consumables/install` 和 `consumables/uninstall` 只确认设备内的安装关系，不替代物理交接。外部对象进入或离开时，参数 MUST 引用已经完成 confirm 的本地 `transfer_id`：

```json
{
  "jsonrpc": "2.0",
  "id": "consumable-install-1",
  "method": "consumables/install",
  "params": {
    "device_id": "device-001",
    "consumable_id": "consumable-pack-current",
    "install_path": "workspace.consumable_mount",
    "confirmed_transfer_id": "tr-consumable-1001",
    "options": {
      "expected_revision": 52,
      "reason": "机器人已完成耗材进场并通过允许的来源确认"
    }
  }
}
```

`uninstall` 使用相同结构，将 `install_path` 替换为当前安装位置，并引用已确认的 egress `transfer_id`。设备内部自动换位不经过边界时，`confirmed_transfer_id` MAY 省略，但 Server MUST 以设备回读或已完成 Action 证明位置变化。

允许的修改主体：

- 经过身份验证的上位机操作员；
- 设备动作成功后的 Server 状态更新；
- 获得 `consumables:write` 权限的单设备智能体。

设备智能体可以控制机器人完成耗材装入或取出，再调用 `consumables/install` 或 `consumables/uninstall` 更新设备事实。接口 MUST 记录 `verified_actor`、修改原因、旧值、新值和 revision。

以下字段不能通过普通 update 伪造：

- 设备传感器回读；
- 已完成动作的 Evidence；
- 锁定的耗材类型约束；
- 其他调用者创建的审计记录。

`install` 和 `uninstall` 表示设备对安装关系的确认。若物理动作由机器人执行，必须先完成 Physical Resource Transfer 两阶段流程；未完成 confirm 时不得把状态改为 `installed` 或 `removed`。

动作和 Workflow SHOULD 声明 Device Supply 依赖与影响：

```json
{
  "required_device_supplies": [
    {
      "device_supply_type": "supply_pack",
      "minimum_quantity": 1,
      "quantity_unit": "piece"
    }
  ],
  "device_supply_effects": [
    {
      "device_supply_type": "supply_pack",
      "operation": "decrease",
      "quantity": 1,
      "quantity_unit": "piece"
    }
  ]
}
```

供给物数量只在对应动作明确成功后更新；结果为 `unknown` 时，相关 Device Supply 状态 SHOULD 标记为 `unknown` 或等待人工修正。

## 物理资源转移

Physical Resource Transfer 规范 Work Object 或需要追踪物理交接的 Device Supply 进入、离开当前 Device Node 控制工作区的过程。协议只追踪本设备边界内的准备和确认，不追踪资源在两个设备之间的完整运输路线。

### 转移点

```json
{
  "transfer_point_id": "handoff-01",
  "workspace_path": "workspace.position-01",
  "directions": ["ingress", "egress"],
  "allowed_resource_types": ["work_object.generic", "device_supply.generic"],
  "physical_actors": ["human", "robot", "device_agent_controlled_robot"],
  "confirmation_sources": ["operator_confirmed", "vision", "device_readback"],
  "capacity": 1
}
```

每个 Transfer Point MUST 定义：

- 本设备内的工作区路径；
- 允许进入和离开的方向；
- 允许的物理资源类型；
- 可执行物理交接的主体；
- 可以用于 confirm 的确认来源；
- 并发容量和占用约束。

### 边界状态

需要跨越设备边界的 Physical Resource 使用以下边界状态：

```text
outside
ingress_pending
present
reserved
in_use
egress_pending
unknown
```

跨设备运输过程不属于本 Device Node 的状态。资源离开后，本设备只保留审计记录，不需要追踪其是否到达另一个设备。

### 两阶段转移

进出均使用两阶段流程：

```text
transfers/prepare
→ human or robot performs physical handoff
→ transfers/confirm
```

`prepare` 只验证、预留并把资源置为对应的 pending 状态，不建立最终位置关系。预留会改变可执行状态，因此必须更新 `device_state` revision。`confirm` 在获得允许的确认来源后，原子更新位置、包含关系、位置占用和 revision。

支持进出的设备 MUST 实现：

- `transfers/prepare`
- `transfers/confirm`
- `transfers/get`
- `transfers/cancel`

### 准备进入

```json
{
  "jsonrpc": "2.0",
  "id": "transfer-prepare-1",
  "method": "transfers/prepare",
  "params": {
    "device_id": "device-001",
    "direction": "ingress",
    "transfer_point_id": "handoff-01",
    "resource": {
      "id": "resource-incoming-001",
      "kind": "work_object",
      "type": "work_object.generic"
    },
    "counterparty_ref": "opaque-external-robot-reference",
    "options": {
      "expected_revision": 412,
      "idempotency_key": "transfer-prepare-key-001",
      "deadline": "2026-08-31T11:40:00+08:00"
    }
  }
}
```

响应：

```json
{
  "resultType": "complete",
  "transfer_id": "tr-1001",
  "direction": "ingress",
  "state": "PREPARED",
  "previous_revision": 412,
  "new_revision": 413,
  "reservation_expires_at": "2026-08-31T11:40:00+08:00",
  "confirmation_policy": {
    "mode": "any_of",
    "sources": ["operator_confirmed", "vision"]
  },
  "error": null
}
```

`counterparty_ref` 是可选的外部不透明引用，仅用于审计关联。Server MUST NOT 依赖它追踪跨设备路线或另一设备状态。

`transfers/prepare` MUST 支持 `idempotency_key`，并把它绑定到调用身份、设备、方向、Transfer Point 和资源摘要。相同绑定在预留有效期内重试时 MUST 返回同一 `transfer_id`；同一键对应不同内容时必须拒绝。

### 确认转移

```json
{
  "jsonrpc": "2.0",
  "id": "transfer-confirm-1",
  "method": "transfers/confirm",
  "params": {
    "device_id": "device-001",
    "transfer_id": "tr-1001",
    "confirmation": {
      "source": "operator_confirmed",
      "observed_resource_id": "resource-incoming-001",
      "observed_at": "2026-08-31T11:35:20+08:00",
      "resource_uri": null
    },
    "options": {
      "expected_revision": 413
    }
  }
}
```

`confirmed_by` 必须由 Server 根据已验证身份或受信任设备证据写入审计记录，不能接受请求正文自报。传感器、视觉或机器人确认必须引用 Server 可验证的证据或已登记来源。

同一 `transfer_id` 已成功 confirm 后，内容一致的重复 confirm MUST 返回原终态结果，不得再次修改资源或 revision；内容冲突的重复 confirm 必须拒绝。

成功 confirm 后：

- ingress 将资源状态更新为 `present`，建立本设备位置关系并占用 Transfer Point；
- egress 将资源状态更新为 `outside`，清除本设备位置和占用关系；
- 容器型 Work Object 移动时，其 `contained_in` 子对象作为一个聚合整体更新；
- 更新必须产生新的 revision 和审计记录。

如果物理交接无法确认：

- Server MUST NOT 猜测最终位置；
- Transfer 和相关资源 MUST 标记为 `unknown`；
- 后续依赖该位置的动作 MUST 被拒绝，直到人工或传感器重新确认。

### 准备离开

egress 的 `prepare` MUST 额外验证：

- 资源没有被 Action 或 Workflow 使用；
- 资源未被执行锁或 reservation 占用；
- Work Object 的封闭和安全状态满足离开条件；
- 子 Work Object 是否随父 Work Object 一起离开已经明确；
- Transfer Point 可以安全交接。

`transfers/cancel` 只允许在最终 confirm 前取消预留。物理资源已经可能移动时，取消不得直接恢复旧位置；Server 应进入 `unknown` 并请求重新确认。

### 跨设备边界

ALP 允许外部编排系统把一次 egress 与另一设备的 ingress 关联，但不规定跨设备事务、路线、运输状态或端到端完成协议。每个设备只负责：

1. 自己的 Transfer Point；
2. 自己的 prepare 与 confirm；
3. 自己的物理资源位置和 revision；
4. 自己的安全约束与审计。

外部系统可以保存两个本地 `transfer_id` 的关联，本设备无需保存或理解该关联。
