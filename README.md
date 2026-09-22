# AI-native Laboratory Language

AI-native Laboratory Language（ALL，AI 原生实验室语言）规范文档。

ALL 语言引擎由编译/解释器、仿真器和执行器组成。FSP 服务通过动作契约、能力门控和适配器调用设备；底层设备接口从操作、对象和系统三个维度表达请求与结果。HTTP、CLI、MCP、RPC 和厂商 SDK 均可作为承载方式。

## 本地预览

安装 Node.js 20 或更高版本，然后在仓库根目录运行：

```bash
npx mint dev
```

Mintlify 会读取根目录的 `docs.json`，首页为 `index.mdx`，其他页面位于 `docs/`。

## 发布

主仓库为 [GitCode / mimedal/all](https://gitcode.com/mimedal/all)，默认分支为 `main`。GitHub 仓库只保存 Mintlify 发布需要的正式文档镜像；不在 GitHub 上编辑。Mintlify 继续从 GitHub 镜像自动部署，网站导航中的“GitCode”链接指向主仓库。

完成 GitCode 提交后，在主仓库运行：

```bash
./scripts/publish-github-docs.sh
```

脚本只把 `docs/`、`images/`、`index.mdx`、`docs.json`、`style.css`、`README.md` 和 `.mintignore` 组成的新快照推送到 GitHub `main`。它不会复制本地草稿和临时资料。

## 文档边界

规范性要求以“规范”导航下的条款为准。架构背景和文末示例用于解释，不决定实现符合性。

## 目录结构

```text
ALL/
├── docs/                 # 正式站点文档
│   ├── architecture/     # 架构与术语
│   ├── specification/    # 规范、FSP、设备接口与语言引擎
│   ├── community/        # 社区与治理
│   ├── proposals/        # 改进提案流程与模板
│   ├── quickstart.mdx    # 快速开始
│   └── faq.mdx           # 常见问题
├── images/               # 网站使用的图片与标志
├── planning/             # 本地计划和研究过程，不提交
├── references/           # 本地研究原件、外部样例与历史文档
│   └── legacy-docs/      # 历史协议草稿、分析文档及配图
├── artifacts/            # 历史会话产物、截图和附件
├── index.mdx             # 网站首页
├── docs.json             # 网站配置、导航和旧页面重定向
├── style.css             # 网站全局样式
├── AGENTS.md             # 本地协作约定，不提交
└── README.md             # 项目入口与使用说明
```

## Git 管理与网站发布范围

| 内容 | 提交到 GitCode | 发布到 Mintlify |
| --- | --- | --- |
| `docs/`、`images/`、`index.mdx`、`style.css` | 是 | 是 |
| `docs.json` | 是 | 作为网站配置使用 |
| `README.md`、`.mintignore` | 是 | 进入 GitHub 文档镜像 |
| `scripts/`、`.gitignore` | 是 | 否 |
| `AGENTS.md`、`planning/`、`references/`、`artifacts/`、`drafts/`、`tmp/`、`temp/` | 否，仅本地保存 | 否 |
| 依赖、缓存、编辑器配置 | 否 | 否 |

`.gitignore` 控制 Git 收录范围；`.mintignore` 控制网站处理和发布范围。GitCode 主仓库可以包含发布脚本等开源项目文件；GitHub 镜像只包含上面列出的正式文档和站点配置。

研究原件和历史产物按原目录保留，不删除附件。新增参考材料放入 `references/`，截图和临时输出放入 `artifacts/`；只将审核后的正式内容与所需配图放入 `docs/` 和 `images/`。不要仅靠移出导航来隐藏参考页面，排除机制见 [Mintlify 官方说明](https://www.mintlify.com/docs/organize/mintignore)。

## 提交前检查

在仓库根目录运行：

```bash
git status --short
git diff --check
npx mint validate
npx mint broken-links
```

目录迁移提交需要同时包含旧文件删除、新文件加入和导航更新。提交前查看暂存区差异，确保没有研究原件、缓存或临时文件；GitCode 推送不会直接触发 Mintlify，发布脚本推送 GitHub 文档镜像后才会触发网站发布。

整理前的文档地址已在 `docs.json` 中设置重定向，首页和 `/images/` 资源路径不变。继续在仓库根目录执行预览命令，无需更改 Mintlify 的仓库目录设置。
