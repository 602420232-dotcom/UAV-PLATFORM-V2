<template>
  <div class="docs-page">
    <div class="docs-grid">
      <!-- 左侧目录（保持不变） -->
      <aside class="docs-toc">
        <div class="toc-title">文档目录</div>
        <el-menu
          :default-active="activeSection"
          class="toc-menu"
          @select="onSelectSection"
        >
          <el-menu-item index="quickstart">
            <el-icon><Lightning /></el-icon>
            <span>快速开始</span>
          </el-menu-item>
          <el-menu-item index="roles">
            <el-icon><UserFilled /></el-icon>
            <span>角色与权限</span>
          </el-menu-item>
          <el-menu-item index="weather">
            <el-icon><PartlyCloudy /></el-icon>
            <span>气象模型</span>
          </el-menu-item>
          <el-menu-item index="planning">
            <el-icon><Position /></el-icon>
            <span>路径规划</span>
          </el-menu-item>
          <el-menu-item index="assimilation">
            <el-icon><Connection /></el-icon>
            <span>数据同化</span>
          </el-menu-item>
          <el-menu-item index="architecture">
            <el-icon><Cpu /></el-icon>
            <span>系统架构</span>
          </el-menu-item>
          <el-menu-item index="faq">
            <el-icon><QuestionFilled /></el-icon>
            <span>FAQ</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 右侧：远程 Markdown 渲染 -->
      <main class="docs-main">
        <!-- 顶部同步状态 -->
        <div class="docs-sync-bar">
          <template v-if="loading">
            <el-icon class="sync-icon sync-loading"><Loading /></el-icon>
            <span class="sync-text">正在同步...</span>
          </template>
          <template v-else-if="!fallbackMode">
            <el-icon class="sync-icon sync-success"><CircleCheck /></el-icon>
            <span class="sync-text">已同步</span>
          </template>
          <template v-else>
            <el-icon class="sync-icon sync-fail"><Warning /></el-icon>
            <span class="sync-text">文档同步失败，使用内置兜底内容</span>
          </template>
        </div>

        <!-- fallback 提示 -->
        <el-alert
          v-if="fallbackMode"
          class="docs-fallback-alert"
          type="warning"
          show-icon
          :closable="false"
          title="文档同步失败，当前为内置内容"
        />

        <article class="docs-article" v-html="renderedHtml"></article>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'

const defaultRemoteUrl =
  'https://raw.githubusercontent.com/602420232-dotcom/weather/main/docs/usage.md'

const activeSection = ref('quickstart')
const mdText = ref('')
const loading = ref(true)
const fallbackMode = ref(false)

