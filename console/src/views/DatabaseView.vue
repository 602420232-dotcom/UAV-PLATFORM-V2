<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { databaseApi } from '@/api/database'
import type { DatabaseInfo, TableInfo, ColumnInfo, QueryResult } from '@/api/database'
import { useDemoModeStore } from '@/stores/demoMode'

const demoModeStore = useDemoModeStore()

// 数据库列表
const databases = ref<DatabaseInfo[]>([])
const currentDatabase = ref('')
const tablesLoading = ref(false)
const tables = ref<TableInfo[]>([])
const currentTable = ref('')

// 表结构
const columns = ref<ColumnInfo[]>([])
const columnsLoading = ref(false)

// SQL 编辑器
const sqlContent = ref('')
const queryLoading = ref(false)
const queryResult = ref<QueryResult | null>(null)

// 表数据
const tableDataLoading = ref(false)
const tableData = ref<Record<string, unknown>[]>([])
const tableDataTotal = ref(0)
const tableDataPage = ref(1)
const tableDataSize = ref(20)

// 当前激活的标签页：table-structure | table-data | query-result
const activeTab = ref('table-structure')

/** 加载数据库列表 */
async function loadDatabases() {
  if (demoModeStore.isDemoMode) return
  try {
    databases.value = await databaseApi.getDatabases()
    // 默认选中第一个数据库
    if (databases.value.length > 0 && !currentDatabase.value) {
      currentDatabase.value = databases.value[0]?.name ?? ''
    }
  } catch {
    // 错误已在拦截器中处理
  }
}

/** 选择数据库 */
async function handleDatabaseClick(dbName: string) {
  currentDatabase.value = dbName
  currentTable.value = ''
  columns.value = []
  queryResult.value = null
  tableData.value = []
  activeTab.value = 'table-structure'
  await loadTables()
}

/** 加载表列表 */
async function loadTables() {
  if (!currentDatabase.value) return
  tablesLoading.value = true
  try {
    tables.value = await databaseApi.getTables(currentDatabase.value)
  } catch {
    // 错误已在拦截器中处理
  } finally {
    tablesLoading.value = false
  }
}

/** 选择表 */
async function handleTableClick(tableName: string) {
  currentTable.value = tableName
  queryResult.value = null
  activeTab.value = 'table-structure'
  await loadTableColumns()
  await loadTableData()
}

/** 加载表结构 */
async function loadTableColumns() {
  if (!currentDatabase.value || !currentTable.value) return
  columnsLoading.value = true
  try {
    columns.value = await databaseApi.getTableColumns(currentDatabase.value, currentTable.value)
  } catch {
    // 错误已在拦截器中处理
  } finally {
    columnsLoading.value = false
  }
}

/** 加载表数据 */
async function loadTableData() {
  if (!currentDatabase.value || !currentTable.value) return
  tableDataLoading.value = true
  try {
    const result = await databaseApi.getTableData(
      currentDatabase.value,
      currentTable.value,
      { page: tableDataPage.value, size: tableDataSize.value }
    )
    tableData.value = result.rows
    tableDataTotal.value = result.total
  } catch {
    // 错误已在拦截器中处理
  } finally {
    tableDataLoading.value = false
  }
}

/** 表数据分页变化 */
function handleTableDataPageChange(page: number) {
  tableDataPage.value = page
  loadTableData()
}

function handleTableDataSizeChange(size: number) {
  tableDataSize.value = size
  tableDataPage.value = 1
  loadTableData()
}

