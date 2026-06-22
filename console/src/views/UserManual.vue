<script setup lang="ts">
import { ref, onMounted } from 'vue'
/** 当前激活的目录索引 */
const activeSection = ref('overview')

/** 目录是否折叠 */
const menuCollapsed = ref(false)

/** 滚动容器引用 */
const contentRef = ref<HTMLElement | null>(null)

/** 目录数据 */
const menuItems = [
  { index: 'overview', title: '一、平台概述', icon: 'InfoFilled' },
  { index: 'quickstart', title: '二、快速入门', icon: 'Guide' },
  { index: 'dashboard', title: '三、仪表盘', icon: 'Odometer' },
  { index: 'algorithms', title: '四、算法管理', icon: 'Cpu' },
  {
    index: 'research',
    title: '五、科研平台',
    icon: 'SetUp',
    children: [
      { index: 'research-sandbox', title: '5.1 科研沙箱' },
      { index: 'research-lab', title: '5.2 算法实验室' },
      { index: 'research-experiment', title: '5.3 实验管理' },
      { index: 'research-report', title: '5.4 报告中心' },
    ],
  },
  { index: 'weather', title: '六、气象数据', icon: 'Cloudy' },
  { index: 'planning', title: '七、路径规划', icon: 'Map' },
  { index: 'assimilation', title: '八、数据同化', icon: 'Connection' },
  { index: 'risk', title: '九、风险评估', icon: 'Warning' },
  { index: 'observation', title: '十、观测决策', icon: 'View' },
  {
    index: 'api-ops',
    title: '十一、API 运营管理',
    icon: 'Management',
    children: [
      { index: 'api-health', title: '11.1 服务健康' },
      { index: 'api-alerts', title: '11.2 告警规则' },
      { index: 'api-utm', title: '11.3 UTM 环境配置' },
    ],
  },
  {
    index: 'system',
    title: '十二、系统管理',
    icon: 'Setting',
    children: [
      { index: 'sys-users', title: '12.1 用户管理' },
      { index: 'sys-roles', title: '12.2 角色管理' },
      { index: 'sys-tenants', title: '12.3 租户管理' },
      { index: 'sys-database', title: '12.4 数据库管理' },
      { index: 'sys-weather-source', title: '12.5 气象数据源配置' },
    ],
  },
  { index: 'permission-matrix', title: '十三、角色权限矩阵', icon: 'Lock' },
]

/** 角色权限矩阵数据 */
const permissionMatrix = [
  { module: '仪表盘', superAdmin: true, tenantAdmin: true, operator: true, observer: true, algorithmAdmin: true },
  { module: '气象数据', superAdmin: true, tenantAdmin: true, operator: true, observer: true, algorithmAdmin: false },
  { module: '路径规划', superAdmin: true, tenantAdmin: true, operator: true, observer: false, algorithmAdmin: false },
  { module: '数据同化', superAdmin: true, tenantAdmin: true, operator: true, observer: false, algorithmAdmin: false },
  { module: '风险评估', superAdmin: true, tenantAdmin: true, operator: true, observer: false, algorithmAdmin: false },
  { module: '观测决策', superAdmin: true, tenantAdmin: true, operator: true, observer: true, algorithmAdmin: false },
  { module: 'UTM 管理', superAdmin: true, tenantAdmin: true, operator: true, observer: false, algorithmAdmin: false },
  { module: '算法管理', superAdmin: true, tenantAdmin: false, operator: false, observer: false, algorithmAdmin: true },
  { module: '科研沙箱', superAdmin: true, tenantAdmin: true, operator: true, observer: false, algorithmAdmin: true },
  { module: '算法实验室', superAdmin: true, tenantAdmin: false, operator: true, observer: false, algorithmAdmin: true },
  { module: '实验管理', superAdmin: true, tenantAdmin: true, operator: true, observer: false, algorithmAdmin: true },
  { module: '报告中心', superAdmin: true, tenantAdmin: true, operator: true, observer: true, algorithmAdmin: true },
  { module: 'API 运营仪表盘', superAdmin: true, tenantAdmin: true, operator: false, observer: false, algorithmAdmin: false },
  { module: '服务健康', superAdmin: true, tenantAdmin: true, operator: false, observer: false, algorithmAdmin: false },
  { module: '告警规则', superAdmin: true, tenantAdmin: true, operator: false, observer: false, algorithmAdmin: false },
  { module: 'UTM 环境配置', superAdmin: true, tenantAdmin: true, operator: false, observer: false, algorithmAdmin: false },
  { module: '用户管理', superAdmin: true, tenantAdmin: false, operator: false, observer: false, algorithmAdmin: false },
  { module: '角色管理', superAdmin: true, tenantAdmin: false, operator: false, observer: false, algorithmAdmin: false },
  { module: '租户管理', superAdmin: true, tenantAdmin: false, operator: false, observer: false, algorithmAdmin: false },
  { module: '数据库管理', superAdmin: true, tenantAdmin: false, operator: false, observer: false, algorithmAdmin: false },
  { module: '气象数据源配置', superAdmin: true, tenantAdmin: true, operator: false, observer: false, algorithmAdmin: false },
  { module: '操作手册', superAdmin: true, tenantAdmin: true, operator: true, observer: true, algorithmAdmin: true },
]

