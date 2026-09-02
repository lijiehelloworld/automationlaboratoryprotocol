# Automation Laboratory Language

Automation Laboratory Language（ALL，自动化实验室语言）规范文档。

ALL 使用 HTTPS 远程连接。ALL 语言引擎由编译/解释器、仿真器和执行器组成；其设备通信部分 FSP 从操作、对象和系统三个维度说明设备接口。

## 本地预览

安装 Node.js 20 或更高版本，然后在仓库根目录运行：

```bash
npx mint dev
```

Mintlify 会读取根目录的 `docs.json` 和 MDX 页面。

## 发布

在 Mintlify 控制台导入本 GitHub 仓库。默认生产分支为 `main`；此后推送到 `main` 即触发构建和发布。

## 文档边界

规范性要求以“规范”导航下的条款为准。架构背景和文末示例用于解释，不决定实现符合性。
