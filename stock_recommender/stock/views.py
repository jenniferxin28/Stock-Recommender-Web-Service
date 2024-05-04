from django.shortcuts import render
import pandas as pd
from django.conf import settings
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress
import numpy as np
from .models import SP500Stocks, DOWStocks, NASDAQStocks, StockData
from django.http import HttpResponse
import csv

# Create your views here.

# function for get market summary for sp500, nasdaq, dow, etc
def get_market_summary(ticker):
    market_data = yf.Ticker(ticker)
    hist_data = market_data.history(period="5d")

    if len(hist_data) < 2:
        # no data error
        return None

    latest_close = hist_data['Close'].iloc[-1]
    previous_close = hist_data['Close'].iloc[-2]

    point_change = latest_close - previous_close
    change_percentage = (point_change / previous_close) * 100
    stock_change_color = 'green' if point_change >= 0 else 'red'

    # convert to string with 2 decimal places
    stock_value = f"{latest_close:,.2f}"
    stock_change_percentage = f"{change_percentage:.2f}%"
    stock_point_change = f"{point_change:+.2f}"

    return {
        'stock_value': stock_value,
        'stock_change_percentage': stock_change_percentage,
        'stock_point_change': stock_point_change,
        'stock_change_color': stock_change_color,
    }
# index page
def index(request):
    sp500fig_converted = setup_index_chart("^GSPC", 'S&P 500 Performance Over the Past Year')
    dowfig_converted = setup_index_chart("^DJI", 'DOW Performance Over the Past Year')
    nasdaqfig_converted = setup_index_chart("^IXIC", 'NASDAQ Performance Over the Past Year')

    context = {
        'sp500fig_converted': sp500fig_converted,
        'dowfig_converted': dowfig_converted,
        'nasdaqfig_converted': nasdaqfig_converted,
        'top_sp500_stocks': SP500Stocks.objects.all().order_by('-score')[:10],
        'top_dow_stocks': DOWStocks.objects.all().order_by('-score')[:10],
        'top_nasdaq_stocks': NASDAQStocks.objects.all().order_by('-score')[:10],
        'sp500': get_market_summary("^GSPC"),
        'nasdaq': get_market_summary("^IXIC"),
        'dow': get_market_summary("^DJI"),
        'russel': get_market_summary("^RUT")
    }
    return render(request, "stock/index.html", context)

def regression_line(df, fig):
    x = np.arange(len(df.index))
    y = df['Close'].values
    slope, intercept, _, _, _ = linregress(x, y)
    fig.add_trace(go.Scatter(x=df.index, y=intercept + slope * x, mode='lines', name='Regression Line', line=dict(color='red')))

def setup_index_chart(ticker, title):
    obj = yf.Ticker(ticker)
    df = obj.history(period='1y')
    fig = go.Figure(data=go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close'))
    fig.update_layout(
        title=title,
        xaxis=dict(title='Date', tickmode='array', tickvals=pd.date_range(start=df.index.min(), end=df.index.max(), freq='ME'), tickformat='%b %Y', autorange=True),
        yaxis=dict(title='Closing Price', autorange=True),
        template='seaborn',
        autosize=True,
        
    )
    regression_line(df, fig)
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

# download list button
def download_stock_list(request):
    # creating http response object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="recommended_stocks.csv"'},
    )
    
    writer = csv.writer(response)
    writer.writerow(['Type', 'Symbol', 'Score', 'Company Name', 'Last Close Price', 'Slope', 'RSI', 'P/E Ratio'])

    # S&P 500
    for stock in SP500Stocks.objects.order_by('-score')[:10]:
        ticker_obj = yf.Ticker(stock.symbol)
        hist = ticker_obj.history(period="7d") 

        writer.writerow(['S&P 500', stock.symbol, stock.score, ticker_obj.info['shortName'], hist['Close'].iloc[-1], stock.slope, stock.rsi, stock.pe_ratio])
    # NASDAQ
    for stock in NASDAQStocks.objects.order_by('-score')[:10]:
        ticker_obj = yf.Ticker(stock.symbol)
        hist = ticker_obj.history(period="7d") 

        writer.writerow(['NASDAQ', stock.symbol, stock.score, ticker_obj.info['shortName'], hist['Close'].iloc[-1], stock.slope, stock.rsi, stock.pe_ratio])
    # DOW
    for stock in DOWStocks.objects.order_by('-score')[:10]:
        ticker_obj = yf.Ticker(stock.symbol)
        hist = ticker_obj.history(period="7d") 

        writer.writerow(['DOW', stock.symbol, stock.score, ticker_obj.info['shortName'], hist['Close'].iloc[-1], stock.slope, stock.rsi, stock.pe_ratio])
    return response


