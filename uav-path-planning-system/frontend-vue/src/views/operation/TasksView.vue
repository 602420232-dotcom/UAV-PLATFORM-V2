<template>
  <div class="tasks-view">
    <div class="page-header">
      <h2 class="page-title">运输任务管理</h2>
      <p class="page-desc">管理无人机运输任务的全生命周期，包括新建、调度、执行跟踪和取消。</p>
    </div>

    <!-- 顶部工具栏 -->
    <el-card class="toolbar-card" shadow="never">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="12" :md="4">
          <div class="scope-info">
            <span class="scope-label">数据范围：</span>
            <DataScopeBadge
              :scope="activeScope"
              :team="authStore.team"
            />
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="4">
          <el-select
            v-model="dataScopeFilter"
            placeholder="数据范围（跟随账号）"
            clearable
            size="large"
            style="width: 100%"
          >
            <el-option label="跟随账号" value="" />
            <el-option label="仅个人" value="personal" />
            <el-option label="仅团队" value="team" />
            <el-option label="全部数据" value="all" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="4">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索任务名称/编号"
            clearable
            size="large"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态筛选"
            clearable
            size="large"
            style="width: 100%"
          >
            <el-option label="全部任务" value="" />
            <el-option label="待调度" value="待调度" />
            <el-option label="执行中" value="执行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="6" :md="4">
          <el-select
            v-model="filterPriority"
            placeholder="优先级"
            clearable
            size="large"
            style="width: 100%"
          >
            <el-option label="全部优先级" value="" />
            <el-option label="紧急" value="紧急" />
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="6" :md="8" class="actions-col">
          <el-button type="primary" size="large" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
          <el-button size="large" @click="exportTasks">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card total" shadow="never">
          <div class="stat-icon"><el-icon><Collection /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">总任务数</div>
            <div class="stat-value">{{ allTasks.length }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card new" shadow="never">
          <div class="stat-icon"><el-icon><Plus /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">今日新增</div>
            <div class="stat-value">{{ todayNewCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card running" shadow="never">
          <div class="stat-icon"><el-icon><Loading /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">执行中</div>
            <div class="stat-value">{{ runningCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card done" shadow="never">
          <div class="stat-icon"><el-icon><CircleCheck /></el-icon></div>
          <div class="stat-content">
            <div class="stat-label">已完成</div>
            <div class="stat-value">{{ doneCount }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="filteredTasks"
        border
        stripe
        size="default"
        style="width: 100%"
        :empty-text="emptyText"
      >
        <el-table-column prop="id" label="任务编号" width="140" fixed="left" />
        <el-table-column prop="name" label="任务名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="origin" label="起点" min-width="130" show-overflow-tooltip />
        <el-table-column prop="destination" label="终点" min-width="130" show-overflow-tooltip />
        <el-table-column label="重量(kg)" prop="weight" width="100" align="right" />
        <el-table-column label="优先级" prop="priority" width="90" align="center">
          <template #default="scope">
            <el-tag
              :type="getPriorityTagType(scope.row.priority)"
              :effect="getPriorityEffect(scope.row.priority)"
              size="small"
            >
              {{ scope.row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="150">
          <template #default="scope">
            <div class="owner-cell">
              <span>{{ scope.row.owner }}</span>
              <el-tag size="small" type="info" effect="plain" class="owner-team">{{ teamDisplay(scope.row.team) }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="status" width="110" align="center">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)" size="small" effect="light">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="createdAt" width="160" />
        <el-table-column label="操作" width="240" fixed="right" align="center">
          <template #default="scope">
            <el-button size="small" type="primary" link @click="viewTask(scope.row)">
              查看
            </el-button>
            <el-button
              size="small"
              type="warning"
              link
              :disabled="scope.row.status === '已完成' || scope.row.status === '已取消'"
              @click="editTask(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              :disabled="scope.row.status === '已完成' || scope.row.status === '已取消'"
              @click="cancelTask(scope.row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredTasks.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>

    <!-- 新建 / 编辑任务弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建任务' : dialogMode === 'edit' ? '编辑任务' : '任务详情'"
      width="600px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="formRules"
        label-width="90px"
        :disabled="dialogMode === 'view'"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" maxlength="50" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="起点" prop="origin">
              <el-input v-model="taskForm.origin" placeholder="起始位置" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="终点" prop="destination">
              <el-input v-model="taskForm.destination" placeholder="目的地" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="重量(kg)" prop="weight">
              <el-input-number
                v-model="taskForm.weight"
                :min="0.1"
                :max="50"
                :step="0.5"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="taskForm.priority" placeholder="选择优先级" style="width: 100%">
                <el-option label="紧急" value="紧急" />
                <el-option label="高" value="高" />
                <el-option label="中" value="中" />
                <el-option label="低" value="低" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="负责人" prop="owner">
          <el-select v-model="taskForm.owner" placeholder="选择负责人" style="width: 100%">
            <el-option label="张工" value="张工" />
            <el-option label="李工" value="李工" />
            <el-option label="王工" value="王工" />
            <el-option label="赵工" value="赵工" />
            <el-option label="陈工" value="陈工" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="taskForm.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ dialogMode === 'view' ? '关闭' : '取消' }}</el-button>
        <el-button
          v-if="dialogMode !== 'view'"
          type="primary"
          :loading="submitLoading"
          @click="submitTask"
        >
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, h, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Plus, Download, Collection, Loading, CircleCheck
} from '@element-plus/icons-vue'
import { useNotificationStore } from '../../stores/notification'
import { useAuthStore, TEAM_LABELS } from '../../stores/auth'
import DataScopeBadge from '../../components/shared/DataScopeBadge.vue'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const searchKeyword = ref('')
const filterStatus = ref('')
const filterPriority = ref('')
// dataScopeFilter: 'personal' | 'team' | 'all' | '' (跟随 authStore)
const dataScopeFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const dialogVisible = ref(false)
const dialogMode = ref('create') // create | edit | view
const submitLoading = ref(false)
const taskFormRef = ref(null)

watch(dataScopeFilter, () => { currentPage.value = 1 })

const activeScope = computed(() => dataScopeFilter.value || authStore.dataScope || 'personal')

const emptyText = h('div', { style: 'padding: 20px; color: #909399;' }, '暂无符合条件的任务')

const taskForm = reactive({
  id: '',
  name: '',
  origin: '',
  destination: '',
  weight: 1,
  priority: '中',
  owner: '',
  remark: '',
  status: '待调度',
  createdAt: ''
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  origin: [{ required: true, message: '请输入起点', trigger: 'blur' }],
  destination: [{ required: true, message: '请输入终点', trigger: 'blur' }],
  weight: [{ required: true, message: '请输入重量', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  owner: [{ required: true, message: '请选择负责人', trigger: 'change' }]
}

const OWNER_ID_MAP = {
  '张工': 'user01',
  '李工': 'flight01',
  '王工': 'prod01',
  '赵工': 'test01',
  '陈工': 'deploy01',
  'admin01': 'admin01'
}

const OWNER_TEAM_MAP = {
  '张工': 'team-a',
  '李工': 'team-b',
  '王工': 'team-a',
  '赵工': 'team-c',
  '陈工': 'team-c',
  'admin01': 'team-a'
}

const mockTasks = ref([
  { id: 'T-2026-0001', name: '医疗物资配送-西二旗', origin: '海淀仓A', destination: '西二旗医院', weight: 8.5, priority: '紧急', owner: '张工', ownerId: 'user01', team: 'team-a', status: '执行中', createdAt: '2026-06-09 08:15', remark: '血液样本,请谨慎运输' },
  { id: 'T-2026-0002', name: '生鲜配送-朝阳', origin: '通州生鲜仓', destination: '朝阳国贸', weight: 12.0, priority: '高', owner: '李工', ownerId: 'flight01', team: 'team-b', status: '待调度', createdAt: '2026-06-09 09:02', remark: '冷链运输,0-4摄氏度' },
  { id: 'T-2026-0003', name: '快递同城-A区', origin: '顺义分拣中心', destination: '望京SOHO', weight: 5.2, priority: '中', owner: '王工', ownerId: 'prod01', team: 'team-a', status: '执行中', createdAt: '2026-06-09 09:30', remark: '' },
  { id: 'T-2026-0004', name: '电力巡检-亦庄', origin: '亦庄变电站', destination: '次渠变电站', weight: 2.0, priority: '高', owner: '赵工', ownerId: 'test01', team: 'team-c', status: '已完成', createdAt: '2026-06-08 14:20', remark: '日常巡检任务' },
  { id: 'T-2026-0005', name: '应急救援-门头沟', origin: '海淀应急中心', destination: '门头沟山区', weight: 15.0, priority: '紧急', owner: '张工', ownerId: 'user01', team: 'team-a', status: '已完成', createdAt: '2026-06-08 16:45', remark: '紧急救援物资投放' },
  { id: 'T-2026-0006', name: '药品配送-丰台', origin: '丰台医药仓', destination: '丰台医院', weight: 3.5, priority: '中', owner: '陈工', ownerId: 'deploy01', team: 'team-c', status: '待调度', createdAt: '2026-06-09 10:10', remark: '常规药品配送' },
  { id: 'T-2026-0007', name: '餐饮配送-三里屯', origin: '朝阳餐饮中心', destination: '三里屯', weight: 4.8, priority: '低', owner: '李工', ownerId: 'flight01', team: 'team-b', status: '待调度', createdAt: '2026-06-09 11:00', remark: '' },
  { id: 'T-2026-0008', name: '样本运输-实验室', origin: '北医三院', destination: '中科院实验室', weight: 1.2, priority: '高', owner: '王工', ownerId: 'prod01', team: 'team-a', status: '执行中', createdAt: '2026-06-09 10:30', remark: '生物样本需冷藏' },
  { id: 'T-2026-0009', name: '文件快递-国贸', origin: 'CBD', destination: '国贸大厦', weight: 0.5, priority: '低', owner: '赵工', ownerId: 'test01', team: 'team-c', status: '已取消', createdAt: '2026-06-08 15:00', remark: '客户取消订单' },
  { id: 'T-2026-0010', name: '测绘任务-昌平', origin: '昌平基地', destination: '昌平山区', weight: 6.0, priority: '中', owner: '陈工', ownerId: 'deploy01', team: 'team-c', status: '已完成', createdAt: '2026-06-07 08:00', remark: '地形测绘任务' }
])

function _canSeeTask(ownerId, team) {
  const scope = activeScope.value
  if (scope === 'all') return true
  if (scope === 'personal') {
    const uid = authStore.userId
    return ownerId && uid && String(ownerId) === String(uid)
  }
  if (scope === 'team') {
    return team && authStore.team && team === authStore.team
  }
  return true
}

const visibleTasks = computed(() => mockTasks.value.filter(t => _canSeeTask(t.ownerId, t.team)))
const allTasks = computed(() => visibleTasks.value)

const todayNewCount = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return allTasks.value.filter(t => (t.createdAt || '').slice(0, 10) === today).length
})

const runningCount = computed(() => allTasks.value.filter(t => t.status === '执行中').length)
const doneCount = computed(() => allTasks.value.filter(t => t.status === '已完成').length)

const filteredTasks = computed(() => {
  return allTasks.value.filter(task => {
    const kw = (searchKeyword.value || '').trim().toLowerCase()
    const matchKw =
      !kw ||
      task.name.toLowerCase().includes(kw) ||
      task.id.toLowerCase().includes(kw)
    const matchStatus = !filterStatus.value || task.status === filterStatus.value
    const matchPriority = !filterPriority.value || task.priority === filterPriority.value
    return matchKw && matchStatus && matchPriority
  })
})

function teamDisplay(team) {
  return TEAM_LABELS[team] || team || '-'
}

function getPriorityTagType(priority) {
  return { 紧急: 'danger', 高: 'warning', 中: '', 低: 'info' }[priority] || 'info'
}

function getPriorityEffect(priority) {
  return priority === '紧急' || priority === '高' ? 'dark' : 'plain'
}

function getStatusTagType(status) {
  return {
    待调度: 'warning',
    执行中: 'primary',
    已完成: 'success',
    已取消: 'info'
  }[status] || 'info'
}

function resetForm() {
  Object.assign(taskForm, {
    id: '',
    name: '',
    origin: '',
    destination: '',
    weight: 1,
    priority: '中',
    owner: '',
    remark: '',
    status: '待调度',
    createdAt: ''
  })
}

function openCreateDialog() {
  resetForm()
  dialogMode.value = 'create'
  dialogVisible.value = true
}

function viewTask(row) {
  resetForm()
  Object.assign(taskForm, { ...row })
  dialogMode.value = 'view'
  dialogVisible.value = true
}

function editTask(row) {
  resetForm()
  Object.assign(taskForm, { ...row })
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

function cancelTask(row) {
  ElMessageBox.confirm(
    `确定要取消任务 "${row.name}" 吗？此操作不可撤销。`,
    '取消任务',
    {
      confirmButtonText: '确认取消',
      cancelButtonText: '返回',
      type: 'warning'
    }
  )
    .then(() => {
      const target = mockTasks.value.find(t => t.id === row.id)
      if (target) {
        target.status = '已取消'
        ElMessage.success('任务已取消')
        notificationStore.pushWithDesktop({
          type: 'danger',
          title: '任务已取消',
          message: `任务 ${row.id} · ${row.name || ''} 已被取消`,
          source: 'task'
        })
      }
    })
    .catch(() => {})
}

async function submitTask() {
  if (!taskFormRef.value) return
  await taskFormRef.value.validate((valid) => {
    if (!valid) {
      ElMessage.warning('请检查表单填写')
      return
    }
    submitLoading.value = true
    setTimeout(() => {
      if (dialogMode.value === 'create') {
        const nextNum = String(mockTasks.value.length + 1).padStart(4, '0')
        const newTask = {
          ...taskForm,
          id: 'T-2026-' + nextNum,
          status: '待调度',
          createdAt: new Date().toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
        }
        mockTasks.value.unshift(newTask)
        ElMessage.success('任务创建成功')
        notificationStore.pushWithDesktop({
          type: 'info',
          title: '新任务已创建',
          message: `任务 ${newTask.id} · ${newTask.name || ''} 已进入待调度队列`,
          source: 'task'
        })
      } else if (dialogMode.value === 'edit') {
        const target = mockTasks.value.find(t => t.id === taskForm.id)
        if (target) {
          Object.assign(target, { ...taskForm })
          ElMessage.success('任务已更新')
          notificationStore.pushWithDesktop({
            type: 'info',
            title: '任务已更新',
            message: `任务 ${taskForm.id} 参数已更新`,
            source: 'task'
          })
        }
      }
      submitLoading.value = false
      dialogVisible.value = false
    }, 500)
  })
}

function exportTasks() {
  ElMessage.info('导出任务功能演示中...')
}
</script>

<style scoped>
.tasks-view {
  padding: 16px 20px 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px;
}

.page-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.toolbar-card {
  margin-bottom: 16px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.scope-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 2px;
  min-height: 36px;
}

.scope-label {
  font-size: 13px;
  color: #606266;
}

.actions-col {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.owner-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.owner-team {
  margin-left: 0;
}

@media (min-width: 768px) {
  .actions-col {
    margin-top: 0;
  }
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 4px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
}

.stat-card.total .stat-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.stat-card.new .stat-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}
.stat-card.running .stat-icon {
  background: linear-gradient(135deg, #fa709a, #fee140);
}
.stat-card.done .stat-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  font-family: 'Courier New', monospace;
}

/* 任务表格卡片 */
.table-card {
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid #f0f2f5;
}

/* 响应式 */
@media (max-width: 768px) {
  .tasks-view {
    padding: 12px;
  }
  .page-title {
    font-size: 18px;
  }
  .stat-value {
    font-size: 22px;
  }
}
</style>
