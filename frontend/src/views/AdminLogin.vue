<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()
const route = useRoute()

const form = reactive({ username: '', password: '' })
const submitting = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  errorMessage.value = ''
  submitting.value = true
  try {
    await api.post('/admin/login', { username: form.username, password: form.password })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/admin'
    router.push(redirect)
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Не вдалося увійти. Спробуйте ще раз.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-panel bracket">
      <span class="bl"></span><span class="br"></span>
      <div class="wordmark">ЦЕХ<small>3D-ДРУК НА ЗАМОВЛЕННЯ</small></div>
      <span class="eyebrow">адмінка</span>
      <h1>Вхід до панелі заявок</h1>

      <form @submit.prevent="handleSubmit">
        <div class="field">
          <label for="username">Логін</label>
          <input id="username" v-model="form.username" type="text" autocomplete="username" />
        </div>
        <div class="field">
          <label for="password">Пароль</label>
          <input id="password" v-model="form.password" type="password" autocomplete="current-password" />
        </div>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? 'Входимо…' : 'Увійти' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.login-panel {
  width: 100%;
  max-width: 380px;
  padding: 36px 32px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.login-panel .wordmark {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 700;
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 18px;
}
.login-panel .wordmark small {
  font-size: 0.62rem;
  color: var(--text-faint);
  letter-spacing: 0.1em;
}
.login-panel h1 {
  font-size: 1.4rem;
  margin: 10px 0 24px;
}
.login-panel form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.login-panel .btn {
  justify-content: center;
  margin-top: 4px;
}
</style>
