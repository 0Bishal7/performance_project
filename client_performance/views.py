import matplotlib.pyplot as plt
import io
import base64
from django.shortcuts import render
from .utils import fetch_data_from_sheets
import numpy as np
from matplotlib.dates import DateFormatter, AutoDateLocator
import pandas as pd


def calculate_metrics(df, client_name, starting_balance):
    daily_profit_loss = df[['Date', client_name]].dropna()

    daily_profit_loss['CumulativeProfit'] = daily_profit_loss[client_name].cumsum()
    daily_profit_loss['Balance'] = starting_balance + daily_profit_loss['CumulativeProfit']
    daily_profit_loss['Drawdown'] = daily_profit_loss['Balance'] - daily_profit_loss['Balance'].cummax()

    daily_profit_loss['DailyReturn'] = daily_profit_loss['Balance'].pct_change().fillna(0)

    win_trades = daily_profit_loss[daily_profit_loss[client_name] >= 0]
    loss_trades = daily_profit_loss[daily_profit_loss[client_name] < 0]
    win_rate = round(len(win_trades) / len(daily_profit_loss), 2)
    loss_rate = round(1 - win_rate, 2)

    average_gain = win_trades[client_name].mean()
    average_loss = -loss_trades[client_name].mean() if len(loss_trades) > 0 else 0
    reward_risk_ratio = average_gain / average_loss if average_loss != 0 else 0
    expectancy = round((win_rate * reward_risk_ratio) - loss_rate, 2)

    max_drawdown = daily_profit_loss['Drawdown'].min()

    max_drawdown_percentage = round((max_drawdown / starting_balance) * 100, 2)

    calmar_ratio = None
    if max_drawdown != 0:
        calmar_ratio = round(abs(expectancy) / abs(max_drawdown_percentage), 2)

    avg_daily_return = daily_profit_loss['DailyReturn'].mean()
    std_daily_return = daily_profit_loss['DailyReturn'].std()

    sharpe_ratio = round(((avg_daily_return * 252 - 0.08) / (std_daily_return * np.sqrt(252))), 2) if std_daily_return != 0 else 0

    return daily_profit_loss, win_rate, loss_rate, expectancy, max_drawdown, max_drawdown_percentage, calmar_ratio, sharpe_ratio


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

    starting_balance = float(request.GET.get('starting_balance', 1000000))

    daily_profit_loss, win_rate, loss_rate, expectancy, max_drawdown, max_drawdown_percentage, calmar_ratio, sharpe_ratio = calculate_metrics(df, client_name, starting_balance)

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
        'max_drawdown_percentage': max_drawdown_percentage,
        'calmar_ratio': calmar_ratio,
        'sharpe_ratio': sharpe_ratio,
        'starting_balance': starting_balance
    }

    return render(request, 'client_performance/performance.html', context)
