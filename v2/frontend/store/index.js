export const state = () => ({
  miniPlayerLock: null
})

export const mutations = {
  acquireMiniPlayerLock (state, id) {
    state.miniPlayerLock = id
  },
  releaseMiniPlayerLock (state) {
    state.miniPlayerLock = null
  }
}
