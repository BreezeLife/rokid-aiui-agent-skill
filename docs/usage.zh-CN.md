[简体中文](usage.zh-CN.md) | [English](usage.en.md) | [日本語](usage.ja.md) | [项目首页](../README.md)

# ROKID AIUI Agent Skill 使用说明

<!-- usage:scope -->
## 1. 它解决什么问题

`rokid-aiui-agent` 用于让支持 Agent Skills 的编码智能体创建、修改、审查、调试和验证 ROKID AIUI Agent 项目。它的默认实现交付物是一个完整、可编辑、可直接选择为 AIUI Studio 导入根的源码目录，而不是零散代码或只有 `.aix` 的压缩包。

一个创建或实现任务通常会得到：

- 含 `AGENTS.md`、`app.json`、应用入口、全部已声明 Page 和资源的 AIUI 源码工程；
- 用于闭合产品能力声明的 `aiui-audit-claims.json`；
- 与准确导入根绑定的源码指纹、能力清单、严格结构验证和业务逻辑测试结果；
- `## Project UX evidence matrix` 与 `## Per-capability matrix` 两张强制证据表；
- 当前 AIX CLI 确实支持时的 preview、pack 和 list 结果；
- 本地路径，或 GitHub 仓库、ref 与导入子目录三项坐标；
- 未执行的 AIUI Studio、物理眼镜或签名证据门槛，明确标记为 `BLOCKED`。

每个可检查的导入根都必须包含闭合的 `aiui-audit-claims.json`。没有额外产品能力声明时，最小 schema 1 文件是：

```json
{
  "schemaVersion": 1,
  "scopeClosed": true,
  "claims": []
}
```

只有真实存在但不能从源码可靠推导的产品能力才放入 `claims`。每条非空声明仍需独立的能力 gate 和证据；`scopeClosed: true` 只表示声明清单闭合，不表示能力已通过测试。

如果工程和宿主都没有给出目标版本，Skill 会说明假设并采用稳定基线 AIUI `0.17.0`。Widget、Agent Worker 等 `0.18` 能力只有在目标明确支持时才应生成。

<!-- usage:install -->
## 2. 安装

在支持 Agent Skills 的编码环境中，使用通用 Skills CLI：

```bash
npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent
```

如果本机 GitHub CLI 提供 `gh skill` 命令，也可以使用：

```bash
gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
```

安装前建议检查仓库中的 [`SKILL.md`](../skills/rokid-aiui-agent/SKILL.md) 与脚本。更新时重新执行所选安装命令，并核对安装工具显示的来源和 revision；不要把重新安装本身当成项目验证结果。

<!-- usage:invoke -->
## 3. 怎么调用

在编码智能体的对话中，把 `$rokid-aiui-agent` 写进请求即可显式调用。显式调用最容易复现：

```text
请使用 $rokid-aiui-agent 创建一个可导入 AIUI Studio 的完整 ROKID AIUI 项目，并完成本地验证与 UX/能力审查。
```

支持隐式发现的宿主也可能在你直接提出 AIUI 开发、审查、调试、AIX 预览或打包需求时自动加载它。为减少路由歧义，发布相关任务建议始终显式写出 `$rokid-aiui-agent`。

请求中最好提供：目标目录或现有导入根、AIUI runtime、眼镜型号、`_current` / `_blank` 承载面、输入方式、权限、界面语言和期望交付位置。信息缺失时，Skill 应先检查工程；仍无法确认的内容必须保留为假设、`UNKNOWN` 或 `BLOCKED`，不能猜测 API。

<!-- usage:prompts -->
## 4. 可直接复制的调用示例

<!-- prompt:new-project -->
### 从零创建 AIUI Agent

```text
请使用 $rokid-aiui-agent 在独立目录 /absolute/path/to/weather-agent 中创建一个完整的 ROKID AIUI 天气 Agent。
目标是 AIUI 0.17.0，同时支持对话内 _current 与全屏 _blank Page。先核对版本匹配的官方来源，
不要从浏览器或微信小程序猜 API。交付可直接导入 AIUI Studio 的完整源码目录，加入确定性测试、
严格项目验证、能力盘点、AIX preview/pack/list（仅在 CLI 帮助确认支持时），并输出强制的
Project UX evidence matrix 和 Per-capability matrix。没有实际执行的 Studio 与真机项保持 BLOCKED。
```

<!-- prompt:timer -->
### 开发一个计时器

```text
请使用 $rokid-aiui-agent 创建一个面向 Rokid Glasses 的专注计时器，输出到独立目录 /absolute/path/to/my-focus-timer。
采用 AIUI 0.17.0 Page-only 工程，目录必须可直接导入 AIUI Studio。接收 1～3600 的整数
durationSeconds 和可选 label，缺省为 600 秒；实现 idle、running、paused、finished、error。
用绝对截止时间计算剩余时间，在 hide/show 时重新校准，在 unload 时清理定时器。
为 _current 和 _blank 设计合适密度，保留按钮点击和焦点路径；点头或硬件键只有在版本来源确认后才加入，
并始终提供非传感器 fallback。不要承诺后台计时、系统闹钟、通知或持久化恢复。

运行确定性逻辑测试、严格验证、能力盘点，以及 AIX 支持的 preview/pack/list。
输出完整 Project UX evidence matrix 与 Per-capability matrix；未实际执行的 Studio 和物理眼镜门槛必须保持 BLOCKED，
最后报告准确的本地导入根或 GitHub Repository、Ref、Directory。
```

