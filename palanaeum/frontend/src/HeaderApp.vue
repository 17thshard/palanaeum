<template>
  <div>
    <Header />
    <MobileHeader />
  </div>
</template>

<script>
import Header from '@/components/layout/Header.vue'
import MobileHeader from '@/components/layout/MobileHeader.vue'

export default {
  name: 'HeaderApp',
  components: { MobileHeader, Header }
}
</script>