/** 点击目录项，滚动到对应章节 */
function handleMenuSelect(index: string) {
  activeSection.value = index
  const el = document.getElementById(index)
  if (el && contentRef.value) {
    const container = contentRef.value
    const offset = el.offsetTop - container.offsetTop - 20
    container.scrollTo({ top: offset, behavior: 'smooth' })
  }
}

/** 监听滚动，自动高亮当前章节 */
function handleScroll() {
  if (!contentRef.value) return
  const sections = contentRef.value.querySelectorAll('[id]')
  const scrollTop = contentRef.value.scrollTop
  let currentId = 'overview'
  for (const section of sections) {
    const el = section as HTMLElement
    if (el.offsetTop - contentRef.value.offsetTop - 40 <= scrollTop) {
      currentId = el.id
    }
  }
  activeSection.value = currentId
}

onMounted(() => {
  if (contentRef.value) {
    contentRef.value.addEventListener('scroll', handleScroll)
  }
})

/** 角色标签颜色 */
function roleTagType(role: string): string {
  switch (role) {
    case 'SUPER_ADMIN': return 'danger'
    case 'TENANT_ADMIN': return 'primary'
    case 'OPERATOR': return 'success'
    case 'OBSERVER': return 'info'
    case 'ALGORITHM_ADMIN': return 'warning'
    default: return 'info'
  }
}
</script>

