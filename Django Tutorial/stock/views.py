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
from .models import SP500Stocks

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
    sp500_index = "^GSPC"
    sp500_obj = yf.Ticker(sp500_index)
    sp500_df = sp500_obj.history(period='5y')
    years = pd.date_range(start=sp500_df.index.min(), end=sp500_df.index.max(), freq='YS')

    fig = go.Figure(data=go.Scatter(x=sp500_df.index, y=sp500_df['Close'], mode='lines', name='Close'))

    fig.update_layout(title='S&P 500 Performance Over the Past 5 Years',
                    xaxis=dict(
                        title='Year',
                        tickmode='array',
                        tickvals=years,  # place tick at start of year
                        tickformat='%Y', # formatting for only year
                        ),
                    yaxis_title='Closing Price',
                    template='seaborn',
                    autosize=True) 

    x = np.arange(len(sp500_df.index))
    y = sp500_df['Close'].values
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    y_regression = intercept + slope * x
    fig.add_trace(go.Scatter(x=sp500_df.index, y=y_regression, mode='lines', name='Regression Line', line=dict(color='red')))
    sp500fig_converted = fig.to_html(full_html=False)

    # market summary 
    sp500_summary = get_market_summary("^GSPC")
    nasdaq_summary = get_market_summary("^IXIC")
    dow_summary = get_market_summary("^DJI")
    russel_summary = get_market_summary("^RUT")
    # top 10 SP500 Stocks
    top_sp500_stocks = SP500Stocks.objects.all()[:10]
    context = {
        'sp500fig_converted': sp500fig_converted,
        'top_sp500_stocks': top_sp500_stocks,
        'sp500': sp500_summary,
        'nasdaq': nasdaq_summary,
        'dow': dow_summary,
        'russel': russel_summary
               
        }
    return render(request, "stock/index.html", context)
