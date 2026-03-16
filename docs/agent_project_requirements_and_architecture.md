# Agent 求职项目需求文档与架构设计

## 1. 文档信息

**项目名称**：LifeOS / Personal Agent OS  
**项目定位**：面向个人用户的主动式 AI 助理 Agent 系统  
**目标用途**：作为 Agent 开发工程师求职项目，重点展示系统架构设计、Agent 编排、记忆系统、工具调用与工程落地能力  
**目标周期**：1-2 个月  
**目标岗位**：中小厂业务型 Agent / AI 应用开发工程师

---

## 2. 项目背景

当前市面上的 AI 产品大多停留在“问一句、答一句”的被动交互模式。即使具备聊天、搜索、总结等能力，也往往缺乏以下关键能力：

1. 对用户长期状态的持续记忆
2. 对任务的多步骤规划与执行
3. 对工具的自主选择与调用
4. 在合适时机进行主动式提醒和辅助

本项目拟构建一个**个人 AI Agent 操作系统**，既不是单纯聊天机器人，也不是简单的任务助手，而是一个围绕用户生活与轻工作场景的 **Proactive Personal Agent**。

该系统的核心价值在于：

- 能理解用户目标与偏好
- 能基于长期记忆提供连续体验
- 能对任务进行规划、执行与总结
- 能结合日程、待办、搜索等工具完成闭环
- 能通过多 Agent 架构展示工程化能力

---

## 3. 项目目标

### 3.1 业务目标

构建一个可演示、可扩展、可讲解的 Agent 系统 Demo，用于在面试中证明以下能力：

- 具备 Agent 系统级架构设计能力
- 理解多 Agent 协同与职责拆分
- 能设计长期记忆和用户画像机制
- 能实现 Tool Calling 与任务执行闭环
- 能做出具备“主动性”的 Agent 产品形态

### 3.2 技术目标

1. 实现一个可运行的 Agent Orchestrator
2. 实现 Planner / Memory / Executor 等核心 Agent
3. 实现至少 3 个工具集成（如 Search / Calendar / Todo）
4. 实现短期记忆与长期记忆双层机制
5. 实现至少 2 个主动触发场景
6. 提供可视化交互界面与完整项目结构

### 3.3 面试展示目标

面试官看到项目后，能形成以下判断：

- 候选人不只是会调接口，而是能做完整 Agent 系统
- 候选人理解复杂业务中的模块解耦与流程编排
- 候选人具备较强的工程落地与架构思维

---

## 4. 产品定位

### 4.1 产品定义

LifeOS 是一个面向个人用户的 AI Agent 系统，围绕“生活管理 + 轻工作辅助”场景，提供：

- 自然语言交互
- 任务理解与拆解
- 长期用户记忆
- 工具调用与执行
- 主动提醒与建议

### 4.2 不做什么

为了保证 1-2 个月内可落地，本项目**不做**以下内容：

- 不做强社交属性的虚拟恋人产品
- 不做复杂多模态生成（如语音克隆、视频生成）
- 不做企业级权限体系
- 不做复杂工作流市场 / 插件平台
- 不做重度办公协同

### 4.3 核心定位语

> 一个拥有长期记忆、任务规划、工具执行和主动提醒能力的个人 AI Agent 系统。

---

## 5. 目标用户与使用场景

### 5.1 目标用户

首期目标用户为：

- 知识工作者
- 程序员 / 产品 / 运营等日常需要安排任务的人
- 希望获得更连续、更懂自己的 AI 助理用户

### 5.2 用户特征

- 日常任务较多，容易分心
- 有明确目标，但执行和规划不足
- 愿意通过对话方式管理任务和信息
- 希望 AI 不只是回答，而是协助推进事情

### 5.3 核心使用场景

#### 场景 A：工作规划

用户输入：
“帮我规划一下明天的工作安排。”

系统能力：
- 读取用户日程和待办
- 分析任务优先级
- 生成可执行时间块计划
- 输出建议性安排

#### 场景 B：长期目标追踪

用户输入：
“记住我最近想系统学习 AI Agent 开发。”

系统能力：
- 提取用户长期目标
- 写入长期记忆
- 后续在相关上下文中主动提及

#### 场景 C：信息辅助

用户输入：
“帮我找一下今天值得看的 AI 新闻。”

系统能力：
- 调用搜索工具
- 汇总信息
- 输出精简摘要和建议阅读顺序

#### 场景 D：情绪与状态关注

用户输入：
“我最近有点焦虑，事情太多了。”