<template>
  <div class="user-manual-page">
    <!-- 左侧目录导航 -->
    <aside class="manual-sidebar" :class="{ collapsed: menuCollapsed }">
      <div class="sidebar-header">
        <el-icon :size="20" color="#e94560"><Document /></el-icon>
        <span v-show="!menuCollapsed" class="sidebar-title">操作手册</span>
        <el-button
          v-show="!menuCollapsed"
          class="collapse-btn"
          :icon="menuCollapsed ? 'DArrowRight' : 'DArrowLeft'"
          text
          size="small"
          @click="menuCollapsed = true"
        />
      </div>
      <el-menu
        :default-active="activeSection"
        :collapse="menuCollapsed"
        :collapse-transition="false"
        background-color="#16213e"
        text-color="#a0a0b0"
        active-text-color="#e0e0e0"
        class="manual-menu"
        @select="handleMenuSelect"
      >
        <template v-for="item in menuItems" :key="item.index">
          <el-sub-menu v-if="item.children" :index="item.index">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.index"
              :index="child.index"
            >
              <span>{{ child.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
      <div v-if="menuCollapsed" class="expand-area">
        <el-button
          :icon="'DArrowRight'"
          text
          size="small"
          @click="menuCollapsed = false"
        />
      </div>
    </aside>

    <!-- 右侧内容区域 -->
    <main ref="contentRef" class="manual-content">
      <!-- 一、平台概述 -->
      <section id="overview" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><InfoFilled /></el-icon>
          一、平台概述
        </h1>

        <el-card shadow="never" class="content-card">
          <h3 class="card-subtitle">UAV 气象数据处理与算法管理平台</h3>
          <p class="card-text">
            本平台是面向无人机（UAV）领域的气象数据处理与算法管理综合平台，集成了气象数据查询、路径规划、数据同化、风险评估、观测决策等核心业务功能，同时提供科研沙箱、算法实验室等科研工具，支持 63 种气象算法的参数化运行与对比分析。
          </p>

          <h3 class="card-subtitle">系统架构概览</h3>
          <div class="arch-diagram">
            <div class="arch-layer">
              <div class="arch-box frontend">前端控制台 (Vue 3 + Element Plus)</div>
            </div>
            <div class="arch-arrow">&#9660;</div>
            <div class="arch-layer">
              <div class="arch-box gateway">API 网关 (Spring Cloud Gateway)</div>
            </div>
            <div class="arch-arrow">&#9660;</div>
            <div class="arch-layer multi">
              <div class="arch-box service">气象服务</div>
              <div class="arch-box service">路径规划</div>
              <div class="arch-box service">数据同化</div>
              <div class="arch-box service">风险评估</div>
              <div class="arch-box service">模型引擎</div>
            </div>
            <div class="arch-arrow">&#9660;</div>
            <div class="arch-layer">
              <div class="arch-box engine">算法引擎 (Python / WRF / FengWu)</div>
            </div>
          </div>

          <h3 class="card-subtitle">支持的浏览器和推荐配置</h3>
          <el-table :data="[
            { browser: 'Chrome', version: '90+', status: '推荐', note: '最佳体验' },
            { browser: 'Firefox', version: '88+', status: '推荐', note: '完整支持' },
            { browser: 'Edge', version: '90+', status: '推荐', note: '完整支持' },
            { browser: 'Safari', version: '14+', status: '兼容', note: '部分功能可能存在差异' },
          ]" stripe style="width: 100%" class="dark-table">
            <el-table-column prop="browser" label="浏览器" width="120" />
            <el-table-column prop="version" label="最低版本" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === '推荐' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="备注" />
          </el-table>
        </el-card>
      </section>

      <!-- 二、快速入门 -->
      <section id="quickstart" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Guide /></el-icon>
          二、快速入门
        </h1>

        <el-card shadow="never" class="content-card">
          <h3 class="card-subtitle">登录与注册</h3>
          <ol class="step-list">
            <li>打开浏览器，访问平台地址（默认：<code>http://localhost:5173</code>）</li>
            <li>在登录页面输入用户名和密码</li>
            <li>点击「登录」按钮进入平台主界面</li>
            <li>首次使用请联系管理员创建账户并分配角色</li>
          </ol>

          <h3 class="card-subtitle">演示模式 vs 生产模式</h3>
          <p class="card-text">
            平台支持两种运行模式，可在顶栏切换：
          </p>
          <el-table :data="[
            { feature: '演示模式', desc: '使用内置模拟数据，无需后端服务', scene: '功能演示、培训、开发调试' },
            { feature: '生产模式', desc: '连接真实后端 API，操作实际数据', scene: '日常运营、科研实验、生产环境' },
          ]" stripe style="width: 100%" class="dark-table">
            <el-table-column prop="feature" label="模式" width="120" />
            <el-table-column prop="desc" label="说明" />
            <el-table-column prop="scene" label="适用场景" width="220" />
          </el-table>

          <h3 class="card-subtitle">界面布局说明</h3>
          <div class="layout-diagram">
            <div class="layout-topbar">顶栏：模式切换、通知、用户信息</div>
            <div class="layout-body">
              <div class="layout-sidebar">侧边栏<br/>导航菜单</div>
              <div class="layout-main">主内容区<br/>各功能模块</div>
            </div>
          </div>

          <h3 class="card-subtitle">常用操作快捷键</h3>
          <el-table :data="[
            { key: 'Ctrl + K', action: '全局搜索（规划中）' },
            { key: 'Ctrl + B', action: '切换侧边栏折叠' },
            { key: 'Esc', action: '关闭弹窗/对话框' },
          ]" stripe style="width: 100%" class="dark-table">
            <el-table-column prop="key" label="快捷键" width="150">
              <template #default="{ row }">
                <kbd class="kbd">{{ row.key }}</kbd>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="功能" />
          </el-table>
        </el-card>
      </section>

      <!-- 三、仪表盘 -->
      <section id="dashboard" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Odometer /></el-icon>
          三、仪表盘
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag v-for="role in ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'OBSERVER', 'ALGORITHM_ADMIN']" :key="role" :type="roleTagType(role)" size="small">{{ role }}</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>全局数据概览</strong>：展示租户总数、活跃 API Key 数、今日 API 调用量、运行中实验数等核心 KPI</li>
            <li><strong>API 调用趋势</strong>：以折线图展示近 7 天 / 30 天的 API 调用量变化趋势</li>
            <li><strong>服务健康状态</strong>：实时监控各微服务的运行状态，以卡片形式展示健康/异常状态</li>
            <li><strong>科研摘要</strong>：展示运行中/已完成的实验数量及 5DVar 执行次数</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>登录后默认进入仪表盘页面</li>
            <li>查看顶部 KPI 卡片了解全局数据</li>
            <li>在趋势图区域可切换时间范围（7 天 / 30 天）</li>
            <li>服务健康卡片展示各微服务的实时状态，绿色表示正常，红色表示异常</li>
          </ol>
        </el-card>
      </section>

      <!-- 四、算法管理 -->
      <section id="algorithms" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Cpu /></el-icon>
          四、算法管理
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="warning" size="small">ALGORITHM_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>查看算法列表</strong>：以表格/卡片形式展示平台已注册的所有算法</li>
            <li><strong>搜索筛选</strong>：支持按分类、名称关键词搜索算法</li>
            <li><strong>查看算法详情</strong>：点击算法名称弹出详情弹窗，查看描述、参数 schema、输入输出格式</li>
            <li><strong>测试运行</strong>：在详情弹窗中配置参数，提交测试运行请求</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏点击「算法管理」进入算法列表页面</li>
            <li>使用顶部分类标签按类别筛选算法（如数值预报、数据同化、边界层等）</li>
            <li>在搜索框中输入关键词快速定位算法</li>
            <li>点击算法名称打开详情弹窗，查看算法完整信息</li>
            <li>在详情弹窗的「参数配置」区域设置参数值</li>
            <li>点击「运行测试」按钮提交算法运行请求，查看运行结果</li>
          </ol>
        </el-card>
      </section>

      <!-- 五、科研平台 -->
      <section id="research" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><SetUp /></el-icon>
          五、科研平台
        </h1>
      </section>

      <!-- 5.1 科研沙箱 -->
      <section id="research-sandbox" class="manual-section sub-section">
        <h2 class="sub-title">5.1 科研沙箱</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
            <el-tag type="warning" size="small">ALGORITHM_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>实验管理</strong>：创建、查看、管理科研实验</li>
            <li><strong>算法对比面板</strong>：选择多个算法进行横向对比，以雷达图展示各维度表现</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏「科研平台」菜单下点击「科研沙箱」</li>
            <li>点击「创建实验」按钮，填写实验名称和描述</li>
            <li>在对比面板中，通过 <strong>Tag 标签 + 弹窗选择器</strong> 选择要对比的算法</li>
            <li>选择完成后，系统自动运行对比并生成雷达图结果</li>
            <li>雷达图展示各算法在精度、速度、稳定性等维度的对比</li>
          </ol>
        </el-card>
      </section>

      <!-- 5.2 算法实验室 -->
      <section id="research-lab" class="manual-section sub-section">
        <h2 class="sub-title">5.2 算法实验室</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
            <el-tag type="warning" size="small">ALGORITHM_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>选择算法</strong>：从 63 个已注册算法中选择目标算法</li>
            <li><strong>参数调整</strong>：根据算法的独立参数 schema 动态加载参数面板</li>
            <li><strong>运行实验</strong>：提交参数配置后运行算法，实时查看日志输出</li>
            <li><strong>查看结果</strong>：运行完成后展示结果图表和数据</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在算法选择区域选择目标算法</li>
            <li>右侧参数面板自动加载该算法对应的参数 schema</li>
            <li>根据需要调整参数值（每个算法有独立的参数定义）</li>
            <li>点击「运行」按钮提交实验</li>
            <li>在日志面板查看实时运行日志</li>
            <li>运行完成后在结果区域查看图表和数据</li>
          </ol>

          <el-alert
            title="参数说明"
            type="info"
            :closable="false"
            show-icon
            class="info-alert"
          >
            平台共注册 63 个气象算法，每个算法拥有独立的参数 schema。选择不同算法后，参数面板会自动切换为对应的参数配置项，包括数值型、选择型、布尔型等多种参数类型。
          </el-alert>
        </el-card>
      </section>

      <!-- 5.3 实验管理 -->
      <section id="research-experiment" class="manual-section sub-section">
        <h2 class="sub-title">5.3 实验管理</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
            <el-tag type="warning" size="small">ALGORITHM_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>实验列表</strong>：查看所有实验的列表，支持按状态筛选</li>
            <li><strong>状态管理</strong>：跟踪实验的运行状态（待运行、运行中、已完成、失败）</li>
            <li><strong>快照/恢复</strong>：对实验进行快照保存，支持从快照恢复实验环境</li>
            <li><strong>报告生成</strong>：基于实验数据生成对比分析报告</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「科研平台」菜单下点击「实验管理」进入实验列表</li>
            <li>使用状态筛选器查看特定状态的实验</li>
            <li>点击实验名称查看实验详情（参数配置、运行日志、结果数据）</li>
            <li>点击「快照」按钮保存当前实验状态</li>
            <li>点击「恢复」按钮从快照恢复实验环境</li>
            <li>点击「生成报告」创建实验对比分析报告</li>
          </ol>
        </el-card>
      </section>

      <!-- 5.4 报告中心 -->
      <section id="research-report" class="manual-section sub-section">
        <h2 class="sub-title">5.4 报告中心</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag v-for="role in ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'OBSERVER', 'ALGORITHM_ADMIN']" :key="role" :type="roleTagType(role)" size="small">{{ role }}</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>报告模板</strong>：提供多种预设报告模板</li>
            <li><strong>报告生成</strong>：基于模板和实验数据自动生成报告</li>
            <li><strong>下载</strong>：支持导出为 PDF 等格式</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「科研平台」菜单下点击「报告中心」</li>
            <li>浏览可用的报告模板，选择适合的模板</li>
            <li>配置报告参数（时间范围、实验选择、数据源等）</li>
            <li>点击「生成报告」按钮</li>
            <li>生成完成后点击「下载」获取报告文件</li>
          </ol>
        </el-card>
      </section>

      <!-- 六、气象数据 -->
      <section id="weather" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Cloudy /></el-icon>
          六、气象数据
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
            <el-tag type="info" size="small">OBSERVER</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>单点气象查询</strong>：输入经纬度坐标，查询指定位置的气象数据</li>
            <li><strong>区域格点查询</strong>：选择矩形区域范围和气象要素，获取格点化气象数据</li>
            <li><strong>风场剖面</strong>：查看特定区域的风场垂直剖面图</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏点击「气象数据」进入气象查询页面</li>
            <li><strong>单点查询</strong>：在地图上点击或手动输入经纬度，选择气象要素和时间范围，点击查询</li>
            <li><strong>区域查询</strong>：在地图上框选矩形区域，选择要素类型，提交查询</li>
            <li><strong>风场剖面</strong>：选择剖面位置和高度范围，查看风场可视化图表</li>
            <li>查询结果以图表和数据表格形式展示</li>
          </ol>
        </el-card>
      </section>

      <!-- 七、路径规划 -->
      <section id="planning" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Map /></el-icon>
          七、路径规划
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>UAV 路径规划</strong>：基于气象数据和约束条件为无人机规划最优飞行路径</li>
            <li><strong>任务管理</strong>：创建、查看、管理路径规划任务</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏点击「路径规划」进入路径规划页面</li>
            <li>在地图上设置起点和终点（点击或输入坐标）</li>
            <li>配置飞行约束条件（最大飞行高度、避障区域、气象阈值等）</li>
            <li>点击「提交规划」按钮</li>
            <li>等待规划完成，在地图上查看规划路径和详细信息</li>
          </ol>
        </el-card>
      </section>

      <!-- 八、数据同化 -->
      <section id="assimilation" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Connection /></el-icon>
          八、数据同化
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>气象数据同化</strong>：将观测数据融入数值预报模型，提高预报精度</li>
            <li><strong>任务管理</strong>：创建、监控、管理数据同化任务</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏点击「数据同化」进入数据同化页面</li>
            <li>选择同化算法（如 3DVar、4DVar、EnKF 等）</li>
            <li>配置同化参数（时间窗口、观测数据源、背景场等）</li>
            <li>点击「提交任务」按钮</li>
            <li>在任务列表中查看任务状态和进度</li>
            <li>任务完成后查看同化结果和分析报告</li>
          </ol>
        </el-card>
      </section>

      <!-- 九、风险评估 -->
      <section id="risk" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Warning /></el-icon>
          九、风险评估
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>气象风险评估</strong>：基于气象数据评估飞行区域的风险等级</li>
            <li><strong>适航评估</strong>：判断当前气象条件是否满足无人机飞行要求</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏点击「风险/适航」进入风险评估页面</li>
            <li>在地图上选择评估区域</li>
            <li>配置评估参数（飞行器类型、风险阈值等）</li>
            <li>点击「运行评估」按钮</li>
            <li>查看风险地图和评估报告，了解各区域的风险等级</li>
          </ol>
        </el-card>
      </section>

      <!-- 十、观测决策 -->
      <section id="observation" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><View /></el-icon>
          十、观测决策
        </h1>

        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
            <el-tag type="success" size="small">OPERATOR</el-tag>
            <el-tag type="info" size="small">OBSERVER</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>观测任务管理</strong>：创建和管理气象观测任务</li>
            <li><strong>决策支持</strong>：基于观测数据和模型分析提供决策建议</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏点击「观测决策」进入观测决策页面</li>
            <li>点击「创建任务」按钮，填写观测任务信息</li>
            <li>配置观测参数（观测区域、时间、频次、要素等）</li>
            <li>提交任务后查看任务执行状态</li>
            <li>在决策结果区域查看系统生成的决策建议</li>
          </ol>
        </el-card>
      </section>

      <!-- 十一、API 运营管理 -->
      <section id="api-ops" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Management /></el-icon>
          十一、API 运营管理
        </h1>
      </section>

      <!-- 11.1 服务健康 -->
      <section id="api-health" class="manual-section sub-section">
        <h2 class="sub-title">11.1 服务健康</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>微服务健康状态监控</strong>：实时监控所有微服务的运行状态、响应时间、错误率等指标</li>
            <li><strong>服务拓扑</strong>：展示微服务之间的依赖关系和调用链路</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏「API 运营管理」菜单下点击「服务健康」</li>
            <li>查看各服务的健康状态卡片，绿色表示正常，黄色表示告警，红色表示故障</li>
            <li>点击服务卡片查看详细指标（响应时间、QPS、错误率等）</li>
          </ol>
        </el-card>
      </section>

      <!-- 11.2 告警规则 -->
      <section id="api-alerts" class="manual-section sub-section">
        <h2 class="sub-title">11.2 告警规则</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>告警规则配置</strong>：创建和管理告警规则，定义触发条件和通知方式</li>
            <li><strong>告警历史</strong>：查看历史告警记录和处理状态</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「API 运营管理」菜单下点击「告警规则」</li>
            <li>点击「新建规则」按钮配置告警条件（指标阈值、持续时间等）</li>
            <li>设置通知方式（邮件、Webhook 等）</li>
            <li>在告警历史中查看已触发的告警和处理状态</li>
          </ol>
        </el-card>
      </section>

      <!-- 11.3 UTM 环境配置 -->
      <section id="api-utm" class="manual-section sub-section">
        <h2 class="sub-title">11.3 UTM 环境配置</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>UTM 环境参数配置</strong>：管理无人机交通管理系统的环境参数</li>
            <li><strong>连接配置</strong>：配置与 UTM 系统的连接参数和认证信息</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「API 运营管理」菜单下点击「UTM 环境配置」</li>
            <li>编辑 UTM 服务地址、端口、认证信息等参数</li>
            <li>点击「保存配置」按钮应用更改</li>
            <li>使用「测试连接」功能验证配置是否正确</li>
          </ol>
        </el-card>
      </section>

      <!-- 十二、系统管理 -->
      <section id="system" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Setting /></el-icon>
          十二、系统管理
        </h1>
      </section>

      <!-- 12.1 用户管理 -->
      <section id="sys-users" class="manual-section sub-section">
        <h2 class="sub-title">12.1 用户管理</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>用户 CRUD</strong>：创建、查看、编辑、删除用户账户</li>
            <li><strong>角色分配</strong>：为用户分配系统角色（SUPER_ADMIN、TENANT_ADMIN、OPERATOR、OBSERVER、ALGORITHM_ADMIN）</li>
            <li><strong>密码重置</strong>：管理员可重置用户密码</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在侧边栏「系统管理」菜单下点击「用户管理」</li>
            <li>点击「新建用户」按钮，填写用户名、邮箱、初始密码</li>
            <li>选择要分配的角色</li>
            <li>在用户列表中可编辑用户信息、重置密码或禁用账户</li>
          </ol>
        </el-card>
      </section>

      <!-- 12.2 角色管理 -->
      <section id="sys-roles" class="manual-section sub-section">
        <h2 class="sub-title">12.2 角色管理</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>角色 CRUD</strong>：创建、查看、编辑、删除系统角色</li>
            <li><strong>权限配置</strong>：为角色配置菜单访问权限和功能操作权限</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「系统管理」菜单下点击「角色管理」</li>
            <li>查看系统预置的五种角色及其权限配置</li>
            <li>点击角色名称查看和编辑权限配置</li>
            <li>在权限树中勾选/取消菜单和操作权限</li>
          </ol>
        </el-card>
      </section>

      <!-- 12.3 租户管理 -->
      <section id="sys-tenants" class="manual-section sub-section">
        <h2 class="sub-title">12.3 租户管理</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>租户 CRUD</strong>：创建、查看、编辑、删除租户</li>
            <li><strong>配额管理</strong>：设置租户的 API 调用配额和资源限制</li>
            <li><strong>API Key 管理</strong>：为租户生成和管理 API 密钥</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「系统管理」菜单下点击「租户管理」</li>
            <li>点击「新建租户」按钮，填写租户名称、联系人等信息</li>
            <li>配置租户的 API 调用配额</li>
            <li>在租户详情中管理 API Key（生成、吊销、查看使用统计）</li>
          </ol>
        </el-card>
      </section>

      <!-- 12.4 数据库管理 -->
      <section id="sys-database" class="manual-section sub-section">
        <h2 class="sub-title">12.4 数据库管理</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>数据库连接管理</strong>：查看和管理数据库连接配置</li>
            <li><strong>SQL 查询</strong>：在安全沙箱中执行 SQL 查询语句</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「系统管理」菜单下点击「数据库管理」</li>
            <li>查看当前数据库连接状态和基本信息</li>
            <li>在 SQL 编辑器中输入查询语句</li>
            <li>点击「执行」按钮运行查询，查看结果表格</li>
          </ol>

          <el-alert
            title="安全提示"
            type="warning"
            :closable="false"
            show-icon
            class="info-alert"
          >
            数据库管理功能仅限 SUPER_ADMIN 使用，且仅支持 SELECT 查询，不支持修改数据的 DML/DDL 操作。
          </el-alert>
        </el-card>
      </section>

      <!-- 12.5 气象数据源配置 -->
      <section id="sys-weather-source" class="manual-section sub-section">
        <h2 class="sub-title">12.5 气象数据源配置</h2>
        <el-card shadow="never" class="content-card">
          <div class="role-tags">
            <el-tag type="danger" size="small">SUPER_ADMIN</el-tag>
            <el-tag type="primary" size="small">TENANT_ADMIN</el-tag>
          </div>

          <h3 class="card-subtitle">功能说明</h3>
          <ul class="feature-list">
            <li><strong>数据源管理</strong>：添加、编辑、删除气象数据源</li>
            <li><strong>API 密钥配置</strong>：管理第三方气象数据 API 的密钥和认证信息</li>
            <li><strong>WRF 服务器配置</strong>：配置 WRF 数值预报服务器的连接参数</li>
          </ul>

          <h3 class="card-subtitle">使用方法</h3>
          <ol class="step-list">
            <li>在「系统管理」菜单下点击「气象数据源」</li>
            <li>点击「添加数据源」按钮，选择数据源类型</li>
            <li>填写连接参数和 API 密钥</li>
            <li>点击「测试连接」验证数据源可用性</li>
            <li>保存配置后，平台将自动从配置的数据源获取气象数据</li>
          </ol>
        </el-card>
      </section>

      <!-- 十三、角色权限矩阵 -->
      <section id="permission-matrix" class="manual-section">
        <h1 class="section-title">
          <el-icon class="title-icon"><Lock /></el-icon>
          十三、角色权限矩阵
        </h1>

        <el-card shadow="never" class="content-card">
          <p class="card-text">
            下表展示了平台各功能模块与用户角色的权限对应关系。<el-tag type="success" size="small">&#10003;</el-tag> 表示有权限，<el-tag type="danger" size="small">&#10007;</el-tag> 表示无权限。
          </p>

          <div class="matrix-table-wrapper">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th class="module-col">功能模块</th>
                  <th>SUPER_ADMIN</th>
                  <th>TENANT_ADMIN</th>
                  <th>OPERATOR</th>
                  <th>OBSERVER</th>
                  <th>ALGORITHM_ADMIN</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in permissionMatrix" :key="row.module">
                  <td class="module-col">{{ row.module }}</td>
                  <td>
                    <el-icon :color="row.superAdmin ? '#67c23a' : '#f56c6c'">
                      <component :is="row.superAdmin ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                  </td>
                  <td>
                    <el-icon :color="row.tenantAdmin ? '#67c23a' : '#f56c6c'">
                      <component :is="row.tenantAdmin ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                  </td>
                  <td>
                    <el-icon :color="row.operator ? '#67c23a' : '#f56c6c'">
                      <component :is="row.operator ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                  </td>
                  <td>
                    <el-icon :color="row.observer ? '#67c23a' : '#f56c6c'">
                      <component :is="row.observer ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                  </td>
                  <td>
                    <el-icon :color="row.algorithmAdmin ? '#67c23a' : '#f56c6c'">
                      <component :is="row.algorithmAdmin ? 'CircleCheckFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <el-divider />

          <h3 class="card-subtitle">角色说明</h3>
          <el-descriptions :column="1" border class="dark-descriptions">
            <el-descriptions-item label="SUPER_ADMIN">
              <el-tag type="danger" size="small">超级管理员</el-tag>
              拥有所有功能的完整权限，包括系统管理、用户管理、租户管理等
            </el-descriptions-item>
            <el-descriptions-item label="TENANT_ADMIN">
              <el-tag type="primary" size="small">租户管理员</el-tag>
              管理所属租户的 API 运营、气象数据源配置等
            </el-descriptions-item>
            <el-descriptions-item label="OPERATOR">
              <el-tag type="success" size="small">操作员</el-tag>
              使用业务功能和科研工具，包括气象查询、路径规划、算法实验等
            </el-descriptions-item>
            <el-descriptions-item label="OBSERVER">
              <el-tag type="info" size="small">观察者</el-tag>
              只读权限，可查看仪表盘、气象数据、观测决策和报告
            </el-descriptions-item>
            <el-descriptions-item label="ALGORITHM_ADMIN">
              <el-tag type="warning" size="small">算法管理员</el-tag>
              管理算法库、运行算法实验，专注于科研和算法开发
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </section>

      <!-- 页脚 -->
      <div class="manual-footer">
        <p>UAV 气象数据处理与算法管理平台 -- 用户操作手册 v1.0</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.user-manual-page {
  display: flex;
  height: 100%;
  background-color: #0a0f1e;
  overflow: hidden;
}

