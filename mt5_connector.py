import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

logger = logging.getLogger(__name__)

class MT5Connector:
    def __init__(self):
        """Khởi tạo kết nối MT5 từ biến môi trường"""
        load_dotenv() # Load variables from .env
        self.login = os.getenv("MT5_LOGIN")
        self.password = os.getenv("MT5_PASSWORD")
        self.server = os.getenv("MT5_SERVER")
        self.symbol = os.getenv("SYMBOL", "AUDNZDm")
        self.magic_number = int(os.getenv("MAGIC_NUMBER", "999999"))
        
        if not self.login or not self.password or not self.server:
            logger.error("Missing .env variables for MT5 connection!")

    def connect(self) -> bool:
        """Thực hiện kết nối đến Terminal MetaTrader 5"""
        if not mt5.initialize(login=int(self.login), server=self.server, password=self.password):
            logger.error(f"MT5 initialize() failed, error code: {mt5.last_error()}")
            return False
            
        logger.info(f"Connected to MT5 Server: {self.server} - Account: {self.login}")
        return True

    def disconnect(self):
        """Đóng kết nối MT5"""
        mt5.shutdown()
        logger.info("MT5 connection closed.")

    def get_account_leverage(self) -> float:
        """Lấy đòn bẩy hiện tại của tài khoản (VD: 2000 cho đòn bẩy 1:2000)"""
        account_info = mt5.account_info()
        if account_info is None:
            return 0.0
        return float(account_info.leverage)

    def get_account_equity(self) -> float:
        """Lấy Equity hiện tại của tài khoản"""
        account_info = mt5.account_info()
        if account_info is None:
            return 0.0
        return account_info.equity

    def get_market_data(self):
        """
        Lấy Spread, ATR, RSI và Giờ Server.
        Vì thư viện ngoài lỗi build, ta tự tính RSI 14 và ATR 14 bằng Pandas.
        :return: spread_points, atr_value, rsi_value, server_time
        """
        # Ensure symbol is selected
        mt5.symbol_select(self.symbol, True)
        symbol_info = mt5.symbol_info(self.symbol)
        
        if symbol_info is None:
            logger.error(f"Symbol {self.symbol} not found")
            return 0, 0, 50.0, datetime.now()

        spread_points = symbol_info.spread
        server_time = datetime.fromtimestamp(symbol_info.time)
        
        # Pull last 50 candles on H1 timeframe to calculate RSI(14) and ATR(14)
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 50)
        if rates is None or len(rates) < 15:
            return spread_points, 0.0, 50.0, server_time

        df = pd.DataFrame(rates)
        
        # Calculate ATR(14)
        df['h-l'] = df['high'] - df['low']
        df['h-pc'] = abs(df['high'] - df['close'].shift(1))
        df['l-pc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        # Using Simple Moving Average for ATR for simplicity
        df['atr_14'] = df['tr'].rolling(window=14).mean()
        
        # Calculate RSI(14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))

        current_atr = df['atr_14'].iloc[-1]
        current_rsi = df['rsi_14'].iloc[-1]
        
        # Thay thế NaN bằng giá trị an toàn nếu chưa đủ dữ liệu (đã chặn len<15 nên an toàn)
        current_atr = current_atr if not np.isnan(current_atr) else 0.0 
        current_rsi = current_rsi if not np.isnan(current_rsi) else 50.0

        return spread_points, current_atr, current_rsi, server_time

    # ... Sẽ thêm hàm get_open_positions() và send_order() ở các phiên bản sau

