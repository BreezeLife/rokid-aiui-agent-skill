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

function normalizeNearby(value) {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > 3) return null;

  const normalized = [];
  for (const item of value) {
    if (item === null || typeof item !== 'object' || Array.isArray(item)) {
      return null;
    }
    const keys = Object.keys(item);
    if (
      keys.length !== NEARBY_FIELDS.length ||
      !NEARBY_FIELDS.every((field) => keys.includes(field))
    ) {
      return null;
    }

    const spotId = boundedString(item.spotId, LIMITS.spotId);
    const name = boundedString(item.name, LIMITS.nearbyName);
    const distanceLabel = boundedString(
      item.distanceLabel,
      LIMITS.distanceLabel
    );
    const directionHint = boundedString(
      item.directionHint,
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
  if (query === null || typeof query !== 'object' || Array.isArray(query)) {
    return invalidResult();
  }
  if (!STATUSES.includes(query.status) || query.status === 'invalid') {
    return invalidResult();
  }

  const strings = {};
  for (const field of RESULT_STRING_FIELDS) {
    const value = query[field] === undefined
      ? ''
      : boundedString(query[field], LIMITS[field]);
    if (value === null) return invalidResult();
    strings[field] = value;
  }
  const nearbySpots = normalizeNearby(query.nearbySpots);
  if (nearbySpots === null) return invalidResult();

  if (
    query.status === 'matched' &&
    (!strings.workTitle ||
      !strings.episodeScene ||
      !strings.storyLine ||
      !strings.photoGuidance)
  ) {
    return invalidResult();
  }
  if (query.status === 'uncertain' && !strings.photoGuidance) {
    return invalidResult();
  }

  return {
    state: query.status,
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
