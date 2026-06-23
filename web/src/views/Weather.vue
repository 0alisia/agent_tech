<template>
  <div>
    <div class="page-header">
      <div>
        <h1>天气飞行评估</h1>
        <p class="sub">实时获取天气数据，AI综合判断当前是否适合飞行</p>
      </div>
    </div>

    <div class="card">
      <div class="suggest-chips">
        <span class="chip" v-for="s in suggestions" :key="s" @click="question=s">{{ s }}</span>
      </div>
      <label class="field-label">输入问题</label>
      <textarea v-model.trim="question" placeholder="例如：今天上海适合飞DJI Mini 4 Pro吗？明天下午浑南区风速多大？"></textarea>
      <div class="ask-actions">
        <button class="btn" :disabled="loading || !question" @click="ask">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '查询中...' : '查询天气并评估' }}
        </button>
        <span v-if="loading" class="loading-text">正在调用天气API并分析...</span>
      </div>
    </div>

    <div v-if="loading || answer" class="card card-gap">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" style="width:18px;height:18px"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z"/></svg>
        <span style="font-size:15px;font-weight:600">飞行气象评估结果</span>
        <span class="tag gray" style="font-size:11px">Tool Call · 和风天气</span>
      </div>
      <div v-if="loading" class="answer-loading"><span></span><span></span><span></span></div>
      <div v-else class="answer markdown-body" v-html="renderMarkdown(answer)"></div>
    </div>
  </div>
</template>

<script>
import request from '../api/request'

export default {
  data() {
    return {
      question: '',
      answer: '',
      loading: false,
      suggestions: [
        '今天北京适合飞无人机吗？',
        '上海明天风速多大，能飞穿越机吗？',
        '深圳今天下午的天气如何？',
        '成都这周末适合航拍吗？',
        '浑南区今天的GPS信号会受磁场干扰吗？',
      ]
    }
  },
  methods: {
    async ask() {
      if (!this.question || this.loading) return
      this.loading = true
      this.answer = ''
      try {
        const res = await request.post('/rag/weather/', { question: this.question })
        this.answer = res.data.answer || ''
      } catch (e) {
        this.answer = e.response?.data?.message || '查询失败，请检查和风天气API Key是否已配置'
      } finally {
        this.loading = false
      }
    },
    escapeHtml(v) {
      return String(v||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')
    },
    formatInline(v) {
      return v.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>')
    },
    renderMarkdown(value) {
      const lines = this.escapeHtml(value).split('\n')
      const html = []
      let inCode = false, inList = false, para = []
      const flushPara = () => { if(para.length){html.push(`<p>${this.formatInline(para.join(' '))}</p>`);para=[]} }
      const closeList = () => { if(inList){html.push('</ul>');inList=false} }
      lines.forEach(line => {
        if(/^```/.test(line.trim())){flushPara();closeList();html.push(inCode?'</code></pre>':'<pre><code>');inCode=!inCode;return}
        if(inCode){html.push(line+'\n');return}
        if(!line.trim()){flushPara();closeList();return}
        const h=line.match(/^(#{1,4})\s+(.+)$/)
        if(h){flushPara();closeList();html.push(`<h${h[1].length}>${this.formatInline(h[2])}</h${h[1].length}>`);return}
        const li=line.match(/^[-*+]\s+(.+)$/)
        if(li){flushPara();if(!inList){html.push('<ul>');inList=true}html.push(`<li>${this.formatInline(li[1])}</li>`);return}
        para.push(line.trim())
      })
      flushPara();closeList()
      if(inCode)html.push('</code></pre>')
      return html.join('')
    }
  }
}
</script>
