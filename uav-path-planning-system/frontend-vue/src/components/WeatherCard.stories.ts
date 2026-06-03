import WeatherCard from './WeatherCard.vue'

export default {
  title: 'Components/WeatherCard',
  component: WeatherCard,
  argTypes: {
    status: {
      control: { type: 'select' },
      options: ['normal', 'warning', 'danger']
    }
  }
}

const Template = (args: Record<string, unknown>) => ({
  components: { WeatherCard },
  setup() { return { args } },
  template: '<WeatherCard v-bind="args" />'
})

export const Normal = Template.bind({})
Normal.args = {
  title: '温度',
  value: 25.5,
  unit: '°C',
  status: 'normal'
}

export const Warning = Template.bind({})
Warning.args = {
  title: '风速',
  value: 12.0,
  unit: 'm/s',
  status: 'warning'
}

export const Danger = Template.bind({})
Danger.args = {
  title: '湍流强度',
  value: 3.5,
  unit: 'm²/s²',
  status: 'danger'
}
