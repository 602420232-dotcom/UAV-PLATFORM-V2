// 统一的演示数据 Fixture
export const demoData = {
  // 无人机数据
  drones: [
    { id: 'UAV-001', name: '无人机1', type: 'multirotor', status: '在线', battery: 85, location: '39.90, 116.40' },
    { id: 'UAV-002', name: '无人机2', type: 'multirotor', status: '执行任务', battery: 60, location: '39.91, 116.41' },
    { id: 'UAV-003', name: '无人机3', type: 'fixed-wing', status: '待命', battery: 90, location: '39.92, 116.42' },
  ],

  // 任务数据
  tasks: [
    { id: 1, name: '配送任务1', type: 'delivery', location: '39.9042, 116.4074', priority: 'high', status: '待分配', description: '紧急配送任务' },
    { id: 2, name: '巡检任务1', type: 'inspection', location: '39.9142, 116.4174', priority: 'medium', status: '已分配', description: '电力线路巡检' },
    { id: 3, name: '测绘任务1', type: 'survey', location: '39.9242, 116.4274', priority: 'low', status: '已完成', description: '区域测绘' },
  ],

  // 历史记录数据
  history: [
    {
      id: 1,
      name: '路径规划任务1',
      startTime: '2024-01-01 10:00:00',
      endTime: '2024-01-01 10:02:30',
      status: '成功',
      duration: '2分30秒',
      droneCount: 2,
      taskCount: 3,
      totalDistance: 1500,
      totalTime: 25,
      routes: [
        { droneId: 1, path: ['基地', '任务点1', '任务点3', '基地'], distance: 800, time: 12, risk: '低' },
        { droneId: 2, path: ['基地', '任务点2', '基地'], distance: 700, time: 13, risk: '低' }
      ],
      weatherData: { windSpeed: 5.2, windDirection: 135, temperature: 25.5, humidity: 65, turbulence: '低', visibility: 10 }
    },
    {
      id: 2,
      name: '气象预测任务',
      startTime: '2024-01-01 09:45:00',
      endTime: '2024-01-01 09:46:15',
      status: '成功',
      duration: '1分15秒',
      droneCount: 0,
      taskCount: 0,
      totalDistance: 0,
      totalTime: 0,
      routes: [],
      weatherData: { windSpeed: 4.8, windDirection: 120, temperature: 24.8, humidity: 60, turbulence: '低', visibility: 12 }
    },
    {
      id: 3,
      name: '路径规划任务2',
      startTime: '2024-01-01 09:30:00',
      endTime: '2024-01-01 09:33:45',
      status: '成功',
      duration: '3分45秒',
      droneCount: 3,
      taskCount: 5,
      totalDistance: 2500,
      totalTime: 40,
      routes: [
        { droneId: 1, path: ['基地', '任务点1', '任务点3', '基地'], distance: 900, time: 15, risk: '低' },
        { droneId: 2, path: ['基地', '任务点2', '任务点5', '基地'], distance: 800, time: 14, risk: '中' },
        { droneId: 3, path: ['基地', '任务点4', '基地'], distance: 800, time: 11, risk: '低' }
      ],
      weatherData: { windSpeed: 6.5, windDirection: 90, temperature: 26.2, humidity: 55, turbulence: '中', visibility: 8 }
    }
  ],

  // 气象数据
  weather: {
    windSpeed: 5.2,
    windDirection: 135,
    temperature: 25.5,
    humidity: 65,
    windField: [
      { lat: 39.90, lng: 116.40, speed: 5.2, direction: 135, temperature: 25.5, humidity: 65 },
      { lat: 39.91, lng: 116.41, speed: 5.0, direction: 140, temperature: 25.3, humidity: 66 },
      { lat: 39.92, lng: 116.42, speed: 5.5, direction: 130, temperature: 25.7, humidity: 64 },
    ]
  },

  // 路径规划数据
  pathPlanning: {
    defaultTaskPoints: [
      { id: 1, name: '任务点1', lat: 39.9042, lng: 116.4074, demand: 1 },
      { id: 2, name: '任务点2', lat: 39.9142, lng: 116.4174, demand: 2 },
      { id: 3, name: '任务点3', lat: 39.9242, lng: 116.4274, demand: 1 }
    ],
    defaultSavedPlans: [
      { id: 1, name: '方案1' },
      { id: 2, name: '方案2' },
      { id: 3, name: '方案3' }
    ],
    mockResult: {
      droneCount: 2,
      taskCount: 3,
      totalDistance: 1500,
      totalTime: 25,
      routes: [
        {
          droneId: 1,
          path: ['基地', '任务点1', '任务点3', '基地'],
          distance: 800,
          time: 12,
          riskLevel: '低'
        },
        {
          droneId: 2,
          path: ['基地', '任务点2', '基地'],
          distance: 700,
          time: 13,
          riskLevel: '低'
        }
      ]
    },
    defaultRealtimeData: {
      windSpeed: 5.2,
      windDirection: 135,
      temperature: 22,
      humidity: 65,
      droneStatus: '正常',
      taskProgress: 0,
      riskLevel: '低',
      alertCount: 0
    }
  }
}

// 状态颜色映射
export const statusColors = {
  '待分配': 'blue',
  '已分配': 'orange',
  '执行中': 'purple',
  '已完成': 'green',
  '已取消': 'red',
  '成功': 'green',
  '失败': 'red',
  '进行中': 'blue'
}

export const riskColors = {
  '低': 'green',
  '中': 'orange',
  '高': 'red'
}

// 辅助函数：安全处理API响应
export function normalizeApiResponse(response) {
  if (Array.isArray(response)) return response
  if (response?.data) return normalizeApiResponse(response.data)
  if (response?.content) return normalizeApiResponse(response.content)
  return response
}
