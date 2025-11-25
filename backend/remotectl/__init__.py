# -*- coding: utf-8 -*-
"""
Remote Control Module for Ollama Management

This module provides tools for managing remote Ollama instances:
- Model creation and management
- Server monitoring
- Resource optimization
"""

from .client import RemoteOllamaClient
from .model_manager import ModelManager

__all__ = ['RemoteOllamaClient', 'ModelManager']
