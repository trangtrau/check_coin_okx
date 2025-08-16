"""
Configuration Management Module

Handles all configuration operations including loading, saving, and validation.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Manages application configuration including environment variables and JSON config."""
    
    def __init__(self, config_file: str = 'trading_config.json'):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = config_file
        self._load_environment()
        self._load_config()
    
    def _load_environment(self):
        """Load environment variables from .env file."""
        load_dotenv()
        
        # NTFY configuration for alerts
        self.ntfy_server = os.getenv('NTFY_SERVER', 'https://ntfy.sh')
        self.ntfy_topic = os.getenv('NTFY_TOPIC', 'crypto_alerts')
        self.ntfy_password = os.getenv('NTFY_PASSWORD', '')
        
        # Application settings
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', '5000'))
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # Load trading pairs for price monitoring
                    self.trading_pairs = config.get('trading_pairs', [])
                    
                    # Load NTFY configuration
                    ntfy_config = config.get('ntfy_config', {})
                    self.ntfy_server = ntfy_config.get('server', self.ntfy_server)
                    self.ntfy_topic = ntfy_config.get('topic', self.ntfy_topic)
                    
                    # Load price thresholds for alerts
                    raw_thresholds = config.get('thresholds', {})
                    self.price_thresholds = {}
                    
                    for pair, thresholds in raw_thresholds.items():
                        if isinstance(thresholds, dict):
                            # Ensure proper data structure for alerts
                            self.price_thresholds[pair] = {
                                'upper': float(thresholds.get('upper', 0)),
                                'lower': float(thresholds.get('lower', 0))
                            }
                        else:
                            print(f"Warning: Invalid thresholds format for {pair}")
                    
                    print(f"Loaded {len(self.trading_pairs)} trading pairs for price monitoring")
                    
            else:
                # Create default configuration
                self.trading_pairs = []
                self.price_thresholds = {}
                self._save_config()
                print("Created new configuration file")
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.trading_pairs = []
            self.price_thresholds = {}
    
    def _save_config(self):
        """Save current configuration to JSON file."""
        try:
            # Ensure all thresholds have proper data structure
            validated_thresholds = {}
            for pair, thresholds in self.price_thresholds.items():
                if isinstance(thresholds, dict):
                    validated_thresholds[pair] = {
                        'upper': float(thresholds.get('upper', 0)),
                        'lower': float(thresholds.get('lower', 0))
                    }
            
            config = {
                'trading_pairs': self.trading_pairs,
                'thresholds': validated_thresholds,
                'ntfy_config': {
                    'server': self.ntfy_server,
                    'topic': self.ntfy_topic
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"Configuration saved: {len(self.trading_pairs)} trading pairs for monitoring")
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def get_trading_pairs(self) -> list:
        """Get list of trading pairs for price monitoring.
        
        Returns:
            List of trading pair strings
        """
        return self.trading_pairs.copy()
    
    def add_trading_pair(self, pair: str, upper: float, lower: float) -> bool:
        """Add a new trading pair for price monitoring with alert thresholds.
        
        Args:
            pair: Trading pair string (e.g., 'BTC/USDT')
            upper: Upper price threshold for alerts
            lower: Lower price threshold for alerts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if pair not in self.trading_pairs:
                self.trading_pairs.append(pair)
            
            # Store thresholds for price alerts
            self.price_thresholds[pair] = {
                'upper': float(upper),
                'lower': float(lower)
            }
            
            self._save_config()
            print(f"Added monitoring pair: {pair} with alert thresholds upper=${upper}, lower=${lower}")
            return True
            
        except Exception as e:
            print(f"Error adding monitoring pair: {e}")
            return False
    
    def update_trading_pair(self, pair: str, upper: float, lower: float) -> bool:
        """Update alert thresholds for an existing monitoring pair.
        
        Args:
            pair: Trading pair string
            upper: New upper price threshold
            lower: New lower price threshold
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if pair in self.price_thresholds:
                # Update thresholds for price alerts
                self.price_thresholds[pair].update({
                    'upper': float(upper),
                    'lower': float(lower)
                })
                
                self._save_config()
                print(f"Updated monitoring pair: {pair} with alert thresholds upper=${upper}, lower=${lower}")
                return True
            return False
            
        except Exception as e:
            print(f"Error updating monitoring pair: {e}")
            return False
    
    def delete_trading_pair(self, pair: str) -> bool:
        """Delete a monitoring pair and its alert thresholds.
        
        Args:
            pair: Trading pair string to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if pair in self.trading_pairs:
                self.trading_pairs.remove(pair)
            
            if pair in self.price_thresholds:
                del self.price_thresholds[pair]
            
            self._save_config()
            return True
            
        except Exception as e:
            print(f"Error deleting monitoring pair: {e}")
            return False
    
    def get_thresholds(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get alert thresholds for a specific monitoring pair.
        
        Args:
            pair: Trading pair string
            
        Returns:
            Threshold dictionary or None if not found
        """
        if pair in self.price_thresholds:
            thresholds = self.price_thresholds[pair]
            # Ensure required fields exist
            if 'upper' not in thresholds or 'lower' not in thresholds:
                # Set default values if missing
                thresholds['upper'] = thresholds.get('upper', 0)
                thresholds['lower'] = thresholds.get('lower', 0)
                self._save_config()  # Save the updated config
            return thresholds
        return None
    
    def update_ntfy_config(self, server: str, topic: str, password: str = '') -> bool:
        """Update NTFY configuration for alerts.
        
        Args:
            server: NTFY server URL
            topic: NTFY topic name
            password: NTFY password (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.ntfy_server = server
            self.ntfy_topic = topic
            self.ntfy_password = password
            
            self._save_config()
            return True
            
        except Exception as e:
            print(f"Error updating NTFY config: {e}")
            return False
    
    def get_ntfy_config(self) -> Dict[str, str]:
        """Get current NTFY configuration for alerts.
        
        Returns:
            Dictionary with NTFY configuration
        """
        return {
            'server': self.ntfy_server,
            'topic': self.ntfy_topic,
            'password': self.ntfy_password
        }
    
    def validate_config(self) -> Dict[str, list]:
        """Validate current configuration.
        
        Returns:
            Dictionary with validation errors by category
        """
        errors = {
            'ntfy': [],
            'monitoring': []
        }
        
        # Validate NTFY configuration
        if not self.ntfy_server:
            errors['ntfy'].append('NTFY server is not configured')
        if not self.ntfy_topic:
            errors['ntfy'].append('NTFY topic is not configured')
        
        # Validate monitoring pairs
        for pair in self.trading_pairs:
            if pair not in self.price_thresholds:
                errors['monitoring'].append(f'No alert thresholds configured for {pair}')
            else:
                thresholds = self.price_thresholds[pair]
                if thresholds['upper'] <= thresholds['lower']:
                    errors['monitoring'].append(f'Invalid alert thresholds for {pair}: upper must be > lower')
        
        return errors
    
    def is_config_valid(self) -> bool:
        """Check if configuration is valid.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = self.validate_config()
        return all(len(error_list) == 0 for error_list in errors.values()) 