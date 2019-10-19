<template>
  <main id="app">
    <Header></Header>
    <router-view />
  </main>
</template>

<script>
import Header from '@/components/layout/Header.vue';

export default {
  name: 'App',
  components: { Header },
};
</script>

<style lang="scss">
body {
  max-width: $max-body-width !important;
  background-color: $body-background;
  font-size: $base-font-size;
  font-family: "Roboto", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  border-style: solid;
  border-width: 1px;
  border-color: #003a52;
  background-color: #fcfcfc;
}
</style>