/** 执行 SQL */
async function handleExecuteSql() {
  const sql = sqlContent.value.trim()
  if (!sql) {
    ElMessage.warning('请输入 SQL 语句')
    return
  }
  queryLoading.value = true
  try {
    const result = await databaseApi.executeQuery({
      sql,
      database: currentDatabase.value || undefined,
    })
    queryResult.value = result
    activeTab.value = 'query-result'
    if (result.affectedRows !== undefined) {
      ElMessage.success(result.message || `执行成功，影响 ${result.affectedRows} 行`)
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    queryLoading.value = false
  }
}

/** 清空 SQL 编辑器 */
function handleClearSql() {
  sqlContent.value = ''
  queryResult.value = null
}

/** 获取表数据的列名 */
function getTableDataColumns(): string[] {
  if (tableData.value.length === 0) return []
  return Object.keys(tableData.value[0] as Record<string, unknown>)
}

/** 格式化显示值 */
function formatValue(val: unknown): string {
  if (val === null || val === undefined) return 'NULL'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadDatabases()
})

watch(() => demoModeStore.isDemoMode, () => {
  if (demoModeStore.isDemoMode) {
    databases.value = []
    currentDatabase.value = ''
    tables.value = []
    columns.value = []
    queryResult.value = null
    tableData.value = []
  } else {
    loadDatabases()
  }
})
</script>

