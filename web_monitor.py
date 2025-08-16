from flask import Flask, render_template, jsonify, request
from crypto_monitor import CryptoMonitor
import threading
import time
import json
from datetime import datetime
import os

app = Flask(__name__)

# Global variables
monitor = CryptoMonitor()
monitoring_active = False
monitoring_thread = None
current_prices = {}
futures_mode = False
font_size = 16

def monitor_prices():
    """Background monitoring function"""
    global current_prices, monitoring_active
    
    while monitoring_active:
        try:
            # Get all prices at once
            prices = monitor.get_all_prices()
            if prices:
                # Ensure all configured trading pairs are in current_prices
                for pair in monitor.trading_pairs:
                    if pair not in prices:
                        prices[pair] = None  # Mark as not fetched yet
                    current_prices[pair] = prices.get(pair, None)
                
                # Check thresholds and trigger alerts (ntfy only)
                monitor.check_thresholds_and_alert()
            else:
                # If get_all_prices fails, at least ensure all pairs are in current_prices
                for pair in monitor.trading_pairs:
                    if pair not in current_prices:
                        current_prices[pair] = None
            
            time.sleep(2)  # Update every 2 seconds
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            # Ensure all trading pairs are still in current_prices even on error
            for pair in monitor.trading_pairs:
                if pair not in current_prices:
                    current_prices[pair] = None
            time.sleep(5)  # Wait longer on error

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/prices')
def get_prices():
    global current_prices
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Ensure all trading pairs are included in response
    response_prices = {}
    for pair in monitor.trading_pairs:
        response_prices[pair] = current_prices.get(pair, None)
    
    return jsonify({
        'prices': response_prices,
        'timestamp': timestamp
    })

@app.route('/api/start_monitoring', methods=['POST'])
def start_monitoring():
    global monitoring_active, monitoring_thread
    
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitor_prices, daemon=True)
        monitoring_thread.start()
        return jsonify({'status': 'success', 'message': 'Monitoring started'})
    else:
        return jsonify({'status': 'error', 'message': 'Monitoring already active'})

@app.route('/api/stop_monitoring', methods=['POST'])
def stop_monitoring():
    global monitoring_active
    
    monitoring_active = False
    return jsonify({'status': 'success', 'message': 'Monitoring stopped'})

@app.route('/api/monitoring_status')
def get_monitoring_status():
    global monitoring_active, futures_mode
    return jsonify({
        'monitoring_active': monitoring_active,
        'futures_mode': futures_mode
    })

@app.route('/api/toggle_futures', methods=['POST'])
def toggle_futures():
    global futures_mode, monitor
    
    futures_mode = not futures_mode
    monitor.set_futures_mode(futures_mode)
    
    status = 'ON' if futures_mode else 'OFF'
    return jsonify({
        'status': 'success',
        'futures_mode': futures_mode,
        'message': f'Futures mode switched to {status}'
    })

@app.route('/api/font_size', methods=['POST'])
def set_font_size():
    global font_size
    
    data = request.get_json()
    font_size = data.get('size', 16)
    return jsonify({'status': 'success'})

@app.route('/api/trading_pairs')
def get_trading_pairs():
    pairs = monitor.trading_pairs
    thresholds = monitor.price_thresholds
    return jsonify({
        'pairs': pairs,
        'thresholds': thresholds
    })

@app.route('/api/add_pair', methods=['POST'])
def add_trading_pair():
    data = request.get_json()
    pair = data.get('pair')
    upper = data.get('upper')
    lower = data.get('lower')
    
    if not pair or upper is None or lower is None:
        return jsonify({'status': 'error', 'message': 'Missing required fields'})
    
    if upper <= lower:
        return jsonify({'status': 'error', 'message': 'Upper price must be greater than lower price'})
    
    try:
        # Normalize pair format
        pair = normalize_pair_format(pair)
        
        # Add to monitor
        if pair not in monitor.trading_pairs:
            monitor.trading_pairs.append(pair)
        
        monitor.price_thresholds[pair] = {
            'upper': upper,
            'lower': lower,
            'upper_action': 'None',
            'upper_price': upper,
            'lower_action': 'None',
            'lower_price': lower,
            'trade_amount': 0.0
        }
        
        # Initialize old_data and trade_executed
        monitor.old_data[pair] = {'price': None, 'time': None}
        monitor.trade_executed[pair] = {'upper': False, 'lower': False}
        
        # Save configuration
        monitor.save_config()
        
        # Always add to current_prices, even if price fetch fails
        current_prices[pair] = None  # Will be updated by background monitoring
        
        # Try to fetch price immediately
        try:
            inst_id = pair.replace('/', '-')
            current_price = monitor.get_current_price(inst_id)
            if current_price is not None:
                current_prices[pair] = current_price
        except Exception as e:
            print(f"Warning: Could not fetch initial price for {pair}: {e}")
            # Keep pair in current_prices with None value - will be updated by background monitoring
        
        return jsonify({'status': 'success', 'message': f'Added {pair} successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error adding pair: {str(e)}'})

