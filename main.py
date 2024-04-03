
# First we need to read the CSV we got from Interactive Brokers
# We got this CSV from "Activity Report", and by using custom dates!
from datetime import datetime
import csv
import yfinance as yf

RED = '\033[31m'  # Red text
GREEN = '\033[32m'  # Green text
RESET = '\033[0m'  # Reset to default text color

EXCEPTION_LIST = [
    "SPY"
]

# Print text in different colors
def print_green(text):
    print(f"{GREEN}{text}{RESET}")

def print_red(text):
    print(f"{RED}{text}{RESET}")

SPY = yf.Ticker("SPY")

class Trade():
    DATE_FORMAT = '%Y-%m-%d, %H:%M:%S'

    def __init__(self, row):
        self.date = datetime.strptime(row[6], self.DATE_FORMAT)
        self.ticker = row[5]
        self.price = int(float(row[8]))
        self.quantitiy = abs(int(row[7]))
        self.buy = not(row[7].startswith("-"))

    def __str__(self):
        return f"""
        Date: {self.date}
        Ticker: {self.ticker}
        Price: {self.price}
        Quantity: {self.quantitiy}
        Buy: {self.buy}"""
    
    def __repr__(self):
        return f"""
        Date: {self.date}
        Ticker: {self.ticker}
        Price: {self.price}
        Quantity: {self.quantitiy}
        Buy: {self.buy}"""
    

def get_spy_dates(start_date, closed, close_date=None, percentage=False):
    snopy_start_date = SPY.history(start=start_date, end=start_date).iloc[0]
    snopy_start_price = (snopy_start_date['High'] + snopy_start_date['Low']) / 2

    if closed:
        snopy_close_date = SPY.history(start=close_date, end=close_date).iloc[0]
        snopy_close_price = (snopy_close_date['High'] + snopy_close_date['Low']) / 2
    else: # Getting the last price
        snopy_close_date = SPY.history(period="1d").iloc[-1]
        snopy_close_price = (snopy_close_date['High'] + snopy_close_date['Low']) / 2

    if not percentage:
        return snopy_close_price - snopy_start_price

    snopy_percentage = ((snopy_close_price - snopy_start_price) / snopy_start_price)

    return snopy_percentage

TICKER_LAST_PRICE = {}

def get_last_stock_price(ticker):
    global TICKER_LAST_PRICE
    if ticker in TICKER_LAST_PRICE:
        return TICKER_LAST_PRICE[ticker]

    ticker_obj = yf.Ticker(ticker)
    last_stock_date = ticker_obj.history(period="1d").iloc[-1]
    last_stock_price = (last_stock_date['High'] + last_stock_date['Low']) / 2
    TICKER_LAST_PRICE[ticker] = last_stock_price

    return TICKER_LAST_PRICE[ticker]

# def get_spy_value(date=None):
#     if date is None:
#         snopy_close_date = SPY.history(period="1d").iloc[-1]
#         snopy_close_price = (snopy_close_date['High'] + snopy_close_date['Low']) / 2
#         return snopy_close_price
    
#     snopy_start_date = SPY.history(start=start_date, end=start_date).iloc[0]
#     snopy_start_price = (snopy_start_date['High'] + snopy_start_date['Low']) / 2

csv_summary = [
    ["Ticker", 
     "Ticker Bought Date", 
     "Ticker Current Date", 
     "Ticker Bought Price", 
     "Ticker Current Price", 
     "Ticker Sold", 
     "PnL", 
     "PnL SPY"]
]