<template>
  <div class="database-page">
    <!-- 演示模式提示 -->
    <el-alert
      v-if="demoModeStore.isDemoMode"
      title="演示模式下数据库管理功能不可用"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    />

    <!-- 左侧面板 -->
    <div class="left-panel">
      <div class="panel-section">
        <div class="section-title">数据库</div>
        <el-menu
          :default-active="currentDatabase"
          class="db-menu"
          @select="handleDatabaseClick"
        >
          <el-menu-item
            v-for="db in databases"
            :key="db.name"
            :index="db.name"
          >
            <el-icon><Database /></el-icon>
            <span class="menu-text">{{ db.name }}</span>
            <span class="menu-badge">{{ db.tableCount }}</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="panel-section" v-if="currentDatabase">
        <div class="section-title">数据表</div>
        <div v-loading="tablesLoading" class="table-list">
          <div
            v-for="table in tables"
            :key="table.name"
            :class="['table-item', { active: currentTable === table.name }]"
            @click="handleTableClick(table.name)"
          >
            <el-icon><Grid /></el-icon>
            <span class="table-name">{{ table.name }}</span>
          </div>
          <el-empty v-if="tables.length === 0 && !tablesLoading" description="暂无数据表" :image-size="60" />
        </div>
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="right-content">
      <!-- SQL 编辑器 -->
      <el-card class="sql-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">SQL 编辑器</span>
            <div class="card-actions">
              <el-button type="primary" :loading="queryLoading" :disabled="demoModeStore.isDemoMode" @click="handleExecuteSql">
                <el-icon><VideoPlay /></el-icon>
                执行
              </el-button>
              <el-button :disabled="demoModeStore.isDemoMode" @click="handleClearSql">
                <el-icon><Delete /></el-icon>
                清空
              </el-button>
            </div>
          </div>
        </template>
        <el-alert
          title="注意：SQL 操作直接影响数据库，请谨慎执行"
          type="warning"
          :closable="false"
          show-icon
          class="sql-warning"
        />
        <el-input
          v-model="sqlContent"
          type="textarea"
          :rows="6"
          placeholder="请输入 SQL 语句..."
          class="sql-editor"
          resize="vertical"
          @keydown.ctrl.enter="handleExecuteSql"
          @keydown.meta.enter="handleExecuteSql"
        />
        <div class="sql-hint">按 Ctrl+Enter 执行 SQL</div>
      </el-card>

      <!-- 结果区域 -->
      <el-card class="result-card">
        <el-tabs v-model="activeTab">
          <!-- 表结构 -->
          <el-tab-pane label="表结构" name="table-structure" v-if="currentTable">
            <div v-loading="columnsLoading">
              <el-table
                :data="columns"
                stripe
                style="width: 100%"
                size="small"
              >
                <el-table-column prop="name" label="列名" min-width="150" />
                <el-table-column prop="type" label="类型" min-width="120" />
                <el-table-column prop="nullable" label="可空" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.nullable === 'YES' ? 'info' : 'danger'" size="small">
                      {{ row.nullable === 'YES' ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="key" label="键" width="100">
                  <template #default="{ row }">
                    <el-tag v-if="row.key === 'PRI'" type="success" size="small">主键</el-tag>
                    <el-tag v-else-if="row.key === 'UNI'" type="warning" size="small">唯一</el-tag>
                    <el-tag v-else-if="row.key === 'MUL'" size="small">索引</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="default" label="默认值" min-width="120">
                  <template #default="{ row }">
                    {{ row.default === null || row.default === undefined ? '-' : row.default }}
                  </template>
                </el-table-column>
                <el-table-column prop="comment" label="注释" min-width="150">
                  <template #default="{ row }">
                    {{ row.comment || '-' }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- 表数据 -->
          <el-tab-pane label="表数据" name="table-data" v-if="currentTable">
            <div v-loading="tableDataLoading">
              <el-table
                :data="tableData"
                stripe
                style="width: 100%"
                size="small"
                max-height="400"
              >
                <el-table-column
                  v-for="col in getTableDataColumns()"
                  :key="col"
                  :prop="col"
                  :label="col"
                  min-width="120"
                  show-overflow-tooltip
                >
                  <template #default="{ row }">
                    {{ formatValue(row[col]) }}
                  </template>
                </el-table-column>
              </el-table>
              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="tableDataPage"
                  v-model:page-size="tableDataSize"
                  :total="tableDataTotal"
                  :page-sizes="[10, 20, 50, 100]"
                  layout="total, sizes, prev, pager, next, jumper"
                  @current-change="handleTableDataPageChange"
                  @size-change="handleTableDataSizeChange"
                />
              </div>
            </div>
          </el-tab-pane>

          <!-- 查询结果 -->
          <el-tab-pane label="查询结果" name="query-result" v-if="queryResult">
            <template v-if="queryResult.columns && queryResult.columns.length > 0">
              <el-table
                :data="queryResult.rows"
                stripe
                style="width: 100%"
                size="small"
                max-height="400"
              >
                <el-table-column
                  v-for="col in queryResult.columns"
                  :key="col"
                  :prop="col"
                  :label="col"
                  min-width="120"
                  show-overflow-tooltip
                >
                  <template #default="{ row }">
                    {{ formatValue(row[col]) }}
                  </template>
                </el-table-column>
              </el-table>
              <div class="result-info">
                共 {{ queryResult.total }} 条记录
              </div>
            </template>
            <template v-else-if="queryResult.affectedRows !== undefined">
              <el-result icon="success" :title="queryResult.message || '执行成功'" />
            </template>
          </el-tab-pane>

          <!-- 空状态 -->
          <el-tab-pane v-if="!currentTable && !queryResult" label="结果" name="empty" disabled>
            <el-empty description="请选择数据表或执行 SQL 查询" />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.database-page {
  display: flex;
  gap: 16px;
  height: calc(100vh - var(--header-height, 60px) - 32px);
}

/* 左侧面板 */
.left-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.panel-section {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}

.section-title {
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.db-menu {
  border-right: none;
}

.db-menu .el-menu-item {
  height: 40px;
  line-height: 40px;
  display: flex;
  align-items: center;
}

.menu-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-badge {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color);
  padding: 0 6px;
  border-radius: 10px;
  line-height: 20px;
}

.table-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 4px 0;
}

.table-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-regular);
  transition: background-color 0.2s;
}

.table-item:hover {
  background-color: var(--el-fill-color-light);
}

.table-item.active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.table-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 右侧内容区 */
.right-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.sql-card {
  flex-shrink: 0;
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.sql-warning {
  margin-bottom: 12px;
}

.sql-editor :deep(.el-textarea__inner) {
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
}

.sql-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

/* 结果区域 */
.result-card {
  flex: 1;
  border-radius: 8px;
  overflow: hidden;
}

.result-card :deep(.el-card__body) {
  overflow: auto;
}

.result-info {
  margin-top: 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  text-align: right;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
