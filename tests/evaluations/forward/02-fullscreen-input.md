Scenario: 02-fullscreen-input
Conditions: Forward behavior test; existing task-list Page; assume stable AIUI 0.17.0 and host-selected `_blank`; local `aix` unavailable
Captured: 2026-09-07 22:20 +0800

这是一个由宿主以 `_blank` 打开的全屏 **Page**，不是 Widget，也不是仅用于会话内展示的 `_current` 卡片。目标由宿主打开页面时选择，不应伪装成 Page 自己的固定清单字段。题目未指定版本，以下按稳定 AIUI `0.17.0` 实现。

我不会照做“所有按键都在 `onKeyDown` 里 `preventDefault()`”。AIUI 的 Backspace 返回、方向键根滚动和 Enter 激活等宿主默认动作定义在相应的 `keyup` 阶段；只有页面完整替代某个动作时，才应在 `onKeyUp` 对那一次事件调用 `preventDefault()`。把移动或执行同时放在 down/up 两边还会造成一次按键触发两次业务动作。这个行为以版本匹配的 [Page events 文档](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/1-framework/open-agent-format/page-events.en-US.md#interception-mechanism) 为准。

把下面逻辑合并进现有任务页的 `<script setup>`。实际业务副作用也应只接在 `executeCurrentItem`、`confirmCurrentItem`、`cancelCurrentItem` 这三个单一入口内，不要再从 `onKeyDown` 重复调用。

```html
<script setup>
export default {
  data: {
    items: [],
    focusIndex: -1,
    overlayVisible: false,
    activeTaskId: null,
    confirmedTaskId: null,
    cancelledTaskId: null,
    wakeKeyword: '',
    status: '暂无任务',
    gestureAvailable: false,
    gestureStatus: '正在检查头部手势能力'
  },

  onLoad() {
    this._worldAwarenessEnabled = false;
    this.setItems(this.data.items);

    // enableWorldAwareness 是 Page-only 能力；先探测、再启用、再接受手势。
    if (typeof this.enableWorldAwareness !== 'function') {
      this.setData({
        gestureAvailable: false,
        gestureStatus: '头部手势不可用，请使用 Enter 或页面控件'
      });
      return;
    }

    try {
      this.enableWorldAwareness();
      this._worldAwarenessEnabled = true;
      this.setData({
        gestureAvailable: true,
        gestureStatus: '头部手势已启用'
      });
    } catch (error) {
      this._worldAwarenessEnabled = false;
      this.setData({
        gestureAvailable: false,
        gestureStatus: '头部手势启用失败，请使用 Enter 或页面控件'
      });
    }
  },

  onUnload() {
    this._worldAwarenessEnabled = false;
    if (typeof this.disableWorldAwareness === 'function') {
      try {
        this.disableWorldAwareness();
      } catch (error) {
        // 页面已在卸载；不再写渲染状态。
      }
    }
  },

  setItems(nextItems) {
    const items = Array.isArray(nextItems) ? nextItems : [];
    let focusIndex = -1;

    if (items.length > 0) {
      const previous = Number.isInteger(this.data.focusIndex)
        ? this.data.focusIndex
        : 0;
      focusIndex = Math.max(0, Math.min(previous, items.length - 1));
    }

    this.setData({
      items,
      focusIndex,
      status: items.length > 0
        ? '当前：' + this.itemLabel(items[focusIndex])
        : '暂无任务'
    });
  },

  getItems() {
    return Array.isArray(this.data.items) ? this.data.items : [];
  },

  itemLabel(item) {
    if (!item || typeof item !== 'object') return '未命名任务';
    return item.title || item.name || '未命名任务';
  },

  currentItem() {
    const items = this.getItems();
    const index = this.data.focusIndex;
    if (!Number.isInteger(index) || index < 0 || index >= items.length) {
      return null;
    }
    return items[index];
  },

  currentTaskId(item) {
    return item && item.id !== undefined && item.id !== null
      ? item.id
      : this.data.focusIndex;
  },

  moveFocus(delta) {
    const items = this.getItems();
    if (items.length === 0) return false;

    const current = Math.max(
      0,
      Math.min(this.data.focusIndex, items.length - 1)
    );
    const next = Math.max(0, Math.min(current + delta, items.length - 1));

    // 一次 keyup 只提交一次状态；边界处仍由列表完整接管方向动作。
    this.setData({
      focusIndex: next,
      status: '当前：' + this.itemLabel(items[next])
    });
    return true;
  },

  executeCurrentItem() {
    const item = this.currentItem();
    if (!item) return false;

    // 将现有页面真正的“执行任务”副作用放在这个唯一入口。
    this.setData({
      activeTaskId: this.currentTaskId(item),
      status: '执行：' + this.itemLabel(item)
    });
    return true;
  },

  confirmCurrentItem() {
    const item = this.currentItem();
    if (!item) {
      this.setData({ status: '暂无可确认任务' });
      return false;
    }

    // 将现有确认副作用放在这里；点头只调用一次。
    this.setData({
      confirmedTaskId: this.currentTaskId(item),
      overlayVisible: false,
      status: '已确认：' + this.itemLabel(item)
    });
    return true;
  },

  cancelCurrentItem() {
    const item = this.currentItem();
    if (!item) {
      this.setData({ status: '暂无可取消任务' });
      return false;
    }

    // 将现有取消副作用放在这里；摇头只调用一次。
    this.setData({
      cancelledTaskId: this.currentTaskId(item),
      overlayVisible: false,
      status: '已取消：' + this.itemLabel(item)
    });
    return true;
  },

  onKeyUp(event) {
    if (!event) return;

    if (event.code === 'Backspace') {
      if (this.data.overlayVisible) {
        event.preventDefault();
        // 不返回、不移动焦点、不取消任务：只关闭遮罩。
        this.setData({ overlayVisible: false });
      }
      // 无遮罩时不 preventDefault，让宿主执行正常返回/关闭行为。
      return;
    }

    if (event.code === 'ArrowUp' || event.code === 'ArrowDown') {
      if (this.getItems().length === 0) return;
      event.preventDefault();
      this.moveFocus(event.code === 'ArrowUp' ? -1 : 1);
      return;
    }

    if (event.code === 'Enter') {
      if (this.getItems().length === 0) return;
      event.preventDefault();
      this.executeCurrentItem();
    }
  },

  onVoiceWakeup(event) {
    const keyword = event && typeof event.keyword === 'string'
      ? event.keyword
      : '';
    this.setData({
      wakeKeyword: keyword,
      status: keyword
        ? '语音唤醒：' + keyword
        : '已收到语音唤醒（宿主未提供关键词）'
    });
  },

  onHeadGesture(event) {
    if (!this._worldAwarenessEnabled || !event) return;

    if (event.gesture === 'nod') {
      this.confirmCurrentItem();
    } else if (event.gesture === 'shake') {
      this.cancelCurrentItem();
    }
  }
};
</script>
```

列表数据异步刷新时必须经过 `setItems(nextItems)`，这样删除末项、返回空列表等情况下 `focusIndex` 始终限制在 `0..length-1`，空列表固定为 `-1`。对应视图至少要同时显示焦点标记和状态文字，不能只靠亮度变化：

```html
<page>
  <view class="task-page">
    <view wx:if="{{items.length > 0}}" class="task-list">
      <view
        wx:for="{{items}}"
        wx:key="id"
        class="task-row {{index === focusIndex ? 'is-focused' : ''}}"
      >
        <text wx:if="{{index === focusIndex}}" class="focus-mark">▶</text>
        <text wx:else class="focus-placeholder">·</text>
        <text>{{item.title || item.name || '未命名任务'}}</text>
        <text wx:if="{{index === focusIndex}}" class="focus-label">当前</text>
      </view>
    </view>
    <text wx:else class="empty-state">暂无任务</text>

    <text class="status">{{status}}</text>
    <text class="gesture-status">{{gestureStatus}}</text>

    <view wx:if="{{overlayVisible}}" class="overlay">
      <text>任务详情</text>
      <text>Backspace 关闭</text>
    </view>
  </view>
</page>

<style>
.task-page { padding: 12px; }
.task-row { display: flex; padding: 8px; border-left: 1px solid transparent; }
.task-row.is-focused { border-left-width: 2px; }
.focus-mark, .focus-placeholder { width: 18px; }
.focus-label { margin-left: auto; }
.status, .gesture-status, .empty-state { display: block; margin-top: 8px; }
.overlay { position: absolute; left: 12px; right: 12px; top: 40px; padding: 12px; }
@media (target: _blank) {
  .task-page { display: flex; flex-direction: column; }
}
</style>
```

`onVoiceWakeup(event)` 直接读取 `event.keyword` 并显示实际匹配值，不写死某个唤醒词。头部输入先调用并能力探测 Page-only 的 `enableWorldAwareness()`；不可用或启用失败时保留 Enter/页面控件后备。`onHeadGesture(event)` 只消费 Page 已识别出的 `event.gesture` (`nod`/`shake`)，无需读取四元数或自行用低层传感器重建点头、摇头。卸载时清理状态并显式停止能力；运行时本身也会在 Page 卸载前停止这一 Page 私有会话，见 [Page API](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/3-api/framework/page.en-US.md#world-awareness)。

验证必须分层完成，不能因为“今天上线”跳过眼镜实机门槛：

1. **确定性状态测试**：用 `preventDefault` spy 分别投递 down/up。断言 keydown 不改变焦点、不执行任务、不拦截默认动作；每个 Arrow/Enter 的 keyup 只改变/执行一次；首尾不越界；空列表为 `-1` 且不拦截方向键/Enter。遮罩开启时 Backspace keyup 恰好拦截一次且唯一变化是 `overlayVisible: false`，遮罩关闭时不拦截。再覆盖任意 `event.keyword`、能力存在/缺失/抛错、启用前忽略手势、nod 确认、shake 取消及卸载清理。
2. **静态与 AIX 检查**：对 Studio 实际导入目录运行仓库的严格校验，明确 `--target-version 0.17.0`，再跑仓库测试；确认 `app.json`、路由、单一 `<page>` 根、模板方法和资源路径。当前捕获环境没有可用的 `aix`，所以不能声称 AIX 打包/预览已通过；在发布机先记录 Node、AIX 路径及 `aix --help`，只有帮助实际列出 `pack`、`list`/`ls`、`preview` 时才执行对应检查，并核对最终 AIX 内确有 `app.json`、该 Page 和资源。AIX 打包不等于商店发布。
3. **受支持的预览**：在 AIUI Studio 的受支持 Web simulation 中以 `_blank` 打开，检查遮罩层级、首尾/空列表、焦点标记和状态文字，并记录宿主实际发出的 down/up 与 `event.code`。浏览器键盘行为和桌面模拟器结果都不是通用运行时事实。
4. **Rokid Glasses 实机**：对目标型号和目标运行时逐项记录 pass/fail：host focus/blur；Backspace 的 down/up（有遮罩只关遮罩，无遮罩走宿主返回）；ArrowUp/Down 的 down/up、边界及焦点始终可见；Enter 只执行一次；设备实际唤醒词能更新状态；世界感知成功后 nod 确认、shake 取消；能力不可用时后备路径有效；退出/卸载后不再收到手势且传感会话已停止。还要在明亮、黑暗、杂乱背景下确认焦点与文字可读。

我不会把设备特有的 `GlobalHook` 映射、浏览器 `KeyboardEvent` 行为或模拟器表现说成所有 AIUI 宿主的保证；只有目标眼镜确实上报且产品需要时，才增加设备分支。官方流程也明确区分 [Web simulation 与实机调试](https://github.com/yodaos-project/AIUI/blob/88e70bb0382525c1a93ef077c2401dcc31a273ce/documentation/0-guide/quickstart/quickstart.md#debug-on-rokid-glasses)。上述实机矩阵未通过前，状态应写“未达到上线门槛”，不能仅凭桌面预览宣称硬件输入或手势已经成功。
