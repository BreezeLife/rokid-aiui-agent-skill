<script def>
{
  "navigationBarTitleText": "AIUI Ready"
}
</script>

<script setup>
export default {
  data: {
    title: 'AIUI project ready',
    detail: 'Import this directory in AIUI Studio'
  }
};
</script>

<page class="page">
  <view class="panel">
    <text class="title">{{title}}</text>
    <text class="detail">{{detail}}</text>
  </view>
</page>

<style>
.page {
  width: 100%;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  color: #40ff5e;
  background-color: #000000;
}

.panel {
  padding: 12px;
  border: 1px solid rgba(64, 255, 94, 0.24);
  border-radius: 6px;
}

.title {
  font-size: 22px;
  font-weight: 500;
}

.detail {
  margin-top: 8px;
  font-size: 14px;
  color: rgba(64, 255, 94, 0.72);
}
</style>
