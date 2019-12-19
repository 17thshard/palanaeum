<template>
  <GridContainer>
    <GridCell :width="6" center>
      <Card>
        <template slot="header">
          Sign in
        </template>

        <label for="username">Username</label> <input id="username" v-model="username" type="text"><br>
        <label for="password">Password</label> <input id="password" v-model="password" type="password"><br>
        <Button @click="login" type="submit" theme="dark">
          Sign in
        </Button>
      </Card>
    </GridCell>
  </GridContainer>
</template>

<script>
import Card from '@/components/ui/Card.vue'
import GridCell from '@/components/ui/GridCell.vue'
import Button from '@/components/ui/Button.vue'
import GridContainer from '@/components/ui/GridContainer.vue'

export default {
  middleware: 'auth',
  auth: 'guest',
  components: { GridContainer, Button, GridCell, Card },
  data () {
    return {
      username: '',
      password: ''
    }
  },
  methods: {
    async login () {
      try {
        await this.$auth.loginWith('local', {
          data: {
            username: this.username,
            password: this.password
          }
        })
      } catch (e) {
      }
    }
  }
}
</script>
