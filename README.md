# ROKID AIUI Agent Skill

[![CI](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml)

[简体中文指南](docs/usage.zh-CN.md) | [English](docs/usage.en.md) | [日本語](docs/usage.ja.md)

让 Codex、Claude Code、Cursor 等编码工具按 ROKID AIUI 规范开发 Agent。安装这个 Skill 后，你描述需求，编码工具生成可继续编辑、可导入 AIUI Studio 的完整项目，并检查功能、交互体验和提交材料。

新项目默认使用 **AIUI 0.19.0**。仓库内的日文 Focus Timer 示例保留在 **0.17.0**，用于兼容性回归。

[选择入口](#选择使用入口) · [开始开发](#快速开始) · [查看交付物](#你会得到什么) · [了解验证范围](#自动检查)

## 这个 Skill 能做什么

你可以让编码工具使用它完成以下任务：

- 创建完整、可编辑的 AIUI 项目
- 修改或扩展现有 AIUI 工程
- 借鉴社区示例构建相机、模型与语音流程，检查取消重试、重复输入及真实数据链路，见[实践指南](skills/rokid-aiui-agent/references/community-patterns.md)
- 审查和调试 AIUI 代码、交互与版本兼容性
- 验证项目，交付可由 AIUI Studio 导入的源码；满足打包条件时，额外交付 `.aix` 包
- 检查功能与 UX，准备 Agent 介绍、权限说明和审核材料

## 选择使用入口

可以使用网页、桌面 App 或 CLI（命令行）。先安装或打开工具，再添加本 Skill；安装 App 本身不会自动安装 Skill。

| 使用入口 | 如何开始 | 安装与操作步骤 |
| --- | --- | --- |
| Codex 网页端 | 在 ChatGPT 中创建 Codex Cloud 环境，将 Skill 放进云端项目仓库 | [网页与云端配置](docs/web-and-desktop.zh-CN.md#codex-web) |
| Claude 网页端 | 在 Customize → Skills 上传完整 Skill ZIP 并启用 | [网页上传步骤](docs/web-and-desktop.zh-CN.md#claude-web) |
| Codex 桌面 App | 下载 ChatGPT 桌面 App，选择 Codex，用内置安装器添加 Skill | [App 下载、安装与调用](docs/web-and-desktop.zh-CN.md#codex-desktop) |
| Claude 桌面 App | 下载 Claude，选择 Code 打开本地项目，再添加 Skill | [App 下载、安装与调用](docs/web-and-desktop.zh-CN.md#claude-desktop) |
| CLI / IDE | 在终端用 Skills CLI 安装，再在编码工具中调用 | [下方五步流程](#路线-2用-codex-等-vibe-coding-工具开发) |

不想使用终端，可以按桌面 App 指南操作。只使用浏览器时，分别遵循 Codex Cloud 或 Claude 网页流程；本机安装的 Skill 不会自动变成所有网页任务可用的 Skill。

## 快速开始

已有项目或想先看示例，选择路线 1；想让 AI 帮你开发，选择路线 2。

### 路线 1：在 AIUI Studio 中打开项目

按[导入 AIUI Studio](#导入-aiui-studio)打开本地或 GitHub 上的完整项目，然后在 Studio 中继续编辑和开发。

还没有项目时，可以先打开[内置 Focus Timer](#内置-focus-timer)。

### 路线 2：用 Codex 等 Vibe Coding 工具开发

以下以 Codex 的 CLI / IDE 安装方式为例；其他支持 Agent Skills 的编码工具也适用。运行这里的 Skills CLI 需要 Node.js `22.20` 或更高版本，见[运行要求](https://github.com/vercel-labs/skills#install-a-skill)。桌面 App 用户也可用上方指南中的安装方式，再复用下面的开发需求。

1. 安装 Skill。在支持 Agent Skills 的编码环境终端运行。推荐以下命令，将 Skill 安装到当前用户，并检查安装结果：

   ```bash
   npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent --agent codex --global
   npx skills list --agent codex --global
   ```

   列表中应出现 `rokid-aiui-agent`。Claude Code 或 Cursor 用户，把两条命令中的 `codex` 换成下表对应参数。`--global` 允许多个工程共用 Skill，避免把技能文件放进 AIUI 项目的导入目录。

   | 工具 | `--agent` 参数 | 在聊天中调用 |
   | --- | --- | --- |
   | Codex | `codex` | 输入 `$rokid-aiui-agent`；[官方说明](https://learn.chatgpt.com/docs/build-skills#how-chatgpt-and-codex-use-skills) |
   | Claude Code | `claude-code` | 输入 `/rokid-aiui-agent`；[官方说明](https://code.claude.com/docs/en/skills) |
   | Cursor | `cursor` | 输入 `/`，搜索并选择 `rokid-aiui-agent`；[官方说明](https://cursor.com/docs/skills#how-skills-work) |

   如果 `gh skill --help` 可用，也可以使用以下备用命令安装到 Codex：

   ```bash
   gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
   ```

2. 打开独立工作区。在编码工具中打开本 Skill 仓库之外的目录，并启用能读写文件、运行终端命令的 Agent 模式。

3. 调用 Skill。把 `/absolute/path/to/my_focus_timer` 替换为你自己的绝对输出目录，将下面的提示词发到 Codex 聊天输入框：

   ```text
   使用 $rokid-aiui-agent，创建 AIUI 0.19.0 专注计时器。
   输出到独立目录 /absolute/path/to/my_focus_timer，不要写入本 Skill 仓库。
   先说明已读取的 SKILL.md 路径，并确认默认目标版本为 0.19.0。
   支持语音设置时长，以及开始、暂停、继续、重置，覆盖 _current 和 _blank。
   交付完整、可编辑、可导入 AIUI Studio 的源码工程。
   检查功能、边界输入、异常恢复、生命周期，以及焦点、触摸和语音交互的 UX。
   执行可用检查，交付实际结果、项目级 UX 表和逐能力表。
   AIX pack/list 与源码指纹校验成功时，在导入根之外交付 .aix 包。
   在导入根之外准备 Agent 介绍、调用示例、权限用途和审核材料清单。
   未执行的 Studio、平台或真机验证保留 BLOCKED，不把本地预览写成真机通过。
   ```

   Claude Code 用户将首行改为 `/rokid-aiui-agent 创建 AIUI 0.19.0 专注计时器。`；Cursor 用户先从 `/` 菜单选中 Skill，再粘贴需求并删去 `使用 $rokid-aiui-agent，` 前缀。可将“专注计时器”换成你的需求，或要求审查、修复现有工程。

4. 检查交付结果。确认收到完整、可编辑的 AIUI 项目目录，并查看智能体已实际执行的检查与验证结果。交付物清单见[下一节](#你会得到什么)。

5. 导入 AIUI Studio。选择包含 `app.json` 的源码目录本身，按[导入说明](#导入-aiui-studio)继续验收。

如果安装后找不到 Skill，重新打开会话或重启工具，并确认安装与开发使用的是同一台机器和用户。其他工具的安装参数见 [Skills CLI 支持列表](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)。

## 你会得到什么

创建任务中，完整、可编辑的源码工程始终是必交付物，以 AIUI 项目目录交付。选择这个目录即可导入 AIUI Studio。

| 交付物 | 内容与位置 |
| --- | --- |
| 源码工程 | `app.json`、入口代码、全部页面及资源，放在独立输出目录 |
| 验证报告 | 实际执行结果、项目级 UX 表、逐能力表，以及仍待验证的项目 |
| `.aix` 包 | 打包条件满足时额外交付，放在导入根之外 |
| 提交材料 | Agent 介绍、调用示例、权限用途、审核步骤和待补素材清单，放在导入根之外 |

`app.json.pages` 声明的所有页面，以及页面引用的所有图片、样式和其他资源，都必须包含在源码工程中。一个单页工程的目录示例：

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

若完整 AIX pack/list 与指纹校验成功，默认同时在导入根之外交付一个 `.aix` 包，并报告源码指纹、包路径、字节数、SHA-256 和清单结果。该包不能作为 AIUI Studio 导入根，也不能替代源码。

报告中的 `_current` 表示嵌入对话的界面，`_blank` 表示全屏界面；`PASS` 表示该项检查已执行并通过，`FAIL` 表示执行后失败，`BLOCKED` 表示条件不足、仍待验证。AIX 工具不可用时记为 `BLOCKED`，实际打包或检查失败时记为 `FAIL`。

## 导入 AIUI Studio

根据源码所在位置选择导入方式：

- **本地项目**：选择包含 `app.json` 的目录本身
- **GitHub 项目**：提供仓库地址、分支或提交，以及 AIUI 项目子目录

内置 Focus Timer 使用以下 GitHub 导入坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: skills/rokid-aiui-agent/assets/focus-timer-agent
```

本地检查不能替代 AIUI Studio 导入和 Rokid Glasses 真机验证。未登录 Studio 或未连接目标设备时，相应结果保留为 `BLOCKED`。

## 内置 Focus Timer

[Focus Timer 源码](skills/rokid-aiui-agent/assets/focus-timer-agent/)是仓库唯一的产品化示例 Agent，可直接作为 Studio 导入根。它是 AIUI `0.17.0` 的日文单页计时器，默认 10 分钟，接受 1～3600 秒及可选标签。

源码和本地测试验证以下事件与状态映射：

| 计时器状态 | 收到事件后的操作 |
| --- | --- |
| 未开始 | 开始 |
| 进行中 | 暂停 |
| 已暂停 | 继续 |
| 已完成 | 重新开始 |

对话中修改为新时长会打开一个新 Page。语音触发仍需 AIUI Studio 和 Rokid Glasses 真机验证，状态为 `BLOCKED`；点头和触摸板仍需真机验证，同样为 `BLOCKED`。该示例不承诺后台计时、系统通知或持久化恢复。

以下是 2026-10-24 实际运行内置源码后截取的界面，依次通过预览器的 Enter 控件开始、暂停计时。保留原始 480 × 352 画布比例，点击可查看原图。

| 待开始 · `idle` | 计时中 · `running` | 已暂停 · `paused` |
| --- | --- | --- |
| ![Focus Timer 实际预览：10:00，開始按钮](docs/assets/focus-timer-preview/idle.jpg) | ![Focus Timer 实际预览：09:54，一時停止按钮](docs/assets/focus-timer-preview/running.jpg) | ![Focus Timer 实际预览：09:53，再開按钮](docs/assets/focus-timer-preview/paused.jpg) |

截图环境：AIX CLI `0.8.2`，浏览器实际加载 Ink `0.19.1`，默认紧凑视图（`_current`）；示例源码仍按 AIUI `0.17.0` 维护。截图来自浏览器预览，不是真机实拍，不替代 Studio、语音或物理眼镜验证。[完整预览画面与复现记录](docs/focus-timer-screenshots.md)

## 自动检查

Skill 会按项目实际能力组织检查，并区分本地证据与 Studio、真机证据：

| 检查范围 | 检查内容 |
| --- | --- |
| 工程与版本 | 项目结构、页面与资源完整性、目标版本兼容性 |
| 功能 | 正常流程、边界输入、失败恢复、生命周期 |
| UX | 实际操作界面，检查状态反馈、文案、焦点，以及触摸和语音路径 |
| AIX | 先探测实际支持的命令，再执行预览、打包和包内容检查 |
| 提交准备 | 核对文案、权限用途、源码与包信息、审核步骤和素材来源 |

生成预览 HTML 不等于界面成功运行，本地交互通过也不等于真机通过。没有执行条件的检查记录为 `BLOCKED`；材料准备完成不代表已上传或审核通过。

完整检查方法见 [UX 与能力测试](skills/rokid-aiui-agent/references/ux-and-capability-testing.md)和[提交准备指南](skills/rokid-aiui-agent/references/submission-preparation.md)。[最近一次独立生成验证](tests/evaluations/forward/08-fresh-agent-submission.md)记录了 0.19 Agent 的实际通过项、预览故障和待完成项目。

## 版本边界

新项目默认使用 AIUI `0.19.0`。已有工程明确指定的 `0.17.0`、`0.18.0` 等版本会保留；内置计时器和最小模板仍使用 `0.17.0`。

当前工具支持 0.19 项目结构检查和能力清单，但尚未注册该版本的能力 PASS 策略，因此逐能力验收仍为 `BLOCKED`。详情见 [AIUI 0.19 指南](skills/rokid-aiui-agent/references/aiui-0.19.md)和[官方 0.19.0 快速开始](https://open.rokid.com/aiui/guide/quickstart/intro?version=0.19.0&lang=en-US)。

## 仓库内容

按用途查找文件：

| 路径 | 用途 |
| --- | --- |
| [SKILL.md](skills/rokid-aiui-agent/SKILL.md) | Skill 入口与任务流程 |
| [references/](skills/rokid-aiui-agent/references/) | 按需读取的开发与验收参考 |
| [scripts/](skills/rokid-aiui-agent/scripts/) | 项目结构、能力和审计检查工具 |
| [assets/studio-importable-minimal/](skills/rokid-aiui-agent/assets/studio-importable-minimal/) | 可导入 Studio 的最小工程模板 |
| [assets/focus-timer-agent/](skills/rokid-aiui-agent/assets/focus-timer-agent/) | 唯一的产品化示例 Agent |
| [中文](docs/usage.zh-CN.md)、[English](docs/usage.en.md)、[日本語](docs/usage.ja.md) | 完整使用指南 |

## 深入指南

需要更多提示词、验证命令或排障步骤时，使用以下入口：

- [中文完整指南](docs/usage.zh-CN.md)：创建、修改、审查、调试和打包
- [Skill 入口](skills/rokid-aiui-agent/SKILL.md)：任务流程与交付要求
- [来源优先级](skills/rokid-aiui-agent/references/source-of-truth.md)：官方文档、实现和示例冲突时如何取舍

## 来源与许可证

开发依据为版本匹配的官方文档、实现和可运行示例，第三方材料单独标注。详细归属见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)，代码使用 [Apache License 2.0](LICENSE)。
