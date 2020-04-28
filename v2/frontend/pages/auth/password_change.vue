<template>
  <GridContainer>
    <GridCell :width="6" :start="4">
      <Card>
        <template slot="header">
          Register
        </template>

        <Form @submit="changePassword">
          <label for="password-change__current-password" class="form__label">Current password</label>
          <input
            id="password-change__current-password"
            v-model="currentPassword"
            class="form__control"
            type="password"
            autocomplete="new-password"
            required
          >

          <label for="password-change__new-password" class="form__label">New password</label>
          <div class="form__control">
            <input
              id="password-change__new-password"
              v-model="newPassword"
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

          <label for="password-change__new-password-confirmation" class="form__label">New password confirmation</label>
          <div class="form__control">
            <input
              id="password-change__new-password-confirmation"
              v-model="newPasswordConfirmation"
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
                Change password
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
  components: { Form, GridContainer, Button, GridCell, Card },
  data () {
    return {
      currentPassword: '',
      newPassword: '',
      newPasswordConfirmation: ''
    }
  },
  methods: {
    async changePassword () {
    }
  }
}
</script>
