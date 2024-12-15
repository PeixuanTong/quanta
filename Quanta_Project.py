'''# Fetch data from yahoo finance

import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

#Get all break out date

def calculate_breakout_days(data, volume_threshold, price_change_threshold):
    data['20d_avg_volume'] = data['Volume'].rolling(window=20).mean()
    data['Pct_Change'] = data['Close'].pct_change() * 100

    breakout_days = data[(data['Volume'] > volume_threshold * data['20d_avg_volume']) & 
                         (data['Pct_Change'] > price_change_threshold)]
    return breakout_days

# simulate stratagy profit

def simulate_returns(data, breakout_days, holding_period):
    results = []
    for index, row in breakout_days.iterrows():
        buy_date = index
        sell_date = data.index[data.index.get_loc(buy_date) + holding_period]
        buy_price = row['Close']
        sell_price = data.loc[sell_date, 'Close'] if sell_date in data.index else None
        if sell_price:
            results.append({
                'Buy_Date': buy_date,
                'Buy_Price': buy_price,
                'Sell_Date': sell_date,
                'Sell_Price': sell_price,
                'Return (%)': (sell_price - buy_price) / buy_price * 100
            })
    return pd.DataFrame(results)

#Save to file

def save_results_to_csv(results, filename='breakout_report.csv'):
    results.to_csv(filename, index=False)
    return filename'''

from flask import Flask, render_template, request, send_file
import pandas as pd
import yfinance as yf

app = Flask(__name__)

# Function to fetch stock data
def fetch_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Function to calculate breakout days
def calculate_breakout_days(data, volume_threshold, price_change_threshold):
    data['20d_avg_volume'] = data['Volume'].rolling(window=20).mean()
    data['Pct_Change'] = data['Close'].pct_change() * 100

    breakout_days = data[(data['Volume'] > volume_threshold * data['20d_avg_volume']) & 
                         (data['Pct_Change'] > price_change_threshold)]
    return breakout_days

# Function to simulate returns
def simulate_returns(data, breakout_days, holding_period):
    results = []
    for index, row in breakout_days.iterrows():
        buy_date = index
        try:
            sell_date = data.index[data.index.get_loc(buy_date) + holding_period]
            buy_price = row['Close']
            sell_price = data.loc[sell_date, 'Close']
            results.append({
                'Buy_Date': buy_date,
                'Sell_Date': sell_date,
                'Return (%)': (sell_price - buy_price) / buy_price * 100
            })
        except IndexError:
            continue
    return pd.DataFrame(results)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_report', methods=['POST'])
def generate_report():
    # Get user inputs from the form
    ticker = request.form['ticker']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    volume_threshold = float(request.form['volume_threshold'])
    price_change_threshold = float(request.form['price_change_threshold'])
    holding_period = int(request.form['holding_period'])

    # Fetch and process stock data
    data = fetch_stock_data(ticker, start_date, end_date)
    breakout_days = calculate_breakout_days(data, volume_threshold / 100, price_change_threshold)
    results = simulate_returns(data, breakout_days, holding_period)

    # Save results to a CSV file
    filename = "breakout_report.csv"
    results.to_csv(filename, index=False)

    # Send the file back to the user
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

