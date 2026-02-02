# -*- coding: utf-8 -*-
"""
重试逻辑模块
"""

import time
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar('T')


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2,
        initial_delay: float = 1
    ):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'RetryConfig':
        """从字典创建配置"""
        return cls(
            max_attempts=config.get('max_attempts', 3),
            backoff_factor=config.get('backoff_factor', 2),
            initial_delay=config.get('initial_delay', 1)
        )


def with_retry(
    func: Callable[[], T],
    config: RetryConfig,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
) -> T:
    """
    带重试的函数执行

    Args:
        func: 要执行的函数
        config: 重试配置
        on_retry: 重试回调 (attempt, exception, delay)

    Returns:
        函数返回值

    Raises:
        RuntimeError: 所有重试都失败
    """
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if attempt < config.max_attempts - 1:
                delay = config.initial_delay * (config.backoff_factor ** attempt)

                if on_retry:
                    on_retry(attempt + 1, e, delay)
                else:
                    print(f"Request failed (attempt {attempt + 1}/{config.max_attempts}), "
                          f"retrying in {delay}s: {e}")

                time.sleep(delay)

    raise RuntimeError(f"Request failed after {config.max_attempts} attempts: {last_exception}")


def retry_decorator(config: RetryConfig):
    """
    重试装饰器

    Args:
        config: 重试配置

    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            return with_retry(
                lambda: func(*args, **kwargs),
                config
            )
        return wrapper
    return decorator
