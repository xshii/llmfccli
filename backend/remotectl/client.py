# -*- coding: utf-8 -*-
"""
Remote Ollama Client for SSH-based operations
"""

import subprocess
import json
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import yaml


class RemoteOllamaClient:
    """Client for remote Ollama operations via SSH"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize remote Ollama client

        Args:
            config_path: Path to ollama.yaml config file
        """
        if config_path is None:
            config_path = str(Path(__file__).parent.parent.parent / "config" / "ollama.yaml")

        self.config_path = config_path
        self.config = self._load_config()

        # SSH configuration
        self.ssh_enabled = self.config.get('ssh', {}).get('enabled', False)
        self.ssh_host = self.config.get('ssh', {}).get('host', 'ollama-tunnel')
        self.ssh_user = self.config.get('ssh', {}).get('user')

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return {}

    def _ssh_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute command on remote server via SSH

        Args:
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.ssh_enabled:
            # Try local execution
            return self._local_command(command, timeout)

        # Build SSH command
        if self.ssh_user:
            ssh_target = f"{self.ssh_user}@{self.ssh_host}"
        else:
            ssh_target = self.ssh_host

        ssh_cmd = ['ssh', ssh_target, command]

        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"SSH command timeout after {timeout}s"
        except FileNotFoundError:
            return False, "", "SSH command not found. Please install openssh-client"
        except Exception as e:
            return False, "", str(e)

    def _local_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute command locally

        Args:
            command: Command to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ['bash', '-c', command],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timeout after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def list_models(self) -> Tuple[bool, list]:
        """
        List all available models

        Returns:
            Tuple of (success, models_list)
        """
        success, stdout, stderr = self._ssh_command("ollama list")

        if not success:
            return False, []

        # Parse output
        models = []
        lines = stdout.strip().split('\n')

        # Skip header line
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 1:
                    models.append({
                        'name': parts[0],
                        'raw': line.strip()
                    })

        return True, models

    def show_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Show model details

        Args:
            model_name: Model name (e.g., "qwen3:latest")

        Returns:
            Tuple of (success, modelfile_content)
        """
        success, stdout, stderr = self._ssh_command(
            f"ollama show {model_name} --modelfile"
        )

        if not success:
            return False, stderr

        return True, stdout

    def create_model(self, model_name: str, modelfile_content: str) -> Tuple[bool, str]:
        """
        Create custom model from Modelfile

        Args:
            model_name: Name for the new model
            modelfile_content: Content of the Modelfile

        Returns:
            Tuple of (success, output_message)
        """
        # Write Modelfile to temp location
        temp_modelfile = f"/tmp/Modelfile.{model_name.replace(':', '_')}"

        # Create Modelfile on remote server
        escaped_content = modelfile_content.replace('"', '\\"').replace('$', '\\$')
        write_cmd = f'cat > {temp_modelfile} << \'EOF\'\n{modelfile_content}\nEOF'

        success, stdout, stderr = self._ssh_command(write_cmd)
        if not success:
            return False, f"Failed to write Modelfile: {stderr}"

        # Create model
        create_cmd = f"ollama create {model_name} -f {temp_modelfile}"
        success, stdout, stderr = self._ssh_command(create_cmd, timeout=300)

        # Cleanup temp file
        self._ssh_command(f"rm -f {temp_modelfile}")

        if not success:
            return False, f"Failed to create model: {stderr}"

        return True, stdout

    def delete_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Delete a model

        Args:
            model_name: Model name to delete

        Returns:
            Tuple of (success, message)
        """
        success, stdout, stderr = self._ssh_command(f"ollama rm {model_name}")

        if not success:
            return False, stderr

        return True, f"Model {model_name} deleted successfully"

    def pull_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Pull a model from Ollama registry

        Args:
            model_name: Model name to pull

        Returns:
            Tuple of (success, output)
        """
        success, stdout, stderr = self._ssh_command(
            f"ollama pull {model_name}",
            timeout=600  # 10 minutes for large models
        )

        if not success:
            return False, stderr

        return True, stdout

    def check_health(self) -> Dict[str, Any]:
        """
        Check Ollama server health

        Returns:
            Dict with health status
        """
        # Check if ollama process is running
        success, stdout, stderr = self._ssh_command("pgrep -f 'ollama serve'")

        process_running = success and stdout.strip()

        # Try to list models (tests API connectivity)
        list_success, models = self.list_models()

        return {
            'process_running': bool(process_running),
            'api_accessible': list_success,
            'model_count': len(models) if list_success else 0,
            'healthy': process_running and list_success
        }