const fallbackMarkdown = `
# 快速开始

本系统是一套基于 WRF 气象驱动的无人机路径规划系统。通过融合实时气象数据与智能算法，为无人机集群提供安全、高效、可靠的航线规划能力。

## 使用步骤

1. 登录系统（使用默认测试账号或注册账号）。
2. 进入"气象数据"查看当前区域的气象概览。
3. 选择您的角色对应的默认模块（例如：路径规划 / 智能驾驶舱）。
4. 在"设置"中自定义主题、语言以及默认进入页面。

## 示例

\`\`\`javascript
const authStore = useAuthStore()
console.log(authStore.roleLabel, authStore.displayName)

const appStore = useAppStore()
const defaultKey = appStore.getDefaultRoute(authStore.role)
router.push('/' + defaultKey)
\`\`\`

---

# 角色与权限

系统基于角色控制（RBAC）管理不同模块的访问权限。不同角色登录后可见的菜单会动态变化，确保用户只能访问其职责范围内的数据与功能。

## 使用步骤

1. 普通用户 (user)：可访问首页、气象数据、下单与设置。
2. 生产人员 (production)：在普通用户基础上增加驾驶舱与任务管理。
3. 飞控人员 (flight)：在生产人员基础上增加路径规划与数据同化。
4. 测试人员 (tester)：在飞控人员基础上增加系统监控面板。
5. 部署人员 (deployment)：侧重 Docker / 服务器状态与 API 配置。
6. 管理员 (admin)：拥有所有模块的访问权限。

## 示例

\`\`\`javascript
const PERMISSION_MATRIX = {
  admin: ['dashboard', 'weather', 'orders', 'cockpit', 'tasks',
          'path-planning', 'assimilation', 'monitoring', 'database',
          'docker', 'api-config', 'settings', 'docs']
}

if (authStore.hasAction('planning:execute')) {
  // 允许执行路径规划
}
\`\`\`

---

# 气象模型

气象模块基于 WRF (Weather Research & Forecasting) 模型输出的格点数据，提供风场、温度、湿度、云量等关键气象要素的实时与预报信息。

## 使用步骤

1. 在左侧菜单选择"气象数据"进入气象概览页。
2. 选择时间步长（0h / 6h / 24h）查看不同预测时长。
3. 在地图上点击任意位置查看该点的气象要素详情。
4. 切换图层查看风场、温度、气压等分布。

## 示例

\`\`\`javascript
const weather = useWeatherStore()
await weather.fetchByPoint(lat, lon, timeStep)
console.log(weather.wind.u, weather.wind.v, weather.temperature)
\`\`\`

---

# 路径规划

结合气象风险与禁飞区，使用 Dijkstra / A* / 遗传算法等多种求解器，为单架或多架无人机规划安全、经济的航线。

## 使用步骤

1. 进入"路径规划"页面，在地图上绘制起飞点与降落点。
2. 选择任务参数（续航、载荷、规避天气阈值）。
3. 选择求解算法并点击"计算航线"。
4. 查看最优航线并导出为 GeoJSON / KML 或下发给飞控系统。

## 示例

\`\`\`javascript
const payload = {
  origin:      { lat: 31.23, lon: 121.47 },
  destination: { lat: 31.30, lon: 121.60 },
  waypoints:   [...],
  constraints: { maxWind: 15, minCeiling: 100 },
  solver:      'astar'
}
const route = await api.path.plan(payload)
\`\`\`

---

# 数据同化

将无人机实测回传的数据（气象、轨迹、故障告警）与模型预测进行融合，形成更贴近真实状态的分析场，用于迭代优化路径规划。

## 使用步骤

1. 进入"数据同化"页面查看最近一次同化时间。
2. 手动上传无人机回传的 CSV / JSON 观测数据。
3. 触发同化任务并等待后端完成计算。
4. 对比同化前后的误差指标（RMSE、相关系数）。

## 示例

\`\`\`javascript
const formData = new FormData()
formData.append('observations', file)
await api.assimilation.upload(formData)

const result = await api.assimilation.run({ timeWindow: 3600 })
console.log('RMSE before/after:', result.rmseBefore, result.rmseAfter)
\`\`\`

---

# 系统架构

系统采用前后端分离架构，前端为 Vue 3 + Element Plus，后端通过 RESTful 接口对接 WRF、求解器与数据库；支持容器化部署。

## 使用步骤

1. 前端：Vue 3 + Vite + Element Plus + Pinia + Vue Router。
2. 后端：RESTful API，可对接任意 WRF/WRFDA 环境。
3. 数据存储：关系型数据库 + 栅格数据库 (可选)。
4. 部署：Docker Compose 一键启动所有服务。

## 示例

\`\`\`bash
# 一键启动生产环境
docker compose up -d

# 目录结构
frontend-vue/   # Vue 3 前端
backend/        # 后端 API 服务
wrf/            # WRF 模型运行环境
docker/         # 部署配置
\`\`\`

---

# FAQ

常见问题解答。

## 使用步骤

1. 登录失败？请确认账号与密码匹配，演示模式下可使用默认账号 admin01 / Admin@123456。
2. 看不到某个菜单项？请联系管理员为您的账号分配对应的角色。
3. 地图加载空白？请检查网络是否允许访问 Cesium Ion / 地图瓦片服务。
4. 如何切换主题与语言？在"设置 → 偏好设置"中一键切换。

## 示例

\`\`\`javascript
const appStore = useAppStore()
appStore.setTheme('dark')   // 深色
appStore.setTheme('light')  // 浅色

appStore.setLanguage('en')  // English
\`\`\`
`

const renderedHtml = computed(() => {
  if (!mdText.value) return ''
  return marked.parse(mdText.value)
})

