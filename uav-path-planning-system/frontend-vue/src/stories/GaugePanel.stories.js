import GaugePanel from '../components/shared/GaugePanel.vue'
export default { title: '监控/GaugePanel 仪表盘', component: GaugePanel, tags: ['autodocs'],
  argTypes: { value: { control: { type: 'range', min: 0, max: 100 } } } }
export const 正常 = { args: { label: 'CPU 使用率', value: 42, threshold: 80, avg: 48 } }
export const 告警 = { args: { label: '内存占用', value: 72, threshold: 80, avg: 60 } }
export const 超限 = { args: { label: '磁盘占用', value: 91, threshold: 85, avg: 70 } }
