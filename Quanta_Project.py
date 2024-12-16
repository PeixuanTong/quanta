from flask import Flask, render_template, request, send_file
import pandas as pd
import yfinance as yf

app = Flask(__name__)

from datetime import datetime, timedelta

app = Flask(__name__)

# Function to fetch stock data
def fetch_stock_data(ticker, start_date, end_date, holding_period):
    # Convert input strings to datetime objects
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Adjust dates: 20 days before start_date and holding_period days after end_date
    adjusted_start_date = (start_date_dt - timedelta(days=20)).strftime("%Y-%m-%d")
    adjusted_end_date = (end_date_dt + timedelta(days=holding_period)).strftime("%Y-%m-%d")

    # Download data using adjusted dates
    data = yf.download(ticker, start=adjusted_start_date, end=adjusted_end_date)

    return data

# Function to calculate breakout days

def calculate_breakout_days(data, volume_threshold, price_change_threshold):
    if len(data) < 20:
        raise ValueError("Data must have at least 20 rows to calculate rolling averages.")


    # Calculate the rolling average volume and percentage change
    data['20d_avg_volume'] = data['Volume'].rolling(window=20).mean()
    data['Pct_Change'] = data['Close'].pct_change() * 100

    # Keep rows where '20d_avg_volume' is not NaN
    filtered_data = data.iloc[20:-20,:]
    # Calculate breakout conditions
    filtered_data['Breakout'] = filtered_data['Volume'].squeeze() > (
    volume_threshold * filtered_data['20d_avg_volume'].squeeze()
)

    breakout_days = filtered_data[(filtered_data['Breakout']) & 
                                  (filtered_data['Pct_Change'] > price_change_threshold)]

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

    # Check if results are empty
    if results.empty:
        message = "No breakout day in the period."
        return render_template('index.html', message=message)

    # Save results to a CSV file
    filename = "breakout_report.csv"
    results.to_csv(filename, index=False)

    # Send the file back to the user
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)


