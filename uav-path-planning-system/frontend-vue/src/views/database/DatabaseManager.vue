<template>
  <div class="database-manager">
    <div class="page-title">数据库管理</div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="演示模式"
      description="当前为演示环境，所有数据库操作均为模拟，不会影响真实数据。管理员可在此页面执行查询、导出、清空缓存与执行 SQL 等操作。"
      class="demo-alert"
    />

    <!-- 连接状态卡片 -->
    <template v-if="authStore.hasAction('database:view')">
    <el-row :gutter="16" class="status-row">
      <el-col :xs="24" :sm="8">
        <el-card class="conn-card" shadow="hover">
          <template #header>
            <div class="conn-header">
              <span class="conn-icon" style="background: #409EFF">🐬</span>
              <span class="conn-title">MySQL</span>
              <el-tag size="small" type="success" effect="light">8.0</el-tag>
            </div>
          </template>
          <div class="conn-info">
            <div class="conn-row">
              <span class="conn-label">主机</span>
              <span class="conn-value">mysql.local.io</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">端口</span>
              <span class="conn-value">3306</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">连接池</span>
              <span class="conn-value">32 / 100</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">状态</span>
              <el-tag type="success" size="small" effect="dark">在线</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card class="conn-card" shadow="hover">
          <template #header>
            <div class="conn-header">
              <span class="conn-icon" style="background: #E6A23C">⚡</span>
              <span class="conn-title">Redis</span>
              <el-tag size="small" type="warning" effect="light">6.2</el-tag>
            </div>
          </template>
          <div class="conn-info">
            <div class="conn-row">
              <span class="conn-label">主机</span>
              <span class="conn-value">redis.local.io</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">端口</span>
              <span class="conn-value">6379</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">内存用量</span>
              <span class="conn-value">1.24 / 4 GB</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">状态</span>
              <el-tag type="success" size="small" effect="dark">在线</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="8">
        <el-card class="conn-card" shadow="hover">
          <template #header>
            <div class="conn-header">
              <span class="conn-icon" style="background: #67C23A">🗂️</span>
              <span class="conn-title">Nacos</span>
              <el-tag size="small" type="success" effect="light">2.3</el-tag>
            </div>
          </template>
          <div class="conn-info">
            <div class="conn-row">
              <span class="conn-label">主机</span>
              <span class="conn-value">nacos.local.io</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">端口</span>
              <span class="conn-value">8848</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">配置数</span>
              <span class="conn-value">86</span>
            </div>
            <div class="conn-row">
              <span class="conn-label">状态</span>
              <el-tag type="success" size="small" effect="dark">在线</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    </template>
    <el-empty v-else description="无权限查看数据库状态" />

    <!-- 数据表浏览器 -->
    <el-row :gutter="16" class="browse-row">
      <!-- 左侧表列表 -->
      <el-col :xs="24" :md="6">
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="header-icon">📋</span>
              <span>表列表</span>
              <el-tag type="info" size="small" effect="plain">{{ tables.length }} 张表</el-tag>
            </div>
          </template>
          <div class="table-list">
            <div
              v-for="t in tables"
              :key="t.name"
              class="table-item"
              :class="{ active: selectedTable === t.name }"
              @click="selectTable(t.name)"
            >
              <span class="table-icon">📄</span>
              <span class="table-name">{{ t.name }}</span>
              <span class="table-rows">{{ t.rows }} 行</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧结构 + 数据 -->
      <el-col :xs="24" :md="18">
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="header-icon">🔍</span>
              <span>{{ selectedTable }} 表</span>
              <div class="header-right">
                <el-button size="small" type="primary" v-if="authStore.hasAction('database:query')" @click="handleQuery">查询数据</el-button>
                <el-button size="small" type="success" v-if="authStore.hasAction('database:export')" @click="handleExport">导出 CSV</el-button>
                <el-button size="small" type="warning" v-if="authStore.hasAction('database:clear')" @click="handleClearCache">清空缓存</el-button>
                <el-button size="small" type="danger" v-if="authStore.hasAction('database:edit')" @click="handleExecSql">执行 SQL</el-button>
              </div>
            </div>
          </template>

          <!-- 结构 -->
          <div class="sub-section">
            <div class="sub-title">📐 字段结构</div>
            <el-table :data="currentTableSchema" size="small" border stripe>
              <el-table-column prop="name" label="字段名" width="180" />
              <el-table-column prop="type" label="类型" width="140" align="center" />
              <el-table-column prop="nullable" label="可空" width="80" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.nullable ? 'info' : 'success'" effect="plain">
                    {{ row.nullable ? '是' : '否' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="key" label="键" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.key" size="small" type="danger" effect="plain">{{ row.key }}</el-tag>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="default" label="默认值" width="160" align="center" />
              <el-table-column prop="comment" label="备注" />
            </el-table>
          </div>

          <el-divider />

          <!-- 示例数据 -->
          <div class="sub-section">
            <div class="sub-title">📊 前 5 行示例数据</div>
            <el-table :data="currentTableData" size="small" border stripe>
              <el-table-column
                v-for="col in currentTableColumns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="120"
              />
            </el-table>
          </div>

          <!-- SQL 执行面板 -->
          <el-collapse class="sql-collapse" v-model="sqlPanelActive">
            <el-collapse-item title="🛠 SQL 执行面板（仅管理员）" name="sql">
              <el-input
                v-model="sqlContent"
                type="textarea"
                :rows="4"
                placeholder="在此输入 SQL，例如：SELECT * FROM tasks LIMIT 10;"
                :disabled="!authStore.hasAction('database:edit')"
              />
              <div class="sql-actions">
                <el-button type="primary" size="small" :disabled="!authStore.hasAction('database:edit')" @click="execSql">执行</el-button>
                <el-button size="small" @click="sqlContent = ''">清空</el-button>
                <el-tag type="warning" size="small" effect="light" class="sql-tip">
                  演示模式：仅允许执行 SELECT，其他语句将被拦截。
                </el-tag>
              </div>

              <div v-if="sqlResultVisible" class="sql-result">
                <div class="result-title">
                  执行结果
                  <el-tag :type="sqlResultSuccess ? 'success' : 'danger'" size="small" effect="plain" style="margin-left: 8px">
                    {{ sqlResultSuccess ? '成功' : '失败' }}
                  </el-tag>
                  <span class="result-time">耗时 {{ sqlResultTime }} ms</span>
                </div>
                <el-table v-if="sqlResultSuccess" :data="sqlResultRows" size="small" border>
                  <el-table-column
                    v-for="col in sqlResultCols"
                    :key="col"
                    :prop="col"
                    :label="col"
                    min-width="120"
                  />
                </el-table>
                <div v-else class="sql-error">{{ sqlResultMsg }}</div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

// ===== 表列表 =====
const tables = [
  { name: 'users', rows: 12845 },
  { name: 'tasks', rows: 89642 },
  { name: 'drones', rows: 328 },
  { name: 'routes', rows: 12480 },
  { name: 'weather_cache', rows: 286931 },
  { name: 'assimilation_logs', rows: 44210 },
  { name: 'system_logs', rows: 1884322 }
]

const selectedTable = ref('users')

// ===== 结构定义 =====
const tableSchemas = {
  users: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '用户主键' },
    { name: 'username', type: 'VARCHAR(64)', nullable: false, key: 'UNI', default: '-', comment: '用户名' },
    { name: 'role', type: 'VARCHAR(32)', nullable: false, key: '', default: 'user', comment: '角色' },
    { name: 'email', type: 'VARCHAR(128)', nullable: true, key: '', default: 'NULL', comment: '邮箱' },
    { name: 'created_at', type: 'DATETIME', nullable: false, key: '', default: 'NOW()', comment: '创建时间' }
  ],
  tasks: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '任务 ID' },
    { name: 'title', type: 'VARCHAR(200)', nullable: false, key: '', default: '-', comment: '任务标题' },
    { name: 'status', type: 'VARCHAR(32)', nullable: false, key: 'IDX', default: 'pending', comment: '状态' },
    { name: 'user_id', type: 'BIGINT', nullable: false, key: 'FK', default: '-', comment: '创建用户' },
    { name: 'created_at', type: 'DATETIME', nullable: false, key: '', default: 'NOW()', comment: '创建时间' }
  ],
  drones: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '无人机 ID' },
    { name: 'model', type: 'VARCHAR(64)', nullable: false, key: '', default: '-', comment: '型号' },
    { name: 'status', type: 'VARCHAR(32)', nullable: false, key: '', default: 'idle', comment: '状态' },
    { name: 'battery', type: 'TINYINT', nullable: false, key: '', default: '100', comment: '电量%' }
  ],
  routes: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '路线 ID' },
    { name: 'task_id', type: 'BIGINT', nullable: false, key: 'FK', default: '-', comment: '关联任务' },
    { name: 'start_point', type: 'POINT', nullable: false, key: '', default: '-', comment: '起点' },
    { name: 'end_point', type: 'POINT', nullable: false, key: '', default: '-', comment: '终点' },
    { name: 'distance_km', type: 'DECIMAL(8,2)', nullable: false, key: '', default: '0', comment: '距离 km' }
  ],
  weather_cache: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '缓存 ID' },
    { name: 'model', type: 'VARCHAR(32)', nullable: false, key: 'IDX', default: 'WRF', comment: '模型' },
    { name: 'location', type: 'POINT', nullable: false, key: '', default: '-', comment: '位置' },
    { name: 'forecast_at', type: 'DATETIME', nullable: false, key: 'IDX', default: '-', comment: '预报时间' },
    { name: 'wind_m_s', type: 'DECIMAL(6,2)', nullable: true, key: '', default: 'NULL', comment: '风速 m/s' }
  ],
  assimilation_logs: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '同化 ID' },
    { name: 'model', type: 'VARCHAR(32)', nullable: false, key: '', default: '-', comment: '模型' },
    { name: 'observations', type: 'INT', nullable: false, key: '', default: '0', comment: '观测数' },
    { name: 'status', type: 'VARCHAR(32)', nullable: false, key: '', default: 'ok', comment: '状态' },
    { name: 'created_at', type: 'DATETIME', nullable: false, key: '', default: 'NOW()', comment: '完成时间' }
  ],
  system_logs: [
    { name: 'id', type: 'BIGINT', nullable: false, key: 'PK', default: '-', comment: '日志 ID' },
    { name: 'level', type: 'VARCHAR(16)', nullable: false, key: 'IDX', default: 'INFO', comment: '级别' },
    { name: 'service', type: 'VARCHAR(64)', nullable: false, key: 'IDX', default: '-', comment: '服务名' },
    { name: 'message', type: 'TEXT', nullable: true, key: '', default: 'NULL', comment: '消息' },
    { name: 'created_at', type: 'DATETIME', nullable: false, key: 'IDX', default: 'NOW()', comment: '时间' }
  ]
}

