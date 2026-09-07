# Forward Response: AIUI Studio Import Delivery

- Scenario: `tests/scenarios/04-studio-import-delivery.md`
- Skill: `skills/rokid-aiui-agent/SKILL.md`
- Captured: 2026-09-07
- Evidence staging root: `/tmp/rokid-aiui-forward04.xAnLwR`

## Response

我把主交付物整理成了完整、可编辑的 AIUI 源码工程，而不是只交代码片段或 `.aix`。由于项目和宿主都没有给出版本，明确采用官方稳定兼容基线 **AIUI 0.17.0**；没有加入 0.18.0 才有的 Widgets、Agent Workers、清单字段或 API。

本轮已物化并验证的 AIUI Studio 本地导入根目录是：

```text
/tmp/rokid-aiui-forward04.xAnLwR/rokid-water-reminder
```

该目录直接包含 `app.json`，完整结构为：

```text
rokid-water-reminder/
├── AGENTS.md
├── app.json
├── app.js
├── app.wxss
└── pages/
    └── home/
        └── index.ink
```

项目不引用任何外部组件或资产。以下是全部源码，而非节选。

`AGENTS.md`

```markdown
# 喝水提醒

你是一个简洁、克制的喝水节奏助手。

- 当用户询问喝水进度时，展示 `pages/home/index`。
- 引导用户使用“记录一杯”更新当天进度。
- 不提供医疗诊断，不把通用饮水建议描述为个体医疗建议。
- 当前目标是 AIUI 0.17.0 Page-only 兼容工程。
- 未验证目标主机的后台调度能力前，不声称可以主动发送系统通知。
```

`app.json`

```json
{
  "pages": ["pages/home/index"],
  "window": {
    "navigationBarTitleText": "喝水提醒"
  }
}
```

`app.js`

```js
export default {};
```

`app.wxss`

```css
page {
  color: #40ff5e;
  background-color: transparent;
}
```

`pages/home/index.ink`

```html
<script type="application/json" def>
{
  "description": "展示并更新当天的喝水杯数"
}
</script>

<script setup>
export default {
  data: {
    cups: 0,
    goalCups: 8,
    complete: false,
    status: "今天还没有记录喝水"
  },

  drinkOne() {
    const cups = Math.min(this.data.cups + 1, this.data.goalCups);
    const complete = cups >= this.data.goalCups;
    this.setData({
      cups,
      complete,
      status: complete ? "今日目标已完成" : `已记录 ${cups} 杯`
    });
  },

  resetDay() {
    this.setData({
      cups: 0,
      complete: false,
      status: "今天还没有记录喝水"
    });
  }
};
</script>

<page>
  <view class="panel">
    <text class="eyebrow">HYDRATION</text>
    <text class="title">喝水提醒</text>
    <text class="count">{{cups}} / {{goalCups}} 杯</text>
    <text class="status">{{status}}</text>
    <button class="primary" bindtap="drinkOne">记录一杯</button>
    <button class="secondary" bindtap="resetDay">重新开始</button>
    <text wx:if="{{complete}}" class="complete">完成 · 继续保持</text>
  </view>
</page>

<style>
.panel {
  box-sizing: border-box;
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(64, 255, 94, 0.32);
  border-radius: 6px;
  background-color: rgba(64, 255, 94, 0.08);
}

.eyebrow {
  display: block;
  font-size: 12px;
  opacity: 0.72;
}

.title {
  display: block;
  margin-top: 6px;
  font-size: 22px;
  font-weight: 500;
}

.count {
  display: block;
  margin-top: 16px;
  font-size: 28px;
}

.status,
.complete {
  display: block;
  margin-top: 8px;
  font-size: 14px;
}

.primary,
.secondary {
  width: 100%;
  margin-top: 12px;
  border-radius: 4px;
}

.secondary {
  background-color: transparent;
  border: 1px solid rgba(64, 255, 94, 0.48);
}

.complete {
  color: #40ff5e;
}
</style>
```

