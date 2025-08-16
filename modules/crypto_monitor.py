"""
Crypto Monitor Module

Main monitoring class that coordinates all other modules for cryptocurrency price monitoring and alerts.
"""

import time
import threading
from typing import Dict, Optional, List
from datetime import datetime
from .config_manager import ConfigManager
from .ntfy_manager import NTFYManager
from .price_manager import PriceManager


class CryptoMonitor:
    """Main cryptocurrency monitoring class for price tracking and alerts."""
    
    def __init__(self, config_file: str = 'trading_config.json'):
        """Initialize crypto monitor.
        
        Args:
            config_file: Path to configuration file
        """
        # Initialize managers
        self.config_manager = ConfigManager(config_file)
        self.ntfy_manager = NTFYManager(
            self.config_manager.ntfy_server,
            self.config_manager.ntfy_topic,
            self.config_manager.ntfy_password
        )
        self.price_manager = PriceManager()  # No API keys needed for price monitoring
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.current_prices = {}
        
        # Price tracking for alerts
        self.old_data = {}
        self.alert_sent = {}
        
        # Initialize price tracking
        self._init_price_tracking()
        
        print("✅ Crypto monitor initialized for price monitoring and alerts")
    
    def _init_price_tracking(self):
        """Initialize price tracking for all monitoring pairs."""
        for pair in self.config_manager.get_trading_pairs():
            self.old_data[pair] = {
                'price': None,
                'time': None
            }
            self.alert_sent[pair] = {
                'upper': False,
                'lower': False,
                'last_alert_time': 0
            }
    
    def start_monitoring(self) -> bool:
        """Start price monitoring.
        
        Returns:
            True if monitoring started successfully, False otherwise
        """
        if self.monitoring_active:
            print("Monitoring is already active")
            return False
        
        # Validate configuration
        if not self.config_manager.is_config_valid():
            print("Configuration validation failed")
            return False
        
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("Price monitoring started successfully")
        return True
    
    def stop_monitoring(self):
        """Stop price monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        print("Price monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        print("Starting price monitoring...")
        trading_pairs = self.config_manager.get_trading_pairs()
        print(f"Monitoring pairs: {', '.join(trading_pairs)}")
        
        # Print alert thresholds
        print("\nAlert thresholds:")
        for pair in trading_pairs:
            thresholds = self.config_manager.get_thresholds(pair)
            if thresholds:
                print(f"{pair}: Upper ${thresholds['upper']:.2f} - Lower ${thresholds['lower']:.2f}")
        
        print("\nPress Ctrl+C to stop monitoring\n")
        
        while self.monitoring_active:
            try:
                # Clear console by printing multiple newlines
                print("\n" * 50)
                
                # Print header
                print("Starting price monitoring...")
                print(f"Monitoring pairs: {', '.join(trading_pairs)}")
                print("\nAlert thresholds:")
                for pair in trading_pairs:
                    thresholds = self.config_manager.get_thresholds(pair)
                    if thresholds:
                        print(f"{pair}: Upper ${thresholds['upper']:.2f} - Lower ${thresholds['lower']:.2f}")
                print("\nCurrent Prices:")
                
                # Get current prices
                prices = self.price_manager.get_all_prices(trading_pairs)
                self.current_prices = prices
                
                # Check thresholds and send alerts
                alerts = self.check_thresholds_and_alert()
                
                # Print current prices
                for pair in trading_pairs:
                    inst_id = pair.replace('/', '-')
                    current_price = prices.get(pair)
                    
                    if current_price is not None:
                        now = datetime.now()
                        print(f"[{now.strftime('%H:%M:%S')}] {inst_id} = {current_price}")
                        
                        # Check for alerts
                        if alerts:
                            print(f"\nALERT: {inst_id} - {alerts}")
                
                # Wait before next check
                time.sleep(1.5)
                
            except KeyboardInterrupt:
                print("\nStopping price monitoring...")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {str(e)}")
                time.sleep(1)
    
    def get_current_prices(self) -> Dict[str, Optional[float]]:
        """Get current prices for all monitoring pairs.
        
        Returns:
            Dictionary mapping pairs to current prices
        """
        return self.current_prices.copy()
    
    def get_all_prices(self) -> Dict[str, Optional[float]]:
        """Get all current prices (alias for get_current_prices).
        
        Returns:
            Dictionary mapping pairs to current prices
        """
        return self.get_current_prices()
    
    def add_trading_pair(self, pair: str, upper: float, lower: float) -> bool:
        """Add a new monitoring pair with alert thresholds.
        
        Args:
            pair: Trading pair string
            upper: Upper price threshold for alerts
            lower: Lower price threshold for alerts
            
        Returns:
            True if successful, False otherwise
        """
        success = self.config_manager.add_trading_pair(pair, upper, lower)
        if success:
            # Initialize tracking for new pair
            self.old_data[pair] = {
                'price': None,
                'time': None
            }
            self.alert_sent[pair] = {
                'upper': False,
                'lower': False,
                'last_alert_time': 0
            }
        return success
    
    def update_trading_pair(self, pair: str, upper: float, lower: float) -> bool:
        """Update alert thresholds for an existing monitoring pair.
        
        Args:
            pair: Trading pair string
            upper: New upper threshold
            lower: New lower threshold
            
        Returns:
            True if successful, False otherwise
        """
        success = self.config_manager.update_trading_pair(pair, upper, lower)
        if success:
            # Reset alert flags for updated pair
            self.alert_sent[pair] = {
                'upper': False,
                'lower': False,
                'last_alert_time': 0
            }
        return success
    
    def delete_trading_pair(self, pair: str) -> bool:
        """Delete a monitoring pair and its alert thresholds.
        
        Args:
            pair: Trading pair string to delete
            
        Returns:
            True if successful, False otherwise
        """
        success = self.config_manager.delete_trading_pair(pair)
        if success:
            # Clean up tracking data
            if pair in self.old_data:
                del self.old_data[pair]
            if pair in self.alert_sent:
                del self.alert_sent[pair]
        return success
    
    def get_trading_pairs(self) -> List[Dict]:
        """Get all monitoring pairs with their alert thresholds.
        
        Returns:
            List of dictionaries containing pair info and thresholds
        """
        pairs = []
        for pair in self.config_manager.get_trading_pairs():
            thresholds = self.config_manager.get_thresholds(pair)
            if thresholds:
                pairs.append({
                    'pair': pair,
                    'upper': thresholds['upper'],
                    'lower': thresholds['lower']
                })
            else:
                # If no thresholds found, still include the pair with default values
                pairs.append({
                    'pair': pair,
                    'upper': 0,
                    'lower': 0
                })
        return pairs
    
    def set_futures_mode(self, enabled: bool):
        """Set futures mode on/off.
        
        Args:
            enabled: True to enable futures mode, False for spot
        """
        self.price_manager.set_futures_mode(enabled)
    
    def update_ntfy_config(self, server: str, topic: str, password: str = '') -> bool:
        """Update NTFY configuration for alerts.
        
        Args:
            server: NTFY server URL
            topic: NTFY topic name
            password: NTFY password (optional)
            
        Returns:
            True if successful, False otherwise
        """
        success = self.config_manager.update_ntfy_config(server, topic, password)
        if success:
            self.ntfy_manager.update_config(server, topic, password)
        return success
    
    def get_ntfy_config(self) -> Dict[str, str]:
        """Get current NTFY configuration for alerts.
        
        Returns:
            Dictionary with NTFY configuration
        """
        return self.ntfy_manager.get_config()
    
    def send_test_ntfy_notification(self) -> bool:
        """Send a test NTFY notification.
        
        Returns:
            True if successful, False otherwise
        """
        return self.ntfy_manager.send_test_notification()
    
    def check_thresholds_and_alert(self) -> List[str]:
        """Check all monitoring pairs for threshold alerts.
        
        Returns:
            List of alert messages
        """
        alerts = []
        
        for pair in self.config_manager.get_trading_pairs():
            inst_id = pair.replace('/', '-')
            current_price = self.price_manager.get_current_price(inst_id)
            
            if current_price is not None:
                # Only log when checking thresholds that are set
                thresholds = self.config_manager.get_thresholds(pair)
                if thresholds and (thresholds['upper'] > 0 or thresholds['lower'] > 0):
                    # Only log every 30 seconds to avoid spam
                    current_time = datetime.now().timestamp()
                    if pair not in self.alert_sent or 'last_log_time' not in self.alert_sent[pair]:
                        self.alert_sent[pair]['last_log_time'] = 0
                    
                    if current_time - self.alert_sent[pair]['last_log_time'] >= 30:
                        print(f"🔍 Checking {pair}: price={current_price:.2f}, upper={thresholds['upper']:.2f}, lower={thresholds['lower']:.2f}")
                        self.alert_sent[pair]['last_log_time'] = current_time
                
                alert = self.check_price_thresholds(pair, current_price)
                if alert:
                    alerts.append(f"{pair}: {alert}")
        
        return alerts
    
    def check_price_thresholds(self, pair: str, current_price: float) -> Optional[str]:
        """Check if price exceeds alert thresholds.
        
        Args:
            pair: Trading pair string
            current_price: Current price
            
        Returns:
            Alert message if threshold exceeded, None otherwise
        """
        if current_price is None:
            return None
        
        # Get thresholds for this pair
        thresholds = self.config_manager.get_thresholds(pair)
        if not thresholds:
            return None
        
        # Skip if thresholds are not set (both are 0)
        if thresholds['upper'] == 0 and thresholds['lower'] == 0:
            return None
        
        old_data = self.old_data.get(pair, {'price': None, 'time': None})
        current_time = datetime.now()
        
        # Initialize old_data if not exists
        if pair not in self.old_data:
            self.old_data[pair] = {'price': None, 'time': None}
            old_data = self.old_data[pair]
        
        # Initialize alert_sent if not exists
        if pair not in self.alert_sent:
            self.alert_sent[pair] = {'upper': False, 'lower': False, 'last_alert_time': 0}
        
        # Check if enough time has passed since last alert (5 minutes = 300 seconds)
        time_since_last_alert = current_time.timestamp() - self.alert_sent[pair].get('last_alert_time', 0)
        can_send_alert = time_since_last_alert >= 300
        
        # Check fixed price thresholds (only if thresholds are set and enough time has passed)
        if (thresholds['upper'] > 0 and current_price > thresholds['upper'] and 
            not self.alert_sent[pair]['upper'] and can_send_alert):
            print(f"🚨 ALERT: {pair} price {current_price:.2f} is ABOVE upper threshold {thresholds['upper']:.2f}")
            self.ntfy_manager.send_price_alert(pair, current_price, 'upper', thresholds['upper'])
            self.alert_sent[pair]['upper'] = True
            self.alert_sent[pair]['last_alert_time'] = current_time.timestamp()
            return f"Price {current_price:.2f} is ABOVE upper threshold {thresholds['upper']:.2f}"
            
        elif (thresholds['lower'] > 0 and current_price < thresholds['lower'] and 
              not self.alert_sent[pair]['lower'] and can_send_alert):
            print(f"🚨 ALERT: {pair} price {current_price:.2f} is BELOW lower threshold {thresholds['lower']:.2f}")
            self.ntfy_manager.send_price_alert(pair, current_price, 'lower', thresholds['lower'])
            self.alert_sent[pair]['lower'] = True
            self.alert_sent[pair]['last_alert_time'] = current_time.timestamp()
            return f"Price {current_price:.2f} is BELOW lower threshold {thresholds['lower']:.2f}"
        
        # Reset alert flags if price is back within thresholds for more than 5 minutes
        if thresholds['upper'] > 0 and current_price <= thresholds['upper']:
            # Only reset if price has been within threshold for 5 minutes
            if time_since_last_alert >= 300:
                self.alert_sent[pair]['upper'] = False
        if thresholds['lower'] > 0 and current_price >= thresholds['lower']:
            # Only reset if price has been within threshold for 5 minutes
            if time_since_last_alert >= 300:
                self.alert_sent[pair]['lower'] = False
        
        # Check percentage change (only if we have old price data and enough time has passed)
        if (old_data['price'] is not None and old_data['price'] > 0 and can_send_alert):
            percent_change = abs((current_price - old_data['price']) / old_data['price']) * 100
            if percent_change > 5:  # Alert if price changes more than 5%
                if current_price > old_data['price']:
                    print(f"📈 ALERT: {pair} price UP by {percent_change:.2f}%")
                    self.ntfy_manager.send_percentage_alert(pair, current_price, old_data['price'], percent_change)
                    self.alert_sent[pair]['last_alert_time'] = current_time.timestamp()
                    return f"Price UP by {percent_change:.2f}%"
                else:
                    print(f"📉 ALERT: {pair} price DOWN by {percent_change:.2f}%")
                    self.ntfy_manager.send_percentage_alert(pair, current_price, old_data['price'], percent_change)
                    self.alert_sent[pair]['last_alert_time'] = current_time.timestamp()
                    return f"Price DOWN by {percent_change:.2f}%"
        
        # Update old price for next comparison (update every 5 minutes)
        if old_data['time'] is None or (current_time - old_data['time']).total_seconds() >= 300:
            old_data['price'] = current_price
            old_data['time'] = current_time
        
        return None
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status.
        
        Returns:
            Dictionary with monitoring status information
        """
        status = {
            'monitoring_active': self.monitoring_active,
            'monitoring_pairs_count': len(self.config_manager.get_trading_pairs()),
            'futures_mode': self.price_manager.futures_mode
        }
        
        return status
    
    def get_price_summary(self) -> Dict[str, Dict]:
        """Get price summary for all monitoring pairs.
        
        Returns:
            Dictionary with price information for each pair
        """
        summary = {}
        
        for pair in self.config_manager.get_trading_pairs():
            inst_id = pair.replace('/', '-')
            current_price = self.price_manager.get_current_price(inst_id)
            thresholds = self.config_manager.get_thresholds(pair)
            
            summary[pair] = {
                'current_price': current_price,
                'upper_threshold': thresholds['upper'] if thresholds else None,
                'lower_threshold': thresholds['lower'] if thresholds else None
            }
        
        return summary
    
    def validate_config(self) -> Dict[str, list]:
        """Validate current configuration.
        
        Returns:
            Dictionary with validation errors by category
        """
        return self.config_manager.validate_config()
    
    def is_config_valid(self) -> bool:
        """Check if configuration is valid.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        return self.config_manager.is_config_valid()
    
    def reset_alert_flags(self, pair: str = None):
        """Reset alert flags.
        
        Args:
            pair: Specific pair to reset, or None to reset all
        """
        if pair:
            if pair in self.alert_sent:
                self.alert_sent[pair] = {
                    'upper': False, 
                    'lower': False, 
                    'last_alert_time': 0
                }
        else:
            # Reset all pairs
            for p in self.alert_sent:
                self.alert_sent[p] = {
                    'upper': False, 
                    'lower': False, 
                    'last_alert_time': 0
                }
    
    def get_alert_status(self, pair: str = None) -> Dict:
        """Get current alert status.
        
        Args:
            pair: Specific pair to check, or None for all pairs
            
        Returns:
            Dictionary with alert status
        """
        if pair:
            return {
                'pair': pair,
                'alert_sent': self.alert_sent.get(pair, {
                    'upper': False, 
                    'lower': False, 
                    'last_alert_time': 0
                }),
                'old_data': self.old_data.get(pair, {'price': None, 'time': None})
            }
        else:
            return {
                'alert_sent': self.alert_sent,
                'old_data': self.old_data
            } 