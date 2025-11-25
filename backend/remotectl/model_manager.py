# -*- coding: utf-8 -*-
"""
Model Manager for Ollama custom models
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

from .client import RemoteOllamaClient


class ModelManager:
    """Manage Ollama custom models"""

    def __init__(self, client: Optional[RemoteOllamaClient] = None):
        """
        Initialize model manager

        Args:
            client: RemoteOllamaClient instance (optional)
        """
        self.client = client or RemoteOllamaClient()
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"

        # Load model management config
        config_path = self.config_dir / "ollama.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        self.model_config = config.get('model_management', {})

    def sync_claude_qwen_model(self) -> bool:
        """
        Sync claude-qwen custom model from Modelfile
        (Legacy method - uses first enabled model from config)

        Returns:
            True if successful
        """
        # Find claude-qwen model in config
        models = self.model_config.get('models', [])
        claude_qwen_def = next(
            (m for m in models if m.get('name') == 'claude-qwen:latest' and m.get('enabled', True)),
            None
        )

        if not claude_qwen_def:
            print("Error: claude-qwen:latest not found in config")
            return False

        return self._sync_model(claude_qwen_def)

    def _sync_model(self, model_def: Dict[str, Any]) -> bool:
        """
        Sync a single model from its definition

        Args:
            model_def: Model definition dict from config

        Returns:
            True if successful
        """
        model_name = model_def.get('name')
        modelfile_rel_path = model_def.get('modelfile')

        if not model_name or not modelfile_rel_path:
            print(f"Error: Invalid model definition: {model_def}")
            return False

        # Resolve modelfile path (relative to config dir)
        modelfile_path = self.config_dir / modelfile_rel_path

        if not modelfile_path.exists():
            print(f"Error: Modelfile not found at {modelfile_path}")
            return False

        # Read Modelfile
        with open(modelfile_path, 'r', encoding='utf-8') as f:
            modelfile_content = f.read()

        print(f"Creating {model_name} model...")

        # Create model
        success, output = self.client.create_model(model_name, modelfile_content)

        if success:
            print(f"✓ Model {model_name} created successfully")
            if output:
                print(output)
        else:
            print(f"✗ Failed to create model {model_name}: {output}")

        return success

    def ensure_model_exists(self, model_name: str = "claude-qwen:latest") -> bool:
        """
        Ensure a model exists, create if not

        Args:
            model_name: Model name to check

        Returns:
            True if model exists or was created successfully
        """
        # Check if model exists
        success, models = self.client.list_models()

        if not success:
            print("Error: Cannot list models")
            return False

        # Check if our model exists
        model_exists = any(m['name'].startswith(model_name.split(':')[0]) for m in models)

        if model_exists:
            print(f"✓ Model {model_name} already exists")
            return True

        # Model doesn't exist, create it
        print(f"Model {model_name} not found, creating...")
        return self.sync_claude_qwen_model()

    def list_models(self) -> Dict[str, Any]:
        """
        List all models with details

        Returns:
            Dict with models information
        """
        success, models = self.client.list_models()

        if not success:
            return {
                'success': False,
                'models': [],
                'error': 'Failed to list models'
            }

        return {
            'success': True,
            'models': models,
            'count': len(models)
        }

    def show_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Show detailed model information

        Args:
            model_name: Model name

        Returns:
            Dict with model information
        """
        success, modelfile = self.client.show_model(model_name)

        if not success:
            return {
                'success': False,
                'error': modelfile
            }

        return {
            'success': True,
            'model_name': model_name,
            'modelfile': modelfile
        }

    def delete_model(self, model_name: str, confirm: bool = False) -> bool:
        """
        Delete a model

        Args:
            model_name: Model name to delete
            confirm: Require confirmation

        Returns:
            True if successful
        """
        if not confirm:
            print(f"Warning: This will delete model '{model_name}'")
            response = input("Continue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled")
                return False

        success, message = self.client.delete_model(model_name)

        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")

        return success

    def sync_all_models(self) -> Dict[str, bool]:
        """
        Sync all enabled models from config

        Returns:
            Dict mapping model names to success status
        """
        results = {}
        models = self.model_config.get('models', [])

        for model_def in models:
            if not model_def.get('enabled', True):
                continue

            model_name = model_def.get('name')
            if model_name:
                results[model_name] = self._sync_model(model_def)

        return results

    def ensure_base_models(self) -> Dict[str, bool]:
        """
        Ensure all base models exist, pull if needed

        Returns:
            Dict mapping base model names to success status
        """
        results = {}
        base_models = self.model_config.get('base_models', [])

        for base_model_def in base_models:
            registry_name = base_model_def.get('registry_name')
            local_name = base_model_def.get('local_name', registry_name)
            auto_pull = base_model_def.get('auto_pull', False)

            if not registry_name:
                continue

            # Check if model exists
            success, models = self.client.list_models()
            if not success:
                print(f"Error: Cannot check if {local_name} exists")
                results[local_name] = False
                continue

            model_exists = any(m['name'].startswith(local_name.split(':')[0]) for m in models)

            if model_exists:
                print(f"✓ Base model {local_name} already exists")
                results[local_name] = True
            elif auto_pull:
                print(f"Pulling base model {registry_name}...")
                pull_success, output = self.client.pull_model(registry_name)
                if pull_success:
                    print(f"✓ Base model {registry_name} pulled successfully")
                    results[local_name] = True
                else:
                    print(f"✗ Failed to pull {registry_name}: {output}")
                    results[local_name] = False
            else:
                print(f"⚠ Base model {local_name} not found (auto_pull disabled)")
                results[local_name] = False

        return results

    def update_from_config(self) -> Dict[str, Any]:
        """
        Update model parameters from config file

        Returns:
            Dict with update status
        """
        config_path = self.project_root / "config" / "ollama.yaml"

        if not config_path.exists():
            return {
                'success': False,
                'error': 'Config file not found'
            }

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        model_name = config.get('ollama', {}).get('model', 'claude-qwen:latest')
        generation_params = config.get('ollama', {}).get('generation', {})

        # Check if model exists
        success, models = self.client.list_models()
        model_exists = any(m['name'].startswith(model_name.split(':')[0]) for m in models) if success else False

        if not model_exists:
            return {
                'success': False,
                'error': f'Model {model_name} does not exist. Run sync_claude_qwen_model() first.'
            }

        return {
            'success': True,
            'model': model_name,
            'parameters': generation_params,
            'note': 'Parameters are set in Modelfile. To update, modify Modelfile and re-create model.'
        }
