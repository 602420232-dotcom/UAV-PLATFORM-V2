<template>
  <div class="alert-rules">
    <h2>告警规则</h2>
    <p>阈值、通知、历史</p>
    <el-alert type="info" :closable="false">
      配置告警阈值、通知渠道和查看告警历史
    </el-alert>
  </div>
</template>

<style scoped>
.alert-rules {
  padding: 20px;
}
</style>
