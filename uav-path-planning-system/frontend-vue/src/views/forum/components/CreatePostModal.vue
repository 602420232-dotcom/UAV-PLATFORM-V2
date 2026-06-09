<template>
  <el-dialog
    :title="t('forum.createPost')"
    v-model="dialogVisible"
    width="700px"
    :close-on-click-modal="false"
    class="create-post-modal"
  >
    <div class="form-container">
      <el-form :model="form" ref="formRef" label-width="80px">
        <el-form-item :label="t('forum.section') || '板块'" required>
          <el-select v-model="form.section" :placeholder="t('forum.selectSection') || '请选择板块'">
            <el-option
              v-for="section in sections"
              :key="section.key"
              :label="section.label"
              :value="section.key"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="t('forum.postTitle') || '标题'" required>
          <el-input
            v-model="form.title"
            :placeholder="t('forum.titlePlaceholder') || '请输入帖子标题'"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item :label="t('forum.content') || '内容'" required>
          <textarea
            v-model="form.content"
            :placeholder="t('forum.contentPlaceholder') || '请输入帖子内容（支持HTML格式）'"
            class="content-textarea"
            rows="8"
          ></textarea>
        </el-form-item>

        <el-form-item :label="t('forum.tags') || '标签'">
          <el-input
            v-model="tagInput"
            :placeholder="t('forum.tagPlaceholder') || '输入标签后按回车添加'"
            @keyup.enter="addTag"
          />
          <div class="tags-container">
            <el-tag
              v-for="(tag, index) in form.tags"
              :key="index"
              closable
              @close="removeTag(index)"
            >
              {{ tag }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item>
          <div class="form-actions">
            <el-button @click="handleClose">{{ t('forum.cancel') }}</el-button>
            <el-button type="primary" @click="submitForm" :loading="submitting">
              {{ t('forum.publish') || '发布帖子' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import forumApi from '@/api/forum';

const { t } = useI18n();
const authStore = useAuthStore();

const props = defineProps({
  section: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['close', 'created']);

const sections = ref([]);
const tagInput = ref('');
const formRef = ref(null);
const submitting = ref(false);

// 对话框显示状态
const dialogVisible = ref(true);

const form = reactive({
  section: props.section,
  title: '',
  content: '',
  tags: []
});

const addTag = () => {
  const tag = tagInput.value.trim();
  if (tag && !form.tags.includes(tag) && form.tags.length < 5) {
    form.tags.push(tag);
    tagInput.value = '';
  }
};

const removeTag = (index) => {
  form.tags.splice(index, 1);
};

const handleClose = () => {
  emit('close');
};

const submitForm = async () => {
  if (!form.section || !form.title.trim() || !form.content.trim()) {
    ElMessage.warning(t('common.fillRequired') || '请填写必填项');
    return;
  }

  submitting.value = true;
  try {
    await forumApi.createPost({
      title: form.title.trim(),
      content: form.content.trim(),
      section: form.section,
      tags: [...form.tags],
      authorId: authStore.userId
    });

    ElMessage.success(t('common.operationSuccess') || '操作成功');
    emit('created');
  } catch (error) {
    ElMessage.error(t('common.operationFailed') + ': ' + error.message);
  } finally {
    submitting.value = false;
  }
};

onMounted(async () => {
  const data = await forumApi.getSections();
  sections.value = data;
});
</script>

<style scoped>
.create-post-modal {
  :deep(.el-dialog__body) {
    padding: 20px;
  }
}

.form-container {
  .content-textarea {
    width: 100%;
    border: 1px solid var(--el-border-color-lighter, #e4e7ed);
    border-radius: 4px;
    padding: 10px;
    font-size: 14px;
    resize: none;
    outline: none;
    transition: border-color 0.2s;
    background: var(--el-fill-color-light, #f5f7fa);
    color: var(--el-text-color-primary, #303133);
  }

  .content-textarea:focus {
    border-color: var(--el-color-primary, #409eff);
  }

  .content-textarea::placeholder {
    color: var(--el-text-color-secondary, #909399);
  }

  .tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
}

/* ===== 暗色模式全局覆盖 ===== */
:deep(.el-dialog) {
  background: var(--el-bg-color, #ffffff) !important;
}

:deep(.el-dialog__header) {
  background: var(--el-fill-color-lighter, #f5f7fa) !important;
  border-bottom: 1px solid var(--el-border-color-lighter, #e4e7ed) !important;
}

:deep(.el-dialog__title) {
  color: var(--el-text-color-primary, #303133) !important;
}

:deep(.el-dialog__body) {
  background: var(--el-bg-color, #ffffff) !important;
  color: var(--el-text-color-primary, #303133) !important;
}
</style>
