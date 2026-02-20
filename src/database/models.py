"""
Camada de persistência — SQLite para tarefas, histórico e status.
"""

import sqlite3
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from config.settings import DATABASE_PATH


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Cria as tabelas se não existirem."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            telegram_message_id INTEGER,
            agent_slug TEXT NOT NULL,
            task_description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            result TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            agent_slug TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(telegram_user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_history_user_agent
            ON conversation_history(telegram_user_id, agent_slug);
    """)
    conn.commit()
    conn.close()


def create_task(
    user_id: int,
    message_id: int | None,
    agent_slug: str,
    description: str,
) -> int:
    """Cria uma nova tarefa e retorna o ID."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO tasks
           (telegram_user_id, telegram_message_id, agent_slug,
            task_description, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            message_id,
            agent_slug,
            description,
            TaskStatus.PENDING.value,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id


def update_task_status(
    task_id: int,
    status: TaskStatus,
    result: str | None = None,
    error: str | None = None,
):
    """Atualiza o status de uma tarefa."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    if status == TaskStatus.IN_PROGRESS:
        conn.execute(
            "UPDATE tasks SET status=?, started_at=? WHERE id=?",
            (status.value, now, task_id),
        )
    elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        conn.execute(
            "UPDATE tasks SET status=?, result=?, error=?, completed_at=? WHERE id=?",
            (status.value, result, error, now, task_id),
        )
    else:
        conn.execute(
            "UPDATE tasks SET status=? WHERE id=?",
            (status.value, task_id),
        )

    conn.commit()
    conn.close()


def get_task(task_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_tasks(user_id: int, limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE telegram_user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_tasks(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM tasks
           WHERE telegram_user_id=? AND status IN ('pending', 'in_progress')
           ORDER BY created_at DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_conversation_message(
    user_id: int, agent_slug: str, role: str, content: str
):
    conn = get_connection()
    conn.execute(
        """INSERT INTO conversation_history
           (telegram_user_id, agent_slug, role, content, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, agent_slug, role, content, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def get_conversation_history(
    user_id: int, agent_slug: str, limit: int = 10
) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content FROM conversation_history
           WHERE telegram_user_id=? AND agent_slug=?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, agent_slug, limit),
    ).fetchall()
    conn.close()
    # Retorna em ordem cronológica
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def clear_conversation_history(user_id: int, agent_slug: str | None = None):
    conn = get_connection()
    if agent_slug:
        conn.execute(
            "DELETE FROM conversation_history WHERE telegram_user_id=? AND agent_slug=?",
            (user_id, agent_slug),
        )
    else:
        conn.execute(
            "DELETE FROM conversation_history WHERE telegram_user_id=?",
            (user_id,),
        )
    conn.commit()
    conn.close()
