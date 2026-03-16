# LifeOS — 个人 AI Agent 系统

> 面向个人用户的**主动式 AI 助理**，具备多 Agent 协同、长期记忆、任务规划、工具调用与主动提醒能力。

## 项目亮点

| 能力 | 说明 |
|------|------|
| **多 Agent 架构** | Orchestrator → Planner → Executor → Memory → Proactive，5 个 Agent 各司其职 |
| **意图路由** | LLM 驱动的 4 类意图分类（chat / plan_task / tool_request / memory_write） |
| **长期记忆** | SQLite 结构化存储 + Chroma 向量语义检索，混合评分召回 |
| **任务规划与执行** | Planner 拆解任务 → Executor 串行调用工具 → LLM 综合生成回答 |
| **工具调用** | 统一 BaseTool 接口，已接入 Search / Calendar / Todo 三个工具 |
| **主动提醒** | APScheduler 定时触发每日早报，读取日程+待办自动生成建议 |
| **全链路可观测** | 每次请求记录完整 trace（意图 → 记忆 → 计划 → 工具 → 响应），持久化到 DB |

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Chat UI                   │
│           (聊天界面 + 调试面板 + 主动消息)              │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│                   FastAPI Backend                     │
│  /api/chat  /api/memories  /api/proactive  /api/debug│
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Orchestrator (LangGraph)                 │
│                                                      │
│  classify_intent → load_memory → route_by_intent     │
│       │                              │               │
│       ▼                              ▼               │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐        │
│  │ Planner │  │  Memory  │  │   Proactive   │       │
│  │  Agent  │  │  Agent   │  │    Agent      │       │
│  └────┬────┘  └────┬─────┘  └──────────────┘        │
│       │            │                                  │
│       ▼            ▼                                  │
│  ┌─────────┐  ┌──────────────┐                       │
│  │Executor │  │SQLite + Chroma│                      │
│  │  Agent  │  └──────────────┘                       │
│  └────┬────┘                                         │
│       │                                              │
│       ▼                                              │
│  ┌──────────────────────────┐                        │
│  │      Tool Layer          │                        │
│  │  Search  Calendar  Todo  │                        │
│  └──────────────────────────┘                        │
└──────────────────────────────────────────────────────┘
```

## 核心流转

```
用户输入
  → Orchestrator
    → 意图分类 (LLM)
    → 记忆加载 (Chroma 语义 + SQLite 结构化)
    → 路由到对应 Handler
      ├─ chat       → LLM 直接回复
      ├─ plan_task  → Planner 生成计划 → Executor 执行 → 综合回答
      ├─ tool_request → Planner + Executor (同上)
      └─ memory_write → Memory Agent 抽取并持久化
    → 后置记忆抽取 (自动从对话中提取值得记住的信息)
  → 返回 response + intent + plan + tool_logs + trace
```

## 快速开始

### 环境要求

- Python 3.11+
- 至少一个 LLM API Key（OpenAI / Anthropic / DeepSeek）

### 安装

```bash
# 克隆项目
git clone <repo-url> && cd lifeos

# 创建虚拟环境并安装依赖
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 初始化数据库 & Demo 数据

```bash
# 初始化数据库
python scripts/init_db.py

# (可选) 导入演示数据
python scripts/seed_demo_data.py
```

### 启动

```bash
# 终端 1: 启动后端
uvicorn backend.main:app --reload --port 12345

# 终端 2: 启动前端
streamlit run frontend/app.py
```

### 验证

| 地址 | 说明 |
|------|------|
| http://localhost:12345/health | 后端健康检查 |
| http://localhost:12345/docs | Swagger API 文档 |
| http://localhost:8501 | Streamlit 前端 |

## Demo 场景

### Demo 1：规划明天工作

```
输入: "帮我规划一下明天的工作安排"
流程: Planner → Calendar(mock) + Todo(list) → Executor → 综合生成时间块计划
展示: 意图路由 + Plan 生成 + 工具调用 + LLM 综合
```

### Demo 2：长期记忆

```
输入: "记住我最近想系统学习 AI Agent 开发"
流程: Memory Agent → LLM 抽取 → SQLite + Chroma 写入
验证: 后续对话中会自动召回这条记忆作为上下文
```

