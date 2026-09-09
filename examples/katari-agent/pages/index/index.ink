<script def>
{
  "navigationBarTitleText": "KATARI",
  "description": "Show one short, source-traceable Osaka local story.",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string",
          "enum": ["matched", "uncertain", "no_story", "no_match", "invalid"]
        },
        "spotId": { "type": "string", "maxLength": 48 },
        "placeNameJa": { "type": "string", "maxLength": 48 },
        "placeNameEn": { "type": "string", "maxLength": 64 },
        "localityLabel": { "type": "string", "maxLength": 48 },
        "storyDurationSeconds": {
          "type": "integer",
          "minimum": 15,
          "maximum": 30
        },
        "memoryHook": { "type": "string", "maxLength": 140 },
        "confidenceLabel": { "type": "string", "maxLength": 64 },
        "evidenceNote": { "type": "string", "maxLength": 160 },
        "knowledgeKind": {
          "type": "string",
          "enum": ["fact", "legend", "tradition"]
        },
        "recoveryHint": { "type": "string", "maxLength": 160 }
      },
      "required": ["status"]
    }
  }
}
</script>

<script setup>
const LIMITS = {
  spotId: 48,
  placeNameJa: 48,
  placeNameEn: 64,
  localityLabel: 48,
  memoryHook: 140,
  confidenceLabel: 64,
  evidenceNote: 160,
  recoveryHint: 160
};

const VALID_STATUSES = new Set([
  'matched',
  'uncertain',
  'no_story',
  'no_match',
  'invalid'
]);
const KNOWLEDGE_LABELS = {
  fact: 'FACT',
  legend: 'LEGEND',
  tradition: 'TRADITION'
};

function unicodeLength(value) {
  return Array.from(value).length;
}

function safeInvalidState() {
  return {
    status: 'invalid',
    spotId: '',
    placeNameJa: '場所を見せてください',
    placeNameEn: 'LOOK AT A LANDMARK',
    localityLabel: '',
    storyDurationSeconds: 0,
    memoryHook: '',
    confidenceLabel: 'KATARI',
    evidenceNote: '',
    knowledgeKind: 'fact',
    knowledgeLabel: '',
    recoveryHint: '建物や看板が見える向きでもう一度聞いてください。',
    showStoryMeta: false,
    showExpandedDetail: false,
    nameDensity: 'regular'
  };
}

function stringsAreBounded(query) {
  return Object.entries(LIMITS).every(([field, maximum]) => {
    const value = query[field];
    return value === undefined || (
      typeof value === 'string' && unicodeLength(value) <= maximum
    );
  });
}

function text(query, field) {
  return typeof query[field] === 'string' ? query[field].trim() : '';
}

function identityDensity(placeNameJa, placeNameEn) {
  return unicodeLength(placeNameJa) > 24 || unicodeLength(placeNameEn) > 48
    ? 'compact'
    : 'regular';
}

function recoveryState(query) {
  const shared = {
    spotId: text(query, 'spotId'),
    localityLabel: text(query, 'localityLabel'),
    storyDurationSeconds: 0,
    memoryHook: '',
    confidenceLabel: text(query, 'confidenceLabel') || 'KATARI',
    evidenceNote: text(query, 'evidenceNote'),
    knowledgeKind: 'fact',
    knowledgeLabel: '',
    showStoryMeta: false,
    showExpandedDetail: false
  };

  if (query.status === 'uncertain') {
    const result = {
      status: 'uncertain',
      ...shared,
      placeNameJa: text(query, 'placeNameJa') || '場所を確認しています',
      placeNameEn: text(query, 'placeNameEn') || 'ONE MORE VIEW',
      recoveryHint: text(query, 'recoveryHint') ||
        '看板と建物全体が一緒に見える向きで、もう一度見せてください。'
    };
    return {
      ...result,
      nameDensity: identityDensity(result.placeNameJa, result.placeNameEn)
    };
  }

  if (query.status === 'no_story') {
    const result = {
      status: 'no_story',
      ...shared,
      placeNameJa: text(query, 'placeNameJa') || '場所は確認できました',
      placeNameEn: text(query, 'placeNameEn') || 'PLACE CONFIRMED',
      recoveryHint: text(query, 'recoveryHint') ||
        '信頼できる短い物語を確認できないため、ここでは紹介を控えます。'
    };
    return {
      ...result,
      nameDensity: identityDensity(result.placeNameJa, result.placeNameEn)
    };
  }

  const result = {
    status: 'no_match',
    ...shared,
    placeNameJa: '場所を特定できません',
    placeNameEn: 'NO MATCH',
    recoveryHint: text(query, 'recoveryHint') ||
      'この景色は大阪20地点のカタログと一致しませんでした。'
  };
  return {
    ...result,
    nameDensity: identityDensity(result.placeNameJa, result.placeNameEn)
  };
}

