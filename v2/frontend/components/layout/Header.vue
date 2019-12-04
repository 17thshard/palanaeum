<template>
  <header class="header w3-hide-small w3-hide-medium">
    <div class="header__logo">
      <a href="/" class="w3-left"><img
        id="svg-logo"
        src="https://wob.coppermind.net/media/config/arcanum-white-shapes.svg"
        alt="logo"
      ></a>
    </div>
    <div class="header__navigation">
      <div class="login w3-theme-dark  hidden ">
        <nav class="w3-bar">
          <a class="w3-hover-theme w3-bar-item" href="/auth/login/?next=/">
            <span class="fa fa-sign-in" aria-hidden="true" />
            Sign in</a>
          <a class="w3-hover-theme w3-bar-item" href="/auth/register/">
            <span class="fa fa-user-plus" aria-hidden="true" />
            Sign up
          </a>
        </nav>
      </div>
      <div id="search-box" class="w3-hide-small w3-hide-medium">
        <form class="" action="/adv_search/" method="get">
          <table style="width: 485px;">
            <tbody>
              <tr>
                <td style="padding-right:16px;">
                  <input
                    type="search"
                    style="width: 100%"
                    title="search"
                    placeholder="Search..."
                    name="query"
                    value=""
                  >
                </td>
                <td style="width: 1px">
                  <button class="w3-btn w3-round w3-theme-dark" type="submit">
                    <span class="fa fa-search" aria-hidden="true" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </form>
      </div>
      <nav class="w3-bar navigation-bar">
        <div class="navButtonHolder">
          <a class="w3-hover-theme w3-bar-item " href="/events/"> Events</a>
          <a class="w3-hover-theme w3-bar-item " href="/recent/"> Recent</a>

          <a class="w3-hover-theme w3-bar-item " href="/tags/"> Tags</a>
          <a class="w3-hover-theme w3-bar-item" href="https://coppermind.net/" target="_blank"> Wiki</a>
          <a class="w3-hover-theme w3-bar-item" href="https://discord.gg/DUMHAVV" target="_blank"> Chat</a>
          <div class="w3-dropdown-click w3-hover-theme " style="margin-left: 12px;">
            <button id="dropdown-trigger" class="w3-button w3-hover-theme">
              <span class="fa fa-user" aria-hidden="true" />
            </button>
            <div id="userMenu" class="w3-dropdown-content w3-bar-block w3-border">
              <a class="w3-hover-theme w3-bar-item " href="/collections/">
                <span class="fa fa-list" aria-hidden="true" />
                Collections
              </a>
              <a class="w3-hover-theme w3-bar-item " href="/auth/profile/">
                <span class="fa fa-cog" aria-hidden="true" />
                Settings
              </a>
              <a class="w3-hover-theme w3-bar-item " href="/auth/logout/">
                <span class="fa fa-power-off" aria-hidden="true" />
                Sign out
              </a>
            </div>
          </div>
        </div>
      </nav>
    </div>
  </header>
</template>

<script>
export default {
  name: 'Header'
}
</script>

<style lang="scss">
.header {
  font-size: 21px;
  background-color: #003a52;
  color: #fff;
  width: 100%;
  max-width: 1300px;
  height: 158px;

  &__logo {
    width: 370px;
    margin-left: 2.5%;
    padding-top: 3px;

    img {
      height: 150px;
    }
  }

  &__navigation {
    width: 500px;
    float: right;
    margin-right: 2.5%;

    .w3-bar .w3-bar-item {
      font-family: 'Roboto Slab', serif;
    }
  }
}
</style>