// ===== 示例数据 =====
const tableData = {
  users: [
    { id: 1, username: 'admin01', role: 'admin', email: 'admin@example.com', created_at: '2026-05-20 08:22:10' },
    { id: 2, username: 'deploy01', role: 'deployment', email: 'deploy@example.com', created_at: '2026-05-22 11:03:40' },
    { id: 3, username: 'test01', role: 'tester', email: 'test@example.com', created_at: '2026-05-24 15:11:25' },
    { id: 4, username: 'flight01', role: 'flight', email: 'flight@example.com', created_at: '2026-06-01 09:45:00' },
    { id: 5, username: 'prod01', role: 'production', email: 'prod@example.com', created_at: '2026-06-05 14:27:18' }
  ],
  tasks: [
    { id: 1001, title: '物流配送 A-12 区', status: 'done', user_id: 2, created_at: '2026-06-08 09:00:12' },
    { id: 1002, title: '电网巡检 B-5 线', status: 'running', user_id: 4, created_at: '2026-06-08 09:20:41' },
    { id: 1003, title: '应急救援 C-9 点', status: 'pending', user_id: 2, created_at: '2026-06-08 09:55:00' },
    { id: 1004, title: '农林植保 D-3 田', status: 'running', user_id: 4, created_at: '2026-06-08 10:05:27' },
    { id: 1005, title: '城市管理 E-7 街', status: 'pending', user_id: 1, created_at: '2026-06-08 10:11:55' }
  ],
  drones: [
    { id: 1, model: 'DJI M300 RTK', status: 'flying', battery: 72 },
    { id: 2, model: 'DJI M300 RTK', status: 'idle', battery: 100 },
    { id: 3, model: 'Autel EVO II', status: 'charging', battery: 35 },
    { id: 4, model: 'Autel EVO II', status: 'flying', battery: 58 },
    { id: 5, model: 'Yuneec H520', status: 'idle', battery: 90 }
  ],
  routes: [
    { id: 1, task_id: 1001, start_point: '(31.23,121.47)', end_point: '(31.25,121.49)', distance_km: '3.18' },
    { id: 2, task_id: 1002, start_point: '(31.30,121.40)', end_point: '(31.35,121.45)', distance_km: '7.63' },
    { id: 3, task_id: 1003, start_point: '(31.18,121.52)', end_point: '(31.22,121.55)', distance_km: '5.40' },
    { id: 4, task_id: 1004, start_point: '(31.40,121.38)', end_point: '(31.42,121.41)', distance_km: '3.61' },
    { id: 5, task_id: 1005, start_point: '(31.27,121.48)', end_point: '(31.30,121.50)', distance_km: '3.82' }
  ],
  weather_cache: [
    { id: 1, model: 'WRF', location: '(31.23,121.47)', forecast_at: '2026-06-08 12:00:00', wind_m_s: '5.20' },
    { id: 2, model: 'FengWu', location: '(31.25,121.49)', forecast_at: '2026-06-08 12:00:00', wind_m_s: '4.80' },
    { id: 3, model: 'TianZi', location: '(31.30,121.40)', forecast_at: '2026-06-08 12:00:00', wind_m_s: '6.10' },
    { id: 4, model: 'FengLei', location: '(31.35,121.45)', forecast_at: '2026-06-08 12:00:00', wind_m_s: '7.30' },
    { id: 5, model: 'WRF', location: '(31.18,121.52)', forecast_at: '2026-06-08 13:00:00', wind_m_s: '5.60' }
  ],
  assimilation_logs: [
    { id: 1, model: 'WRF', observations: 1284, status: 'ok', created_at: '2026-06-08 09:12:44' },
    { id: 2, model: 'FengWu', observations: 896, status: 'ok', created_at: '2026-06-08 09:15:12' },
    { id: 3, model: 'TianZi', observations: 512, status: 'warn', created_at: '2026-06-08 09:18:30' },
    { id: 4, model: 'FengLei', observations: 2048, status: 'ok', created_at: '2026-06-08 09:22:10' },
    { id: 5, model: 'WRF', observations: 1305, status: 'ok', created_at: '2026-06-08 10:00:00' }
  ],
  system_logs: [
    { id: 1, level: 'INFO', service: 'api-gateway', message: 'request processed in 23ms', created_at: '2026-06-08 10:45:12' },
    { id: 2, level: 'WARN', service: 'fenglei-service', message: 'cpu usage above 90%', created_at: '2026-06-08 10:45:18' },
    { id: 3, level: 'ERROR', service: 'kafka', message: 'broker-3 unreachable', created_at: '2026-06-08 10:45:22' },
    { id: 4, level: 'INFO', service: 'path-planning', message: 'solved task #1284 in 2.3s', created_at: '2026-06-08 10:45:30' },
    { id: 5, level: 'INFO', service: 'platform-service', message: 'deploy v3.3.0 completed', created_at: '2026-06-08 10:45:44' }
  ]
}

