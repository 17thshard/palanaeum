<template>
  <GridContainer>
    <GridCell :width="6" :start="4">
      <Card>
        <template slot="header">
          Sign in
        </template>

        <Form @submit="login">
          <label for="login__username" class="form__label">Username</label>
          <input
            id="login__username"
            v-model="username"
            class="form__control"
            type="text"
            autocomplete="username"
            required
          >

          <label for="login__password" class="form__label">Password</label>
          <input
            id="login__password"
            v-model="password"
            class="form__control"
            type="password"
            autocomplete="current-password"
            required
          >

          <div class="form__control">
            <nuxt-link to="/auth/password_reset">
              <small>Forgot your password?</small>
            </nuxt-link>

            <div class="form__buttons">
              <Button type="submit">
                Sign in
              </Button>
            </div>
          </div>
        </Form>
      </Card>
    </GridCell>
  </GridContainer>
</template>

<script>
import Card from '@/components/ui/Card.vue'
import GridCell from '@/components/ui/GridCell.vue'
import Button from '@/components/ui/Button.vue'
import GridContainer from '@/components/ui/GridContainer.vue'
import Form from '@/components/ui/Form.vue'

export default {
  middleware: 'auth',
  auth: 'guest',
  components: { Form, GridContainer, Button, GridCell, Card },
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
