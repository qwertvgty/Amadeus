# LifeOS — 个人 Agent 系统（简化版需求与架构）

## 1. 项目信息

**项目名称**：LifeOS / Personal Agent OS
**定位**：面向个人用户的主动式 AI 助理 Agent 系统
**目标**：作为 Agent 开发工程师求职项目，展示系统架构、Agent 编排、记忆系统、工具调用与工程落地能力
**周期**：8 周
**目标岗位**：中小厂业务型 Agent / AI 应用开发工程师

---

## 2. 项目背景

当前 AI 产品大多停留在"问一句、答一句"的被动模式，缺乏：

1. 对用户长期状态的持续记忆
2. 对任务的多步骤规划与执行
3. 对工具的自主选择与调用
4. 在合适时机进行主动提醒

本项目构建一个围绕用户生活与轻工作场景的 **Proactive Personal Agent**，核心价值：

- 能理解用户目标与偏好
- 能基于长期记忆提供连续体验
- 能对任务进行规划、执行与总结
- 能结合日程、待办、搜索等工具完成闭环
- 能通过多 Agent 架构展示工程化能力

---

## 3. 项目目标

### 3.1 业务目标

构建一个可演示、可扩展、可讲解的 Agent 系统 Demo，证明：

- Agent 系统级架构设计能力
- 多 Agent 协同与职责拆分
- 长期记忆和用户画像机制
- Tool Calling 与任务执行闭环
- 具备"主动性"的 Agent 产品形态

### 3.2 技术目标

1. 实现可运行的 Agent Orchestrator（含意图路由）
2. 实现 Planner / Memory / Executor 核心 Agent
3. 实现至少 3 个工具集成（Search / Calendar mock / Todo）
4. 实现短期记忆与长期记忆双层机制
5. 实现至少 1 个主动触发场景（定时早报）
6. 提供可视化交互界面与完整项目结构

### 3.3 面试展示目标

面试官看到项目后应形成判断：

- 候选人能做完整 Agent 系统，不只是调接口
- 候选人理解模块解耦与流程编排
- 候选人具备工程落地与架构思维

---

## 4. 产品定位

### 4.1 产品定义

LifeOS 是单用户个人 AI Agent 系统，围绕"生活管理 + 轻工作辅助"场景，提供：

- 自然语言交互
- 任务理解与拆解
- 长期用户记忆
- 工具调用与执行
- 主动提醒与建议

### 4.2 不做什么

- 不做登录注册 / 多用户 / 权限体系（单用户系统）
- 不做多模态生成（语音、视频）
- 不做复杂工作流市场 / 插件平台
- 不做重度办公协同
- 不做社交属性产品

---

## 5. 核心使用场景

### 场景 A：工作规划（P0）

> "帮我规划一下明天的工作安排。"

- 读取用户日程和待办
- 分析任务优先级
- 生成可执行时间块计划

### 场景 B：长期目标追踪（P0）

> "记住我最近想系统学习 AI Agent 开发。"

- 提取用户长期目标
- 写入长期记忆
- 后续在相关上下文中主动提及

### 场景 C：信息辅助（P1）

> "帮我找一下今天值得看的 AI 新闻。"

- 调用搜索工具
- 汇总信息
- 输出精简摘要

### 场景 D：主动早报（P1）

> 系统每日定时输出："今日你有 3 个待办未完成，建议优先处理 X。"

- 定时触发
- 读取待办和日程
- 生成简要提醒

### 场景 E：情绪关注（P2，可选）

> "我最近有点焦虑，事情太多了。"

- 识别情绪
- 提供轻量建议
- 记录用户状态

---

## 6. 功能模块设计

MVP 划分为 5 大模块：

### 6.1 对话与意图理解（Orchestrator 内部）

**目标**：理解用户输入，识别意图，路由到对应流程。

意图路由作为 Orchestrator 的内部步骤，不独立成 Agent。

**MVP 意图类型（4 种）**：

| 意图 | 说明 | 路由目标 |
|------|------|----------|
| `chat` | 普通闲聊 | 直接 LLM 回复 |
| `plan_task` | 任务规划 | Planner → Executor |
| `tool_request` | 工具请求 | Executor |
| `memory_write` | 记忆写入 | Memory Agent |

