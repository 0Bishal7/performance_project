import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from .utils import fetch_data_from_sheets
import numpy as np
from matplotlib.dates import DateFormatter, AutoDateLocator
import pandas as pd

# Function to calculate the metrics
def calculate_metrics(df, client_name):
    daily_profit_loss = df[['Date', client_name]].dropna()
    
    starting_balance = 1000000
    daily_profit_loss['CumulativeProfit'] = daily_profit_loss[client_name].cumsum()
    daily_profit_loss['Balance'] = starting_balance + daily_profit_loss['CumulativeProfit']
    daily_profit_loss['Drawdown'] = daily_profit_loss['Balance'] - daily_profit_loss['Balance'].cummax()

    win_trades = daily_profit_loss[daily_profit_loss[client_name] >= 0]
    loss_trades = daily_profit_loss[daily_profit_loss[client_name] < 0]
    win_rate = len(win_trades) / len(daily_profit_loss)
    loss_rate = 1 - win_rate

    average_gain = win_trades[client_name].mean()
    average_loss = -loss_trades[client_name].mean() if len(loss_trades) > 0 else 0
    reward_risk_ratio = average_gain / average_loss if average_loss != 0 else 0
    expectancy = (win_rate * reward_risk_ratio) - loss_rate

    max_drawdown = daily_profit_loss['Drawdown'].min()

    win_rate = round(win_rate, 3)
    loss_rate = round(loss_rate, 3)
    expectancy = round(expectancy, 3)
    max_drawdown = round(max_drawdown, 3)

    # Calculate max drawdown percentage
    max_drawdown_percentage = (max_drawdown / starting_balance) * 100
    max_drawdown_percentage=round(max_drawdown_percentage,3)

    return daily_profit_loss, win_rate, loss_rate, expectancy, max_drawdown, max_drawdown_percentage

def plot_graph(data, graph_type):
    data['Date'] = pd.to_datetime(data['Date'], format='%d.%m.%Y')
    data = data.sort_values(by='Date')

    plt.figure(figsize=(10, 6))

    if graph_type == 'drawdown':
        plt.plot(data['Date'], data['Drawdown'], label='Drawdown', color='red')
        plt.title('Drawdown Graph')
    elif graph_type == 'equity':
        plt.plot(data['Date'], data['Balance'], label='Equity Curve')
        plt.title('Equity Curve')

    plt.xlabel('Date')
    plt.ylabel('Value')

    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(AutoDateLocator())
    plt.xticks(rotation=35)
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True, prune='both'))

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def performance_view(request):
    df = fetch_data_from_sheets()

    clients = df.columns[1:].tolist()  
    client_name = request.GET.get('client', clients[0])  

    daily_profit_loss, win_rate, loss_rate, expectancy, max_drawdown, max_drawdown_percentage = calculate_metrics(df, client_name)

    drawdown_img = plot_graph(daily_profit_loss, 'drawdown')
    equity_img = plot_graph(daily_profit_loss, 'equity')

    context = {
        'clients': clients,
        'client_name': client_name,
        'drawdown_img': drawdown_img,
        'equity_img': equity_img,
        'win_rate': win_rate,
        'loss_rate': loss_rate,
        'expectancy': expectancy,
        'max_drawdown': max_drawdown,
        'max_drawdown_percentage': max_drawdown_percentage  
    }

    return render(request, 'client_performance/performance.html', context)
