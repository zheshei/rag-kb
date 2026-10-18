<template>
  <el-container class="kb-page">
    <el-header class="kb-header">
      <span class="logo">🗂️ 知识库管理</span>
      <el-button link @click="$router.push('/')">返回首页</el-button>
    </el-header>

    <el-main class="kb-main">
      <!-- 上传区 -->
      <el-card shadow="never" class="upload-card">
        <div class="upload-row">
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.docx,.txt,.md"
            :on-change="onFileChange"
            :on-remove="() => (selectedFile = null)"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或 <em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PDF / Word / TXT / Markdown，单文件 ≤ 50MB</div>
            </template>
          </el-upload>
          <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="onUpload">
            上传并入库
          </el-button>
        </div>
      </el-card>

      <!-- 统计 -->
      <el-card shadow="never" class="stat-card">
        <el-statistic title="知识库文档数" :value="stats.document_count" />
        <el-statistic title="向量分块数" :value="stats.chunk_count" />
      </el-card>

      <!-- 文档列表 -->
      <el-card shadow="never">
        <template #header>
          <div class="list-header">
            <span>文档列表（{{ total }}）</span>
            <el-button size="small" @click="load(1)">刷新</el-button>
          </div>
        </template>
        <el-table :data="docs" v-loading="loading" empty-text="暂无文档，请先上传">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="filename" label="文件名" min-width="220" show-overflow-tooltip />
          <el-table-column prop="file_type" label="类型" width="80" />
          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.size) }}</template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块数" width="90" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
              <el-tag v-else-if="row.status === 'processing'" type="warning" size="small">处理中</el-tag>
              <el-tag v-else type="danger" size="small">失败</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110">
            <template #default="{ row }">
              <el-popconfirm title="确定删除该文档及其向量？" @confirm="onDelete(row)">
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="total > pageSize"
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="load"
          style="margin-top: 12px; justify-content: center"
        />
      </el-card>
    </el-main>
  </el-container>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getStats, listDocuments, uploadDocument, deleteDocument } from '../api/kb'

const docs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const stats = ref({ document_count: 0, chunk_count: 0 })

function onFileChange(file) {
  selectedFile.value = file.raw
}

function formatSize(n) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

async function load(p = 1) {
  page.value = p
  loading.value = true
  try {
    const data = await listDocuments(p, pageSize.value)
    docs.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await getStats()
  } catch (e) { /* 忽略 */ }
}

async function onUpload() {
  uploading.value = true
  try {
    await uploadDocument(selectedFile.value)
    ElMessage.success('上传成功，正在后台解析入库')
    selectedFile.value = null
    loadStats()
    load(page.value)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    uploading.value = false
  }
}

async function onDelete(row) {
  try {
    await deleteDocument(row.id)
    ElMessage.success('已删除')
    loadStats()
    load(page.value)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(() => {
  loadStats()
  load(1)
})
</script>

<style scoped>
.kb-page {
  min-height: 100vh;
}
.kb-header {
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
.kb-main {
  max-width: 980px;
  margin: 0 auto;
}
.upload-card {
  margin-bottom: 16px;
}
.upload-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.upload-row .el-upload {
  flex: 1;
}
.stat-card {
  display: flex;
  gap: 60px;
  margin-bottom: 16px;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
