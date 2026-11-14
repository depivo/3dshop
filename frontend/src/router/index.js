import { createRouter, createWebHistory } from 'vue-router'
import api from '../api/client'

const routes = [
  { path: '/', name: 'order', component: () => import('../views/OrderForm.vue') },
  { path: '/admin/login', name: 'admin-login', component: () => import('../views/AdminLogin.vue') },
  {
    path: '/admin',
    name: 'admin-orders',
    component: () => import('../views/AdminOrders.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/orders/:id',
    name: 'admin-order-detail',
    component: () => import('../views/AdminOrderDetail.vue'),
    meta: { requiresAuth: true },
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true

  try {
    await api.get('/admin/me')
    return true
  } catch {
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
})

export default router
