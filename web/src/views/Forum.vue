<template>
  <div>
    <div class="page-header">
      <div>
        <h1>飞手论坛</h1>
        <p class="sub">飞行心得 · 调试求助 · 作品展示 · 技术问答</p>
      </div>
      <button class="btn" @click="openCreate">发布帖子</button>
    </div>

    <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
      <button :class="['btn','sm', !activeCat ? '' : 'ghost']" @click="activeCat='';load()">全部</button>
      <button
        v-for="c in categories" :key="c.value"
        :class="['btn','sm', activeCat===c.value ? '' : 'ghost']"
        @click="activeCat=c.value;load()">
        {{ c.label }}
      </button>
    </div>

    <div class="forum-grid">
      <div v-for="post in posts" :key="post.id" class="card post-item" @click="openDetail(post.id)">
        <div style="display:flex;align-items:start;justify-content:space-between;gap:12px">
          <div style="flex:1;min-width:0">
            <div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap">
              <span class="tag">{{ post.category_label }}</span>
            </div>
            <div class="post-title">{{ post.title }}</div>
            <div class="post-snippet">{{ post.content }}</div>
          </div>
        </div>
        <div class="post-meta" style="margin-top:8px">
          <span>{{ post.author_name }}</span>
          <span>{{ post.created_at }}</span>
          <span>{{ post.view_count }} 浏览</span>
          <span>{{ post.comment_count }} 评论</span>
          <span style="color:var(--danger)">{{ post.like_count }} 点赞</span>
        </div>
      </div>
    </div>

    <div v-if="!posts.length && !loading" class="card" style="text-align:center;padding:40px;color:var(--muted)">
      暂无帖子，点击"发布帖子"成为第一个发帖的飞手
    </div>

    <div v-if="showDetail" class="modal-backdrop" @click.self="showDetail=false">
      <div class="modal" style="width:680px">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:14px">
          <div>
            <div style="margin-bottom:6px"><span class="tag">{{ detail.category_label }}</span></div>
            <h2 style="margin:0;font-size:18px">{{ detail.title }}</h2>
            <div style="color:var(--muted);font-size:12px;margin-top:5px">
              {{ detail.author_name }} · {{ detail.created_at }} · {{ detail.view_count }} 浏览
            </div>
          </div>
          <button class="btn ghost sm" @click="showDetail=false">关闭</button>
        </div>
        <div style="white-space:pre-wrap;line-height:1.75;font-size:14px;color:var(--text);background:var(--surface2);padding:16px;border-radius:10px;border:1px solid var(--border);max-height:280px;overflow-y:auto">{{ detail.content }}</div>
        <div style="display:flex;align-items:center;gap:12px;margin-top:12px">
          <button :class="['like-btn', detail.liked ? 'liked' : '']" @click="toggleLike">
            <svg viewBox="0 0 24 24" :fill="detail.liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            {{ detail.like_count }} 点赞
          </button>
          <span style="color:var(--muted);font-size:13px">{{ detail.comment_count }} 条评论</span>
          <span v-if="detail.author_id === myId" style="margin-left:auto">
            <button class="btn danger sm" @click="deletePost">删除帖子</button>
          </span>
        </div>
        <div class="divider"></div>
        <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">评论 ({{ comments.length }})</h3>
        <div v-if="!comments.length" class="muted" style="margin-bottom:12px">暂无评论，快来发表第一条评论</div>
        <div v-for="c in comments" :key="c.id" class="comment-item">
          <div>
            <span class="comment-author">{{ c.author_name }}</span>
            <span class="comment-time">{{ c.created_at }}</span>
          </div>
          <div class="comment-content">{{ c.content }}</div>
        </div>
        <div style="margin-top:14px">
          <label class="field-label">发表评论</label>
          <textarea v-model="commentText" placeholder="写下你的评论..." style="min-height:70px"></textarea>
          <button class="btn sm" @click="submitComment" :disabled="!commentText.trim()">提交评论</button>
        </div>
      </div>
    </div>

    <div v-if="showForm" class="modal-backdrop" @click.self="showForm=false">
      <div class="modal">
        <h2>发布帖子</h2>
        <label class="field-label">标题</label>
        <input class="input" v-model="form.title" placeholder="帖子标题">
        <label class="field-label">分类</label>
        <select class="input" v-model="form.category">
          <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
        <label class="field-label">内容</label>
        <textarea v-model="form.content" placeholder="分享你的飞行经验、问题或作品..." style="min-height:180px"></textarea>
        <div class="modal-footer">
          <button class="btn ghost" @click="showForm=false">取消</button>
          <button class="btn" @click="createPost">发布</button>
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
      posts: [],
      total: 0,
      categories: [],
      activeCat: '',
      loading: false,
      showDetail: false,
      showForm: false,
      detail: {},
      comments: [],
      commentText: '',
      form: { title: '', category: 'qa', content: '' },
      myId: null
    }
  },
  async created() {
    const [cats, profile] = await Promise.all([
      request.get('/forum/categories/'),
      request.get('/auth/profile/'),
    ])
    this.categories = cats.data || []
    this.myId = profile.data.id
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await request.get('/forum/', { params: { category: this.activeCat, size: 30 } })
        this.posts = res.data.items
        this.total = res.data.total
      } finally {
        this.loading = false
      }
    },
    async openDetail(id) {
      const res = await request.get(`/forum/${id}/`)
      this.detail = res.data.post
      this.comments = res.data.comments
      this.commentText = ''
      this.showDetail = true
    },
    openCreate() {
      this.form = { title: '', category: 'qa', content: '' }
      this.showForm = true
    },
    async createPost() {
      if (!this.form.title || !this.form.content) return alert('标题和内容不能为空')
      await request.post('/forum/create/', this.form)
      this.showForm = false
      this.load()
    },
    async submitComment() {
      if (!this.commentText.trim()) return
      const res = await request.post(`/forum/${this.detail.id}/comment/`, { content: this.commentText })
      this.comments.push(res.data)
      this.detail.comment_count++
      this.commentText = ''
    },
    async toggleLike() {
      const res = await request.post(`/forum/${this.detail.id}/like/`)
      this.detail.liked = res.data.liked
      this.detail.like_count = res.data.like_count
      const post = this.posts.find(p => p.id === this.detail.id)
      if (post) { post.liked = res.data.liked; post.like_count = res.data.like_count }
    },
    async deletePost() {
      if (!confirm('确认删除此帖子？')) return
      await request.delete(`/forum/${this.detail.id}/edit/`)
      this.showDetail = false
      this.load()
    }
  }
}
</script>
