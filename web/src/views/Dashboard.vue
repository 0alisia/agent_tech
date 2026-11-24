<template>
  <div>
    <div style="margin-bottom:24px">
      <h1 style="font-size:22px;font-weight:700;margin-bottom:6px">无人机实训教学智能体平台</h1>
      <p style="color:var(--text-secondary);font-size:14px">服务教、学、管、评、服 · 实训指导 · RAG问答 · 安全评估</p>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(160px,1fr));margin-bottom:24px">
      <div class="card stat-card" v-for="s in stats" :key="s.label">
        <div class="stat-val">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr))">
      <div class="card" v-for="f in features" :key="f.title" style="cursor:pointer" @click="$router.push(f.route)">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
          <div style="width:36px;height:36px;background:var(--accent-light);border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg :viewBox="f.icon.vb" fill="none" stroke="var(--accent)" stroke-width="2" style="width:18px;height:18px" v-html="f.icon.path"></svg>
          </div>
          <h3 style="font-size:15px;font-weight:600">{{ f.title }}</h3>
        </div>
        <p style="font-size:13px;color:var(--text-secondary);line-height:1.6">{{ f.desc }}</p>
        <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:5px">
          <span class="tag gray" v-for="t in f.tags" :key="t">{{ t }}</span>
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
      docCount: 0,
      postCount: 0,
      features: [
        {
          route: '/drones',
          title: '知识文档库',
          desc: '涵盖调试、操作、维护、安全24篇专业文档，支持全文搜索和分类浏览。',
          tags: ['Pixhawk', 'ArduPilot', 'DJI', 'Betaflight'],
          icon: { vb: '0 0 24 24', path: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>' }
        },
        {
          route: '/training-agent',
          title: '实训智能体',
          desc: '面向学生无人机设计制作实训，提供任务引导、操作规范提醒、安全提示、故障排查和实验报告辅助。',
          tags: ['实验实训', '课程助教', '学情管理', '过程评价'],
          icon: { vb: '0 0 24 24', path: '<path d="M12 2v4"/><path d="M12 18v4"/><path d="m4.93 4.93 2.83 2.83"/><path d="m16.24 16.24 2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="m4.93 19.07 2.83-2.83"/><path d="m16.24 7.76 2.83-2.83"/><circle cx="12" cy="12" r="3"/>' }
        },
        {
          route: '/ask',
          title: '实训问答',
          desc: '基于Chroma向量检索+Qwen大模型，围绕无人机设计制作、调试排故、报告撰写给出分步骤指导。',
          tags: ['Chroma', 'RAG', 'Qwen', '实训导师'],
          icon: { vb: '0 0 24 24', path: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' }
        },
        {
          route: '/weather',
          title: '天气飞行评估',
          desc: '对接和风天气API，通过Tool Call获取实时风速、降水等数据，AI给出飞行建议。',
          tags: ['和风天气', 'Tool Call', '风速', 'GPS'],
          icon: { vb: '0 0 24 24', path: '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9z"/>' }
        },
        {
          route: '/forum',
          title: '飞手论坛',
          desc: '飞手交流社区，发布飞行心得、调试求助、作品展示，互动点赞评论。',
          tags: ['发帖', '评论', '点赞', '社区'],
          icon: { vb: '0 0 24 24', path: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>' }
        },
      ]
    }
  },
  computed: {
    stats() {
      return [
        { value: this.docCount, label: '知识文档' },
        { value: this.postCount, label: '论坛帖子' },
        { value: '5', label: '教学环节' },
        { value: 'Qwen', label: '大模型' },
      ]
    }
  },
  async created() {
    try {
      const [d, f] = await Promise.all([
        request.get('/drones/', { params: { size: 1 } }),
        request.get('/forum/', { params: { size: 1 } }),
      ])
      this.docCount = d.data.total || 0
      this.postCount = f.data.total || 0
    } catch {}
  }
}
</script>
