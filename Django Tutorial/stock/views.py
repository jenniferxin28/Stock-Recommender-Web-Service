from django.shortcuts import render
from django.views import generic
import pandas as pd
import os
from django.conf import settings
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress
import numpy as np
from .models import SP500Stocks, DOWStocks, NASDAQStocks, RUSSELLStocks
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
def index(request):
    sp500fig_converted = setup_index_chart("^GSPC", 'S&P 500 Performance Over the Past Year')
    dowfig_converted = setup_index_chart("^DJI", 'DOW Performance Over the Past Year')
    nasdaqfig_converted = setup_index_chart("^IXIC", 'NASDAQ Performance Over the Past Year')

    context = {
        'sp500fig_converted': sp500fig_converted,
        'dowfig_converted': dowfig_converted,
        'nasdaqfig_converted': nasdaqfig_converted,
        'top_sp500_stocks': SP500Stocks.objects.all()[:10],
        'top_dow_stocks': DOWStocks.objects.all()[:10],
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
        xaxis=dict(title='Date', tickmode='array', tickvals=pd.date_range(start=df.index.min(), end=df.index.max(), freq='M'), tickformat='%b %Y', autorange=True),
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


def create_stock_chart(stock_symbols, title, period='3y'):
    """
    Create a line chart for given stock symbols over a specified period.
    
    Args:
        stock_symbols (list of str): List of stock ticker symbols.
        title (str): Title of the chart.
        period (str): Period of historical data to fetch, default is '3y' (3 years).
    
    Returns:
        str: HTML string of the created Plotly chart.
    """
    fig = go.Figure()

    for symbol in stock_symbols:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name=symbol))


    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Closing Price',
        template='seaborn',
        autosize=True  
    )

    # html link
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

# charts.html
def charts(request):

    # sp500
    top_10_sp500 = SP500Stocks.objects.order_by('-score')[:10].values_list('symbol', flat=True)
    sp500_chart = create_stock_chart(list(top_10_sp500), 'Top 10 S&P 500 Stocks Closing Prices')

    # nasdaq
    top_10_nasdaq = NASDAQStocks.objects.order_by('-score')[:10].values_list('symbol', flat=True)
    nasdaq_chart = create_stock_chart(list(top_10_nasdaq), 'Top 10 NASDAQ Stocks Closing Prices')

    # dow
    top_10_dow = DOWStocks.objects.order_by('-score')[:10].values_list('symbol', flat=True)
    dow_chart = create_stock_chart(list(top_10_dow), 'Top 10 DOW Stocks Closing Prices')

    context = {
        'sp500_chart': sp500_chart,
        'nasdaq_chart': nasdaq_chart,
        'dow_chart': dow_chart,
        'top_sp500_stocks': SP500Stocks.objects.all().order_by('-score')[:10],
        'top_dow_stocks': DOWStocks.objects.all().order_by('-score')[:10],
        'top_nasdaq_stocks': NASDAQStocks.objects.all().order_by('-score')[:10],
    }

    return render(request, "stock/charts.html", context)