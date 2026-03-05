# 🤖 Grid Bot: Infinite Range Stability Grid (ISGB) v1.5

Dự án này là một thuật toán giao dịch lưới tự động (**Grid Bot**) được thiết kế để treo máy 24/7 trên môi trường MetaTrader 5 (MT5). Hệ thống này ưu tiên duy trì trạng thái tài khoản an toàn với **Tài khoản Cents (Micro)** thông qua quản lý vị thế thông minh và logic "Zone DCA" kết hợp bảo vệ Equity.

---

## 🏗️ Kiến trúc Chiến lược Cốt lõi (Strategies)

Bot ISGB v1.5 áp dụng đồng thời các cơ chế sau để bảo vệ tài khoản khỏi biến động khắc nghiệt thay vì nhồi lệnh Martingale truyền thống rủi ro cao:

### 1. 📏 ATR-Based Dynamic Spacing (Lưới Động)
Thay vì sử dụng khoảng cách Pip lưới cố định, Bot tự động tính chu kỳ trung bình quá khứ thông qua **ATR(14) trên khung H1**. Khi thị trường biến động mạnh, lưới sẽ tự dãn rộng để tránh nhồi lệnh liên tục dính chùm; khi thị trường êm ả, lưới thu hẹp lại để bắt sóng lăn tăn.

### 2. 🥊 Zone DCA & Lưới Bậc Thang ("Cú đấm thép")
Bot áp dụng Non-Martingale System (lot = base_lot) ở giai đoạn đầu và chỉ tung "Hỏa lực" mạnh khi xác suất đảo chiều cao.
*   **Tầng 1 - 10:** Multiplier 1.0 (Giữ Margin cực thấp).
*   **Tầng 11 - 15:** Multiplier 1.5 (Tăng tiến nhẹ Volume khi bị âm sâu).
*   **Tầng 16 (Zone DCA):** Khi giá đã đi qua xa (`> 500 points` quãng đường lưới) VÀ chỉ số **RSI(14)** tiến vào trạng thái *Quá mua/Quá bán cực đại*, Bot bơm lệnh DCA Lớn (bằng tổng Volume các lệnh trước) để kéo giá hòa vốn (Break-Even) về sát cực độ với giá rơi hiện tại. Chỉ cần nến bật lại nhẹ là dọn bù lỗ toàn bộ hệ thống.

### 3. 🛡️ High-Water Mark (HWM) Equity Hedge
Bot có Module `RiskManager` luôn ghi nhận mức **Equity lớn nhất (HWM)** của tài khoản. 
Nếu Bot gồng lỗ và tài khoản sụt giảm (Drawdown) vượt **ngưỡng nguy hiểm 15%**, Bot sẽ tự động **Bơm Ngược Chiều 1 lệnh Hedge Net Lot** ngay lập tức để khoá băng tài khoản lại, không cho mức lỗ tiếp tục tụt dốc.
*Hedge Khẩn Cấp (20%):* Dừng bot khẩn cấp để xử lý tay nếu Trend sập dài không báo trước.

### 4. 📉 Dynamic Basket Take Profit (Chốt lời động)
Để giải phóng lệnh nhanh nhất có thể theo cấp bậc gồng tính điểm Break-even chung của rổ lệnh:
*   Đang gồng **1-4 lệnh**: TP Target cao (ví dụ: `+15 Pips`).
*   Đang gồng **5-8 lệnh**: TP Target thấp dần (ví dụ: `+5 Pips`) nhằm dọn Margin.
*   Đang gồng **>8 lệnh**: Mọi lệnh chốt giá `Hòa vốn` (0 Pips), tập trung sinh tồn, cắt tỉa rủi ro, không tham lam lời.

### 5. ⏰ Múi giờ & Bộ lọc Phí (Spread/Time Filter)
*   **Time Filter:** Bot sẽ ngừng tung lệnh DCA vào các khung giờ giao dịch độc hại (Rollover - Giao phiên múi giờ) VD: `04:30 AM - 05:30 AM (Giờ VN)`.
*   **Spread Filter:** Nếu độ dãn nở Spread của sàn vọt trên `5 Pips`, bot ngắt mở lệnh mới để bảo vệ phần vốn hụt vô hình lãng phí.

### 6. 📉 Initial RSI Entry (Tín hiệu Khởi gốc)
Bộ lưới sẽ không nổ ngẫu nhiên. Vòng lặp đầu tiên chỉ nổ súng (Sell/Buy) khi biểu đồ chạm vùng `RSI 70/30 (Quá mua/Quá bán)` nhằm giảm thiệu độ nhiễu của một trend mới mọc.

---

## 🛠️ Tech Stack & Requirements

*   **Ngôn ngữ:** Python `>= 3.12`
*   **Sàn giao dịch tối ưu:** **Exness Account Cent** (Margin Vô cực / Không Stop Out sớm).
*   **Các tính năng tương lai / Phiên bản hiện tại:**
    *   MT5 API Connector qua thư viện `MetaTrader5` ✅ 
    *   Quản trị Virtual Env với `uv` ✅
    *   Tính toán logic bằng `pandas` ✅ 

## 🚀 Hướng Dẫn Chạy (Quick Start)

**1. Copy thư mục cài đặt (`uv`)**
Kích hoạt venv (tránh confict thư viện Python máy chủ).

**2. Điều chỉnh API sàn (.env)**
Copy `.env.example` thành `.env`, đặt tài khoản ID, Pass và MT5 Server Name của Exness Trial / Live.

**3. Bật AutoTrading MT5**
Mở Exness MT5 App, đăng nhập Account, bật nút "Algo Trading" màu xanh góc trên.

**4. Khởi chạy Bot**
```sh
python main.py
```
