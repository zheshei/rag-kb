// 认证状态（Pinia）：token 持久化 + 用户信息 + 路由拦截辅助
import { defineStore } from 'pinia'
import { getMe } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin'
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    async refreshMe() {
      if (!this.token) return
      try {
        this.user = await getMe(this.token)
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch (e) {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    }
  }
})
