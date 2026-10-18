<template>
  <el-container class="chat-page">
    <el-header class="chat-header">
      <span class="logo">💬 知识库问答</span>
      <el-dropdown @command="onHeaderCommand">
        <span class="user-chip">
          {{ auth.user?.username }}
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-if="auth.isAdmin" command="kb">知识库管理</el-dropdown-item>
            <el-dropdown-item command="profile">修改密码</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-header>

    <el-container class="chat-body">
      <!-- 会话侧栏（M4） -->
      <el-aside width="260px" class="chat-aside">
        <div class="aside-top">
          <el-button type="primary" size="small" style="width: 100%" @click="onNewConversation">
            ＋ 新建会话
          </el-button>
        </div>
        <div class="conv-list" v-loading="loadingConvs">
          <div
            v-for="c in conversations"
            :key="c.id"
            class="conv-item"
            :class="{ active: currentId === c.id }"
            @click="onSelectConversation(c)"
          >
            <div class="conv-title">{{ c.title }}</div>
            <div class="conv-meta">
              <span>{{ formatTime(c.updated_at) }}</span>
              <span class="conv-actions" @click.stop>
                <el-button link size="small" type="primary" @click="onRename(c)">重命名</el-button>
                <el-button link size="small" type="danger" @click="onDeleteConversation(c)">删除</el-button>
              </span>
            </div>
          </div>
          <div v-if="!loadingConvs && conversations.length === 0" class="conv-empty">
            暂无会话，点击上方新建
          </div>
        </div>
      </el-aside>

      <!-- 聊天主区 -->
      <el-main class="chat-main">
        <div class="msg-list" ref="listRef">
          <div v-if="messages.length === 0" class="empty">
            <div class="empty-title">{{ currentId ? '该会话暂无消息' : '电商商品知识库问答' }}</div>
            <div class="empty-tip">{{ currentId ? '输入问题开始对话，问答会自动保存到本会话' : '例如：无线蓝牙耳机续航多久？智能手表支持哪些运动模式？' }}</div>
          </div>

          <div v-for="(m, i) in messages" :key="i" class="msg-row" :class="m.role">
            <div class="msg-bubble">
              <div class="msg-role">{{ m.role === 'user' ? '我' : '助手' }}</div>
              <div class="msg-text" :class="{ loading: m.loading }">{{ m.text || (m.loading ? '思考中…' : '') }}</div>
            </div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="input-area">
          <el-input
            v-model="question"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="输入你的问题，例如：无线蓝牙耳机续航多久？"
            :disabled="sending"
            @keydown.enter.exact.prevent="onSend"
          />
          <div class="input-actions">
            <el-button type="primary" :loading="sending" :disabled="!question.trim()" @click="onSend">
              发送
            </el-button>
          </div>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { askStream } from '../api/chat'
import { listConversations, createConversation, renameConversation, deleteConversation, getMessages } from '../api/conversation'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const messages = ref([])
const question = ref('')
const topK = 5
const sending = ref(false)
const listRef = ref(null)
const conversations = ref([])
const loadingConvs = ref(false)
const currentId = ref(null)

function onHeaderCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    ElMessage.success('已退出登录')
    window.location.href = '/login'
  } else if (cmd === 'kb') {
    window.location.href = '/kb'
  } else if (cmd === 'profile') {
    window.location.href = '/profile'
  }
}

function scrollBottom() {
  nextTick(() => {
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
  })
}

function formatTime(s) {
  if (!s) return ''
  const d = new Date(s)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return sameDay ? `${hh}:${mm}` : `${d.getMonth() + 1}-${d.getDate()} ${hh}:${mm}`
}

async function loadConversations() {
  loadingConvs.value = true
  try {
    const data = await listConversations(1, 100)
    conversations.value = data.items
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loadingConvs.value = false
  }
}

async function onSelectConversation(c) {
  currentId.value = c.id
  sending.value = false
  try {
    const msgs = await getMessages(c.id)
    messages.value = msgs.map((m) => ({
      role: m.role,
      text: m.content,
      loading: false
    }))
  } catch (e) {
    ElMessage.error(e.message)
    messages.value = []
  }
  scrollBottom()
}