系统能力：
- 识别情绪与压力来源
- 提供轻量建议
- 记录用户状态偏好
- 后续在规划中减少过载安排

#### 场景 E：主动提醒

系统主动输出：
- “你昨天提到想学习 Agent，我给你安排了今晚 30 分钟学习时间。”
- “你这周已经连续两天熬夜，今天建议把重要任务提前。”

---

## 6. 需求分析

### 6.1 核心问题陈述

用户需要的不是一个单纯能聊天的 AI，而是一个：

1. **能记住我是谁、最近在做什么、长期目标是什么** 的系统
2. **能把模糊需求转化成行动计划** 的系统
3. **能调用外部工具完成简单任务** 的系统
4. **能在合适时机主动提醒和辅助** 的系统

### 6.2 需求拆分

#### 6.2.1 用户需求

- 用自然语言管理任务
- 让 AI 记住个人偏好、目标和状态
- 让 AI 帮我做计划，而不是只给建议
- 让 AI 在必要时主动提醒
- 让 AI 通过工具获取外部信息

#### 6.2.2 产品需求

- 支持多轮对话
- 支持任务拆解
- 支持用户画像抽取
- 支持长短期记忆管理
- 支持工具编排
- 支持主动触发机制

#### 6.2.3 技术需求

- LLM 接入
- Agent 状态机 / 工作流编排
- Memory 存储层
- Tool 抽象层
- 任务日志与可观测性
- 前后端交互

---

## 7. 功能需求

### 7.1 功能总览

MVP 功能划分为 5 大模块：

1. 对话与意图理解模块
2. 任务规划模块
3. 记忆管理模块
4. 工具执行模块
5. 主动触发模块

---

### 7.2 功能模块详细说明

## 7.2.1 对话与意图理解模块

**目标**：理解用户输入，识别用户意图并决定后续流程。

**输入**：用户自然语言  
**输出**：结构化意图对象

**典型意图类型**：
- chat：普通闲聊
- plan_task：任务规划
- memory_write：记忆写入
- memory_query：历史偏好查询
- tool_request：工具请求
- emotional_support：情绪支持
- proactive_setup：主动任务设置

**需求点**：
- 支持多轮对话上下文
- 支持意图分类
- 支持参数抽取
- 支持模糊任务转结构化请求

---

## 7.2.2 Planner Agent 模块

**目标**：将用户需求拆解成可执行步骤。

**输入**：任务描述、用户上下文、记忆信息、工具能力列表  
**输出**：执行计划 Plan

**Plan 结构建议**：
- goal：目标
- constraints：约束
- required_tools：所需工具
- steps：步骤数组
- fallback：失败兜底方案

**示例**：

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
- 支持简单重规划
- 支持输出可执行中间态

---

## 7.2.3 Memory Agent 模块

**目标**：管理用户的短期上下文和长期画像。

**记忆类型**：

### A. 短期记忆

用于当前对话上下文：
- 最近 N 轮消息
- 当前任务状态
- 当前计划草稿

### B. 长期记忆

用于长期个性化：
- 用户基础画像
- 长期目标
- 偏好信息
- 历史行为特征
- 情绪趋势

**长期记忆分类建议**：
- Profile Memory：身份、职业、习惯
- Goal Memory：长期目标
- Preference Memory：偏好
- Episodic Memory：关键历史事件
- Emotional Memory：高频情绪特征

**需求点**：
- 支持记忆抽取
- 支持记忆写入
- 支持记忆检索
- 支持记忆摘要与去重
- 支持重要度评分

---

## 7.2.4 Executor Agent 模块

**目标**：根据 Planner 产出的计划执行具体步骤。

**职责**：
- 按步骤调度工具
- 收集执行结果
- 处理异常
- 汇总最终结果

**需求点**：
- 支持串行执行
- 支持简单条件判断
- 支持失败重试
- 支持执行日志输出

---

## 7.2.5 Tool Layer 模块

**目标**：为 Agent 提供统一工具能力抽象。

MVP 工具建议：

### Tool 1：Search Tool
- 搜索公开信息
- 返回摘要结果

### Tool 2：Calendar Tool
- 获取当天/明天日程
- 可扩展到创建提醒

### Tool 3：Todo Tool
- 新增待办
- 查询待办
- 更新待办状态

### Tool 4（可选）：Notes Tool
- 写入笔记 / 日志
- 保存计划结果

**工具统一接口建议**：
- name
- description
- input_schema
- execute(params)
- error_handler