`app.json.pages[0]` 精确解析为完整文件 `pages/home/index.ink`，模板使用的两个处理函数都存在，也没有遗漏的资产路径。为了不虚构能力，这个 0.17.0 版本实现的是前台喝水记录与提醒界面；通用后台定时/系统通知能力尚未从目标宿主得到证据，不能假装已经实现。

### GitHub 导入三元组

GitHub 交付应使用以下精确坐标：

```text
Repository: https://github.com/BreezeLife/rokid-aiui-agent-skill
Ref: main
AIUI project directory: examples/rokid-water-reminder
```

本轮评测没有执行远端推送或 Studio 账号侧导入，因此该三元组是待发布坐标，**没有冒充已可用**。实际交付时必须先把同一完整目录提交并推送到该 ref；若最终 ref 或目录改变，应回报实际值并重新校验。

### 已真实执行的严格结构校验

命令针对的就是上述本地导入根目录：

```bash
python3 skills/rokid-aiui-agent/scripts/validate_aiui_project.py \
  /tmp/rokid-aiui-forward04.xAnLwR/rokid-water-reminder \
  --target-version 0.17.0 --strict --json
```

实际退出码为 `0`，输出为：

```json
{
  "diagnostics": [],
  "errorCount": 0,
  "strict": true,
  "targetVersion": "0.17.0",
  "valid": true,
  "warningCount": 0
}
```

### 已真实执行的 AIX 探测、打包与检查

实际 Node 为 `v24.19.0`。先探测锁定的已发布 CLI：

```bash
npx --yes --package @yodaos-pkg/aix-cli@0.8.2 aix --help
```

退出码 `0`；根帮助明确列出 `pack` 和 `list`（别名 `ls`）。随后只执行这两个已公布命令：

```bash
npx --yes --package @yodaos-pkg/aix-cli@0.8.2 aix pack \
  /tmp/rokid-aiui-forward04.xAnLwR/rokid-water-reminder \
  -o /tmp/rokid-aiui-forward04.xAnLwR/artifacts/rokid-water-reminder.aix

npx --yes --package @yodaos-pkg/aix-cli@0.8.2 aix list \
  /tmp/rokid-aiui-forward04.xAnLwR/artifacts/rokid-water-reminder.aix
```

两条命令实际退出码均为 `0`。`pack` 收集 5 个源码文件并生成 4,064 字节的附加产物；SHA-256 为：

```text
ea539c4d98fdbbb52e4f75812baef0a952232a74bf65db493a4ecb1c1e8dbd92
```

`list` 的实际关键清单为：

```text
AGENTS.md
META-INF/aix/manifest.json
VERSION
app.js
app.json
app.wxss
pages/home/index.ink
```

`.aix` 位于 `/tmp/rokid-aiui-forward04.xAnLwR/artifacts/rokid-water-reminder.aix`，是附加交付物；可编辑源码目录仍是唯一的 Studio 源码导入根。

### Studio 操作与证据门禁

- 本地导入：AIUI Studio 选择本地目录导入，并选择 `/tmp/rokid-aiui-forward04.xAnLwR/rokid-water-reminder`。
- GitHub 导入：填写仓库 URL、branch/tag（这里是 `main`）和指定目录 `examples/rokid-water-reminder`；必须在对应 ref 已推送后执行。
- 结构校验和 AIX `pack/list` 已验证；它们只证明结构与包内容，不证明 Studio 账号侧导入成功。
- Studio Web 模拟、平台上传/发布、Rokid AI App 下载以及实体眼镜上的光学、焦点、按键、语音和持续运行均未在本轮执行，全部保留为后续手工证据门禁，不能报告为已通过。

## Evaluation cleanup note

The project above was materialized byte-for-byte under the stated staging root. The validator, published AIX CLI help, `pack`, `list`, byte-size check, and SHA-256 calculation were executed before this response was recorded. The temporary staging tree may be safely removed after evaluation; no Studio, platform, or device success is claimed.
