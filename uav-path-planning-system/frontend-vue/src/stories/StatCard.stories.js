import StatCard from '../components/shared/StatCard.vue'

export default {
  title: '通用/StatCard 数字卡片',
  component: StatCard,
  tags: ['autodocs'],
  argTypes: {
    label: { control: 'text' },
    value: { control: 'number' },
    unit: { control: 'text' },
    tagText: { control: 'text' },
    tagType: { control: { type: 'select' }, options: ['success','warning','danger','info','primary'] },
    description: { control: 'text' },
    valueColor: { control: 'color' }
  }
}

export const Default = { args: { label: '今日任务数', value: 127, unit: '单', tagText: '今日', description: '较昨日 +8.3%' } }
export const 警告状态 = { args: { label: '异常任务', value: 4, unit: '单', tagText: '告警', tagType: 'warning', valueColor: '#E6A23C', description: '需要关注' } }
export const 危险状态 = { args: { label: '错误率', value: 2.4, unit: '%', tagText: '严重', tagType: 'danger', valueColor: '#F56C6C', description: '超出阈值' } }
export const 深色背景 = { args: { label: 'CPU 使用率', value: 68, unit: '%', tagText: '实时', description: '过去 60 秒均值', valueColor: '#e2e8f0' } }
