# -*- coding: utf-8 -*-
"""
Token counter configuration loading
"""

import re
from pathlib import Path
from typing import Optional

import yaml


def parse_modelfile_num_ctx(modelfile_path: Path) -> Optional[int]:
    """
    Parse num_ctx from modelfile

    Args:
        modelfile_path: Path to the modelfile

    Returns:
        num_ctx value if found, None otherwise
    """
    try:
        if not modelfile_path.exists():
            return None

        with open(modelfile_path, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'PARAMETER\s+num_ctx\s+(\d+)', content)
        if match:
            return int(match.group(1))
        return None
    except Exception:
        return None


def get_max_tokens_from_modelfile(config_dir: Path) -> Optional[int]:
    """
    Get max_tokens from modelfile's num_ctx parameter

    Args:
        config_dir: Path to config directory

    Returns:
        num_ctx value if found, None otherwise
    """
    try:
        llm_config_path = config_dir / "llm.yaml"

        if not llm_config_path.exists():
            return None

        with open(llm_config_path, 'r', encoding='utf-8') as f:
            llm_config = yaml.safe_load(f)

        model_mgmt = llm_config.get('model_management', {})
        models = model_mgmt.get('models', [])

        if not models:
            return None

        for model in models:
            if model.get('enabled', True):
                modelfile_rel = model.get('modelfile', '')
                if modelfile_rel:
                    modelfile_path = config_dir / modelfile_rel
                    num_ctx = parse_modelfile_num_ctx(modelfile_path)
                    if num_ctx:
                        return num_ctx

        return None
    except Exception:
        return None


def load_token_budget_config(config_path: Optional[Path] = None) -> dict:
    """
    Load token budget configuration

    Args:
        config_path: Path to token_budget.yaml

    Returns:
        Configuration dict
    """
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    # Default config
    return {
        'token_management': {
            'budgets': {
                'active_files': 0.25,
                'processed_files': 0.15,
                'project_structure': 0.05,
                'compressed_history': 0.30,
                'recent_messages': 0.25
            },
            'compression': {
                'trigger_threshold': 0.85,
                'min_interval': 300,
                'max_retries': 2,
                'target_after_compress': 0.6
            },
            'limits': {
                'max_file_size': 10000,
                'max_compile_output': 2000,
                'max_tool_result': 5000
            }
        }
    }
