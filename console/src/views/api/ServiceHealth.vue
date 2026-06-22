<template>
  <div class="service-health">
    <h2>服务健康</h2>
    <p>状态、告警、拓扑</p>
    <el-alert type="info" :closable="false">
      查看微服务健康状态、告警信息和依赖拓扑
    </el-alert>
  </div>
</template>

<style scoped>
.service-health {
  padding: 20px;
}
</style>
