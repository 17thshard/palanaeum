<template>
  <nav class="navigation-bar">
    <ul class="navigation-bar__links">
      <li><a class="navigation-bar__link" href="/events/">Events</a></li>
      <li><a class="navigation-bar__link" href="/recent/">Recent</a></li>
      <li><a class="navigation-bar__link" href="/tags/">Tags</a></li>
      <li><a class="navigation-bar__link" href="https://coppermind.net/" target="_blank">Wiki</a></li>
      <li><a class="navigation-bar__link" href="https://discord.gg/DUMHAVV" target="_blank">Chat</a></li>
    </ul>
  </nav>
</template>

<script>
export default {
  name: 'NavBar'
}
</script>

<style lang="scss">
.navigation-bar {
  font-family: 'Roboto Slab', serif;
  display: flex;
  align-items: stretch;

  &__links {
    list-style-type: none;
    display: flex;
    align-items: stretch;
    margin: 0;
    padding: 0;

    li {
      display: flex;
      align-items: stretch;
    }
  }

  &__link {
    display: flex;
    align-items: center;
    padding: 8px 16px;

    &:hover {
      color: $text-light;
      background: $theme-color;
    }
  }
}
</style>
