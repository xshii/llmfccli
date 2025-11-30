"""
JSON-RPC Client for VSCode Communication (Socket Mode)

通过 Unix Socket 与 VSCode extension 通信
定期心跳检测连接状态
"""

import json
import socket
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from queue import Queue, Empty


# 默认 socket 路径
DEFAULT_SOCKET_PATH = "/tmp/claude-qwen.sock"


class SocketRpcClient:
    """基于 Socket 的 JSON-RPC 客户端"""

    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH, heartbeat_interval: float = 5.0):
        """
        初始化 Socket RPC 客户端

        Args:
            socket_path: Unix socket 路径
            heartbeat_interval: 心跳检测间隔（秒）
        """
        self.socket_path = socket_path
        self.heartbeat_interval = heartbeat_interval

        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._running = False
        self._lock = threading.Lock()

        self._request_id = 0
        self._pending_requests: Dict[int, Queue] = {}

        self._heartbeat_thread: Optional[threading.Thread] = None
        self._receiver_thread: Optional[threading.Thread] = None

    def start(self):
        """启动客户端（心跳线程）"""
        if self._running:
            return

        self._running = True

        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="rpc-heartbeat"
        )
        self._heartbeat_thread.start()

    def stop(self):
        """停止客户端"""
        self._running = False
        self._disconnect()

        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1.0)
        if self._receiver_thread:
            self._receiver_thread.join(timeout=1.0)

    def is_connected(self) -> bool:
        """检查是否已连接到 extension"""
        return self._connected

    def _heartbeat_loop(self):
        """心跳循环：定期尝试连接或验证连接"""
        while self._running:
            if not self._connected:
                # 未连接，尝试连接
                self._try_connect()
            else:
                # 已连接，发送心跳验证连接是否有效
                self._send_heartbeat()

            time.sleep(self.heartbeat_interval)

    def _send_heartbeat(self):
        """发送心跳请求验证连接"""
        try:
            # 发送 ping 请求，超时 2 秒
            self.send_request("ping", timeout=2.0)
        except Exception:
            # 心跳失败，断开连接（下次循环会尝试重连）
            self._disconnect()

    def _try_connect(self) -> bool:
        """尝试连接到 extension socket"""
        with self._lock:
            if self._connected:
                return True

            # 检查 socket 文件是否存在
            if not Path(self.socket_path).exists():
                return False

            try:
                self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._socket.settimeout(2.0)
                self._socket.connect(self.socket_path)
                self._socket.settimeout(None)
                self._connected = True

                # 启动接收线程
                self._receiver_thread = threading.Thread(
                    target=self._receive_loop,
                    daemon=True,
                    name="rpc-receiver"
                )
                self._receiver_thread.start()

                return True

            except (socket.error, OSError):
                self._disconnect_internal()
                return False

    def _disconnect(self):
        """断开连接"""
        with self._lock:
            self._disconnect_internal()

    def _disconnect_internal(self):
        """断开连接（内部方法，需在锁内调用）"""
        self._connected = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _receive_loop(self):
        """接收响应循环"""
        buffer = b""  # 使用字节缓冲区

        while self._running and self._connected:
            try:
                if not self._socket:
                    break

                data = self._socket.recv(4096)
                if not data:
                    # 连接断开
                    self._disconnect()
                    break

                buffer += data

                # 处理完整的 JSON 行（按换行符分割）
                while b'\n' in buffer:
                    line_bytes, buffer = buffer.split(b'\n', 1)

                    try:
                        line = line_bytes.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        # 解码失败，跳过这行
                        continue

                    if not line:
                        continue

                    try:
                        response = json.loads(line)
                        self._handle_response(response)
                    except json.JSONDecodeError:
                        continue

            except socket.timeout:
                continue
            except (socket.error, OSError):
                self._disconnect()
                break

    def _handle_response(self, response: Dict[str, Any]):
        """处理收到的响应"""
        request_id = response.get('id')
        if request_id is None:
            return

        with self._lock:
            if request_id in self._pending_requests:
                self._pending_requests[request_id].put(response)

    def send_request(self, method: str, params: Any = None, timeout: float = 10.0) -> Any:
        """
        发送 JSON-RPC 请求

        Args:
            method: 方法名
            params: 参数
            timeout: 超时时间（秒）

        Returns:
            响应结果

        Raises:
            ConnectionError: 未连接到 extension
            TimeoutError: 请求超时
            Exception: RPC 错误
        """
        if not self._connected:
            raise ConnectionError("Not connected to VSCode extension")

        with self._lock:
            self._request_id += 1
            request_id = self._request_id

        # 创建响应队列
        response_queue: Queue = Queue()
        with self._lock:
            self._pending_requests[request_id] = response_queue

        try:
            # 构建请求
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {}
            }

            # 发送请求
            request_json = json.dumps(request) + '\n'
            with self._lock:
                if not self._socket:
                    raise ConnectionError("Socket disconnected")
                self._socket.sendall(request_json.encode('utf-8'))

            # 等待响应
            try:
                response = response_queue.get(timeout=timeout)
            except Empty:
                raise TimeoutError(f"No response for '{method}' after {timeout}s")

            # 检查错误
            if 'error' in response:
                error = response['error']
                raise Exception(f"RPC Error: {error.get('message', 'Unknown error')}")

            return response.get('result')

        finally:
            with self._lock:
                self._pending_requests.pop(request_id, None)


# 全局客户端实例
_client: Optional[SocketRpcClient] = None


def get_client() -> SocketRpcClient:
    """获取全局 RPC 客户端"""
    global _client
    if _client is None:
        _client = SocketRpcClient()
        _client.start()
    return _client


def is_vscode_mode() -> bool:
    """检查是否连接到 VSCode extension"""
    return get_client().is_connected()


def send_vscode_request(method: str, params: Any = None, timeout: float = 10.0) -> Any:
    """
    发送请求到 VSCode extension

    Args:
        method: 方法名
        params: 参数
        timeout: 超时时间（秒）

    Returns:
        响应结果
    """
    return get_client().send_request(method, params, timeout)
