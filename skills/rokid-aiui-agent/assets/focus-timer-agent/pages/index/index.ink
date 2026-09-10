<script def>
{
  "navigationBarTitleText": "フォーカスタイマー",
  "description": "集中時間を新しく指定または変更するたびに呼び出します。「25 分集中」「专注 25 分钟」「改成 10 分钟」などの時間を整数秒へ換算し、この Page が表示されている間に計測します。",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "durationSeconds": {
          "type": "integer",
          "minimum": 1,
          "maximum": 3600,
          "default": 600,
          "description": "集中する時間を換算した整数秒。例：25 分は 1500。"
        },
        "label": {
          "type": "string",
          "maxLength": 48,
          "description": "任意の作業名。"
        }
      }
    }
  }
}
</script>

<script setup>
const MAX_DURATION_SECONDS = 3600;
const DEFAULT_DURATION_SECONDS = 600;
const MAX_LABEL_LENGTH = 48;
const REFRESH_INTERVAL_MS = 250;
const DEFAULT_LABEL = 'フォーカスタイマー';

const STATE_CONTENT = {
  idle: {
    statusLabel: '準備完了',
    statusDetail: '開始すると、この画面で集中時間を計測します。',
    nodHint: 'うなずく / タッチパッド：開始'
  },
  running: {
    statusLabel: '集中中',
    statusDetail: '残り時間は実際の終了時刻から計算しています。',
    nodHint: 'うなずく / タッチパッド：一時停止'
  },
  paused: {
    statusLabel: '一時停止',
    statusDetail: '再開するまで残り時間は変わりません。',
    nodHint: 'うなずく / タッチパッド：再開'
  },
  finished: {
    statusLabel: '完了',
    statusDetail: '集中セッションが終了しました。',
    nodHint: 'うなずく / タッチパッド：最初から'
  },
  error: {
    statusLabel: '入力エラー',
    statusDetail: '1～3600 秒の集中時間を会話で指定してください。',
    nodHint: '会話で時間を指定してください'
  }
};

function unicodeLength(value) {
  return Array.from(value).length;
}

function formatTime(remainingMs) {
  const seconds = Math.ceil(Math.max(0, remainingMs) / 1000);
  const minutesPart = Math.floor(seconds / 60);
  const secondsPart = seconds % 60;
  return String(minutesPart).padStart(2, '0') + ':' +
    String(secondsPart).padStart(2, '0');
}

function buildTimerPatch(state, totalMs, remainingMs, deadlineMs) {
  const safeRemaining = Math.max(0, Math.min(totalMs, remainingMs));
  const elapsedRatio = totalMs > 0 ? (totalMs - safeRemaining) / totalMs : 0;
  const content = STATE_CONTENT[state] || STATE_CONTENT.error;
  return {
    state,
    remainingMs: safeRemaining,
    deadlineMs,
    displayTime: formatTime(safeRemaining),
    progressPercent: state === 'finished' ? 100 :
      Math.min(99, Math.floor(elapsedRatio * 100)),
    statusLabel: content.statusLabel,
    statusDetail: content.statusDetail,
    nodHint: content.nodHint,
    focusedAction: ''
  };
}

function normalizeInput(query) {
  const input = query === undefined || query === null ? {} : query;
  if (typeof input !== 'object' || Array.isArray(input)) {
    return { valid: false, durationSeconds: 0, label: DEFAULT_LABEL };
  }
  const durationSeconds = input.durationSeconds === undefined ?
    DEFAULT_DURATION_SECONDS : input.durationSeconds;
  if (
    typeof durationSeconds !== 'number' ||
    !Number.isInteger(durationSeconds) ||
    durationSeconds < 1 ||
    durationSeconds > MAX_DURATION_SECONDS
  ) {
    return { valid: false, durationSeconds: 0, label: DEFAULT_LABEL };
  }
  if (input.label !== undefined && typeof input.label !== 'string') {
    return { valid: false, durationSeconds: 0, label: DEFAULT_LABEL };
  }
  const rawLabel = typeof input.label === 'string' ? input.label : '';
  if (unicodeLength(rawLabel) > MAX_LABEL_LENGTH) {
    return { valid: false, durationSeconds: 0, label: DEFAULT_LABEL };
  }
  return {
    valid: true,
    durationSeconds,
    label: rawLabel.trim() || DEFAULT_LABEL
  };
}

