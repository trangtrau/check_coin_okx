import requests
import time
import json
import hmac
import base64
import hashlib
import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Import winsound only on Windows
if os.name == 'nt':  # Windows
    import winsound
    ALERT_SOUND_PATH = "alert_sound.wav"
    TRUE_SOUND_PATH = "alert_sound2.wav"
    
    # Check if sound files exist
    if not os.path.exists(ALERT_SOUND_PATH):
        print(f"Warning: {ALERT_SOUND_PATH} not found!")
    if not os.path.exists(TRUE_SOUND_PATH):
        print(f"Warning: {TRUE_SOUND_PATH} not found!")
else:
    # On non-Windows systems, set sound paths to None
    ALERT_SOUND_PATH = None
    TRUE_SOUND_PATH = None

# Load environment variables
load_dotenv()

API_KEY = os.getenv('OKX_API_KEY')
SECRET_KEY = os.getenv('OKX_SECRET_KEY')
PASSPHRASE = os.getenv('OKX_PASSPHRASE')
BASE_URL = "https://www.okx.com"
NTFY_SERVER = os.getenv('NTFY_SERVER', 'https://ntfy.sh')  # Default to ntfy.sh if not specified
NTFY_TOPIC = os.getenv('NTFY_TOPIC', 'crypto_alerts')  # Default topic if not specified

