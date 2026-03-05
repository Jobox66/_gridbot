import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TakeProfitModule:
    def __init__(self, tp_level_1: float = 15.0, tp_level_2: float = 5.0, tp_level_3: float = 0.0, point_value: float = 0.00001):
        """
        Khởi tạo Mô-đun Quản lý Chốt Lời Tổng (Dynamic Basket TP).
        
        :param tp_level_1: Mục tiêu TP (Pips) cho nhóm 1-4 lệnh.
        :param tp_level_2: Mục tiêu TP (Pips) cho nhóm 5-8 lệnh.
        :param tp_level_3: Mục tiêu TP (Pips) cho nhóm >= 9 lệnh (thoát hòa vốn).
        :param point_value: Giá trị của 1 Point (ví dụ 0.00001 với EURUSD).
        """
        self.tp_level_1_points = tp_level_1 * 10
        self.tp_level_2_points = tp_level_2 * 10
        self.tp_level_3_points = tp_level_3 * 10
        self.point_value = point_value

    def calculate_basket_tp(self, is_buy_grid: bool, open_positions: List[Dict[str, Any]]) -> float:
        """
        Tính toán mức giá Take Profit (Mức giá cụ thể) cho rổ lệnh dựa trên số lượng lệnh đang mở.
        
        Giả định cấu trúc của 1 phần tử trong open_positions:
        {
            "ticket": 12345,
            "type": "BUY",
            "open_price": 1.0500,
            "volume": 0.01,
        }
        
        :param is_buy_grid: Giao dịch Buy hay Sell?
        :param open_positions: Danh sách các lệnh đang mở của cặp hiện tại.
        :return: Mức giá TP chung cho toàn bộ rổ lệnh (Price).
        """
        total_orders = len(open_positions)
        if total_orders == 0:
            return 0.0

        # Tính toán giá Break-Even (Điểm hòa vốn trung bình bình quân gia quyền theo Volume)
        total_volume = sum(pos["volume"] for pos in open_positions)
        total_value = sum(pos["open_price"] * pos["volume"] for pos in open_positions)
        
        if total_volume == 0:
            return 0.0
            
        break_even_price = total_value / total_volume

        # Quyết định Số Point cộng thêm dựa trên số lệnh đang phải gồng
        target_points = 0.0
        if total_orders <= 4:
            target_points = self.tp_level_1_points
            logger.info(f"Basket Level 1 (1-4 orders). Target Pips: {self.tp_level_1_points / 10}")
        elif total_orders <= 8:
            target_points = self.tp_level_2_points
            logger.info(f"Basket Level 2 (5-8 orders). Target Pips: {self.tp_level_2_points / 10}")
        else:
            target_points = self.tp_level_3_points
            logger.info(f"Basket Level 3 (>8 orders). Target Pips: {self.tp_level_3_points / 10} (Break-Even Exit)")

        # Tính mức Giá TP cuối cùng
        target_price_offset = target_points * self.point_value
        
        if is_buy_grid:
            final_tp_price = break_even_price + target_price_offset
        else:
            # Lệnh Sell: Take profit nằm DƯỚI giá Break-Even
            final_tp_price = break_even_price - target_price_offset
            
        logger.debug(f"Break-Even Price: {break_even_price:.5f} | Final Basket TP Price: {final_tp_price:.5f}")
        return final_tp_price
