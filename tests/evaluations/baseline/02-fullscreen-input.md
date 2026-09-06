# Baseline Response: Full-screen Multimodal Input

- Scenario: `tests/scenarios/02-fullscreen-input.md`
- Conditions: fresh subagent, no web access, no workspace inspection, no AIUI-specific Skill
- Captured: 2026-09-07

## Verbatim response

按键动作放在 `onKeyDown` 保证即时响应；但宿主的返回、滚动和激活默认行为发生在 `onKeyUp`，必须在那里再次拦截，否则会“双执行”。合并到任务页 `.ink`：

```ink
<script setup>
export default {
  data: {
    tasks: [],                 // 保留现有任务数据
    focusedIndex: 0,
    focusedId: 'task-0',
    maskOpen: false,
    status: '就绪'
  },

  onLoad() {
    this._owned = Object.create(null);
    this._down = Object.create(null);
    try {
      this.enableWorldAwareness({ mode: 'normal' });
    } catch (_) {
      this.setData({ status: '头部手势不可用' });
    }
  },

  onKeyDown(e) {
    const k = e.code;

    if (this.data.maskOpen) {
      if (k === 'Backspace' || k === 'ArrowUp' ||
          k === 'ArrowDown' || k === 'Enter') {
        e.preventDefault();
        this._owned[k] = true;
      }
      if (k === 'Backspace' && !this._down[k]) {
        this.setData({ maskOpen: false, status: '已关闭遮罩' });
      }
      this._down[k] = true;
      return;
    }

    if (k === 'ArrowUp' || k === 'ArrowDown' || k === 'Enter') {
      e.preventDefault();
      this._owned[k] = true;
      if (this._down[k]) return;
      this._down[k] = true;

      if (k === 'ArrowUp') this.moveFocus(-1);
      if (k === 'ArrowDown') this.moveFocus(1);
      if (k === 'Enter') this.executeCurrent('key');
    }
    // 无遮罩时不接管 Backspace，保留系统返回能力
  },

  onKeyUp(e) {
    if (this._owned[e.code]) {
      e.preventDefault();
      delete this._owned[e.code];
    }
    delete this._down[e.code];
  },

  moveFocus(step) {
    const max = this.data.tasks.length - 1;
    if (max < 0) return;
    const index = Math.max(0, Math.min(max, this.data.focusedIndex + step));
    this.setData({ focusedIndex: index, focusedId: `task-${index}` });
  },

  executeCurrent(source) {
    const item = this.data.tasks[this.data.focusedIndex];
    if (!item) return;
    this.postMessage({ type: 'task.execute', payload: { item, source } });
    this.setData({ status: `执行：${item.title}` });
  },

  cancelCurrent(source) {
    const item = this.data.tasks[this.data.focusedIndex];
    if (!item) return;
    this.postMessage({ type: 'task.cancel', payload: { item, source } });
    this.setData({ maskOpen: false, status: `取消：${item.title}` });
  },

  onVoiceWakeup(e) {
    this.setData({ status: `已唤醒：${e.keyword || 'leqi'}` });
  },

  onHeadGesture(e) {
    if (e.gesture === 'nod') this.executeCurrent('nod');
    if (e.gesture === 'shake') this.cancelCurrent('shake');
  }
};
</script>

<page>
  <view class="page">
    <text>{{status}}</text>
    <scroll-view scroll-y="true" scroll-into-view="{{focusedId}}">
      <view ink:for="{{tasks}}" ink:key="id"
        id="task-{{index}}"
        class="task {{index === focusedIndex ? 'focused' : ''}}">
        {{item.title}}
      </view>
    </scroll-view>
    <view ink:if="{{maskOpen}}" class="mask">处理中…</view>
  </view>
</page>

<style>
.task { padding: 16px; }
.focused { border: 2px solid #fff; background: #333; }
.mask { position: fixed; inset: 0; background: rgba(0,0,0,.75); }
</style>
```

上线前真机验证：遮罩开启按 Backspace 只关遮罩且页面不退出；关闭遮罩后 Backspace 正常返回；方向键逐项移动且根视图不额外滚动；Enter 每次按压只发一条 `task.execute`；唤醒词更新状态；点头执行、摇头取消；连续快速按键无重复执行。宿主还需启用 World Awareness/方向传感器能力。
