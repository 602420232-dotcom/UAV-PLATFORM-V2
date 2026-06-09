<template>
  <div class="forum-container">
    <div class="forum-header">
      <div class="header-title">
        <el-icon class="title-icon"><Message /></el-icon>
        <h1>{{ t('forum.title') }}</h1>
      </div>
      <el-button 
        type="primary" 
        size="default"
        :disabled="!canPost"
        @click="showCreatePostModal = true"
        class="create-btn"
      >
        <el-icon><EditPen /></el-icon>
        {{ t('forum.createPost') }}
      </el-button>
    </div>

    <div class="forum-body">
      <div class="sidebar">
        <div class="section-list">
          <div 
            v-for="section in sections" 
            :key="section.key"
            class="section-item"
            :class="{ active: activeSection === section.key }"
            @click="selectSection(section.key)"
          >
            <el-icon class="section-icon">{{ getSectionIcon(section.key) }}</el-icon>
            <span>{{ getSectionLabel(section.key) }}</span>
            <span class="section-count">{{ getSectionCount(section.key) }}</span>
          </div>
        </div>

        <div class="quick-actions">
          <h3>{{ t('forum.quickActions') }}</h3>
          <div class="action-item" @click="showMyPosts">
            <el-icon><User /></el-icon>
            <span>{{ t('forum.myPosts') }}</span>
          </div>
          <div class="action-item" @click="showMyFavorites">
            <el-icon><Star /></el-icon>
            <span>{{ t('forum.myFavorites') }}</span>
          </div>
        </div>
      </div>

      <div class="main-content">
        <div class="filter-bar">
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索帖子..." 
            class="search-input"
            prefix-icon="Search"
            @input="handleSearch"
          />
          <el-select 
            v-model="sortBy" 
            placeholder="排序方式" 
            class="sort-select"
          >
            <el-option label="最新发布" value="latest" />
            <el-option label="最多回复" value="comments" />
            <el-option label="最多浏览" value="views" />
          </el-select>
        </div>

        <div class="post-list">
          <div 
            v-for="post in posts" 
            :key="post.id" 
            class="post-card"
            @click="viewPost(post)"
          >
            <div class="post-header">
              <div class="author-info">
                <img :src="post.author.avatar" :alt="post.author.displayName" class="author-avatar" />
                <span class="author-name">{{ post.author.displayName }}</span>
                <span class="post-time">{{ formatTime(post.createdAt) }}</span>
              </div>
              <div class="post-tags">
                <el-tag 
                  v-for="tag in post.tags" 
                  :key="tag" 
                  size="small" 
                  class="post-tag"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            <div class="post-title">
              <span v-if="post.status === 'pinned'" class="pin-icon">📌</span>
              {{ post.title }}
            </div>
            <div class="post-preview">{{ stripHtml(post.content) }}</div>
            <div class="post-footer">
              <span class="footer-item">
                <el-icon><Search /></el-icon>
                {{ post.viewCount }}
              </span>
              <span class="footer-item">
                <el-icon><Message /></el-icon>
                {{ post.commentCount }}
              </span>
              <span class="footer-item">
                <el-icon><Check /></el-icon>
                {{ post.likeCount }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="total > pageSize" class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next, jumper"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </div>

    <PostDetailModal 
      v-if="showPostDetail" 
      :post="selectedPost"
      @close="showPostDetail = false"
    />

    <CreatePostModal 
      v-if="showCreatePostModal"
      :section="activeSection"
      @close="showCreatePostModal = false"
      @created="handlePostCreated"
    />
  </div>
</template>

<script setup>import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '@/stores/auth';
import { EditPen, Search, User, Star, Message, Check, Bell } from '@element-plus/icons-vue';
import forumApi, { SECTIONS } from '@/api/forum';
import PostDetailModal from './components/PostDetailModal.vue';
import CreatePostModal from './components/CreatePostModal.vue';
const { t } = useI18n();
const authStore = useAuthStore();
const sections = ref([]);
const posts = ref([]);
const activeSection = ref('');
const searchKeyword = ref('');
const sortBy = ref('latest');
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const showPostDetail = ref(false);
const showCreatePostModal = ref(false);
const selectedPost = ref(null);
const sectionStats = ref({}); // 存储每个板块的帖子总数
const canPost = computed(() => {
  return authStore.hasAction('forum:post');
});

const canReply = computed(() => {
  return authStore.hasAction('forum:comment');
});
const getSectionIcon = (section) => {
 const icons = {
 [SECTIONS.ANNOUNCEMENT]: Bell,
 [SECTIONS.TECH_DISCUSS]: Message,
 [SECTIONS.TASK_COLLAB]: User,
 [SECTIONS.KNOWLEDGE]: Star
 };
 return icons[section] || Message;
};

const getSectionLabel = (section) => {
  // 直接使用中文标签，避免翻译键不匹配问题
  const labels = {
    'announcement': '公告通知',
    'announcements': '公告通知',
    'tech_discuss': '技术讨论',
    'tech_discussion': '技术讨论',
    'task_collab': '任务协作',
    'task_collaboration': '任务协作',
    'knowledge': '知识库',
    'knowledge_sharing': '知识库'
  };
  // 安全返回：如果section为空或undefined，返回默认文本
  if (!section) {
    return '未知板块';
  }
  // 返回映射的标签，如果找不到则格式化section key为可读文本
  return labels[section] || String(section).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

const getSectionCount = (section) => {
  // 返回该板块的帖子总数
  // 如果API返回了sectionStats，使用它；否则使用本地统计
  if (sectionStats.value && sectionStats.value[section] !== undefined) {
    return sectionStats.value[section];
  }
  // 回退：统计当前加载的帖子
  const count = posts.value.filter(p => p.section === section).length;
  return count;
};
const selectSection = (section) => {
 activeSection.value = section;
 currentPage.value = 1;
 loadPosts();
};
const handleSearch = () => {
 currentPage.value = 1;
 loadPosts();
};
const handlePageChange = (page) => {
 currentPage.value = page;
 loadPosts();
};
const loadPosts = async () => {
 const params = {
 section: activeSection.value || undefined,
 search: searchKeyword.value || undefined,
 page: currentPage.value,
 pageSize: pageSize.value
 };
 const result = await forumApi.getPosts(params);
 posts.value = result.list;
 total.value = result.total;
};
const viewPost = async (post) => {
 selectedPost.value = post;
 showPostDetail.value = true;
};
const handlePostCreated = () => {
  showCreatePostModal.value = false;
  loadPosts();
  loadSectionStats(); // 更新板块统计
};

const loadSectionStats = async () => {
  try {
    const stats = await forumApi.getSectionStats();
    sectionStats.value = stats;
  } catch (error) {
    console.error('加载板块统计失败:', error);
  }
};

const showMyPosts = () => {
};
const showMyFavorites = () => {
};
const formatTime = (dateStr) => {
 const date = new Date(dateStr);
 const now = new Date();
 const diff = now - date;
 const minutes = Math.floor(diff / 60000);
 const hours = Math.floor(diff / 3600000);
 const days = Math.floor(diff / 86400000);
 if (minutes < 1)
 return '刚刚';
 if (minutes < 60)
 return `${minutes}分钟前`;
 if (hours < 24)
 return `${hours}小时前`;
 if (days < 7)
 return `${days}天前`;
 return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};
const stripHtml = (html) => {
 const tmp = document.createElement('DIV');
 tmp.innerHTML = html;
 const text = tmp.textContent || tmp.innerText || '';
 return text.length > 100 ? text.substring(0, 100) + '...' : text;
};
onMounted(async () => {
  const sectionsData = await forumApi.getSections();
  sections.value = sectionsData;
  if (sectionsData.length > 0) {
  activeSection.value = sectionsData[0].key;
  }
  await Promise.all([
    loadPosts(),
    loadSectionStats()
  ]);
});
</script>

<style scoped>
.forum-container {
  min-height: 100%;
  background: #f5f7fa;
  padding: 20px;
}

.forum-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 28px;
  color: #409eff;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

.forum-body {
  display: flex;
  gap: 20px;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
}

.section-list {
  background: #fff;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 16px;
}

.section-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.section-item:hover {
  background: #f5f7fa;
}

.section-item.active {
  background: #ecf5ff;
  color: #409eff;
}

.section-icon {
  font-size: 18px;
}

.section-count {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 10px;
}

.section-item.active .section-count {
  background: #409eff;
  color: #fff;
}

.quick-actions {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
}

.quick-actions h3 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #606266;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-item:hover {
  background: #f5f7fa;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.search-input {
  width: 300px;
}

.sort-select {
  width: 150px;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e4e7ed;
}

.post-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.author-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.post-time {
  font-size: 12px;
  color: #909399;
}

.post-tags {
  display: flex;
  gap: 8px;
}

.post-tag {
  background: #ecf5ff;
  color: #409eff;
  border: none;
}

.post-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
  line-height: 1.5;
}

