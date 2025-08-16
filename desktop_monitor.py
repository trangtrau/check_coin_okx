import sys
import json
import os
import requests
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter
from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget, 
                            QPushButton, QSlider, QHBoxLayout, QColorDialog,
                            QMainWindow, QDialog, QGridLayout, QSpinBox)


API_URL = "https://coin.hoangvan.name.vn/api/prices"
CONFIG_FILE = "desktop.json"


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 200)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        layout = QGridLayout()
        
        # Font Size Setting
        layout.addWidget(QLabel("Font Size:"), 0, 0)
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(8)
        self.font_size_slider.setMaximum(32)
        self.font_size_slider.setValue(self.parent.font_size if self.parent else 14)
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        layout.addWidget(self.font_size_slider, 0, 1)
        
        self.font_size_label = QLabel(f"{self.font_size_slider.value()}px")
        layout.addWidget(self.font_size_label, 0, 2)
        
        # Text Color Setting
        layout.addWidget(QLabel("Text Color:"), 1, 0)
        
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        layout.addWidget(self.color_button, 1, 1, 1, 2)
        
        # Close Button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button, 2, 1)
        
        self.setLayout(layout)
        
    def update_font_size(self, value):
        try:
            self.font_size_label.setText(f"{value}px")
            if self.parent:
                self.parent.update_font_size(value)
        except Exception as e:
            print(f"Error updating font size: {e}")
            
    def choose_color(self):
        try:
            # Sử dụng QColorDialog với parent widget
            color = QColorDialog.getColor(QColor(self.parent.text_color), self, "Choose Text Color")
            if color.isValid() and self.parent:
                color_name = color.name()
                print(f"Selected color: {color_name}")  # Debug
                self.parent.update_text_color(color_name)
        except Exception as e:
            print(f"Error choosing color: {e}")
            # Fallback to a safe color
            if self.parent:
                self.parent.update_text_color("#00ff00")


class TransparentWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = self.load_config()
        
        # Settings
        self.font_size = self.config.get('font_size', 14)
        self.text_color = self.config.get('text_color', "lime")
        
        self.initUI()
        self.update_prices()
        
        # Timer cập nhật mỗi 2 giây
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_prices)
        self.timer.start(1000)  # 2 seconds
        
        # Settings button
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 100);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 150);
            }
        """)
        self.settings_button.clicked.connect(self.show_settings)
        
        # Add settings button to layout
        self.layout().addWidget(self.settings_button)
        
        # Settings dialog
        self.settings_dialog = None
        
        # Restore window position
        self.restore_position()

    def load_config(self):
        """Load configuration from JSON file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"Loaded config: {config}")
                    return config
            else:
                # Default configuration
                default_config = {
                    'font_size': 14,
                    'text_color': 'lime',
                    'window_position': {'x': 100, 'y': 100}
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                'font_size': 14,
                'text_color': 'lime',
                'window_position': {'x': 100, 'y': 100}
            }
    
    def save_config(self, config=None):
        """Save configuration to JSON file."""
        try:
            if config is None:
                config = {
                    'font_size': self.font_size,
                    'text_color': self.text_color,
                    'window_position': {
                        'x': self.pos().x(),
                        'y': self.pos().y()
                    }
                }
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                print(f"Saved config: {config}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def restore_position(self):
        """Restore window position from config."""
        try:
            position = self.config.get('window_position', {'x': 100, 'y': 100})
            self.move(position['x'], position['y'])
            print(f"Restored position: {position}")
        except Exception as e:
            print(f"Error restoring position: {e}")

    def initUI(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        self.labels = {}
        font = QFont("Segoe UI", self.font_size, QFont.Bold)

        # Tạo label cho từng coin
        for coin in ["BTC/USDT", "DOT/USDT", "XCH/USDT", "ETHW/USDT"]:
            lbl = QLabel(f"{coin}  ---")
            lbl.setFont(font)
            lbl.setStyleSheet(f"color: {self.text_color}; background-color: transparent;")
            layout.addWidget(lbl)
            self.labels[coin] = lbl

        self.setLayout(layout)

        # Biến hỗ trợ kéo thả
        self.offset = QPoint()
        
    def show_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        
    def update_text_color(self, color):
        try:
            self.text_color = color
            print(f"Updating text color to: {color}")  # Debug
            
            for lbl in self.labels.values():
                if lbl and lbl.isVisible():
                    lbl.setStyleSheet(f"color: {color}; background-color: transparent;")
                    print(f"Updated label style: color: {color}; background-color: transparent;")
            
            # Save configuration
            self.save_config()
        except Exception as e:
            print(f"Error updating text color: {e}")
            
    def update_font_size(self, size):
        try:
            self.font_size = size
            font = QFont("Segoe UI", size, QFont.Bold)
            
            for lbl in self.labels.values():
                if lbl and lbl.isVisible():
                    lbl.setFont(font)
                    print(f"Updated font size to: {size}")
            
            # Save configuration
            self.save_config()
        except Exception as e:
            print(f"Error updating font size: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def closeEvent(self, event):
        """Save configuration when closing the application."""
        try:
            self.save_config()
            print("Configuration saved on close")
        except Exception as e:
            print(f"Error saving config on close: {e}")
        event.accept()

    def update_prices(self):
        try:
            resp = requests.get(API_URL, timeout=5)
            data = resp.json()
            prices = data["prices"]

            for coin, lbl in self.labels.items():
                if coin in prices:
                    price = prices[coin]
                    if 'BTC' in coin:
                        # BTC: no decimal places
                        formatted_price = f"${int(price)}"
                    else:
                        # Other coins: 3 decimal places
                        formatted_price = f"${price:.3f}"
                    
                    lbl.setText(f"{coin.replace('/USDT','')}: {formatted_price}")
        except Exception as e:
            print("Error fetching data:", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TransparentWidget()
    w.show()
    sys.exit(app.exec_())
