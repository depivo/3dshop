<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const STATUS_LABELS = {
  new: 'Новий',
  quoted: 'Оцінений',
  printing: 'Друк',
  done: 'Готовий',
  cancelled: 'Скасований',
}

const FILTERS = [
  { value: '', label: 'Всі' },
  { value: 'new', label: 'Нові' },
  { value: 'quoted', label: 'Оцінені' },
  { value: 'printing', label: 'У друці' },
  { value: 'done', label: 'Готові' },
  { value: 'cancelled', label: 'Скасовані' },
]

const router = useRouter()
const orders = ref([])
const loading = ref(true)
const errorMessage = ref('')
const activeFilter = ref('')

async function loadOrders() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = activeFilter.value ? { status_filter: activeFilter.value } : {}
    const { data } = await api.get('/admin/orders', { params })
    orders.value = data
  } catch (err) {
    errorMessage.value = err.response?.data?.detail || 'Не вдалося завантажити заявки'
  } finally {
    loading.value = false
  }
}

async function handleLogout() {
  await api.post('/admin/logout')
  router.push({ name: 'admin-login' })
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatPrice(price) {
  return price == null ? '—' : `${price.toFixed(0)} грн`
}

watch(activeFilter, loadOrders)
onMounted(loadOrders)
</script>

<template>
  <div class="admin-shell">
    <header class="admin-topbar">
      <div class="wrap admin-topbar-inner">
        <div class="admin-title">
          <span class="wordmark">ЦЕХ</span>
          <span class="page-name">Заявки</span>
        </div>
        <button type="button" class="btn btn-ghost btn-sm" @click="handleLogout">Вийти</button>
      </div>
    </header>

    <main class="admin-main">
      <div class="wrap">
        <div class="filters">
          <button
            v-for="f in FILTERS"
            :key="f.value"
            type="button"
            class="filter-tab"
            :class="{ active: activeFilter === f.value }"
            @click="activeFilter = f.value"
          >
            {{ f.label }}
          </button>
        </div>

        <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
        <p v-else-if="loading" class="muted">Завантаження…</p>
        <p v-else-if="orders.length === 0" class="muted">Заявок поки немає.</p>

        <div v-else class="table-wrap bracket">
          <span class="bl"></span><span class="br"></span>
          <table class="orders-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Клієнт</th>
                <th>Файл</th>
                <th>Статус</th>
                <th class="tabular-nums">Ціна</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="order in orders"
                :key="order.id"
                class="order-row"
                tabindex="0"
                @click="router.push({ name: 'admin-order-detail', params: { id: order.id } })"
              >
                <td class="tabular-nums muted-cell">{{ formatDate(order.created_at) }}</td>
                <td>
                  <div class="client-name">{{ order.name }}</div>
                  <div class="client-phone muted-cell">{{ order.phone }}</div>
                </td>
                <td class="file-cell">
                  {{ order.files[0]?.original_filename }}
                  <span v-if="order.files.length > 1" class="file-more">+{{ order.files.length - 1 }}</span>
                </td>
                <td>
                  <span class="status-badge" :class="`status-${order.status}`">{{ STATUS_LABELS[order.status] }}</span>
                </td>
                <td class="tabular-nums">{{ formatPrice(order.price) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.filter-tab {
  font-family: var(--font-display);
  font-size: 0.76rem;
  letter-spacing: 0.03em;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  padding: 8px 14px;
  cursor: pointer;
  transition: border-color 0.15s ease, color 0.15s ease;
}
.filter-tab:hover {
  color: var(--text);
}
.filter-tab.active {
  color: var(--bg);
  background: var(--accent-cool);
  border-color: var(--accent-cool);
}

.muted {
  color: var(--text-muted);
}

.table-wrap {
  overflow-x: auto;
}
.orders-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}
.orders-table th {
  text-align: left;
  font-family: var(--font-display);
  font-size: 0.7rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-faint);
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.orders-table td {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.order-row {
  cursor: pointer;
  transition: background 0.12s ease;
}
.order-row:hover,
.order-row:focus-visible {
  background: var(--bg-elevated-2);
  outline: none;
}
.order-row:last-child td {
  border-bottom: none;
}
.client-name {
  font-weight: 600;
}
.muted-cell {
  color: var(--text-muted);
  font-size: 0.86rem;
}
.file-cell {
  font-family: var(--font-display);
  font-size: 0.84rem;
  color: var(--text-muted);
}
.file-more {
  color: var(--text-faint);
  margin-left: 4px;
}
</style>
