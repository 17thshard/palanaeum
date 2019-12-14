import Vue from 'vue'
import HeaderApp from '@/HeaderApp.vue'

Vue.config.productionTip = false

new Vue({
  render: h => h(HeaderApp)
}).$mount('#header-app')