function normalizeInput(query) {
  if (
    query === undefined ||
    query === null ||
    typeof query !== 'object' ||
    Array.isArray(query) ||
    typeof query.status !== 'string' ||
    !VALID_STATUSES.has(query.status)
  ) {
    return safeInvalidState();
  }

  if (query.status === 'invalid') {
    return safeInvalidState();
  }

  if (!stringsAreBounded(query)) {
    return safeInvalidState();
  }

  if (query.status !== 'matched') {
    return recoveryState(query);
  }

  const duration = query.storyDurationSeconds;
  const knowledgeKind = query.knowledgeKind;
  if (
    !text(query, 'spotId') ||
    !text(query, 'placeNameJa') ||
    !text(query, 'placeNameEn') ||
    !Number.isInteger(duration) ||
    duration < 15 ||
    duration > 30 ||
    !Object.prototype.hasOwnProperty.call(KNOWLEDGE_LABELS, knowledgeKind)
  ) {
    return safeInvalidState();
  }

  return {
    status: 'matched',
    spotId: text(query, 'spotId'),
    placeNameJa: text(query, 'placeNameJa'),
    placeNameEn: text(query, 'placeNameEn'),
    localityLabel: text(query, 'localityLabel'),
    storyDurationSeconds: duration,
    memoryHook: text(query, 'memoryHook'),
    confidenceLabel: text(query, 'confidenceLabel') || 'KATARI',
    evidenceNote: text(query, 'evidenceNote'),
    knowledgeKind,
    knowledgeLabel: KNOWLEDGE_LABELS[knowledgeKind],
    recoveryHint: '',
    showStoryMeta: true,
    showExpandedDetail: false,
    nameDensity: identityDensity(
      text(query, 'placeNameJa'),
      text(query, 'placeNameEn')
    )
  };
}

export default {
  data: safeInvalidState(),

  onLoad(query) {
    this.setData(normalizeInput(query));
  }
};
</script>

<page class="katari-page state-{{status}}">
  <view class="quiet-marker">
    <view class="topline">
      <text class="eyebrow">KATARI / LOCAL MEMORY</text>
      <text class="status-code">{{confidenceLabel}}</text>
    </view>

    <view class="divider"></view>

    <view class="identity">
      <text class="place-name-ja name-density-{{nameDensity}}">{{placeNameJa}}</text>
      <text class="place-name-en name-density-{{nameDensity}}">{{placeNameEn}}</text>
      <text class="locality">{{localityLabel}}</text>
    </view>

    <view ink:if="{{showStoryMeta}}" class="matched-content">
      <view class="story-row">
        <view class="status-dot"></view>
        <text class="story-duration">LOCAL STORY · {{storyDurationSeconds}} SEC</text>
      </view>

      <view class="detail-group expanded-only">
        <text class="detail-label">REMEMBER THIS</text>
        <text class="memory-hook">{{memoryHook}}</text>
        <view class="evidence-row">
          <text class="knowledge-label">{{knowledgeLabel}}</text>
          <text class="evidence-note">{{evidenceNote}}</text>
        </view>
      </view>
    </view>

    <view ink:if="{{!showStoryMeta}}" class="recovery-content">
      <text class="recovery-label">{{confidenceLabel}}</text>
      <text class="recovery-hint">{{recoveryHint}}</text>
      <text class="evidence-note expanded-only">{{evidenceNote}}</text>
    </view>
  </view>
