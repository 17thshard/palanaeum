<template>
  <GridContainer>
    <GridCell :width="12">
      <PageTitle>Settings</PageTitle>
    </GridCell>
    <GridCell :width="6" :start="4">
      <Card>
        <template slot="header">
          Basic account information
        </template>

        <Form @submit="changeEmail">
          <label for="profile__email" class="form__label">Email</label>
          <input
            id="profile__email"
            v-model="email"
            class="form__control"
            type="email"
            autocomplete="off"
            required
          >

          <label for="profile__password" class="form__label">Password</label>
          <div class="form__control">
            <input
              id="profile__password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
            >

            <div class="form__help">
              Password is required to change your e-mail address.
            </div>
          </div>

          <div class="form__actions">
            <nuxt-link to="/auth/password_change" class="button">
              Change password
            </nuxt-link>

            <div class="form__buttons">
              <Button type="submit">
                Save
              </Button>
            </div>
          </div>
        </Form>
      </Card>
    </GridCell>

    <GridCell :width="6" :start="4">
      <Card>
        <template slot="header">
          Display settings
        </template>

        <Form @submit="changeDisplaySettings">
          <label for="profile__timezone" class="form__label">Timezone</label>
          <select
            id="profile__timezone"
            v-model="timezone"
            class="form__control"
            required
          >
            <option>UTC</option>
          </select>

          <label for="profile__page-length" class="form__label">Page length</label>
          <input
            id="profile__page-length"
            v-model="pageLength"
            class="form__control"
            type="number"
            min="0"
            required
          >

          <div class="form__actions">
            <div class="form__buttons">
              <Button type="submit">
                Save
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
import PageTitle from '@/components/layout/PageTitle.vue'

export default {
  middleware: 'auth',
  components: { PageTitle, Form, GridContainer, Button, GridCell, Card },
  data () {
    return {
      email: '',
      password: '',
      timezone: 'UTC',
      pageLength: 20
    }
  },
  methods: {
    async changeEmail () {
    },
    async changeDisplaySettings () {
    }
  }
}
</script>