async function fetchRemoteDoc() {
  loading.value = true
  fallbackMode.value = false

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 5000)

  try {
    const response = await fetch(defaultRemoteUrl, {
      signal: controller.signal
    })
    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error('HTTP ' + response.status)
    }

    const text = await response.text()
    mdText.value = text
    fallbackMode.value = false
  } catch (err) {
    mdText.value = fallbackMarkdown
    fallbackMode.value = true
  } finally {
    loading.value = false
  }
}

function onSelectSection(index) {
  activeSection.value = index
  const sectionTitles = {
    quickstart: '快速开始',
    roles: '角色与权限',
    weather: '气象模型',
    planning: '路径规划',
    assimilation: '数据同化',
    architecture: '系统架构',
    faq: 'FAQ'
  }
  const title = sectionTitles[index]
  if (!title) return

  const article = document.querySelector('.docs-article')
  if (!article) return

  const headings = article.querySelectorAll('h1, h2')
  for (const h of headings) {
    if (h.textContent && h.textContent.trim() === title) {
      h.scrollIntoView({ behavior: 'smooth', block: 'start' })
      return
    }
  }
}

onMounted(() => {
  fetchRemoteDoc()
})
</script>

<style scoped>
.docs-page {
  padding: 16px;
  min-height: 100%;
  background: #f5f7fa;
}

.docs-grid {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 16px;
  max-width: 1280px;
  margin: 0 auto;
}

.docs-toc {
  background: #ffffff;
  border-radius: 10px;
  padding: 12px 0;
  height: fit-content;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.04);
  position: sticky;
  top: 16px;
}

.toc-title {
  padding: 4px 20px 10px;
  font-size: 13px;
  font-weight: 600;
  color: #909399;
  letter-spacing: 0.5px;
}

.toc-menu {
  border-right: none;
}

.docs-main {
  background: #ffffff;
  border-radius: 10px;
  padding: 32px 40px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.04);
  color: #303133;
  line-height: 1.8;
}

.docs-sync-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
}

.sync-icon {
  font-size: 16px;
}

.sync-loading {
  color: #409eff;
}

.sync-loading :deep(.el-icon) {
  animation: spin 1s linear infinite;
}

.sync-success {
  color: #67c23a;
}

.sync-fail {
  color: #e6a23c;
}

.sync-text {
  color: #606266;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.docs-fallback-alert {
  margin-bottom: 20px;
}

.docs-article {
  color: #303133;
  font-size: 14px;
  line-height: 1.8;
}

.docs-article :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #1f2937;
  padding-top: 16px;
  scroll-margin-top: 16px;
}

.docs-article :deep(h1:first-child) {
  padding-top: 0;
}

.docs-article :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 24px 0 10px;
  color: #1f2937;
  scroll-margin-top: 16px;
}

.docs-article :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 20px 0 10px;
  color: #1f2937;
}

.docs-article :deep(p) {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 16px;
}

.docs-article :deep(ul),
.docs-article :deep(ol) {
  padding-left: 22px;
  margin: 0 0 16px;
  color: #4b5563;
  font-size: 14px;
}

.docs-article :deep(li) {
  margin-bottom: 6px;
}

.docs-article :deep(pre) {
  background: #1e1e1e;
  color: #dcdcdc;
  padding: 16px 18px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12.5px;
  line-height: 1.7;
  margin: 10px 0 20px;
}

.docs-article :deep(code) {
  font-family: Menlo, Consolas, 'Courier New', monospace;
  white-space: pre;
}

.docs-article :deep(p code),
.docs-article :deep(li code) {
  background: #f4f4f5;
  color: #c7254e;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12.5px;
  white-space: normal;
}

.docs-article :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  font-size: 14px;
}

.docs-article :deep(th),
.docs-article :deep(td) {
  border: 1px solid #ebeef5;
  padding: 8px 12px;
  text-align: left;
}

.docs-article :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  color: #1f2937;
}

.docs-article :deep(tr:nth-child(even)) {
  background: #fafafa;
}

.docs-article :deep(hr) {
  border: none;
  border-top: 1px solid #ebeef5;
  margin: 36px 0;
}

.docs-article :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.docs-article :deep(a:hover) {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .docs-grid {
    grid-template-columns: 64px 1fr;
    gap: 8px;
  }

  .toc-title,
  .toc-menu .el-menu-item span {
    display: none;
  }

  .docs-main {
    padding: 20px 16px;
  }
}
</style>
