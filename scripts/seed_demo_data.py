"""Seed demo data for LifeOS demonstration.

Creates:
- Default user profile
- Sample tasks (pending/in_progress/done)
- Sample memories (profile + episodic)
- Chroma vector embeddings for memories

Usage:
    python scripts/seed_demo_data.py
"""

import json
import sqlite3
import uuid
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "lifeos.db"

# ---------------------------------------------------------------------------
# Demo tasks
# ---------------------------------------------------------------------------

DEMO_TASKS = [
    {"title": "完成 Agent 系统架构设计文档", "priority": "high", "status": "done"},
    {"title": "实现 Memory Agent 的混合检索", "priority": "high", "status": "done"},
    {"title": "编写 Planner Agent 单元测试", "priority": "medium", "status": "in_progress"},
    {"title": "接入真实搜索 API (Tavily)", "priority": "medium", "status": "pending"},
    {"title": "优化前端调试面板 UI", "priority": "low", "status": "pending"},
    {"title": "准备面试 Demo 演示脚本", "priority": "urgent", "status": "pending"},
    {"title": "阅读 LangGraph 高级用法文档", "priority": "medium", "status": "pending"},
    {"title": "部署项目到云服务器", "priority": "low", "status": "pending"},
]

# ---------------------------------------------------------------------------
# Demo memories
# ---------------------------------------------------------------------------

DEMO_MEMORIES = [
    {
        "memory_type": "profile",
        "tags": '["identity", "preference"]',
        "content": "用户是一名后端开发工程师，正在转型 AI Agent 方向，目标是中小厂的 Agent/AI 应用开发岗位",
        "summary": "后端工程师，转型AI Agent方向",
    },
    {
        "memory_type": "profile",
        "tags": '["habit", "preference"]',
        "content": "用户喜欢在晚上 9 点到 12 点之间学习新技术，偏好实战项目驱动学习",
        "summary": "晚上学习，偏好实战驱动",
    },
    {
        "memory_type": "profile",
        "tags": '["preference"]',
        "content": "用户偏好使用 Python，熟悉 FastAPI、Pydantic、SQLAlchemy 等框架",
        "summary": "Python技术栈偏好",
    },
    {
        "memory_type": "episodic",
        "tags": '["goal"]',
        "content": "用户计划用 8 周时间完成 LifeOS 个人 Agent 系统项目，作为面试作品展示",
        "summary": "8周完成LifeOS项目，用于面试",
    },
    {
        "memory_type": "episodic",
        "tags": '["goal"]',
        "content": "用户想系统学习 AI Agent 开发，包括 LangGraph、RAG、Tool Calling 等核心技术",
        "summary": "系统学习AI Agent开发技术栈",
    },
    {
        "memory_type": "episodic",
        "tags": '["event"]',
        "content": "用户已完成 LifeOS 项目的 Orchestrator、Memory Agent、Planner、Executor、Tool Layer 的开发",
        "summary": "LifeOS核心模块开发完成",
    },
]


def seed_demo_data() -> None:
    """Insert demo data into the database."""
    if not DB_PATH.exists():
        print("Database not found. Run 'python scripts/init_db.py' first.")
        return

    conn = sqlite3.connect(str(DB_PATH))

    # Update default user profile
    conn.execute(
        """UPDATE user_profiles SET name = ?, role = ?, preferences_json = ?
           WHERE user_id = 'default_user'""",
        (
            "Demo User",
            "AI Agent Developer",
            json.dumps({"language": "zh", "study_time": "evening", "tech_stack": "python"}, ensure_ascii=False),
        ),
    )

    # Clear existing demo data
    conn.execute("DELETE FROM tasks WHERE user_id = 'default_user' AND source = 'demo_seed'")
    conn.execute("DELETE FROM memories WHERE user_id = 'default_user' AND source_turn_id = 'demo_seed'")

    # Insert tasks
    for task in DEMO_TASKS:
        conn.execute(
            "INSERT INTO tasks (id, user_id, title, priority, status, source) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "default_user", task["title"], task["priority"], task["status"], "demo_seed"),
        )
    print(f"Inserted {len(DEMO_TASKS)} demo tasks")

    # Insert memories
    memory_ids = []
    for mem in DEMO_MEMORIES:
        mid = str(uuid.uuid4())
        memory_ids.append((mid, mem["content"], mem))
        conn.execute(
            "INSERT INTO memories (id, user_id, memory_type, tags, content, summary, source_turn_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (mid, "default_user", mem["memory_type"], mem["tags"], mem["content"], mem["summary"], "demo_seed"),
        )
    print(f"Inserted {len(DEMO_MEMORIES)} demo memories")

    conn.commit()
    conn.close()

    # Index memories in Chroma
    try:
        from backend.app.memory.vector import add_memory_embedding

        for mid, content, mem in memory_ids:
            add_memory_embedding(
                memory_id=mid,
                content=content,
                metadata={
                    "user_id": "default_user",
                    "memory_type": mem["memory_type"],
                    "tags": mem["tags"],
                    "summary": mem["summary"],
                },
            )
        print(f"Indexed {len(memory_ids)} memories in Chroma")
    except Exception as e:
        print(f"Warning: Chroma indexing failed (run from project root): {e}")

    print("\nDemo data seeded successfully!")
    print("Start the backend and try these prompts:")
    print('  - "帮我规划一下明天的工作"')
    print('  - "记住我最近在准备面试"')
    print('  - "搜一下最新的AI Agent开发趋势"')
    print('  - "我有哪些待办事项？"')


if __name__ == "__main__":
    seed_demo_data()
