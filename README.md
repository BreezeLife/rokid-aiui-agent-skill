# ROKID AIUI Agent Skill

[![CI](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml)

[简体中文使用说明](docs/usage.zh-CN.md) | [English usage guide](docs/usage.en.md) | [日本語の使い方](docs/usage.ja.md)

这是面向 ROKID AIUI 的 Vibe Coding 快速开始：和 AI 一起写代码，从一句需求走到可导入、可检查、可继续编辑的完整工程，同时避免把浏览器或微信小程序经验误当成 AIUI 能力。

## 这个 Skill 能做什么

你可以用它完成以下 AIUI 开发任务：

- 创建完整、可编辑的 AIUI 项目
- 修改或扩展现有 AIUI 工程
- 审查并调试 AIUI 工程的项目结构、交互和版本兼容性
- 验证项目并交付可由 AIUI Studio 导入的源码目录；本地检查不代表 AIUI Studio 或 Rokid Glasses 真机已经通过

## 快速开始

在支持 Agent Skills 的编码环境终端运行以下安装命令：

```bash
npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent
```

如果 `gh skill --help` 可用，也可以运行 GitHub CLI 安装命令：

```bash
gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
```

先把示例路径 `/absolute/path/to/my_focus_timer` 替换为你自己的绝对输出目录，再把下面这段话交给编码智能体：

```text
使用 $rokid-aiui-agent，为 Rokid Glasses 创建一个 AIUI 0.17.0 专注计时器。
在独立输出目录 /absolute/path/to/my_focus_timer 中创建，不要把新 Agent 写入本 Skill 仓库。
支持语音设置时长，在 _current 和 _blank 中都保持清晰易用；完成后交付可由
AIUI Studio 导入的完整源码目录，运行可用的自动检查，并明确列出仍需 Studio
或真机验证的项目。不要把未执行的检查写成已经通过。
```

你也可以把“专注计时器”换成天气、清单、导航提示，或直接要求审查和修复现有 AIUI 工程。

## 你会得到什么

创建或实现任务会交付完整、可编辑的 AIUI 项目目录，可直接作为 AIUI Studio 的导入根，而不是一组零散代码或只有 `.aix` 包。

`app.json.pages` 声明的所有页面，以及这些页面引用的所有图片、样式和其他资源，都必须包含在交付目录中；缺少任何一项都不算完整工程。

典型目录如下：

```text
my-agent/
├── AGENTS.md
├── aiui-audit-claims.json
├── app.js
├── app.json
└── pages/
    └── index/
        └── index.ink
```

智能体还会说明目标版本、承载面、输入方式、已运行的检查，以及哪些 Studio 或设备项目仍待人工确认。

`_current` 是嵌入对话的承载面，`_blank` 是全屏承载面；`BLOCKED` 表示该项仍待验证，而不是已经通过。

## 导入 AIUI Studio

根据工程所在位置选择导入方式：

- 本地导入：选择包含 `app.json` 的交付目录本身，不要只选择其中的页面或打包产物。
- GitHub 导入：提供仓库、ref 和 AIUI 项目所在的子目录。内置示例可直接使用以下坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: skills/rokid-aiui-agent/assets/focus-timer-agent
```

本地检查不能替代 AIUI Studio 导入和 Rokid Glasses 真机验证。没有登录 Studio 或连接目标设备时，相应结果应明确保留为 `BLOCKED`。

## 内置 Focus Timer

[`skills/rokid-aiui-agent/assets/focus-timer-agent`](skills/rokid-aiui-agent/assets/focus-timer-agent/) 是随 Skill 安装的唯一产品化示例 Agent，也是一个完整的 AIUI Studio 导入根。

它是面向 Rokid Glasses、仅使用 Page 的日文计时器。未指定时长时默认 10 分钟，也接受 1～3600 秒和可选标签。

源码和本地测试只验证收到主要操作事件后的状态映射：

| 计时器状态 | 收到事件后的操作 |
| --- | --- |
| 未开始 | 开始 |
| 进行中 | 暂停 |
| 已暂停 | 继续 |
| 已完成 | 重新开始 |

本地证据不能证明眼镜已发出对应事件。点头和触摸板仍需 Rokid Glasses 真机验证，状态为 `BLOCKED`。

对话中修改为新的时长会打开一个新 Page。语音触发仍需 AIUI Studio 和 Rokid Glasses 真机验证，状态同样为 `BLOCKED`。

该计时器不承诺后台持续运行、系统通知或持久化恢复。

## 自动检查

Skill 会根据当前工程运行结构验证、确定性业务逻辑测试，以及本机 AIX 实际支持的 preview、pack 和 list 流程。它还要求项目级 UX 表与逐能力表，避免用一次浏览器预览代替 Studio 或真机结论。

完整命令与结果语义见三份语言指南；验收原则见 [UX 与能力测试](skills/rokid-aiui-agent/references/ux-and-capability-testing.md)。

## 版本边界

当工程和宿主没有明确版本时，Skill 默认以稳定版 AIUI `0.17.0` 为目标。`0.18` 能力只有在目标明确支持时才会启用，避免把预览版配置混进稳定版项目。

Skill 会先检查当前环境实际提供的 AIX 命令，不会假设不存在的创建、构建或部署流程。

## 仓库内容

仓库将 Skill、参考资料、检查工具和可导入示例分开存放：

| 路径 | 用途 |
| --- | --- |
| [`skills/rokid-aiui-agent/SKILL.md`](skills/rokid-aiui-agent/SKILL.md) | Skill 入口和任务流程 |
| [`skills/rokid-aiui-agent/references/`](skills/rokid-aiui-agent/references/) | 按需读取的 AIUI 开发参考 |
| [`skills/rokid-aiui-agent/scripts/`](skills/rokid-aiui-agent/scripts/) | 项目结构、能力和审计检查工具 |
| [`skills/rokid-aiui-agent/assets/studio-importable-minimal/`](skills/rokid-aiui-agent/assets/studio-importable-minimal/) | 可导入 AIUI Studio 的最小工程模板 |
| [`skills/rokid-aiui-agent/assets/focus-timer-agent/`](skills/rokid-aiui-agent/assets/focus-timer-agent/) | 仓库中唯一的产品化示例 Agent |
| [`docs/usage.zh-CN.md`](docs/usage.zh-CN.md)、[`docs/usage.en.md`](docs/usage.en.md) 和 [`docs/usage.ja.md`](docs/usage.ja.md) | 中文、英文和日文完整指南 |

## 深入指南

需要完整提示词、验证命令或规范细节时，按任务选择以下入口：

- [简体中文完整指南](docs/usage.zh-CN.md)：常见提示词、完整验证顺序、打包、Studio 导入与故障排查。
- [English guide](docs/usage.en.md)：the same end-to-end workflow in English.
- [日本語ガイド](docs/usage.ja.md)：同じ開発・検証フローの日本語版。
- [Skill 入口](skills/rokid-aiui-agent/SKILL.md)：任务路由、交付规则和按需参考资料。
- [来源优先级](skills/rokid-aiui-agent/references/source-of-truth.md)：官方版本、实现与示例发生冲突时的取舍原则。

## 来源与许可证

本项目以 AIUI 版本匹配的官方文档、实现和可运行示例为主要依据，并明确区分第三方材料。详细归属见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。

代码以 [Apache License 2.0](LICENSE) 发布。未经真实执行的 AIUI Studio、平台或设备行为不会被写成已验证结论。
