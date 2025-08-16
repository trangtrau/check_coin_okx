"""
Price Management Module

Handles all price-related operations including API calls, caching, and price calculations.
"""

import requests
import time
import json
import os
from typing import Dict, Optional, List
from datetime import datetime


class PriceManager:
    """Manages cryptocurrency price operations for monitoring and alerts."""
    
    def __init__(self):
        """Initialize price manager for monitoring only."""
        self.base_url = "https://www.okx.com"
        
        # Price caching
        self.price_cache = {}
        self.price_cache_time = {}
        self.cache_duration = 2  # seconds
        
        # Futures mode
        self.futures_mode = False
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # seconds between requests
        
        # Coins that don't have futures mode (will fallback to spot)
        self.no_futures_coins = set()
        self.no_futures_file = 'no_futures_coins.json'
        self._load_no_futures_coins()
        
        print("ℹ️  Price manager initialized for monitoring only")
    
    def _load_no_futures_coins(self):
        """Load list of coins that don't have futures mode."""
        try:
            if os.path.exists(self.no_futures_file):
                with open(self.no_futures_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.no_futures_coins = set(data.get('coins', []))
                    print(f"📋 Loaded {len(self.no_futures_coins)} coins without futures mode")
            else:
                # Initialize with some common coins that don't have futures
                self.no_futures_coins = {
                    'XCH', 'ETHW', 'DOT', 'ADA', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XRP',
                    'DOGE', 'SHIB', 'MATIC', 'AVAX', 'SOL', 'TRX', 'ETC', 'FIL', 'NEAR'
                }
                self._save_no_futures_coins()
                print(f"📋 Initialized with {len(self.no_futures_coins)} common coins without futures mode")
        except Exception as e:
            print(f"⚠️  Error loading no-futures coins: {e}")
            self.no_futures_coins = set()
    
    def _save_no_futures_coins(self):
        """Save list of coins that don't have futures mode."""
        try:
            data = {
                'coins': list(self.no_futures_coins),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.no_futures_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error saving no-futures coins: {e}")
    
    def add_no_futures_coin(self, coin: str):
        """Add a coin to the no-futures list.
        
        Args:
            coin: Coin symbol (e.g., 'BTC', 'ETH')
        """
        self.no_futures_coins.add(coin.upper())
        self._save_no_futures_coins()
        print(f"➕ Added {coin} to no-futures list")
    
    def get_no_futures_coins(self) -> List[str]:
        """Get list of coins that don't have futures mode.
        
        Returns:
            List of coin symbols
        """
        return sorted(list(self.no_futures_coins))
    
    def set_futures_mode(self, enabled: bool):
        """Set futures mode on/off.
        
        Args:
            enabled: True to enable futures mode, False for spot
        """
        self.futures_mode = enabled
        self.clear_price_cache()
        print(f"Futures mode: {'ON' if enabled else 'OFF'}")
    
    def _rate_limit(self):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _get_coin_symbol(self, inst_id: str) -> str:
        """Extract coin symbol from instrument ID.
        
        Args:
            inst_id: Instrument ID (e.g., 'BTC-USDT', 'BTC-USDT-SWAP')
            
        Returns:
            Coin symbol (e.g., 'BTC')
        """
        return inst_id.split('-')[0]
    
    def get_current_price(self, inst_id: str) -> Optional[float]:
        """Get current price for a trading pair with caching and futures fallback.
        
        Args:
            inst_id: Instrument ID (e.g., 'BTC-USDT')
            
        Returns:
            Current price or None if failed
        """
        # Check cache first
        current_time = time.time()
        if inst_id in self.price_cache and current_time - self.price_cache_time.get(inst_id, 0) < self.cache_duration:
            return self.price_cache[inst_id]
        
        # Determine market type based on futures_mode flag
        original_inst_id = inst_id
        coin_symbol = self._get_coin_symbol(inst_id)
        
        if self.futures_mode:
            # Check if this coin has futures mode
            if coin_symbol in self.no_futures_coins:
                # Coin doesn't have futures, use spot price
                print(f"ℹ️  {coin_symbol} has no futures mode, using spot price")
                inst_id = inst_id  # Keep original (spot) format
            else:
                # For futures, add -SWAP suffix if not already present
                if not inst_id.endswith('-SWAP'):
                    inst_id = inst_id.replace('-USDT', '-USDT-SWAP')
        
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/api/v5/market/ticker?instId={inst_id}"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                data = response.json()
                if data and data.get('code') == '0' and data.get('data') and len(data['data']) > 0:
                    ticker = data['data'][0]
                    raw_price = float(ticker['last'])
                    
                    # Format price based on coin type
                    if 'BTC' in original_inst_id:
                        # BTC: keep 6 decimal places
                        price = round(raw_price, 6)
                    else:
                        # Other coins: maximum 3 decimal places
                        price = round(raw_price, 3)
                    
                    # Cache the price using original inst_id
                    self.price_cache[original_inst_id] = price
                    self.price_cache_time[original_inst_id] = current_time
                    
                    return price
                else:
                    # If futures request failed and we're in futures mode, try spot
                    if self.futures_mode and coin_symbol not in self.no_futures_coins and not inst_id.endswith('-SWAP'):
                        print(f"⚠️  Futures request failed for {inst_id}, trying spot price")
                        self.add_no_futures_coin(coin_symbol)
                        # Retry with spot price
                        return self.get_current_price(original_inst_id)
                    else:
                        print(f"Không có dữ liệu hợp lệ cho {inst_id}")
                        return None
            else:
                # If futures request failed and we're in futures mode, try spot
                if self.futures_mode and coin_symbol not in self.no_futures_coins and not inst_id.endswith('-SWAP'):
                    print(f"⚠️  Futures request failed for {inst_id} (HTTP {response.status_code}), trying spot price")
                    self.add_no_futures_coin(coin_symbol)
                    # Retry with spot price
                    return self.get_current_price(original_inst_id)
                else:
                    print(f"API request failed: {response.status_code}")
                    return None
                
        except requests.exceptions.Timeout:
            print(f"Timeout khi lấy giá {inst_id}")
            return None
        except Exception as e:
            print(f"Lỗi khi lấy giá {inst_id}: {e}")
            return None
    
    def get_all_prices(self, trading_pairs: List[str]) -> Dict[str, Optional[float]]:
        """Get all current prices for trading pairs.
        
        Args:
            trading_pairs: List of trading pair strings
            
        Returns:
            Dictionary mapping pairs to prices
        """
        prices = {}
        
        for pair in trading_pairs:
            inst_id = pair.replace('/', '-')
            price = self.get_current_price(inst_id)
            prices[pair] = price
        
        return prices
    
    def get_cached_price(self, inst_id: str) -> Optional[float]:
        """Get cached price without making API call.
        
        Args:
            inst_id: Instrument ID
            
        Returns:
            Cached price or None if not available
        """
        current_time = time.time()
        if inst_id in self.price_cache and current_time - self.price_cache_time.get(inst_id, 0) < self.cache_duration:
            return self.price_cache[inst_id]
        return None
    
    def clear_price_cache(self):
        """Clear the price cache."""
        self.price_cache.clear()
        self.price_cache_time.clear() 