<!-- prompt:review -->
### 审查已有项目

```text
请使用 $rokid-aiui-agent 审查 /absolute/path/to/aiui-project，但不要修改源码。
确认准确的 AIUI Studio 导入根、目标版本、Page/Widget/Agent Worker、_current/_blank、全部输入和权限。
运行源码指纹、能力盘点和严格验证；只运行仓库已有且安全的测试。按严重程度列出问题，
并生成 Project UX evidence matrix 与 Per-capability matrix。没有当前 revision 的执行证据时不得写 PASS；
缺少 Studio 登录或物理眼镜时写 BLOCKED，不要用 N/A 代替。
```

<!-- prompt:debug -->
### 修复或调试项目

```text
请使用 $rokid-aiui-agent 修复当前 AIUI 工程中“触摸板单击没有触发主操作”的问题。
先复现并定位 Page 事件、host focus、element focus、默认事件和 fallback 路径，再用回归测试驱动最小修复。
保留当前 authoring mode 和目标版本，不要发明事件名。修复后重新计算源码指纹和能力清单，
执行严格验证及可用的 AIX 流程，并刷新 Project UX evidence matrix 与 Per-capability matrix；
旧 revision 的证据不得复用。
```

<!-- prompt:verify-package -->
### 验证、预览和打包

```text
请使用 $rokid-aiui-agent 验证 skills/rokid-aiui-agent/assets/focus-timer-agent。先运行 scripts/fingerprint_aiui_project.py，
再运行 scripts/inventory_aiui_capabilities.py 和 scripts/validate_aiui_project.py 严格项目验证器，
再运行 deterministic tests（确定性测试），然后探测当前 aix --help；
对 AIX 只执行帮助中实际公开的 preview、pack 和 list，不上传、不部署。
确认 .aix 清单不含 .git 或 .aiui-evidence，并报告执行命令、退出码、产物路径和当前源码 revision。
同时完成 Project UX evidence matrix 与 Per-capability matrix，并用 scripts/validate_aiui_audit.py 验证最终审计；
AIX 浏览器预览不能替代 AIUI Studio 或真机证据。
```

<!-- usage:verify -->
## 5. 如何检查交付结果

先确认所报告的导入根本身直接包含 `app.json`，而不是它的父仓库。以下命令以本仓库中的计时器示例为可运行参考；在自有项目中替换 `AIUI_IMPORT_ROOT` 和目标版本：

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt

AIUI_REPOSITORY_ROOT="$PWD"
AIUI_IMPORT_ROOT="skills/rokid-aiui-agent/assets/focus-timer-agent"

python3 skills/rokid-aiui-agent/scripts/fingerprint_aiui_project.py \
  "$AIUI_IMPORT_ROOT" --repository-root "$AIUI_REPOSITORY_ROOT"
python3 skills/rokid-aiui-agent/scripts/inventory_aiui_capabilities.py \
  "$AIUI_IMPORT_ROOT" --target-version 0.17.0 --repository-root "$AIUI_REPOSITORY_ROOT"
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  "$AIUI_IMPORT_ROOT" --target-version 0.17.0 --repository-root "$AIUI_REPOSITORY_ROOT" --strict
python3 -m unittest discover -s tests -v
```

本仓库 lockfile 固定 `@yodaos-pkg/aix-cli@0.8.2`，要求 Node.js `>=20`。先确认当前 Node/npm，再安装锁定依赖；随后检查 `--help`，只在其中明确支持时运行 preview、pack 和 list。本仓库脚本会执行 pack/list 冒烟流程：

```bash
node --version
npm --version
npm ci --ignore-scripts --no-audit --no-fund

AIX_BIN="$PWD/node_modules/.bin/aix"
AIUI_PREVIEW_DIR="$(mktemp -d "${TMPDIR:-/tmp}/focus-timer-preview.XXXXXX")"
AIUI_PREVIEW_HTML="$AIUI_PREVIEW_DIR/index.html"
export AIX_BIN
"$AIX_BIN" --help
"$AIX_BIN" preview "$AIUI_IMPORT_ROOT" --html-out "$AIUI_PREVIEW_HTML"
test -s "$AIUI_PREVIEW_HTML"
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh skills/rokid-aiui-agent/assets/focus-timer-agent
```

最终审计验证需要当前 revision 的审计报告、内容寻址证据，以及位于仓库外的绝对 trust policy：

```bash
python3 skills/rokid-aiui-agent/scripts/validate_aiui_audit.py AUDIT.md \
  --repository-root /absolute/path/to/repository \
  --import-root skills/rokid-aiui-agent/assets/focus-timer-agent \
  --trust-policy /absolute/path/outside/repository/trust-policy.json