def analyze_stocks(file_path):
    csv_file = []
    tickers = {}

    with open(file_path, 'r') as file:
        report = csv.reader(file, delimiter=",")
        for row in report:
            csv_file.append(row)

    # Going over the trades
    for row in csv_file:
        if row[0] == "Trades" and row[1] == "Data" and row[3] == "Stocks":
            trade = Trade(row)

            if trade.ticker in EXCEPTION_LIST:
                continue

            if trade.ticker not in tickers:
                tickers[trade.ticker] = {
                    "buy": [],
                    "sell": []
                }

            # print(trade)

            if trade.buy:
                tickers[trade.ticker]["buy"].append(trade)

            if not(trade.buy):
                tickers[trade.ticker]["sell"].append(trade)
    
    
    pnl = 0
    pnl_spy = 0

    # Analyzing stock by stock, after processing the Excel
    for ticker_name, trades in tickers.items():

        
        
        pnl_ticker = 0
        pnl_spy_ticker = 0

        bought_positions = []
        sold_positions = []
        
        for sell_trade in trades["sell"]:
            sold_positions.extend([sell_trade] * sell_trade.quantitiy)

        for buying_trade in trades["buy"]:
            # Not, going buy after buy and understand how much we lost or not
            bought_positions.extend([buying_trade] * buying_trade.quantitiy)
            
        # print("Ticker: ", ticker_name)
        # print("Bought: ", len(bought_positions))
        
        # For every stock, I'm checking how much I did in terms of money, and what 
        # we could have in SPY
        for trade_number, buying_trade in enumerate(bought_positions):
            
            try:
                selling_price = sold_positions[trade_number].price
                close_date = sold_positions[trade_number].date
                closed = True
            except IndexError: # Not closed position
                selling_price = get_last_stock_price(ticker_name)
                close_date = datetime.now()
                closed = False

            # print("Bought stock at price: ", buying_trade.price)
            # print("Sold stock at price: ", selling_price)

            # Note that this is per stock, so I should take the money I've used and see...
            earning_stock = selling_price - buying_trade.price
            percentage_spy = get_spy_dates(start_date=buying_trade.date, 
                                        closed=closed, 
                                        close_date=close_date,
                                        percentage=True)
            earning_spy = buying_trade.price * percentage_spy
            pnl_ticker += earning_stock
            pnl_spy_ticker += earning_spy

###
 #           csv = [
#    ["Ticker", 
#     "Ticker Bought Date", 
#     "Ticker Current Date", 
#     "Ticker Bought Price", 
#     "Ticker Current Price", 
#   "Ticker Sold", 
#     "PnL", 
#    "PnL SPY"]
# ]
            ###
            csv_summary.append([ticker_name, buying_trade.date, close_date, buying_trade.price, selling_price, closed, earning_stock, earning_spy])

        print(f"Stock: {ticker_name}")
        print(f"PnL: {pnl_ticker}")
        print(f"PnL SPY: {pnl_spy_ticker}")
        difference = pnl_ticker - pnl_spy_ticker
        if difference > 0:
            print_green(f"Difference: {difference}")
        else:
            print_red(f"Difference: {difference}")

        pnl += pnl_ticker
        pnl_spy += pnl_spy_ticker

    print("------Finel Results!------")
    print(f"PnL: {pnl}")
    print(f"PnL SPY: {pnl_spy}")
    difference = pnl - pnl_spy
    if difference > 0:
        print_green(f"Difference: {difference}")
    else:
        print_red(f"Difference: {difference}")

    with open("summary.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerows(csv_summary)

            # # At stock level, how much I earned?
            # stock_percentage = ((close_price - start_price) / start_price) * 100
            # spy_percentage = get_spy_dates(start_date, close_date)

        

        # if "buy" in trades and "sell" in trades:

        #     # Let's analyze for each quantity bought how much we got for it.
        #     start_date = trades["buy"].date
        #     close_date = trades["sell"].date 
        #     start_price = trades["buy"].price
        #     close_price = trades["sell"].price           

        #     # How much the stock did
        #     stock_percentage = ((close_price - start_price) / start_price) * 100
        #     spy_percentage = get_spy_dates(start_date, close_date)

        #     if stock_percentage > spy_percentage:
        #         print_green(f"Stock: {ticker_name}")
        #     else:
        #         print_red(f"Stock: {ticker_name}")
        #     print(f"Stock Percentage: {stock_percentage}")
        #     print(f"SPY Percentage: {spy_percentage}")
        #     print(f"Bought Price: {start_price}")
        #     print(f"Selled Price: {close_price}")
        #     print(f"Start Date: {start_date}")
        #     print(f"Close Date: {close_date}")
        #     continue

        # start_date = trades["buy"].date
        # start_price = trades["buy"].price

        # ticker_data = yf.Ticker(ticker_name)
        # ticket_last_data = ticker_data.history(period="1d").iloc[-1]
        # close_price = (ticket_last_data['High'] + ticket_last_data['Low']) / 2
        

        # stock_percentage = ((close_price - start_price) / start_price) * 100
        # spy_percentage = get_spy_dates(start_date)

        # if stock_percentage > spy_percentage:
        #     print_green(f"Stock: {ticker_name}")
        # else:
        #     print_red(f"Stock: {ticker_name}")
        # print(f"Stock Percentage: {stock_percentage}")
        # print(f"SPY Percentage: {spy_percentage}")
        # print(f"Bought Price: {start_price}")
        # print(f"Selled Price: {close_price}")
        # print(f"Start Date: {start_date}")
        # print(f"Close Date: Today!")
    

if __name__ == "__main__":
    analyze_stocks("/Users/omriperi/Library/Containers/com.microsoft.Excel/Data/Downloads/U7828414_20230501_20240322.csv")