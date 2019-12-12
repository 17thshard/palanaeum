<template>
  <GridRow>
    <GridColumn :width="6" center>
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
    </GridColumn>
  </GridRow>
</template>

<script>
import Card from '@/components/ui/Card.vue'
import GridColumn from '@/components/ui/GridColumn.vue'
import GridRow from '@/components/ui/GridRow.vue'
import Button from '@/components/ui/Button.vue'

export default {
  middleware: 'auth',
  auth: 'guest',
  components: { Button, GridRow, GridColumn, Card },
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