---

## 7.2.6 Proactive Agent 模块

**目标**：实现系统主动行为，而非纯被动响应。

**触发类型**：

### A. 时间触发
- 每日早间总结
- 晚间复盘

### B. 状态触发
- 用户任务堆积较多
- 用户连续多天高压/熬夜
- 长期目标长时间未推进

### C. 事件触发
- 新增日程冲突
- 高优任务临近截止

**主动输出示例**：
- 今日重点事项提醒
- 基于目标的学习建议
- 基于最近状态的节奏建议

**需求点**：
- 支持规则触发
- 支持从记忆中提取用户状态
- 支持主动建议模板

---

## 7.2.7 可观测性模块

**目标**：方便演示与排查 Agent 工作流程。

**需记录内容**：
- 用户输入
- 意图识别结果
- 选中的 Agent
- Plan 内容
- 工具调用记录
- Memory 读写日志
- 最终回复

**展示方式**：
- 后端日志
- 调试面板
- LangGraph 可视化状态流（若支持）

---

## 8. 非功能需求

### 8.1 可扩展性

- 未来可新增更多工具
- 未来可新增更多 Agent
- 支持从单体流程升级为事件驱动

### 8.2 可维护性

- 模块职责清晰
- 统一接口抽象
- Agent 与 Tool 解耦
- 记忆存储层可替换

### 8.3 可演示性

- 支持本地一键启动
- 支持可视化展示流程
- 支持准备固定 Demo 脚本

### 8.4 性能要求

- 常规对话响应 < 5 秒
- 带工具调用复杂任务响应 < 15 秒
- 内部流程超时可降级到普通回答

### 8.5 安全与边界

- 不处理敏感隐私推断
- 不执行危险外部操作
- 工具调用采用白名单机制
- 用户数据本地存储或开发环境隔离

---

## 9. MVP 范围定义

### 9.1 必做功能

1. Chat UI
2. Agent Orchestrator
3. Intent Router
4. Planner Agent
5. Memory Agent
6. Executor Agent
7. Search Tool
8. Calendar Tool（可先 mock）
9. Todo Tool
10. 短期/长期记忆存储
11. 主动早报 / 学习提醒场景
12. 调试日志面板

### 9.2 可选增强功能

1. 情绪识别增强
2. 计划执行结果复盘
3. 周总结能力
4. Notion 集成
5. 邮件总结工具
6. 多用户支持

### 9.3 不纳入首期范围

1. 语音对话
2. 多模态图像理解
3. 企业协同
4. 复杂权限管理
5. 真正的自动外呼 / 自动发消息

---

## 10. 总体架构设计

### 10.1 架构设计原则

1. **职责单一**：每个 Agent 专注一个角色
2. **可编排**：Agent 间通过状态和任务流衔接
3. **可扩展**：工具和记忆存储可以替换
4. **可观测**：每一步可追踪
5. **面向演示**：结构足够清晰，便于面试讲解

### 10.2 总体逻辑架构

```text
[Frontend Chat UI]
        |
        v
[API Gateway / FastAPI]
        |
        v
[Agent Orchestrator]
   |         |          |
   |         |          |
   v         v          v
[Intent]  [Planner]  [Memory Manager]
   |                     |
   |                     v
   |               [Vector DB / SQL]
   |
   v
[Executor Agent]
   |
   v
[Tool Layer]
   |      |      |
   v      v      v
Search Calendar Todo
```

### 10.3 分层架构

#### 表现层
- Web Chat 界面
- 调试流程面板

#### 接入层
- FastAPI API
- 请求鉴权（可简化）

#### 编排层
- Agent Orchestrator
- Intent Router
- State Manager

#### 领域能力层
- Planner Agent
- Memory Agent
- Executor Agent
- Proactive Agent

#### 基础设施层
- LLM Provider
- PostgreSQL
- 向量库 / pgvector / Chroma
- Redis（可选）
- 外部工具接口

---

## 11. Agent 架构设计

### 11.1 Agent 列表

#### 1. Orchestrator Agent

**职责**：
- 接收用户输入
- 维护整体状态
- 调用下游 Agent
- 决定流程入口与出口

**输入**：用户请求  
**输出**：最终响应或执行流转

#### 2. Intent Router

**职责**：
- 识别用户意图类型
- 路由到对应流程

#### 3. Planner Agent

**职责**：
- 任务拆解
- 生成执行计划
- 选择工具

#### 4. Memory Agent

