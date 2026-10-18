<template>
  <el-container class="dash-page">
    <el-header class="dash-header">
      <span class="logo">📊 数据看板</span>
      <el-button link @click="$router.push('/')">返回首页</el-button>
    </el-header>

    <el-main class="dash-main">
      <!-- 核心指标 -->
      <div class="stat-grid">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="用户数" :value="stats.users" />
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="文档数" :value="stats.documents" />
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="向量分块" :value="stats.chunks" />
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="会话数" :value="stats.conversations" />
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="问答消息" :value="stats.messages" />
        </el-card>
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="向量库条目" :value="stats.vector_count" />
        </el-card>
      </div>

      <!-- 最近文档 -->
      <el-card shadow="never" class="recent-card">
        <template #header>
          <div class="list-header">
            <span>最近上传文档</span>
            <el-button size="small" @click="load">刷新</el-button>
          </div>
        </template>
        <el-table :data="stats.recent_documents || []" v-loading="loading" empty-text="暂无文档">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
              <el-tag v-else-if="row.status === 'processing'" type="warning" size="small">处理中</el-tag>
              <el-tag v-else type="danger" size="small">失败</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块数" width="90" />
          <el-table-column label="上传时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

const stats = ref({})
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/dashboard/stats', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    const data = await resp.json()
    if (!resp.ok) throw new Error(data.detail || '加载失败')
    stats.value = data
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function formatTime(s) {
  if (!s) return ''
  const d = new Date(s)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

onMounted(load)
</script>

<style scoped>
.dash-page {
  min-height: 100vh;
}
.dash-header {
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
.dash-main {
  max-width: 1080px;
  margin: 0 auto;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  text-align: center;
}
.recent-card {
  margin-bottom: 20px;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
