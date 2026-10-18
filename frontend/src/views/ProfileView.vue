<template>
  <el-container class="profile-page">
    <el-header class="profile-header">
      <span class="logo">📚 RAG 知识库问答</span>
      <el-button link @click="$router.push('/')">返回首页</el-button>
    </el-header>
    <el-main class="profile-main">
      <el-card class="profile-card" shadow="never">
        <h3>修改密码</h3>
        <el-form :model="form" label-width="90px" style="max-width: 420px; margin-top: 16px">
          <el-form-item label="原密码">
            <el-input v-model="form.old" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="form.confirm" type="password" show-password @keyup.enter="onSubmit" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="onSubmit">确认修改</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from '../api/auth'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const form = reactive({ old: '', password: '', confirm: '' })
const loading = ref(false)

async function onSubmit() {
  if (form.password !== form.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (form.password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  loading.value = true
  try {
    await changePassword(auth.token, form.old, form.password)
    ElMessage.success('密码修改成功，请重新登录')
    auth.logout()
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
}
.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.logo {
  font-size: 17px;
  font-weight: 700;
  color: #409eff;
}
.profile-main {
  display: flex;
  justify-content: center;
  padding-top: 40px;
}
.profile-card {
  width: 520px;
  padding: 12px 20px;
}
</style>
