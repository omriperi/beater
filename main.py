
# First we need to read the CSV we got from Interactive Brokers
# We got this CSV from "Activity Report", and by using custom dates!
from datetime import datetime
import csv
import yfinance as yf

RED = '\033[31m'  # Red text
GREEN = '\033[32m'  # Green text
RESET = '\033[0m'  # Reset to default text color

EXCEPTION_LIST = [
    "NVDA",
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
        self.quantitiy = row[7]
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
    

def get_spy_percentage_dates(start_date, close_date=None):
    snopy_start_date = SPY.history(start=start_date, end=start_date).iloc[0]
    snopy_start_price = (snopy_start_date['High'] + snopy_start_date['Low']) / 2

    if close_date is not None:
        snopy_close_date = SPY.history(start=close_date, end=close_date).iloc[0]
        snopy_close_price = (snopy_close_date['High'] + snopy_close_date['Low']) / 2
    else: # Getting the last price
        snopy_close_date = SPY.history(period="1d").iloc[-1]
        snopy_close_price = (snopy_close_date['High'] + snopy_close_date['Low']) / 2

    snopy_percentage = ((snopy_close_price - snopy_start_price) / snopy_start_price) * 100

    return snopy_percentage



def analyze_stocks(file_path):
    csv_file = []
    tickers = {}

    with open(file_path, 'r') as file:
        report = csv.reader(file, delimiter=",")
        for row in report:
            csv_file.append(row)

    for row in csv_file:
        if row[0] == "Trades" and row[1] == "Data" and row[3] == "Stocks":
            trade = Trade(row)

            if trade.ticker in EXCEPTION_LIST:
                continue

            if trade.ticker not in tickers:
                tickers[trade.ticker] = {}

            if trade.buy and "buy" not in tickers[trade.ticker]:
                tickers[trade.ticker]["buy"] = trade

            if not(trade.buy) and "sell" not in tickers[trade.ticker]:
                tickers[trade.ticker]["sell"] = trade
    
    # Analyzing stock by stock
    for ticker_name, trades in tickers.items():
        
        if "buy" in trades and "sell" in trades:
            start_date = trades["buy"].date
            close_date = trades["sell"].date 
            start_price = trades["buy"].price
            close_price = trades["sell"].price           

            # How much the stock did
            stock_percentage = ((close_price - start_price) / start_price) * 100
            spy_percentage = get_spy_percentage_dates(start_date, close_date)

            if stock_percentage > spy_percentage:
                print_green(f"Stock: {ticker_name}")
            else:
                print_red(f"Stock: {ticker_name}")
            print(f"Stock Percentage: {stock_percentage}")
            print(f"SPY Percentage: {spy_percentage}")
            print(f"Bought Price: {start_price}")
            print(f"Selled Price: {close_price}")
            print(f"Start Date: {start_date}")
            print(f"Close Date: {close_date}")
            continue

        start_date = trades["buy"].date
        start_price = trades["buy"].price

        ticker_data = yf.Ticker(ticker_name)
        ticket_last_data = ticker_data.history(period="1d").iloc[-1]
        close_price = (ticket_last_data['High'] + ticket_last_data['Low']) / 2
        

        stock_percentage = ((close_price - start_price) / start_price) * 100
        spy_percentage = get_spy_percentage_dates(start_date)

        if stock_percentage > spy_percentage:
            print_green(f"Stock: {ticker_name}")
        else:
            print_red(f"Stock: {ticker_name}")
        print(f"Stock Percentage: {stock_percentage}")
        print(f"SPY Percentage: {spy_percentage}")
        print(f"Bought Price: {start_price}")
        print(f"Selled Price: {close_price}")
        print(f"Start Date: {start_date}")
        print(f"Close Date: Today!")
    
