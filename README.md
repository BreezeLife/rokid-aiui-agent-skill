# ROKID AIUI Agent Skill

[![CI](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/BreezeLife/rokid-aiui-agent-skill/actions/workflows/ci.yml)

面向编码智能体的 ROKID AIUI 开发 Skill：从工程识别、`.ink` / WXML / WXSS 编写，到硬件输入、单绿色眼镜设计、AIX 预览与打包，再到真机验收，最终交付可被 AIUI Studio 直接导入的完整源码工程。

This repository is a compact, source-traceable development workflow—not a frozen copy of the AIUI manual.

## 为什么需要它

本 Skill 直接基于官方 `aiui-dev` 和官方 samples 的高价值规则，但不盲从已经落后的摘要。它会：

- 禁止从浏览器或微信小程序经验推断 AIUI API、组件、事件和 CSS 行为；
- 先确认设备、runtime、Page / Widget / Agent Worker，以及 `_current` / `_blank` 承载面；
- 显式处理官方资料内部的版本冲突，例如对话流交互、CSS animation、页面注册和视觉 token；
- 运行静态验证，按本机 `aix --help` 选择真实存在的命令；
- 把浏览器 preview、平台上传和真机验收视为不同证据层级。

## 输出契约

创建或实现类任务必须交付完整、可编辑的 AIUI 项目目录，而不是零散代码片段或只有 `.aix` 包。项目根至少包含 `AGENTS.md`、`app.json`、应用入口，以及 `app.json.pages` 声明的全部页面和引用资源。

- 本地导入：将交付目录本身选为 AIUI Studio 的“本地导入”文件夹。
- GitHub 导入：仓库根目录或明确给出的子目录必须就是 AIUI 项目根，并同时给出仓库 URL、分支/标签和导入子目录。
- 示例：本仓库的 [`skills/rokid-aiui-agent/assets/studio-importable-minimal`](skills/rokid-aiui-agent/assets/studio-importable-minimal) 按官方 GitHub 指定目录契约准备，并经过严格结构检查、真实 AIX 打包和浏览器预览。GitHub 导入坐标是仓库 `https://github.com/BreezeLife/rokid-aiui-agent-skill`、ref `main`、指定目录 `skills/rokid-aiui-agent/assets/studio-importable-minimal`。账号侧 Studio 导入仍是单独的人工验收门槛，不能由这些本地证据替代。

当工程和宿主都没有暴露目标版本时，本 Skill 明示假设并默认使用官网标记为稳定版的 AIUI `0.17.0`。Widget、Agent Worker 等 `0.18.0` 新能力只有在目标版本明确支持后才会生成，避免把预览版配置混进稳定版项目。

## 安装

使用通用 Skills CLI：

```bash
npx skills add BreezeLife/rokid-aiui-agent-skill --skill rokid-aiui-agent
```

或使用支持 Agent Skills 的 GitHub CLI，并显式指定技能名：

```bash
gh skill install BreezeLife/rokid-aiui-agent-skill rokid-aiui-agent --agent codex --scope user
```

安装前请审阅 `skills/rokid-aiui-agent/SKILL.md` 和脚本；Agent Skill 会影响编码智能体的行为。

## 使用

显式调用示例：

```text
Use $rokid-aiui-agent to build a ROKID AIUI weather agent for Rokid Glasses 2,
validate the project, preview it when supported, and package an AIX artifact.
```

也可直接提出 AIUI 开发、代码审查、调试、AIX 打包或真机验收需求；支持隐式触发的 Agent 会根据 Skill 描述加载它。

## 使用 Skill 生成的 Agent

[examples/next-step-agent](examples/next-step-agent/) 是使用本 Skill 生成的首个完整、可编辑、稳定版 AIUI `0.17.0` 项目。它将 `goal` 收敛为一个 `nextStep`，并在 Page 内呈现 `empty`、`error`、`ready`、`active`、`done` 五种状态；有效行动可依次开始、完成和重新开始。

该项目不使用网络、设备权限、持久化存储、计时器、Widget 或 Agent Worker。`_current` 和 `_blank` 只调整信息密度，不改变业务状态。

AIUI Studio GitHub 导入坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: examples/next-step-agent
```

自动验证不能替代账号侧 AIUI Studio 导入和 Rokid Glasses 真机验收。

### Japanese Focus Timer Agent

[examples/focus-timer-agent](examples/focus-timer-agent/) 是面向 Rokid Glasses 的日文专注计时器，同样保持稳定版 AIUI `0.17.0`、Page-only 和零权限边界。Agent 从对话中提取 1～3600 的整数 `durationSeconds` 与可选 `label`；页面提供 `idle`、`running`、`paused`、`finished`、`error`，以及开始、暂停、继续、重新开始和重置。页面启用 World Awareness，显示期间将点头 `nod` 映射为当前主要操作；不使用眼球追踪，触摸板单击通过页面级 `Enter` / `GlobalHook` 执行相同操作，按钮仍提供 `bindtap`、`bindfocus` 和 `bindblur`。

未指定时间时默认使用 10 分钟（`600` 秒）。语音设置或修改时间时，Agent 必须把分钟、小时换算为整数秒并重新调用 Page，例如“专注 25 分钟”传入 `{ "durationSeconds": 1500 }`。AIUI 0.17 的 `onLoad(query)` 对每个 Page 实例只执行一次，因此新的时间会显示在新 Page 中，不会原地改写对话里旧的计时卡片。

运行期间以绝对截止时间和 `Date.now()` 计算真实剩余时间，刷新定时器不逐秒修改业务时间。页面隐藏时停止刷新，重新显示时校准，卸载时清理定时器。它不承诺后台持续运行、系统闹钟、通知或持久化恢复。

AIUI Studio GitHub 导入坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: examples/focus-timer-agent
```

页面文案与 Agent 提示词为日文；字段名和状态名保留英文技术契约。账号登录后的 Studio 导入与 Rokid Glasses 真机操作仍需人工验收。

### SceneQuest / セイチ｜SEICHI

[examples/scenequest-agent](examples/scenequest-agent/) 是日文优先的动漫圣地识别 MVP，也是完整、可编辑的稳定版 AIUI `0.17.0` Page-only 项目。首版严格限定为 12 个大阪精选圣地；Agent 只在有来源记录的目录中结合地点与视觉特征判断，并将结果收敛为 `matched`、`uncertain`、`no_match`、`invalid` 四种状态。它不声称覆盖全日本，也不会把目录未命中解释为某地点从未出现在其他作品中。

摄像头画面与 GPS / 当前地点由 Agent host 提供，Page 不直接采集摄像头或 GPS；缺少某类宿主上下文时，Agent 必须降级为仍有证据支持的回答或安全恢复状态。项目只携带来源记录、场景说明、可观察构图特征和拍摄建议，不随项目分发动漫截图，也不实现后台地理围栏或自动弹出。

仅当图像、位置、地点/作品约束和可用问题文本全部不可用时才进入 `invalid`。缺图时只能返回预先核实的拍摄位或请求补拍，不做动态视觉微调；缺位置时不输出距离，也不声称按距离排序。`_blank` 的附近点选中后，方向提示直接在该行展开，焦点移入或移出不会清除选中。

AIUI Studio GitHub 导入坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
Directory: examples/scenequest-agent
```

本地测试、严格验证、AIX 打包/清单与静态 preview 只能证明源码结构和本地工具链行为；尚未验证 AIUI Studio 导入和 Rokid Glasses 真机行为。宿主摄像头/GPS 传递及权限授权、拒绝与撤销，日文语音与 Page 协同，`_current` / `_blank` 切换、焦点、光学可读性和运动场景中的视觉指引均保留为人工门槛。

## 开发闭环

1. 确定 AIUI Studio 将导入的准确目录，读取其中的项目指引、`app.json`、入口、页面和现有脚本。
2. 明确 runtime、设备、承载面、输入方式和交付阶段；无法识别版本时采用并声明 `0.17.0` 稳定基线。
3. 只加载与当前任务有关的 `references/` 指南，并按来源优先级消解冲突。
4. 小步实现，保留既有 authoring mode，运行项目静态验证。
5. 探测 AIX 能力；支持时执行 preview，并用 pack + list 检查产物。
6. 对按键、焦点、语音、手势、光学显示、弱网和返回流进行真机验证。

物理眼镜和 ROKID 平台凭据不属于本仓库，CI 不会伪造这两类证据。

## 本地验证

```bash
python3 -m pip install --only-binary=:all: -r requirements-dev.txt
python3 -m unittest discover -s tests -v
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py tests/fixtures/valid-minimal --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py skills/rokid-aiui-agent/assets/studio-importable-minimal --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/next-step-agent --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/focus-timer-agent --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py examples/scenequest-agent --target-version 0.17.0 --strict
python3 skills/rokid-aiui-agent/scripts/verify_references.py .
npm ci --ignore-scripts --no-audit --no-fund
AIX_BIN="$PWD/node_modules/.bin/aix"
export AIX_BIN
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh tests/fixtures/valid-minimal
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh skills/rokid-aiui-agent/assets/studio-importable-minimal
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/next-step-agent
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/focus-timer-agent
bash skills/rokid-aiui-agent/scripts/smoke_aix.sh examples/scenequest-agent
preview_dir="$(mktemp -d "${TMPDIR:-/tmp}/next-step-preview.XXXXXX")"
preview_html="$preview_dir/next-step-agent.html"
"$AIX_BIN" preview examples/next-step-agent --html-out "$preview_html"
test -s "$preview_html"
grep -Fq 'pages/index/index.ink' "$preview_html"
focus_preview_dir="$(mktemp -d "${TMPDIR:-/tmp}/focus-timer-preview.XXXXXX")"
focus_preview_html="$focus_preview_dir/focus-timer-agent.html"
"$AIX_BIN" preview examples/focus-timer-agent --html-out "$focus_preview_html"
test -s "$focus_preview_html"
grep -Fq 'pages/index/index.ink' "$focus_preview_html"
scenequest_preview_dir="$(mktemp -d "${TMPDIR:-/tmp}/scenequest-preview.XXXXXX")"
scenequest_preview_html="$scenequest_preview_dir/scenequest-agent.html"
"$AIX_BIN" preview examples/scenequest-agent --html-out "$scenequest_preview_html"
test -s "$scenequest_preview_html"
grep -Fq 'pages/index/index.ink' "$scenequest_preview_html"
```

上述流程通过 lockfile 安装 `@yodaos-pkg/aix-cli@0.8.2`，再用 `AIX_BIN` 指定同一个可执行文件完成打包和预览。未设置 `AIX_BIN` 时，AIX smoke 默认使用已安装的 `aix`；找不到时通过 pnpm 或 npx 调用已验证的发布版。也可同时设置 `AIX_FORCE_PACKAGE=1` 与 `AIX_PACKAGE` 强制绕过 `PATH` 中的同名 CLI。脚本只打包到自身临时目录，不上传或部署。

## 目录

- `skills/rokid-aiui-agent/SKILL.md`：任务路由、证据原则和验证门槛。
- `skills/rokid-aiui-agent/references/`：工程、`.ink`、交互设计、runtime、AIX 与发布指南。
- `skills/rokid-aiui-agent/scripts/validate_aiui_project.py`：零依赖结构检查器，默认以 `0.17.0` 为目标，支持 `--target-version` / `--strict` / `--json`。
- `skills/rokid-aiui-agent/scripts/smoke_aix.sh`：真实 AIX pack + list 冒烟流程。
- `skills/rokid-aiui-agent/assets/studio-importable-minimal/`：按 AIUI Studio 本地/GitHub 指定目录结构准备的最小 `0.17.0` 兼容工程。
- `examples/scenequest-agent/`：日文优先、12 个大阪精选圣地、四状态的稳定版 `0.17.0` Page-only SceneQuest 示例。
- `tests/`：单元测试、正反 fixtures 和前后行为评估。
- `PROJECT.md` / `MEMORY.md` / `TASKS.md` / `WORKLOG.md`：跨设备项目连续性。

## 来源与边界

权威顺序、固定提交、已知冲突和第三方边界见 [source-of-truth](skills/rokid-aiui-agent/references/source-of-truth.md) 与 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。本项目把用户指定的 [AIUI 0.17 快速入门](https://js.rokid.com/AIUI/guide/quickstart/quickstart?version=0.17.0&lang=zh-CN)、[项目结构](https://js.rokid.com/AIUI/guide/structure?version=0.17.0&lang=zh-CN)、[智能体框架](https://js.rokid.com/AIUI/guide/framework?version=0.17.0&lang=zh-CN)和[基础能力](https://js.rokid.com/AIUI/guide/basic?version=0.17.0&lang=zh-CN)作为稳定版入口；详细 API 仍须与选定版本、实现和可运行 samples 对齐。本仓库不会保证未经真机验证的设备行为。

## 许可证

本仓库以 [Apache License 2.0](LICENSE) 发布。外部资料的归属和非再分发说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
