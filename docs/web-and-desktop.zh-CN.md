# 在网页和桌面 App 中使用 ROKID AIUI Skill

[返回 README](../README.md) · [CLI / IDE 安装流程](../README.md#路线-2用-codex-等-vibe-coding-工具开发)

先选你使用的工具，再安装 Skill。网页端无需安装桌面 App；桌面端需要先安装 App，再添加 `rokid-aiui-agent`。本指南依据 2026-10-23 的官方文档，包含无需手动执行终端命令的操作方式。

- [Codex 桌面 App](#codex-desktop)：在本机项目中开发
- [Claude 桌面 App](#claude-desktop)：通过 Code 编辑本机项目，或在 Chat 使用账号 Skill
- [Codex 网页端](#codex-web)：在云端仓库中开发
- [Claude 网页端](#claude-web)：上传 Skill ZIP，生成并下载源码
- [准备完整 Skill 文件夹和 ZIP](#skill-zip)：供手动安装或网页上传

<a id="codex-desktop"></a>

## Codex 桌面 App：下载、安装、添加 Skill

当前官方入口是 ChatGPT 桌面 App 内的 Codex。按[官方安装页](https://learn.chatgpt.com/docs/quickstart?setup=app)选择系统对应的下载，完成安装并登录，然后在产品选择器中切换到 **Codex**。打开一个独立的开发目录，用于存放你的 AIUI 项目。

在 Codex 的聊天输入框发送以下安装请求，无需先安装 Codex CLI：

```text
请使用 $skill-installer，从以下 GitHub 目录安装 rokid-aiui-agent：
https://github.com/BreezeLife/rokid-aiui-agent-skill/tree/main/skills/rokid-aiui-agent
安装完整 Skill 目录，保留 references、scripts、assets 和 agents。
完成后报告安装路径和读取到的默认 AIUI 版本。
```

安装完成后，在侧栏 **Skills** 中确认技能存在；若列表未更新，重新打开会话或重启 App。再发送“使用 rokid-aiui-agent Skill”，附上 [README 的开发需求](../README.md#路线-2用-codex-等-vibe-coding-工具开发)。内置安装器和本地发现方式见 [OpenAI Skills 文档](https://learn.chatgpt.com/docs/build-skills)。

<a id="claude-desktop"></a>

## Claude 桌面 App：下载、安装、添加 Skill

从 [Claude 下载页](https://claude.com/download)下载安装包，完成安装并登录。macOS、Windows 和 Linux 的要求见[官方安装说明](https://support.claude.com/en/articles/10065433-install-claude-desktop)。

要让 Claude 编辑本机工程，使用 **Code** 标签，选择 **Local → Open folder…** 打开独立项目目录。桌面已包含 Claude Code，无需为了使用 Code 标签另装 CLI 或 Node.js；Code 需要支持它的付费计划。AIUI 检查所需的 Python、Node.js、AIX 等开发依赖仍需按任务准备。[官方 Code 入门](https://code.claude.com/docs/en/desktop-quickstart)

无需终端的本地安装步骤：

1. 按[下载说明](#skill-zip)取得完整 `rokid-aiui-agent` 文件夹。
2. 在文件管理器中，将它复制到个人 Skills 目录。macOS / Linux 为 `~/.claude/skills/rokid-aiui-agent/`，Windows 本地会话为 `%USERPROFILE%\.claude\skills\rokid-aiui-agent\`；父目录不存在时创建它。
3. 确认目标位置直接包含 `SKILL.md`，同时保留 `references/`、`scripts/`、`assets/` 和 `agents/`。不要再多套一层同名文件夹。
4. 新建 Code 会话，输入 `/`，找到 `rokid-aiui-agent`，或输入 `/rokid-aiui-agent` 后附上开发需求。

macOS 可在 Finder 的“前往文件夹”中输入 `~/.claude/skills/`；Windows 可把 `%USERPROFILE%\.claude\skills\` 粘贴到资源管理器地址栏。个人目录让多个本机项目共用 Skill；官方也支持项目级 `.claude/skills/`。[Skills 位置与作用域](https://code.claude.com/docs/en/skills#choose-where-skills-load)

如果选择 WSL 环境，使用该 Linux 发行版内的 `~/.claude/skills/`，不要把 Windows 本地目录当成 WSL 的安装位置。[WSL 说明](https://code.claude.com/docs/en/desktop-wsl)

如果使用桌面 **Chat**，按下面的 [Claude 网页上传流程](#claude-web)添加账号 Skill。Cowork 和云端会话使用账号启用的 Skills，本机个人目录并不是它们的安装位置。新版 Claude Code 在使用同一 Claude 账号登录时支持账号 Skill 单向同步，不能据此认为本地文件的修改会上传回账号；具体条件见[同步说明](https://code.claude.com/docs/en/skills#skills-synced-from-claudeai)。

<a id="codex-web"></a>

## Codex 网页端：让云端任务读取 Skill

从 [ChatGPT 网页](https://chatgpt.com/)进入 **Work in → Cloud → Select environment → Create environment**，连接并选择你自己的 AIUI 应用仓库。准备环境、核对配置后发布，再启动任务。入口与操作见[官方云环境指南](https://learn.chatgpt.com/docs/environments/cloud-environments)。

本仓库建议把 Skill 放在应用仓库根目录的 `.agents/skills/rokid-aiui-agent/`，把生成的 AIUI 源码放在 `app/`。这是应用仓库的布局，不是在本 Skill 仓库里增加产品 Agent：

```text
your-aiui-project/
├── .agents/
│   └── skills/
│       └── rokid-aiui-agent/
│           ├── SKILL.md
│           ├── references/
│           ├── scripts/
│           ├── assets/
│           └── agents/
└── app/
    ├── app.json
    ├── app.js
    └── pages/
```

不熟悉终端时，可以在云环境准备对话或已有云端编码任务中请求：

```text
请从 BreezeLife/rokid-aiui-agent-skill 的 main 分支取得
skills/rokid-aiui-agent 完整目录，放到本应用仓库的
.agents/skills/rokid-aiui-agent/，保留全部参考、脚本和资源。
检查 SKILL.md 默认目标为 AIUI 0.19.0，并列出实际安装路径。
生成的 AIUI 工程使用 app/，不要把 Skill 文件混入 app/。
```

检查安装结果后，将 `.agents/skills/rokid-aiui-agent/` 提交并推送到应用仓库的目标分支，更新并发布云环境，再新建任务调用 Skill。复用 README 开发提示词时，把本机绝对路径换成云端实际工作区中的 `app/` 路径。完成后下载完整源码或查看仓库变更，Studio 只导入 `app/`。

Codex Cloud 能读取仓库中的 Skills，本机个人 Skills 不会自动同步。当前 Codex Cloud 环境尚不支持浏览器与 Computer Use，界面实操需要转到具备条件的桌面环境。普通 ChatGPT 网页对话中的附件也不等于安装了本地 Skill；官方对网页 Chat / Work 的分发方式是插件，本仓库目前提供的是独立 Skill。[云端限制](https://learn.chatgpt.com/docs/environments/cloud-environments#current-limitations)、[Skill 与插件范围](https://learn.chatgpt.com/docs/build-skills)

<a id="claude-web"></a>

## Claude 网页端：上传并启用 Skill

使用 [Claude 网页](https://claude.ai/)或桌面 Chat 时，通过账号设置上传完整 Skill ZIP：

1. 按[下一节](#skill-zip)准备 `rokid-aiui-agent.zip`。
2. 在 **Settings → Capabilities** 开启 **Code execution and file creation**。Team / Enterprise 还需要组织策略允许 Skills 和代码执行。
3. 打开 **Customize → Skills → + → + Create skill → Upload a skill**，上传 ZIP。
4. 在技能列表启用 `rokid-aiui-agent`，新建聊天，明确要求使用这个 Skill。

菜单路径和账号条件见 [Claude 官方 Skills 使用说明](https://support.claude.com/en/articles/12512180-use-skills-in-claude)。在普通聊天中，用文字指定 Skill，无需照抄 Codex 的 `$` 或 Claude Code 的 `/` 调用语法：

```text
请使用已启用的 rokid-aiui-agent Skill。
先读取 SKILL.md 及相关参考，创建 AIUI 0.19.0 专注计时器。
支持语音设置时长，以及开始、暂停、继续、重置，覆盖 _current 和 _blank。
在本次代码执行环境中建立独立 app/ 目录，包含全部源码、页面和资源。
检查核心功能、边界输入、异常恢复、生命周期、焦点及触摸和语音交互的 UX。
交付可下载的完整源码 ZIP、实际检查结果、项目级 UX 表和逐能力表。
在 app/ 之外准备 Agent 介绍、调用示例、权限用途和审核材料清单。
AIX pack/list 与源码指纹校验成功时，在 app/ 之外另交付 .aix 包。
如果环境无法运行 AIX、浏览器、Studio 或真机检查，明确标为 BLOCKED。
```

可直接替换提示词中的产品需求。云端任务的输出不是你电脑上的目录：下载源码 ZIP 并解压后，选择含 `app.json` 的目录导入 AIUI Studio。源码 ZIP、Skill ZIP 和 `.aix` 包用途不同。

<a id="skill-zip"></a>

## 准备完整 Skill 文件夹和 ZIP

以下方式不需要命令行：

1. 打开[本仓库首页](https://github.com/BreezeLife/rokid-aiui-agent-skill)，选择 **Code → Download ZIP**，下载并解压仓库。
2. 在解压目录内打开 `skills/`，找到 `rokid-aiui-agent/`。本地安装时复制这个完整文件夹。
3. 网页上传时，只压缩这个文件夹，生成 `rokid-aiui-agent.zip`；不上传整个仓库 ZIP，也不只上传 `SKILL.md`。
4. 打开 ZIP 检查顶层结构，保留全部真实文件，排除 `.DS_Store`、`__MACOSX` 等系统附加文件。

正确的 ZIP 目录结构如下：

```text
rokid-aiui-agent.zip
└── rokid-aiui-agent/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

其中参考资料、验证脚本和示例资源都是本 Skill 的组成部分。Claude 网页文档要求 `description` 不超过 200 字符；本仓库已采用符合该限制的简介。[官方 ZIP 与元数据要求](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

## 安装后确认什么

无论使用哪种入口，先让智能体报告已读取的 `SKILL.md` 路径、目标 AIUI 版本和可访问的参考目录，再开始创建项目。版本默认应为 `0.19.0`；项目已有明确版本时保持原目标。

本指南经过官方文档与本地包结构核对，未代替用户在各账号中安装或上传测试。安装成功只代表 Skill 可加载；功能、UX、AIX、Studio 和真机结果仍按[验证要求](../README.md#自动检查)分别记录，不能把缺少执行条件的项目记为通过。
