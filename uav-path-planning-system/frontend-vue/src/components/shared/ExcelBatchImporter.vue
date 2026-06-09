<template>
  <el-dialog
    v-model="dialogVisible"
    title="Excel 批量导入任务点"
    width="680px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <!-- 步骤 1：文件上传 -->
    <div v-if="step === 1" class="step-content">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        支持 .xlsx / .xls 格式，Excel 中需包含 <strong>纬度</strong> 和 <strong>经度</strong> 列
      </el-alert>

      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        class="upload-area"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖放文件或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">文件需小于 10MB</div>
        </template>
      </el-upload>

      <div v-if="parseError" class="error-msg">
        <el-icon color="#F56C6C"><CircleClose /></el-icon>
        {{ parseError }}
      </div>
    </div>

    <!-- 步骤 2：字段映射 -->
    <div v-if="step === 2" class="step-content">
      <el-alert type="success" :closable="false" style="margin-bottom: 16px">
        解析成功，共 <strong>{{ parsedRows.length }}</strong> 个有效航点，请确认字段映射
      </el-alert>

      <el-form label-width="100px" size="small">
        <el-form-item label="纬度列">
          <el-select v-model="fieldMap.lat" placeholder="选择纬度列" style="width: 100%">
            <el-option v-for="col in sheetColumns" :key="col" :label="col" :value="col" />
          </el-select>
        </el-form-item>
        <el-form-item label="经度列">
          <el-select v-model="fieldMap.lng" placeholder="选择经度列" style="width: 100%">
            <el-option v-for="col in sheetColumns" :key="col" :label="col" :value="col" />
          </el-select>
        </el-form-item>
        <el-form-item label="航点名（可选）">
          <el-select v-model="fieldMap.name" placeholder="不设置" clearable style="width: 100%">
            <el-option v-for="col in sheetColumns" :key="col" :label="col" :value="col" />
          </el-select>
        </el-form-item>
        <el-form-item label="高度（可选）">
          <el-select v-model="fieldMap.alt" placeholder="不设置" clearable style="width: 100%">
            <el-option v-for="col in sheetColumns" :key="col" :label="col" :value="col" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注（可选）">
          <el-select v-model="fieldMap.desc" placeholder="不设置" clearable style="width: 100%">
            <el-option v-for="col in sheetColumns" :key="col" :label="col" :value="col" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认高度">
          <el-input-number v-model="defaultAlt" :min="5" :max="500" :step="5" style="width: 100%" />
          <div class="form-tip">当高度列未指定时使用此值（米）</div>
        </el-form-item>
      </el-form>

      <!-- 预览前 10 条 -->
      <div class="preview-table">
        <div class="preview-title">数据预览（前 10 条）</div>
        <el-table :data="previewRows" border size="small" max-height="200" style="width: 100%">
          <el-table-column prop="_index" label="#" width="50" />
          <el-table-column prop="_lat" label="纬度" width="110" />
          <el-table-column prop="_lng" label="经度" width="110" />
          <el-table-column prop="_name" label="航点名" min-width="100" />
          <el-table-column prop="_alt" label="高度(m)" width="80" />
        </el-table>
      </div>
    </div>

    <!-- 步骤 3：确认导入 -->
    <div v-if="step === 3" class="step-content">
      <el-result icon="success" title="数据就绪" sub-title="确认后将从第 {{ importStartRow }} 行开始导入，共 {{ validWaypoints.length }} 个航点">
        <template #extra>
          <el-button type="primary" @click="confirmImport">确认导入</el-button>
        </template>
      </el-result>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button v-if="step === 1" :disabled="!selectedFile" type="primary" :loading="parsing" @click="parseFile">
          解析文件
        </el-button>
        <el-button v-if="step === 2" :disabled="!canProceed" type="primary" @click="proceedToConfirm">
          下一步
        </el-button>
        <el-button v-if="step === 2" @click="step = 1">重新选择文件</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'import'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const step = ref(1)
const parsing = ref(false)
const selectedFile = ref(null)
const parseError = ref('')
const uploadRef = ref(null)
const rawData = ref([])
const sheetColumns = ref([])
const fieldMap = ref({ lat: '', lng: '', name: '', alt: '', desc: '' })
const defaultAlt = ref(50)
const importStartRow = ref(2)

const parsedRows = computed(() => rawData.value.slice(1)) // 跳过表头

