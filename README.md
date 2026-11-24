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
- PCB 缺陷 AI 质检：上传 PCB 图片，调用 YOLO11 缺陷检测模型，自动输出缺陷类型、置信度、扣分、评分和改进建议

### 2. 智能问答

基于 Chroma 向量检索、OpenAI 文本向量模型和 `gpt-6-sol`，对无人机实训问题进行结构化回答。回答会尽量包含：

- 结论概览
- 原因分析
- 操作步骤
- 安全提醒
- 实验报告记录要点

问答页面支持“学生版”和“教师版”两种视角。

### 3. 天气飞行评估

调用和风天气 v1 API 获取实时天气或未来 3 天预报，再结合 Qwen 生成无人机飞行建议。评估依据包括：

- 风速、阵风与风力
- 能见度
- 降水和雷暴风险
- 湿度与设备防潮
- 实训飞行安全建议

### 4. 知识文档库

用于维护无人机相关文档，支持按分类、机型、标签和关键词检索。文档内容会用于 RAG 问答索引。

仓库附带 25 篇实训文档，源数据位于 `server/drones/knowledge_docs.json`，当前 `server/db.sqlite3` 也已导入。若使用新数据库，先运行迁移，再在 `server` 目录执行 `python drones/seed_knowledge_docs.py`。重复执行只补充缺失标题，不覆盖已编辑的文档。文档变更后可运行 `python manage.py build_chroma_index` 更新问答索引（需要配置向量模型凭据）。

### 5. 飞手论坛

提供实训经验交流、故障求助、作品展示和评论点赞等社区功能。

### 6. PCB 缺陷检测

平台已接入 `PCB_Defect/YoloV11_new` 训练工程中的 YOLO11 改造版模型，用于 PCB 缺陷识别演示。支持的缺陷类别包括：

- `missing_hole`：缺孔
- `mouse_bite`：鼠咬
- `open_circuit`：开路
- `short`：短路
- `spurious_copper`：杂铜
- `spur`：毛刺

前端入口位于“实训智能体”页面的“PCB缺陷检测与评分”模块。上传图片后，后端会返回检测框、类别、置信度、扣分、总分、等级、标注图和改进建议。

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
- OpenAI API（智能问答和向量检索）
- DashScope / Qwen（天气评估文字生成）
- 和风天气 API
- Ultralytics YOLO
- PyTorch
- YOLO11 PCB 缺陷检测模型

## 目录结构

```text
code/
├── server/              # Django 后端
│   ├── accounts/        # 用户注册、登录、Token 鉴权
│   ├── drones/          # 无人机知识文档
│   ├── forum/           # 飞手论坛
│   ├── rag/             # RAG 问答、天气评估、向量索引
│   ├── soldering/       # PCB/焊点视觉检测接口、评分规则
│   ├── vendor_ultralytics/ # PCB_Defect 提供的改造版 Ultralytics 源码
│   ├── weights/         # YOLO 权重文件
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

后端需要在 `server/.env` 中配置 API Key、模型路径等参数。可复制 `server/.env.example` 作为模板；请不要将 `.env` 提交到 GitHub，也不要把密钥写在前端代码中。生产环境（`DEBUG=0`）必须设置独立的 `DJANGO_SECRET_KEY`。

示例：

```env
# 智能问答（OpenAI Responses 兼容接口）
DJANGO_SECRET_KEY=请在本地生成随机长字符串
OPENAI_API_KEY=请填写自己的API密钥
OPENAI_BASE_URL=https://your-endpoint.example/v1
OPENAI_MODEL=gpt-6-sol
OPENAI_REASONING_EFFORT=high
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIM=1024

# 天气评估
DASHSCOPE_API_KEY=请填写自己的DashScope密钥
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_BASE_URL=https://ap-southeast-1.maas.qwencloudapi.com/compatible-mode/v1
HEFENG_API_KEY=请填写自己的和风天气API密钥
HEFENG_API_HOST=https://your-api-host.example

