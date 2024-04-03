from django.shortcuts import render
from django.views import generic
from .models import Stock, StockPrice
import plotly.express as px
import pandas as pd
import os
from django.conf import settings
import plotly.graph_objects as go
# Create your views here.

# home of the clock page
def index(request):
    context = {

    }
    return render(request, "single_page_app/clock_page.html", context)

def help_page(request):
    context = {

    }
    return render(request, "single_page_app/help_page.html", context)

def about_page(request):
    context = {

    }
    return render(request, "single_page_app/about_page.html", context)

def service_page(request):
    data = []
    for stock in Stock.objects.all():
        for price in stock.prices.all():
            data.append({
                "symbol": stock.symbol,
                "date": price.date,
                "volume": price.volume
            })
    df = pd.DataFrame(data)
    fig = px.line(df, x="date", y="volume", color="symbol")
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Volume"
    )
    fig.update_layout(xaxis=dict(rangeslider=dict(visible=True)))
    converted_fig = fig.to_html(full_html=False)
    context = {'converted_fig': converted_fig}
    return render(request, "single_page_app/service_page.html", context)

def data_page(request):
    data = []
    for stock in Stock.objects.all():
        for price in stock.prices.all():
            data.append({
                "symbol": stock.symbol,
                "date": price.date,
                "volume": price.volume,
                "close_price": price.close_price,
                "high_price": price.high_price,
                "low_price": price.low_price,
                "open_price": price.open_price
            })
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.strftime('%B')
    fig = px.box(df, x='month', y='volume', color='symbol')
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Volume",
        title="Monthly Stock Trade Volume"
    )
    static_path = 'single_page_app/static/single_page_app/images'
    filename = 'box_plot.png'
    image_path = os.path.join(settings.BASE_DIR, static_path, filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    #fig.write_image(image_path)
    converted_fig = fig.to_html(full_html=False)

    # fig 2
    fig2 = px.line(df, x='date', y='close_price', color='symbol')
    fig2.update_layout(
        xaxis_title="Day",
        yaxis_title="Closing Price",
        title="Stock Closing Price"
    )
    converted_fig2 = fig2.to_html(full_html=False)

    # fig 3
    apple_stock = df[df["symbol"] == 'AAPL']
    fig3 = go.Figure(data=[go.Candlestick(x=apple_stock['date'],
                open=apple_stock['open_price'],
                high=apple_stock['high_price'],
                low=apple_stock['low_price'],
                close=apple_stock['close_price'])])
    fig3.update_layout(
        title="Candlestick Chart for AAPL"
    )
    converted_fig3 = fig3.to_html(full_html=False)

    # fig 4
    # fig 3
    microsoft_stock = df[df["symbol"] == 'MSFT']
    fig4 = go.Figure(data=[go.Candlestick(x=microsoft_stock['date'],
                open=microsoft_stock['open_price'],
                high=microsoft_stock['high_price'],
                low=microsoft_stock['low_price'],
                close=microsoft_stock['close_price'])])
    fig4.update_layout(
        title="Candlestick Chart for MFST"
    )
    converted_fig4 = fig4.to_html(full_html=False)
    context = {
        'converted_fig': converted_fig,
        'converted_fig2': converted_fig2,
        'converted_fig3': converted_fig3,
        'converted_fig4': converted_fig4
    }
    return render(request, "single_page_app/data_page.html", context)
