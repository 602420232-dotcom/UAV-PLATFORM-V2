<template>
  <div class="api-config">
    <div class="page-title">气象模型 API 配置</div>

    <el-alert
      v-if="!editable"
      type="info"
      :closable="false"
      show-icon
      title="权限提示"
      description="您的角色仅拥有查看权限，如需修改请联系管理员"
      class="demo-alert"
    />
    <el-alert
      v-else
      type="warning"
      :closable="false"
      show-icon
      title="演示环境"
      description="演示环境，您的修改将保存在浏览器会话中，不会影响线上服务"
      class="demo-alert"
    />

    <div class="top-action-bar" v-if="editable">
      <el-button type="primary" @click="handleSave">保存</el-button>
      <el-button @click="handleExportJson">导出 JSON</el-button>
      <el-button type="danger" :disabled="config.mode === 'prod'" @click="handleSwitchMode">
        切换到生产模式
      </el-button>
      <el-tag v-if="config.mode === 'prod'" type="danger" effect="dark" size="small">
        已锁定：生产模式不可逆向切换
      </el-tag>
    </div>

    <!-- 二、服务总览 -->
    <el-card class="section-card overview-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">🌐</span>
          <span>API 服务总览</span>
          <el-tag :type="config.mode === 'prod' ? 'danger' : 'warning'" effect="light" size="small">
            {{ config.mode === 'prod' ? '生产模式' : '演示模式' }}
          </el-tag>
        </div>
      </template>

      <div class="overview">
        <div class="overview-main">
          <div class="overview-title">
            当前接入服务：
            <b>{{ configuredCount }} / {{ totalCount }}</b>
          </div>
          <div class="overview-desc">
            包含 4 个气象模型、Model Engine、API Gateway、边云协同、WRF 处理器、以及数据库连接。
          </div>
        </div>

        <el-progress
          :percentage="Math.round((configuredCount / totalCount) * 100)"
          :stroke-width="16"
          color="#409EFF"
          class="overview-progress"
        />
      </div>

      <div class="overview-footer">
        <el-tag :type="config.mode === 'prod' ? 'danger' : 'warning'" effect="light">
          {{ config.mode === 'prod' ? '生产模式' : '演示模式' }}
        </el-tag>
      </div>
    </el-card>

    <!-- 三、气象模型（4 张并排卡片） -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">🌀</span>
          <span>气象模型</span>
          <el-tag type="warning" size="small" effect="plain">4 个子模型</el-tag>
        </div>
      </template>

      <el-row :gutter="16" class="model-row">
        <!-- 1. 天资 TianZi Service (8090) -->
        <el-col :xs="24" :md="12" :lg="6" :xl="6">
          <div class="model-card tianzi">
            <div class="model-title">天资 TianZi Service</div>
            <div class="model-subtitle">8090 · 双重认证（API Key + JWT）</div>
            <el-form :model="config.tianzi" label-width="140px" size="small" class="model-form">
              <el-form-item label="服务地址 host">
                <el-input v-model="config.tianzi.host" :disabled="!editable" placeholder="tianzi.internal" />
              </el-form-item>
              <el-form-item label="端口 port">
                <el-input-number
                  v-model="config.tianzi.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="config.tianzi.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
              </el-form-item>
              <el-form-item label="JWT Secret">
                <el-input v-model="config.tianzi.jwtSecret" :disabled="!editable" show-password placeholder="JWT Secret" />
              </el-form-item>
              <el-form-item label="超时（秒）">
                <el-input-number
                  v-model="config.tianzi.timeout"
                  :min="1"
                  :max="600"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="健康检查路径">
                <el-input v-model="config.tianzi.healthPath" :disabled="!editable" placeholder="/health" />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.tianzi.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 2. 风雷 FengLei Service (8091) -->
        <el-col :xs="24" :md="12" :lg="6" :xl="6">
          <div class="model-card fenglei">
            <div class="model-title">风雷 FengLei Service</div>
            <div class="model-subtitle">8091 · 雷暴短临 / 雷达外推</div>
            <el-form :model="config.fenglei" label-width="140px" size="small" class="model-form">
              <el-form-item label="服务地址 host">
                <el-input v-model="config.fenglei.host" :disabled="!editable" placeholder="fenglei.internal" />
              </el-form-item>
              <el-form-item label="端口 port">
                <el-input-number
                  v-model="config.fenglei.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="config.fenglei.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
              </el-form-item>
              <el-form-item label="超时（秒）">
                <el-input-number
                  v-model="config.fenglei.timeout"
                  :min="1"
                  :max="600"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="健康检查路径">
                <el-input v-model="config.fenglei.healthPath" :disabled="!editable" placeholder="/health" />
              </el-form-item>
              <el-form-item label="更新频率（分钟）">
                <el-input-number
                  v-model="config.fenglei.updateFreq"
                  :min="1"
                  :max="120"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.fenglei.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 3. 风乌 FengWu (8085) -->
        <el-col :xs="24" :md="12" :lg="6" :xl="6">
          <div class="model-card fengwu">
            <div class="model-title">风乌 FengWu</div>
            <div class="model-subtitle">8085 · 大模型 / 中期天气预报</div>
            <el-form :model="config.fengwu" label-width="140px" size="small" class="model-form">
              <el-form-item label="服务地址 host">
                <el-input v-model="config.fengwu.host" :disabled="!editable" placeholder="fengwu.internal" />
              </el-form-item>
              <el-form-item label="端口 port">
                <el-input-number
                  v-model="config.fengwu.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="config.fengwu.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
              </el-form-item>
              <el-form-item label="超时（秒）">
                <el-input-number
                  v-model="config.fengwu.timeout"
                  :min="1"
                  :max="600"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="健康检查路径">
                <el-input v-model="config.fengwu.healthPath" :disabled="!editable" placeholder="/health" />
              </el-form-item>
              <el-form-item label="模型版本">
                <el-select v-model="config.fengwu.version" :disabled="!editable" style="width: 100%">
                  <el-option label="v1.0" value="v1.0" />
                  <el-option label="v2.0" value="v2.0" />
                  <el-option label="v3.0" value="v3.0" />
                </el-select>
              </el-form-item>
              <el-form-item label="GPU 加速">
                <el-switch v-model="config.fengwu.gpu" :disabled="!editable" />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.fengwu.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 4. ConvLSTM + XGBoost -->
        <el-col :xs="24" :md="12" :lg="6" :xl="6">
          <div class="model-card convlstm">
            <div class="model-title">ConvLSTM + XGBoost</div>
            <div class="model-subtitle">本地融合 / 后处理校准</div>
            <el-form :model="config.convlstm" label-width="140px" size="small" class="model-form">
              <el-form-item label="服务地址 host">
                <el-input v-model="config.convlstm.host" :disabled="!editable" placeholder="localhost" />
              </el-form-item>
              <el-form-item label="端口 port">
                <el-input-number
                  v-model="config.convlstm.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="API Key">
                <el-input v-model="config.convlstm.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
              </el-form-item>
              <el-form-item label="超时（秒）">
                <el-input-number
                  v-model="config.convlstm.timeout"
                  :min="1"
                  :max="600"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="健康检查路径">
                <el-input v-model="config.convlstm.healthPath" :disabled="!editable" placeholder="/health" />
              </el-form-item>
              <el-form-item label="模型路径">
                <el-input v-model="config.convlstm.modelPath" :disabled="!editable" placeholder="/models/latest.pkl" />
              </el-form-item>
              <el-form-item label="回滚阈值 0-1">
                <el-input-number
                  v-model="config.convlstm.rollbackThreshold"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.convlstm.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 四、Model Engine (8087) -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">🧠</span>
          <span>模型仓库管理 · Model Engine</span>
          <el-tag type="primary" size="small" effect="light">8087</el-tag>
        </div>
      </template>

      <el-form :model="config.modelEngine" label-width="140px" label-position="right" size="default">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="服务地址 host">
              <el-input v-model="config.modelEngine.host" :disabled="!editable" placeholder="model-engine.internal" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="端口 port">
              <el-input-number
                v-model="config.modelEngine.port"
                :min="1"
                :max="65535"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="API Key">
              <el-input v-model="config.modelEngine.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="超时（秒）">
              <el-input-number
                v-model="config.modelEngine.timeout"
                :min="1"
                :max="600"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="GPU 地址">
              <el-input v-model="config.modelEngine.gpuHost" :disabled="!editable" placeholder="192.168.10.20" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="模型文件路径">
              <el-input v-model="config.modelEngine.modelFilePath" :disabled="!editable" placeholder="/models/fengwu-v3.0" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="模型仓库">
              <el-input v-model="config.modelEngine.registry" :disabled="!editable" placeholder="https://registry.internal/models" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="启用">
              <el-switch v-model="config.modelEngine.enabled" :disabled="!editable" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 五、API Gateway (8088) -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">🚪</span>
          <span>API Gateway · 限流熔断</span>
          <el-tag type="success" size="small" effect="light">8088</el-tag>
        </div>
      </template>

      <el-form :model="config.gateway" label-width="140px" label-position="right" size="default">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="服务地址 host">
              <el-input v-model="config.gateway.host" :disabled="!editable" placeholder="api-gateway.internal" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="端口 port">
              <el-input-number
                v-model="config.gateway.port"
                :min="1"
                :max="65535"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="API Key">
              <el-input v-model="config.gateway.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="限流 QPS">
              <el-input-number
                v-model="config.gateway.qps"
                :min="10"
                :max="100000"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="熔断阈值（错误率 0-1）">
              <el-input-number
                v-model="config.gateway.fuseThreshold"
                :min="0"
                :max="1"
                :step="0.01"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="Nacos dataId">
              <el-input v-model="config.gateway.nacosDataId" :disabled="!editable" placeholder="uav-gateway-rules" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="Nacos group">
              <el-input v-model="config.gateway.nacosGroup" :disabled="!editable" placeholder="DEFAULT_GROUP" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="启用">
              <el-switch v-model="config.gateway.enabled" :disabled="!editable" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 六、Edge Cloud Coordinator (8000/8765) -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">☁️</span>
          <span>边云协同 · Edge Cloud Coordinator</span>
          <el-tag type="warning" size="small" effect="light">8000 / 8765</el-tag>
        </div>
      </template>

      <el-form :model="config.edge" label-width="140px" label-position="right" size="default">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="服务地址 host">
              <el-input v-model="config.edge.host" :disabled="!editable" placeholder="edge.internal" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="端口 port">
              <el-input-number
                v-model="config.edge.port"
                :min="1"
                :max="65535"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="API Key">
              <el-input v-model="config.edge.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="Kafka Topic">
              <el-input v-model="config.edge.kafkaTopic" :disabled="!editable" placeholder="uav.telemetry" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="Kafka Group">
              <el-input v-model="config.edge.kafkaGroup" :disabled="!editable" placeholder="uav-consumer-group" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="WebSocket 地址">
              <el-input v-model="config.edge.wsHost" :disabled="!editable" placeholder="ws.edge.internal" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="WebSocket 端口">
              <el-input-number
                v-model="config.edge.wsPort"
                :min="1"
                :max="65535"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="启用">
              <el-switch v-model="config.edge.enabled" :disabled="!editable" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 七、WRF Processor (8081) -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">🌦️</span>
          <span>WRF 处理器 · WRF Processor</span>
          <el-tag type="primary" size="small" effect="light">8081 · 数值天气预报</el-tag>
        </div>
      </template>

      <el-form :model="config.wrf" label-width="140px" label-position="right" size="default">
        <el-row :gutter="24">
          <el-col :xs="24" :sm="12">
            <el-form-item label="服务地址 host">
              <el-input v-model="config.wrf.host" :disabled="!editable" placeholder="wrf.internal" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="端口 port">
              <el-input-number
                v-model="config.wrf.port"
                :min="1"
                :max="65535"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="API Key">
              <el-input v-model="config.wrf.apiKey" :disabled="!editable" show-password placeholder="请输入 API Key" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="超时（秒）">
              <el-input-number
                v-model="config.wrf.timeout"
                :min="1"
                :max="600"
                :disabled="!editable"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="健康检查路径">
              <el-input v-model="config.wrf.healthPath" :disabled="!editable" placeholder="/health" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="数据文件存储路径">
              <el-input v-model="config.wrf.dataPath" :disabled="!editable" placeholder="/data/wrf/netcdf" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="挂载卷">
              <el-input v-model="config.wrf.mountVolume" :disabled="!editable" placeholder="/mnt/wrf" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="启用">
              <el-switch v-model="config.wrf.enabled" :disabled="!editable" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 八、数据库连接（3 张独立卡片） -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">💾</span>
          <span>数据库连接</span>
          <el-tag type="info" size="small" effect="light">MySQL · Redis · Nacos</el-tag>
        </div>
      </template>

      <el-row :gutter="16">
        <!-- MySQL -->
        <el-col :xs="24" :md="8">
          <div class="db-card mysql">
            <div class="db-title">MySQL</div>
            <el-form :model="config.mysql" label-width="140px" size="small">
              <el-form-item label="host">
                <el-input v-model="config.mysql.host" :disabled="!editable" placeholder="mysql.internal" />
              </el-form-item>
              <el-form-item label="port">
                <el-input-number
                  v-model="config.mysql.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="username">
                <el-input v-model="config.mysql.username" :disabled="!editable" />
              </el-form-item>
              <el-form-item label="password">
                <el-input v-model="config.mysql.password" :disabled="!editable" show-password />
              </el-form-item>
              <el-form-item label="database">
                <el-input v-model="config.mysql.database" :disabled="!editable" />
              </el-form-item>
              <el-form-item label="poolSize">
                <el-input-number
                  v-model="config.mysql.poolSize"
                  :min="1"
                  :max="1000"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.mysql.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- Redis -->
        <el-col :xs="24" :md="8">
          <div class="db-card redis">
            <div class="db-title">Redis</div>
            <el-form :model="config.redis" label-width="140px" size="small">
              <el-form-item label="host">
                <el-input v-model="config.redis.host" :disabled="!editable" placeholder="redis.internal" />
              </el-form-item>
              <el-form-item label="port">
                <el-input-number
                  v-model="config.redis.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="password">
                <el-input v-model="config.redis.password" :disabled="!editable" show-password />
              </el-form-item>
              <el-form-item label="database">
                <el-input-number
                  v-model="config.redis.database"
                  :min="0"
                  :max="15"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="timeout">
                <el-input-number
                  v-model="config.redis.timeout"
                  :min="1"
                  :max="600"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.redis.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- Nacos -->
        <el-col :xs="24" :md="8">
          <div class="db-card nacos">
            <div class="db-title">Nacos</div>
            <el-form :model="config.nacos" label-width="140px" size="small">
              <el-form-item label="host">
                <el-input v-model="config.nacos.host" :disabled="!editable" placeholder="nacos.internal" />
              </el-form-item>
              <el-form-item label="port">
                <el-input-number
                  v-model="config.nacos.port"
                  :min="1"
                  :max="65535"
                  :disabled="!editable"
                  controls-position="right"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="username">
                <el-input v-model="config.nacos.username" :disabled="!editable" />
              </el-form-item>
              <el-form-item label="password">
                <el-input v-model="config.nacos.password" :disabled="!editable" show-password />
              </el-form-item>
              <el-form-item label="namespace">
                <el-input v-model="config.nacos.namespace" :disabled="!editable" placeholder="uav-demo" />
              </el-form-item>
              <el-form-item label="启用">
                <el-switch v-model="config.nacos.enabled" :disabled="!editable" />
              </el-form-item>
            </el-form>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 九、配置备份 / 环境切换 -->
    <el-card class="section-card snapshot-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">💾</span>
          <span>配置备份 / 环境切换</span>
          <el-tag
            :type="envTagType(appStore.envMode)"
            effect="light"
            size="small"
          >
            当前环境：{{ envText(appStore.envMode) }}
          </el-tag>
        </div>
      </template>

      <el-row :gutter="16" class="snapshot-row">
        <!-- 环境切换 -->
        <el-col :xs="24" :md="6">
          <div class="snapshot-block">
            <div class="snapshot-block-title">环境切换</div>
            <el-form label-width="90px" size="default">
              <el-form-item label="当前环境">
                <el-tag :type="envTagType(appStore.envMode)" effect="dark">
                  {{ envText(appStore.envMode) }}
                </el-tag>
              </el-form-item>
              <el-form-item label="目标环境">
                <el-select
                  v-model="targetEnv" style="width: 100%">
                  <el-option label="演示环境" value="demo" />
                  <el-option label="开发环境" value="dev" />
                  <el-option label="测试环境" value="test" />
                  <el-option label="生产环境" value="prod" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="applyEnv">切换环境</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 保存快照 -->
        <el-col :xs="24" :md="6">
          <div class="snapshot-block">
            <div class="snapshot-block-title">保存当前配置为快照</div>
            <el-form label-width="90px" size="default">
              <el-form-item label="快照名称">
                <el-input v-model="snapshotName" placeholder="请输入快照名" maxlength="50" />
              </el-form-item>
              <el-form-item label="说明">
                <el-input v-model="snapshotNote" type="textarea" :rows="2" placeholder="可选备注" />
              </el-form-item>
              <el-form-item>
                <el-button type="success" @click="saveSnapshot">保存快照</el-button>
                <el-button @click="exportEntireConfig">导出全部 JSON</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-col>

        <!-- 导入 JSON -->
        <el-col :xs="24" :md="12">
          <div class="snapshot-block">
            <div class="snapshot-block-title">
              已保存快照
              <el-tag type="info" effect="plain" size="small">{{ snapshots.length }} 条</el-tag>
            </div>
            <el-upload
              :show-file-list="false"
              accept=".json"
              :auto-upload="false"
              :on-change="handleImportFile"
              class="snapshot-upload"
            >
              <el-button type="warning" plain>📥 从 JSON 文件导入</el-button>
            </el-upload>
            <el-table
              :data="snapshots"
              size="small"
              stripe
              style="margin-top: 12px; width: 100%"
              max-height="300"
            >
              <el-table-column label="名称" prop="name" min-width="140" />
              <el-table-column label="环境" prop="env" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="envTagType(row.env)" size="small">{{ envText(row.env) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="时间" prop="timestamp" width="150" align="center" />
              <el-table-column label="操作" width="280" align="center">
                <template #default="{ row, $index }">
                  <el-button size="small" type="primary" link @click="loadSnapshot($index)">加载</el-button>
                  <el-button size="small" type="success" link @click="exportSnapshot($index)">导出</el-button>
                  <el-button size="small" type="warning" link @click="applySnapshotToEnv($index)">
                    应用到当前环境
                  </el-button>
                  <el-button size="small" type="danger" link @click="removeSnapshot($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="snapshots.length === 0" class="snapshot-empty">
              暂无已保存的快照
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { useAppStore } from '../../stores/app'
import { useNotificationStore } from '../../stores/notification'

const notificationStore = useNotificationStore()

const authStore = useAuthStore()
const appStore = useAppStore()
const editable = computed(() => authStore.hasAction('api-config:edit'))

// ===== 配置备份 / 环境切换 =====
const SNAPSHOT_KEY = 'uav_api_snapshots_v1'
const targetEnv = ref(appStore.envMode || 'demo')
const snapshotName = ref('')
const snapshotNote = ref('')

function readSnapshots() {
  try {
    const raw = localStorage.getItem(SNAPSHOT_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch (e) {
    return []
  }
}
function writeSnapshots(list) {
  try {
    localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(list))
  } catch (e) {}
}

const snapshots = ref(readSnapshots())

function envText(e) {
  return { demo: '演示', dev: '开发', test: '测试', prod: '生产' }[e] || e
}
function envTagType(e) {
  return { demo: 'warning', dev: 'primary', test: 'success', prod: 'danger' }[e] || 'info'
}

function serializeConfig() {
  return JSON.parse(JSON.stringify(config))
}
function mergeIntoConfig(data) {
  if (!data || typeof data !== 'object') return false
  Object.keys(config).forEach(k => {
    if (data[k] !== undefined) {
      if (typeof config[k] === 'object' && typeof data[k] === 'object' && !Array.isArray(data[k])) {
        Object.assign(config[k], data[k])
      } else {
        config[k] = data[k]
      }
    }
  })
  return true
}

function applyEnv() {
  if (targetEnv.value === appStore.envMode) {
    ElMessage.info('当前环境已是目标环境')
    return
  }
  ElMessageBox.confirm(
    `确认将环境从「${envText(appStore.envMode)}」切换为「${envText(targetEnv.value)}」吗？`,
    '切换环境确认',
    { confirmButtonText: '切换', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => {
      appStore.setEnvMode(targetEnv.value)
      ElMessage.success(`已切换到：${envText(targetEnv.value)}`)
    })
    .catch(() => {})
}

function saveSnapshot() {
  const name = snapshotName.value.trim()
  if (!name) {
    ElMessage.warning('请先输入快照名称')
    return
  }
  const snap = {
    id: 'snap_' + Date.now(),
    name,
    note: snapshotNote.value.trim(),
    env: appStore.envMode,
    data: serializeConfig(),
    timestamp: new Date().toLocaleString('zh-CN', { hour12: false })
  }
  const list = [snap, ...snapshots.value].slice(0, 50)
  writeSnapshots(list)
  snapshots.value = list
  snapshotName.value = ''
  snapshotNote.value = ''
  ElMessage.success('快照已保存')
}

function loadSnapshot(idx) {
  const snap = snapshots.value[idx]
  if (!snap) return
  ElMessageBox.confirm(
    `确认加载快照「${snap.name}」？当前未保存的修改将被覆盖。`,
    '加载快照确认',
    { confirmButtonText: '加载', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => {
      if (mergeIntoConfig(snap.data)) {
        ElMessage.success(`快照「${snap.name}」已加载`)
      } else {
        ElMessage.error('快照数据格式不正确')
      }
    })
    .catch(() => {})
}

function exportSnapshot(idx) {
  const snap = snapshots.value[idx]
  if (!snap) return
  try {
    const blob = new Blob([JSON.stringify(snap, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `api_config_snapshot_${snap.env}_${snap.id}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('快照已导出')
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  }
}

function applySnapshotToEnv(idx) {
  const snap = snapshots.value[idx]
  if (!snap) return
  ElMessageBox.confirm(
    `将快照「${snap.name}」应用到当前环境（${envText(appStore.envMode)}）并切换为该环境？`,
    '应用到当前环境确认',
    { confirmButtonText: '应用', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => {
      if (snap.env && snap.env !== appStore.envMode) {
        appStore.setEnvMode(snap.env)
      }
      if (mergeIntoConfig(snap.data)) {
        ElMessage.success('快照已应用到当前环境')
      } else {
        ElMessage.error('快照数据格式不正确')
      }
    })
    .catch(() => {})
}

function removeSnapshot(idx) {
  const snap = snapshots.value[idx]
  if (!snap) return
  ElMessageBox.confirm(
    `确认删除快照「${snap.name}」？此操作不可撤销。`,
    '删除快照确认',
    { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' }
  )
    .then(() => {
      const list = snapshots.value.filter((_, i) => i !== idx)
      writeSnapshots(list)
      snapshots.value = list
      ElMessage.success('快照已删除')
    })
    .catch(() => {})
}

function exportEntireConfig() {
  try {
    const payload = {
      env: appStore.envMode,
      config: serializeConfig(),
      exportedAt: new Date().toISOString()
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    a.download = `api_config_${appStore.envMode}_${ts}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('全部配置已导出')
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  }
}

function handleImportFile(file) {
  if (!file) return
  const reader = new FileReader()
  reader.onload = e => {
    try {
      const text = String(e.target.result || '')
      const parsed = JSON.parse(text)
      const data = parsed.config || parsed
      ElMessageBox.confirm(
        `检测到 JSON 配置，是否覆盖当前表单值？\n文件名：${file.name}`,
        '导入配置确认',
        { confirmButtonText: '覆盖导入', cancelButtonText: '取消', type: 'warning' }
      )
        .then(() => {
          if (mergeIntoConfig(data)) {
            if (parsed.env) appStore.setEnvMode(parsed.env)
            ElMessage.success('配置已导入')
          } else {
            ElMessage.error('配置数据格式不正确')
          }
        })
        .catch(() => {})
    } catch (err) {
      ElMessage.error('JSON 解析失败：' + err.message)
    }
  }
  reader.readAsText(file)
}

watch(
  () => appStore.envMode,
  v => {
    targetEnv.value = v
  }
)

// ===== 配置数据 =====
const config = reactive({
  mode: 'demo',
  tianzi: {
    host: 'tianzi.internal.demo.io',
    port: 8090,
    apiKey: 'DEMO-TIANZI-KEY',
    jwtSecret: 'DEMO-TIANZI-JWT-SECRET',
    timeout: 30,
    healthPath: '/health',
    enabled: true
  },
  fenglei: {
    host: 'fenglei.internal.demo.io',
    port: 8091,
    apiKey: 'DEMO-FENGLEI-KEY',
    timeout: 30,
    healthPath: '/health',
    updateFreq: 6,
    enabled: true
  },
  fengwu: {
    host: 'fengwu.internal.demo.io',
    port: 8085,
    apiKey: 'DEMO-FENGWU-KEY',
    timeout: 30,
    healthPath: '/health',
    version: 'v3.0',
    gpu: true,
    enabled: true
  },
  convlstm: {
    host: 'localhost',
    port: 8080,
    apiKey: 'DEMO-CONVLSTM-KEY',
    timeout: 30,
    healthPath: '/health',
    modelPath: '/models/convlstm_xgboost_v2.pkl',
    rollbackThreshold: 0.85,
    enabled: true
  },
  modelEngine: {
    host: 'model-engine.internal.demo.io',
    port: 8087,
    apiKey: 'DEMO-MODEL-ENGINE-KEY',
    timeout: 30,
    gpuHost: '192.168.10.20',
    modelFilePath: '/models/fengwu-v3.0',
    registry: 'https://registry.internal/models',
    enabled: true
  },
  gateway: {
    host: 'api-gateway.internal.demo.io',
    port: 8088,
    apiKey: 'DEMO-GATEWAY-KEY',
    qps: 500,
    fuseThreshold: 0.3,
    nacosDataId: 'uav-gateway-rules',
    nacosGroup: 'DEFAULT_GROUP',
    enabled: true
  },
  edge: {
    host: 'edge.internal.demo.io',
    port: 8000,
    apiKey: 'DEMO-EDGE-KEY',
    kafkaTopic: 'uav.telemetry',
    kafkaGroup: 'uav-consumer-group',
    wsHost: 'ws.edge.internal.demo.io',
    wsPort: 8765,
    enabled: true
  },
  wrf: {
    host: 'wrf.internal.demo.io',
    port: 8081,
    apiKey: 'DEMO-WRF-KEY',
    timeout: 30,
    healthPath: '/health',
    dataPath: '/data/wrf/netcdf',
    mountVolume: '/mnt/wrf',
    enabled: true
  },
  mysql: {
    host: 'mysql.demo.io',
    port: 3306,
    username: 'uav_rw',
    password: 'demo-mysql-password',
    database: 'uav_path_planning',
    poolSize: 20,
    enabled: true
  },
  redis: {
    host: 'redis.demo.io',
    port: 6379,
    password: 'demo-redis-password',
    database: 0,
    timeout: 10,
    enabled: true
  },
  nacos: {
    host: 'nacos.demo.io',
    port: 8848,
    username: 'nacos_demo',
    password: 'demo-nacos-password',
    namespace: 'uav-demo',
    enabled: true
  }
})

// ===== 统计 =====
const totalCount = 8
const configuredCount = computed(() => {
  let count = 0
  if (config.tianzi.enabled) count++
  if (config.fenglei.enabled) count++
  if (config.fengwu.enabled) count++
  if (config.modelEngine.enabled) count++
  if (config.gateway.enabled) count++
  if (config.edge.enabled) count++
  if (config.wrf.enabled) count++
  if (config.mysql.enabled || config.redis.enabled || config.nacos.enabled) count++
  return count
})

// ===== 操作 =====
function handleSave() {
  console.log(config)
  ElMessage.success('配置已保存（演示模式：本地）')
  notificationStore.pushWithDesktop({
    type: 'info',
    title: '配置已保存',
    message: `气象模型 API 配置已保存，当前模式：${config.mode === 'prod' ? '生产' : '演示'}`,
    source: 'apiConfig'
  })
}

function handleExportJson() {
  try {
    const jsonStr = JSON.stringify(config, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'uav-api-config.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('配置已导出为 uav-api-config.json')
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  }
}

async function handleSwitchMode() {
  const confirmed = await authStore.requireSensitiveConfirmation('切换到生产模式')
  if (!confirmed) return
  ElMessageBox.confirm(
    '切换到生产模式后不可逆向切换为演示模式。确认继续？',
    '切换生产模式确认',
    {
      confirmButtonText: '确认切换',
      cancelButtonText: '取消',
      type: 'error',
      distinguishCancelAndClose: true
    }
  )
    .then(() => {
      config.mode = 'prod'
      ElMessage.success('已切换为生产模式，配置锁定')
      notificationStore.pushWithDesktop({
        type: 'info',
        title: '运行环境已切换',
        message: '已切换到生产模式，配置将不可逆向修改',
        source: 'apiConfig'
      })
    })
    .catch(() => {})
}
</script>

<style scoped>
.api-config {
  padding: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1f2937;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.demo-alert {
  margin-bottom: 16px;
}

.top-action-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 16px;
  padding: 0 4px;
}

.section-card {
  border-radius: 10px;
  margin-bottom: 16px;
}

.overview-card {
  padding-top: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
}

.header-icon {
  font-size: 16px;
}

/* 总览 */
.overview {
  display: grid;
  grid-template-columns: 1fr 280px;
  align-items: center;
  gap: 24px;
  padding: 8px 16px 0;
}

.overview-title {
  font-size: 15px;
  color: #1f2937;
  margin-bottom: 6px;
}

.overview-title b {
  color: #409EFF;
  font-size: 20px;
}

.overview-desc {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
}

.overview-progress {
  min-width: 200px;
}

.overview-footer {
  padding: 12px 16px 0;
}

/* 模型卡片 */
.model-row .el-col {
  margin-bottom: 16px;
}

.model-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: linear-gradient(to bottom, #fafbfc, #ffffff);
  height: 100%;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.model-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.08);
}

.model-card.tianzi {
  border-top: 4px solid #E6A23C;
}

.model-card.fenglei {
  border-top: 4px solid #F56C6C;
}

.model-card.fengwu {
  border-top: 4px solid #67C23A;
}

.model-card.convlstm {
  border-top: 4px solid #9B59B6;
}

.model-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
}

.model-subtitle {
  font-size: 12.5px;
  color: #6b7280;
  margin: 4px 0 14px;
}

.model-form {
  margin-top: 4px;
}

/* 数据库卡片 */
.db-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: #fafbfc;
  height: 100%;
}

.db-card.mysql {
  border-top: 4px solid #409EFF;
}

.db-card.redis {
  border-top: 4px solid #E74C3C;
}

.db-card.nacos {
  border-top: 4px solid #2ECC71;
}

.db-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12px;
}

/* 响应式 */
@media (max-width: 992px) {
  .overview {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 8px 8px 0;
  }

  .overview-progress {
    min-width: 0;
  }
}

/* 配置备份 / 环境切换 */
.snapshot-card {
  margin-top: 8px;
}

.snapshot-row {
  margin-top: 4px;
}

.snapshot-block {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 16px;
  background: #fafbfc;
  height: 100%;
}

.snapshot-block-title {
  font-size: 14px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.snapshot-upload {
  display: block;
  margin-top: 4px;
}

.snapshot-empty {
  text-align: center;
  color: #909399;
  padding: 20px 0;
  font-size: 13px;
}
</style>