/* ===== 左侧目录导航 ===== */
.manual-sidebar {
  width: 280px;
  min-width: 280px;
  background-color: #16213e;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.manual-sidebar.collapsed {
  width: 64px;
  min-width: 64px;
}

.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 700;
  color: #e0e0e0;
  white-space: nowrap;
  flex: 1;
}

.collapse-btn {
  color: #a0a0b0;
  padding: 4px;
}

.expand-area {
  display: flex;
  justify-content: center;
  padding: 8px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.manual-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none;
  padding: 8px 0;
}

.manual-menu :deep(.el-menu-item),
.manual-menu :deep(.el-sub-menu__title) {
  height: auto !important;
  line-height: normal !important;
  padding: 8px 16px !important;
  margin: 2px 8px;
  border-radius: 6px;
  font-size: 13px;
  transition: all 0.25s ease;
}

.manual-menu :deep(.el-menu-item:hover),
.manual-menu :deep(.el-sub-menu__title:hover) {
  background: linear-gradient(135deg, #1a2745 0%, #1e2d4d 100%) !important;
}

.manual-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #0f3460 0%, #134070 100%) !important;
  color: #e0e0e0 !important;
  font-weight: 600;
}

.manual-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  font-size: 12px;
  opacity: 0.85;
}

.manual-menu::-webkit-scrollbar {
  width: 4px;
}

