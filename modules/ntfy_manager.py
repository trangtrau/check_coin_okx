"""
NTFY Notification Management Module

Handles all NTFY notification operations including sending alerts and test messages.
"""

import requests
import base64
from typing import Optional, Dict, Any
from datetime import datetime


class NTFYManager:
    """Manages NTFY notifications and alerts."""
    
    def __init__(self, server: str = 'https://ntfy.sh', topic: str = 'crypto_alerts', password: str = ''):
        """Initialize NTFY manager.
        
        Args:
            server: NTFY server URL
            topic: NTFY topic name
            password: NTFY password (optional)
        """
        self.server = server.rstrip('/')
        self.topic = topic
        self.password = password
        self.last_alert_time = 0
        self.alert_cooldown = 30  # seconds between alerts
    
    def update_config(self, server: str, topic: str, password: str = '') -> bool:
        """Update NTFY configuration.
        
        Args:
            server: New NTFY server URL
            topic: New NTFY topic name
            password: New NTFY password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.server = server.rstrip('/')
            self.topic = topic
            self.password = password
            print(f"NTFY config updated: {server}/{topic}")
            return True
        except Exception as e:
            print(f"Error updating NTFY config: {e}")
            return False
    
    def get_config(self) -> Dict[str, str]:
        """Get current NTFY configuration.
        
        Returns:
            Dictionary with current NTFY configuration
        """
        return {
            'server': self.server,
            'topic': self.topic,
            'password': self.password
        }
    
    def _can_send_alert(self) -> bool:
        """Check if enough time has passed since last alert.
        
        Returns:
            True if alert can be sent, False otherwise
        """
        current_time = datetime.now().timestamp()
        return (current_time - self.last_alert_time) >= self.alert_cooldown
    
    def _send_notification(self, title: str, message: str, priority: str = 'default', tags: str = '') -> bool:
        """Send a notification to NTFY.
        
        Args:
            title: Notification title
            message: Notification message
            priority: Notification priority (default, low, high, urgent)
            tags: Comma-separated tags
            
        Returns:
            True if successful, False otherwise
        """
        try:
            notification_url = f"{self.server}/{self.topic}"
            headers = {
                "Title": title,
                "Priority": priority,
                "Tags": tags
            }
            
            # Add authentication if password provided
            if self.password:
                auth = base64.b64encode(f":{self.password}".encode()).decode()
                headers["Authorization"] = f"Basic {auth}"
            
            response = requests.post(
                notification_url, 
                data=message.encode('utf-8'), 
                headers=headers, 
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Notification sent successfully: {title}")
                return True
            else:
                print(f"Failed to send notification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False
    
    def send_alert(self, title: str, message: str) -> bool:
        """Send an alert notification with cooldown protection.
        
        Args:
            title: Alert title
            message: Alert message
            
        Returns:
            True if alert was sent, False otherwise
        """
        if not self._can_send_alert():
            print("Alert sent recently, skipping this one due to cooldown")
            return False
        
        success = self._send_notification(title, message, priority='high', tags='warning,alert')
        if success:
            self.last_alert_time = datetime.now().timestamp()
        
        return success
    
    def send_price_alert(self, pair: str, current_price: float, threshold_type: str, threshold_value: float) -> bool:
        """Send a price threshold alert.
        
        Args:
            pair: Trading pair (e.g., 'BTC/USDT')
            current_price: Current price
            threshold_type: Type of threshold ('upper' or 'lower')
            threshold_value: Threshold value
            
        Returns:
            True if alert was sent, False otherwise
        """
        if threshold_type == 'upper':
            title = f"Price Alert - {pair}"
            message = f"{pair}: Giá ${current_price:.2f} vượt ngưỡng trên ${threshold_value:.2f}"
            tags = "rocket,up,alert"
        else:
            title = f"Price Alert - {pair}"
            message = f"{pair}: Giá ${current_price:.2f} dưới ngưỡng dưới ${threshold_value:.2f}"
            tags = "chart-decreasing,down,alert"
        
        return self.send_alert(title, message)
    
    def send_percentage_alert(self, pair: str, current_price: float, old_price: float, percent_change: float) -> bool:
        """Send a percentage change alert.
        
        Args:
            pair: Trading pair
            current_price: Current price
            old_price: Previous price
            percent_change: Percentage change
            
        Returns:
            True if alert was sent, False otherwise
        """
        if current_price > old_price:
            title = f"Price Change Alert - {pair}"
            message = f"{pair}: Giá tăng {percent_change:.2f}% từ ${old_price:.2f} lên ${current_price:.2f}"
            tags = "chart-increasing,up,trending"
        else:
            title = f"Price Change Alert - {pair}"
            message = f"{pair}: Giá giảm {percent_change:.2f}% từ ${old_price:.2f} xuống ${current_price:.2f}"
            tags = "chart-decreasing,down,trending"
        
        return self.send_alert(title, message)
    
    def send_test_notification(self) -> bool:
        """Send a test notification.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            message = f"Test notification from Crypto Monitor\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            success = self._send_notification(
                "Crypto Monitor Test", 
                message, 
                priority='default', 
                tags='test'
            )
            
            if success:
                print(f"Test notification sent successfully to {self.server}/{self.topic}")
            else:
                print(f"Failed to send test notification")
            
            return success
            
        except Exception as e:
            print(f"Error sending test notification: {e}")
            return False
    
    def send_trade_execution_alert(self, pair: str, side: str, price: float, amount: float) -> bool:
        """Send a trade execution alert.
        
        Args:
            pair: Trading pair
            side: Trade side ('buy' or 'sell')
            price: Execution price
            amount: Trade amount
            
        Returns:
            True if alert was sent, False otherwise
        """
        if side.lower() == 'buy':
            title = f"💰 Buy Order Executed - {pair}"
            message = f"Bought {amount} {pair} at ${price:.2f}"
            tags = "money,green,buy"
        else:
            title = f"💸 Sell Order Executed - {pair}"
            message = f"Sold {amount} {pair} at ${price:.2f}"
            tags = "money,red,sell"
        
        return self._send_notification(title, message, priority='high', tags=tags)
    
    def send_system_alert(self, message: str, priority: str = 'default') -> bool:
        """Send a system-level alert.
        
        Args:
            message: Alert message
            priority: Alert priority
            
        Returns:
            True if alert was sent, False otherwise
        """
        return self._send_notification(
            "System Alert", 
            message, 
            priority=priority, 
            tags='system,alert'
        )
    
    def send_monitoring_status_alert(self, status: str, details: str = '') -> bool:
        """Send monitoring status alert.
        
        Args:
            status: Monitoring status ('started', 'stopped', 'error')
            details: Additional details
            
        Returns:
            True if alert was sent, False otherwise
        """
        if status == 'started':
            title = "🟢 Monitoring Started"
            message = "Crypto price monitoring has been started"
            tags = "green,start,monitoring"
        elif status == 'stopped':
            title = "🔴 Monitoring Stopped"
            message = "Crypto price monitoring has been stopped"
            tags = "red,stop,monitoring"
        else:
            title = "⚠️ Monitoring Error"
            message = f"Error in monitoring: {details}"
            tags = "warning,error,monitoring"
        
        return self._send_notification(title, message, priority='default', tags=tags) 