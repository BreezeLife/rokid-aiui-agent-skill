<script def>
{
  "navigationBarTitleText": "セイチ",
  "description": "聖地照合結果を短く表示します。",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string",
          "enum": ["matched", "uncertain", "no_match", "invalid"]
        },
        "workTitle": {
          "type": "string",
          "maxLength": 64
        },
        "episodeScene": {
          "type": "string",
          "maxLength": 72
        },
        "storyLine": {
          "type": "string",
          "maxLength": 100
        },
        "photoGuidance": {
          "type": "string",
          "maxLength": 80
        },
        "confidenceLabel": {
          "type": "string",
          "maxLength": 16
        },
        "nearbySpots": {
          "type": "array",
          "maxItems": 3,
          "items": {
            "type": "object",
            "properties": {
              "spotId": {
                "type": "string",
                "maxLength": 40
              },
              "name": {
                "type": "string",
                "maxLength": 48
              },
              "distanceLabel": {
                "type": "string",
                "maxLength": 16
              },
              "directionHint": {
                "type": "string",
                "maxLength": 48
              }
            },
            "required": ["spotId", "name", "distanceLabel", "directionHint"],
            "additionalProperties": false
          }
        }
      },
      "required": ["status"],
      "additionalProperties": false
    }
  }
}
</script>

<script setup>
const LIMITS = {
  workTitle: 64,
  episodeScene: 72,
  storyLine: 100,
  photoGuidance: 80,
  confidenceLabel: 16,
  spotId: 40,
  nearbyName: 48,
  distanceLabel: 16,
  directionHint: 48
};

const STATUSES = ['matched', 'uncertain', 'no_match', 'invalid'];
const RESULT_STRING_FIELDS = [
  'workTitle',
  'episodeScene',
  'storyLine',
  'photoGuidance',
  'confidenceLabel'
];
const NEARBY_FIELDS = ['spotId', 'name', 'distanceLabel', 'directionHint'];
const ROOT_FIELDS = ['status', ...RESULT_STRING_FIELDS, 'nearbySpots'];

function unicodeLength(value) {
  return Array.from(value).length;
}

function boundedString(value, limit) {
  if (typeof value !== 'string' || unicodeLength(value) > limit) return null;
  return value.trim();
}

function invalidResult() {
  return {
    state: 'invalid',
    workTitle: '場所を確認できません',
    episodeScene: '',
    storyLine: '作品名または場所を変えて、もう一度聞いてください。',
    photoGuidance: '会話に戻って再確認してください。',
    confidenceLabel: '入力不足',
    nearbySpots: [],
    selectedNearbyIndex: -1,
    focusedNearbyIndex: -1
  };
}

function isRecord(value) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function normalizeNearby(value) {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > 3) return null;

  const normalized = [];
  for (const item of value) {
    if (!isRecord(item)) return null;
    const keys = Object.keys(item);
    if (
      keys.length !== NEARBY_FIELDS.length ||
      !NEARBY_FIELDS.every((field) => keys.includes(field))
    ) {
      return null;
    }

    const rawSpotId = item.spotId;
    const rawName = item.name;
    const rawDistanceLabel = item.distanceLabel;
    const rawDirectionHint = item.directionHint;
    const spotId = boundedString(rawSpotId, LIMITS.spotId);
    const name = boundedString(rawName, LIMITS.nearbyName);
    const distanceLabel = boundedString(
      rawDistanceLabel,
      LIMITS.distanceLabel
    );
    const directionHint = boundedString(
      rawDirectionHint,
      LIMITS.directionHint
    );
    if (
      !spotId ||
      !name ||
      distanceLabel === null ||
      !directionHint
    ) {
      return null;
    }
    normalized.push({
      spotId,
      name,
      distanceLabel,
      directionHint,
      focused: false,
      selected: false
    });
  }
  return normalized;
}

