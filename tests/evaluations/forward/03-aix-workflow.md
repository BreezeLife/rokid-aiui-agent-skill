# Forward Evaluation Capture

Scenario: `03-aix-workflow` — Released AIX Workflow
Conditions: Forward run with the repository `SKILL.md`; only AIX, project anatomy, source-of-truth, and release-gate references loaded.
Captured: 2026-09-07 22:19 CST
Post-capture relocation: the response below is preserved verbatim; its capture-time `scripts/validate_aiui_project.py` path is now `skills/rokid-aiui-agent/scripts/validate_aiui_project.py`.

---

不能把你约定的四个 AIX 命令直接交给团队执行：已核验的已发布 AIX npm CLI 没有公布 `create`、`dev`、`build` 或 `deploy` 子命令。下面给出功能等价、可复制且不会假装已经部署成功的最快路径。

你没有指定运行时，我先按稳定的 **AIUI 0.17.0** 做兼容目标。这里固定使用已核验的 npm 发布版 `@yodaos-pkg/aix-cli@0.8.2`；它要求 Node 20+。该 npm 发布版、仓库 `main`（当时清单为 0.9.0）、Rust 原生 `crates/aix-cli`/crate 发布以及旧文档站是不同证据通道：后几者出现的命令不能自动算作当前 npm CLI 已发布能力。最终以本次实际选中的可执行文件的根级 `--help` 为准。[0.8.2 npm CLI 清单](https://github.com/yodaos-project/aix/blob/19e6133f1984ee4455e6de9167b582864b528252/packages/cli/package.json)；[仓库 main 快照清单](https://github.com/yodaos-project/aix/blob/8e5f5b1ba60691291f99d14ea9516995f2af55e4/packages/cli/package.json)

### 1. 用官方 AIUI 初始化器创建源码工程

在这个 Skill 仓库根目录执行。初始化后先检查实际文件和 `package.json.scripts`；即使初始化器打印了提示，也不要假定存在 `npm start`。

```bash
set -euo pipefail

ROKID_SKILL_ROOT="$PWD"
AIUI_SOURCE_DIR="$ROKID_SKILL_ROOT/my-agent"
test ! -e "$AIUI_SOURCE_DIR" || {
  echo "目标目录已存在，停止以免覆盖：$AIUI_SOURCE_DIR" >&2
  exit 1
}

node --version
node - <<'NODE'
const major = Number(process.versions.node.split('.')[0]);
if (major < 20) {
  throw new Error(`AIX npm CLI 需要 Node >=20；当前为 ${process.version}`);
}
NODE

npm create @yodaos-pkg/aiui-agent@latest my-agent

cd "$AIUI_SOURCE_DIR"
find . -type f -print | sort

node - <<'NODE'
const fs = require('node:fs');

for (const name of ['AGENTS.md', 'app.json']) {
  if (!fs.existsSync(name)) throw new Error(`缺少 ${name}`);
}
if (!fs.existsSync('app.js') && !fs.existsSync('app.ink')) {
  throw new Error('缺少 app.js 或 app.ink 应用入口');
}

const manifest = JSON.parse(fs.readFileSync('app.json', 'utf8'));
if (!Array.isArray(manifest.pages) || manifest.pages.length === 0) {
  throw new Error('app.json.pages 必须是非空数组');
}
for (const route of manifest.pages) {
  if (typeof route !== 'string' || route.length === 0) {
    throw new Error(`非法页面路由：${String(route)}`);
  }
  const ink = `${route}.ink`;
  const wxml = `${route}.wxml`;
  if (!fs.existsSync(ink) && !fs.existsSync(wxml)) {
    throw new Error(`声明页面不存在：${ink} / ${wxml}`);
  }
  console.log(`declared page: ${route}`);
}

if (fs.existsSync('package.json')) {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  console.log('package.json.scripts =', pkg.scripts ?? {});
} else {
  console.log('没有 package.json；不运行任何 npm package script');
}
NODE

cd "$ROKID_SKILL_ROOT"
python3 ./scripts/validate_aiui_project.py \
  "$AIUI_SOURCE_DIR" \
  --target-version 0.17.0 \
  --strict
```

官方稳定版快速入门给出的本地初始化入口就是 `npm create @yodaos-pkg/aiui-agent@latest my-agent`。[AIUI 0.17 快速入门](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md#L33-L49)

### 2. 先解析并探测本次真正使用的 AIX

这一段不使用全局同名命令，而是明确选择发布版 0.8.2，同时记录解析到的 `aix` 路径和完整帮助。后面只能走帮助中实际出现的分支。

```bash
set -euo pipefail

ROKID_SKILL_ROOT="$PWD"
AIUI_ARTIFACT_DIR="$ROKID_SKILL_ROOT/artifacts"
AIUI_AIX_PACKAGE='@yodaos-pkg/aix-cli@0.8.2'
mkdir -p "$AIUI_ARTIFACT_DIR"

npx --yes --package "$AIUI_AIX_PACKAGE" \
  -c 'command -v aix && aix --help' \
  | tee "$AIUI_ARTIFACT_DIR/aix-help.txt"
```

不要用 `aix --version` 猜版本；0.8.2 对该选项会显示通用帮助。这里的 npm 包版本来自显式固定值，命令能力来自刚保存的根帮助。

### 3. 仅在帮助确实公布能力时做浏览器热更新预览

下面的 `preview --dev` 是浏览器 Ink 运行时的预览和热更新，不是真机调试，也不能证明眼镜光学效果、硬件按键、焦点、传感器、权限或持续性能。运行后按终端打印的 URL 在浏览器验收；完成后按 Ctrl-C 停止。

```bash
set -euo pipefail

ROKID_SKILL_ROOT="$PWD"
AIUI_SOURCE_DIR="$ROKID_SKILL_ROOT/my-agent"
AIUI_HELP_FILE="$ROKID_SKILL_ROOT/artifacts/aix-help.txt"
AIUI_AIX_PACKAGE='@yodaos-pkg/aix-cli@0.8.2'

if grep -Eq '(^|[[:space:]])preview([[:space:]<]|$)' "$AIUI_HELP_FILE" \
  && grep -Fq -- '--dev' "$AIUI_HELP_FILE"; then
  npx --yes --package "$AIUI_AIX_PACKAGE" \
    aix preview "$AIUI_SOURCE_DIR" --dev
else
  echo '所选 AIX 的根帮助未同时公布 preview 和 --dev；跳过该分支。' >&2
  exit 2
fi
```

### 4. 用帮助中公布的 `pack` 打包，并用 `list`/`ls` 检查同一个产物

产物写到源码目录之外，使用时间戳避免覆盖已有文件。打包后必须非空，且列表必须包含 `app.json`、`META-INF/aix/manifest.json` 和 `app.json` 声明的首个页面。

```bash
set -euo pipefail

ROKID_SKILL_ROOT="$PWD"
AIUI_SOURCE_DIR="$ROKID_SKILL_ROOT/my-agent"
AIUI_ARTIFACT_DIR="$ROKID_SKILL_ROOT/artifacts"
AIUI_HELP_FILE="$AIUI_ARTIFACT_DIR/aix-help.txt"
AIUI_AIX_PACKAGE='@yodaos-pkg/aix-cli@0.8.2'
AIUI_AIX_OUT="$AIUI_ARTIFACT_DIR/my-agent-$(date +%Y%m%d-%H%M%S).aix"

grep -Eq '(^|[[:space:]])pack([[:space:]<]|$)' "$AIUI_HELP_FILE" || {
  echo '所选 AIX 未公布 pack；停止。' >&2
  exit 2
}

if grep -Eq '(^|[[:space:]])list([[:space:]<]|$)' "$AIUI_HELP_FILE"; then
  AIUI_INSPECT_COMMAND='list'
elif grep -Eq '(^|[[:space:]])ls([[:space:]<]|$)' "$AIUI_HELP_FILE"; then
  AIUI_INSPECT_COMMAND='ls'
else
  echo '所选 AIX 未公布 list 或 ls；停止。' >&2
  exit 2
fi

npx --yes --package "$AIUI_AIX_PACKAGE" \
  aix pack "$AIUI_SOURCE_DIR" -o "$AIUI_AIX_OUT"
test -s "$AIUI_AIX_OUT"

AIUI_LISTING="$AIUI_AIX_OUT.list.txt"
npx --yes --package "$AIUI_AIX_PACKAGE" \
  aix "$AIUI_INSPECT_COMMAND" "$AIUI_AIX_OUT" \
  | tee "$AIUI_LISTING"

AIUI_PAGE_ROUTE="$(node -e '
const fs = require("node:fs");
const manifest = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
process.stdout.write(manifest.pages[0]);
' "$AIUI_SOURCE_DIR/app.json")"

if test -f "$AIUI_SOURCE_DIR/$AIUI_PAGE_ROUTE.ink"; then
  AIUI_PAGE_ENTRY="$AIUI_PAGE_ROUTE.ink"
elif test -f "$AIUI_SOURCE_DIR/$AIUI_PAGE_ROUTE.wxml"; then
  AIUI_PAGE_ENTRY="$AIUI_PAGE_ROUTE.wxml"
else
  echo "找不到声明页面：$AIUI_PAGE_ROUTE" >&2
  exit 3
fi

grep -Fq 'app.json' "$AIUI_LISTING"
grep -Fq 'META-INF/aix/manifest.json' "$AIUI_LISTING"
grep -Fq "$AIUI_PAGE_ENTRY" "$AIUI_LISTING"
wc -c "$AIUI_AIX_OUT"
shasum -a 256 "$AIUI_AIX_OUT"
printf 'AIX artifact: %s\n' "$AIUI_AIX_OUT"
```

`pack` 只生成本地 `.aix`，`list`/`ls` 只验证包内容；二者都不上传、不安装眼镜，也不等于发布。[AIX 0.8.2 CLI 说明](https://github.com/yodaos-project/aix/blob/19e6133f1984ee4455e6de9167b582864b528252/packages/cli/README.md)

### 5. 平台上传、真机安装和上架是独立门禁

AIX CLI 到此结束。后续必须使用有权限的 ROKID 平台和真实设备：

1. 登录 [AIUI Studio](https://aiui.rokid.com/)，从本地导入 `my-agent/` 源码目录；确认所选目录顶层直接包含 `app.json`。
2. 在 Studio 的 Web 模拟中检查输入、镜腿操作和不同光照。这是 Studio 模拟门禁，仍不是真机证据。
3. 在当前账号可见的 Studio/Craft 构建与提审流程里，为正确的 Agent 上传上一步生成的确切 `.aix`（若当前界面由 Studio 直接从源码生成版本，则选择该受支持入口），保存新版本，并核对平台显示的版本、文件大小/校验信息与本地产物。界面没有相应入口时停止，不要用不存在的 CLI 上传命令替代。
4. 在 Rokid AI App 进入“设置 → 开发者”，更新眼镜资源包；看到“智能体资源包下载成功”后，在真实 Rokid Glasses 上语义唤起该 Agent。
5. 在眼镜上验证核心流程、焦点、按键/镜腿输入、权限、明暗和复杂背景、网络失败与持续性能。通过后再在“构建与提审”补全真实权限用途、图标、截图/视频和介绍，保存并提交审核；审核通过/发布状态必须以平台回执为准。

当前我没有你的 ROKID 凭据、平台回执和眼镜，因此不能声称已经部署或今天一定上线。最终放行清单应全部有证据：

- [ ] 0.17.0 严格静态校验通过。
- [ ] 若本次 `--help` 公布 `preview --dev`，浏览器预览/热更新通过；否则记录为未提供而非伪造命令。
- [ ] `pack` 成功，目标 `.aix` 非空，并记录路径、字节数和 SHA-256。
- [ ] `list`/`ls` 针对同一个 `.aix`，包含 `app.json`、manifest 和声明页面。
- [ ] Studio/Craft 已接收正确产物并生成/保存新版本，Web 模拟通过。
- [ ] Rokid AI App 已下载最新资源包，真实眼镜核心矩阵通过。
- [ ] 审核/发布状态已有平台回执；在此之前状态只能写“待上传”“待真机验证”或“待审核”，不能写“已部署”。
