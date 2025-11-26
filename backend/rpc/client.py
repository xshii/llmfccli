"""
JSON-RPC Client for VSCode Communication

Sends requests to VSCode extension and receives responses via stdin/stdout.
"""

import json
import sys
import threading
import time
from typing import Dict, Any, Optional, Callable
from queue import Queue


class JsonRpcClient:
    """JSON-RPC client for communicating with VSCode extension"""

    def __init__(self):
        self.request_id = 0
        self.pending_requests: Dict[int, Queue] = {}
        self.response_listener_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        """Start the response listener thread"""
        if self.running:
            return

        self.running = True
        self.response_listener_thread = threading.Thread(
            target=self._listen_for_responses,
            daemon=True
        )
        self.response_listener_thread.start()

    def stop(self):
        """Stop the response listener thread"""
        self.running = False
        if self.response_listener_thread:
            self.response_listener_thread.join(timeout=1.0)

    def _listen_for_responses(self):
        """Listen for JSON-RPC responses from stdin"""
        while self.running:
            try:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    time.sleep(0.01)
                    continue

                line = line.strip()
                if not line or not line.startswith('{'):
                    continue

                # Parse JSON-RPC response
                response = json.loads(line)
                if 'id' not in response:
                    continue

                request_id = response['id']
                with self.lock:
                    if request_id in self.pending_requests:
                        self.pending_requests[request_id].put(response)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                import os
                if os.getenv('DEBUG_AGENT'):
                    print(f"[RPC CLIENT] Error reading response: {e}", file=sys.stderr)

    def send_request(self, method: str, params: Any, timeout: float = 10.0) -> Any:
        """
        Send JSON-RPC request and wait for response

        Args:
            method: Method name
            params: Method parameters
            timeout: Timeout in seconds

        Returns:
            Response result

        Raises:
            TimeoutError: If no response within timeout
            Exception: If response contains error
        """
        with self.lock:
            self.request_id += 1
            request_id = self.request_id

        # Create response queue
        response_queue: Queue = Queue()
        with self.lock:
            self.pending_requests[request_id] = response_queue

        # Build request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        try:
            # Send request to stdout (VSCode extension reads from our stdout)
            json_str = json.dumps(request)
            print(json_str, flush=True)

            # Debug logging
            import os
            if os.getenv('DEBUG_AGENT'):
                print(f"[RPC CLIENT] Sent request: {method}", file=sys.stderr)

            # Wait for response
            try:
                response = response_queue.get(timeout=timeout)
            except:
                raise TimeoutError(f"No response for method '{method}' after {timeout}s")

            # Check for error
            if 'error' in response:
                error = response['error']
                raise Exception(f"RPC Error: {error.get('message', 'Unknown error')}")

            # Return result
            return response.get('result')

        finally:
            # Clean up
            with self.lock:
                self.pending_requests.pop(request_id, None)


# Global client instance
_rpc_client: Optional[JsonRpcClient] = None


def get_client() -> JsonRpcClient:
    """Get or create global RPC client"""
    global _rpc_client
    if _rpc_client is None:
        _rpc_client = JsonRpcClient()
        _rpc_client.start()
    return _rpc_client


def is_vscode_mode() -> bool:
    """Check if running in VSCode integration mode"""
    import os
    return os.getenv('VSCODE_INTEGRATION', '').lower() == 'true'


def send_vscode_request(method: str, params: Any = None, timeout: float = 10.0) -> Any:
    """
    Send request to VSCode extension

    Args:
        method: Method name
        params: Method parameters
        timeout: Timeout in seconds

    Returns:
        Response result
    """
    if not is_vscode_mode():
        raise RuntimeError("Not in VSCode integration mode")

    client = get_client()
    return client.send_request(method, params or {}, timeout)
