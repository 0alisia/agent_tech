<template>
  <div class="profile-page">
    <div class="card">
      <h1 class="title">个人信息</h1>
      <p class="sub">管理账户信息和密码</p>
      <label class="field-label">昵称</label>
      <input class="input" v-model="form.nickname" placeholder="昵称">
      <label class="field-label">邮箱</label>
      <input class="input" v-model="form.email" placeholder="邮箱">
      <label class="field-label">手机号</label>
      <input class="input" v-model="form.phone" placeholder="手机号">
      <label class="field-label">个人简介</label>
      <textarea v-model="form.bio" placeholder="介绍一下自己..." style="min-height:80px"></textarea>
      <label class="field-label">新密码（不修改请留空）</label>
      <input class="input" v-model="form.password" type="password" placeholder="新密码，至少6位">
      <button class="btn" @click="save">保存修改</button>
      <p v-if="msg" style="margin-top:10px;color:var(--success);font-size:13px">{{ msg }}</p>
    </div>

    <div class="card card-gap">
      <h2 style="font-size:15px;font-weight:700;margin-bottom:6px">知识库管理</h2>
      <p class="sub">构建Chroma向量索引，用于语义检索和智能问答。</p>
      <div class="index-panel">
        <button class="btn" :disabled="indexing" @click="buildIndex">
          <span v-if="indexing" class="spinner"></span>
          {{ indexing ? '构建中...' : '构建向量索引' }}
        </button>
        <div v-if="indexMsg" :class="['status-bar', indexOk ? 'ok' : 'err']" style="margin:0">
          {{ indexMsg }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import request from '../api/request'

export default {
  data() {
    return { form: {}, msg: '', indexing: false, indexMsg: '', indexOk: false }
  },
  async created() {
    const res = await request.get('/auth/profile/')
    this.form = res.data; this.form.password = ''
  },
  methods: {
    async save() {
      this.msg = ''
      const payload = { ...this.form }
      if (!payload.password) delete payload.password
      await request.put('/auth/profile/', payload)
      this.msg = '保存成功'; this.form.password = ''
    },
    async buildIndex() {
      this.indexing = true; this.indexMsg = ''
      try {
        const res = await request.post('/rag/build-index/')
        this.indexOk = res.code === 0; this.indexMsg = res.message
      } catch (e) {
        this.indexOk = false; this.indexMsg = e.response?.data?.message || '构建失败'
      } finally { this.indexing = false }
    }
  }
}
</script>
