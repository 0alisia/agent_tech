<template>
  <div>
    <div class="page-header">
      <div>
        <h1>知识文档库</h1>
        <p class="sub">共 {{ total }} 篇专业文档，支持全文搜索和分类浏览</p>
      </div>
      <button class="btn" @click="openCreate">新增文档</button>
    </div>

    <div class="card" style="margin-bottom:16px">
      <div class="row search-row">
        <input class="input search-input" style="flex:1;margin:0" v-model="keyword" placeholder="搜索标题、机型、内容..." @keyup.enter="load">
        <select class="input" style="width:150px;margin:0" v-model="category" @change="load">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
        <button class="btn" @click="load">搜索</button>
      </div>
    </div>

    <div class="grid docs-grid">
      <div v-for="doc in items" :key="doc.id" class="card doc-card" @click="openDetail(doc)">
        <div class="meta">
          <span class="tag">{{ getCategoryLabel(doc.category) }}</span>
          <span class="tag warn" v-if="doc.model_name">{{ doc.model_name }}</span>
        </div>
        <h3>{{ doc.title }}</h3>
        <p class="snippet">{{ doc.content }}</p>
        <div style="display:flex;gap:5px;margin-top:10px;flex-wrap:wrap">
          <span v-for="t in (doc.tags||'').split(',').filter(x=>x.trim())" :key="t" class="tag gray" style="font-size:11px">{{ t.trim() }}</span>
        </div>
      </div>
    </div>

    <div v-if="!items.length && !loading" class="card" style="text-align:center;padding:40px;color:var(--muted)">
      暂无文档
    </div>

    <div v-if="showDetail" class="modal-backdrop" @click.self="showDetail=false">
      <div class="modal" style="width:660px">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:14px">
          <div>
            <div style="margin-bottom:6px">
              <span class="tag">{{ getCategoryLabel(detail.category) }}</span>
              <span class="tag warn" v-if="detail.model_name">{{ detail.model_name }}</span>
            </div>
            <h2 style="margin:0;font-size:17px">{{ detail.title }}</h2>
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn ghost sm" @click="openEdit(detail)">编辑</button>
            <button class="btn danger sm" @click="deleteDoc(detail.id)">删除</button>
          </div>
        </div>
        <pre style="white-space:pre-wrap;font-size:13px;line-height:1.75;color:var(--text);background:var(--surface2);padding:16px;border-radius:10px;border:1px solid var(--border);max-height:55vh;overflow-y:auto">{{ detail.content }}</pre>
        <div class="modal-footer">
          <button class="btn ghost" @click="showDetail=false">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-backdrop" @click.self="showForm=false">
      <div class="modal">
        <h2>{{ editMode ? '编辑文档' : '新增文档' }}</h2>
        <label class="field-label">标题</label>
        <input class="input" v-model="form.title" placeholder="文档标题">
        <label class="field-label">适用机型</label>
        <input class="input" v-model="form.model_name" placeholder="如：DJI Mini 4 Pro / 通用">
        <label class="field-label">分类</label>
        <select class="input" v-model="form.category">
          <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
        <label class="field-label">标签（逗号分隔）</label>
        <input class="input" v-model="form.tags" placeholder="调试,PID,Pixhawk">
        <label class="field-label">内容</label>
        <textarea v-model="form.content" placeholder="文档内容..." style="min-height:200px"></textarea>
        <div class="modal-footer">
          <button class="btn ghost" @click="showForm=false">取消</button>
          <button class="btn" @click="saveDoc">{{ editMode ? '保存修改' : '创建文档' }}</button>
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
      items: [], total: 0, keyword: '', category: '',
      categories: [], loading: false,
      showDetail: false, showForm: false, editMode: false,
      detail: {}, form: { title: '', model_name: '', category: 'faq', tags: '', content: '' }
    }
  },
  async created() {
    const res = await request.get('/drones/categories/')
    this.categories = res.data || []
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await request.get('/drones/', { params: { keyword: this.keyword, category: this.category, size: 24 } })
        this.items = res.data.items; this.total = res.data.total
      } finally { this.loading = false }
    },
    getCategoryLabel(val) { const c = this.categories.find(x => x.value === val); return c ? c.label : val },
    openDetail(doc) { this.detail = doc; this.showDetail = true },
    openCreate() { this.editMode = false; this.form = { title: '', model_name: '', category: 'faq', tags: '', content: '' }; this.showForm = true },
    openEdit(doc) { this.editMode = true; this.form = { ...doc }; this.showDetail = false; this.showForm = true },
    async saveDoc() {
      if (!this.form.title) return alert('标题不能为空')
      if (this.editMode) await request.put(`/drones/${this.form.id}/edit/`, this.form)
      else await request.post('/drones/create/', this.form)
      this.showForm = false; this.load()
    },
    async deleteDoc(id) {
      if (!confirm('确认删除此文档？')) return
      await request.delete(`/drones/${id}/edit/`)
      this.showDetail = false; this.load()
    }
  }
}
</script>
