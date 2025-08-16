"""
Web Monitor Module

Flask web application for the crypto price monitor with RESTful API endpoints for monitoring and alerts.
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
import threading
import time
from .crypto_monitor import CryptoMonitor


def create_app(config_file: str = 'trading_config.json') -> Flask:
    """Create and configure Flask application.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configured Flask application
    """
    # Get the directory where this module is located
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to find the project root
    project_root = os.path.dirname(current_dir)
    
    # Create Flask app with correct template and static folder paths
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'))
    
    # Initialize crypto monitor
    monitor = CryptoMonitor(config_file)
    
    # Global variables for this app instance
    app_state = {
        'monitoring_active': False,
        'monitoring_thread': None,
        'current_prices': {},
        'futures_mode': False,
        'font_size': 16
    }
    
    def monitor_prices():
        """Background monitoring function."""
        nonlocal app_state
        
        while app_state['monitoring_active']:
            try:
                # Get all prices at once
                trading_pairs = monitor.config_manager.get_trading_pairs()
                prices = monitor.price_manager.get_all_prices(trading_pairs)
                if prices:
                    # Ensure all configured trading pairs are in current_prices
                    for pair in trading_pairs:
                        if pair not in prices:
                            prices[pair] = None  # Mark as not fetched yet
                        app_state['current_prices'][pair] = prices.get(pair, None)
                    
                    # Check thresholds and trigger alerts
                    monitor.check_thresholds_and_alert()
                else:
                    # If get_all_prices fails, at least ensure all pairs are in current_prices
                    for pair in trading_pairs:
                        if pair not in app_state['current_prices']:
                            app_state['current_prices'][pair] = None
                
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                # Ensure all trading pairs are still in current_prices even on error
                for pair in monitor.config_manager.get_trading_pairs():
                    if pair not in app_state['current_prices']:
                        app_state['current_prices'][pair] = None
                time.sleep(5)  # Wait longer on error
    
    @app.route('/')
    def index():
        """Main page route."""
        return render_template('index.html')
    
    @app.route('/api/prices')
    def get_prices():
        """Get current prices API endpoint."""
        nonlocal app_state
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Ensure all trading pairs are included in response
        response_prices = {}
        for pair in monitor.config_manager.get_trading_pairs():
            response_prices[pair] = app_state['current_prices'].get(pair, None)
        
        return jsonify({
            'prices': response_prices,
            'timestamp': timestamp
        })
    
    @app.route('/api/start_monitoring', methods=['POST'])
    def start_monitoring():
        """Start monitoring API endpoint."""
        nonlocal app_state
        
        if not app_state['monitoring_active']:
            success = monitor.start_monitoring()
            if success:
                app_state['monitoring_active'] = True
                app_state['monitoring_thread'] = threading.Thread(target=monitor_prices, daemon=True)
                app_state['monitoring_thread'].start()
                return jsonify({'status': 'success', 'message': 'Monitoring started'})
            else:
                return jsonify({'status': 'error', 'message': 'Failed to start monitoring'})
        else:
            return jsonify({'status': 'error', 'message': 'Monitoring already active'})
    
    @app.route('/api/stop_monitoring', methods=['POST'])
    def stop_monitoring():
        """Stop monitoring API endpoint."""
        nonlocal app_state
        
        app_state['monitoring_active'] = False
        monitor.stop_monitoring()
        return jsonify({'status': 'success', 'message': 'Monitoring stopped'})
    
    @app.route('/api/monitoring_status')
    def get_monitoring_status():
        """Get monitoring status API endpoint."""
        nonlocal app_state
        return jsonify({
            'monitoring_active': app_state['monitoring_active'],
            'futures_mode': app_state['futures_mode']
        })
    
    @app.route('/api/toggle_futures', methods=['POST'])
    def toggle_futures():
        """Toggle futures mode API endpoint."""
        nonlocal app_state
        
        app_state['futures_mode'] = not app_state['futures_mode']
        monitor.set_futures_mode(app_state['futures_mode'])
        
        return jsonify({
            'status': 'success',
            'message': f'Futures mode {"enabled" if app_state["futures_mode"] else "disabled"}',
            'futures_mode': app_state['futures_mode']
        })
    
    @app.route('/api/font_size', methods=['POST'])
    def set_font_size():
        """Set font size API endpoint."""
        nonlocal app_state
        
        data = request.get_json()
        if data and 'size' in data:
            app_state['font_size'] = int(data['size'])
            return jsonify({'status': 'success', 'font_size': app_state['font_size']})
        else:
            return jsonify({'status': 'error', 'message': 'Font size not provided'})
    
    @app.route('/api/trading_pairs')
    def get_trading_pairs():
        """Get monitoring pairs API endpoint."""
        try:
            # Get monitoring pairs from config manager directly
            trading_pairs = monitor.config_manager.get_trading_pairs()
            pairs_data = []
            
            for pair in trading_pairs:
                thresholds = monitor.config_manager.get_thresholds(pair)
                if thresholds:
                    pairs_data.append({
                        'pair': pair,
                        'upper': thresholds.get('upper', 0),
                        'lower': thresholds.get('lower', 0)
                    })
                else:
                    # If no thresholds, still include the pair
                    pairs_data.append({
                        'pair': pair,
                        'upper': 0,
                        'lower': 0
                    })
            
            return jsonify({
                'status': 'success',
                'pairs': pairs_data
            })
        except Exception as e:
            print(f"Error in get_trading_pairs: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error loading monitoring pairs: {str(e)}'
            })
    
    @app.route('/api/add_pair', methods=['POST'])
    def add_pair():
        """Add monitoring pair API endpoint."""
        try:
            data = request.get_json()
            pair = data.get('pair', '').strip()
            upper = float(data.get('upper', 0))
            lower = float(data.get('lower', 0))
            
            if not pair or upper <= lower:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid pair or thresholds'
                })
            
            success = monitor.add_trading_pair(pair, upper, lower)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Monitoring pair {pair} added successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to add monitoring pair'
                })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error adding monitoring pair: {str(e)}'
            })
    
    @app.route('/api/edit_pair', methods=['POST'])
    def edit_pair():
        """Edit monitoring pair API endpoint."""
        try:
            data = request.get_json()
            pair = data.get('pair', '').strip()
            upper = float(data.get('upper', 0))
            lower = float(data.get('lower', 0))
            
            if not pair or upper <= lower:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid thresholds'
                })
            
            success = monitor.update_trading_pair(pair, upper, lower)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Monitoring pair {pair} updated successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to update monitoring pair'
                })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error updating monitoring pair: {str(e)}'
            })
    
    @app.route('/api/delete_pair', methods=['POST'])
    def delete_pair():
        """Delete monitoring pair API endpoint."""
        try:
            data = request.get_json()
            pair = data.get('pair', '').strip()
            
            if not pair:
                return jsonify({
                    'status': 'error',
                    'message': 'Pair not specified'
                })
            
            success = monitor.delete_trading_pair(pair)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Monitoring pair {pair} deleted successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to delete monitoring pair'
                })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error deleting monitoring pair: {str(e)}'
            })
    
    @app.route('/api/ntfy_config', methods=['GET', 'POST'])
    def ntfy_config():
        """NTFY configuration API endpoint."""
        if request.method == 'GET':
            try:
                config = monitor.get_ntfy_config()
                return jsonify({
                    'status': 'success',
                    'config': config
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Error loading NTFY config: {str(e)}'
                })
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                server = data.get('server', '').strip()
                topic = data.get('topic', '').strip()
                password = data.get('password', '').strip()
                
                if not server or not topic:
                    return jsonify({
                        'status': 'error',
                        'message': 'Server and topic are required'
                    })
                
                success = monitor.update_ntfy_config(server, topic, password)
                
                if success:
                    return jsonify({
                        'status': 'success',
                        'message': 'NTFY configuration updated successfully'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to update NTFY configuration'
                    })
                    
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Error updating NTFY config: {str(e)}'
                })
    
    @app.route('/api/test_ntfy', methods=['POST'])
    def test_ntfy():
        """Test NTFY notification API endpoint."""
        try:
            data = request.get_json()
            server = data.get('server', '').strip()
            topic = data.get('topic', '').strip()
            password = data.get('password', '').strip()
            
            if not server or not topic:
                return jsonify({
                    'status': 'error',
                    'message': 'Server and topic are required'
                })
            
            # Update config temporarily for test
            monitor.update_ntfy_config(server, topic, password)
            
            # Send test notification
            success = monitor.send_test_ntfy_notification()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Test notification sent successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to send test notification'
                })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error sending test notification: {str(e)}'
            })
    
    @app.route('/api/reset_alerts', methods=['POST'])
    def reset_alerts():
        """Reset alert flags API endpoint."""
        try:
            data = request.get_json()
            pair = data.get('pair', None) if data else None
            
            monitor.reset_alert_flags(pair)
            
            return jsonify({
                'status': 'success',
                'message': f'Alert flags reset for {"all pairs" if pair is None else pair}'
            })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error resetting alerts: {str(e)}'
            })
    
    @app.route('/api/alert_status')
    def get_alert_status():
        """Get alert status API endpoint."""
        try:
            pair = request.args.get('pair', None)
            status = monitor.get_alert_status(pair)
            
            return jsonify({
                'status': 'success',
                'data': status
            })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error getting alert status: {str(e)}'
            })
    
    @app.route('/api/no_futures_coins')
    def get_no_futures_coins():
        """Get list of coins without futures mode API endpoint."""
        try:
            coins = monitor.price_manager.get_no_futures_coins()
            
            return jsonify({
                'status': 'success',
                'coins': coins,
                'count': len(coins)
            })
                
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error getting no-futures coins: {str(e)}'
            })
    
    return app


def run_app(config_file: str = 'trading_config.json', host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the Flask application.
    
    Args:
        config_file: Path to configuration file
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    # Create the Flask app using create_app function
    app = create_app(config_file)
    
    # Load initial configuration
    monitor = CryptoMonitor(config_file)
    
    # Start monitoring if there are trading pairs configured
    if monitor.config_manager.get_trading_pairs():
        print("Monitoring pairs found, price monitoring can be started via web interface")
    
    app.run(debug=debug, host=host, port=port)


if __name__ == '__main__':
    run_app() 