def create_stock_chart(symbols, title):
    stocks = pd.DataFrame()
    
    # query each symbol's data from the database
    # faster to query from the database vs the api
    for symbol in symbols:
        queryset = StockData.objects.filter(symbol=symbol).order_by('date')
        data = pd.DataFrame(list(queryset.values(
            'date', 'open', 'high', 'low', 'close', 'volume'
        )))
        if data.empty:
            continue

        # calculate moving averages and standard deviations
        data['mean'] = data['close'].rolling(20).mean()
        data['std'] = data['close'].rolling(20).std()
        data['upperBand'] = data['mean'] + (data['std'] * 2)
        data['symbol'] = symbol
        stocks = pd.concat([stocks, data], ignore_index=True)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        subplot_titles=(title, 'Volume'), row_width=[0.2, 0.7])

    for symbol in symbols:
        filtered_data = stocks[stocks['symbol'] == symbol]
        trace1 = go.Candlestick(
            x=filtered_data['date'],
            open=filtered_data['open'],
            high=filtered_data['high'],
            low=filtered_data['low'],
            close=filtered_data['close'],
            name=symbol)
        fig.add_trace(trace1, row=1, col=1)
        trace2 = go.Scatter(
            x=filtered_data['date'],
            y=filtered_data['upperBand'],
            mode='lines',
            name=f"{symbol} Upper Band")
        fig.add_trace(trace2, row=1, col=1)
        trace3 = go.Bar(
            x=filtered_data['date'],
            y=filtered_data['volume'],
            name=f"{symbol} Volume")
        fig.add_trace(trace3, row=2, col=1)

    # Calculate the total number of graphs
    graph_count = len(fig.data)
    # number of Symbols
    symbol_count = len(symbols)
    # Number of graphs per symbol
    tr = 3
    for g in range(tr, graph_count): 
        fig.update_traces(visible=False, selector=g)
    def create_layout_button(k, symbol):
        start, end = tr * k, tr * k + 2
        visibility = [False] * tr * symbol_count
        visibility[start:end] = [True, True, True]
        return dict(label=symbol,
                    method='restyle',
                    args=[{'visible': visibility[:-1],
                           'title': symbol,
                           'showlegend': True}])    
    
    fig.update(layout_xaxis_rangeslider_visible=False)
    fig.update_layout(
        autosize=True,
        updatemenus=[go.layout.Updatemenu(
            active=0,
            buttons=[create_layout_button(k, s) for k, s in enumerate(symbols)]
            )
        ])
    return fig.to_html(full_html=False)
# buy.html
def charts(request):

    # sp500
    top_10_sp500 = SP500Stocks.objects.order_by('-score')[:10]
    sp500_chart = create_stock_chart(list(top_10_sp500.values_list('symbol', flat=True)), 'Top 10 S&P 500 Stocks Closing Prices')

    # nasdaq
    top_10_nasdaq = NASDAQStocks.objects.order_by('-score')[:10]
    nasdaq_chart = create_stock_chart(list(top_10_nasdaq.values_list('symbol', flat=True)), 'Top 10 NASDAQ Stocks Closing Prices')

    # dow
    top_10_dow = DOWStocks.objects.order_by('-score')[:10]
    dow_chart = create_stock_chart(list(top_10_dow.values_list('symbol', flat=True)), 'Top 10 DOW Stocks Closing Prices')

    context = {
        'sp500_chart': sp500_chart,
        'nasdaq_chart': nasdaq_chart,
        'dow_chart': dow_chart,
        'top_sp500_stocks': top_10_sp500,
        'top_dow_stocks': top_10_dow,
        'top_nasdaq_stocks': top_10_nasdaq,
    }

    return render(request, "stock/buy.html", context)

def sellStocks(request):
    # sp500
    bottom_10_sp500 = SP500Stocks.objects.filter(slope__isnull=False, score__isnull=False, pe_ratio__isnull=False, rsi__isnull=False).order_by('score')[:10]
    sp500_chart = create_stock_chart(list(bottom_10_sp500.values_list('symbol', flat=True)), 'Bottom 10 S&P 500 Stocks Closing Prices')

    # nasdaq
    bottom_10_nasdaq = NASDAQStocks.objects.filter(slope__isnull=False, score__isnull=False, pe_ratio__isnull=False, rsi__isnull=False).order_by('score')[:10]
    nasdaq_chart = create_stock_chart(list(bottom_10_nasdaq.values_list('symbol', flat=True)), 'Bottom 10 NASDAQ Stocks Closing Prices')

    # dow
    bottom_10_dow = DOWStocks.objects.filter(slope__isnull=False, score__isnull=False, pe_ratio__isnull=False, rsi__isnull=False).order_by('score')[:10]
    dow_chart = create_stock_chart(list(bottom_10_dow.values_list('symbol', flat=True)), 'Bottom 10 DOW Stocks Closing Prices')
    context = {
        'bottom_sp500_stocks': bottom_10_sp500,
        'bottom_nasdaq_stocks': bottom_10_nasdaq,
        'bottom_dow_stocks': bottom_10_dow,
        'sp500_chart': sp500_chart,
        'nasdaq_chart': nasdaq_chart,
        'dow_chart': dow_chart
    }
    return render(request, "stock/sell.html", context)