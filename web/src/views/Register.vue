<template>
  <div class="card auth">
    <div class="logo-mark">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm8 8a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM4 10a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm8 8a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm-2-8h4v4h-4z"/></svg>
    </div>
    <h1>创建账号</h1>
    <p class="sub">加入无人机知识库社区</p>
    <label class="field-label">用户名（至少3位）</label>
    <input class="input" v-model="form.username" placeholder="用户名">
    <label class="field-label">昵称</label>
    <input class="input" v-model="form.nickname" placeholder="昵称">
    <label class="field-label">邮箱（选填）</label>
    <input class="input" v-model="form.email" placeholder="邮箱">
    <label class="field-label">密码（至少6位）</label>
    <input class="input" v-model="form.password" type="password" placeholder="密码">
    <p v-if="error" style="color:var(--danger);font-size:13px;margin:-6px 0 10px">{{ error }}</p>
    <div class="form-actions" style="margin-top:4px">
      <button class="btn" style="flex:1" @click="register">注册</button>
      <button class="btn ghost" style="flex:1" @click="$router.push('/login')">返回登录</button>
    </div>
  </div>
</template>

<script>
import request from '../api/request'

export default {
  data() {
    return {
      form: { username: '', nickname: '', email: '', password: '' },
      error: ''
    }
  },
  methods: {
    async register() {
      this.error = ''
      try {
        await request.post('/auth/register/', this.form)
        alert('注册成功')
        this.$router.push('/login')
      } catch (e) {
        this.error = e.response?.data?.message || '注册失败，请检查输入'
      }
    }
  }
}
</script>
