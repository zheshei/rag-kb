<template>
  <el-container class="home-page">
    <el-header class="home-header">
      <span class="logo">📚 RAG 知识库问答</span>
      <div class="header-right">
        <el-tag v-if="auth.isAdmin" type="danger" size="small" effect="dark" class="role-tag">管理员</el-tag>
        <el-button link @click="$router.push('/chat')">知识库问答</el-button>
        <el-button v-if="auth.isAdmin" link @click="$router.push('/kb')">知识库管理</el-button>
        <el-button v-if="auth.isAdmin" link @click="$router.push('/dashboard')">数据看板</el-button>
        <el-button link @click="$router.push('/profile')">修改密码</el-button>
        <el-button link @click="onLogout">退出</el-button>
      </div>
    </el-header>
    <el-main class="home-main">
      <el-card shadow="never" class="welcome">
        <h2>欢迎，{{ auth.user?.username }}</h2>
        <p class="role">当前角色：{{ auth.isAdmin ? '管理员（可管理知识库）' : '普通用户（仅问答）' }}</p>
        <el-divider />
        <div class="features">
          <el-card shadow="hover" class="feature">
            <h3>🗂️ 知识库管理</h3>
            <p>管理员可上传商品文档（PDF / Word / TXT / Markdown），系统自动解析、分块、向量化入库。</p>
          </el-card>
          <el-card shadow="hover" class="feature">
            <h3>💬 知识库问答</h3>
            <p>基于 LangChain 混合检索（向量 + BM25 + RRF），流式生成回答并展示知识库引用片段。</p>
          </el-card>
          <el-card shadow="hover" class="feature">
            <h3>🔒 多会话与历史</h3>
            <p>每个用户拥有独立的多会话管理，问答与引用自动持久化，随时找回历史对话。</p>
          </el-card>
        </div>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

function onLogout() {
  auth.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}
.home-header {
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
.role-tag {
  margin-right: 8px;
}
.home-main {
  display: flex;
  justify-content: center;
  padding-top: 40px;
}
.welcome {
  width: 860px;
  padding: 20px 24px;
}
.welcome h2 {
  color: #303133;
}
.role {
  color: #909399;
  margin-top: 6px;
}
.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.feature h3 {
  margin-bottom: 8px;
  color: #409eff;
}
.feature p {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
}
</style>
