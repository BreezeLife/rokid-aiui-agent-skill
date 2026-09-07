<script def>
{
  "navigationBarTitleText": "下一步",
  "description": "把用户目标收敛为一个可以立即开始的下一步，并展示当前会话内的行动状态。",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "goal": {
          "type": "string",
          "minLength": 1,
          "maxLength": 120,
          "description": "保留用户真实意图的目标。"
        },
        "nextStep": {
          "type": "string",
          "minLength": 1,
          "maxLength": 48,
          "description": "一个现在可以开始、以动词开头的具体动作。"
        }
      },
      "required": ["goal", "nextStep"]
    }
  }
}
</script>

<script setup>
const MAX_GOAL_LENGTH = 120;
const MAX_NEXT_STEP_LENGTH = 48;

function unicodeLength(value) {
  return Array.from(value).length;
}

const STATE_CONTENT = {
  empty: {
    statusLabel: '等待目标',
    statusTitle: '还没有下一步',
    statusDetail: '回到对话，告诉我你现在想推进什么。',
    primaryText: '先说出一个你想推进的目标'
  },
  error: {
    statusLabel: '需要重试',
    statusTitle: '暂时无法读取行动内容',
    statusDetail: '回到对话重新生成下一步。',
    primaryText: '行动内容格式不正确'
  },
  ready: {
    statusLabel: '准备开始',
    statusTitle: '只做这一件事',
    statusDetail: '开始后保持专注，完成时在这里确认。'
  },
  active: {
    statusLabel: '正在推进',
    statusTitle: '保持在下一步',
    statusDetail: '完成这个动作后再决定下一件事。'
  },
  done: {
    statusLabel: '已经完成',
    statusTitle: '这一步完成了',
    statusDetail: '回到对话告诉我下一件事，或重新开始这一动作。'
  }
};

function buildViewState(state, nextStep) {
  const content = STATE_CONTENT[state] || STATE_CONTENT.error;
  const actionable = state === 'ready' || state === 'active' || state === 'done';
  return {
    state,
    statusLabel: content.statusLabel,
    statusTitle: content.statusTitle,
    statusDetail: content.statusDetail,
    primaryText: actionable ? nextStep : content.primaryText,
    actionFocused: false
  };
}

function normalizeInput(query) {
  if (query === undefined || query === null) {
    return { state: 'empty', goal: '', nextStep: '' };
  }
  if (typeof query !== 'object' || Array.isArray(query)) {
    return { state: 'error', goal: '', nextStep: '' };
  }
  if (
    (query.goal !== undefined && typeof query.goal !== 'string') ||
    (query.nextStep !== undefined && typeof query.nextStep !== 'string')
  ) {
    return { state: 'error', goal: '', nextStep: '' };
  }
  const rawGoal = typeof query.goal === 'string' ? query.goal : '';
  const rawNextStep =
    typeof query.nextStep === 'string' ? query.nextStep : '';
  if (
    unicodeLength(rawGoal) > MAX_GOAL_LENGTH ||
    unicodeLength(rawNextStep) > MAX_NEXT_STEP_LENGTH
  ) {
    return { state: 'error', goal: '', nextStep: '' };
  }
  const goal = rawGoal.trim();
  const nextStep = rawNextStep.trim();
  if (!goal || !nextStep) {
    return { state: 'empty', goal: '', nextStep: '' };
  }
  return {
    state: 'ready',
    goal,
    nextStep
  };
}

export default {
  data: {
    state: 'empty',
    goal: '',
    nextStep: '',
    statusLabel: STATE_CONTENT.empty.statusLabel,
    statusTitle: STATE_CONTENT.empty.statusTitle,
    statusDetail: STATE_CONTENT.empty.statusDetail,
    primaryText: STATE_CONTENT.empty.primaryText,
    actionFocused: false
  },

  onLoad(query) {
    const input = normalizeInput(query);
    this.setData({
      goal: input.goal,
      nextStep: input.nextStep,
      ...buildViewState(input.state, input.nextStep)
    });
  },

  onActionFocus() {
    this.setData({ actionFocused: true });
  },

  onActionBlur() {
    this.setData({ actionFocused: false });
  },

  startTask() {
    if (this.data.state !== 'ready') return;
    this.setData(buildViewState('active', this.data.nextStep));
  },

  completeTask() {
    if (this.data.state !== 'active') return;
    this.setData(buildViewState('done', this.data.nextStep));
  },

  restartTask() {
    if (this.data.state !== 'done') return;
    this.setData(buildViewState('ready', this.data.nextStep));
  }
};
</script>

