<template>
  <div>
    <div class="page-header">
      <div>
        <h1>无人机实训智能体</h1>
        <p class="sub">围绕任务执行、安全规范、故障排查、报告生成和教师评价构建实训闭环</p>
      </div>
      <div class="row" style="flex-wrap:wrap;justify-content:flex-end">
        <button class="btn ghost" @click="openAsk(quickPrompt)">快速提问</button>
        <button class="btn" @click="openAsk(reportPrompt)">生成报告提纲</button>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin-bottom:16px">
      <div v-for="item in summary" :key="item.label" class="card stat-card">
        <div class="stat-val">{{ item.value }}</div>
        <div class="stat-label">{{ item.label }}</div>
      </div>
    </div>

    <div class="grid training-workbench">
      <div class="card training-surface">
        <div class="panel-title">
          <span class="tag">任务卡</span>
          <h3>实训流程引导</h3>
        </div>
        <p class="muted">按实训阶段组织任务，让学生知道“现在做什么、怎么做、做到什么程度算完成”。</p>
        <div class="task-stack">
          <button
            v-for="task in tasks"
            :key="task.id"
            class="task-card"
            :class="{ active: activeTask.id === task.id }"
            @click="activeTask = task"
          >
            <div>
              <div class="task-title">{{ task.title }}</div>
              <div class="task-meta">{{ task.stage }}</div>
            </div>
            <span class="tag gray">{{ task.goal }}</span>
          </button>
        </div>
      </div>

      <div class="card training-surface">
        <div class="panel-title">
          <span class="tag success">当前任务</span>
          <h3>{{ activeTask.title }}</h3>
        </div>
        <p>{{ activeTask.desc }}</p>
        <div class="divider"></div>
        <label class="field-label">操作步骤</label>
        <ol class="training-list">
          <li v-for="step in activeTask.steps" :key="step">{{ step }}</li>
        </ol>
        <label class="field-label">验收标准</label>
        <div class="pill-row">
          <span v-for="item in activeTask.acceptance" :key="item" class="tag gray">{{ item }}</span>
        </div>
        <div class="training-actions">
          <button class="btn" @click="openAsk(taskPrompt(activeTask))">按此任务提问</button>
          <button class="btn ghost" @click="openAsk(reportPromptForTask(activeTask), 'teacher')">生成教师评价建议</button>
        </div>
      </div>
    </div>

    <div class="grid training-columns card-gap">
      <div class="card training-surface">
        <div class="panel-title">
          <span class="tag warn">安全</span>
          <h3>试飞前检查清单</h3>
        </div>
        <div class="checklist">
          <label v-for="item in safetyChecks" :key="item.label" class="check-item">
            <input type="checkbox" v-model="item.checked">
            <span>{{ item.label }}</span>
          </label>
        </div>
        <div class="status-bar" :class="safetyStatus.class">
          <span>{{ safetyStatus.text }}</span>
        </div>
        <button class="btn ghost" @click="openAsk(safetyPrompt)">生成安全提示话术</button>
      </div>

      <div class="card training-surface">
        <div class="panel-title">
          <span class="tag">排故</span>
          <h3>故障排查树</h3>
        </div>
        <div class="fault-tabs">
          <button
            v-for="item in faults"
            :key="item.id"
            class="chip"
            :class="{ selected: activeFault.id === item.id }"
            @click="activeFault = item"
          >
            {{ item.title }}
          </button>
        </div>
        <p class="muted">{{ activeFault.summary }}</p>
        <ol class="training-list compact">
          <li v-for="step in activeFault.steps" :key="step">{{ step }}</li>
        </ol>
        <button class="btn" @click="openAsk(faultPrompt(activeFault))">按此故障排查</button>
      </div>
    </div>

    <div class="grid training-columns card-gap">
      <div class="card training-surface">
        <div class="panel-title">
          <span class="tag gray">报告</span>
          <h3>实验报告辅助</h3>
        </div>
        <div class="report-grid">
          <div v-for="section in reportSections" :key="section.title" class="report-card">
            <b>{{ section.title }}</b>
            <p>{{ section.tip }}</p>
          </div>
        </div>
        <div class="training-actions">
          <button class="btn" @click="openAsk(reportPrompt)">生成学生报告提纲</button>
          <button class="btn ghost" @click="openAsk(rubricPrompt, 'teacher')">生成评分 rubric</button>
        </div>
      </div>

      <div class="card training-surface">
        <div class="panel-title">
          <span class="tag success">教师</span>
          <h3>教师观察与评价建议</h3>
        </div>
        <div class="insight-list">
          <div v-for="item in teacherInsights" :key="item.title" class="insight-item">
            <b>{{ item.title }}</b>
            <p>{{ item.desc }}</p>
          </div>
        </div>
        <button class="btn ghost" @click="openAsk(teacherSummaryPrompt, 'teacher')">生成课堂反馈摘要</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    const tasks = [
      {
        id: 'assembly',
        title: '机架与动力系统装配',
        stage: '第一阶段',
        goal: '装配完成',
        desc: '完成机架、电机、电调、桨叶等基础部件安装，确保结构牢固、方向正确、供电安全。',
        steps: ['核对机架、电机、电调、螺旋桨型号与安装位置', '按顺序固定机臂、电机和桨座，检查螺丝松紧', '确认电机转向和桨叶正反方向', '整理线束并做好绝缘与固定'],
        acceptance: ['结构牢固', '转向正确', '线束整洁'],
      },
      {
        id: 'wiring',
        title: '飞控接线与固件配置',
        stage: '第二阶段',
        goal: '接线正确',
        desc: '完成飞控、电调、接收机、GPS、遥测等模块接线，并进行固件刷写和端口配置。',
        steps: ['对照接线图连接飞控、电调、接收机和供电模块', '检查 5V/电池供电路径是否正确', '刷写对应固件并校验机型参数', '完成端口、协议和基础 failsafe 设置'],
        acceptance: ['通电正常', '端口识别正常', '基础参数可读'],
      },
      {
        id: 'calibration',
        title: '传感器校准与参数调试',
        stage: '第三阶段',
        goal: '调试可飞',
        desc: '完成加速度计、罗盘、遥控器、动力系统校准，并根据机型进行初步参数调试。',
        steps: ['校准加速度计、罗盘、遥控器和电调', '检查 GPS、姿态、供电、电压告警状态', '设置基础飞行模式、返航和低电保护', '根据试机情况微调 PID 或滤波参数'],
        acceptance: ['校准通过', '模式切换正常', '告警项清零'],
      },
      {
        id: 'flight',
        title: '首飞前检查与试飞',
        stage: '第四阶段',
        goal: '安全首飞',
        desc: '按照规范完成首飞前检查，在可控环境下试飞并记录姿态、振动、遥测等信息。',
        steps: ['完成螺旋桨、供电、机体紧固和遥控链路检查', '评估天气、场地与周边安全条件', '执行低空悬停和姿态测试', '记录异常现象并整理试飞日志'],
        acceptance: ['可稳定悬停', '链路稳定', '日志已记录'],
      },
      {
        id: 'review',
        title: '故障复盘与报告整理',
        stage: '第五阶段',
        goal: '形成闭环',
        desc: '结合试飞数据、故障现象和处理过程，形成可提交的实验报告和改进建议。',
        steps: ['整理现象、时间、参数和处理动作', '定位故障原因并总结验证过程', '形成改进方案与下次调试计划', '提交实验报告并进行小组复盘'],
        acceptance: ['问题闭环', '报告完整', '改进明确'],
      },
    ]

    return {
      tasks,
      activeTask: tasks[0],
      summary: [
        { value: '5', label: '实训阶段' },
        { value: '12+', label: '安全检查项' },
        { value: '6', label: '高频故障模板' },
        { value: '教 学 评', label: '覆盖环节' },
      ],
      safetyChecks: [
        { label: '电池电压正常，电量满足试飞要求', checked: true },
        { label: '螺旋桨方向与紧固状态已确认', checked: true },
        { label: '遥控器、接收机、图传链路正常', checked: false },
        { label: 'GPS、罗盘、姿态与 failsafe 状态正常', checked: true },
        { label: '试飞场地安全，天气满足飞行条件', checked: false },
      ],
      faults: [
        {
          id: 'unlock',
          title: '无法解锁',
          summary: '优先检查飞控自检、模式开关、GPS / 罗盘告警和油门位置。',
          steps: ['查看地面站或遥测中的 pre-arm 提示', '确认遥控器通道映射和油门最低值', '检查飞行模式、GPS 与罗盘状态', '逐项解除告警后再次尝试解锁'],
        },
        {
          id: 'motor',
          title: '电机不转',
          summary: '从供电、电调校准、飞控输出和安全锁定四个方向排查。',
          steps: ['检查电池、电调和电源模块供电', '确认电调已校准并识别油门信号', '查看飞控输出通道是否正常', '排查安全锁定与电机测试权限'],
        },
        {
          id: 'compass',
          title: '指南针异常',
          summary: '重点排查磁干扰、校准环境和 GPS / 罗盘安装位置。',
          steps: ['远离强磁环境重新校准罗盘', '检查 GPS / 罗盘模块安装方向', '确认附近无大电流线束干扰', '核对固件中的罗盘优先级和朝向设置'],
        },
        {
          id: 'hover',
          title: '悬停不稳',
          summary: '通常与校准误差、重心偏移、振动和参数设置有关。',
          steps: ['复查加速度计和遥控器中位校准', '确认机体重心与桨叶状态', '查看飞行日志中的振动与姿态数据', '根据机型适度调整 PID 参数'],
        },
      ],
      activeFault: null,
      reportSections: [
        { title: '实验目的', tip: '说明本次实训要完成的装配、调试或飞行目标。' },
        { title: '操作过程', tip: '按步骤写清设备、参数、操作顺序和关键设置。' },
        { title: '现象记录', tip: '记录异常现象、发生条件、时间和日志信息。' },
        { title: '问题分析', tip: '说明原因判断依据、验证过程和处理结果。' },
        { title: '改进建议', tip: '总结下一轮调试、结构优化或安全改进方向。' },
      ],
      teacherInsights: [
        { title: '课堂组织', desc: '建议教师按“讲解 10 分钟 + 操作 25 分钟 + 复盘 10 分钟”的节奏组织本节实训。' },
        { title: '易错点提醒', desc: '学生最常见的错误集中在线序接反、螺旋桨方向错误、遥控器通道映射不一致。' },
        { title: '过程评价', desc: '可从安全规范、日志记录、故障定位依据、改进方案四个维度进行评价。' },
      ],
    }
  },
  created() {
    this.activeFault = this.faults[0]
  },
  computed: {
    safetyStatus() {
      const checked = this.safetyChecks.filter(item => item.checked).length
      if (checked === this.safetyChecks.length) {
        return { class: 'ok', text: '安全检查已完成，可以进入试飞评估或实训问答。' }
      }
      if (checked >= this.safetyChecks.length - 1) {
        return { class: 'warn', text: '还有少量检查项未完成，建议补齐后再试飞。' }
      }
      return { class: 'err', text: '当前仍有关键安全项未确认，不建议直接试飞。' }
    },
    quickPrompt() {
      return '我是无人机设计制作实训学生。机型/平台：；当前阶段：；遇到的问题：；已经尝试：。请按结论、原因分析、操作步骤、安全提醒四部分详细回答。'
    },
    safetyPrompt() {
      return '请针对无人机首飞前检查，生成一段面向学生的安全提示，包含电池、螺旋桨、链路、场地和天气五项提醒。'
    },
    reportPrompt() {
      return '请根据无人机设计制作实训场景，生成一份实验报告提纲，至少包含实验目的、操作过程、现象记录、问题分析和改进建议。'
    },
    rubricPrompt() {
      return '请为无人机设计制作实训生成教师评分 rubric，维度包括操作规范、安全意识、故障分析、实验报告和团队协作。'
    },
    teacherSummaryPrompt() {
      return '请以教师视角生成一段课堂反馈摘要，内容包括学生完成进度、共性问题、风险提醒和下次课建议。'
    },
  },
  methods: {
    openAsk(question, role = 'student') {
      this.$router.push({ path: '/ask', query: { q: question, role } })
    },
    taskPrompt(task) {
      return `我是无人机设计制作实训学生，当前任务是“${task.title}”。机型/平台：；当前现象或卡点：；已完成步骤：${task.steps.join('、')}。请按任务目标、原因分析、下一步操作、安全提醒、实验记录要点五部分指导我。`
    },
    reportPromptForTask(task) {
      return `请从教师视角为“${task.title}”这一实训任务生成评价建议，包含观察点、常见错误、评分依据和反馈用语。`
    },
    faultPrompt(fault) {
      return `我在无人机实训中遇到“${fault.title}”问题。请按现象判断、可能原因、验证方法、处理步骤、安全提醒五部分详细排查。`
    },
  },
}
</script>
