<template>
  <div class="user-panel">
    <ul class="user-panel__links">
      <li>
        <a :title="showText ? 'Sign in' : undefined" class="user-panel__link" href="/auth/login/?next=/">
          <span class="fa fa-sign-in" aria-hidden="true" />
          {{ showText ? 'Sign in' : undefined }}
        </a>
      </li>
      <li>
        <a :title="showText ? 'Sign up' : undefined" class="user-panel__link" href="/auth/register/">
          <span class="fa fa-user-plus" aria-hidden="true" />
          {{ showText ? 'Sign up' : undefined }}
        </a>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'UserPanel',
  props: {
    showText: Boolean
  }
}
</script>

<style lang="scss">
.user-panel {
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

    .fa {
      margin-right: 4px;
    }

    &:hover {
      color: $text-light;
      background: $theme-color;
    }
  }
}
</style>
