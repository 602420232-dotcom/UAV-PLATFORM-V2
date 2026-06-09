import { ROLES } from '@/stores/auth'

const SECTIONS = {
  ANNOUNCEMENT: 'announcement',
  TECH_DISCUSS: 'tech_discuss',
  TASK_COLLAB: 'task_collab',
  KNOWLEDGE: 'knowledge'
}

const SECTION_LABELS = {
  [SECTIONS.ANNOUNCEMENT]: '公告通知',
  [SECTIONS.TECH_DISCUSS]: '技术讨论',
  [SECTIONS.TASK_COLLAB]: '任务协作',
  [SECTIONS.KNOWLEDGE]: '知识库'
}

// 注意：权限检查现在由前端 authStore.hasPermission 统一处理
// 这里保留结构但不再使用硬编码的角色列表

const MOCK_USERS = [
  { id: 'admin', username: 'admin01', displayName: '系统管理员', role: ROLES.ADMIN, avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20system%20administrator%20avatar%20portrait&image_size=square' },
  { id: 'dev', username: 'dev01', displayName: '张三', role: ROLES.DEVELOPER, avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20software%20developer%20avatar%20portrait&image_size=square' },
  { id: 'test', username: 'test01', displayName: '李四', role: ROLES.TESTER, avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20software%20tester%20avatar%20portrait&image_size=square' },
  { id: 'deploy', username: 'deploy01', displayName: '王五', role: ROLES.DEPLOYMENT, avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20devops%20engineer%20avatar%20portrait&image_size=square' },
  { id: 'flight', username: 'flight01', displayName: '赵六', role: ROLES.FLIGHT, avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20drone%20pilot%20avatar%20portrait&image_size=square' },
  { id: 'prod', username: 'prod01', displayName: '孙七', role: ROLES.PRODUCTION, avatar: 'https://neeko-copilot.bytedance.net/api/text_to_image?prompt=professional%20production%20manager%20avatar%20portrait&image_size=square' }
]

const MOCK_POSTS = [
  {
    id: '1',
    title: 'V2.0版本发布公告',
    content: '<p>各位同事，经过两周的开发和测试，我们的无人机路径规划系统V2.0版本正式发布！</p><p><strong>新增功能：</strong></p><ul><li>支持VRPTW路径规划算法</li><li>集成实时气象数据</li><li>新增多语言支持（中文、英文、日语）</li><li>优化界面响应速度</li></ul><p>请各部门做好测试和部署准备。如有问题，请在技术讨论板块反馈。</p>',
    section: SECTIONS.ANNOUNCEMENT,
    tags: ['版本发布', '系统更新'],
    status: 'pinned',
    authorId: 'admin',
    author: MOCK_USERS[0],
    authorLocation: '北京',
    viewCount: 128,
    likeCount: 24,
    commentCount: 8,
    createdAt: '2026-06-08T10:00:00Z',
    updatedAt: '2026-06-08T10:00:00Z'
  },
  {
    id: '2',
    title: '关于DE-RRT*算法参数调优的讨论',
    content: '<p>最近在测试DE-RRT*算法时发现，当障碍物密度较高时，路径规划时间明显增加。</p><p>我尝试调整了以下参数：</p><ul><li>采样点数量从1000增加到2000</li><li>步长从0.5调整为0.3</li><li>目标偏向概率从0.1提高到0.2</li></ul><p>结果显示路径质量有所提升，但计算时间增加了约30%。大家有没有更好的优化方案？</p>',
    section: SECTIONS.TECH_DISCUSS,
    tags: ['算法', 'DE-RRT*', '参数调优'],
    status: 'normal',
    authorId: 'dev',
    author: MOCK_USERS[1],
    authorLocation: '四川成都',
    viewCount: 86,
    likeCount: 15,
    commentCount: 6,
    createdAt: '2026-06-07T14:30:00Z',
    updatedAt: '2026-06-08T09:15:00Z'
  },
  {
    id: '3',
    title: '飞控端GPS信号异常问题反馈',
    content: '<p>今天在现场测试时发现，无人机在飞行过程中出现GPS信号丢失的情况，导致自动返航功能触发。</p><p><strong>问题详情：</strong></p><ul><li>飞行高度：120m</li><li>天气状况：多云</li><li>重复出现次数：3次</li><li>持续时间：约10-15秒</li></ul><p>请开发同事帮忙分析一下可能的原因。</p>',
    section: SECTIONS.TASK_COLLAB,
    tags: ['问题反馈', 'GPS', '飞控'],
    status: 'normal',
    authorId: 'flight',
    author: MOCK_USERS[4],
    authorLocation: '浙江杭州',
    viewCount: 45,
    likeCount: 8,
    commentCount: 4,
    createdAt: '2026-06-07T16:45:00Z',
    updatedAt: '2026-06-07T16:45:00Z'
  },
  {
    id: '4',
    title: '系统部署指南（完整版）',
    content: '<h3>1. 环境要求</h3><p><strong>操作系统：</strong>Ubuntu 20.04 LTS</p><p><strong>内存：</strong>至少8GB</p><p><strong>CPU：</strong>4核以上</p><h3>2. 安装步骤</h3><pre>sudo apt-get update\nsudo apt-get install docker docker-compose\n</pre><h3>3. 配置文件</h3><p>配置文件位于 <code>/etc/uav-system/config.yml</code></p><h3>4. 启动命令</h3><pre>docker-compose up -d</pre>',
    section: SECTIONS.KNOWLEDGE,
    tags: ['部署', '文档', '指南'],
    status: 'pinned',
    authorId: 'deploy',
    author: MOCK_USERS[3],
    authorLocation: '广东深圳',
    viewCount: 203,
    likeCount: 32,
    commentCount: 5,
    createdAt: '2026-06-05T09:00:00Z',
    updatedAt: '2026-06-06T11:30:00Z'
  },
  {
    id: '5',
    title: 'ConvLSTM气象预测模型更新',
    content: '<p>我们对ConvLSTM气象预测模型进行了更新，主要改进包括：</p><ul><li>增加了新的气象特征输入（湿度、气压）</li><li>调整了网络层数从3层增加到5层</li><li>优化了学习率调度策略</li></ul><p>测试结果显示，预测准确率提升了约8%。新模型已经部署到测试环境，欢迎大家测试并反馈问题。</p>',
    section: SECTIONS.TECH_DISCUSS,
    tags: ['机器学习', 'ConvLSTM', '气象'],
    status: 'normal',
    authorId: 'dev',
    author: MOCK_USERS[1],
    authorLocation: '四川成都',
    viewCount: 67,
    likeCount: 12,
    commentCount: 3,
    createdAt: '2026-06-06T11:20:00Z',
    updatedAt: '2026-06-06T11:20:00Z'
  },
  {
    id: '6',
    title: '生产环境数据同步任务',
    content: '<p>请部署同事协助完成以下任务：</p><ol><li>将测试环境的最新路径规划数据同步到生产环境</li><li>验证数据完整性</li><li>更新生产环境的配置文件</li></ol><p>预计完成时间：本周五之前</p>',
    section: SECTIONS.TASK_COLLAB,
    tags: ['任务', '数据同步', '生产'],
    status: 'normal',
    authorId: 'prod',
    author: MOCK_USERS[5],
    authorLocation: '上海',
    viewCount: 28,
    likeCount: 4,
    commentCount: 2,
    createdAt: '2026-06-08T08:30:00Z',
    updatedAt: '2026-06-08T08:30:00Z'
  }
]

const MOCK_COMMENTS = [
  {
    id: 'c1',
    postId: '1',
    content: '收到，我们测试部门会尽快安排测试！',
    authorId: 'test',
    author: MOCK_USERS[2],
    authorLocation: '江苏南京',
    createdAt: '2026-06-08T10:30:00Z'
  },
  {
    id: 'c2',
    postId: '1',
    content: '部署这边已经准备就绪，等待测试通过后进行部署。',
    authorId: 'deploy',
    author: MOCK_USERS[3],
    authorLocation: '广东深圳',
    createdAt: '2026-06-08T11:00:00Z'
  },
  {
    id: 'c3',
    postId: '2',
    content: '试试调整启发式函数的权重，可能会有帮助。',
    authorId: 'dev',
    author: MOCK_USERS[1],
    authorLocation: '四川成都',
    createdAt: '2026-06-07T15:20:00Z'
  },
  {
    id: 'c4',
    postId: '3',
    content: '我来分析一下，可能是信号干扰问题。',
    authorId: 'dev',
    author: MOCK_USERS[1],
    authorLocation: '四川成都',
    createdAt: '2026-06-07T17:00:00Z'
  },
  {
    id: 'c5',
    postId: '4',
    content: '文档很详细，谢谢分享！',
    authorId: 'test',
    author: MOCK_USERS[2],
    authorLocation: '江苏南京',
    createdAt: '2026-06-05T14:00:00Z'
  }
]

const MOCK_NOTIFICATIONS = [
  {
    id: 'n1',
    userId: 'dev',
    type: 'reply',
    sourceId: 'c3',
    source: { postId: '2', postTitle: '关于DE-RRT*算法参数调优的讨论' },
    read: false,
    createdAt: '2026-06-07T15:20:00Z'
  },
  {
    id: 'n2',
    userId: 'flight',
    type: 'reply',
    sourceId: 'c4',
    source: { postId: '3', postTitle: '飞控端GPS信号异常问题反馈' },
    read: false,
    createdAt: '2026-06-07T17:00:00Z'
  }
]

const forumApi = {
  SECTIONS,
  SECTION_LABELS,

  // 获取每个板块的帖子统计
  getSectionStats() {
    const stats = {};
    Object.values(SECTIONS).forEach(section => {
      stats[section] = MOCK_POSTS.filter(p => p.section === section).length;
    });
    return Promise.resolve(stats);
  },

  getSections() {
    return Promise.resolve(Object.entries(SECTION_LABELS).map(([key, label]) => ({
      key,
      label
    })))
  },

  getPosts(params = {}) {
    let posts = [...MOCK_POSTS]
    
    if (params.section) {
      posts = posts.filter(p => p.section === params.section)
    }
    
    if (params.status) {
      posts = posts.filter(p => p.status === params.status)
    }
    
    if (params.search) {
      const search = params.search.toLowerCase()
      posts = posts.filter(p => 
        p.title.toLowerCase().includes(search) || 
        p.content.toLowerCase().includes(search)
      )
    }
    
    posts.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    
    const page = parseInt(params.page) || 1
    const pageSize = parseInt(params.pageSize) || 10
    const total = posts.length
    const start = (page - 1) * pageSize
    const end = start + pageSize
    
    return Promise.resolve({
      list: posts.slice(start, end),
      total,
      page,
      pageSize
    })
  },

  getPost(id) {
    const post = MOCK_POSTS.find(p => p.id === id)
    if (!post) {
      return Promise.reject(new Error('Post not found'))
    }
    return Promise.resolve(post)
  },

  createPost(data) {
    const newPost = {
      id: Date.now().toString(),
      ...data,
      status: 'normal',
      viewCount: 0,
      likeCount: 0,
      commentCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      author: MOCK_USERS.find(u => u.id === data.authorId)
    }
    MOCK_POSTS.unshift(newPost)
    return Promise.resolve(newPost)
  },

  updatePost(id, data) {
    const index = MOCK_POSTS.findIndex(p => p.id === id)
    if (index === -1) {
      return Promise.reject(new Error('Post not found'))
    }
    MOCK_POSTS[index] = {
      ...MOCK_POSTS[index],
      ...data,
      updatedAt: new Date().toISOString()
    }
    return Promise.resolve(MOCK_POSTS[index])
  },

  deletePost(id) {
    const index = MOCK_POSTS.findIndex(p => p.id === id)
    if (index === -1) {
      return Promise.reject(new Error('Post not found'))
    }
    MOCK_POSTS.splice(index, 1)
    return Promise.resolve({ success: true })
  },

  getComments(postId) {
    const comments = MOCK_COMMENTS.filter(c => c.postId === postId)
    comments.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
    return Promise.resolve(comments)
  },

  createComment(postId, content, authorId, authorLocation = null) {
    const newComment = {
      id: `c${Date.now()}`,
      postId,
      content,
      authorId,
      author: MOCK_USERS.find(u => u.id === authorId),
      authorLocation: authorLocation || generateMockLocation(),
      createdAt: new Date().toISOString()
    }
    MOCK_COMMENTS.push(newComment)
    
    const postIndex = MOCK_POSTS.findIndex(p => p.id === postId)
    if (postIndex !== -1) {
      MOCK_POSTS[postIndex].commentCount++
    }
    
    return Promise.resolve(newComment)
  },

  deleteComment(id) {
    const index = MOCK_COMMENTS.findIndex(c => c.id === id)
    if (index === -1) {
      return Promise.reject(new Error('Comment not found'))
    }
    const comment = MOCK_COMMENTS[index]
    MOCK_COMMENTS.splice(index, 1)
    
    const postIndex = MOCK_POSTS.findIndex(p => p.id === comment.postId)
    if (postIndex !== -1) {
      MOCK_POSTS[postIndex].commentCount--
    }
    
    return Promise.resolve({ success: true })
  },

  getNotifications(userId) {
    const notifications = MOCK_NOTIFICATIONS.filter(n => n.userId === userId)
    notifications.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    return Promise.resolve(notifications)
  },

  markNotificationAsRead(id) {
    const index = MOCK_NOTIFICATIONS.findIndex(n => n.id === id)
    if (index !== -1) {
      MOCK_NOTIFICATIONS[index].read = true
    }
    return Promise.resolve({ success: true })
  },

  markAllNotificationsAsRead(userId) {
    MOCK_NOTIFICATIONS.forEach(n => {
      if (n.userId === userId) {
        n.read = true
      }
    })
    return Promise.resolve({ success: true })
  },

  getUsers() {
    return Promise.resolve(MOCK_USERS)
  }
}

// 注意：canPost 和 canReply 权限检查现在由前端 authStore.hasPermission 统一处理
// 查看 ForumView.vue 中的 canPost 和 canReply computed 属性

// 辅助函数：生成模拟地理位置
function generateMockLocation() {
  const locations = [
    '北京', '上海', '广东广州', '广东深圳', '四川成都', '四川绵阳',
    '浙江杭州', '浙江宁波', '江苏南京', '江苏苏州', '湖北武汉',
    '陕西西安', '重庆', '天津', '河南郑州', '福建厦门'
  ]
  return locations[Math.floor(Math.random() * locations.length)]
}

export { SECTIONS, SECTION_LABELS }
export default forumApi