<page class="page-shell state-{{state}}">
  <view class="surface">
    <view class="topline">
      <text class="eyebrow">NEXT STEP</text>
      <text class="state-label">{{statusLabel}}</text>
    </view>
    <view class="divider"></view>
    <scroll-view class="content" scroll-y="true">
      <text class="status-title">{{statusTitle}}</text>
      <text class="primary-text">{{primaryText}}</text>
      <view class="goal-group expanded-only">
        <text class="section-label">目标</text>
        <text class="goal-text">{{goal}}</text>
      </view>
      <text class="guidance expanded-only">{{statusDetail}}</text>
    </scroll-view>
    <view class="actions">
      <button class="action action-start action-focused-{{actionFocused}}" bindtap="startTask" bindfocus="onActionFocus" bindblur="onActionBlur">开始行动</button>
      <button class="action action-complete action-focused-{{actionFocused}}" bindtap="completeTask" bindfocus="onActionFocus" bindblur="onActionBlur">标记完成</button>
      <button class="action action-restart action-focused-{{actionFocused}}" bindtap="restartTask" bindfocus="onActionFocus" bindblur="onActionBlur">重新开始</button>
    </view>
  </view>
</page>

<style>
.page-shell {
  width: 100%;
  height: 100%;
  padding: 18px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: rgba(0, 0, 0, 0.82);
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
  opacity: 0.78;
}

.surface:host-focus { opacity: 1; }

.topline {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.eyebrow,
.section-label {
  font-size: 11px;
  line-height: 14px;
  color: rgba(64, 255, 94, 0.66);
}

.state-label {
  padding: 3px 6px;
  border: 1px solid rgba(64, 255, 94, 0.24);
  border-radius: 4px;
  font-size: 11px;
  line-height: 14px;
}

.divider {
  flex-shrink: 0;
  height: 1px;
  margin-top: 10px;
  background-color: rgba(64, 255, 94, 0.24);
}

.content,
.goal-group {
  display: flex;
  flex-direction: column;
}

.content {
  flex: 1 1 auto;
  min-height: 0;
  margin-top: 14px;
}
.status-title { font-size: 16px; line-height: 20px; }

.primary-text {
  margin-top: 8px;
  font-size: 22px;
  line-height: 28px;
  color: #b8ffc3;
}

.goal-group {
  margin-top: 18px;
  padding: 10px;
  border: 1px solid rgba(64, 255, 94, 0.18);
  border-radius: 6px;
  background-color: rgba(64, 255, 94, 0.06);
}

.goal-text {
  margin-top: 6px;
  font-size: 13px;
  line-height: 18px;
  color: rgba(184, 255, 195, 0.78);
}

.guidance {
  margin-top: 6px;
  font-size: 13px;
  line-height: 18px;
  color: rgba(184, 255, 195, 0.78);
}

.actions {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  margin-top: auto;
  padding-top: 16px;
}

.action {
  display: none;
  min-width: 112px;
  padding: 7px 12px;
  border: 1px solid rgba(64, 255, 94, 0.54);
  border-radius: 4px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: rgba(64, 255, 94, 0.08);
}

.action-focused-true {
  border: 2px solid #40ff5e;
  background-color: rgba(64, 255, 94, 0.12);
}

.state-ready .action-start,
.state-active .action-complete,
.state-done .action-restart { display: flex; }

.state-empty .goal-group,
.state-error .goal-group { display: none; }

@media (target: _current) {
  .page-shell { padding: 10px; }
  .surface { min-height: 0; padding: 12px; }
  .expanded-only { display: none; }
  .primary-text {
    max-height: 46px;
    font-size: 18px;
    line-height: 23px;
    overflow: hidden;
  }
}

@media (target: _blank) {
  .expanded-only { display: flex; }
}
</style>