**需求点**：
- 支持多轮对话上下文
- 支持意图分类 + 参数抽取
- 支持模糊任务转结构化请求

---

### 6.2 Planner Agent

**目标**：将用户需求拆解成可执行步骤。

**输入**：任务描述、用户上下文、记忆信息、工具能力列表
**输出**：执行计划 Plan

**Plan 结构**：

```json
{
  "goal": "规划明天工作",
  "required_tools": ["calendar", "todo"],
  "steps": [
    "读取明天日程",
    "读取未完成待办",
    "按紧急程度排序",
    "生成时间块计划"
  ]
}
```

**需求点**：
- 支持任务拆解
- 支持根据上下文选择工具
- 支持输出可执行中间态

> 注：`fallback` 和重规划能力放到 V2。

---

### 6.3 Memory Agent

**目标**：管理用户的短期上下文和长期画像。

#### 短期记忆

- 最近 N 轮消息
- 当前任务状态

#### 长期记忆（2 类）

| 类型 | 说明 | 示例 |
|------|------|------|
| `profile` | 身份、职业、习惯、偏好 | "用户是后端开发，喜欢晚上学习" |
| `episodic` | 关键事件、目标、状态 | "用户想学 AI Agent 开发" |

> 通过 tag 字段扩展（如 `goal` / `preference` / `emotion`），不做更细分类。

**需求点**：
- 支持记忆抽取与写入
- 支持记忆检索（语义 + 结构化）
- 支持记忆摘要与去重

---

### 6.4 Executor Agent

**目标**：根据 Planner 产出的计划，串行执行具体步骤。

**职责**：
- 按步骤调度工具
- 收集执行结果
- 汇总最终结果
- 输出执行日志

> 注：条件判断和失败重试放到 V2，MVP 只做串行执行。

---

### 6.5 Tool Layer

**MVP 工具**：

#### Tool 1：Search Tool
- 搜索公开信息，返回摘要结果

#### Tool 2：Calendar Tool（mock）
- 获取当天/明天日程（mock 数据）

#### Tool 3：Todo Tool
- 新增 / 查询 / 更新待办

**统一接口**：

```python
class BaseTool:
    name: str
    description: str
    input_schema: dict

    async def execute(self, params: dict) -> dict:
        pass
```

**调用策略**：
- 由 Planner 给出候选工具
- 由 Executor 具体调用
- 失败时返回可解释错误
- 工具输出统一转中间格式

---

### 6.6 Proactive Agent（P1）

**目标**：实现系统主动行为。

**MVP 只做时间触发**：
- 每日早间待办/日程提醒

> 状态触发（任务堆积、连续熬夜）和事件触发（日程冲突、截止临近）放到 V2。

**需求点**：
- 支持定时规则触发
- 支持从记忆中提取用户状态
- 支持主动建议模板

---

### 6.7 可观测性模块

**目标**：方便演示与排查 Agent 工作流程。面试加分项。

**需记录**：
- 用户输入 → 意图识别结果 → 选中的 Agent → Plan 内容 → 工具调用记录 → Memory 读写日志 → 最终回复

**展示方式**：
- 后端结构化日志（Loguru）
- 前端调试面板（展示每步流转）
- LangSmith（可选，开箱即用）

---

## 7. 非功能需求

### 7.1 可扩展性
- 可新增工具和 Agent
- 支持从单体升级为事件驱动

### 7.2 可维护性
- 模块职责清晰，统一接口抽象
- Agent 与 Tool 解耦
- 存储层可替换

### 7.3 可演示性
- 本地一键启动
- 可视化展示流程
- 准备固定 Demo 脚本

### 7.4 性能
- 常规对话 < 5 秒
- 带工具调用 < 15 秒
- 超时降级到普通回答

### 7.5 安全
- 不处理敏感隐私推断
- 工具调用白名单机制
- 用户数据本地存储

---

## 8. 总体架构

### 8.1 设计原则

1. **职责单一**：每个 Agent 专注一个角色
2. **可编排**：Agent 间通过状态和任务流衔接
3. **可扩展**：工具和存储可替换
4. **可观测**：每一步可追踪
5. **面向演示**：结构清晰，便于面试讲解

