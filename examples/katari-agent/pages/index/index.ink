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
    showExpandedDetail: false
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
    return {
      status: 'uncertain',
      ...shared,
      placeNameJa: text(query, 'placeNameJa') || '場所を確認しています',
      placeNameEn: text(query, 'placeNameEn') || 'ONE MORE VIEW',
      recoveryHint: text(query, 'recoveryHint') ||
        '看板と建物全体が一緒に見える向きで、もう一度見せてください。'
    };
  }

  if (query.status === 'no_story') {
    return {
      status: 'no_story',
      ...shared,
      placeNameJa: text(query, 'placeNameJa') || '場所は確認できました',
      placeNameEn: text(query, 'placeNameEn') || 'PLACE CONFIRMED',
      recoveryHint: text(query, 'recoveryHint') ||
        '信頼できる短い物語を確認できないため、ここでは紹介を控えます。'
    };
  }

  return {
    status: 'no_match',
    ...shared,
    placeNameJa: '場所を特定できません',
    placeNameEn: 'NO MATCH',
    recoveryHint: text(query, 'recoveryHint') ||
      'この景色は大阪20地点のカタログと一致しませんでした。'
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
    showExpandedDetail: false
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
  <view class="marker">
    <text class="brand">KATARI</text>
    <text class="place-name">{{placeNameJa}}</text>
    <text class="place-name-en">{{placeNameEn}}</text>
    <text class="recovery-hint">{{recoveryHint}}</text>
  </view>
</page>

<style>
.katari-page {
  width: 100%;
  height: 100%;
  color: #72ff9e;
  background-color: #000000;
}

.marker {
  padding: 30px 36px;
}
</style>
