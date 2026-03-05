import logging
from typing import List, Dict, Any
from datetime import datetime, time

logger = logging.getLogger(__name__)

class GridEngine:
    def __init__(self,
                 base_lot: float = 0.001,
                 max_lot_threshold: float = 5.0,
                 atr_multiplier: float = 0.5,
                 max_spread_pips: float = 5.0,
                 point_value: float = 0.00001, # Default for 5-digit brokers
                 zone_dca_distance_points: float = 500.0,
                 restricted_start: time = time(4, 30),
                 restricted_end: time = time(5, 30)):
        """
        Khởi tạo Mô-đun Grid Engine (Quản lý Lưới Bậc Thang & Zone DCA).
        
        :param base_lot: Khối lượng ban đầu (Lot)
        :param max_lot_threshold: Giới hạn tổng lot tối đa an toàn
        :param atr_multiplier: Hệ số nhân cho chỉ báo ATR để tính Grid Step
        :param max_spread_pips: Spread tối đa cho phép mở lệnh mới
        :param point_value: Giá trị của 1 Point (ví dụ 0.00001 cho EURUSD 5 chữ số)
        :param zone_dca_distance_points: Khoảng cách tối thiểu để "Cú đấm thép" Zone DCA có thể nổ.
        :param restricted_start: Giờ bắt đầu đóng băng lưới
        :param restricted_end: Giờ kết thúc đóng băng lưới
        """
        self.base_lot = base_lot
        self.max_lot_threshold = max_lot_threshold
        self.atr_multiplier = atr_multiplier
        self.max_spread_points = max_spread_pips * 10 
        self.point_value = point_value
        self.zone_dca_distance_points = zone_dca_distance_points
        self.restricted_start = restricted_start
        self.restricted_end = restricted_end

    def calculate_next_grid_step(self, atr_14_value: float) -> float:
        """
        Tính toán khoảng cách lưới tiếp theo (ATR-Based Dynamic Spacing).
        
        :param atr_14_value: Giá trị hiện tại của chỉ báo ATR(14)
        :return: Khoảng cách lưới để đặt lệnh (theo Point)
        """
        grid_step_points = (atr_14_value / self.point_value) * self.atr_multiplier
        # Trả về khoảng cách theo Point (ví dụ: ATR là 0.00400 -> step khoảng 200 points)
        return round(grid_step_points)

    def calculate_next_lot(self, current_level: int, total_previous_lots: float) -> float:
        """
        Lưới Bậc Thang (Step Grid Multiplier) + Zone DCA.
        
        :param current_level: Cấp độ lệnh hiện tại (tính từ 1).
        :param total_previous_lots: Tổng số Lot đã mở trước đó (cần cho Cú đấm thép).
        :return: Số Lot cho lệnh tiếp theo.
        """
        if current_level <= 1:
            next_lot = self.base_lot
        elif current_level <= 10:
            # Tầng 1-10: Multiplier 1.0 (Giữ Margin sạch, lot duy trì thấp)
            next_lot = self.base_lot
        elif current_level <= 15:
            # Tầng 11-15: Multiplier 1.5. (Tăng volume nhẹ khi dãn sâu)
            # Volume tại các lệnh này phụ thuộc vào lệnh kề trước
            # VD: level 11 = lot level 10 * 1.5
            # Ở đây đơn giản hoá là nhân base_lot với luỹ thừa, nhưng logic step sẽ là:
            previous_lot = self.base_lot * (1.5 ** (current_level - 11))
            next_lot = previous_lot * 1.5
            
            # Làm tròn 3 chữ số thập phân (đối với Cent: min lot 0.01 nhưng quy đổi sang standard là 0.001)
            next_lot = round(next_lot, 3) 
        else:
            # Tầng 16 (Cú đấm thép): Bơm vào thị trường lệnh lấp đầy = Tổng tất cả lệnh trước đó
            next_lot = total_previous_lots
            logger.info(f"Preparing STEEL PUNCH at level {current_level}! Volume: {next_lot}")

        return next_lot

    def can_open_new_trade(self, current_spread_points: float, server_time: datetime, current_level: int, distance_from_first_order_points: float, rsi_confirmed: bool) -> bool:
        """
        Kiểm tra các điều kiện an toàn để mở thêm Grid / Zone DCA.
        
        :param current_spread_points: Chênh lệch Spread hiện hành (Points)
        :param server_time: Giờ hiện tại của Server
        :param current_level: Số thứ tự lệnh đang chuẩn bị mở
        :param distance_from_first_order_points: Tổng quãng đường giá đã đi từ lệnh số 1.
        :param rsi_confirmed: Kết quả kiểm tra từ Mô-đun tín hiệu RSI
        :return: True nếu thoả mãn mọi điều kiện để mở lệnh.
        """
        # 1. Spread Filter
        if current_spread_points > self.max_spread_points:
            logger.warning(f"Spread {current_spread_points} too high! Max allowed: {self.max_spread_points}")
            return False

        # 2. Time Window Filter
        current_time_only = server_time.time()
        if self.restricted_start <= current_time_only <= self.restricted_end:
            logger.warning(f"Restricted Time Window! Current server time {current_time_only}")
            return False

        # 3. Zone DCA (Tầng >= 16) Restrictions
        if current_level >= 16:
            # Chỉ mở Lệnh Cú đấm thép nếu thỏa 2 điều kiện:
            # - Quãng đường giá đã đi > zone_dca_distance_points (vd 500 pips)
            # - RSI đã đi vào vùng quá bán/quá mua cực đại (rsi_confirmed = True)
            if distance_from_first_order_points < self.zone_dca_distance_points:
                logger.debug(f"Level {current_level} refused: Distance {distance_from_first_order_points} < {self.zone_dca_distance_points}")
                return False
            
            if not rsi_confirmed:
                logger.debug(f"Level {current_level} refused: RSI not confirmed.")
                return False

        return True

    def validate_max_lot_allowed(self, projected_next_lot: float) -> bool:
        """
        Kiểm tra an toàn tổng số Lot có vượt ngưỡng không.
        
        :param projected_next_lot: Số lượng Lot sẽ mở sắp tới.
        :return: True nếu Lot <= Ngưỡng an toàn.
        """
        if projected_next_lot > self.max_lot_threshold:
            logger.error(f"BLOCKED: Projected Lot ({projected_next_lot}) exceeds Max Lot Threshold ({self.max_lot_threshold})")
            return False
            
        return True
