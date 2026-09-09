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
        }
      },
      "required": ["status"]
    }
  }
}
</script>

<script setup>
export default {
  data: { status: 'invalid' },
  onLoad(query) {
    const status = query && typeof query.status === 'string'
      ? query.status
      : 'invalid';
    this.setData({ status });
  }
};
</script>

<page class="katari-page">
  <view class="marker">
    <text class="brand">KATARI</text>
    <text class="status">{{status}}</text>
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