### 8.2 逻辑架构

```text
[Streamlit Chat UI]
        |
        v
[FastAPI Backend]
        |
        v
[Orchestrator (含 Intent Router)]
   |         |          |
   v         v          v
[Planner]  [Memory]  [Proactive]
   |         |
   v         v
[Executor] [SQLite + Chroma]
   |
   v
[Tool Layer]
   |      |      |
   v      v      v
Search Calendar Todo
       (mock)
```

### 8.3 分层架构

| 层 | 组件 |
|----|------|
| 表现层 | Streamlit Chat UI + 调试面板 |
| 接入层 | FastAPI API |
| 编排层 | Orchestrator（含 Intent Router + State Manager） |
| 能力层 | Planner / Memory / Executor / Proactive Agent |
| 基础设施层 | LLM Provider / SQLite / Chroma / APScheduler |

---

## 9. Agent 架构

### 9.1 Agent 列表（5 个）

| Agent | 职责 |
|-------|------|
| **Orchestrator** | 接收输入、意图路由、维护状态、调度下游、决定流程出入口 |
| **Planner** | 任务拆解、生成执行计划、选择工具 |
| **Memory** | 提取用户信息、检索记忆、维护长期画像 |
| **Executor** | 执行计划步骤、调用工具、汇总结果 |
| **Proactive** | 定时扫描状态、触发主动建议（P1） |

### 9.2 状态流转

```text
User Input
   |
   v
Orchestrator (Intent Router)
   |
   +--> chat --------------------------> LLM Response
   |
   +--> memory_write --> Memory Agent --> Response
   |
   +--> plan_task --> Planner --> Executor --> Response
   |
   +--> tool_request --> Executor ------> Response
```

---

## 10. 数据流

### 10.1 用户请求流程

1. 前端发送用户输入到后端
2. Orchestrator 创建会话状态
3. Orchestrator 内部意图路由判断请求类型
4. Memory Agent 读取相关用户长期记忆
5. Planner Agent 生成计划（如有）
6. Executor Agent 调用相应工具
7. Memory Agent 对本轮进行记忆抽取
8. 最终回复返回前端
9. 调试链路写入日志

### 10.2 主动任务流程

1. APScheduler 定时触发 Proactive Agent
2. 读取用户待办 / 日程
3. 生成主动建议
4. 推送到前端消息流

---

## 11. 记忆系统

### 11.1 存储方案

**SQLite + Chroma**

- SQLite：结构化数据（用户画像、任务、会话、日志）
- Chroma：向量检索（语义记忆召回）
- 零配置，本地一键启动，适合 MVP 演示

### 11.2 数据模型

#### user_profiles

| 字段 | 类型 |
|------|------|
| user_id | TEXT PK |
| name | TEXT |
| role | TEXT |
| preferences_json | TEXT |
| created_at | DATETIME |
| updated_at | DATETIME |

#### memories

| 字段 | 类型 |
|------|------|
| id | TEXT PK |
| user_id | TEXT |
| memory_type | TEXT (`profile` / `episodic`) |
| tags | TEXT (JSON array, 如 `["goal", "preference"]`) |
| content | TEXT |
| summary | TEXT |
| source_turn_id | TEXT |
| created_at | DATETIME |

> 向量 embedding 存储在 Chroma 中，通过 id 关联。

#### tasks

| 字段 | 类型 |
|------|------|
| id | TEXT PK |
| user_id | TEXT |
| title | TEXT |
| status | TEXT |
| priority | TEXT |
| due_time | DATETIME |
| source | TEXT |
| created_at | DATETIME |

#### sessions

| 字段 | 类型 |
|------|------|
| session_id | TEXT PK |
| user_id | TEXT |
| latest_context | TEXT |
| current_goal | TEXT |
| created_at | DATETIME |

#### tool_logs

| 字段 | 类型 |
|------|------|
| id | TEXT PK |
| session_id | TEXT |
| tool_name | TEXT |
| input_payload | TEXT |
| output_payload | TEXT |
| status | TEXT |
| created_at | DATETIME |

### 11.3 记忆写入策略

只在满足以下条件时写入长期记忆：