### Demo 3：信息搜索

```
输入: "搜一下最新的 AI Agent 开发趋势"
流程: Planner → Search Tool → Executor → 摘要生成
展示: Tool Calling + Summarization
```

### Demo 4：每日早报

```
触发: 侧边栏 "Trigger Morning Briefing" 按钮（或每日 08:00 自动触发）
流程: Proactive Agent → Calendar + Todo + Memory → LLM 生成早报
展示: 主动式 Agent + 定时调度
```

## 项目结构

```
lifeos/
├── frontend/
│   └── app.py                  # Streamlit 主界面 + 调试面板
├── backend/
│   ├── main.py                 # FastAPI 入口 + APScheduler
│   └── app/
│       ├── api/
│       │   ├── chat.py         # 聊天接口 (含 trace 记录)
│       │   ├── proactive.py    # 主动消息接口
│       │   ├── memories.py     # 记忆管理接口
│       │   └── debug.py        # 调试/可观测接口
│       ├── agents/
│       │   ├── orchestrator.py # LangGraph 编排 + 意图路由
│       │   ├── planner.py      # 任务规划 Agent
│       │   ├── executor.py     # 计划执行 Agent
│       │   ├── memory.py       # 记忆管理 Agent
│       │   └── proactive.py    # 主动提醒 Agent
│       ├── tools/
│       │   ├── base.py         # BaseTool + ToolRegistry
│       │   ├── search.py       # 搜索工具
│       │   ├── calendar.py     # 日程工具 (mock)
│       │   └── todo.py         # 待办工具
│       ├── memory/
│       │   ├── store.py        # SQLite 存储层
│       │   └── vector.py       # Chroma 向量存储层
│       ├── models/
│       │   └── schemas.py      # Pydantic 数据模型
│       └── core/
│           ├── config.py       # 配置管理
│           ├── llm.py          # LLM 调用封装
│           └── logger.py       # Loguru 日志配置
├── scripts/
│   ├── init_db.py              # 数据库初始化
│   └── seed_demo_data.py       # Demo 数据导入
├── data/                       # SQLite 数据库文件
├── logs/                       # 运行日志
└── docs/                       # 设计文档
```

## 技术选型

| 层 | 技术 | 选型理由 |
|----|------|----------|
| 后端框架 | FastAPI + Pydantic | 异步高性能，类型安全 |
| Agent 编排 | LangGraph | 显式状态流，可视化友好 |
| LLM | OpenAI / Anthropic / DeepSeek | 多提供商灵活切换 |
| 结构化存储 | SQLite | 零配置，一键启动 |
| 向量存储 | Chroma | 轻量级，内置 embedding |
| 前端 | Streamlit | 快速原型，核心在后端 |
| 定时任务 | APScheduler | 轻量异步调度 |
| 日志 | Loguru | 结构化日志，彩色输出 |

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 聊天（经 Orchestrator 全流程） |
| GET | `/api/memories` | 查看用户记忆 |
| DELETE | `/api/memories/{id}` | 删除记忆 |
| GET | `/api/proactive/messages` | 获取主动消息 |
| POST | `/api/proactive/trigger` | 手动触发早报 |
| GET | `/api/debug/session/{id}` | 查看会话 trace |
| GET | `/api/debug/traces` | 查看最近 trace |
| GET | `/api/debug/tools` | 列出已注册工具 |
| GET | `/api/debug/system` | 系统状态概览 |
| GET | `/health` | 健康检查 |

## 设计亮点（面试讲解）

1. **为什么做多 Agent 架构？** — 职责单一、可独立测试、可扩展，不是一个巨型 Prompt
2. **记忆系统如何避免无脑堆上下文？** — 写入策略（LLM 判断是否值得保存）+ 混合检索（语义 0.5 + 时间衰减 0.5）
3. **Planner 与 Executor 如何解耦？** — Planner 只输出结构化 Plan，Executor 只负责执行，互不依赖
4. **可观测性如何实现？** — 每步产出 trace 标记，全链路持久化到 DB，前端可视化展示
5. **如何扩展？** — 新增工具只需实现 BaseTool + 注册；新增 Agent 只需加 LangGraph 节点

## License

MIT
