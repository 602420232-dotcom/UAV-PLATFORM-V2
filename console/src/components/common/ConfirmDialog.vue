<script setup lang="ts">
const props = withDefaults(defineProps<{
  visible: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'warning' | 'danger' | 'info'
}>(), {
  title: '确认操作',
  confirmText: '确认',
  cancelText: '取消',
  type: 'warning',
})

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleConfirm() {
  emit('confirm')
  emit('update:visible', false)
}

function handleCancel() {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    width="420px"
    @close="handleCancel"
  >
    <div class="confirm-content">
      <el-icon :size="24" :color="type === 'danger' ? 'var(--color-danger)' : 'var(--color-warning)'">
        <WarningFilled v-if="type === 'warning'" />
        <CircleCloseFilled v-else-if="type === 'danger'" />
        <InfoFilled v-else />
      </el-icon>
      <span>{{ message }}</span>
    </div>
    <template #footer>
      <el-button @click="handleCancel">{{ cancelText }}</el-button>
      <el-button
        :type="type === 'danger' ? 'danger' : 'primary'"
        @click="handleConfirm"
      >
        {{ confirmText }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.confirm-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}
</style>