- 用户明确表达偏好/目标
- 用户状态具有长期意义
- 对未来决策可能有帮助

### 11.4 记忆检索策略

混合检索：

1. 结构化筛选（memory_type / user_id / tags）
2. 向量召回（Chroma 语义相似）
3. 排序公式：`final_score = semantic_score * 0.5 + recency * 0.5`

> 权重先硬编码，V2 再加 importance_score 和动态调参。

---

## 12. 技术选型

| 层 | 选型 | 理由 |
|----|------|------|
| 后端 | Python + FastAPI + Pydantic | 主流，生态好 |
| Agent 编排 | LangGraph | 显式状态流，面试友好 |
| 模型 | OpenAI / Claude / DeepSeek API | 灵活切换 |
| 结构化存储 | SQLite | 零配置，一键启动 |
| 向量存储 | Chroma | 轻量，适合 MVP |
| 前端 | Streamlit | 1-2 天搞定，核心卖点在后端 |
| 任务调度 | APScheduler | 轻量够用 |
| 日志 | Loguru | 结构化日志 |
| 可观测（可选） | LangSmith | 开箱即用 |

---

## 13. 接口设计

### 13.1 对话接口

**POST** `/api/chat`

```json
// Request
{
  "user_id": "u1",
  "session_id": "s1",
  "message": "帮我规划一下明天的工作"
}

// Response
{
  "reply": "我已经根据你的日程和待办整理了明天的工作安排...",
  "intent": "plan_task",
  "plan": {...},
  "tool_logs": [...]
}
```

### 13.2 主动消息接口

**GET** `/api/proactive/messages?user_id=u1`

### 13.3 记忆查看接口

**GET** `/api/memories?user_id=u1`

### 13.4 调试链路接口

**GET** `/api/debug/session/{session_id}`

---

## 14. 项目结构

```text
lifeos/
├── frontend/
│   └── app.py                  # Streamlit 主界面
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── proactive.py
│   │   │   ├── memories.py
│   │   │   └── debug.py
│   │   ├── agents/
│   │   │   ├── orchestrator.py  # 含 Intent Router
│   │   │   ├── planner.py
│   │   │   ├── memory.py
│   │   │   ├── executor.py
│   │   │   └── proactive.py
│   │   ├── tools/
│   │   │   ├── base.py
│   │   │   ├── search.py
│   │   │   ├── calendar.py
│   │   │   └── todo.py
│   │   ├── memory/
│   │   │   ├── store.py         # SQLite 操作
│   │   │   └── vector.py        # Chroma 操作
│   │   ├── models/
│   │   │   └── schemas.py
│   │   └── core/
│   │       ├── config.py
│   │       └── logger.py
│   ├── tests/
│   └── main.py
├── docs/
│   ├── architecture.md
│   └── demo-script.md
├── scripts/
│   └── init_db.py
└── README.md
```

> 每个 Agent 一个文件，不单独建目录，MVP 阶段够用。

---

## 15. 核心 Demo 场景

| Demo | 展示点 |
|------|--------|
| **Demo 1：规划明天工作** | Planner + Calendar(mock) + Todo + Executor 全链路 |
| **Demo 2：记住长期目标** | 长期记忆写入与检索 |
| **Demo 3：AI 新闻搜索** | Tool Calling + Summarization |
| **Demo 4：每日早报** | Proactive Agent + 定时触发 |

---

## 16. 开发计划（8 周）

### 第 1 周：基础骨架
- 初始化项目结构
- FastAPI 后端 + Streamlit 前端跑通
- 基础聊天接口（直连 LLM）
- 定义核心 Pydantic 数据结构

### 第 2 周：Orchestrator + Intent
- 实现 Orchestrator 框架（LangGraph）
- 实现意图路由（4 种意图）
- 跑通 chat 意图的完整链路

### 第 3 周：Memory Agent
- 建立 SQLite 表结构
- 接入 Chroma
- 实现记忆写入 / 检索
- 跑通 memory_write 意图链路

### 第 4 周：Planner + Executor
- 实现 Planner Agent
- 实现 Executor Agent（串行执行）
- 定义 Plan Schema
- 跑通 plan_task 意图链路（不含工具）