.manual-menu::-webkit-scrollbar-track {
  background: transparent;
}

.manual-menu::-webkit-scrollbar-thumb {
  background: rgba(160, 160, 176, 0.2);
  border-radius: 2px;
}

/* ===== 右侧内容区域 ===== */
.manual-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
  scroll-behavior: smooth;
}

.manual-content::-webkit-scrollbar {
  width: 6px;
}

.manual-content::-webkit-scrollbar-track {
  background: transparent;
}

.manual-content::-webkit-scrollbar-thumb {
  background: rgba(160, 160, 176, 0.15);
  border-radius: 3px;
}

.manual-content::-webkit-scrollbar-thumb:hover {
  background: rgba(160, 160, 176, 0.3);
}

/* ===== 章节样式 ===== */
.manual-section {
  margin-bottom: 32px;
}

.manual-section:last-child {
  margin-bottom: 0;
}

.sub-section {
  margin-top: -16px;
  margin-bottom: 24px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #e0e0e0;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e94560;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: #e94560;
}

.sub-title {
  font-size: 18px;
  font-weight: 600;
  color: #c0c0d0;
  margin: 0 0 12px 0;
  padding-left: 12px;
  border-left: 3px solid #e94560;
}

/* ===== 内容卡片 ===== */
.content-card {
  background-color: #16213e !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 12px !important;
  color: #c0c0d0;
}