export default {
  data: {
    state: 'error',
    durationSeconds: 0,
    label: DEFAULT_LABEL,
    totalMs: 0,
    remainingMs: 0,
    deadlineMs: 0,
    displayTime: '00:00',
    progressPercent: 0,
    statusLabel: STATE_CONTENT.error.statusLabel,
    statusDetail: STATE_CONTENT.error.statusDetail,
    nodHint: STATE_CONTENT.error.nodHint,
    focusedAction: ''
  },

  onLoad(query) {
    this._refreshTimerId = null;
    this._isVisible = false;
    if (typeof this.enableWorldAwareness === 'function') {
      this.enableWorldAwareness();
    }
    const input = normalizeInput(query);
    if (!input.valid) {
      this.setData({
        durationSeconds: 0,
        label: DEFAULT_LABEL,
        totalMs: 0,
        ...buildTimerPatch('error', 0, 0, 0)
      });
      return;
    }
    const totalMs = input.durationSeconds * 1000;
    this.setData({
      durationSeconds: input.durationSeconds,
      label: input.label,
      totalMs,
      ...buildTimerPatch('idle', totalMs, totalMs, 0)
    });
  },

  onShow() {
    this._isVisible = true;
    if (this.data.state !== 'running') return;
    this._syncRemainingTime();
    if (this.data.state === 'running') this._startRefresh();
  },

  onHide() {
    if (this.data.state === 'running') this._syncRemainingTime();
    this._isVisible = false;
    this._stopRefresh();
  },

  onUnload() {
    this._isVisible = false;
    this._stopRefresh();
  },

  onHeadGesture(event) {
    if (!this._isVisible || !event || event.gesture !== 'nod') return;
    this._runPrimaryAction();
  },

  onKeyUp(event) {
    if (
      !event ||
      (event.code !== 'Enter' && event.code !== 'GlobalHook')
    ) {
      return;
    }
    if (typeof event.preventDefault === 'function') event.preventDefault();
    this._runPrimaryAction();
  },

  _runPrimaryAction() {
    if (this.data.state === 'idle') {
      this.startTimer();
    } else if (this.data.state === 'running') {
      this.pauseTimer();
    } else if (this.data.state === 'paused') {
      this.continueTimer();
    } else if (this.data.state === 'finished') {
      this.restartTimer();
    }
  },

  focusStartAction() {
    this.setData({ focusedAction: 'start' });
  },

  focusPauseAction() {
    this.setData({ focusedAction: 'pause' });
  },

  focusContinueAction() {
    this.setData({ focusedAction: 'continue' });
  },

  focusRestartAction() {
    this.setData({ focusedAction: 'restart' });
  },

  focusResetAction() {
    this.setData({ focusedAction: 'reset' });
  },

  onActionBlur() {
    this.setData({ focusedAction: '' });
  },

  _startRefresh() {
    if (!this._isVisible || this._refreshTimerId !== null) return;
    this._refreshTimerId = setInterval(() => {
      this._syncRemainingTime();
    }, REFRESH_INTERVAL_MS);
  },

  _stopRefresh() {
    if (this._refreshTimerId === null || this._refreshTimerId === undefined) {
      return;
    }
    clearInterval(this._refreshTimerId);
    this._refreshTimerId = null;
  },

  _syncRemainingTime() {
    if (this.data.state !== 'running') return;
    const remainingMs = Math.max(0, this.data.deadlineMs - Date.now());
    if (remainingMs === 0) {
      this._stopRefresh();
      this.setData(buildTimerPatch('finished', this.data.totalMs, 0, 0));
      return;
    }
    this.setData(
      buildTimerPatch(
        'running',
        this.data.totalMs,
        remainingMs,
        this.data.deadlineMs
      )
    );
  },

  startTimer() {
    if (this.data.state !== 'idle') return;
    const deadlineMs = Date.now() + this.data.totalMs;
    this.setData(
      buildTimerPatch(
        'running',
        this.data.totalMs,
        this.data.totalMs,
        deadlineMs
      )
    );
    this._startRefresh();
  },

  pauseTimer() {
    if (this.data.state !== 'running') return;
    this._syncRemainingTime();
    if (this.data.state !== 'running') return;
    this._stopRefresh();
    this.setData(
      buildTimerPatch(
        'paused',
        this.data.totalMs,
        this.data.remainingMs,
        0
      )
    );
  },

  continueTimer() {
    if (this.data.state !== 'paused' || this.data.remainingMs <= 0) return;
    const deadlineMs = Date.now() + this.data.remainingMs;
    this.setData(
      buildTimerPatch(
        'running',
        this.data.totalMs,
        this.data.remainingMs,
        deadlineMs
      )
    );
    this._startRefresh();
  },

  restartTimer() {
    if (
      this.data.durationSeconds < 1 ||
      (this.data.state !== 'running' &&
        this.data.state !== 'paused' &&
        this.data.state !== 'finished')
    ) {
      return;
    }
    this._stopRefresh();
    const deadlineMs = Date.now() + this.data.totalMs;
    this.setData(
      buildTimerPatch(
        'running',
        this.data.totalMs,
        this.data.totalMs,
        deadlineMs
      )
    );
    this._startRefresh();
  },

  resetTimer() {
    if (this.data.durationSeconds < 1) return;
    this._stopRefresh();
    this.setData(
      buildTimerPatch('idle', this.data.totalMs, this.data.totalMs, 0)
    );
  }
};
</script>