**职责**：
- 提取用户信息
- 检索相关记忆
- 维护长期画像

#### 5. Executor Agent

**职责**：
- 执行计划步骤
- 调用工具
- 汇总结果

#### 6. Proactive Agent

**职责**：
- 定期扫描状态
- 触发主动建议

#### 7. Emotion Analyzer（可选）

**职责**：
- 识别情绪倾向
- 给 Planner 和 Memory 提供状态信号

---

### 11.2 Agent 状态流转

```text
User Input
   |
   v
Intent Router
   |
   +--> chat --------------------------+
   |                                   |
   +--> memory_write --> Memory Agent  |
   |                                   |
   +--> plan_task -----> Planner ------+--> Executor --> Response
   |                                   |
   +--> tool_request --> Executor -----+
   |                                   |
   +--> emotional_support -> Memory/Emotion -> Response
```

---

## 12. 数据流设计

### 12.1 用户请求处理流程

1. 前端发送用户输入到后端
2. Orchestrator 创建会话状态
3. Intent Router 判断请求类型
4. Memory Agent 读取相关用户长期记忆
5. Planner Agent 生成计划（如有）
6. Executor Agent 调用相应工具
7. Memory Agent 对本轮进行记忆抽取
8. 最终回复返回前端
9. 调试链路写入日志

### 12.2 主动任务处理流程

1. 定时任务触发 Proactive Agent
2. 读取用户状态 / 日程 / 待办 / 长期目标
3. 判断是否满足触发规则
4. 生成主动建议
5. 推送到前端消息流或消息中心

---

## 13. 记忆系统设计

### 13.1 存储方案建议

#### 方案 A：PostgreSQL + pgvector
适合演示工程化能力，统一结构化 + 语义检索

#### 方案 B：PostgreSQL + Chroma
实现更快，适合 MVP

### 13.2 数据模型建议

#### user_profiles
- user_id
- name
- role
- preferences_json
- created_at
- updated_at

#### memories
- id
- user_id
- memory_type
- content
- summary
- importance_score
- embedding
- source_turn_id
- created_at

#### tasks
- id
- user_id
- title
- status
- priority
- due_time
- source
- created_at

#### sessions
- session_id
- user_id
- latest_context
- current_goal
- created_at

#### tool_logs
- id
- session_id
- tool_name
- input_payload
- output_payload
- status
- created_at

### 13.3 记忆写入策略

并非每轮对话都写长期记忆，只在满足以下条件时写入：

- 用户明确表达偏好/目标
- 用户状态具有长期意义
- 事件重要度较高
- 对未来决策可能有帮助

### 13.4 记忆检索策略

混合检索：
- 结构化筛选（memory_type / user_id）
- 向量召回（语义相似）
- 重要度加权排序
- 时间衰减

排序分数可参考：

`final_score = semantic_score * 0.5 + importance * 0.3 + recency * 0.2`

---

## 14. Tool 设计

### 14.1 Tool 抽象接口

```python
class BaseTool:
    name: str
    description: str
    input_schema: dict

    async def execute(self, params: dict) -> dict:
        pass
```

### 14.2 Search Tool

**输入**：query  
**输出**：搜索摘要列表

### 14.3 Calendar Tool

**输入**：date_range  
**输出**：指定日期日程

### 14.4 Todo Tool

**输入**：task / action  
**输出**：任务结果

### 14.5 Tool 调用策略

- 由 Planner 给出候选工具
- 由 Executor 具体调用
- 失败时返回可解释错误
- 工具输出统一转中间格式

---

## 15. 技术选型建议

### 15.1 推荐技术栈

#### 后端
- Python
- FastAPI
- Pydantic

#### Agent 编排
- LangGraph

#### 模型层
- OpenAI / Claude / DeepSeek API

#### 存储层
- PostgreSQL
- pgvector 或 Chroma
- Redis（可选）

#### 前端
- Next.js
- Tailwind
- 或先用 Streamlit 快速验证

#### 任务调度
- APScheduler / Celery（简化可先用 APScheduler）

#### 观测与日志
- Loguru / structlog
- LangSmith（可选）

### 15.2 选型理由

LangGraph 很适合展示：
- 显式状态流
- 节点编排
- 多分支流程
- Agent 工作流可解释性

这对面试讲架构非常友好。

---

## 16. 接口设计示例

### 16.1 对话接口

**POST** `/api/chat`

请求：
```json
{
  "user_id": "u1",
  "session_id": "s1",
  "message": "帮我规划一下明天的工作"
}
```

