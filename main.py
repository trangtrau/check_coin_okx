#!/usr/bin/env python3
"""
Main Entry Point for Crypto Price Monitor

This is the main script to run the crypto price monitor application.
"""

import os
import sys
from modules.web_monitor import run_app


def main():
    """Main function to run the application."""
    print("🚀 Starting Crypto Price Monitor...")
    
    # Check if trading features are enabled (optional)
    enable_trading = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
    
    if enable_trading:
        # Only check API keys if trading is enabled
        required_vars = ['OKX_API_KEY', 'OKX_SECRET_KEY', 'OKX_PASSPHRASE']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Trading is enabled but missing required API variables: {', '.join(missing_vars)}")
            print("Please set these variables in your .env file or set ENABLE_TRADING=false")
            print("\nNote: You can still use price monitoring without trading features!")
            sys.exit(1)
        else:
            print("✅ Trading features enabled with API keys")
    else:
        print("ℹ️  Trading features disabled - running in monitoring-only mode")
        print("   (Set ENABLE_TRADING=true and provide API keys to enable trading)")
    
    # Configuration
    config_file = os.getenv('CONFIG_FILE', 'trading_config.json')
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    print(f"📁 Config file: {config_file}")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🐛 Debug mode: {'ON' if debug else 'OFF'}")
    
    try:
        # Run the Flask application
        run_app(
            config_file=config_file,
            host=host,
            port=port,
            debug=debug
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Crypto Price Monitor...")
    except Exception as e:
        print(f"❌ Error running application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 