# PCB 缺陷检测，默认值可不写
PCB_DEFECT_YOLO_WEIGHTS=/absolute/path/to/pcb_defect_yolo11_best.pt
SOLDER_YOLO_CONF=0.45
SOLDER_YOLO_IMGSZ=960
SOLDER_YOLO_DEVICE=auto
```

说明：

- `OPENAI_API_KEY` 用于智能问答和文档向量检索；`OPENAI_BASE_URL` 指向你提供的中转站地址
- 问答使用 Responses 接口、`gpt-6-sol` 和 `high` 推理强度，并以 `store=false` 禁用响应存储
- `OPENAI_EMBEDDING_MODEL` 和 `OPENAI_EMBEDDING_DIM` 用于构建和查询智能问答的 Chroma 索引
- `DASHSCOPE_API_KEY`、`DASHSCOPE_MODEL` 和 `DASHSCOPE_BASE_URL` 仅用于天气评估中的 Qwen 文字生成；示例地址为新加坡地域
- `HEFENG_API_KEY` 是和风天气项目中的 API KEY 凭据，仅由后端使用
- `HEFENG_API_HOST` 是和风天气控制台“设置”页分配的专属 API Host，必须填写自己的 HTTPS 地址
- `PCB_DEFECT_YOLO_WEIGHTS` 是 PCB 缺陷检测模型权重路径
- `SOLDER_YOLO_CONF` 是 YOLO 检测置信度阈值
- `SOLDER_YOLO_IMGSZ` 是 YOLO 推理图像尺寸
- `SOLDER_YOLO_DEVICE=auto` 表示自动选择 GPU，若当前环境不可用则回退 CPU

天气问答的配置步骤：

1. 按[和风天气项目与凭据教程](https://dev.qweather.com/docs/configuration/project-and-key/)创建项目，并在项目中添加 **API KEY** 凭据。
2. 在[控制台设置页](https://dev.qweather.com/docs/configuration/api-host/)找到账号专属 API Host。
3. 将完整凭据填入 `server/.env` 的 `HEFENG_API_KEY`，将专属 Host（带 `https://`，不带路径）填入 `HEFENG_API_HOST`。天气评估生成文字还需要填写 `DASHSCOPE_API_KEY`。
4. 重启 Django 后端，进入“天气飞行评估”输入“今天北京适合飞无人机吗？”验证。

后端通过 `X-QW-Api-Key` 请求头发送天气凭据，使用 `/geo/v2/city/lookup`、`/weather/v1/current/{纬度}/{经度}` 和 `/weather/v1/daily/{纬度}/{经度}`；密钥不会出现在请求 URL 中。逐日预报没有能见度字段，回答不会据此断言飞行安全。

## PCB 模型文件

当前项目已接入以下模型文件：

模型权重文件不会上传到 GitHub。请自行将所需权重放入 `server/weights/`，或在本地 `.env` 中填写权重的绝对路径。

```text
server/weights/pcb_defect_yolo11_best.pt   # 当前前端使用的正式 PCB 缺陷检测权重
server/weights/pcb_defect_yolo11n.pt       # YOLO11n 底座/备用权重
server/weights/yolov8n.pt                  # 通用预训练测试权重
```

`pcb_defect_yolo11_best.pt` 依赖训练工程中的改造版 Ultralytics 源码，因此项目内保留了：

```text
server/vendor_ultralytics/
```

后端启动时会优先将 `server/vendor_ultralytics` 加入 `sys.path`，确保 `best.pt` 能加载到 `Addmodules`、`AFPN4Head`、`C_iCAFM` 等自定义模块。

## 运行步骤

### 1. 创建 Conda 环境

项目后端推荐使用 Conda 环境运行，环境名为 `drone-rag`。如果已有该环境，可直接激活并安装依赖。

