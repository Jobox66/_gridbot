import logging

logger = logging.getLogger(__name__)

class SignalModule:
    def __init__(self, rsi_period: int = 14, overbought_threshold: float = 70.0, oversold_threshold: float = 30.0, extreme_overbought: float = 80.0, extreme_oversold: float = 20.0):
        """
        Khởi tạo Mô-đun Tín hiệu RSI.
        
        :param rsi_period: Chu kỳ RSI (Mặc định 14).
        :param overbought_threshold: Ngưỡng quá mua để kích hoạt Lệnh ENTRY đầu tiên (Sell).
        :param oversold_threshold: Ngưỡng quá bán để kích hoạt Lệnh ENTRY đầu tiên (Buy).
        :param extreme_overbought: Ngưỡng quá mua CỰC ĐẠI để xác nhận tung "Cú đấm thép".
        :param extreme_oversold: Ngưỡng quá bán CỰC ĐẠI để xác nhận tung "Cú đấm thép".
        """
        self.rsi_period = rsi_period
        self.overbought_threshold = overbought_threshold
        self.oversold_threshold = oversold_threshold
        self.extreme_overbought = extreme_overbought
        self.extreme_oversold = extreme_oversold

    def check_initial_entry_signal(self, current_rsi: float) -> str:
        """
        Kiểm tra tín hiệu mở lệnh lưới đầu tiên (Entry gốc).
        Thay vì chỉ rải tùy tiện, Grid sẽ bắt đầu khi RSI đi vào vùng quá mua / quá bán.
        
        :param current_rsi: Giá trị RSI hiện hành (H1 / H4).
        :return: 'BUY' nếu RSI chạm Oversold, 'SELL' nếu chạm Overbought, None nếu nằm ở lững lờ.
        """
        if current_rsi <= self.oversold_threshold:
            logger.info(f"RSI Initial Entry Signal: BUY (RSI={current_rsi} <= {self.oversold_threshold})")
            return "BUY"
        elif current_rsi >= self.overbought_threshold:
            logger.info(f"RSI Initial Entry Signal: SELL (RSI={current_rsi} >= {self.overbought_threshold})")
            return "SELL"
        return None

    def confirm_zone_dca_signal(self, current_rsi: float, is_buy_grid: bool) -> bool:
        """
        Kiểm tra tín hiệu DCA Trung Hòa.
        Điều kiện để lưới Tầng 16 (Cú đấm thép) được tung ra phải kết hợp với việc RSI xác nhận đảo chiều mạnh.
        
        :param current_rsi: Giá trị RSI hiện hành.
        :param is_buy_grid: Lưới hiện hành đang cản chiều BUY hay SELL?
        :return: True nếu RSI đủ cực đoan ngược chiều để nhồi lệnh DCA Lớn.
        """
        # Nếu đang là lưới đánh Buy (xu hướng rơi giá quá sâu), cần RSI oversold mạnh
        if is_buy_grid and current_rsi <= self.extreme_oversold:
            logger.info(f"Zone DCA (Buy) Confirmed! Extreme RSI: {current_rsi} <= {self.extreme_oversold}")
            return True
            
        # Nếu đang là đánh Sell Grid (xu hướng tăng giá quá hỗn), cần RSI overbought mạnh
        if not is_buy_grid and current_rsi >= self.extreme_overbought:
            logger.info(f"Zone DCA (Sell) Confirmed! Extreme RSI: {current_rsi} >= {self.extreme_overbought}")
            return True

        return False
