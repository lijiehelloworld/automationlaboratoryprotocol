---
title: "客户端能力"
description: "ALP 客户端的发现、状态协调、审批与输入能力"
---

## 发现

客户端在首次使用服务端时应当调用 `server/discover`，获得：

- 服务端信息；
- 支持的协议版本；
- 服务端能力；
- 设备节点列表；
- 每个设备的能力清单地址；
- 可选能力的支持状态。

客户端不得根据自然语言设备名称猜测动作、参数或容器能力。可执行能力以能力清单和运行时数据结构定义为准。

## 状态协调

客户端在执行 `write`、`invoke` 或 `workflows/run` 前应当：

1. 读取全部强前置状态；
2. 检查 `observed_at` 和 `expires_at`；
3. 保存状态 `revision`；
4. 执行试运行或工作流校验；
5. 在正式请求中携带 `expected_revision`。

状态过期后，客户端必须重新读取，不能仅靠本地缓存继续执行物理动作。

## 审批与输入

高风险动作可以要求人工授权。客户端必须清楚展示：

- 设备；
- 动作或工作流；
- 已验证参数；
- 预期物理效果；
- 风险和不可逆影响；
- 授权有效期。

人工输入不能替代设备限位、安全门或传感器检查。

### 需要输入

```json
{
  "resultType": "input_required",
  "inputRequests": [
    {
      "input_id": "confirm-plate-loaded",
      "type": "confirmation",
      "prompt": "请确认目标对象已经放入指定交接点。",
      "schema": {
        "type": "boolean",
        "const": true
      }
    }
  ],
  "requestState": "server-issued-state-token"
}
```

客户端补充输入时必须使用新的 JSON-RPC `id` 重试原请求，并携带服务端签发的 `requestState`。服务端必须重新验证当前状态。

---