.pin-icon {
  margin-right: 8px;
}

.post-preview {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.post-footer {
  display: flex;
  gap: 20px;
  color: #909399;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .forum-body {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
  }

  .section-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .section-item {
    flex: 1;
    min-width: calc(50% - 4px);
    justify-content: center;
  }

  .filter-bar {
    flex-direction: column;
  }

  .search-input, .sort-select {
    width: 100%;
  }
}

/* ===== 暗色模式适配 ===== */
.is-dark .forum-container {
  background: var(--color-bg);
}

.is-dark .header-title h1 {
  color: var(--color-text);
}

.is-dark .section-list {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.is-dark .section-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.is-dark .section-item.active {
  background: rgba(96, 165, 250, 0.15);
  color: var(--color-primary);
}

.is-dark .section-count {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-muted);
}

.is-dark .section-item.active .section-count {
  background: var(--color-primary);
  color: #fff;
}

.is-dark .quick-actions {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.is-dark .quick-actions h3 {
  color: var(--color-text-muted);
}

.is-dark .action-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.is-dark .post-card {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

.is-dark .post-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  border-color: var(--color-primary);
}

.is-dark .author-name {
  color: var(--color-text);
}

.is-dark .post-time {
  color: var(--color-text-muted);
}

.is-dark .post-tag {
  background: rgba(96, 165, 250, 0.15);
  color: var(--color-primary);
}

.is-dark .post-title {
  color: var(--color-text);
}

.is-dark .post-preview {
  color: var(--color-text-muted);
}

.is-dark .post-footer {
  color: var(--color-text-muted);
}
</style>