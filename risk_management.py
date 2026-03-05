import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, 
                 min_leverage: float = 200.0, 
                 hedge_drawdown_threshold: float = 0.15,
                 emergency_drawdown_threshold: float = 0.20):
        """
        Khởi tạo Risk Manager.
        
        :param min_leverage: Mức đòn bẩy tối thiểu cho phép (vd: 200 cho 1:200).
        :param hedge_drawdown_threshold: Ngưỡng Drawdown để kích hoạt Equity Hedge (15%).
        :param emergency_drawdown_threshold: Ngưỡng Drawdown để kích hoạt Khẩn cấp sau khi đã DCA nhồi (20%).
        """
        self.min_leverage = min_leverage
        self.hedge_drawdown_threshold = hedge_drawdown_threshold
        self.emergency_drawdown_threshold = emergency_drawdown_threshold
        
        # High-Water Mark tracking
        self.high_water_mark: float = 0.0
        
        # Trạng thái cờ an toàn
        self.news_lock_flag: bool = False
        self.equity_hedge_active: bool = False
        self.emergency_hedge_active: bool = False

    def update_high_water_mark(self, current_equity: float):
        """
        Cập nhật mức High-Water Mark (HWM).
        """
        if current_equity > self.high_water_mark:
            self.high_water_mark = current_equity
            logger.info(f"New High-Water Mark recorded: {self.high_water_mark}")
            
    def reset_high_water_mark(self, current_equity: float):
        """
        Reset HWM định kỳ (ví dụ: cuối ngày).
        """
        self.high_water_mark = current_equity
        logger.info(f"High-Water Mark reset to: {self.high_water_mark}")

    def check_leverage(self, current_leverage: float) -> bool:
        """
        Kiểm tra mức đòn bẩy hiện tại của tài khoản.
        Nếu đòn bẩy < min_leverage (ví dụ sàn hạ đòn bẩy trước tin tin tức),
        bật news_lock_flag để chặn vào lệnh mới.
        
        :return: True nếu an toàn để giao dịch, False nếu đòn bẩy quá thấp.
        """
        if current_leverage < self.min_leverage:
            if not self.news_lock_flag:
                logger.warning(f"Leverage dropped to 1:{current_leverage}. Activating News Lock!")
                self.news_lock_flag = True
            return False
            
        if self.news_lock_flag:
            logger.info(f"Leverage restored to 1:{current_leverage}. Deactivating News Lock.")
            self.news_lock_flag = False
            
        return True

    def check_equity_hedge(self, current_equity: float, open_positions_net_lot: float) -> bool:
        """
        Kiểm tra sụt giảm tài khoản so với HWM.
        
        :param current_equity: Vốn chủ sở hữu hiện tại.
        :param open_positions_net_lot: Tổng số Lot Net đang mở (để báo cáo nếu cần).
        :return: True nếu cần kích hoạt Hedge (bơm 1 lệnh đối ứng).
        """
        if self.high_water_mark == 0:
            self.update_high_water_mark(current_equity)
            return False

        drawdown = (self.high_water_mark - current_equity) / self.high_water_mark

        if drawdown >= self.hedge_drawdown_threshold and not self.equity_hedge_active:
            logger.critical(f"Drawdown {drawdown:.2%} hit HEDGE threshold! Net Lot to hedge: {open_positions_net_lot}")
            self.equity_hedge_active = True
            return True
        
        # Có thể thêm logic gỡ cờ khi Drawdown hồi sinh
        if drawdown < self.hedge_drawdown_threshold and self.equity_hedge_active:
            logger.info(f"Drawdown recovered to {drawdown:.2%}. Deactivating Equity Hedge state.")
            self.equity_hedge_active = False

        return False

    def check_emergency_hedge(self, current_equity: float) -> bool:
        """
        Kiểm tra sụt giảm tài khoản mức độ cực đoan (khi Zone DCA thất bại).
        
        :param current_equity: Vốn chủ sở hữu hiện tại.
        :return: True nếu cần đóng băng tài khoản khẩn cấp bằng lệnh Hedge 100%.
        """
        if self.high_water_mark == 0:
            return False
            
        drawdown = (self.high_water_mark - current_equity) / self.high_water_mark

        if drawdown >= self.emergency_drawdown_threshold and not self.emergency_hedge_active:
            logger.critical(f"EMERGENCY! Drawdown {drawdown:.2%} hit EMERGENCY threshold! Locking account.")
            self.emergency_hedge_active = True
            return True

        return False

    def check_global_exit(self, daily_profit: float, target_profit: float) -> bool:
        """
        Kiểm tra tổng lợi nhuận trong ngày.
        
        :param daily_profit: Lợi nhuận đã chốt trong ngày tính tới hiện tại.
        :param target_profit: Mục tiêu lợi nhuận trong ngày để reset chu kỳ.
        :return: True nếu đã đạt target và cần Global Exit.
        """
        if target_profit > 0 and daily_profit >= target_profit:
            logger.info(f"Daily profit target reached! ({daily_profit}/{target_profit}). Initiating Global Exit.")
            return True
        return False