const previewRows = computed(() => {
  const rows = parsedRows.value.slice(0, 10)
  return rows.map((row, i) => ({
    _index: i + 1,
    _lat: fieldMap.value.lat ? row[fieldMap.value.lat] : '—',
    _lng: fieldMap.value.lng ? row[fieldMap.value.lng] : '—',
    _name: fieldMap.value.name ? row[fieldMap.value.name] : '—',
    _alt: fieldMap.value.alt ? row[fieldMap.value.alt] : defaultAlt.value
  }))
})

const validWaypoints = computed(() => {
  return parsedRows.value
    .filter(row => {
      const lat = parseFloat(fieldMap.value.lat ? row[fieldMap.value.lat] : '')
      const lng = parseFloat(fieldMap.value.lng ? row[fieldMap.value.lng] : '')
      return !isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
    })
    .map((row, i) => ({
      id: `imported_${Date.now()}_${i}`,
      name: fieldMap.value.name ? String(row[fieldMap.value.name] || `WP${i + 1}`) : `WP${i + 1}`,
      lat: parseFloat(row[fieldMap.value.lat]),
      lng: parseFloat(row[fieldMap.value.lng]),
      alt: fieldMap.value.alt ? parseFloat(row[fieldMap.value.alt]) || defaultAlt.value : defaultAlt.value,
      description: fieldMap.value.desc ? String(row[fieldMap.value.desc] || '') : '',
      danger: 0
    }))
})

const canProceed = computed(() =>
  fieldMap.value.lat && fieldMap.value.lng
)

async function handleFileChange(file) {
  selectedFile.value = file.raw
  parseError.value = ''
  step.value = 1
}

function handleFileRemove() {
  selectedFile.value = null
  rawData.value = []
  sheetColumns.value = []
  parseError.value = ''
  step.value = 1
}

async function parseFile() {
  if (!selectedFile.value) return
  parsing.value = true
  parseError.value = ''
  try {
    const XLSX = await import('xlsx').then(m => m.default || m)
    const data = await selectedFile.value.arrayBuffer()
    const workbook = XLSX.read(data, { type: 'array' })
    const sheetName = workbook.SheetNames[0]
    const sheet = workbook.Sheets[sheetName]
    const json = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
    if (json.length < 2) {
      parseError.value = '文件内容为空或格式不正确'
      return
    }
    rawData.value = json
    const headers = json[0].map(h => String(h).trim())
    sheetColumns.value = headers
    // 自动尝试匹配
    const lower = headers.map(h => h.toLowerCase())
    fieldMap.value.lat = headers[lower.findIndex(h => /lat|latitude|latitude|纬度/.test(h))] || ''
    fieldMap.value.lng = headers[lower.findIndex(h => /lng|lon|lonitude|lng|经度|经度/.test(h))] || ''
    fieldMap.value.name = headers[lower.findIndex(h => /name|label|point|名称|点名/.test(h))] || ''
    fieldMap.value.alt = headers[lower.findIndex(h => /alt|height|elevation|高度/.test(h))] || ''
    fieldMap.value.desc = headers[lower.findIndex(h => /desc|remark|note|备注/.test(h))] || ''
    step.value = 2
  } catch (e) {
    parseError.value = `解析失败：${e.message || '文件格式不正确'}`
  } finally {
    parsing.value = false
  }
}

function proceedToConfirm() {
  if (validWaypoints.value.length === 0) {
    ElMessage.warning('未找到有效航点，请检查经纬度列映射')
    return
  }
  step.value = 3
}

function confirmImport() {
  emit('import', validWaypoints.value)
  ElMessage.success(`成功导入 ${validWaypoints.value.length} 个航点`)
  handleCancel()
}

function handleCancel() {
  dialogVisible.value = false
  setTimeout(reset, 300)
}

function reset() {
  step.value = 1
  selectedFile.value = null
  rawData.value = []
  sheetColumns.value = []
  fieldMap.value = { lat: '', lng: '', name: '', alt: '', desc: '' }
  parseError.value = ''
  if (uploadRef.value) uploadRef.value.clearFiles()
}
</script>

<style scoped>
.step-content { min-height: 200px; }
.upload-area { width: 100%; }
.error-msg {
  margin-top: 12px;
  color: #F56C6C;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.preview-table { margin-top: 16px; }
.preview-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
