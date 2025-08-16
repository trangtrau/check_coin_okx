# Crypto Price Monitor

Ứng dụng theo dõi giá cryptocurrency và gửi cảnh báo qua NTFY. **Không cần API keys** - chỉ thuần theo dõi giá và gửi cảnh báo.

## 🚀 Tính năng

- **Theo dõi giá real-time** từ OKX API
- **Cảnh báo ngưỡng giá** (upper/lower thresholds)
- **Cảnh báo thay đổi phần trăm** (>5%)
- **Thông báo qua NTFY** (push notifications)
- **Giao diện web** để cấu hình
- **Không cần API keys** - hoạt động ngay lập tức
- **Futures mode với fallback** - Tự động chuyển về spot price cho coin không có futures

## 📋 Yêu cầu

- Python 3.7+
- Kết nối internet
- NTFY (tùy chọn - để nhận thông báo)

## 🛠️ Cài đặt

1. **Clone repository:**
```bash
git clone <repository-url>
cd crypto-price-monitor
```

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

3. **Cấu hình (tùy chọn):**
```bash
cp .env.example .env
# Chỉnh sửa .env nếu cần
```

## 🚀 Chạy ứng dụng

```bash
python main.py
```

Ứng dụng sẽ chạy tại: http://localhost:5000

## 📱 Cấu hình NTFY (tùy chọn)

1. **Tạo topic tại** https://ntfy.sh
2. **Cấu hình trong web interface:**
   - Server: `https://ntfy.sh`
   - Topic: `your-topic-name`
   - Password: (tùy chọn)

## 🎯 Cách sử dụng

### 1. Thêm cặp tiền để theo dõi
- Mở web interface
- Thêm cặp tiền (ví dụ: `BTC/USDT`)
- Đặt ngưỡng trên/dưới

### 2. Bật monitoring
- Click "Start Monitoring"
- Hệ thống sẽ theo dõi giá mỗi 2 giây

### 3. Nhận cảnh báo
- **Ngưỡng giá**: Khi giá vượt ngưỡng trên/dưới
- **Thay đổi phần trăm**: Khi giá thay đổi >5% trong 5 phút
- **Tần suất cảnh báo**: Mỗi coin chỉ cảnh báo 1 lần trong 5 phút để tránh spam

### 4. Futures Mode với Fallback
- **Bật futures mode**: Lấy giá futures cho các coin có sẵn
- **Tự động fallback**: Coin không có futures sẽ tự động dùng spot price
- **Học hỏi**: Hệ thống tự động lưu danh sách coin không có futures
- **Tối ưu**: Lần sau load nhanh hơn với danh sách đã lưu

## 📊 Cấu trúc dự án

```
crypto-price-monitor/
├── main.py                 # Entry point
├── modules/               # Python modules
│   ├── __init__.py
│   ├── config_manager.py  # Quản lý cấu hình
│   ├── crypto_monitor.py  # Logic chính
│   ├── ntfy_manager.py    # Gửi thông báo
│   ├── price_manager.py   # Lấy giá từ API
│   └── web_monitor.py     # Web interface
├── static/                # Frontend files
│   ├── css/
│   └── js/
├── templates/             # HTML templates
├── trading_config.json    # Cấu hình lưu trữ
└── requirements.txt       # Dependencies
```

## 🔧 API Endpoints

- `GET /` - Giao diện chính
- `GET /api/prices` - Lấy giá hiện tại
- `GET /api/trading_pairs` - Lấy danh sách cặp tiền
- `POST /api/add_pair` - Thêm cặp tiền
- `POST /api/edit_pair` - Sửa cặp tiền
- `POST /api/delete_pair` - Xóa cặp tiền
- `POST /api/start_monitoring` - Bật monitoring
- `POST /api/stop_monitoring` - Tắt monitoring
- `GET /api/monitoring_status` - Trạng thái monitoring
- `POST /api/reset_alerts` - Reset alert flags
- `GET /api/alert_status` - Trạng thái alert
- `GET /api/no_futures_coins` - Danh sách coin không có futures mode

## 🎨 Tính năng giao diện

- **Responsive design** - Hoạt động trên mobile/desktop
- **Real-time updates** - Cập nhật giá tự động
- **Collapsible sections** - Giao diện gọn gàng
- **Dark/Light mode** - Tùy chọn theme
- **Font size control** - Điều chỉnh kích thước chữ

## 🔒 Bảo mật

- **Không lưu API keys** - Chỉ theo dõi giá công khai
- **Không giao dịch** - Chỉ monitoring và cảnh báo
- **NTFY password** - Mã hóa base64 khi gửi

## 🐛 Troubleshooting

### Cảnh báo không hoạt động
1. Kiểm tra NTFY configuration
2. Reset alert flags: `POST /api/reset_alerts`
3. Kiểm tra threshold values
4. **Lưu ý**: Mỗi coin chỉ cảnh báo 1 lần trong 5 phút - đợi 5 phút để test lại

### Giá không cập nhật
1. Kiểm tra kết nối internet
2. Restart monitoring
3. Kiểm tra OKX API status

### NTFY không nhận được thông báo
1. Kiểm tra server/topic
2. Test notification trong web interface
3. Kiểm tra NTFY app settings

### Futures mode không hoạt động
1. Kiểm tra danh sách coin không có futures: `GET /api/no_futures_coins`
2. Coin không có futures sẽ tự động fallback về spot price
3. Hệ thống tự động học và lưu coin không có futures

## 📝 License

MIT License - Tự do sử dụng và chỉnh sửa.

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo issue hoặc pull request.

---

**Lưu ý**: Ứng dụng này chỉ dành cho mục đích theo dõi và cảnh báo. Không có tính năng giao dịch tự động. 