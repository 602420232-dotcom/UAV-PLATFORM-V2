import WeatherCard from '../components/shared/WeatherCard.vue'
export default { title: '气象/WeatherCard 天气卡片', component: WeatherCard, tags: ['autodocs'] }
export const 默认 = { args: { city: '北京', timeText: '2026-06-09 12:00', temperature: 26, windDir: '东南', windSpeed: 3.5, pressure: 1015, humidity: 48 } }
export const 上海 = { args: { city: '上海', timeText: '2026-06-09 14:00', temperature: 28, windDir: '东', windSpeed: 5.2, pressure: 1010, humidity: 72 } }
export const 寒冷 = { args: { city: '哈尔滨', timeText: '2026-01-05 08:00', temperature: -18, windDir: '西北', windSpeed: 7.0, pressure: 1025, humidity: 55 } }
