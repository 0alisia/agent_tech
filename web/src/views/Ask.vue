<template>
  <div>
    <div class="page-header">
      <div>
        <h1>智能问答</h1>
        <p class="sub">面向无人机设计制作实训的结构化问答，支持学生操作指导与教师评价建议</p>
      </div>
    </div>

    <div class="card">
      <div class="ask-toolbar">
        <div>
          <div class="field-label" style="margin-top:0">回答视角</div>
          <div class="mode-switch">
            <button
              v-for="item in roles"
              :key="item.value"
              class="mode-btn"
              :class="{ active: role === item.value }"
              @click="role = item.value"
            >
              {{ item.label }}
            </button>
          </div>
        </div>
        <div>
          <div class="field-label" style="margin-top:0">问题模板</div>
          <div class="suggest-chips">
            <span class="chip" v-for="item in templates" :key="item.title" @click="applyTemplate(item)">
              {{ item.title }}
            </span>
          </div>
        </div>
      </div>

      <div class="status-bar ok" style="margin-top:12px">
        <span>{{ roleHint }}</span>
      </div>

      <label class="field-label">输入问题</label>
      <textarea
        v-model.trim="question"
        placeholder="输入无人机实训相关问题，如：Pixhawk如何校准传感器？"
        style="min-height:150px"
      ></textarea>
      <div class="ask-actions">
        <button class="btn" :disabled="loading || !question" @click="ask">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '生成中...' : '发送问题' }}
        </button>
        <button class="btn ghost" :disabled="loading" @click="fillGuidePrompt">插入实训提问模板</button>
        <span v-if="loading" class="loading-text">正在检索知识库并生成回答...</span>
      </div>
    </div>

    <div v-if="loading || answer" class="card card-gap">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" style="width:17px;height:17px"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span style="font-size:15px;font-weight:600">回答</span>
        <span class="tag gray" style="font-size:11px">Chroma RAG · Qwen</span>
        <span class="tag" style="font-size:11px">{{ role === 'teacher' ? '教师视角' : '学生视角' }}</span>
      </div>
      <div v-if="loading && !answer" class="answer-loading"><span></span><span></span><span></span></div>
      <div v-else class="answer markdown-body" v-html="renderMarkdown(streamingAnswer)"></div>
    </div>

    <div class="grid training-columns card-gap">
      <div class="card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h3 style="font-size:15px;font-weight:600">高频实训问题</h3>
          <span class="muted" style="font-size:12px">点击快速填入</span>
        </div>
        <div class="template-list">
          <button v-for="item in quickQuestions" :key="item" class="template-item" @click="question = item">
            {{ item }}
          </button>
        </div>
      </div>

      <div class="card">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h3 style="font-size:15px;font-weight:600">历史记录</h3>
          <span class="muted" style="font-size:12px">最近30条</span>
        </div>
        <div v-if="!history.length" class="muted" style="text-align:center;padding:20px">暂无历史记录</div>
        <div v-for="item in history" :key="item.id" class="history-item">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap">
            <b style="font-size:14px">{{ item.question }}</b>
            <span class="tag gray" style="font-size:11px">{{ item.context }}</span>
          </div>
          <p class="muted">{{ item.created_at }}</p>
          <p style="color:var(--text-secondary);font-size:13px;margin-top:3px">{{ summary(item.answer) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import request from '../api/request'

export default {
  data() {
    return {
      answer: '',
      history: [],
      loading: false,
      question: '',
      role: 'student',
      roles: [
        { value: 'student', label: '学生版' },
        { value: 'teacher', label: '教师版' },
      ],
      quickQuestions: [
        'DJI Mini 4 Pro首飞前要检查什么？',
        'Pixhawk如何校准传感器？',
        '电池怎么正确存储？',
        '炸机后如何分析日志？',
        'FPV穿越机怎么校准电调？',
        '无人机指南针校准失败怎么办？',
      ],
      templates: [
        {
          title: '任务指导',
          role: 'student',
          content: '我是无人机设计制作实训学生。机型/平台：；当前阶段：；当前任务：；已经完成：；卡住的问题：。请按任务目标、原因分析、操作步骤、安全提醒、实验记录要点五部分回答。',
        },
        {
          title: '故障排查',
          role: 'student',
          content: '我在无人机实训中遇到故障。机型/平台：；现象：；发生条件：；已尝试：。请按现象判断、可能原因、验证方法、处理步骤、安全提醒五部分回答。',
        },
        {
          title: '报告生成',
          role: 'student',
          content: '请根据无人机设计制作实训，生成实验报告提纲。任务名称：；操作过程：；异常现象：；处理结果：。请输出实验目的、操作过程、现象记录、问题分析、改进建议。',
        },
        {
          title: '教师评价',
          role: 'teacher',
          content: '请以教师视角对无人机设计制作实训进行点评。任务名称：；学生表现：；常见错误：；最终结果：。请输出教学观察、共性问题、评分建议、反馈话术。',
        },
      ],
    }
  },
  created() {
    this.loadHistory()
    this.applyRoutePreset()
  },
  watch: {
    '$route.query': {
      handler() {
        this.applyRoutePreset()
      },
      deep: true,
    },
  },
  computed: {
    roleHint() {
      return this.role === 'teacher'
        ? '教师版会更强调教学目标、易错点、评价依据和反馈用语。'
        : '学生版会更强调问题判断、操作步骤、安全提醒和实验记录。'
    },
    streamingAnswer() {
      return this.loading && this.answer ? `${this.answer}\n\n▌` : this.answer
    },
  },
  methods: {
    applyTemplate(item) {
      this.role = item.role
      this.question = item.content
    },
    applyRoutePreset() {
      const { q, role } = this.$route.query
      if (role === 'teacher' || role === 'student') {
        this.role = role
      }
      if (q) {
        this.question = q
      }
    },
    fillGuidePrompt() {
      this.question = '我是无人机设计制作实训学生。机型/平台：；当前阶段：；故障或任务：；已经尝试：。请按结论概览、原因分析、操作步骤、安全提醒、实验报告记录要点五部分详细回答。'
      this.role = 'student'
    },
    buildQuestion() {
      const prefix = this.role === 'teacher'
        ? '请以无人机实训教师助手的身份回答，重点关注教学目标、常见错误、过程评价和反馈建议。'
        : '请以无人机实训学生助教的身份回答，重点关注问题判断、操作步骤、安全提醒和实验报告记录。'
      return `${prefix}\n\n${this.question}`
    },
    async ask() {
      if (!this.question || this.loading) return
      this.loading = true
      this.answer = ''
      try {
        const response = await fetch(this.streamApiUrl(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Token ${localStorage.getItem('token') || ''}`,
          },
          body: JSON.stringify({ question: this.buildQuestion() }),
        })
        if (!response.ok) {
          const errorText = await response.text()
          try {
            const errorData = JSON.parse(errorText)
            this.answer = errorData.message || '请求失败，请稍后重试'
          } catch {
            this.answer = errorText || '请求失败，请稍后重试'
          }
          return
        }
        if (!response.body) {
          this.answer = '当前浏览器不支持流式输出'
          return
        }
        const reader = response.body.getReader()
        const decoder = new TextDecoder('utf-8')
        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          this.answer += decoder.decode(value, { stream: true })
        }
        this.answer += decoder.decode()
        await this.loadHistory()
      } catch (e) {
        this.answer = e.response?.data?.message || '请求失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    async loadHistory() {
      const res = await request.get('/rag/history/')
      this.history = res.data || []
    },
    streamApiUrl() {
      if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
        return 'http://127.0.0.1:8000/api/rag/ask-stream/'
      }
      return '/api/rag/ask-stream/'
    },
    escapeHtml(v) { return String(v || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;') },
    formatInline(v) { return v.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\*([^*]+)\*/g, '<em>$1</em>') },
    renderMarkdown(value) {
      const lines = this.escapeHtml(value).split('\n')
      const html = []
      let inCode = false
      let inList = false
      let para = []
      const flushPara = () => { if (para.length) { html.push(`<p>${this.formatInline(para.join(' '))}</p>`); para = [] } }
      const closeList = () => { if (inList) { html.push('</ul>'); inList = false } }
      lines.forEach(line => {
        if (/^```/.test(line.trim())) { flushPara(); closeList(); html.push(inCode ? '</code></pre>' : '<pre><code>'); inCode = !inCode; return }
        if (inCode) { html.push(line + '\n'); return }
        if (!line.trim()) { flushPara(); closeList(); return }
        const h = line.match(/^(#{1,4})\s+(.+)$/)
        if (h) { flushPara(); closeList(); html.push(`<h${h[1].length}>${this.formatInline(h[2])}</h${h[1].length}>`); return }
        const li = line.match(/^[-*+]\s+(.+)$/)
        if (li) { flushPara(); if (!inList) { html.push('<ul>'); inList = true } html.push(`<li>${this.formatInline(li[1])}</li>`); return }
        para.push(line.trim())
      })
      flushPara()
      closeList()
      if (inCode) html.push('</code></pre>')
      return html.join('')
    },
    summary(v) { const t = String(v || '').replace(/[#*_`>-]/g, ''); return t.length > 100 ? t.slice(0, 100) + '...' : t },
  },
}
</script>