<page class="page-shell state-{{state}}">
  <view class="surface">
    <view class="topline">
      <text class="eyebrow">集中</text>
      <text class="state-label expanded-only">{{statusLabel}}</text>
    </view>
    <view class="divider"></view>
    <view class="timer-content">
      <text class="task-label">{{label}}</text>
      <text class="time-value">{{displayTime}}</text>
      <view class="progress-group expanded-only">
        <view class="progress-track">
          <view class="progress-value" style="width: {{progressPercent}}%;"></view>
        </view>
        <view class="progress-meta">
          <text>進捗 {{progressPercent}}%</text>
          <text>設定 {{durationSeconds}}秒</text>
        </view>
      </view>
      <text class="status-detail expanded-only">{{statusDetail}}</text>
      <text class="nod-hint">{{nodHint}}</text>
    </view>
    <view class="actions">
      <button ink:if="{{state === 'idle'}}" class="action action-start action-focused-{{focusedAction}}" bindtap="startTimer" bindfocus="focusStartAction" bindblur="onActionBlur">開始</button>
      <button ink:if="{{state === 'running'}}" class="action action-pause action-focused-{{focusedAction}}" bindtap="pauseTimer" bindfocus="focusPauseAction" bindblur="onActionBlur">一時停止</button>
      <button ink:if="{{state === 'paused'}}" class="action action-continue action-focused-{{focusedAction}}" bindtap="continueTimer" bindfocus="focusContinueAction" bindblur="onActionBlur">再開</button>
      <button ink:if="{{state === 'finished'}}" class="action action-restart action-focused-{{focusedAction}}" bindtap="restartTimer" bindfocus="focusRestartAction" bindblur="onActionBlur">最初から</button>
      <button ink:if="{{state === 'running' || state === 'paused'}}" class="action secondary-action action-restart action-focused-{{focusedAction}}" bindtap="restartTimer" bindfocus="focusRestartAction" bindblur="onActionBlur">最初から</button>
      <button ink:if="{{state !== 'error'}}" class="action secondary-action action-reset action-focused-{{focusedAction}}" bindtap="resetTimer" bindfocus="focusResetAction" bindblur="onActionBlur">リセット</button>
    </view>
  </view>
</page>

<style>
.page-shell {
  width: 100%;
  height: 100%;
  padding: 14px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: #000000;
}

.surface {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  border: 1px solid rgba(64, 255, 94, 0.32);
  border-radius: 6px;
  overflow: hidden;
  opacity: 0.8;
}

.surface:host-focus { opacity: 1; }

.topline,
.progress-meta,
.actions {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.topline,
.progress-meta { justify-content: space-between; }

.eyebrow,
.state-label,
.progress-meta {
  font-size: 11px;
  line-height: 14px;
}

.state-label {
  padding: 3px 6px;
  border: 1px solid rgba(64, 255, 94, 0.26);
  border-radius: 4px;
}

.divider {
  flex-shrink: 0;
  height: 1px;
  margin-top: 10px;
  background-color: rgba(64, 255, 94, 0.24);
}

.timer-content,
.progress-group {
  display: flex;
  flex-direction: column;
}

.timer-content {
  flex: 1 1 auto;
  min-height: 0;
  justify-content: center;
}

.task-label {
  font-size: 16px;
  line-height: 20px;
  color: rgba(184, 255, 195, 0.82);
}

.time-value {
  margin-top: 6px;
  font-size: 52px;
  line-height: 58px;
  color: #b8ffc3;
}

.progress-group { margin-top: 18px; }

.progress-track {
  height: 4px;
  border: 1px solid rgba(64, 255, 94, 0.32);
  border-radius: 4px;
  overflow: hidden;
}

.progress-value {
  height: 100%;
  background-color: #40ff5e;
}

.progress-meta {
  margin-top: 7px;
  color: rgba(64, 255, 94, 0.7);
}

.status-detail {
  margin-top: 12px;
  font-size: 12px;
  line-height: 17px;
  color: rgba(184, 255, 195, 0.76);
}

.nod-hint {
  margin-top: 8px;
  font-size: 12px;
  line-height: 16px;
  color: rgba(64, 255, 94, 0.7);
}

.actions {
  flex-shrink: 0;
  justify-content: flex-start;
  margin-top: auto;
  padding-top: 14px;
}

.action {
  display: flex;
  min-width: 86px;
  margin-right: 8px;
  padding: 7px 10px;
  border: 1px solid rgba(64, 255, 94, 0.56);
  border-radius: 4px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: rgba(64, 255, 94, 0.08);
}

.action-start.action-focused-start,
.action-pause.action-focused-pause,
.action-continue.action-focused-continue,
.action-restart.action-focused-restart,
.action-reset.action-focused-reset {
  border: 2px solid #40ff5e;
  background-color: rgba(64, 255, 94, 0.12);
}

@media (target: _current) {
  .page-shell { padding: 8px; }
  .surface { padding: 12px; }
  .expanded-only { display: none; }
  .secondary-action { display: none; }
  .time-value { font-size: 42px; line-height: 46px; }
}

@media (target: _blank) {
  .expanded-only { display: flex; }
}
</style>