</page>

<style>
.katari-page {
  width: 100%;
  height: 100%;
  padding: 30px 36px;
  box-sizing: border-box;
  color: #72ff9e;
  background-color: #000000;
}

.quiet-marker {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  box-sizing: border-box;
}

.topline,
.story-row,
.evidence-row {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.topline {
  justify-content: space-between;
  flex-shrink: 0;
  min-width: 0;
}

.eyebrow,
.status-code,
.detail-label,
.knowledge-label,
.recovery-label {
  font-size: 10px;
  line-height: 13px;
  letter-spacing: 1px;
  color: rgba(114, 255, 158, 0.64);
}

.status-code {
  max-width: 180px;
  margin-left: 12px;
  overflow: hidden;
  text-align: right;
}

.divider {
  flex-shrink: 0;
  margin-top: 10px;
  border-top: 1px solid rgba(114, 255, 158, 0.24);
}

.identity,
.matched-content,
.recovery-content,
.detail-group {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.identity {
  flex-shrink: 0;
  margin-top: 18px;
}

.place-name-ja {
  max-height: 68px;
  overflow: hidden;
  font-size: 30px;
  line-height: 34px;
  font-weight: 500;
  color: #72ff9e;
}

.place-name-en {
  max-height: 36px;
  margin-top: 5px;
  overflow: hidden;
  font-size: 14px;
  line-height: 18px;
  color: rgba(114, 255, 158, 0.78);
}

.name-density-compact.place-name-ja {
  max-height: 72px;
  font-size: 20px;
  line-height: 24px;
}

.name-density-compact.place-name-en {
  max-height: 32px;
  font-size: 12px;
  line-height: 16px;
}

.locality {
  max-height: 16px;
  margin-top: 3px;
  overflow: hidden;
  font-size: 11px;
  line-height: 15px;
  color: rgba(114, 255, 158, 0.48);
}

.matched-content,
.recovery-content {
  margin-top: auto;
  padding-top: 18px;
}

.story-row { flex-shrink: 0; }

.status-dot {
  width: 6px;
  height: 6px;
  margin-right: 8px;
  border-radius: 6px;
  background-color: #72ff9e;
}

.story-duration {
  font-size: 12px;
  line-height: 16px;
  letter-spacing: 0.7px;
  color: rgba(114, 255, 158, 0.82);
}

.detail-group {
  margin-top: 14px;
  padding: 10px 12px;
  border-radius: 6px;
  background-color: rgba(114, 255, 158, 0.055);
}

.memory-hook {
  max-height: 40px;
  margin-top: 5px;
  overflow: hidden;
  font-size: 15px;
  line-height: 20px;
  color: rgba(114, 255, 158, 0.92);
}

.evidence-row {
  min-width: 0;
  margin-top: 9px;
}

.knowledge-label {
  flex-shrink: 0;
  margin-right: 10px;
  color: rgba(114, 255, 158, 0.76);
}

.evidence-note {
  max-height: 30px;
  overflow: hidden;
  font-size: 10px;
  line-height: 14px;
  color: rgba(114, 255, 158, 0.46);
}

.recovery-label { color: rgba(114, 255, 158, 0.76); }

.recovery-hint {
  max-height: 42px;
  margin-top: 7px;
  overflow: hidden;
  font-size: 13px;
  line-height: 19px;
  color: rgba(114, 255, 158, 0.72);
}

.state-uncertain .status-dot,
.state-no_story .status-dot,
.state-no_match .status-dot,
.state-invalid .status-dot {
  background-color: transparent;
}

@media (target: _current) {
  .katari-page { padding: 30px 36px; }
  .expanded-only { display: none; }
  .place-name-ja { font-size: 28px; line-height: 32px; }
}

@media (target: _blank) {
  .expanded-only { display: flex; }
}
</style>
