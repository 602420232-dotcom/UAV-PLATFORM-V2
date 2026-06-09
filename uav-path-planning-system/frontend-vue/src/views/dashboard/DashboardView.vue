<template>
  <div class="dashboard">
    <!-- 1. Hero 区域 -->
    <el-card class="hero-card" shadow="never">
      <div class="hero-content">
        <div class="hero-left">
          <h1 class="hero-title">基于 WRF 气象驱动的无人机 VRP 智能路径规划系统</h1>
          <p class="hero-subtitle">城市低空物流 · 电力巡检 · 应急救援 · 农林植保 · 城市管理</p>
          <div class="hero-badges">
            <el-tag type="primary" effect="dark">v3.3.0</el-tag>
            <el-tag type="success" effect="plain">MIT License</el-tag>
            <el-tag v-if="authStore.demoMode" type="warning" effect="light">演示模式</el-tag>
          </div>
        </div>
        <div class="hero-right">
          <div class="hero-icon">🚁</div>
        </div>
      </div>
    </el-card>

    <!-- 2. 服务模块入口 -->
    <h2 class="section-title">服务模块</h2>
    <el-row :gutter="16" class="modules-grid">
      <el-col
        v-for="mod in visibleModules"
        :key="mod.key"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <el-card
          class="module-card"
          shadow="hover"
          :class="{ disabled: mod.key === 'dashboard' }"
          @click="handleModuleClick(mod)"
        >
          <div class="module-icon">{{ mod.icon }}</div>
          <div class="module-name">{{ mod.name }}</div>
          <div class="module-desc">{{ mod.desc }}</div>
          <el-button
            type="primary"
            plain
            size="small"
            :disabled="mod.key === 'dashboard'"
            class="module-btn"
          >
            {{ mod.key === 'dashboard' ? '当前位置' : '立即进入' }}
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- 3. 系统公告 -->
    <el-card shadow="never" class="info-card notice-card">
      <template #header>
        <div class="card-header">
          <span class="header-icon">📢</span>
          <span>系统公告</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(notice, idx) in notices"
          :key="idx"
          :timestamp="notice.time"
          placement="top"
          :type="notice.type"
        >
          <div class="notice-title">{{ notice.title }}</div>
          <div class="notice-desc">{{ notice.desc }}</div>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 4. 外部资源链接（分类卡片，不挤不乱） -->
    <h2 class="section-title">外部资源</h2>
    <el-row :gutter="16" class="links-row">
      <el-col
        v-for="group in linkGroups"
        :key="group.title"
        :xs="24"
        :sm="12"
        :md="12"
        :lg="6"
      >
        <el-card shadow="hover" class="link-card" :class="group.cls">
          <template #header>
            <div class="link-card-header">
              <span class="link-card-icon">{{ group.icon }}</span>
              <div>
                <div class="link-card-title">{{ group.title }}</div>
                <div class="link-card-subtitle">{{ group.subtitle }}</div>
              </div>
            </div>
          </template>
          <div class="link-list">
            <a
              v-for="link in group.links"
              :key="link.url"
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer"
              class="link-row"
            >
              <span class="link-row-name">{{ link.name }}</span>
              <span class="link-row-desc">{{ link.desc }}</span>
              <span class="link-row-arrow">↗</span>
            </a>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 5. 四大气象模型数据简介 -->
    <h2 class="section-title">气象模型数据</h2>
    <div class="models-scroll">
      <div class="models-track">
        <el-card
          v-for="model in weatherModels"
          :key="model.name"
          shadow="hover"
          class="model-card"
        >
          <div class="model-header">
            <span class="model-badge" :style="{ background: model.color }">{{ model.tag }}</span>
            <span class="model-name">{{ model.name }}</span>
          </div>
          <div class="model-meta">
            <div class="meta-row">
              <span class="meta-label">分辨率</span>
              <span class="meta-value">{{ model.resolution }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">更新频率</span>
              <span class="meta-value">{{ model.freq }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">数据源</span>
              <span class="meta-value">{{ model.source }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 模块清单
const modules = [
  { key: 'dashboard', name: '首页', desc: '项目简介与模块入口', icon: '🏠' },
  { key: 'weather', name: '气象数据', desc: '多模型气象查询与对比', icon: '⛅' },
  { key: 'orders', name: '下单服务', desc: '选择起点 / 终点下单', icon: '📦' },
  { key: 'cockpit', name: '智能驾驶舱', desc: '无人机飞行状态可视化', icon: '🚁' },
  { key: 'tasks', name: '任务管理', desc: '运输任务全生命周期', icon: '📋' },
  { key: 'path-planning', name: '路径规划', desc: 'WRF 气象驱动 VRP 求解', icon: '🗺️' },
  { key: 'assimilation', name: '数据同化', desc: '多源观测数据融合', icon: '🔄' },
  { key: 'monitoring', name: '系统监控', desc: '服务运行状态实时监控', icon: '📊' },
  { key: 'database', name: '数据库管理', desc: '数据管理与维护', icon: '🗄️' },
  { key: 'docker', name: 'Docker 状态', desc: '容器与服务器运行状态', icon: '🐳' },
  { key: 'api-config', name: 'API 配置', desc: '气象模型 API 接入配置', icon: '⚙️' }
]

const visibleModules = computed(() =>
  modules.filter(m => authStore.hasRouteAccess(m.key))
)

function handleModuleClick(mod) {
  if (mod.key === 'dashboard') return
  router.push('/' + mod.key)
}

// 公告
const notices = [
  {
    time: '2026-06-08',
    type: 'primary',
    title: 'v3.3.0 版本发布',
    desc: '新增风乌 FengWu 模型接入，优化 VRP 求解算法性能约 23%。'
  },
  {
    time: '2026-05-25',
    type: 'success',
    title: '智能驾驶舱可视化重构',
    desc: '驾驶舱支持 3D 路径回放与多机协同编队监控。'
  },
  {
    time: '2026-05-10',
    type: 'warning',
    title: '服务维护计划',
    desc: '2026-06-15 02:00-04:00 气象数据 API 服务维护，期间可能不可用。'
  },
  {
    time: '2026-04-20',
    type: 'info',
    title: '新角色权限上线',
    desc: '新增部署人员角色，支持 Docker 与 API 配置模块独立查看。'
  }
]

// 外部资源链接（分类卡片）
const linkGroups = [
  {
    title: '核心数据源 / 机构',
    subtitle: '官方数据源与权威机构',
    icon: '🏛️',
    cls: 'link-card-source',
    links: [
      {
        name: '中国气象局',
        url: 'http://www.cma.gov.cn/',
        desc: '天资 / 风雷数据源官方入口'
      },
      {
        name: '国家气象科学数据中心',
        url: 'https://data.cma.cn/',
        desc: '气象数据下载 / 接口文档'
      },
      {
        name: '上海人工智能实验室',
        url: 'https://www.shlab.org.cn/',
        desc: '风乌模型所属机构'
      }
    ]
  },
  {
    title: '技术生态 / 开源',
    subtitle: '代码与镜像、核心技术参考',
    icon: '🧰',
    cls: 'link-card-tech',
    links: [
      {
        name: '项目 GitHub',
        url: 'https://github.com/602420232-dotcom/weather',
        desc: '代码仓库'
      },
      {
        name: 'Docker Hub 镜像',
        url: 'https://hub.docker.com/repositories/dithiothreitollf',
        desc: '预构建镜像，部署直接拉取'
      },
      {
        name: 'WRF 官方文档',
        url: 'https://www.mmm.ucar.edu/models/wrf',
        desc: '基础气象模型参考'
      },
      {
        name: 'NetCDF 官方文档',
        url: 'https://www.unidata.ucar.edu/software/netcdf/',
        desc: 'WRF 气象数据格式参考，用户处理上传文件'
      },
      {
        name: 'ONNX Runtime 文档',
        url: 'https://onnxruntime.ai/docs/',
        desc: '风乌模型推理技术参考'
      },
      {
        name: 'Nacos 官方文档',
        url: 'https://nacos.io/zh-cn/docs/',
        desc: '服务配置中心'
      }
    ]
  },
  {
    title: '行业场景合规',
    subtitle: '无人机 / 低空经济相关规范',
    icon: '📜',
    cls: 'link-card-compliance',
    links: [
      {
        name: '中国民航局低空经济专栏',
        url: 'http://www.caac.gov.cn/ztzl/kongdi/',
        desc: '无人机行业合规参考'
      }
    ]
  },
  {
    title: '许可证相关',
    subtitle: '开源协议说明',
    icon: '📄',
    cls: 'link-card-license',
    links: [
      {
        name: 'MIT License 官网',
        url: 'https://opensource.org/licenses/MIT',
        desc: '项目开源协议全文'
      }
    ]
  }
]

// 气象模型
const weatherModels = [
  {
    name: 'WRF',
    tag: 'WRF',
    color: 'linear-gradient(135deg, #409EFF, #1890FF)',
    resolution: '3km × 3km',
    freq: '每 6 小时',
    source: 'NCAR / 本地数值模式'
  },
  {
    name: '风乌 FengWu',
    tag: '风乌',
    color: 'linear-gradient(135deg, #67C23A, #52C41A)',
    resolution: '0.25° × 0.25°',
    freq: '每日更新',
    source: '上海 AI 实验室'
  },
  {
    name: '天资 TianZi',
    tag: '天资',
    color: 'linear-gradient(135deg, #E6A23C, #FAAD14)',
    resolution: '1° × 1°',
    freq: '每日更新',
    source: '中国气象局'
  },
  {
    name: '风雷 FengLei',
    tag: '风雷',
    color: 'linear-gradient(135deg, #F56C6C, #F5222D)',
    resolution: '1km × 1km',
    freq: '每 3 小时',
    source: '本地雷达 + 数值融合'
  }
]
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

/* Hero */
.hero-card {
  border-radius: 12px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f9ff 50%, #fffbe6 100%);
  border: 1px solid #e6f0fa;
}

.hero-card :deep(.el-card__body) {
  padding: 32px;
}

.hero-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.hero-left {
  flex: 1;
}

.hero-title {
  font-size: 28px;
  color: #1f2937;
  margin: 0 0 12px;
  font-weight: 600;
  line-height: 1.35;
}

.hero-subtitle {
  font-size: 15px;
  color: #6b7280;
  margin: 0 0 20px;
}

.hero-badges {
  display: flex;
  gap: 10px;
}

.hero-right {
  flex-shrink: 0;
}

.hero-icon {
  font-size: 84px;
  line-height: 1;
  filter: drop-shadow(0 4px 12px rgba(64, 158, 255, 0.3));
}

/* 标题 */
.section-title {
  font-size: 18px;
  color: #1f2937;
  margin: 0 0 12px;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

/* 模块卡片 */
.modules-grid {
  margin-bottom: 24px;
}

.modules-grid .el-col {
  margin-bottom: 16px;
}

.module-card {
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  text-align: center;
  height: 100%;
}

.module-card:not(.disabled):hover {
  transform: translateY(-3px);
}

.module-card.disabled {
  cursor: default;
  background: #f9fafb;
}

.module-icon {
  font-size: 44px;
  margin-bottom: 10px;
}

.module-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.module-desc {
  font-size: 13px;
  color: #6b7280;
  min-height: 34px;
  margin-bottom: 12px;
}

.module-btn {
  width: 100%;
}

/* 公告卡片 */
.notice-card {
  border-radius: 10px;
  margin-bottom: 24px;
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

.notice-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.notice-desc {
  font-size: 13px;
  color: #6b7280;
}

/* 链接分类卡片行 */
.links-row {
  margin-bottom: 24px;
}

.links-row .el-col {
  margin-bottom: 16px;
}

.link-card {
  border-radius: 10px;
  height: 100%;
  border: 1px solid #e5e7eb;
}

.link-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.link-card-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.link-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.link-card-subtitle {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 四类卡片的顶部高亮色（视觉上能一眼分清） */
.link-card-source {
  border-top: 3px solid #409EFF;
}

.link-card-tech {
  border-top: 3px solid #67C23A;
}

.link-card-compliance {
  border-top: 3px solid #E6A23C;
}

.link-card-license {
  border-top: 3px solid #F56C6C;
}

/* 链接行（每一项名称 + 说明 + 箭头） */
.link-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.link-row {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-areas:
    "name   arrow"
    "desc   arrow";
  row-gap: 2px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: #374151;
  transition: background-color 0.15s, color 0.15s;
}

.link-row:hover {
  background-color: #f3f4f6;
  color: #1f2937;
}

.link-row-name {
  grid-area: name;
  font-size: 13.5px;
  font-weight: 500;
  color: #1f2937;
}

.link-row-desc {
  grid-area: desc;
  font-size: 12px;
  color: #6b7280;
}

.link-row-arrow {
  grid-area: arrow;
  font-size: 14px;
  color: #9ca3af;
  transition: color 0.15s, transform 0.15s;
}

.link-row:hover .link-row-name {
  color: #409EFF;
}

.link-row:hover .link-row-arrow {
  color: #409EFF;
  transform: translate(2px, -2px);
}

/* 模型横向滚动 */
.models-scroll {
  overflow-x: auto;
  padding-bottom: 8px;
}

.models-track {
  display: flex;
  gap: 16px;
  min-width: min-content;
}

.model-card {
  border-radius: 10px;
  width: 260px;
  flex-shrink: 0;
}

.model-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.model-badge {
  display: inline-block;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
}

.model-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.model-meta .meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding: 4px 0;
}

.meta-label {
  color: #6b7280;
}

.meta-value {
  color: #1f2937;
  font-weight: 500;
}
</style>