```bash
conda create -n drone-rag python=3.12 -y
conda activate drone-rag
pip install -r requirements.txt
```

如果需要 GPU 推理，请确保当前环境中的 PyTorch 能识别 CUDA：

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

若输出 `False`，平台仍可运行，YOLO 推理会按配置回退 CPU。

### 2. 初始化数据库

```bash
cd server
python manage.py migrate
```

如需创建本地演示账号，可执行：

```bash
python manage.py shell
```

进入 shell 后执行：

```python
from accounts.models import AppUser
from getpass import getpass
user, _ = AppUser.objects.get_or_create(username='demo', defaults={'nickname': 'demo'})
user.set_password(getpass('设置演示账号密码：'))
user.save()
```

### 3. 启动后端

```bash
conda activate drone-rag
cd server
python manage.py runserver 127.0.0.1:8000
```

可先执行系统检查：

```bash
python manage.py check
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

可在登录页注册新账号，或使用上一步自行创建的演示账号。

### 6. 验证 PCB 模型加载

在项目根目录执行：

```bash
python - <<'PY'
import sys
sys.path.insert(0, 'server/vendor_ultralytics')
from ultralytics import YOLO
m = YOLO('server/weights/pcb_defect_yolo11_best.pt')
print(m.names)
PY
```

预期输出包含：

```python
{0: 'missing_hole', 1: 'mouse_bite', 2: 'open_circuit', 3: 'short', 4: 'spurious_copper', 5: 'spur'}
```

## 常用接口

登录：

```http
POST /api/auth/login/
```

智能问答：

```http
POST /api/rag/ask/
Authorization: Token <登录返回的token>
Content-Type: application/json

{"question":"Pixhawk 如何校准传感器？"}
```

问答页面使用流式接口 `POST /api/rag/ask-stream/`，请求头与请求体相同。问答使用独立的 OpenAI 向量索引；首次切换或修改向量模型后，请登录并调用 `POST /api/rag/build-index/` 构建知识库索引。

如使用兼容接口服务，服务端需提供与 `text-embedding-3-small` 兼容的 Embeddings 接口，才能构建和检索知识库索引。

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

PCB 缺陷检测：

```http
POST /api/soldering/inspect-pcb/
Content-Type: multipart/form-data

file=待检测PCB图片
```

返回内容包括：

- `score`：总分
- `grade`：等级
- `detections`：缺陷列表
- `annotated_image_url`：标注图地址
- `suggestions`：改进建议
- `model.weights`：实际使用的权重文件名

## 演示流程建议

1. 使用测试账号登录系统。
2. 进入“实训智能体”，展示任务卡、安全检查、故障排查和实验报告辅助。
3. 在“PCB缺陷检测与评分”模块上传 PCB 测试图片，演示 YOLO11 自动检测、评分、标注图和改进建议。
4. 点击“生成讲解建议”，跳转到智能问答，演示教师视角的缺陷讲解与纠正建议。
5. 点击任务或故障模板，跳转到“智能问答”，演示学生版结构化回答。
6. 切换到教师版，演示教学评价建议和反馈话术。
7. 进入“天气飞行评估”，输入“今天北京适合飞无人机吗？”，展示天气数据与飞行建议。
8. 进入“知识文档”和“飞手论坛”，展示知识沉淀与协作交流能力。

PCB 测试图片请使用自行准备的样本。

## 安全说明

- 不要提交 `.env`、数据库、向量库、`node_modules`、构建产物等本地文件。
- YOLO 权重文件和 `server/vendor_ultralytics` 体积较大，若使用 Git 托管，建议确认仓库策略或使用 Git LFS。
- API Key 一旦公开，建议立即在控制台重新生成。
- 天气飞行评估结果仅作为教学和实训辅助，真实飞行仍需遵守当地法规、学校安全制度和现场教师要求。
- PCB 缺陷检测结果用于教学演示和辅助评价，正式考核仍建议教师复核。
