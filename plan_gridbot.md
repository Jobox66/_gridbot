# Kế Hoạch Xây Dựng Grid Bot (ISGB)


## 1. Mục tiêu và Môi trường áp dụng
*   **Số vốn:** 200 USD nạp vào tài khoản Cent -> **20.000 USC**.
*   **Sàn giao dịch:** **Exness (Tài khoản Cent)**.
*   **Thời gian:** Treo máy tự động 24/7.

## 2. Thông số Tiền tệ & Khung giờ (The Mean-Reversion Selection)
*   **Cặp tiền ưu tiên:** **AUD/NZD**, EUR/GBP, hoặc NZD/CAD. Đây là các cặp có tính chất Mean-reverting (hồi mã thương) và đi ngang sideway trong biên độ rộng.
*   **Cặp tiền cần tránh:** Gold (XAU/USD), BTC/USD hoặc JPY vì tính chất trend biến động quá mạnh. Nếu bắt buộc chạy Vàng/BTC, phải chuyển sang **Macro Grid** (lưới dãn 200-500 pips) và chỉ đánh 1 chiều (One-way).
*   **Filter Khung giờ & Spread:**
    *   **Max Spread Filter:** Chỉ mở lệnh lệnh mới nếu Spread < 5 pips.
    *   **Time Window Filter:** Đóng băng giao dịch (không mở lệnh mới) vào giờ giao phiên (Rollover) để tránh giãn Spread mạnh quét tài khoản (Nghỉ từ 4:30 AM - 5:30 AM giờ VN).

## 3. Quản trị Đòn bẩy & Rủi ro
*   **Logic Margin:** Sử dụng đòn bẩy Vô cực (Unlimited, >= 1:2000) của Exness để mức Margin Used bị giam lẻ tẻ gần như bằng 0. Hệ quả: Margin Level luôn ở hàng chục nghìn %, giúp tài khoản có thể gồng lỗ đến cent cuối cùng.
*   **Logic Kiểm soát mức Đòn bẩy:** Theo dõi gắt gao hàm `ACCOUNT_LEVERAGE`. Tại Exness, sàn thường tự động hạ đòn bẩy xuống 1:200 trước các tin tức kinh tế quan trọng. Lúc này, bot phát hiện đòn bẩy giảm sẽ lập tức **tự động khóa mở lệnh mới** để bảo vệ Margin Level.
*   **Safety Zone & Global Exit:** 
    *   Sử dụng **RSI Filter (H4/D1)** để xác định điểm bắt đầu vào lệnh (chỉ vớt tại vùng quá mua/quá bán).
    *   Cơ chế **Equity Hedge**: Đặt Soft Stop Loss. Nếu Drawdown chạm ngưỡng nguy hiểm 15-20% (hoặc 25%), bot sẽ bung thế Hedge đối ứng để khóa lỗ ngay lập tức.
    *   Thiết lập Daily Profit Target, để nếu đạt đủ thì bot sẽ Reset chu kỳ.

## 4. Cấu trúc Lưới (Grid Strategy)
*   **Chỉ báo khoảng cách (ATR-Based Dynamic Spacing):**
    Khoảng cách lưới được cấu hình co giãn tự động qua chỉ báo **ATR (Average True Range)** thay vì Fixed Pips cố định.
    *Ví dụ:* `Grid Step = 0.5 x ATR(14)`. Nếu biến động tăng cao, lưới tự dãn rộng nhằm tránh nhồi lệnh liên tục dính chùm.
*   **Quản lý Lot Size (Non-Martingale):**
    *   **Khối lượng khởi tạo:** 0.1 USC (tương đương 0.001 Lot Standard).
    *   Hệ số nhồi lệnh (Multiplier): Chọn mức **1.1x đến 1.3x** (tuyệt đối không dùng 2.0x như Martingale truyền thống).
*   **Phân bổ ngân sách:** Sử dụng chiến lược *Lưới đa tầng*. 30% quỹ dành cho Lưới chủ động đánh thường xuyên. 70% quỹ đóng vai trò Lưới dự phòng ngủ đông, chỉ kích hoạt để đỡ lệnh nếu giá sụt giảm cực mạnh.
*   **Số lệnh tối đa:** 20-30 lệnh (Max Orders).

## 5. Chốt lời tổng (Dynamic Basket TP)
Áp dụng Basket TP giảm dần theo cấp độ số lệnh nhằm đẩy nhanh quá trình thoát thân ở chu kỳ dài:
*   **Từ lệnh 1 đến 4:** TP đạt 15-20 pips.
*   **Từ lệnh 5 đến 8:** Thay đổi TP về mức 5 pips.
*   **Từ 9 lệnh trở đi:** TP = 0 pips (Thoát hòa vốn ngay lập tức để ngắt chu kỳ rủi ro).