### 第 5 周：Tool Layer
- 实现 BaseTool 抽象
- 接入 Search / Todo / Calendar(mock) Tool
- Executor 调用工具完成完整闭环
- 跑通 Demo 1（规划明天工作）

### 第 6 周：Proactive + 串联
- 实现 Proactive Agent + APScheduler
- 每日早报场景
- 全流程串联调试
- 跑通 Demo 2/3/4

### 第 7 周：可观测性 + 打磨
- 实现调试日志面板
- 前端交互优化
- 边界情况处理

### 第 8 周：演示准备
- 准备固定 Demo 数据
- 补充 README、架构图
- 准备面试讲稿
- 端到端测试

---

## 17. 功能优先级总览

| 优先级 | 功能 | 状态 |
|--------|------|------|
| **P0** | Chat UI (Streamlit) | MVP 必做 |
| **P0** | Orchestrator（含 Intent Router） | MVP 必做 |
| **P0** | Memory Agent（profile + episodic） | MVP 必做 |
| **P0** | Planner Agent | MVP 必做 |
| **P0** | Executor Agent（串行） | MVP 必做 |
| **P0** | Todo Tool | MVP 必做 |
| **P1** | Search Tool | MVP 必做 |
| **P1** | Calendar Tool (mock) | MVP 必做 |
| **P1** | 短期/长期记忆存储 | MVP 必做 |
| **P1** | 调试日志面板 | MVP 必做 |
| **P1** | Proactive Agent（定时早报） | MVP 必做 |
| **P2** | 情绪识别 | V2 可选 |
| **P2** | 计划执行复盘 | V2 可选 |
| **P2** | 状态触发 / 事件触发 | V2 可选 |
| **P2** | 周总结 | V2 可选 |
| **P2** | Notion / 邮件集成 | V2 可选 |
| **P2** | 失败重试 / 条件判断 | V2 可选 |
| **P2** | Next.js 前端 | V2 可选 |
| **P2** | PostgreSQL 迁移 | V2 可选 |

---

## 18. 风险与应对

| 风险 | 应对 |
|------|------|
| 范围膨胀 | 严格按优先级执行，P2 全部后置 |
| 工具接入复杂 | Calendar 先 mock，Search 用现成 API |
| LangGraph 学习曲线 | 第 2 周专门消化，遇阻可先用简单函数调用替代 |
| 项目看起来像聊天壳子 | 重点展示 Plan/Memory/Tool Logs/状态流可视化 |
| 进度延迟 | 第 7-8 周为 buffer，可吸收前期延迟 |

---

## 19. 面试讲解重点

1. 为什么做"主动式 Agent 系统"而非普通聊天机器人
2. 为什么采用多 Agent 角色拆分，而不是一个巨型 Prompt
3. 记忆系统如何避免无脑堆上下文（写入策略 + 混合检索）
4. Planner 和 Executor 如何解耦
5. 如何通过日志和状态流提升系统可解释性
6. 如果继续扩展，如何支持更多工具和更复杂工作流

---

## 20. 与原版文档的主要简化

| 项目 | 原版 | 简化版 | 原因 |
|------|------|--------|------|
| Agent 数量 | 7 个（含 Emotion Analyzer） | 5 个 | 减少复杂度 |
| Intent Router | 独立 Agent，7 种意图 | Orchestrator 内部步骤，4 种意图 | 减少模块数 |
| 记忆分类 | 5 种（Profile/Goal/Preference/Episodic/Emotional） | 2 种 + tag 扩展 | 避免过度设计 |
| 主动触发 | 3 种（时间/状态/事件） | 1 种（时间触发） | MVP 够用 |
| 前端 | Next.js + Tailwind | Streamlit | 核心在后端，省时间 |
| 数据库 | PostgreSQL + pgvector | SQLite + Chroma | 零配置，一键启动 |
| Plan 结构 | 含 fallback | 无 fallback | MVP 不需要 |
| Executor | 含条件判断 + 失败重试 | 纯串行执行 | MVP 够用 |
| 开发周期 | 6 周 | 8 周（含 buffer） | 更现实 |
| 检索公式 | 3 因子加权 | 2 因子（语义 + 时间） | 先跑通再优化 |
