# Forward Evaluation Capture

- Scenario: `01-conversation-card`
- Conditions: Fresh behavior-test response after loading the repository Skill and only task-routed references; no Studio or physical-device run was available.
- Captured: `2026-09-07T22:19:39+0800`
- Post-capture relocation: the response below is preserved verbatim; its capture-time `scripts/validate_aiui_project.py` path is now `skills/rokid-aiui-agent/scripts/validate_aiui_project.py`.

---

我会按“可直接导入 AIUI Studio 的源码目录”交付，项目目录名为 `weather-card/`。

先明确两个交付假设：提示没有给出版本和设备，所以兼容目标取稳定版 AIUI `0.17.0`，首要宿主是对话流 `_current`；视觉配置则暂按 RokidGlasses1/2 的单绿色透明显示来做，不能把这套单色约束泛化到其他 ROKID 设备。若实际宿主或眼镜型号不同，需要按实机结果调整。

这里还存在一处必须显式保留的官方资料冲突：当前官方 Page/target 文档允许 `_current` 页面交互，而较旧的官方 bundled Skill 曾把对话卡概括为 display-only。这里按更新且版本匹配的 Page 文档保留“刷新”按钮，但 `_current` 中的宿主焦点、元素焦点、点击/Enter 激活和事件拦截仍与宿主及运行时有关，不能在实测前宣称必然可交互。[AIUI 0.17 Page target 文档](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page.en-US.md#L26-L43)

项目结构：

```text
weather-card/
├── AGENTS.md
├── app.json
├── app.js
├── app.wxss
└── pages/
    └── weather/
        └── index.ink
```

`weather-card/AGENTS.md`

```md
# Weather Card Agent

- Present `pages/weather/index` as a compact weather result in the conversation (`_current`). The host selects the actual target.
- Pass `city`, `latitude`, and `longitude` together when known.
- If location input is absent, use the built-in Beijing default without interrupting the conversation.
- Keep refresh in place; do not navigate away from or close the conversation.
- Never claim that refresh/focus works on a host or device until it has been tested there.
- The sample reads current weather from Open-Meteo. Replace it with the product-owned endpoint before production if provider, privacy, or availability requirements demand that.
```

`weather-card/app.json`

```json
{
  "pages": [
    "pages/weather/index"
  ],
  "window": {
    "navigationBarTitleText": "天气"
  }
}
```

这里刻意没有添加 `INTERNET`：当前资料没有为它建立可用的 AIUI 权限 token，不能从浏览器或微信小程序经验反推。0.17 的官方网络文档直接给出了 `fetch()`、`response.ok`/`json()` 以及每请求 `timeout`。[AIUI 0.17 HTTPS API](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/network/https.en-US.md)

`weather-card/app.js`

```js
App({});
```

`weather-card/app.wxss`

```css
page {
  margin: 0;
  color: rgba(64, 255, 94, 0.72);
  background-color: #000000;
  font-family: sans-serif;
}
```

`weather-card/pages/weather/index.ink`

```html
<script def>
{
  "description": "Show current weather and refresh it in the conversation",
  "schema": {
    "type": "object",
    "properties": {
      "city": { "type": "string" },
      "latitude": { "type": "number" },
      "longitude": { "type": "number" }
    }
  }
}
</script>

<script setup>
export default {
  data: {
    city: "北京",
    latitude: 39.9042,
    longitude: 116.4074,
    temperature: "--",
    rainProbability: "--",
    updatedAt: "--",
    loading: false,
    hasData: false,
    live: false,
    empty: false,
    stale: false,
    failed: false,
    statusText: "等待加载",
    actionText: "刷新"
  },

  onLoad(query) {
    const input = query || {};
    const next = {};

    if (typeof input.city === "string" && input.city.length > 0) {
      next.city = input.city;
    }
    if (typeof input.latitude === "number") {
      next.latitude = input.latitude;
    }
    if (typeof input.longitude === "number") {
      next.longitude = input.longitude;
    }

    this.setData(next);
    this.refresh();
  },

  buildWeatherUrl() {
    return "https://api.open-meteo.com/v1/forecast"
      + "?latitude=" + this.data.latitude
      + "&longitude=" + this.data.longitude
      + "&current=temperature_2m%2Cprecipitation_probability"
      + "&timezone=auto"
      + "&forecast_days=1";
  },

  async refresh() {
    if (this.data.loading) return;

    const hadData = this.data.hasData;
    this.setData({
      loading: true,
      live: false,
      empty: false,
      stale: false,
      failed: false,
      statusText: hadData ? "正在刷新，暂时保留上次数据" : "正在获取天气",
      actionText: "刷新中"
    });

    try {
      const response = await fetch(this.buildWeatherUrl(), {
        method: "GET",
        timeout: 5000
      });

      if (!response.ok) {
        throw new Error("Weather request failed: " + response.status);
      }

      const payload = await response.json();
      const current = payload && payload.current;
      const usable = current
        && typeof current.temperature_2m === "number"
        && typeof current.precipitation_probability === "number"
        && typeof current.time === "string"
        && current.time.length > 0;

      if (!usable) {
        if (hadData) {
          this.setData({
            loading: false,
            hasData: true,
            live: false,
            empty: false,
            stale: true,
            failed: false,
            statusText: "服务未返回新数据，显示上次结果",
            actionText: "重试"
          });
        } else {
          this.setData({
            loading: false,
            hasData: false,
            live: false,
            empty: true,
            stale: false,
            failed: false,
            statusText: "暂无可用天气数据",
            actionText: "重试"
          });
        }
        return;
      }

      this.setData({
        temperature: current.temperature_2m,
        rainProbability: current.precipitation_probability,
        updatedAt: current.time,
        loading: false,
        hasData: true,
        live: true,
        empty: false,
        stale: false,
        failed: false,
        statusText: "天气已更新",
        actionText: "刷新"
      });
    } catch (error) {
      if (hadData) {
        this.setData({
          loading: false,
          hasData: true,
          live: false,
          empty: false,
          stale: true,
          failed: false,
          statusText: "刷新失败，显示上次结果",
          actionText: "重试"
        });
      } else {
        this.setData({
          loading: false,
          hasData: false,
          live: false,
          empty: false,
          stale: false,
          failed: true,
          statusText: "天气服务暂不可用",
          actionText: "重试"
        });
      }
    }
  }
};
</script>

<page>
  <view class="screen">
    <view class="panel">
      <view class="header-row">
        <view>
          <text class="eyebrow">CURRENT WEATHER</text>
          <text class="city">{{city}}</text>
        </view>
        <button class="action" bindtap="refresh" disabled="{{loading}}">{{actionText}}</button>
      </view>

      <view wx:if="{{loading}}" class="status">
        <text class="status-mark">···</text>
        <text>{{statusText}}</text>
      </view>

      <view wx:if="{{hasData}}" class="metrics-row">
        <view class="metric">
          <text class="metric-label">温度</text>
          <text class="metric-value primary-value">{{temperature}}°C</text>
        </view>
        <view class="metric rain-metric">
          <text class="metric-label">降雨概率</text>
          <text class="metric-value">{{rainProbability}}%</text>
        </view>
        <text class="updated">更新 {{updatedAt}}</text>
      </view>

      <view wx:if="{{live}}" class="status">
        <text class="status-mark">●</text>
        <text>LIVE · {{statusText}}</text>
      </view>

      <view wx:if="{{empty}}" class="status status-empty">
        <text class="status-mark">○</text>
        <text>EMPTY · {{statusText}}，请选择“重试”</text>
      </view>

      <view wx:if="{{stale}}" class="status status-warning">
        <text class="status-mark">△</text>
        <text>STALE · {{statusText}}，请选择“重试”</text>
      </view>

      <view wx:if="{{failed}}" class="status status-error">
        <text class="status-mark">△</text>
        <text>ERROR · {{statusText}}，请选择“重试”</text>
      </view>
    </view>
  </view>
</page>

<style>
.screen {
  padding: 12px 16px;
  background-color: #000000;
}

.panel {
  padding: 12px;
  background-color: rgba(64, 255, 94, 0.06);
  border: 1px solid rgba(64, 255, 94, 0.24);
  border-radius: 6px;
}

:host-focus .panel {
  border-width: 2px;
  border-color: rgba(64, 255, 94, 0.72);
}

.header-row,
.metrics-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.eyebrow,
.metric-label,
.updated {
  display: block;
  color: rgba(64, 255, 94, 0.48);
  font-size: 10px;
  line-height: 14px;
}

.eyebrow {
  letter-spacing: 1px;
}

.city {
  display: block;
  margin-top: 2px;
  color: rgba(64, 255, 94, 0.72);
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
}

.action {
  min-width: 64px;
  min-height: 32px;
  margin: 0;
  padding: 0 12px;
  color: rgba(64, 255, 94, 0.72);
  background-color: transparent;
  border: 1px solid rgba(64, 255, 94, 0.48);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.metrics-row {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(64, 255, 94, 0.24);
}

.metric {
  min-width: 96px;
}

.rain-metric {
  margin-left: 16px;
}

.metric-value {
  display: block;
  margin-top: 2px;
  color: rgba(64, 255, 94, 0.72);
  font-family: monospace;
  font-size: 13px;
  font-weight: 500;
  line-height: 17px;
}

.primary-value {
  color: #40ff5e;
}

.updated {
  margin-left: 16px;
  font-family: monospace;
}

.status {
  margin-top: 8px;
  padding-top: 8px;
  color: rgba(64, 255, 94, 0.72);
  border-top: 1px solid rgba(64, 255, 94, 0.24);
  font-size: 12px;
  line-height: 17px;
}

.status-mark {
  margin-right: 8px;
  color: #40ff5e;
}

.status-empty,
.status-warning,
.status-error {
  padding: 8px;
  background-color: rgba(64, 255, 94, 0.06);
  border: 1px dashed rgba(64, 255, 94, 0.72);
  border-radius: 4px;
}

@media (target: _current) {
  .screen {
    padding: 8px 12px;
  }

  .panel {
    padding: 8px 12px;
  }
}

@media (target: _blank) {
  .screen {
    padding: 12px 16px;
  }
}
</style>
```

示例使用 Open-Meteo 的无密钥 forecast API；它的文档列出了 `current` 参数和当前天气变量。上线前仍应按产品的数据合规、服务条款、可用性和网络策略决定是否换成自有代理接口。[Open-Meteo Forecast API](https://open-meteo.com/en/docs)

这个 Page 只有一个 `<page>` 根，没有 `<widget>`，也没有路由跳转、深层流程或默认按键拦截；刷新始终原位发生，因此不会主动让用户离开对话。

视觉上采用当前 RokidGlasses1/2 单绿色方向中的 `#40ff5e` 亮绿与 72/48/24/12/6% 亮度层级：普通结构线 1px、焦点 2px、按钮 4px 圆角、分组面板 6px 圆角、正常局部填充仅 6%（不超过 12%），没有阴影、渐变或大面积实心绿。它来自当前 0.18 仓库的 beta 设计方向，只作为目标眼镜的视觉配置，不被误写成 0.17 新运行时能力。[当前单绿色 beta 设计](https://github.com/yodaos-project/AIUI/blob/8b19a87b4ba8b486c0dd4dd3fd32290d27891069/design/monochrome/design-system-green.md)

验证按以下顺序执行，不能把其中任何一层冒充实机结论。

1. 从本 Skill 仓库根目录做严格静态验证：

```bash
python3 scripts/validate_aiui_project.py ./weather-card --strict --target-version 0.17.0
```

预期至少确认 `app.json` 可解析、声明的 `pages/weather/index` 能解析到 `.ink`、`script def` 是 JSON、只有一个 Page 根且处理器可解析。出现 warning 也不进入打包。

2. 先探测本机 AIX，而不是猜命令：

```bash
node --version
command -v aix
aix --help
```

记录 Node 版本、解析到的可执行文件和完整 help。若本机没有 `aix`，可先用已固定的已发布版本隔离探测：

```bash
npx --yes --package @yodaos-pkg/aix-cli@0.8.2 aix --help
```

3. 只有根 help 明确列出对应命令/参数时，才运行以下分支；若名称是 `ls` 而不是 `list`，使用 help 中实际广告的名称：

```bash
aix preview ./weather-card
mkdir -p ./artifacts
aix pack ./weather-card -o ./artifacts/weather-card.aix
aix list ./artifacts/weather-card.aix
```

`list` 输出应包含 `app.json` 和 `pages/weather/index.ink`。`preview` 只是浏览器 Ink 运行时，`pack` 也只是本地封装；这里没有 `aix create`、`aix dev`、`aix build` 或 `aix deploy`。

4. 在 AIUI Studio 导入的目录必须就是 `weather-card/`。在准确的对话宿主上以 `_current` 验证：首次 loading、正常 success、空/缺字段、HTTP 失败、5 秒 timeout、弱网、断网、连续点击，以及从失败点击“重试”恢复；有旧数据时失败应显示 `STALE` 并保留上次值。还要分别记录宿主 focus/blur、按钮元素焦点、点击/Enter/镜腿输入是否能激活，以及宿主提供展开时 `_current → _blank → 返回对话` 是否保留位置。

5. 最后在实际目标 RokidGlasses1/2 上重复以上交互，并在明亮、黑暗、杂乱背景下检查城市、温度、降雨概率、时间、错误标签与焦点边界。`480×352` 是当前 Ink/运行时参考视口；较旧官方光学指南中的 `480×640` 光学画布及 `480×400` 推荐区域是另一坐标层，二者不能当成同一尺寸。以实机舒适视野与实际运行时测量为最终依据。

当前只能交付源码和验证方案；在 Studio/真实宿主/实机记录完成前，不会声称刷新按钮、焦点、光学可读性或回到对话的行为已经通过。
