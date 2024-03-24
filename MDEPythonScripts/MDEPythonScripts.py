import sys
import subprocess
#subprocess.check_call([sys.executable, '-m', 'pip', 'freeze'])
#subprocess.check_call([sys.executable, 'virtualenv' 'env'])

#subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Metatrader5'])

from typing import List
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import time
import MetaTrader5 as mt5
import pandas as pd 

#Code generation bit

#Connect ( all the variables go here, except for the strategy and fund variables. connect to mt5 and broker account) ------------------------------------------------------------------------------------------
#connect to broker SwissBank with login "personA", password "passwordA", timeframe "1HR"

if not mt5.initialize(login=5023919288, server="MetaQuotes-Demo",password="N+UcJj4q"):
    print("initialize() failed, error code =",mt5.last_error())
    quit()


timeframe_dict ={
    "M1":(mt5.TIMEFRAME_M1, timedelta(days=2)),
    "M2":(mt5.TIMEFRAME_M2, timedelta(days=4)),
    "M3":(mt5.TIMEFRAME_M3, timedelta(days=6)),
    "M4":(mt5.TIMEFRAME_M4, timedelta(days=8)),
    "M5":(mt5.TIMEFRAME_M5, timedelta(days=10)),
    "M6":(mt5.TIMEFRAME_M6, timedelta(days=12)),
    "M10":(mt5.TIMEFRAME_M10, timedelta(days=20)),
    "M12":(mt5.TIMEFRAME_M12, timedelta(days=24)),
    "M20":(mt5.TIMEFRAME_M20, timedelta(days=40)),
    "M30":(mt5.TIMEFRAME_M30, timedelta(days=60)),
    "H1":(mt5.TIMEFRAME_H1, timedelta(days=120)),
    "H2":(mt5.TIMEFRAME_H2, timedelta(days=240)),
    "H3":(mt5.TIMEFRAME_H3, timedelta(days=360)),
    "H4":(mt5.TIMEFRAME_H4, timedelta(days=480)),
    "H6":(mt5.TIMEFRAME_H6, timedelta(days=720)),
    "H8":(mt5.TIMEFRAME_H8, timedelta(days=960)),
    "H12":(mt5.TIMEFRAME_H12, timedelta(days=1440)),
    "D1":(mt5.TIMEFRAME_D1, timedelta(days=2880)),
    "W1":(mt5.TIMEFRAME_W1, timedelta(days=20160)),
    "MN1":(mt5.TIMEFRAME_MN1, timedelta(days=86400)),
    }
timeframe = timeframe_dict["M1"]

initial_market_df = pd.DataFrame(mt5.copy_rates_range('EURUSD', mt5.TIMEFRAME_M1, datetime.now() - timedelta(days=3), datetime.now()))
initial_market_df['time'] = pd.to_datetime(initial_market_df['time'], unit = 's')
print(initial_market_df)
trading_bot_array = []

#--------------------------------------------------------------------------------------------------


#Create Bot (include strategies and trader objects. Remember to only create one and just append to a dynamic array) ----------------------------------------------------------------------------------------
#create bot with buyAndHold strategy using 60.15 from money


class TradingStrategy(ABC):
    @abstractmethod
    def __init__(self, market_data) -> None:
        pass

    @abstractmethod
    def long_condition() -> bool:
        pass

    @abstractmethod
    def short_condition() -> bool:
        pass

    @abstractmethod
    def closelong_condition() -> bool:
        pass

    @abstractmethod
    def closeshort_condition() -> bool:
        pass

    @abstractmethod
    def get_execution_instructions() -> List[str]:
        pass

    @abstractmethod
    def getName(self) -> str:
        pass