const currentTableSchema = computed(() => tableSchemas[selectedTable.value] || [])
const currentTableData = computed(() => tableData[selectedTable.value] || [])
const currentTableColumns = computed(() => (currentTableData.value[0] ? Object.keys(currentTableData.value[0]) : []))

function selectTable(name) {
  selectedTable.value = name
  sqlResultVisible.value = false
}

// ===== 操作 =====
function handleQuery() {
  ElMessage.success(`已从 ${selectedTable.value} 查询最新 ${currentTableData.value.length} 行示例数据`)
}

function handleExport() {
  ElMessage.success(`正在导出 ${selectedTable.value}.csv（演示：不会生成真实文件）`)
}

async function handleClearCache() {
  const confirmed = await authStore.requireSensitiveConfirmation('清空缓存')
  if (!confirmed) return
  ElMessageBox.confirm(
    `确认要清空 Redis 中所有 "${selectedTable.value}" 相关缓存吗？`,
    '清空缓存确认',
    { confirmButtonText: '确认清空', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => ElMessage.success(`缓存已清空（演示）`))
    .catch(() => {})
}

function handleExecSql() {
  sqlPanelActive.value = ['sql']
  sqlContent.value = `SELECT * FROM ${selectedTable.value} LIMIT 10;`
}

// ===== SQL 执行 =====
const sqlPanelActive = ref([])
const sqlContent = ref('')
const sqlResultVisible = ref(false)
const sqlResultSuccess = ref(true)
const sqlResultMsg = ref('')
const sqlResultTime = ref(0)
const sqlResultRows = ref([])
const sqlResultCols = ref([])

function execSql() {
  if (!authStore.hasAction('database:edit')) {
    ElMessage.error('仅管理员可执行 SQL')
    return
  }
  const trimmed = sqlContent.value.trim().toLowerCase()
  sqlResultTime.value = 20 + Math.floor(Math.random() * 80)

  if (!trimmed) {
    sqlResultSuccess.value = false
    sqlResultMsg.value = 'SQL 不能为空'
    sqlResultVisible.value = true
    return
  }

  if (!trimmed.startsWith('select')) {
    sqlResultSuccess.value = false
    sqlResultMsg.value = '演示模式仅允许执行 SELECT 语句，其他 DML/DDL 已被安全策略拦截。'
    sqlResultVisible.value = true
    return
  }

  // 尝试匹配表名
  const matched = tables.find(t => trimmed.includes(t.name))
  if (matched) {
    sqlResultCols.value = Object.keys(tableData[matched.name][0])
    sqlResultRows.value = tableData[matched.name]
    sqlResultSuccess.value = true
  } else {
    sqlResultCols.value = ['count']
    sqlResultRows.value = [{ count: 0 }]
    sqlResultSuccess.value = true
  }
  sqlResultVisible.value = true
  ElMessage.success('SQL 执行完成')
}
</script>

<style scoped>
.database-manager {
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

.status-row {
  margin-bottom: 16px;
}

.status-row .el-col {
  margin-bottom: 12px;
}

.conn-card {
  border-radius: 10px;
}

.conn-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
}

.conn-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.conn-title {
  font-size: 15px;
}

.conn-info {
  padding: 4px 2px;
}

.conn-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px dashed #eef0f3;
}

