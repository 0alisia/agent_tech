# 无人机实训教学智能体平台

面向学生无人机设计制作实训的智能体平台，围绕教师赛道中“教、学、管、评、服”的教学场景，提供知识库检索、实训问答、天气飞行评估、实训任务指导、故障排查和飞手社区等功能。

## 项目定位

本项目在无人机知识库平台基础上，扩展为面向实训教学的智能体系统。平台重点服务“实验实训类智能体”方向，同时融合课程助教、智能学伴、学情管理和过程评价能力，帮助学生完成无人机设计、装配、调试、试飞和复盘全过程。

适用场景包括：

- 无人机设计制作实训课程
- 飞控调试与参数配置教学
- 首飞前安全检查与天气评估
- 实验报告辅助撰写
- 教师课堂答疑、过程评价和教学反馈

## 功能模块

### 1. 实训智能体

提供面向实训流程的工作台，包括：

- 实训任务卡：机架装配、飞控接线、传感器校准、首飞检查、故障复盘
- 安全检查清单：电池、螺旋桨、遥控链路、GPS、天气与场地检查
- 故障排查树：无法解锁、电机不转、指南针异常、悬停不稳等高频问题
- 实验报告辅助：生成实验目的、操作过程、现象记录、问题分析和改进建议
- 教师评价建议：生成观察点、常见错误、评分依据和课堂反馈

### 2. 智能问答

基于 Chroma 向量检索和 Qwen 大模型，对无人机实训问题进行结构化回答。回答会尽量包含：

- 结论概览
- 原因分析
- 操作步骤
- 安全提醒
- 实验报告记录要点

问答页面支持“学生版”和“教师版”两种视角。

### 3. 天气飞行评估

调用和风天气 API 获取实时天气或未来天气数据，再结合大模型生成无人机飞行建议。评估依据包括：

- 风速与风力
- 能见度
- 降水和雷暴风险
- 湿度与设备防潮
- 实训飞行安全建议

### 4. 知识文档库

用于维护无人机相关文档，支持按分类、机型、标签和关键词检索。文档内容会用于 RAG 问答索引。

### 5. 飞手论坛

提供实训经验交流、故障求助、作品展示和评论点赞等社区功能。

## 技术栈

前端：

- Vue 2
- Vue Router
- Axios
- Vue CLI

后端：

- Django 4.2
- SQLite
- ChromaDB
- DashScope / Qwen
- 和风天气 API

## 目录结构

```text
code/
├── server/              # Django 后端
│   ├── accounts/        # 用户注册、登录、Token 鉴权
│   ├── drones/          # 无人机知识文档
│   ├── forum/           # 飞手论坛
│   ├── rag/             # RAG 问答、天气评估、向量索引
│   ├── dronekg/         # Django 项目配置
│   └── db.sqlite3       # 本地数据库
├── web/                 # Vue 前端
│   ├── src/views/       # 页面组件
│   ├── src/api/         # Axios 请求封装
│   ├── src/router/      # 前端路由
│   └── package.json
├── requirements.txt     # 后端 Python 依赖
└── README.md
```

## 环境配置

后端需要在 `server/.env` 中配置 API Key。请不要将 `.env` 提交到 GitHub。

示例：

```env
DASHSCOPE_API_KEY=你的DashScope密钥
DASHSCOPE_MODEL=qwen-plus
HEFENG_API_KEY=你的和风天气API_KEY
HEFENG_API_HOST=https://你的和风天气API_HOST
```

说明：

- `DASHSCOPE_API_KEY` 用于智能问答和天气评估中的大模型调用
- `DASHSCOPE_MODEL` 是 DashScope 中可用的模型名称
- `HEFENG_API_KEY` 用于查询天气数据
- `HEFENG_API_HOST` 是和风天气控制台分配的 API Host

## 运行步骤

### 1. 创建 Conda 环境

项目后端推荐使用 Conda 环境运行，环境名为 `drone-rag`。

```bash
conda create -n drone-rag python=3.12 -y
conda activate drone-rag
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
cd server
python manage.py migrate
```

如需创建 README 中的测试账号，可执行：

```bash
python manage.py shell
```

进入 shell 后执行：

```python
from accounts.models import AppUser
user, _ = AppUser.objects.get_or_create(username='demo', defaults={'nickname': 'demo'})
user.set_password('demo123456')
user.save()
```

### 3. 启动后端

```bash
conda activate drone-rag
cd server
python manage.py runserver 127.0.0.1:8000
```

### 4. 启动前端

另开一个终端窗口：

```bash
cd web
npm install
npm run serve
```

### 5. 打开系统

浏览器访问：

```text
http://localhost:8080
```

测试账号：

```text
用户名：demo
密码：demo123456
```

## 常用接口

登录：

```http
POST /api/auth/login/
```

智能问答：

```http
POST /api/rag/ask/
```

天气评估：

```http
POST /api/rag/weather/
```

构建知识库索引：

```http
POST /api/rag/build-index/
```

知识库检索预览：

```http
GET /api/rag/search-preview/?q=关键词
```

## 演示流程建议

1. 使用测试账号登录系统。
2. 进入“实训智能体”，展示任务卡、安全检查、故障排查和实验报告辅助。
3. 点击任务或故障模板，跳转到“智能问答”，演示学生版结构化回答。
4. 切换到教师版，演示教学评价建议和反馈话术。
5. 进入“天气飞行评估”，输入“今天北京适合飞无人机吗？”，展示天气数据与飞行建议。
6. 进入“知识文档”和“飞手论坛”，展示知识沉淀与协作交流能力。

## 安全说明

- 不要提交 `.env`、数据库、向量库、`node_modules`、构建产物等本地文件。
- API Key 一旦公开，建议立即在控制台重新生成。
- 天气飞行评估结果仅作为教学和实训辅助，真实飞行仍需遵守当地法规、学校安全制度和现场教师要求。