class CryptoMonitor:
    def __init__(self):
        # Load environment variables for API credentials only
        load_dotenv()
        
        # Initialize API credentials
        self.api_key = os.getenv('OKX_API_KEY')
        self.secret_key = os.getenv('OKX_SECRET_KEY')
        self.passphrase = os.getenv('OKX_PASSPHRASE')
        
        # Initialize trading pairs and thresholds
        self.trading_pairs = []
        self.price_thresholds = {}
        self.old_data = {}
        self.trade_executed = {}  # Track executed trades
        self.last_sound_time = 0  # Track last sound alert time
        self.futures_mode = False  # Flag for futures mode
        
        # Shared price cache for monitoring and mini window
        self.price_cache = {}
        self.price_cache_time = {}
        self.cache_duration = 2  # Cache prices for 2 seconds
        
        # Load configuration from JSON
        self.config_file = 'trading_config.json'
        self.load_config()

    def load_config(self):
        """Load trading configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.trading_pairs = config.get('trading_pairs', [])
                    
                    # Load NTFY configuration
                    ntfy_config = config.get('ntfy_config', {})
                    global NTFY_SERVER, NTFY_TOPIC
                    NTFY_SERVER = ntfy_config.get('server', 'https://ntfy.sh')
                    NTFY_TOPIC = ntfy_config.get('topic', 'crypto_alerts')
                    
                    # Safe conversion function for float values
                    def safe_float(value, default=0.0):
                        if value == '' or value is None:
                            return default
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    # Load thresholds for each pair
                    for pair in self.trading_pairs:
                        if pair in config.get('thresholds', {}):
                            settings = config['thresholds'][pair]
                            self.price_thresholds[pair] = {
                                'upper': safe_float(settings.get('upper'), 0.0),
                                'lower': safe_float(settings.get('lower'), 0.0),
                                'upper_action': settings.get('upper_action', 'None'),
                                'upper_price': safe_float(settings.get('upper_price', settings.get('upper', 0.0))),
                                'lower_action': settings.get('lower_action', 'None'),
                                'lower_price': safe_float(settings.get('lower_price', settings.get('lower', 0.0))),
                                'trade_amount': safe_float(settings.get('trade_amount', 0.0))
                            }
                            self.old_data[pair] = {'price': None, 'time': None}
                            self.trade_executed[pair] = {
                                'upper': False,
                                'lower': False
                            }
            else:
                # Create new config file with empty structure
                self.save_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.trading_pairs = []
            self.price_thresholds = {}

    def save_config(self):
        """Save trading configuration to JSON file"""
        try:
            config = {
                'trading_pairs': self.trading_pairs,
                'thresholds': {},
                'ntfy_config': {
                    'server': NTFY_SERVER,
                    'topic': NTFY_TOPIC
                }
            }
            
            for pair, settings in self.price_thresholds.items():
                config['thresholds'][pair] = {
                    'upper': settings['upper'],
                    'lower': settings['lower'],
                    'upper_action': settings.get('upper_action', 'None'),
                    'upper_price': settings.get('upper_price', settings['upper']),
                    'lower_action': settings.get('lower_action', 'None'),
                    'lower_price': settings.get('lower_price', settings['lower']),
                    'trade_amount': settings.get('trade_amount', 0.0)
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def get_timestamp(self):
        return datetime.utcnow().isoformat("T", "milliseconds") + "Z"

    def generate_signature(self, timestamp, method, request_path, body):
        prehash = f"{timestamp}{method}{request_path}{body}"
        hmac_key = bytes(SECRET_KEY, encoding='utf-8')
        signature = hmac.new(hmac_key, prehash.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(signature).decode()

    def get_current_price(self, inst_id):
        """Get current price for a trading pair with caching"""
        # Check cache first
        current_time = time.time()
        if inst_id in self.price_cache and current_time - self.price_cache_time.get(inst_id, 0) < self.cache_duration:
            return self.price_cache[inst_id]
        
        # Determine market type based on futures_mode flag
        original_inst_id = inst_id
        if self.futures_mode:
            # For futures, add -SWAP suffix if not already present
            if not inst_id.endswith('-SWAP'):
                inst_id = inst_id.replace('-USDT', '-USDT-SWAP')
        
        url = f"{BASE_URL}/api/v5/market/ticker?instId={inst_id}"
        try:
            response = requests.get(url, timeout=2)  # Reduced timeout to 2 seconds
            data = response.json()
            if data and data.get('code') == '0' and data.get('data') and len(data['data']) > 0:
                ticker = data['data'][0]
                price = float(ticker['last'])
                
                # Cache the price using original inst_id (without -SWAP)
                self.price_cache[original_inst_id] = price
                self.price_cache_time[original_inst_id] = current_time
                
                return price
            else:
                print(f"Không có dữ liệu hợp lệ cho {inst_id}")
                return None
        except requests.exceptions.Timeout:
            print(f"Timeout khi lấy giá {inst_id}")
            return None
        except Exception as e:
            print(f"Lỗi khi lấy giá {inst_id}: {e}")
            return None

    def get_cached_price(self, inst_id):
        """Get cached price without making API call"""
        current_time = time.time()
        if inst_id in self.price_cache and current_time - self.price_cache_time.get(inst_id, 0) < self.cache_duration:
            return self.price_cache[inst_id]
        return None

    def clear_price_cache(self):
        """Clear the price cache"""
        self.price_cache.clear()
        self.price_cache_time.clear()

    def set_futures_mode(self, enabled):
        """Set futures mode on/off"""
        self.futures_mode = enabled
        # Clear cache when switching modes
        self.clear_price_cache()
        print(f"Futures mode: {'ON' if enabled else 'OFF'}")

    def get_all_prices(self):
        """Get all current prices for trading pairs - used by both monitoring and mini window"""
        prices = {}
        for pair in self.trading_pairs:
            inst_id = pair.replace('/', '-')
            
            # Check cache first
            cached_price = self.get_cached_price(inst_id)
            if cached_price is not None:
                prices[pair] = cached_price
                continue
            
            # If not in cache, get fresh price
            price = self.get_current_price(inst_id)
            if price is not None:
                prices[pair] = price
        
        return prices

    def play_alert_sound(self, sound_path):
        """Send ntfy notification only (cross-platform compatible)"""
        try:
            current_time = time.time()
            if current_time - self.last_sound_time >= 30:  # Check if 30 seconds have passed
                # Send ntfy notification
                try:
                    notification_url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
                    headers = {
                        "Title": "Crypto Alert",
                        "Priority": "urgent",
                        "Tags": "warning"
                    }
                    message = "Cảnh báo giá crypto!"
                    response = requests.post(notification_url, data=message.encode('utf-8'), headers=headers)
                    if response.status_code == 200:
                        print("Đã gửi thông báo ntfy")
                        self.last_sound_time = current_time  # Update last notification time
                    else:
                        print(f"Lỗi gửi thông báo ntfy: {response.status_code}")
                except Exception as e:
                    print(f"Lỗi khi gửi thông báo ntfy: {e}")
            else:
                print("Đã gửi thông báo trong 30 giây gần đây, bỏ qua cảnh báo này")
        except Exception as e:
            print("Lỗi khi gửi thông báo:", e)

    def send_ntfy_notification(self, title, message):
        """Send NTFY notification with custom title and message"""
        try:
            notification_url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
            headers = {
                "Title": title,
                "Priority": "urgent",
                "Tags": "warning"
            }
            response = requests.post(notification_url, data=message.encode('utf-8'), headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"Đã gửi thông báo ntfy: {title}")
                return True
            else:
                print(f"Lỗi gửi thông báo ntfy: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Lỗi khi gửi thông báo ntfy: {e}")
            return False

    def update_ntfy_config(self, server, topic, password=None):
        """Update NTFY configuration"""
        global NTFY_SERVER, NTFY_TOPIC
        NTFY_SERVER = server
        NTFY_TOPIC = topic
        
        # Update environment variable for password (for security)
        if password:
            self._ntfy_password = password
        
        # Save to config file
        self.save_config()
        print(f"NTFY config updated: {server}/{topic}")

    def get_ntfy_config(self):
        """Get current NTFY configuration"""
        return {
            'server': NTFY_SERVER,
            'topic': NTFY_TOPIC,
            'password': getattr(self, '_ntfy_password', '')
        }

    def send_test_ntfy_notification(self, server, topic, password=None):
        """Send a test NTFY notification"""
        try:
            notification_url = f"{server}/{topic}"
            headers = {
                "Title": "Crypto Monitor Test",
                "Priority": "default",
                "Tags": "test"
            }
            
            # Add authentication if password provided
            if password:
                import base64
                auth = base64.b64encode(f":{password}".encode()).decode()
                headers["Authorization"] = f"Basic {auth}"
            
            message = f"Test notification from Crypto Monitor\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            response = requests.post(notification_url, data=message.encode('utf-8'), headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"Test notification sent successfully to {notification_url}")
                return True
            else:
                print(f"Failed to send test notification: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error sending test notification: {e}")
            return False

    def check_price_thresholds(self, inst_id, current_price):
        """Check if price exceeds thresholds and percentage change"""
        if current_price is None:
            return None
            
        # Get thresholds for this pair
        pair = inst_id.replace('-', '/')
        thresholds = self.price_thresholds[pair]
        old_data = self.old_data[pair]
        
        # Check if we need to update old price (every hour)
        current_time = datetime.now()
        if old_data['time'] is None or (current_time - old_data['time']).total_seconds() >= 3600:
            old_data['price'] = current_price
            old_data['time'] = current_time
            return None

        # Check fixed price thresholds
        if current_price > thresholds['upper'] and not self.trade_executed[pair]['upper']:
            print("Giá vượt mức tối đa!")
            alert_message = f"{pair}: Giá ${current_price:.2f} vượt ngưỡng trên ${thresholds['upper']:.2f}"
            self.send_ntfy_notification(f"Crypto Alert - {pair}", alert_message)
            self.trade_executed[pair]['upper'] = True  # Mark upper threshold as executed
            return f"Price {current_price:.2f} is ABOVE upper threshold {thresholds['upper']:.2f}"
        elif current_price < thresholds['lower'] and not self.trade_executed[pair]['lower']:
            print("Giá dưới mức tối thiểu!")
            alert_message = f"{pair}: Giá ${current_price:.2f} dưới ngưỡng dưới ${thresholds['lower']:.2f}"
            self.send_ntfy_notification(f"Crypto Alert - {pair}", alert_message)
            self.trade_executed[pair]['lower'] = True  # Mark lower threshold as executed
            return f"Price {current_price:.2f} is BELOW lower threshold {thresholds['lower']:.2f}"

        # Check percentage change
        if old_data['price'] is not None:
            percent_change = abs((current_price - old_data['price']) / old_data['price']) * 100
            if percent_change > 5:
                if current_price > old_data['price']:
                    print("Tăng trên 5%")
                    alert_message = f"{pair}: Giá tăng {percent_change:.2f}% từ ${old_data['price']:.2f} lên ${current_price:.2f}"
                    self.send_ntfy_notification(f"Crypto Alert - {pair}", alert_message)
                    return f"Price UP by {percent_change:.2f}%"
                else:
                    print("Giảm trên 5%")
                    alert_message = f"{pair}: Giá giảm {percent_change:.2f}% từ ${old_data['price']:.2f} xuống ${current_price:.2f}"
                    self.send_ntfy_notification(f"Crypto Alert - {pair}", alert_message)
                    return f"Price DOWN by {percent_change:.2f}%"

        # Update old price
        old_data['price'] = current_price
        return None

    def check_thresholds_and_alert(self):
        """Check all trading pairs for threshold alerts (for web monitoring)"""
        for pair in self.trading_pairs:
            if pair in self.price_thresholds:
                inst_id = pair.replace('/', '-')
                current_price = self.get_cached_price(inst_id)
                
                if current_price is not None:
                    result = self.check_price_thresholds(inst_id, current_price)
                    if result:
                        print(f"ALERT: {pair} - {result}")
                        # Send ntfy notification
                        try:
                            notification_url = f"{NTFY_SERVER}/{NTFY_TOPIC}"
                            headers = {
                                "Title": f"Crypto Alert - {pair}",
                                "Priority": "urgent",
                                "Tags": "warning"
                            }
                            message = f"{pair}: {result}"
                            response = requests.post(notification_url, data=message.encode('utf-8'), headers=headers)
                            if response.status_code == 200:
                                print(f"Đã gửi thông báo ntfy cho {pair}")
                            else:
                                print(f"Lỗi gửi thông báo ntfy cho {pair}: {response.status_code}")
                        except Exception as e:
                            print(f"Lỗi khi gửi thông báo ntfy cho {pair}: {e}")

    def get_spot_balance(self, coin="USDT"):
        # Add caching to avoid repeated API calls
        if hasattr(self, '_balance_cache') and hasattr(self, '_balance_cache_time'):
            # Cache balance for 30 seconds
            if time.time() - self._balance_cache_time < 30:
                return self._balance_cache.get(coin, 0)
        
        endpoint = "/api/v5/account/balance"
        url = BASE_URL + endpoint
        method = "GET"
        body = ""
        timestamp = self.get_timestamp()
        sign = self.generate_signature(timestamp, method, endpoint, body)

        headers = {
            "OK-ACCESS-KEY": API_KEY,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": PASSPHRASE,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=2)  # Reduced timeout to 2 seconds
            data = response.json()
            balances = data["data"][0]["details"]
            
            # Initialize cache if not exists
            if not hasattr(self, '_balance_cache'):
                self._balance_cache = {}
                self._balance_cache_time = time.time()
            
            for b in balances:
                if b["ccy"] == coin:
                    balance = float(b["availBal"])
                    self._balance_cache[coin] = balance
                    self._balance_cache_time = time.time()
                    print(f"Số dư {coin}: {balance}")
                    return balance
            print(f"Không tìm thấy số dư {coin}")
            return 0
        except requests.exceptions.Timeout:
            print(f"Timeout khi lấy số dư {coin}")
            return 0
        except Exception as e:
            print("Lỗi khi lấy số dư:", e)
            return 0

    def place_order(self, inst_id, side, ord_type, px, sz):
        """Place an order on OKX"""
        method = "POST"
        request_path = "/api/v5/trade/order"
        timestamp = self.get_timestamp()

        if sz == "max":
            try:
                usdt_balance = self.get_spot_balance("USDT")
                if not px or px <= 0:
                    raise ValueError("Giá không hợp lệ.")
                sz = max(0, int(usdt_balance // px) - 1)
                print(f"Kích thước tính toán: {sz}")
            except Exception as e:
                print("Không thể tính kích thước:", e)
                return

        order_data = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": side,
            "ordType": ord_type,
            "px": str(px),
            "sz": str(sz)
        }
        body = json.dumps(order_data)
        sign = self.generate_signature(timestamp, method, request_path, body)

        headers = {
            "OK-ACCESS-KEY": API_KEY,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": PASSPHRASE,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(BASE_URL + request_path, headers=headers, data=body)
            print("Kết quả đặt lệnh:", response.json())
        except Exception as e:
            print("Lỗi khi đặt lệnh:", e)

    def place_market_order(self, inst_id, side, sz):
        """Place a market order on OKX"""
        method = "POST"
        request_path = "/api/v5/trade/order"
        timestamp = self.get_timestamp()

        # Calculate size if using max
        if sz == "max":
            try:
                usdt_balance = self.get_spot_balance("USDT")
                current_price = self.get_current_price(inst_id)
                if not current_price or current_price <= 0:
                    raise ValueError("Không thể lấy giá hiện tại.")
                sz = max(0, int(usdt_balance // current_price) - 1)
                print(f"Kích thước tính toán: {sz}")
            except Exception as e:
                print("Không thể tính kích thước:", e)
                return

        order_data = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": side,
            "ordType": "market",
            "sz": str(sz)
        }
        body = json.dumps(order_data)
        sign = self.generate_signature(timestamp, method, request_path, body)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(BASE_URL + request_path, headers=headers, data=body)
            result = response.json()
            print("Kết quả đặt lệnh:", result)
            return result
        except Exception as e:
            print("Lỗi khi đặt lệnh:", e)
            return None

    def place_limit_order(self, inst_id, side, px, sz):
        """Place a limit order on OKX"""
        method = "POST"
        request_path = "/api/v5/trade/order"
        timestamp = self.get_timestamp()

        # Calculate size if using max
        if sz == "max":
            try:
                usdt_balance = self.get_spot_balance("USDT")
                if not px or px <= 0:
                    raise ValueError("Giá không hợp lệ.")
                sz = max(0, int(usdt_balance // px) - 1)
                print(f"Kích thước tính toán: {sz}")
            except Exception as e:
                print("Không thể tính kích thước:", e)
                return

        order_data = {
            "instId": inst_id,
            "tdMode": "cash",
            "side": side,
            "ordType": "limit",
            "px": str(px),
            "sz": str(sz)
        }
        body = json.dumps(order_data)
        sign = self.generate_signature(timestamp, method, request_path, body)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(BASE_URL + request_path, headers=headers, data=body)
            result = response.json()
            print("Kết quả đặt lệnh:", result)
            return result
        except Exception as e:
            print("Lỗi khi đặt lệnh:", e)
            return None

    def monitor_prices(self):
        """Main monitoring loop"""
        print("Starting price monitoring...")
        print(f"Monitoring pairs: {', '.join(self.trading_pairs)}")
        print("\nPrice thresholds:")
        for pair, thresholds in self.price_thresholds.items():
            print(f"{pair}: Upper ${thresholds['upper']:.2f} - Lower ${thresholds['lower']:.2f}")
        print("\nPress Ctrl+C to stop monitoring\n")

        while True:
            try:
                # Clear console by printing multiple newlines
                print("\n" * 50)
                
                # Print header
                print("Starting price monitoring...")
                print(f"Monitoring pairs: {', '.join(self.trading_pairs)}")
                print("\nPrice thresholds:")
                for pair, thresholds in self.price_thresholds.items():
                    print(f"{pair}: Upper ${thresholds['upper']:.2f} - Lower ${thresholds['lower']:.2f}")
                print("\nCurrent Prices:")
                
                for pair in self.trading_pairs:
                    inst_id = pair.replace('/', '-')
                    current_price = self.get_current_price(inst_id)
                    if current_price is None:
                        continue

                    # Print current price
                    now = datetime.now()
                    print(f"[{now.strftime('%H:%M:%S')}] {inst_id} = {current_price}")

                    # Check price thresholds and percentage change
                    result = self.check_price_thresholds(inst_id, current_price)
                    if result:
                        print(f"\nALERT: {inst_id} - {result}")

                # Wait for 1.5 seconds before next check
                time.sleep(1)

            except KeyboardInterrupt:
                print("\nStopping price monitoring...")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {str(e)}")
                time.sleep(1)

    def calculate_max_amount(self, pair, price):
        """Calculate maximum amount that can be bought with USDT balance"""
        try:
            # Get USDT balance and subtract 5 USDT for fees
            usdt_balance = self.get_spot_balance("USDT") - 5
            if usdt_balance <= 0:
                return 0
            
            # Calculate amount based on price
            amount = usdt_balance / price
            
            # Round to appropriate decimal places
            if "BTC" in pair:
                return round(amount, 6)  # BTC has 6 decimal places
            elif "ETH" in pair:
                return round(amount, 5)  # ETH has 5 decimal places
            else:
                return round(amount, 2)  # Other coins typically have 2 decimal places
                
        except Exception as e:
            print("Error calculating max amount:", e)
            return 0

if __name__ == "__main__":
    monitor = CryptoMonitor()
    monitor.monitor_prices() 