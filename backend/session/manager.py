# -*- coding: utf-8 -*-
"""
Session manager for saving and resuming conversation sessions
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class SessionData:
    """会话数据"""
    id: str
    project_root: str
    created_at: str
    updated_at: str
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    active_files: List[str] = field(default_factory=list)
    role_id: str = "programmer"
    summary: str = ""
    message_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        return cls(**data)


class SessionManager:
    """会话管理器 - 保存和恢复会话"""

    def __init__(self, project_root: str):
        """
        初始化会话管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root).resolve()
        self._project_hash = self._hash_path(str(self.project_root))

        # 会话存储目录: ~/.claude-qwen/sessions/{project_hash}/
        self._sessions_dir = Path.home() / '.claude-qwen' / 'sessions' / self._project_hash
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话
        self._current_session: Optional[SessionData] = None

    def _hash_path(self, path: str) -> str:
        """生成路径的短哈希值"""
        return hashlib.md5(path.encode()).hexdigest()[:12]

    def _get_session_file(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self._sessions_dir / f'{session_id}.json'

    def _generate_session_id(self) -> str:
        """生成会话 ID (简短格式: MMDD_HHMMSS)"""
        timestamp = datetime.now().strftime('%m%d_%H%M%S')
        return timestamp

    def _generate_summary(self, history: List[Dict[str, Any]], max_length: int = 80) -> str:
        """从对话历史生成摘要"""
        # 找第一条用户消息作为摘要
        for msg in history:
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                # 清理 system-reminder 标签
                import re
                content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.DOTALL)
                content = content.strip()
                if content:
                    if len(content) > max_length:
                        return content[:max_length - 3] + '...'
                    return content
        return "空会话"

    def create_session(self) -> SessionData:
        """创建新会话"""
        now = datetime.now().isoformat()
        session = SessionData(
            id=self._generate_session_id(),
            project_root=str(self.project_root),
            created_at=now,
            updated_at=now
        )
        self._current_session = session
        return session

    def save_session(
        self,
        conversation_history: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]] = None,
        active_files: List[str] = None,
        role_id: str = "programmer"
    ) -> Optional[str]:
        """
        保存当前会话

        Args:
            conversation_history: 对话历史
            tool_calls: 工具调用记录
            active_files: 活动文件列表
            role_id: 当前角色 ID

        Returns:
            会话 ID，如果保存失败返回 None
        """
        if not conversation_history:
            return None

        # 创建或更新会话
        if self._current_session is None:
            self.create_session()

        session = self._current_session
        session.conversation_history = conversation_history
        session.tool_calls = tool_calls or []
        session.active_files = active_files or []
        session.role_id = role_id
        session.updated_at = datetime.now().isoformat()
        session.message_count = len([m for m in conversation_history if m.get('role') == 'user'])
        session.summary = self._generate_summary(conversation_history)

        # 保存到文件
        try:
            session_file = self._get_session_file(session.id)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            return session.id
        except Exception as e:
            print(f"保存会话失败: {e}")
            return None

    def list_sessions(self, limit: int = 10) -> List[SessionData]:
        """
        列出最近的会话

        Args:
            limit: 最多返回数量

        Returns:
            会话列表（按时间倒序）
        """
        sessions = []

        for session_file in self._sessions_dir.glob('*.json'):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append(SessionData.from_dict(data))
            except Exception:
                continue

        # 按更新时间倒序排序
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return sessions[:limit]

    def load_session(self, session_id: str) -> Optional[SessionData]:
        """
        加载指定会话

        Args:
            session_id: 会话 ID

        Returns:
            会话数据，如果不存在返回 None
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                session = SessionData.from_dict(data)
                self._current_session = session
                return session
        except Exception as e:
            print(f"加载会话失败: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """
        删除指定会话

        Args:
            session_id: 会话 ID

        Returns:
            是否删除成功
        """
        session_file = self._get_session_file(session_id)

        if session_file.exists():
            try:
                session_file.unlink()
                if self._current_session and self._current_session.id == session_id:
                    self._current_session = None
                return True
            except Exception:
                return False
        return False

    def get_latest_session(self) -> Optional[SessionData]:
        """获取最新的会话"""
        sessions = self.list_sessions(limit=1)
        return sessions[0] if sessions else None

    def clear_old_sessions(self, keep_count: int = 20):
        """
        清理旧会话，只保留最近的 N 个

        Args:
            keep_count: 保留的会话数量
        """
        sessions = self.list_sessions(limit=100)

        if len(sessions) > keep_count:
            for session in sessions[keep_count:]:
                self.delete_session(session.id)

    @property
    def current_session_id(self) -> Optional[str]:
        """获取当前会话 ID"""
        return self._current_session.id if self._current_session else None

    @property
    def sessions_dir(self) -> Path:
        """获取会话存储目录"""
        return self._sessions_dir


# 全局单例
_session_manager: Optional[SessionManager] = None


def get_session_manager(project_root: str = None) -> SessionManager:
    """
    获取会话管理器单例

    Args:
        project_root: 项目根目录（首次调用时必须提供）

    Returns:
        SessionManager 实例
    """
    global _session_manager

    if _session_manager is None:
        if project_root is None:
            raise ValueError("首次调用必须提供 project_root")
        _session_manager = SessionManager(project_root)
    elif project_root and str(Path(project_root).resolve()) != str(_session_manager.project_root):
        # 项目根目录变更，重新创建
        _session_manager = SessionManager(project_root)

    return _session_manager