async function onNewConversation() {
  try {
    const conv = await createConversation('新会话')
    conversations.value.unshift(conv)
    currentId.value = conv.id
    messages.value = []
    scrollBottom()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function onRename(c) {
  try {
    const { value } = await ElMessageBox.prompt('输入新的会话标题', '重命名会话', {
      inputValue: c.title,
      inputPlaceholder: '会话标题',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    const updated = await renameConversation(c.id, value)
    const idx = conversations.value.findIndex((x) => x.id === c.id)
    if (idx >= 0) conversations.value[idx] = updated
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('重命名失败')
  }
}

async function onDeleteConversation(c) {
  try {
    await ElMessageBox.confirm(`确定删除会话「${c.title}」及其全部历史消息？`, '删除会话', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await deleteConversation(c.id)
    conversations.value = conversations.value.filter((x) => x.id !== c.id)
    if (currentId.value === c.id) {
      currentId.value = null
      messages.value = []
    }
    ElMessage.success('会话已删除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function onSend() {
  const q = question.value.trim()
  if (!q || sending.value) return

  messages.value.push({ role: 'user', text: q })
  const assistant = reactive({ role: 'assistant', text: '', loading: true })
  messages.value.push(assistant)
  question.value = ''
  sending.value = true
  scrollBottom()

  try {
    await askStream(q, topK.value, currentId.value, async (event, data) => {
      if (event === 'meta') {
        if (data.conversation_id && currentId.value !== data.conversation_id) {
          currentId.value = data.conversation_id
          await loadConversations()
        }
      } else if (event === 'delta') {
        assistant.text += data.text || ''
        scrollBottom()
      } else if (event === 'error') {
        assistant.text = (assistant.text ? assistant.text + '\n' : '') + `⚠️ ${data.message || '生成出错'}`
      } else if (event === 'done') {
        assistant.loading = false
        await loadConversations() // 更新会话时间与标题
      }
    })
  } catch (e) {
    assistant.text = assistant.text ? assistant.text : `⚠️ ${e.message}`
    ElMessage.error(e.message)
  } finally {
    assistant.loading = false
    sending.value = false
    scrollBottom()
  }
}

onMounted(async () => {
  await loadConversations()
  if (conversations.value.length > 0) {
    await onSelectConversation(conversations.value[0])
  }
})
</script>

<style scoped>
.chat-page {
  min-height: 100vh;
}
.chat-header {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  gap: 12px;
}
.logo {
  font-size: 16px;
  font-weight: 700;
  color: #409eff;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
  outline: none;
}
.chat-body {
  height: calc(100vh - 60px);
}
.chat-aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}
.aside-top {
  padding: 12px;
  border-bottom: 1px solid #f0f2f5;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.conv-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
}
.conv-item:hover {
  background: #f5f7fa;
}
.conv-item.active {
  background: #ecf5ff;
}
.conv-title {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}
.conv-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #909399;
}
.conv-actions {
  display: none;
}
.conv-item:hover .conv-actions {
  display: inline-flex;
}
.conv-empty {
  text-align: center;
  color: #909399;
  font-size: 12px;
  padding: 24px 0;
}
.chat-main {
  display: flex;
  flex-direction: column;
  padding: 16px 24px;
}
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.empty {
  text-align: center;
  padding-top: 15vh;
  color: #909399;
}
.empty-title {
  font-size: 22px;
  font-weight: 700;
  color: #606266;
  margin-bottom: 12px;
}
.empty-tip {
  font-size: 14px;
}
.msg-row {
  display: flex;
  margin-bottom: 16px;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.assistant {
  justify-content: flex-start;
}
.msg-bubble {
  max-width: 78%;
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.msg-row.user .msg-bubble {
  background: #ecf5ff;
  border-color: #d9ecff;
}
.msg-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.msg-text {
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-text.loading::after {
  content: '▍';
  animation: blink 1s infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}
.input-area {
  margin-top: 12px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 10px 12px;
}
.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
