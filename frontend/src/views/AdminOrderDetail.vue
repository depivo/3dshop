<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const props = defineProps({ id: String })
const router = useRouter()

const STATUS_OPTIONS = [
  { value: 'new', label: 'Новий' },
  { value: 'quoted', label: 'Оцінений' },
  { value: 'printing', label: 'У друці' },
  { value: 'done', label: 'Готовий' },
  { value: 'cancelled', label: 'Скасований' },
]

const order = ref(null)
const loading = ref(true)
const errorMessage = ref('')
const saving = ref(false)
const saved = ref(false)

const editForm = reactive({ status: '', price: '' })

async function loadOrder() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await api.get(`/admin/orders/${props.id}`)
    order.value = data
    editForm.status = data.status
    editForm.price = data.price ?? ''
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Не вдалося завантажити заявку'
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  saved.value = false
  errorMessage.value = ''
  try {
    const payload = {
      status: editForm.status,
      price: editForm.price === '' ? null : Number(editForm.price),
    }
    const { data } = await api.patch(`/admin/orders/${props.id}`, payload)
    order.value = data
    saved.value = true
    setTimeout(() => (saved.value = false), 2500)
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Не вдалося зберегти зміни'
  } finally {
    saving.value = false
  }
}

function downloadUrl(fileId) {
  return `/api/admin/orders/${props.id}/files/${fileId}`
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatSize(bytes) {
  return `${(bytes / 1024 / 1024).toFixed(2)} МБ`
}

onMounted(loadOrder)
</script>

<template>
  <div class="admin-shell">
    <header class="admin-topbar">
      <div class="wrap admin-topbar-inner">
        <div class="admin-title">
          <span class="wordmark">ЦЕХ</span>
          <span class="page-name">Заявка</span>
        </div>
        <button type="button" class="btn btn-ghost btn-sm" @click="router.push({ name: 'admin-orders' })">
          ← До списку
        </button>
      </div>
    </header>

    <main class="admin-main">
      <div class="wrap">
        <p v-if="loading" class="muted">Завантаження…</p>
        <p v-else-if="errorMessage && !order" class="error-text">{{ errorMessage }}</p>

        <div v-else-if="order" class="detail-grid">
          <div class="panel bracket">
            <span class="bl"></span><span class="br"></span>
            <span class="eyebrow">клієнт</span>
            <h1>{{ order.name }}</h1>
            <div class="info-row"><span class="info-label">Телефон</span><a :href="`tel:${order.phone}`">{{ order.phone }}</a></div>
            <div class="info-row"><span class="info-label">Заявка №</span><span class="tabular-nums">{{ order.id.slice(0, 8) }}</span></div>
            <div class="info-row"><span class="info-label">Створена</span><span class="tabular-nums">{{ formatDate(order.created_at) }}</span></div>
            <div v-if="order.comment" class="comment-block">
              <span class="info-label">Коментар</span>
              <p>{{ order.comment }}</p>
            </div>

            <hr class="divider" />

            <span class="eyebrow">файли моделі ({{ order.files.length }})</span>
            <ul class="files-list">
              <li v-for="f in order.files" :key="f.id" class="files-list-item">
                <div>
                  <div class="file-name">{{ f.original_filename }}</div>
                  <div class="file-size tabular-nums">{{ formatSize(f.file_size) }}</div>
                </div>
                <a :href="downloadUrl(f.id)" class="btn btn-ghost btn-sm" download>Завантажити</a>
              </li>
            </ul>
          </div>

          <form class="panel bracket edit-panel" @submit.prevent="handleSave">
            <span class="bl"></span><span class="br"></span>
            <span class="eyebrow">обробка заявки</span>
            <h2>Ціна і статус</h2>

            <div class="field">
              <label for="status">Статус</label>
              <select id="status" v-model="editForm.status">
                <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>

            <div class="field">
              <label for="price">Ціна, грн</label>
              <input id="price" v-model="editForm.price" type="number" min="0" step="1" placeholder="Не виставлена" />
            </div>

            <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
            <p v-if="saved" class="saved-text">Збережено</p>

            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Зберігаємо…' : 'Зберегти' }}
            </button>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
  align-items: start;
}
.panel {
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.panel h1 {
  font-size: 1.5rem;
  margin: 8px 0 12px;
}
.panel h2 {
  font-size: 1.15rem;
  margin: 8px 0 6px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.92rem;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}
.info-label {
  color: var(--text-faint);
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  flex-shrink: 0;
}
.comment-block {
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.comment-block p {
  color: var(--text-muted);
  font-size: 0.92rem;
  line-height: 1.55;
}
.files-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.files-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.file-name {
  font-family: var(--font-display);
  font-size: 0.86rem;
}
.file-size {
  font-size: 0.78rem;
  color: var(--text-faint);
  margin-top: 2px;
}
.panel > .btn {
  align-self: flex-start;
  margin-top: 8px;
}
.edit-panel {
  gap: 16px;
}
.saved-text {
  color: var(--status-done);
  font-size: 0.86rem;
}
.muted {
  color: var(--text-muted);
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