.conn-row:last-child {
  border-bottom: none;
}

.conn-label {
  color: #6b7280;
}

.conn-value {
  color: #1f2937;
  font-weight: 500;
  font-family: 'SFMono-Regular', Menlo, monospace;
}

/* 浏览器 */
.browse-row {
  margin-bottom: 0;
}

.section-card {
  border-radius: 10px;
  height: 100%;
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

.header-right {
  margin-left: auto;
  display: flex;
  gap: 8px;
  font-weight: normal;
}

/* 表列表 */
.table-list {
  max-height: 520px;
  overflow-y: auto;
}

.table-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.table-item:hover {
  background: #f5f7fa;
}

.table-item.active {
  background: #ecf5ff;
  border-color: #409EFF;
}

.table-name {
  flex: 1;
  font-size: 13px;
  color: #1f2937;
  font-family: 'SFMono-Regular', Menlo, monospace;
  font-weight: 500;
}

.table-rows {
  font-size: 12px;
  color: #9ca3af;
}

/* 子区块 */
.sub-section {
  margin-top: 4px;
}

.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 10px;
}

.text-muted {
  color: #c0c4cc;
}

/* SQL 面板 */
.sql-collapse {
  margin-top: 16px;
}

.sql-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.sql-tip {
  margin-left: auto;
}

.sql-result {
  margin-top: 14px;
  padding: 12px;
  border: 1px dashed #e5e7eb;
  border-radius: 8px;
  background: #fafbfc;
}

.result-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.result-time {
  margin-left: auto;
  color: #6b7280;
  font-weight: normal;
  font-size: 12px;
}

.sql-error {
  color: #f56c6c;
  font-size: 13px;
  padding: 8px 4px;
  background: #fef0f0;
  border-radius: 6px;
}
</style>
