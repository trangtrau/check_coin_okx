# 🖥️ Crypto Price Monitor - Desktop App

Ứng dụng desktop GUI để theo dõi giá cryptocurrency từ web API với cửa sổ luôn on-top và hiệu ứng trong mờ.

## 🚀 Tính năng

- **Kết nối API**: Tự động kết nối với web API tại https://coin.hoangvan.name.vn
- **Cửa sổ luôn on-top**: Hiển thị giá crypto trong cửa sổ luôn ở trên cùng
- **Hiệu ứng trong mờ**: Cửa sổ có độ trong suốt 90%
- **Có thể kéo thả**: Di chuyển cửa sổ giá bằng chuột
- **Real-time updates**: Cập nhật giá mỗi 2 giây
- **Quản lý trading pairs**: Thêm/sửa/xóa cặp tiền
- **Futures mode**: Bật/tắt chế độ futures
- **Mở web interface**: Nút để mở web interface trong browser

## 📋 Yêu cầu

- Python 3.7+
- tkinter (thường có sẵn với Python)
- requests library
- Kết nối internet

## 🛠️ Cài đặt

1. **Cài đặt dependencies:**
```bash
pip install -r requirements_desktop.txt
```

2. **Chạy ứng dụng:**
```bash
python desktop_monitor.py
```

## 🎯 Cách sử dụng

### 1. Khởi động ứng dụng
- Chạy `python desktop_monitor.py`
- Ứng dụng sẽ tự động kết nối với web API

### 2. Kiểm tra kết nối
- **API Status**: Hiển thị trạng thái kết nối (Connected/Disconnected)
- **Refresh Data**: Nhấn để làm mới dữ liệu

### 3. Quản lý trading pairs
- **Xem danh sách**: Trading pairs hiện tại sẽ hiển thị trong listbox
- **Thêm pair**: Nhập pair name, upper/lower thresholds và nhấn "Add Pair"
- **Cập nhật**: Nhấn "Refresh Data" để cập nhật danh sách

### 4. Bật monitoring
- Nhấn **"Start Monitoring"** để bắt đầu theo dõi giá
- Ứng dụng sẽ cập nhật giá mỗi 2 giây

### 5. Hiển thị cửa sổ giá
- Nhấn **"Show Price Window"** để mở cửa sổ luôn on-top
- Cửa sổ sẽ hiển thị giá real-time với hiệu ứng trong mờ
- **Kéo thả**: Click và kéo để di chuyển cửa sổ
- **Đóng**: Nhấn nút "✕" để đóng cửa sổ

### 6. Futures Mode
- Tích vào checkbox "Enable" để bật futures mode
- Ứng dụng sẽ gửi request toggle futures đến web API

## 🎨 Giao diện

### Main Window
- **API Status**: Hiển thị trạng thái kết nối
- **Control Buttons**: Start/Stop monitoring, Show price window
- **Futures Mode**: Checkbox để bật/tắt futures
- **Trading Pairs**: Danh sách và form thêm pair
- **Current Prices**: Hiển thị giá hiện tại
- **Bottom Buttons**: Mở web interface, refresh data

### Price Window (Always On Top)
- **Title**: "💎 Live Crypto Prices"
- **Timestamp**: Thời gian cập nhật cuối
- **Price List**: Danh sách giá theo format:
  - BTC/USDT: $119,459.800000 (6 decimal places)
  - ETH/USDT: $4,485.500 (3 decimal places)
- **Draggable**: Có thể kéo thả bằng chuột
- **Semi-transparent**: Độ trong suốt 90%

## 🔧 Cấu hình

### API URL
Mặc định kết nối đến: `https://coin.hoangvan.name.vn`

Để thay đổi, chỉnh sửa dòng này trong code:
```python
self.api_base_url = "https://coin.hoangvan.name.vn"
```

### Update Frequency
Mặc định cập nhật mỗi 2 giây. Để thay đổi, chỉnh sửa:
```python
time.sleep(2)  # Update every 2 seconds
```

### Window Transparency
Mặc định độ trong suốt 90%. Để thay đổi:
```python
self.price_window.attributes('-alpha', 0.9)  # 0.9 = 90% opacity
```

## 🐛 Troubleshooting

### Không kết nối được API
1. Kiểm tra kết nối internet
2. Kiểm tra URL API có đúng không
3. Kiểm tra web server có đang chạy không

### Cửa sổ giá không hiển thị
1. Đảm bảo đã nhấn "Show Price Window"
2. Kiểm tra cửa sổ có bị ẩn không
3. Restart ứng dụng nếu cần

### Giá không cập nhật
1. Kiểm tra "Start Monitoring" đã được nhấn chưa
2. Kiểm tra API Status có "Connected" không
3. Nhấn "Refresh Data" để thử lại

### Lỗi tkinter
1. Đảm bảo Python có tkinter:
```bash
python -c "import tkinter; print('tkinter available')"
```
2. Trên Linux, có thể cần cài đặt:
```bash
sudo apt-get install python3-tk
```

## 📱 Tương thích

- **Windows**: ✅ Hoạt động tốt
- **macOS**: ✅ Hoạt động tốt
- **Linux**: ✅ Hoạt động tốt (cần cài python3-tk)

## 🔒 Bảo mật

- **Chỉ đọc dữ liệu**: Ứng dụng chỉ đọc dữ liệu từ API
- **Không lưu mật khẩu**: Không lưu trữ thông tin nhạy cảm
- **HTTPS**: Kết nối an toàn qua HTTPS

## 📝 License

MIT License - Tự do sử dụng và chỉnh sửa.

---

**Lưu ý**: Ứng dụng này cần web API đang chạy để hoạt động. Đảm bảo web server đã được khởi động trước khi chạy desktop app. 