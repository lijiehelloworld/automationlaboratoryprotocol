---
title: "身份认证与授权"
description: "ALL 远程连接的 OAuth 2.1 发现、令牌、权限和错误规范"
---

## 适用范围

ALL 只定义基于 HTTPS 的远程连接。除公开发现元数据外，服务端必须要求经过验证的访问令牌。

身份认证回答“调用者是谁”，授权回答“该调用者可以对哪些系统、对象、操作和 Workflow 做什么”。服务端不得使用客户端名称、设备描述、对象内容、自然语言文本或 Workflow 内容替代授权判断。

## 参与方

| 参与方 | 责任 |
| --- | --- |
| 客户端 | 集成在 Agent、用户应用或自动化系统中；获取令牌并发送 ALL 请求 |
| ALL 服务端 | OAuth 受保护资源；验证令牌并执行资源级授权 |
| 授权服务器 | 验证主体、取得授权并签发访问令牌 |
| 资源所有者 | 授权客户端代表其访问实验室系统的主体 |

ALL 服务端与授权服务器可以由同一组织部署，但必须保持资源标识、发行方和受众校验边界。

## HTTPS 要求

- 生产端点必须使用 HTTPS。
- 客户端必须验证服务端证书和主机名。
- 服务端不得接受 URL 查询参数中的访问令牌。
- 访问令牌、授权码、客户端密钥和刷新令牌不得写入 ALL 请求参数、能力清单、对象字段、Workflow、日志或错误描述。
- 服务端可以额外要求双向 TLS，但不得以此替代 OAuth 权限判断。

## 受保护资源元数据

服务端必须发布 OAuth 受保护资源元数据。默认地址为：

```text
https://<all-server>/.well-known/oauth-protected-resource
```

当一个主机托管多个独立 ALL 资源标识时，可以使用带路径的受保护资源元数据地址。客户端必须以元数据中的 `resource` 为准，不得仅根据主机名推断令牌受众。

```json
{
  "resource": "https://lab.example.com/all",
  "authorization_servers": [
    "https://auth.example.com"
  ],
  "bearer_methods_supported": ["header"],
  "scopes_supported": [
    "all:system:read",
    "all:objects:read",
    "all:objects:write",
    "all:operations:read",
    "all:operations:execute",
    "all:workflows:read",
    "all:workflows:run"
  ],
  "resource_documentation": "https://lab.example.com/all/docs"
}
```

字段规则：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `resource` | `string` | 是 | ALL 资源的绝对 HTTPS URI；必须与令牌受众比较使用的资源标识完全一致 |
| `authorization_servers` | `string[]` | 是 | 一个或多个可信授权服务器发行方 URI；不得为空 |
| `bearer_methods_supported` | `string[]` | 是 | ALL 仅允许 `header` |
| `scopes_supported` | `string[]` | 是 | 服务端可能接受的权限范围；实际授予范围可以更小 |
| `resource_documentation` | `string` | 否 | 面向人的绝对 HTTPS 文档地址 |

客户端不得把元数据中的授权服务器自动视为可信。客户端必须根据部署策略或用户选择确认授权服务器，并把客户端注册信息绑定到授权服务器发行方。

## 授权服务器发现

客户端从 `authorization_servers` 选择授权服务器后，必须读取其 OAuth 授权服务器元数据或 OpenID Connect 发现文档。客户端至少校验：

- `issuer` 与选择的授权服务器发行方完全一致；
- `authorization_endpoint` 和 `token_endpoint` 使用 HTTPS；
- 支持 `S256` PKCE；
- 支持客户端需要的授权类型和令牌端点认证方式；
- 响应中的发行方标识与授权请求使用的发行方一致。

客户端凭据必须与签发它的 `issuer` 绑定。授权服务器变化时，客户端不得复用另一发行方签发或登记的客户端凭据。

## 客户端标识

客户端可以使用以下方式之一获得 `client_id`：

1. 预先登记的静态客户端标识；
2. 授权服务器支持的客户端元数据文档；
3. 部署方明确支持的其他标准客户端登记方式。

ALL 核心不要求动态客户端注册。不能安全保存客户端密钥的 Agent、本地桌面应用和浏览器应用必须作为公共客户端，不得被要求持有长期共享密钥。

## 授权流程

### 用户委托访问

用户委托访问必须使用授权码流程并启用 PKCE：

