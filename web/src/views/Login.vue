<template>
  <div class="card auth">
    <div class="logo-mark">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm8 8a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM4 10a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm8 8a2 2 0 1 1 0 4 2 2 0 0 1 0-4zm-2-8h4v4h-4z"/></svg>
    </div>
    <h1>无人机知识库</h1>
    <p class="sub">智能问答 · 飞行评估 · 飞手论坛</p>
    <label class="field-label">用户名</label>
    <input class="input" v-model="form.username" placeholder="请输入用户名" @keyup.enter="login">
    <label class="field-label">密码</label>
    <input class="input" v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="login">
    <p v-if="error" style="color:var(--danger);font-size:13px;margin:-6px 0 10px">{{ error }}</p>
    <div class="form-actions" style="margin-top:4px">
      <button class="btn" style="flex:1" @click="login">登录</button>
      <button class="btn ghost" style="flex:1" @click="$router.push('/register')">注册账号</button>
    </div>
    <p class="muted" style="margin-top:16px;text-align:center">测试账号：demo / demo123456</p>
  </div>
</template>

<script>
import request from '../api/request'

export default {
  data() {
    return {
      form: { username: 'demo', password: 'demo123456' },
      error: ''
    }
  },
  methods: {
    async login() {
      this.error = ''
      try {
        const res = await request.post('/auth/login/', this.form)
        localStorage.setItem('token', res.data.token)
        this.$router.push('/dashboard')
      } catch (e) {
        if (!e.response) {
          this.error = '后端服务未启动，请先运行 Django 服务'
          return
        }
        if (e.response.status === 400) {
          this.error = e.response.data?.message || '用户名或密码错误'
          return
        }
        this.error = e.response.data?.message || '登录服务异常，请检查后端控制台'
      }
    }
  }
}
</script>