function normalizeInput(query) {
  try {
    if (!isRecord(query)) return invalidResult();
    const keys = Object.keys(query);
    if (
      !keys.includes('status') ||
      !keys.every((field) => ROOT_FIELDS.includes(field))
    ) {
      return invalidResult();
    }

    const status = query.status;
    if (!STATUSES.includes(status) || status === 'invalid') {
      return invalidResult();
    }

    const strings = {};
    for (const field of RESULT_STRING_FIELDS) {
      if (!keys.includes(field)) {
        strings[field] = '';
        continue;
      }
      const rawValue = query[field];
      const value = boundedString(rawValue, LIMITS[field]);
      if (value === null) return invalidResult();
      strings[field] = value;
    }

    let nearbySpots = [];
    if (keys.includes('nearbySpots')) {
      const rawNearbySpots = query.nearbySpots;
      nearbySpots = normalizeNearby(rawNearbySpots);
      if (nearbySpots === null || rawNearbySpots === undefined) {
        return invalidResult();
      }
    }

    if (
      status === 'matched' &&
      (!strings.workTitle ||
        !strings.episodeScene ||
        !strings.storyLine ||
        !strings.photoGuidance)
    ) {
      return invalidResult();
    }
    if (status === 'uncertain' && !strings.photoGuidance) {
      return invalidResult();
    }

    return {
      state: status,
      workTitle: strings.workTitle,
      episodeScene: strings.episodeScene,
      storyLine: strings.storyLine,
      photoGuidance: strings.photoGuidance,
      confidenceLabel: strings.confidenceLabel,
      nearbySpots,
      selectedNearbyIndex: -1,
      focusedNearbyIndex: -1
    };
  } catch (error) {
    return invalidResult();
  }
}

export default {
  data: invalidResult(),

  onLoad(query) {
    this.setData(normalizeInput(query));
  },

  eventIndex(event) {
    try {
      if (event === null || typeof event !== 'object') return -1;
      const currentTarget = event.currentTarget;
      if (currentTarget === null || typeof currentTarget !== 'object') return -1;
      const dataset = currentTarget.dataset;
      if (dataset === null || typeof dataset !== 'object') return -1;
      const index = dataset.index;
      if (!Number.isInteger(index)) return -1;
      const nearbySpots = this.data.nearbySpots;
      if (!Array.isArray(nearbySpots)) return -1;
      if (index < 0 || index >= nearbySpots.length) return -1;
      return index;
    } catch (error) {
      return -1;
    }
  },

  focusNearby(event) {
    const index = this.eventIndex(event);
    if (index < 0) return;
    const nearbySpots = this.data.nearbySpots.map((nearby, nearbyIndex) => ({
      ...nearby,
      focused: nearbyIndex === index
    }));
    this.setData({ focusedNearbyIndex: index, nearbySpots });
  },

  blurNearby(event) {
    const index = this.eventIndex(event);
    if (index < 0) return;
    const nearbySpots = this.data.nearbySpots.map((nearby) => ({
      ...nearby,
      focused: false
    }));
    this.setData({ focusedNearbyIndex: -1, nearbySpots });
  },

  selectNearby(event) {
    const index = this.eventIndex(event);
    if (index < 0) return;
    try {
      const nearby = this.data.nearbySpots[index];
      if (
        typeof nearby.name !== 'string' ||
        typeof nearby.directionHint !== 'string'
      ) return;
      const nearbySpots = this.data.nearbySpots.map(
        (item, nearbyIndex) => ({
          ...item,
          selected: nearbyIndex === index
        })
      );
      this.setData({
        selectedNearbyIndex: index,
        nearbySpots
      });
    } catch (error) {
      return;
    }
  }
};
</script>

<page class="page-shell state-{{state}}">
  <view class="result-group">
    <view class="topline">
      <text class="wordmark">SEICHI</text>
      <text class="confidence">{{confidenceLabel}}</text>
    </view>

    <view class="state-row">
      <text class="state-label" ink:if="{{state === 'matched'}}">一致</text>
      <text class="state-label" ink:elif="{{state === 'uncertain'}}">要確認</text>
      <text class="state-label" ink:elif="{{state === 'no_match'}}">登録なし</text>
      <text class="state-label" ink:else>入力不足</text>
    </view>

    <view class="core-answer">
      <text class="work-title">{{workTitle}}</text>
      <text class="episode-scene" ink:if="{{state !== 'invalid'}}">{{episodeScene}}</text>
      <text class="story-line" ink:if="{{state !== 'invalid'}}">{{storyLine}}</text>
      <text class="fallback-copy" ink:if="{{state === 'no_match'}}">登録カタログに一致する候補はありません。ほかの作品への登場は否定できません。</text>
      <view class="photo-guide">
        <text class="section-label">PHOTO GUIDE</text>
        <text class="photo-copy" ink:if="{{photoGuidance.length > 0}}">{{photoGuidance}}</text>
        <text class="photo-copy" ink:else>安全な場所で見え方を確認してください。</text>
      </view>
    </view>

    <scroll-view class="result-scroll expanded-only" scroll-y="true">
      <view class="nearby-list">
        <text class="section-label">NEARBY</text>
        <button
          class="nearby-button nearby-focused-{{item.focused}} nearby-selected-{{item.selected}}"
          ink:for="{{nearbySpots}}"
          ink:key="spotId"
          data-index="{{index}}"
          bindtap="selectNearby"
          bindfocus="focusNearby"
          bindblur="blurNearby"
        >
          <view class="nearby-line">
            <text class="nearby-name">{{item.name}}</text>
            <text class="nearby-distance">{{item.distanceLabel}}</text>
          </view>
          <text class="nearby-direction" ink:if="{{item.selected}}">{{item.directionHint}}</text>
        </button>
        <text class="nearby-empty" ink:if="{{nearbySpots.length === 0}}">近隣候補はありません。</text>
      </view>
    </scroll-view>
  </view>
