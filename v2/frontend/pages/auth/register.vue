<template>
  <GridContainer>
    <GridCell :width="6" :start="4">
      <Card>
        <template slot="header">
          Register
        </template>

        <Form @submit="register">
          <label for="register__username" class="form__label">Username</label>
          <div class="form__control">
            <input
              id="register__username"
              v-model="username"
              type="text"
              autocomplete="username"
              maxlength="150"
              required
            >

            <div class="form__help">
              Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.
            </div>
          </div>

          <label for="register__email" class="form__label">Email</label>
          <input
            id="register__email"
            v-model="email"
            class="form__control"
            type="email"
            autocomplete="email"
            required
          >

          <label for="register__password" class="form__label">Password</label>
          <div class="form__control">
            <input
              id="register__password"
              v-model="password"
              type="password"
              minlength="8"
              autocomplete="new-password"
              required
            >

            <ul class="form__help">
              <li>Your password can't be too similar to your other personal information.</li>
              <li>Your password must contain at least 8 characters.</li>
              <li>Your password can't be a commonly used password.</li>
              <li>Your password can't be entirely numeric.</li>
            </ul>
          </div>

          <label for="register__password-confirmation" class="form__label">Password confirmation</label>
          <div class="form__control">
            <input
              id="register__password-confirmation"
              v-model="passwordConfirmation"
              type="password"
              minlength="8"
              autocomplete="new-password"
              required
            >

            <div class="form__help">
              Enter the same password as before, for verification.
            </div>
          </div>

          <div class="form__control">
            <div class="form__buttons">
              <Button type="submit">
                Sign up
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
      email: '',
      password: '',
      passwordConfirmation: ''
    }
  },
  methods: {
    async register () {
    }
  }
}
</script>