.content-card :deep(.el-card__body) {
  padding: 20px 24px;
}

.card-subtitle {
  font-size: 16px;
  font-weight: 600;
  color: #e0e0e0;
  margin: 20px 0 12px 0;
}

.card-subtitle:first-child {
  margin-top: 0;
}

.card-text {
  font-size: 14px;
  line-height: 1.8;
  color: #a0a0b0;
}

/* ===== 角色标签 ===== */
.role-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

/* ===== 功能列表 ===== */
.feature-list {
  padding-left: 20px;
  margin: 8px 0;
}

.feature-list li {
  font-size: 14px;
  line-height: 2;
  color: #a0a0b0;
}

.feature-list li strong {
  color: #c0c0d0;
}

/* ===== 步骤列表 ===== */
.step-list {
  padding-left: 20px;
  margin: 8px 0;
  counter-reset: step-counter;
  list-style: none;
}

.step-list li {
  font-size: 14px;
  line-height: 2;
  color: #a0a0b0;
  position: relative;
  padding-left: 8px;
}

.step-list li::before {
  counter-increment: step-counter;
  content: counter(step-counter);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background-color: #0f3460;
  color: #e94560;
  font-size: 12px;
  font-weight: 700;
  margin-right: 10px;
  flex-shrink: 0;
}

