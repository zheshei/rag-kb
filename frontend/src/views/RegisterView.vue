<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="title">注册账号</h2>
      <p class="sub">注册后即可进行知识库问答</p>
      <el-form :model="form" @submit.prevent="onRegister">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名（2-32 字符）" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码（至少 6 位）" size="large" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.confirm" type="password" placeholder="确认密码" size="large" :prefix-icon="Lock" show-password @keyup.enter="onRegister" />
        </el-form-item>
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="onRegister">
          注册
        </el-button>
      </el-form>
      <div class="footer">
        <span>已有账号？</span>
        <el-link type="primary" @click="$router.push('/login')">去登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { register } from '../api/auth'

const router = useRouter()
const form = reactive({ username: '', password: '', confirm: '' })
const loading = ref(false)

async function onRegister() {
  if (form.password !== form.confirm) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await register(form.username, form.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
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
</style>
