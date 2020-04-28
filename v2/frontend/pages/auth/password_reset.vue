<template>
  <GridContainer>
    <GridCell :width="6" :start="4">
      <Card>
        <template slot="header">
          Recover password
        </template>

        <Form @submit="recover">
          <div class="form__instructions">
            <p>
              To reset your password you need to type in the e-mail address that's assigned to your account.
            </p>

            <p>
              Further instructions will be sent to that address.
            </p>
          </div>

          <label for="password-reset__email" class="form__label">Email</label>
          <input
            id="password-reset__email"
            v-model="email"
            class="form__control"
            type="email"
            autocomplete="email"
            required
          >

          <div class="form__control">
            <div class="form__buttons">
              <Button type="submit">
                Recover
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
      email: ''
    }
  },
  methods: {
    async recover () {
    }
  }
}
</script>
