# 属性

Property 表示设备、工作区、对象、样品或环境中的一个状态值。

## 属性定义

```json
{
  "path": "environment.temperature_c",
  "title": "环境温度",
  "description": "工作站环境温度。",
  "schema": {
    "type": "number"
  },
  "unit": "Cel",
  "access": ["read"],
  "source": "sensor",
  "freshness_ms": 5000,
  "read_side_effect": "sensor_acquisition",
  "constraint_ids": []
}
```

状态路径 SHOULD 使用以下命名空间：

```text
device.*
workspace.*
actuator.*
sensor.*
environment.*
sample.*
consumable.*
objects.*
```

#### `read`

`read` 读取一个逻辑状态路径。调用方不需要知道其来源是寄存器、相机、传感器还是软件状态。

请求：

```json
{
  "jsonrpc": "2.0",
  "id": "read-1",
  "method": "read",
  "params": {
    "device_id": "device-001",
    "path": "environment.temperature_c",
    "parameters": {
      "max_age_ms": 5000
    }
  }
}
```

响应中的 `StateValue`：

```json
{
  "path": "environment.temperature_c",
  "value": 24.6,
  "unit": "Cel",
  "quality": "confirmed",
  "source": "sensor",
  "revision": 324,
  "observed_at": "2026-08-31T10:20:31.203+08:00",
  "expires_at": "2026-08-31T10:20:36.203+08:00",
  "error": null
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `path` | 是 | 状态路径 |
| `value` | 是 | 当前值；未知时为 `null` |
| `unit` | 是 | 单位；无单位时为 `null` |
| `quality` | 是 | `confirmed`、`estimated` 或 `unknown` |
| `source` | 是 | 状态来源 |
| `revision` | 是 | 状态字典版本 |
| `observed_at` | 是 | 实际观测时间 |
| `expires_at` | 是 | 超过该时间后不得作为强前置状态；不适用时为 `null` |
| `error` | 是 | 读取错误；成功时为 `null` |

允许的来源：

```text
device_readback
sensor
vision
operator_confirmed
software_derived
```

`read` 默认 MUST NOT 移动物理执行机构。确实需要移动硬件才能获得的观测必须定义为 Action，并通过 `invoke` 执行。

#### `write`

`write` 修改单一可写状态或执行简单原子写入。包含多个物理步骤或多个状态效果的动作 MUST 使用 `invoke`。

```json
{
  "jsonrpc": "2.0",
  "id": "write-1",
  "method": "write",
  "params": {
    "device_id": "device-001",
    "path": "actuator.primary.enabled",
    "value": true,
    "options": {
      "expected_revision": 324,
      "deadline": "2026-08-31T10:22:00+08:00",
      "dry_run": false
    }
  }
}
```

```json
{
  "resultType": "complete",
  "outcome": "succeeded",
  "changed": true,
  "previous_revision": 324,
  "new_revision": 325,
  "evidence": [],
  "error": null
}
```

Physical Resource 跨越设备边界时 MUST 使用 `transfers/prepare` 和 `transfers/confirm`，不得通过通用 `write` 直接伪造其位置或安装状态。

Server MUST：

- 校验属性是否可写；
- 校验输入 Schema、权限、截止时间和约束；
- 在执行锁内比较 `expected_revision`；
- 在 `dry_run=true` 时禁止发送设备写命令；
- 只在明确成功后更新状态和 revision；
- 在物理结果未知时返回 `unknown`。