- `code_challenge_method` 必须为 `S256`；
- 每次授权请求必须生成新的 `state`；
- 支持 OpenID Connect 时应当使用 `nonce`；
- 客户端必须验证授权响应的 `state` 和发行方；
- 授权码只能发送给原授权请求使用的令牌端点；
- 客户端必须在授权请求和令牌请求中携带 ALL `resource` 标识。

授权请求示例：

```http
GET /authorize?
  response_type=code&
  client_id=https%3A%2F%2Fclient.example.com%2Fmetadata.json&
  redirect_uri=https%3A%2F%2Fclient.example.com%2Fcallback&
  code_challenge=<S256-challenge>&
  code_challenge_method=S256&
  state=<random-state>&
  resource=https%3A%2F%2Flab.example.com%2Fall&
  scope=all%3Asystem%3Aread%20all%3Aoperations%3Aread
Host: auth.example.com
```

成功授权响应：

```http
HTTP/1.1 302 Found
Location: https://client.example.com/callback?code=<authorization-code>&state=<random-state>&iss=https%3A%2F%2Fauth.example.com
```

客户端必须在交换授权码前验证 `state`、`iss` 和回调地址。

令牌请求使用 `application/x-www-form-urlencoded`：

```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=<authorization-code>&
redirect_uri=https%3A%2F%2Fclient.example.com%2Fcallback&
client_id=https%3A%2F%2Fclient.example.com%2Fmetadata.json&
code_verifier=<pkce-verifier>&
resource=https%3A%2F%2Flab.example.com%2Fall
```

令牌响应：

```json
{
  "access_token": "<access-token>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "all:system:read all:operations:read",
  "refresh_token": "<refresh-token>"
}
```

| 字段 | 必填 | 规则 |
| --- | --- | --- |
| `access_token` | 是 | 只能发送到其受众包含的 ALL 资源 |
| `token_type` | 是 | 必须为 `Bearer`，大小写不敏感 |
| `expires_in` | 是 | 正整数秒数 |
| `scope` | 是 | 实际授予权限，可能少于请求范围 |
| `refresh_token` | 否 | 客户端必须安全保存并只发送到原发行方令牌端点 |

客户端必须以响应中的实际 `scope` 为准。缺少后续调用所需权限时不得继续执行。

### 自动化服务访问

无人值守自动化可以使用授权服务器明确声明支持的客户端凭据流程。服务端必须把权限限定到具体客户端、ALL 资源、设备范围和允许方法，不得为方便自动化授予无限制管理员权限。

```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <client-credentials>

grant_type=client_credentials&
resource=https%3A%2F%2Flab.example.com%2Fall&
scope=all%3Asystem%3Aread%20all%3Aoperations%3Aexecute
```

客户端凭据流程不得冒充用户主体。服务端审计必须区分用户委托令牌和自动化客户端令牌。

### 禁止流程

ALL 不允许隐式流程、资源所有者密码凭据流程或在请求参数中直接提交用户名和密码。

## 访问令牌

客户端必须使用 HTTP `Authorization` 请求头发送令牌：

```http
Authorization: Bearer <access-token>
```

服务端必须验证：

1. 令牌签名或不透明令牌内省结果；
2. 签名算法符合部署策略，不接受算法降级；
3. 发行方属于受保护资源元数据声明的授权服务器；
4. 受众包含当前 ALL `resource`；
5. `exp` 尚未过期，`nbf` 已生效；
6. 令牌未被撤销且当前处于活动状态；
7. 权限范围覆盖当前方法；
8. 令牌绑定信息与当前客户端或传输一致（如部署使用令牌绑定）；
9. 主体、客户端和授权上下文满足部署策略。

自包含令牌中的未知声明不得自动产生权限。访问令牌的显示名称、电子邮件或自然语言角色名称不得作为唯一授权依据。

## 权限范围

ALL 定义以下基础权限范围：

| 权限范围 | 允许行为 |
| --- | --- |
| `all:system:read` | 系统发现、能力清单、状态和事件读取 |
| `all:objects:read` | 查询研究对象 |
| `all:objects:write` | 登记和修正研究对象元数据 |
| `all:operations:read` | 查询操作定义和操作任务 |
| `all:operations:execute` | 执行写入、调用、响应输入和取消 |
| `all:workflows:read` | 查询 Workflow 模板 |
| `all:workflows:run` | 校验和运行 Workflow |

