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
    focusedNearbyIndex: -1,
    selectedNearbyName: '',
    selectedNearbyHint: ''
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
    normalized.push({ spotId, name, distanceLabel, directionHint });
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
      focusedNearbyIndex: -1,
      selectedNearbyName: '',
      selectedNearbyHint: ''
    };
  } catch (error) {
    return invalidResult();
  }
}

export default {
  data: invalidResult(),

  onLoad(query) {
    this.setData(normalizeInput(query));
  }
};
</script>

<page class="page">
  <text>セイチ</text>
</page>

<style>
page {
  color: #40ff5e;
  background-color: #000000;
}
</style>