```

审计验证器把报告和记录的 `argv` 当作执行来源数据校验，但从不执行其中记录的命令。只有当前环境实际采集并由所需权威签名的结果才能成为执行证据。

审计退出码含义固定：

| 退出码 | 稳定语义 | 含义 |
| --- | --- | --- |
| `0` | `release-ready-pass` | 结构有效，并且恰好是 `Final status: PASS` 与 `Release-ready: YES` |
| `2` | `valid-not-release-ready` | 结构有效，但最终结果仍为 `FAIL` 或 `BLOCKED` |
| `1` | `invalid-or-untrusted` | 报告无效、过期、被篡改或不受信任 |

<!-- usage:audit -->
## 6. 强制 UX 与能力验收

每次创建、实现、修改或审查都必须产出两张独立表，完整格式以 [`ux-and-capability-testing.md`](../skills/rokid-aiui-agent/references/ux-and-capability-testing.md) 为准：

- `## Project UX evidence matrix`：逐项覆盖 target、状态、边界文本、host/element focus、每条输入、恢复、生命周期、单绿色视觉、真实光学环境和运动/性能；
- `## Per-capability matrix`：逐项覆盖每个 API、组件、事件、route、声明、权限、fallback 与 cleanup，并绑定固定版本官方来源及扫描器 gate。

结果只能是：

- `PASS`：该行要求的每个证据层都已对当前源码执行并支持结论；
- `FAIL`：已执行证据明确反驳验收条件；
- `BLOCKED`：所需环境、权限或当前 revision 证据未提供；
- `N/A`：只有源码范围与闭合产品范围共同证明条件不适用时才能使用，缺设备或缺时间不是 `N/A`。

六层证据互不替代：`SOURCE` 证明版本来源，`STATIC` 证明结构与绑定，`LOGIC` 证明确定性逻辑，`AIX` 证明本机 CLI 与基础浏览器渲染，`STUDIO` 证明已登录导入和 Web simulation，`DEVICE` 证明指定物理眼镜上的输入、光学和性能。执行证据与 AIX 捕获需要 `RUNNER` 权威；Studio、物理眼镜和范围排除分别还需要 `STUDIO`、`DEVICE`、`SCOPE` 权威。缺少相应签名时保持 `BLOCKED`。

<!-- usage:import -->
## 7. 导入 AIUI Studio

本地导入时，应选择直接含 `app.json` 的 AIUI 项目目录。不要选择只在更深层才包含工程的父仓库。

GitHub 导入时必须同时给出 Repository、Ref 和 Directory。计时器示例的坐标是：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: skills/rokid-aiui-agent/assets/focus-timer-agent
```

AIUI Studio 账号侧导入是一次独立执行。即使源码严格验证、AIX preview 和 pack 都成功，未实际导入时仍只能报告“源码已准备好供 AIUI Studio 导入”，Studio gate 保持 `BLOCKED`，不能报告“Studio 已验证”。

<!-- usage:completion -->
## 8. 什么才算完成

“源码交付完成”表示完整源码工程、导入坐标和本地验证结果都已提供；它不自动等于“发布就绪”。只有审计验证器对当前指纹和受信证据返回 `0`，并且没有适用的 `FAIL` / `BLOCKED`，才可以写 `Release-ready: YES`。

常见的正确阶段性结论是：“严格结构验证、逻辑测试与 AIX pack/list 已通过；AIUI Studio 导入和物理 Rokid Glasses UX 仍为 `BLOCKED`。”

<!-- usage:examples -->
## 9. 可导入示例

- [`skills/rokid-aiui-agent/assets/studio-importable-minimal`](../skills/rokid-aiui-agent/assets/studio-importable-minimal/)：最小稳定版 Page 工程；
- [`skills/rokid-aiui-agent/assets/focus-timer-agent`](../skills/rokid-aiui-agent/assets/focus-timer-agent/)：日文专注计时器；

两个目录本身都是导入根；其中计时器是本仓库唯一的产品化示例 Agent。仓库内的自动测试不替代你自己的 AIUI Studio 和目标设备验收。

<!-- usage:troubleshooting -->
## 10. 常见问题

- **Skill 没有触发**：在请求开头显式写“请使用 `$rokid-aiui-agent`”。
- **Studio 看不到工程**：确认所选目录直接包含 `app.json` 和已声明页面，不要选择父目录。
- **AIX 命令不存在**：先运行选定可执行文件的 `--help`，只使用当前版本实际列出的命令；不要照搬其他分支或旧网站命令。
- **preview 成功但眼镜不工作**：preview 只是 `AIX` 层证据，不能证明 Studio host、传感器、硬件键、焦点、权限或光学显示。
- **缺少眼镜时能否写 N/A**：不能。适用的真机项应为 `BLOCKED`。
- **pack 是否等于发布**：不等于。pack 只生成和检查 `.aix`；上传、平台审核、部署与真机验收属于后续流程。
- **何时能用 Widget / Agent Worker**：只有目标 runtime 明确支持 `0.18` 对应能力并完成该版本来源与证据策略时。