权限范围只表示能力上限。服务端必须继续按以下维度执行细粒度授权：

```text
verified_subject
client_id
device_ids
object_ids 或 object_types
operation_names
workflow_names
parameter_constraints
valid_from / valid_until
human_approval_requirement
```

服务端可以通过策略系统、令牌声明或授权服务器令牌交换结果获得这些限制，但不得要求客户端把可伪造的权限对象放入普通请求参数。

## 方法所需权限

能力清单中的每个方法、操作定义和 Workflow 定义必须声明 `required_scopes`。服务端可以要求更多部署权限，但不得把未公开的权限当作长期稳定接口。

```json
{
  "name": "move_object",
  "required_scopes": ["all:operations:execute"],
  "authorization": {
    "device_scope_required": true,
    "object_scope_required": true,
    "human_approval": "conditional"
  }
}
```

客户端必须把能力清单中的权限声明视为调用前提示，而不是服务端授权结果。最终授权只能由服务端在请求时决定。

## 未认证响应

请求缺少令牌、令牌无效或令牌不适用于当前资源时，服务端必须返回 HTTP `401 Unauthorized`，并包含 `WWW-Authenticate`：

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer resource_metadata="https://lab.example.com/.well-known/oauth-protected-resource", error="invalid_token"
Content-Type: application/json
```

```json
{
  "error": "invalid_token",
  "error_description": "访问令牌无效、已过期或不适用于当前 ALL 资源"
}
```

在身份认证完成前，服务端不得返回设备是否存在、对象内容、能力差异或授权策略细节。

## 权限不足响应

令牌有效但权限不足时，服务端必须返回 HTTP `403 Forbidden` 和 JSON-RPC 错误：

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope", scope="all:operations:execute"
Content-Type: application/json
```

```json
{
  "jsonrpc": "2.0",
  "id": "req-42",
  "error": {
    "code": -32004,
    "message": "当前身份没有执行该操作的权限",
    "data": {
      "name": "PermissionDenied",
      "recoverable": true,
      "required_scopes": ["all:operations:execute"],
      "authorization_uri": "https://auth.example.com/authorize"
    }
  }
}
```

服务端只能返回客户端可安全获知的权限范围，不得泄露其他主体、隐藏设备或内部策略。

## 权限提升

操作或 Workflow 需要更高权限时，服务端可以返回 `PermissionDenied`，并给出所需权限范围。客户端必须重新发起授权流程并明确请求新增范围；不得把旧令牌与新范围在本地拼接。

新增权限应当累积当前仍需要的范围，避免权限提升后意外丢失前序步骤需要的权限。授权服务器拒绝新增权限时，客户端必须停止执行。

## 缓存与身份隔离

- 带身份的能力清单、对象目录和 Workflow 目录必须使用 `cacheScope=private`。
- 缓存键必须至少包含 ALL 资源标识、授权服务器发行方、客户端身份、主体身份、协议版本和权限集合摘要。
- 身份、权限或令牌受众变化时不得复用旧缓存。
- 客户端不得仅因两个令牌的主体显示名称相同而共享缓存。

## 撤销与过期

客户端收到 `invalid_token` 后可以使用受支持的刷新机制获取新令牌，但不得无限重试。服务端发现令牌被撤销、主体被禁用或授权上下文失效时，必须立即拒绝新请求；已经开始的物理操作必须进入安全终态，并在审计中记录授权失效事件。

## 审计要求

授权审计至少记录：

```text
timestamp
request_id
issuer
subject
client_id
resource
granted_scopes
method
device_id
authorization_decision
policy_reference
```

审计中不得记录访问令牌、授权码、刷新令牌、客户端密钥或完整敏感声明。

## 正式类型定义

```typescript
interface ProtectedResourceMetadata {
  resource: string;
  authorization_servers: string[];
  bearer_methods_supported: ["header"];
  scopes_supported: string[];
  resource_documentation?: string;
}

interface AuthorizationRequirement {
  required_scopes: string[];
  device_scope_required?: boolean;
  object_scope_required?: boolean;
  human_approval?: "never" | "conditional" | "always";
}

interface PermissionDeniedData {
  name: "PermissionDenied";
  recoverable: boolean;
  required_scopes: string[];
  authorization_uri?: string;
}
```
