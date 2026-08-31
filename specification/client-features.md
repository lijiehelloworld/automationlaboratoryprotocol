---
title: "客户端能力"
description: "ALP 客户端的发现、状态协调、审批与输入能力"
---

## 发现

Client SHOULD 在首次使用 Server 时调用 `server/discover`，获得：

- Server 信息；
- 支持的协议版本；
- Server 能力；
- Device Node 列表；
- 每个设备的 Manifest URI；
- 可选能力的支持状态。

Client MUST NOT 根据自然语言设备名称猜测动作、参数或容器能力。可执行能力以 Manifest 和运行时 Schema 为准。

## 状态协调

Client 在执行 `write`、`invoke` 或 `workflows/run` 前 SHOULD：

1. 读取全部强前置状态；
2. 检查 `observed_at` 和 `expires_at`；
3. 保存状态 `revision`；
4. 执行 dry-run 或 Workflow 校验；
5. 在正式请求中携带 `expected_revision`。

状态过期后，Client MUST 重新读取，不能仅靠本地缓存继续执行物理动作。

## 审批与输入

高风险动作可以要求人工授权。Client MUST 清楚展示：

- 设备；
- 动作或 Workflow；
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

Client 补充输入时 MUST 使用新的 JSON-RPC `id` 重试原请求，并携带 Server 签发的 `requestState`。Server MUST 重新验证当前状态。

---