def normalize_pair_format(input_pair):
    """Normalize trading pair format to standard format"""
    # Remove any spaces
    input_pair = input_pair.replace(' ', '')
    
    # If it's just a coin name (e.g., "DOT"), add "/USDT"
    if '/' not in input_pair and '-' not in input_pair:
        return input_pair + '/USDT'
    
    # If it's in format "DOT-USDT", convert to "DOT/USDT"
    if '-' in input_pair:
        return input_pair.replace('-', '/')
    
    # If it's already in format "DOT/USDT", return as is
    return input_pair

@app.route('/api/edit_pair', methods=['POST'])
def edit_trading_pair():
    data = request.get_json()
    pair = data.get('pair')
    upper = data.get('upper')
    lower = data.get('lower')
    
    if not pair or upper is None or lower is None:
        return jsonify({'status': 'error', 'message': 'Missing required fields'})
    
    if upper <= lower:
        return jsonify({'status': 'error', 'message': 'Upper price must be greater than lower price'})
    
    try:
        if pair in monitor.price_thresholds:
            monitor.price_thresholds[pair]['upper'] = upper
            monitor.price_thresholds[pair]['lower'] = lower
            monitor.price_thresholds[pair]['upper_price'] = upper
            monitor.price_thresholds[pair]['lower_price'] = lower
            
            # Reset trade executed flags for new thresholds
            monitor.trade_executed[pair] = {'upper': False, 'lower': False}
            
            # Save configuration
            monitor.save_config()
            
            return jsonify({'status': 'success', 'message': f'Updated {pair} successfully'})
        else:
            return jsonify({'status': 'error', 'message': f'Trading pair {pair} not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating pair: {str(e)}'})

@app.route('/api/delete_pair', methods=['POST'])
def delete_trading_pair():
    data = request.get_json()
    pair = data.get('pair')
    
    if not pair:
        return jsonify({'status': 'error', 'message': 'Missing pair parameter'})
    
    try:
        if pair in monitor.trading_pairs:
            monitor.trading_pairs.remove(pair)
        
        if pair in monitor.price_thresholds:
            del monitor.price_thresholds[pair]
        
        if pair in monitor.old_data:
            del monitor.old_data[pair]
        
        if pair in monitor.trade_executed:
            del monitor.trade_executed[pair]
        
        # Save configuration
        monitor.save_config()
        
        return jsonify({'status': 'success', 'message': f'Deleted {pair} successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error deleting pair: {str(e)}'})

@app.route('/api/ntfy_config', methods=['GET', 'POST'])
def ntfy_config():
    if request.method == 'GET':
        # Load current NTFY config from monitor
        config = monitor.get_ntfy_config()
        return jsonify({'status': 'success', 'config': config})
    
    elif request.method == 'POST':
        data = request.get_json()
        server = data.get('server', '').strip()
        topic = data.get('topic', '').strip()
        password = data.get('password', '').strip()
        
        if not server or not topic:
            return jsonify({'status': 'error', 'message': 'Server and topic are required'})
        
        try:
            # Update monitor's NTFY settings (this will also save to file)
            monitor.update_ntfy_config(server, topic, password)
            
            return jsonify({'status': 'success', 'message': 'NTFY configuration updated successfully'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Error updating NTFY config: {str(e)}'})

@app.route('/api/test_ntfy', methods=['POST'])
def test_ntfy():
    data = request.get_json()
    server = data.get('server', '').strip()
    topic = data.get('topic', '').strip()
    password = data.get('password', '').strip()
    
    if not server or not topic:
        return jsonify({'status': 'error', 'message': 'Server and topic are required'})
    
    try:
        # Send test notification
        success = monitor.send_test_ntfy_notification(server, topic, password)
        if success:
            return jsonify({'status': 'success', 'message': 'Test notification sent successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send test notification'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error sending test notification: {str(e)}'})

if __name__ == '__main__':
    # Load initial configuration
    monitor.load_config()
    
    # Start monitoring if there are trading pairs configured
    if monitor.trading_pairs:
        print("Trading pairs found, monitoring can be started via web interface")
    
    app.run(debug=False, host='0.0.0.0', port=5000) 