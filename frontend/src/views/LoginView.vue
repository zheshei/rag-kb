<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">RAG 知识库问答系统</h2>
      <p class="sub">登录以开始</p>
      <el-form :model="form" @submit.prevent="onLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" :prefix-icon="Lock" show-password @keyup.enter="onLogin" />
        </el-form-item>
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="onLogin">
          登录
        </el-button>
      </el-form>
      <div class="footer">
        <span>没有账号？</span>
        <el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
      </div>
      <el-divider />
      <div class="hint">管理员账号：admin / 123456</div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function onLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const data = await login(form.username, form.password)
    auth.setAuth(data.access_token, data.user)
    ElMessage.success(`欢迎回来，${data.user.username}`)
    router.push(route.query.redirect || '/')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f3a93 0%, #409eff 100%);
}
.auth-card {
  width: 400px;
  padding: 16px 8px;
  border-radius: 12px;
}
.title {
  text-align: center;
  color: #303133;
  margin-bottom: 4px;
}
.sub {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-bottom: 20px;
}
.footer {
  text-align: center;
  margin-top: 14px;
  font-size: 13px;
  color: #606266;
}
.hint {
  text-align: center;
  font-size: 12px;
  color: #909399;
}
</style>