class BuyAndHold(TradingStrategy):
    def __init__(self, symbol, market_df) -> None:
        self.symbol = symbol
        self.current_close = list(market_df[-1:]['close'])[0]
        self.last_close = list(market_df[-2:]['close'])[0]
        self.last_high = list(market_df[-2:]['high'])[0]
        self.last_low = list(market_df[-2:]['low'])[0]

        
        self.sl = 0.05
        self.tp = 0.1
        self.buy_sl = mt5.symbol_info_tick(self.symbol).ask * (1-self.sl)
        self.buy_tp = mt5.symbol_info_tick(self.symbol).ask * (1+self.tp)
        self.sell_sl = mt5.symbol_info_tick(self.symbol).bid * (1+self.sl)
        self.sell_tp = mt5.symbol_info_tick(self.symbol).bid * (1-self.tp)

    def long_condition(self) -> bool:
        return self.current_close < self.last_close

    def short_condition(self) -> bool:
        return self.current_close < self.last_low

    def closelong_condition(self) -> bool:
        return self.current_close < self.last_close

    def closeshort_condition(self) -> bool:
        return self.current_close > self.last_close

    def set_market_df(self, market_df):
        self.current_close = list(market_df[-1:]['close'])[0]
        self.last_close = list(market_df[-2:]['close'])[0]
        self.last_high = list(market_df[-2:]['high'])[0]
        self.last_low = list(market_df[-2:]['low'])[0]

    def get_execution_instructions(self) -> List[str]:
        instructions = []

        already_buy = False
        already_sell = False

        try:
            already_sell = mt5.positions_get()[0]._asdict()['type']==1
            already_buy = mt5.positions_get()[0]._asdict()['type']==0
        except:
            pass

        if self.long_condition():
            if len(mt5.positions_get()) == 0:
                instructions.append(("create", self.symbol, 0, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask, self.buy_sl, self.buy_tp))
                #self.create_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask, self.buy_sl, self.buy_tp)
                print("buy placed")
            if already_sell:
                instructions.append(("close", self.symbol, 0, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask))
                #self.close_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask)
                print('Sell position closed')
                time.sleep(1)
                instructions.append(("create", self.symbol, 0, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask, self.buy_sl, self.buy_tp))
                #self.create_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask, self.buy_sl, self.buy_tp)

        if self.short_condition():
            if len(mt5.positions_get()) == 0:
                instructions.append(("create", self.symbol, 0, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid, self.sell_sl, self.sell_tp))
                #self.create_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid, self.sell_sl, self.sell_tp)
                print("sell placed")
            if already_buy:
                instructions.append(("close", self.symbol, 0, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid))
                #self.close_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid)
                print('Buy position closed')
                time.sleep(1)
                instructions.append(("create", self.symbol, 0, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid, self.sell_sl, self.sell_tp))
                #self.create_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid, self.sell_sl, self.sell_tp)


        try:
            already_sell = mt5.positions_get()[0]._asdict()['type']==1
            already_buy = mt5.positions_get()[0]._asdict()['type']==0
        except:
            pass

        if self.closelong_condition and already_buy:
            instructions.append(("close", self.symbol, 0, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick(self.symbol).bid))
            #self.close_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_SELL, mt5.symbol_info_tick("EURUSD").bid)
            print('buy position closed')

        if self.closeshort_condition and already_sell:
            instructions.append(("close", self.symbol, 0, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick(self.symbol).ask))
            #self.close_order(self.symbol, self.lot_size, mt5.ORDER_TYPE_BUY, mt5.symbol_info_tick("EURUSD").ask)
            print('sell position closed')

        already_buy = False
        already_sell = False



        return instructions

    def getName(self) -> str:
        return self.__class__.__name__


class MeanReversion(TradingStrategy):
    def __init__(self, market_data) -> None:
        pass

    def should_buy(self, price) -> str:
        pass

    def should_sell(self, price) -> str:
        pass

    def should_wait(self, price) -> str:
        pass









class TradingBot():
    def __init__(self, strategy: TradingStrategy, lot_size: float, symbol_to_trade: str) -> None:
        self.strategy: TradingStrategy = strategy
        self.lot_size: float = lot_size
        self.symbol = symbol_to_trade
        

    def create_order(self, symbol, lot, type, price, sl, tp):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": self.lot_size,
            "type": type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "comment": "Open position by Python Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            }
        order = mt5.order_send(request)
        return order

    def close_order(self, symbol, lot, type, price):
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": self.lot_size,
            "type": type,
            "position": mt5.positions_get()[0]._asdict()['ticket'],
            "price": price,
            "comment": "Close position by Python Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            }
        order = mt5.order_send(request)
        return order

    def run(self):
        instructions = self.strategy.get_execution_instructions()

        for instruction in instructions:
            if instruction[0] == "create":
                self.create_order(instruction[1], self.lot_size + instruction[2], instruction[3], instruction[4], instruction[5], instruction[6])
            
            if instruction[0] == "close":
                self.close_order(instruction[1], self.lot_size + instruction[2], instruction[3], instruction[4])

    





strategy = BuyAndHold("EURUSD", initial_market_df)
lot_size = 0.01

trading_bot_array.append(TradingBot(strategy, lot_size, 'EURUSD'))



#---------------------------------------------------------------------------------------------------


#See Bots (print all trader objects created)------------------------------------------------------------------------------------------
#see registered bots

for bot in trading_bot_array:
    print(f'Bot with id {id(bot)} using the {bot.strategy.getName()} strategy and {bot.lot_size} lots.')
#---------------------------------------------------------------------------------------------------


#Execute (runs a while loop to allow objects to run) -----------------------------------------------------------------------------------------
#execute bots for a days b hours c minutes d seconds
a = 0
b = 0
c = 3
d = 0
timeout = time.time() + a*86400 + b*3600 + c*60 + d*1

i = 0
while True:
    i = i+1
    print(i)
    prices = pd.DataFrame(mt5.copy_rates_range('EURUSD', mt5.TIMEFRAME_M1, datetime(2024, 3, 22), datetime.now()))
    prices['time'] = pd.to_datetime(prices['time'], unit = 's')

    for bot in trading_bot_array:
        bot.strategy.set_market_df(prices)
        bot.run()

    time.sleep(60)
    if time.time() > timeout:
        break


#--------------------------------------------------------------------------------------------------


#Stop Bots (disrupts the while loop and terminates the program)------------------------------------------------------------------------------------------
#stop bots

#----------------------------------------------------------------------------------------------------



