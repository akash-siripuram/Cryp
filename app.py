import time
from binance.client import Client
import numpy as np
import streamlit as st
import pandas as pd

api_key = "7g07Ki6i8Wdhu08uPZVXAV59weAdxi6RKaq7QLd0fmj5HTcgyu8Vp8g8MjIDLRIC"
api_secret = "Mx1c0DkfKtSw3Uuj0QtnxnnFE8dZIQE99245jq6ZbDyJQOkkWmKlyWFReLzc5d0x"

client = Client(api_key, api_secret, testnet=True)

# Define trading parameters
symbol = 'BTCUSDT'
buy_sell_interval = 5

# Initialize lists for EMA calculations
short_ema_values = []
long_ema_values = []

# Initialize lists for trade history
trade_history = []

# Create an initial empty container for the trade table
trade_container = st.empty()

# Function to perform trading and update trade history
def perform_trading():
    initial_balance = 100.0
    trading_balance = initial_balance  # Initialize trading_balance here
    while True:
        try:
            # Fetch ticker data
            ticker = client.get_symbol_ticker(symbol=symbol)
            close_price = float(ticker['price'])

            short_ema_values.append(close_price)
            long_ema_values.append(close_price)

            # Calculate the short and long EMAs
            if len(short_ema_values) > 50:
                short_ema_values.pop(0)
            if len(long_ema_values) > 200:
                long_ema_values.pop(0)

            short_ema = np.mean(short_ema_values)
            long_ema = np.mean(long_ema_values)

            action = "No Action"
            trade_amount = 0

            if short_ema > long_ema:
                # Execute buy order (Golden Cross)
                action = "Buy"
                trade_amount = trading_balance
                trading_balance -= trade_amount

                # Place a testnet buy order
                order = client.create_test_order(
                    symbol=symbol,
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=trade_amount
                )

            elif short_ema < long_ema:
                # Execute sell order (Death Cross)
                action = "Sell"
                trading_balance += close_price * trade_amount

                # Place a testnet sell order
                order = client.create_test_order(
                    symbol=symbol,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=trade_amount
                )

            # Calculate profit and loss (P&L)
            if trade_history:
                last_trade = trade_history[-1]
                if action == "Buy":
                    pnl = (close_price - last_trade["Price"]) * last_trade["Trade Amount"]
                elif action == "Sell":
                    pnl = (close_price - last_trade["Price"]) * last_trade["Trade Amount"]
                else:
                    pnl = 0.0
            else:
                pnl = 0.0

            # Record the trade in the trade history with P&L
            trade_history.append({
                "Timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                "Action": action,
                "Price": close_price,
                "Trade Amount": trade_amount,
                "Trading Balance": trading_balance,
                "P&L": pnl
            })

           
            # Display the latest 10 trades in a table and update the content
            
            
            latest_trades = trade_history[-5:]
            
            trade_df = pd.DataFrame(latest_trades)
            
            # Update the content of the trade container with the latest trades
            trade_container.title("Latest Trade\n")
            trade_container.table(trade_df)

            # Wait for a few seconds before checking again
            time.sleep(buy_sell_interval)

        except Exception as e:
            st.write(f"An error occurred: {str(e)}")
            # Wait before checking again after an error
            time.sleep(5)

# Call the perform_trading function to start trading
perform_trading()