/* ===== 架构图 ===== */
.arch-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  margin: 16px 0;
  background-color: rgba(15, 52, 96, 0.3);
  border-radius: 8px;
}

.arch-layer {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.arch-layer.multi {
  gap: 8px;
}

.arch-box {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  min-width: 200px;
}

.arch-box.frontend {
  background: linear-gradient(135deg, #0f3460, #1a4a8a);
  color: #e0e0e0;
  border: 1px solid rgba(233, 69, 96, 0.3);
}

.arch-box.gateway {
  background: linear-gradient(135deg, #1a3a5c, #2a5a8c);
  color: #e0e0e0;
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.arch-box.service {
  background: linear-gradient(135deg, #1a3a4c, #2a5a6c);
  color: #e0e0e0;
  border: 1px solid rgba(103, 194, 58, 0.3);
  min-width: 120px;
  font-size: 12px;
  padding: 8px 14px;
}

.arch-box.engine {
  background: linear-gradient(135deg, #3a2a1c, #5a4a2c);
  color: #e0e0e0;
  border: 1px solid rgba(230, 162, 60, 0.3);
}

.arch-arrow {
  color: #a0a0b0;
  font-size: 16px;
  line-height: 1;
}

/* ===== 布局示意图 ===== */
.layout-diagram {
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  overflow: hidden;
  margin: 16px 0;
}

.layout-topbar {
  background-color: rgba(15, 52, 96, 0.5);
  padding: 12px;
  text-align: center;
  font-size: 13px;
  color: #c0c0d0;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
}

.layout-body {
  display: flex;
  min-height: 120px;
}

.layout-sidebar {
  width: 120px;
  background-color: rgba(22, 33, 62, 0.8);
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 12px;
  color: #a0a0b0;
  border-right: 1px dashed rgba(255, 255, 255, 0.1);
}

.layout-main {
  flex: 1;
  background-color: rgba(10, 15, 30, 0.5);
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 12px;
  color: #a0a0b0;
}

/* ===== 快捷键样式 ===== */
.kbd {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  font-family: monospace;
  color: #e0e0e0;
  background-color: #0a0f1e;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* ===== 暗色表格 ===== */
.dark-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(15, 52, 96, 0.3);
  --el-table-row-hover-bg-color: rgba(15, 52, 96, 0.2);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: #a0a0b0;
  --el-table-header-text-color: #c0c0d0;
  margin: 12px 0;
  border-radius: 8px;
  overflow: hidden;
}

.dark-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

/* ===== 暗色描述列表 ===== */
.dark-descriptions {
  --el-descriptions-table-border: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 16px;
}

.dark-descriptions :deep(.el-descriptions__label) {
  background-color: rgba(15, 52, 96, 0.3) !important;
  color: #c0c0d0 !important;
}

.dark-descriptions :deep(.el-descriptions__content) {
  background-color: transparent !important;
  color: #a0a0b0 !important;
}

/* ===== 权限矩阵表格 ===== */
.matrix-table-wrapper {
  overflow-x: auto;
  margin: 16px 0;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.matrix-table th,
.matrix-table td {
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  text-align: center;
}

.matrix-table th {
  background-color: rgba(15, 52, 96, 0.4);
  color: #c0c0d0;
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
}

.matrix-table td {
  color: #a0a0b0;
}

.matrix-table .module-col {
  text-align: left;
  color: #c0c0d0;
  font-weight: 500;
  min-width: 160px;
}

.matrix-table tbody tr:hover {
  background-color: rgba(15, 52, 96, 0.15);
}

/* ===== 提示框 ===== */
.info-alert {
  margin-top: 16px;
  background-color: rgba(15, 52, 96, 0.3) !important;
  border-color: rgba(64, 158, 255, 0.3) !important;
}

.info-alert :deep(.el-alert__title) {
  color: #c0c0d0;
}

.info-alert :deep(.el-alert__description) {
  color: #a0a0b0;
}

/* ===== 分割线 ===== */
:deep(.el-divider) {
  border-color: rgba(255, 255, 255, 0.08);
}

:deep(.el-divider__text) {
  background-color: #16213e;
  color: #a0a0b0;
}

/* ===== 页脚 ===== */
.manual-footer {
  text-align: center;
  padding: 32px 0 16px;
  color: #606080;
  font-size: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 40px;
}

/* ===== 代码标签 ===== */
code {
  padding: 2px 6px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #e94560;
  background-color: rgba(233, 69, 96, 0.1);
  border-radius: 4px;
}
</style>
