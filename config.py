"""
secret-ai-perun: Intelligent Crypto Trading Bot

This module is part of the secret-ai-perun project, which analyzes social media sentiment,
news, and market data using Llama 3.1 70B to make cryptocurrency trading decisions.

Author: Alex H (alexh@scrtlabs.com)
License: MIT

Copyright (c) 2025 Alex H

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

DISCLAIMER:
This software is for educational purposes only. Cryptocurrency trading carries
significant risks, and past performance does not guarantee future results.
Use this software at your own risk. The author and contributors are not
responsible for any financial losses or damages resulting from the use of
this software.

Usage:
    [Module usage instructions here]

Example:
    [Code example here]

Dependencies:
    [List of key dependencies]
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from copy import deepcopy
from threading import Lock
import yaml
from functools import lru_cache
from settings import PERUN_CONFIG, PERUN_DIR_ENV

class ConfigDiscoveryError(Exception):
    """Raised when configuration file cannot be found, accessed, or validated.

    Attributes:
        component -- identifier of the failing component ('config', 'path', etc.)
        message -- detailed error explanation
        details -- optional additional context (paths searched, validation errors, etc.)
    """
    def __init__(self, component: str, message: str, details: str = None):
        self.component = component
        self.message = message
        self.details = details
        formatted_message = f"{message}"
        if details:
            formatted_message += f"\nDetails: {details}"
        super().__init__(formatted_message)

class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be parsed."""
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(message if details is None else f"{message}: {details}")

class Config:
    _instance = None
    _config: Dict[str, Any] = {}
    _instance_lock = Lock()  # For singleton creation
    _config_lock = Lock()    # For config loading
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._config_lock:
                if not self._initialized:
                    self._initialized = True

    @classmethod
    @lru_cache(maxsize=1)
    def load_config(cls, config_path: str = None) -> 'Config':
        if not cls._config:
            with cls._config_lock:
                if not cls._config:
                    if config_path is None:
                        config_path = find_config_file()
                    try:
                        cls._config = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
                    except yaml.YAMLError as e:
                        raise ConfigurationError("Failed to parse config file", str(e)) from e
                    except OSError as e:
                        raise ConfigDiscoveryError(str(config_path), f"Failed to read config file: {e}") from e
        return cls()
   
    def get_value(self, path: str, default = None) -> any:
        """
        Retrieve a value from a nested dictionary using dot notation path.
        
        Args:
            path (str): Dot-separated path to the desired value (e.g., 'web_search.parsing.api_key')
        
        Returns:
            any: The value if found, None otherwise
        
        Example:
            >>> cfg = {'web_search': {'parsing': {'api_key': 'abc123'}}}
            >>> get_value('web_search.parsing.api_key')
            'abc123'
            >>> get_value(cfg, 'invalid.path')
            None
        """
        current = self._config
        for key in path.split('.'):
            if not isinstance(current, dict):
                return None
            current = current.get(key, default)
            if current is None:
                return None
        return current

    def get(self, key: str, default: Any = None) -> Any:
        """Safely retrieve configuration value."""
        try:
            path = key.split('.')
            value = self._config
            for k in path:
                value = value[k]
            return deepcopy(value)
        except (KeyError, TypeError):
            return default

    def get_config(self) -> Dict[str, Any]:
        """Return deep copy of entire configuration."""
        return deepcopy(self._config)

@lru_cache(maxsize=1)
def discover_project_root() -> Path:
    current_dir = Path.cwd()
    markers = ['.git', 'pyproject.toml', 'setup.py', 'src']

    while current_dir != current_dir.parent:
        if any((current_dir / marker).exists() for marker in markers):
            return current_dir
        current_dir = current_dir.parent

    raise ConfigDiscoveryError(str(current_dir), "Unable to determine project root directory")

def find_config_file(filename: str = PERUN_CONFIG) -> Path:
    search_paths = []

    if ai2_root := os.getenv(PERUN_DIR_ENV):
        search_paths.append(Path(ai2_root) / filename)

    try:
        project_root = discover_project_root()
        search_paths.extend([
            project_root / filename,
            project_root / "config" / filename
        ])
    except ConfigDiscoveryError:
        pass

    search_paths.append(Path.cwd() / filename)

    for path in search_paths:
        if path.is_file():
            return path

    raise ConfigDiscoveryError("config", 
        f"Configuration file '{filename}' not found. Searched:\n" +
        "\n".join(f"  - {p}" for p in search_paths))