响应：
```json
{
  "reply": "我已经根据你的日程和待办整理了明天的工作安排...",
  "intent": "plan_task",
  "plan": {...},
  "tool_logs": [...]
}
```

### 16.2 主动消息接口

**GET** `/api/proactive/messages?user_id=u1`

### 16.3 记忆查看接口

**GET** `/api/memories?user_id=u1`

### 16.4 调试链路接口

**GET** `/api/debug/session/{session_id}`

---

## 17. GitHub 项目结构建议

```text
lifeos/
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   │   ├── orchestrator/
│   │   │   ├── planner/
│   │   │   ├── memory/
│   │   │   ├── executor/
│   │   │   └── proactive/
│   │   ├── tools/
│   │   ├── memory/
│   │   ├── models/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── core/
│   ├── tests/
│   └── main.py
├── docs/
│   ├── architecture.md
│   ├── prd.md
│   └── demo-script.md
├── scripts/
├── docker-compose.yml
└── README.md
```

---

## 18. 关键时序示例

### 18.1 用户规划任务时序

```text
User -> Frontend -> API -> Orchestrator
Orchestrator -> Intent Router
Intent Router -> Memory Agent (retrieve profile/goals)
Intent Router -> Planner Agent (make plan)
Planner Agent -> Executor Agent
Executor Agent -> Calendar Tool
Executor Agent -> Todo Tool
Executor Agent -> Orchestrator
Orchestrator -> Memory Agent (write key memory)
Orchestrator -> API -> Frontend -> User
```

---

## 19. 核心 Demo 场景设计

### Demo 1：规划明天工作
展示点：Planner + Calendar + Todo + Executor

### Demo 2：记住长期目标
展示点：长期记忆写入与提取

### Demo 3：AI 新闻搜索
展示点：Tool Calling + Summarization

### Demo 4：情绪压力识别
展示点：用户状态理解 + Memory 写入

### Demo 5：主动学习提醒
展示点：Proactive Agent + Goal Memory

---

## 20. 开发计划建议

### 第 1 周
- 初始化前后端框架
- 跑通基础聊天接口
- 定义核心数据结构

### 第 2 周
- 实现 Intent Router
- 实现 Memory Agent 基础版
- 建立数据库表结构

### 第 3 周
- 实现 Planner Agent
- 定义 Plan Schema
- 打通基本任务流程

### 第 4 周
- 接入 Search / Todo / Calendar Tool
- 实现 Executor Agent
- 完成一次完整工具调用闭环

### 第 5 周
- 实现 Proactive Agent
- 增加规则触发场景
- 加入调试日志和可视化

### 第 6 周
- 打磨前端交互
- 准备固定 Demo 数据
- 补充 README、架构图、面试讲稿

---

## 21. 风险与应对

### 风险 1：范围过大
**应对**：严格按 MVP 控制，优先保证规划、记忆、工具调用闭环

### 风险 2：工具接入复杂
**应对**：优先 mock Calendar / Todo，再逐步替换真实接口

### 风险 3：主动能力不稳定
**应对**：首期以规则驱动为主，不强依赖复杂自治逻辑

### 风险 4：项目看起来像聊天壳子
**应对**：重点展示状态流、Plan、Memory、Tool Logs、主动提醒

---

## 22. 面试讲解重点

在面试时应重点强调：

1. 为什么没有做“普通聊天机器人”，而是做“主动式 Agent 系统”
2. 为什么采用多 Agent 角色拆分，而不是一个巨型 Prompt
3. 记忆系统如何避免无脑堆上下文
4. Planner 和 Executor 如何解耦
5. 如何通过日志和状态流提升系统可解释性
6. 如果继续扩展，如何支持更多工具和更复杂工作流

---

## 23. 结论

这个项目的本质不是“做一个 AI 伴侣”，而是：

> 通过一个贴近用户的个人助理场景，构建一个具备长期记忆、任务规划、工具执行和主动行为能力的 Agent 系统。

它非常适合作为中小厂业务型 Agent 工程师求职项目，因为它同时具备：

- 明确的业务场景
- 清晰的系统架构
- 可展示的工程能力
- 可落地的 MVP 范围
- 容易准备高质量 Demo

如果后续继续迭代，可以进一步扩展为：
- 周报 Agent
- 学习规划 Agent
- 邮件助手 Agent
- 个人知识管理 Agent

这会让项目从一个 Demo，逐渐演进为一个真正的 Agent 平台雏形。

