# Baseline Response: AIUI Studio Import Delivery

- Scenario: `tests/scenarios/04-studio-import-delivery.md`
- Conditions: fresh subagent, no web access, no workspace inspection, no AIUI-specific Skill
- Captured: 2026-09-07

## Verbatim response

下面给出一个最小可运行的实现。由于 `.aix` 的清单格式和运行时 API 会随 AIUI Studio 版本变化，而你没有指定版本，我不能诚实地声称这里手工构造的包一定能被所有版本直接导入。以下默认采用“JavaScript 智能体 + ZIP 改名为 `.aix`”结构；若 Studio 提示清单不兼容，请先导入本地目录，再由当前 Studio 导出正式 `.aix`。

核心逻辑 `src/index.js`：

```js
const DEFAULT_INTERVAL_MINUTES = 60;
const DEFAULT_GOAL_ML = 2000;
const JOB_ID = "water-reminder";

function today() {
  return new Date().toISOString().slice(0, 10);
}

async function readState(ctx) {
  const state = (await ctx.storage.get("hydration")) || {};

  if (state.day !== today()) {
    state.day = today();
    state.consumedMl = 0;
  }

  return {
    enabled: false,
    intervalMinutes: DEFAULT_INTERVAL_MINUTES,
    dailyGoalMl: DEFAULT_GOAL_ML,
    consumedMl: 0,
    ...state,
  };
}

async function saveState(ctx, state) {
  await ctx.storage.set("hydration", state);
}

async function startReminder(ctx, minutes = DEFAULT_INTERVAL_MINUTES) {
  const intervalMinutes = Math.max(15, Math.min(240, Number(minutes) || 60));
  const state = await readState(ctx);

  state.enabled = true;
  state.intervalMinutes = intervalMinutes;
  state.nextReminderAt = Date.now() + intervalMinutes * 60_000;
  await saveState(ctx, state);

  await ctx.scheduler.cancel(JOB_ID).catch(() => {});
  await ctx.scheduler.scheduleRepeating({
    id: JOB_ID,
    intervalMs: intervalMinutes * 60_000,
    event: "water_reminder_tick",
  });

  return `好的，我会每${intervalMinutes}分钟提醒你喝水。`;
}

async function stopReminder(ctx) {
  const state = await readState(ctx);
  state.enabled = false;
  delete state.nextReminderAt;

  await saveState(ctx, state);
  await ctx.scheduler.cancel(JOB_ID).catch(() => {});

  return "喝水提醒已关闭。";
}

async function recordDrink(ctx, amount = 250) {
  const state = await readState(ctx);
  const amountMl = Math.max(1, Number(amount) || 250);

  state.consumedMl += amountMl;
  await saveState(ctx, state);

  const remaining = Math.max(0, state.dailyGoalMl - state.consumedMl);

  if (remaining === 0) {
    return `已记录${amountMl}毫升。今天累计${state.consumedMl}毫升，目标完成！`;
  }

  return `已记录${amountMl}毫升。今天累计${state.consumedMl}毫升，还差${remaining}毫升。`;
}

export default {
  async onLaunch(ctx) {
    return ctx.reply("喝水提醒已就绪。你可以说：每45分钟提醒我喝水。");
  },

  async onIntent(request, ctx) {
    const intent = request.intent?.name;
    const slots = request.intent?.slots || {};

    switch (intent) {
      case "StartWaterReminder":
        return ctx.reply(await startReminder(ctx, slots.intervalMinutes));

      case "StopWaterReminder":
        return ctx.reply(await stopReminder(ctx));

      case "RecordWater":
        return ctx.reply(await recordDrink(ctx, slots.amountMl));

      case "WaterStatus": {
        const state = await readState(ctx);
        const status = state.enabled
          ? `提醒已开启，每${state.intervalMinutes}分钟一次`
          : "提醒未开启";

        return ctx.reply(
          `${status}。今天已喝${state.consumedMl}毫升，目标${state.dailyGoalMl}毫升。`
        );
      }

      default:
        return ctx.reply(
          "你可以说：每小时提醒我喝水、我喝了300毫升、查看喝水进度，或者关闭喝水提醒。"
        );
    }
  },

  async onEvent(event, ctx) {
    if (event.name !== "water_reminder_tick") return;

    const state = await readState(ctx);
    if (!state.enabled) return;

    state.nextReminderAt =
      Date.now() + state.intervalMinutes * 60_000;
    await saveState(ctx, state);

    await ctx.notify({
      title: "喝水提醒",
      text: "该喝水啦，起来活动一下，喝一杯水吧。",
      speak: true,
    });
  },
};
```

`manifest.json`：

```json
{
  "schemaVersion": "1.0",
  "id": "com.example.rokid.water-reminder",
  "name": "喝水提醒",
  "version": "1.0.0",
  "description": "定时提醒喝水并记录每日饮水量",
  "entry": "src/index.js",
  "locale": "zh-CN",
  "permissions": [
    "storage",
    "scheduler",
    "notification",
    "speech"
  ],
  "intents": [
    {
      "name": "StartWaterReminder",
      "samples": [
        "提醒我喝水",
        "每小时提醒我喝水",
        "每{intervalMinutes}分钟提醒我喝水"
      ],
      "slots": {
        "intervalMinutes": {
          "type": "number",
          "required": false
        }
      }
    },
    {
      "name": "StopWaterReminder",
      "samples": [
        "关闭喝水提醒",
        "停止提醒我喝水"
      ]
    },
    {
      "name": "RecordWater",
      "samples": [
        "我喝水了",
        "我喝了{amountMl}毫升水"
      ],
      "slots": {
        "amountMl": {
          "type": "number",
          "required": false
        }
      }
    },
    {
      "name": "WaterStatus",
      "samples": [
        "查看喝水进度",
        "今天喝了多少水",
        "喝水提醒状态"
      ]
    }
  ]
}
```

目录结构：

```text
rokid-water-reminder/
├── manifest.json
└── src/
    └── index.js
```

在 `rokid-water-reminder` 的上级目录执行：

```bash
cd rokid-water-reminder
zip -r ../rokid-water-reminder.aix manifest.json src
```

会生成：

```text
rokid-water-reminder.aix
```

导入方式：

- 本地目录：AIUI Studio → 导入项目 → 选择 `rokid-water-reminder/`。
- `.aix`：AIUI Studio → 导入/安装智能体包 → 选择 `rokid-water-reminder.aix`。
- GitHub：将目录提交到仓库，AIUI Studio 选择“从 Git/GitHub 导入”，填写仓库地址和分支。
- 如果 Studio 报清单版本或运行时接口不兼容，先新建一个当前版本的 JavaScript 智能体，将 `src/index.js` 的业务逻辑迁入 Studio 生成的入口文件，并在 Studio 内重新配置四个意图后导出 `.aix`。
