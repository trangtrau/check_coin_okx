"""Crypto Monitor Modules Package

This package contains all the modules for the cryptocurrency price monitoring application.
"""

__version__ = "1.0.0"
__author__ = "Crypto Monitor Team"

# Import main modules
from .crypto_monitor import CryptoMonitor
from .web_monitor import create_app
from .config_manager import ConfigManager
from .ntfy_manager import NTFYManager
from .price_manager import PriceManager

# Export all modules
__all__ = [
    'CryptoMonitor',
    'create_app', 
    'ConfigManager',
    'NTFYManager',
    'PriceManager'
] 