</page>

<style>
.page-shell {
  width: 100%;
  height: 100%;
  padding: 10px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: #000000;
}

.result-group {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  padding: 12px;
  box-sizing: border-box;
  border: 1px solid rgba(64, 255, 94, 0.32);
  border-radius: 6px;
  overflow: hidden;
}

.topline,
.state-row,
.nearby-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.topline {
  justify-content: space-between;
  flex-shrink: 0;
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(64, 255, 94, 0.24);
}

.wordmark,
.section-label {
  font-size: 11px;
  line-height: 14px;
  letter-spacing: 1px;
  color: rgba(64, 255, 94, 0.72);
}

.confidence {
  padding: 2px 6px;
  border: 1px solid rgba(64, 255, 94, 0.32);
  border-radius: 4px;
  font-size: 11px;
  line-height: 14px;
}

.state-row {
  flex-shrink: 0;
  margin-top: 9px;
}

.state-label {
  min-width: 48px;
  font-size: 12px;
  line-height: 16px;
}

.fallback-copy {
  margin-top: 5px;
  font-size: 11px;
  line-height: 15px;
  color: rgba(184, 255, 195, 0.82);
}

.result-scroll,
.core-answer,
.nearby-list,
.nearby-button,
.photo-guide {
  display: flex;
  flex-direction: column;
}

.result-scroll {
  flex: 1 1 auto;
  min-height: 0;
  margin-top: 8px;
}

.core-answer {
  flex-shrink: 0;
  margin-top: 5px;
}

.work-title {
  font-size: 15px;
  line-height: 19px;
  color: #b8ffc3;
}

.episode-scene,
.story-line,
.photo-copy,
.nearby-direction,
.nearby-empty {
  font-size: 11px;
  line-height: 15px;
  color: rgba(184, 255, 195, 0.82);
}

.episode-scene { margin-top: 2px; }
.story-line { margin-top: 3px; }

.nearby-list {
  margin-top: 14px;
  padding-bottom: 6px;
}

.nearby-button {
  align-items: stretch;
  width: 100%;
  margin-top: 6px;
  padding: 6px 8px;
  box-sizing: border-box;
  border: 1px solid rgba(64, 255, 94, 0.46);
  border-radius: 4px;
  color: #40ff5e;
  background-color: rgba(64, 255, 94, 0.06);
}

.nearby-focused-true {
  border: 2px solid #40ff5e;
  background-color: rgba(64, 255, 94, 0.12);
}

.nearby-selected-true {
  background-color: rgba(64, 255, 94, 0.12);
}

.nearby-line {
  justify-content: space-between;
  width: 100%;
}

.nearby-name {
  font-size: 12px;
  line-height: 16px;
}

.nearby-distance {
  margin-left: 8px;
  font-size: 11px;
  line-height: 15px;
  color: rgba(184, 255, 195, 0.72);
}

.nearby-empty { margin-top: 6px; }

.nearby-direction {
  margin-top: 5px;
  padding-top: 4px;
  border-top: 1px solid rgba(64, 255, 94, 0.24);
}

.photo-guide {
  flex-shrink: 0;
  margin-top: 6px;
  padding-top: 5px;
  border-top: 1px solid rgba(64, 255, 94, 0.24);
}

.photo-copy { margin-top: 2px; }

@media (target: _current) {
  .expanded-only { display: none; }
  .result-group { padding: 10px; }
}

@media (target: _blank) {
  .expanded-only { display: flex; }
}
</style>
