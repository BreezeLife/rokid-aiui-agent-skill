# Baseline Response: Conversation Weather Card

- Scenario: `tests/scenarios/01-conversation-card.md`
- Conditions: fresh subagent, no web access, no workspace inspection, no AIUI-specific Skill
- Captured: 2026-09-07

## Verbatim response

AIUI 对话流里的卡片不适合放可点击“刷新”按钮：眼镜端对话卡片通常是展示型消息，不能可靠接收按钮点击事件。强行画一个按钮只会得到“看得见、点不了”的假交互。

今天可交付的实现应改为：

- 卡片展示：城市、温度、降雨概率、更新时间。
- 卡片底部显示提示：`说“刷新天气”获取最新天气`。
- Agent 收到“刷新天气”或“更新天气”后重新请求天气数据，并发送一张新卡片。
- 不在原卡片上原地更新；对话流追加最新卡片。

建议的数据结构：

```json
{
  "type": "weather",
  "city": "上海",
  "temperature": "28°C",
  "rainProbability": "35%",
  "updatedAt": "2026-09-07 14:30",
  "hint": "说“刷新天气”获取最新天气"
}
```

处理逻辑：

```ts
async function renderWeather(city: string) {
  const weather = await weatherService.getCurrent(city);

  return {
    type: "weather",
    city: weather.city,
    temperature: `${weather.temperature}°C`,
    rainProbability: `${weather.rainProbability}%`,
    updatedAt: new Date().toLocaleString("zh-CN", {
      timeZone: "Asia/Shanghai",
      hour12: false,
    }),
    hint: "说“刷新天气”获取最新天气",
  };
}

async function handleIntent(intent: string, city: string) {
  if (
    intent === "weather.query" ||
    intent === "weather.refresh"
  ) {
    return renderWeather(city);
  }

  return {
    type: "text",
    text: "你可以说“刷新天气”。",
  };
}
```

意图样例：

```json
{
  "weather.refresh": [
    "刷新天气",
    "更新天气",
    "重新查一下天气",
    "看看最新天气"
  ]
}
```

验证流程：

```bash
aix dev
```

依次测试：

```text
上海天气怎么样
刷新天气
更新天气
```

确认每次都生成包含四项数据的新卡片，然后：

```bash
aix build
aix deploy
```

如果产品必须保留“刷新”字样，可以将其做成非交互提示，但不应把它描述成按钮。真正的刷新入口应使用语音意图。
