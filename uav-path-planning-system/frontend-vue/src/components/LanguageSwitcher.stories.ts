import LanguageSwitcher from './LanguageSwitcher.vue'

export default {
  title: 'Components/LanguageSwitcher',
  component: LanguageSwitcher
}

const Template = (args: Record<string, unknown>) => ({
  components: { LanguageSwitcher },
  setup() { return { args } },
  template: '<LanguageSwitcher v-bind="args" />'
})

export const Default = Template.bind({})
Default.args = {}
